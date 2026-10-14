# -*- coding: utf-8 -*-
"""
14 Ekim — anlam sırası (rapor 18.40). Claude elle seçti, API yok.

Kartta, okuma baloncuğunda ve Learn & Pass'te ilk anlam öne çıkıyor; kelime hattı
bazı kelimelerde yaygın anlamı arkaya koymuştu (land: "elde etmek" önde, "yere inmek"
ikinci). Çok anlamlı 4.077 kelime sıklık sırasıyla okundu; ilk anlamı yanlış olan
321 kelimenin sırası veri/anlam_sirasi/2026-10-14.tsv dosyasına yazıldı.

Yalnız sort_order değişir: anlam satırları, ilerleme ve bağlar olduğu gibi kalır.
Dosyada adı geçmeyen anlamlar eski sıralarıyla sona eklenir.

Aynı taramada aynı anlamın iki satıra bölündüğü kelimeler de bulundu (think "düşünmek" /
"düşünmek, sanmak"; increase "artırmak" / "artmak"; law "yasa, hukuk" / "hukuk"). Öğrencinin
ayrı ayrı öğrenmesi gereken bir fark yoksa satırlar birleştirildi: 437 kelime,
veri/anlam_sirasi/2026-10-14-birlestirme.tsv. İlerleme kelime düzeyinde tutulduğu için
(learnpass, Listem) kimsenin ilerlemesi etkilenmez. Birleşen anlamın örnek cümleleri,
kalıpları, kullanım kalıpları, eş/zıt anlamları, konuları ve diyalogları kalan anlama
taşınır; aynı kalıp ikinci kez yazılmaz.

Çalıştırma:
  python manage.py shell -c "from words.duzeltmeler import d_2026_10_14 as d; print(d.anlam_sirasi()); print(d.anlam_birlestir())"
İkisi de tekrar çalıştırmak güvenli. Önce sıra, sonra birleştirme.
"""
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.db import transaction

from texts.models import Diyalog
from words.arama import CEFR_SIRASI, cefr_sirasi
from words.models import Collocation, UsagePattern, Word, WordRelation

DOSYA = Path(settings.BASE_DIR) / "veri" / "anlam_sirasi" / "2026-10-14.tsv"
BIRLESTIRME = Path(settings.BASE_DIR) / "veri" / "anlam_sirasi" / "2026-10-14-birlestirme.tsv"


def oku(yol=DOSYA):
    """(kelime, tür, [Türkçe karşılıklar sırasıyla]) satırları."""
    for satir in yol.read_text(encoding="utf-8").splitlines():
        if satir and not satir.startswith("#"):
            kelime, tur, *sira = satir.split("\t")
            yield kelime, tur, sira


def anlam_sirasi(kuru=False):
    sayac = Counter()
    with transaction.atomic():
        for kelime, tur, sira in oku():
            w = Word.objects.filter(text=kelime, pos=tur).first()
            if not w:
                sayac["kelime yok"] += 1
                continue
            anlamlar = list(w.meanings.all())
            bulunan = {m.meaning_tr: m for m in anlamlar}
            eksik = [tr for tr in sira if tr not in bulunan]
            if eksik:
                sayac["anlam yok"] += 1
                continue
            secilen = [bulunan[tr] for tr in sira]
            yeni = secilen + [m for m in anlamlar if m not in secilen]
            if [m.pk for m in yeni] == [m.pk for m in anlamlar] and all(
                    m.sort_order == i for i, m in enumerate(yeni)):
                sayac["zaten doğru"] += 1
                continue
            sayac["sırası değişen kelime"] += 1
            for i, m in enumerate(yeni):
                if m.sort_order != i:
                    m.sort_order = i
                    if not kuru:
                        m.save(update_fields=["sort_order"])
        if kuru:
            transaction.set_rollback(True)
    return dict(sayac)


def _tasi(kalan, giden, sayac):
    """giden anlamın her şeyini kalana taşır; aynı kalıp ikinci kez yazılmaz."""
    son = max(kalan.examples.values_list("sort_order", flat=True), default=-1) + 1
    var = set(kalan.examples.values_list("text", flat=True))
    for c in giden.examples.all():
        if c.text in var:
            c.delete()
            continue
        c.meaning, c.sort_order = kalan, son + c.sort_order
        c.save(update_fields=["meaning", "sort_order"])
        sayac["taşınan cümle"] += 1
    for Model, ad in ((Collocation, "kalıp"), (UsagePattern, "kullanım kalıbı")):
        son = max(Model.objects.filter(meaning=kalan).values_list("sort_order", flat=True),
                  default=-1) + 1
        var = {p.lower() for p in Model.objects.filter(meaning=kalan).values_list("pattern", flat=True)}
        for k in Model.objects.filter(meaning=giden):
            if k.pattern.lower() in var:
                k.delete()
                continue
            var.add(k.pattern.lower())
            k.meaning, k.sort_order = kalan, son + k.sort_order
            k.save(update_fields=["meaning", "sort_order"])
            sayac[f"taşınan {ad}"] += 1
    var = set(WordRelation.objects.filter(meaning=kalan).values_list("from_word", "to_word", "type"))
    for r in WordRelation.objects.filter(meaning=giden):
        if (r.from_word_id, r.to_word_id, r.type) in var:
            r.delete()
            continue
        r.meaning = kalan
        r.save(update_fields=["meaning"])
        sayac["taşınan bağ"] += 1
    sayac["taşınan diyalog"] += Diyalog.objects.filter(meaning=giden).update(meaning=kalan)
    kalan.categories.add(*giden.categories.all())


def anlam_birlestir(kuru=False):
    sayac = Counter()
    with transaction.atomic():
        for satir in BIRLESTIRME.read_text(encoding="utf-8").splitlines():
            if not satir or satir.startswith("#"):
                continue
            kelime, tur, yeni_tr, *eski = satir.split("\t")
            w = Word.objects.filter(text=kelime, pos=tur).first()
            if not w:
                sayac["kelime yok"] += 1
                continue
            anlamlar = {m.meaning_tr: m for m in w.meanings.all()}
            if eski[0] not in anlamlar or (eski[0] == yeni_tr and not any(t in anlamlar for t in eski[1:])):
                # Tekrar çalıştırma: kalan anlam yeni adıyla duruyor, ötekiler silinmiş.
                sayac["zaten yapılmış" if yeni_tr in anlamlar else "anlam yok"] += 1
                continue
            kalan = anlamlar[eski[0]]
            gidenler = [anlamlar[tr] for tr in eski[1:] if tr in anlamlar]
            seviyeler = [m.cefr for m in [kalan, *gidenler] if m.cefr in CEFR_SIRASI]
            if seviyeler:
                kalan.cefr = min(seviyeler, key=cefr_sirasi)
            kalan.meaning_tr = yeni_tr
            kalan.save(update_fields=["meaning_tr", "cefr"])
            for giden in gidenler:
                _tasi(kalan, giden, sayac)
                giden.delete()
                sayac["silinen anlam satırı"] += 1
            for i, m in enumerate(w.meanings.all()):
                if m.sort_order != i:
                    m.sort_order = i
                    m.save(update_fields=["sort_order"])
            sayac["birleşen kelime" if gidenler else "yalnız karşılık düzeltildi"] += 1
        if kuru:
            transaction.set_rollback(True)
    return dict(sayac)
