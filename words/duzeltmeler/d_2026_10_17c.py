# -*- coding: utf-8 -*-
"""
17 Ekim — Büyük/küçük harf çiftleri. Canlı veritabanı (MySQL, utf8mb4_general_ci) harf büyüklüğünü
ayırt etmez; words_word'ün (text, pos) tekilliği "March"/"march" gibi çiftlerde çakıştı ve ilk
yükleme durdu. Efe'nin kararı:
  - Moorish, Passover, Satan: küçük harfli kayıt (moorish, passover, satan) kalır; büyük harfli kopya
    birleştirilir (anlamı aynı olduğu için silinir).
  - March (ay): march (isim) kaydında birleşir; "Mart" anlamı march'ın son anlamı olur.
Bağlar (listeler, ifadeler, hazır listeler, kullanıcı kayıtları) kalan kayda taşınır; kalan kayıtta
zaten olan bağ kopyası silinir. Silinenler BIRLESME_DOSYASI'na yazılır.

Çalıştırma (önce kuru deneme; yedek: ~/LearnVocab-yedekler/db.sqlite3.yedek-20261017-harf-oncesi):
  python manage.py shell -c "from words.duzeltmeler import d_2026_10_17c as d; print(d.harf_ciftleri(kuru=True))"
  python manage.py shell -c "from words.duzeltmeler import d_2026_10_17c as d; print(d.harf_ciftleri())"
Tekrar çalıştırmak güvenli: büyük harfli kayıt yoksa atlanır.
(İlk çalıştırmada "mart" olarak taşınan anlam elle "Mart (ay)" yapıldı; kod artık bunu kendisi yapar.)
"""
import csv
from collections import Counter

from django.db import IntegrityError, transaction

from words.duzeltmeler.d_2026_10_14b import KLASOR, _calistir
from words.models import Meaning, Word, WordFamily

BIRLESME_DOSYASI = KLASOR / "buyuk-kucuk-harf-birlesme.tsv"
# (silinecek, kalacak, tür, büyük harflinin anlamı kalan kayda taşınsın mı)
CIFTLER = [
    ("Moorish", "moorish", "adjective", False),
    ("Passover", "passover", "noun", False),
    ("Satan", "satan", "noun", False),
    ("March", "march", "noun", True),
]


def _bagi_tasi(nesne, alan, eski, yeni, sayac):
    """nesne.alan eski → yeni; kalan kayıtta aynısı varsa (tekillik) kopya silinir."""
    setattr(nesne, alan, yeni)
    try:
        with transaction.atomic():
            nesne.save(update_fields=[alan])
        sayac[f"taşındı: {type(nesne).__name__}.{alan}"] += 1
    except IntegrityError:
        nesne.delete()
        sayac[f"kopya silindi: {type(nesne).__name__}.{alan}"] += 1


def _kelime_baglari(eski, yeni, sayac):
    for rel in Word._meta.related_objects:
        if rel.related_model in (Meaning,) or rel.field.name == "word" and rel.related_model.__name__ == "WordForm":
            continue
        if rel.many_to_many:
            if not rel.through._meta.auto_created:
                continue          # ara modeli olan (HazirListeKelimesi) FK olarak taşınır
            for sahip in rel.related_model.objects.filter(**{rel.field.name: eski}):
                getattr(sahip, rel.field.name).remove(eski)
                getattr(sahip, rel.field.name).add(yeni)
                sayac[f"taşındı: {rel.related_model.__name__}.{rel.field.name}"] += 1
            continue
        for nesne in rel.related_model.objects.filter(**{rel.field.name: eski}):
            _bagi_tasi(nesne, rel.field.attname.removesuffix("_id"), eski, yeni, sayac)


def _anlam_baglari(eski_anlam, yeni_anlam, sayac):
    """Silinecek anlama bağlı içerik dışı kayıtlar (kullanıcı listeleri vb.) kalan anlama taşınır."""
    from LearnVocab.veritabani_esitleme import ICERIK
    for rel in Meaning._meta.related_objects:
        if rel.many_to_many or rel.related_model._meta.db_table in ICERIK:
            continue              # içerik (örnek, eş dizim …) anlamla birlikte silinir
        for nesne in rel.related_model.objects.filter(**{rel.field.name: eski_anlam}):
            _bagi_tasi(nesne, rel.field.name, eski_anlam, yeni_anlam, sayac)


def harf_ciftleri(kuru=False):
    def is_():
        sayac, kayit = Counter(), []
        for sil, kal, tur, anlami_tasi in CIFTLER:
            eski = Word.objects.filter(text=sil, pos=tur).first()
            yeni = Word.objects.filter(text=kal, pos=tur).first()
            if not eski or not yeni:
                sayac["yok: atlandı"] += 1
                continue
            aile = eski.family_id
            for m in eski.meanings.all():
                kayit.append([sil, tur, kal, m.id, m.meaning_tr, "taşındı" if anlami_tasi else "silindi"])
                if anlami_tasi:
                    son = yeni.meanings.order_by("-sort_order").values_list("sort_order", flat=True).first() or 0
                    m.word, m.sort_order = yeni, son + 1
                    if m.meaning_tr == "mart":
                        m.meaning_tr = "Mart (ay)"        # yürüyüş anlamıyla karışmasın
                    m.save(update_fields=["word", "sort_order", "meaning_tr"])
                    sayac["anlam taşındı"] += 1
                else:
                    _anlam_baglari(m, yeni.meanings.order_by("sort_order", "id").first(), sayac)
            _kelime_baglari(eski, yeni, sayac)
            eski.delete()
            sayac["kelime silindi"] += 1
            if aile and aile != yeni.family_id and not Word.objects.filter(family_id=aile).exists():
                WordFamily.objects.filter(pk=aile).delete()
                sayac["boş aile silindi"] += 1
        if not kuru:
            with BIRLESME_DOSYASI.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f, delimiter="\t")
                w.writerow(["silinen_kelime", "tur", "kalan_kelime", "anlam_id", "anlam", "anlamin_durumu"])
                w.writerows(kayit)
        return sayac
    return dict(_calistir(is_, kuru))
