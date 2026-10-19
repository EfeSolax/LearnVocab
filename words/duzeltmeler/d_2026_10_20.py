# -*- coding: utf-8 -*-
"""
20 Ekim — C2 veri kalitesi (Efe: "C2'de olmaması gerekenleri çıkar, B2/C1'de sıkışmış C2'leri taşı").

C2'deki 153 kelimenin hepsi bizim etiketimizdi (learnvocab) ve çoğu eskimiş ya da uzmanlık kelimesiydi
(corolla, seine, firth). Claude hepsini ve C2 adayı olabilecek düşük sıklıklı learnvocab etiketli
B2 (Zipf < 2,8: 2.128) ve C1 (Zipf < 3,0: 1.458) kelimelerini elle okudu. Kararlar
veri/kalite_olcumu/c2/ altında:
  karar_c2_mevcut.txt  C2'de kalanlar (K) ve az kullanılan işaretlenenler (A)
  c2ye_tasi.txt        B2/C1'den C2'ye taşınanlar (yalnızca learnvocab etiketli)
  az_kullanilan_aday.txt  B2/C1'de olup az kullanılana aday olanlar: UYGULANMAZ, Efe inceleyecek
Satırlar "kelime" ya da "kelime:tür"; tür yoksa o yazımın uygun bütün kayıtları. Kelimeyle eşleşir
(kimlikle değil), canlıda da aynen çalışır. Değişenler UYGULANAN dosyasına yazılır.

Çalıştırma (önce kuru deneme; yedek: ~/LearnVocab-yedekler/db.sqlite3.yedek-20261020-c2-oncesi):
  python manage.py shell -c "from words.duzeltmeler import d_2026_10_20 as d; print(d.c2_duzelt(kuru=True))"
  python manage.py shell -c "from words.duzeltmeler import d_2026_10_20 as d; print(d.c2_duzelt())"
  python manage.py oncelik_hesapla
Sunucuda kayit=False verilir: depodaki uygulanan.tsv değişirse sonraki git pull çakışır.
Tekrar çalıştırmak güvenli: zaten C2 olan / zaten işaretli kayıt atlanır.
"""
import csv
from collections import Counter

from django.conf import settings

from words.duzeltmeler.d_2026_10_14b import _calistir
from words.models import DILBILGISI_TURLERI, Word

KLASOR = settings.BASE_DIR / "veri" / "kalite_olcumu" / "c2"
UYGULANAN = KLASOR / "uygulanan.tsv"


def _ogeler(metin):
    """Yorum satırları atlanır; 'kelime[:tür]' ya da çok kelimeli phrasal ('mull over')."""
    ogeler = []
    for satir in metin.splitlines():
        satir = satir.strip()
        if not satir or satir.startswith("#"):
            continue
        ogeler.append(satir)
    return ogeler


def _cozumle(parcalar):
    """Boşlukla ayrılmış öğeler -> [(kelime, tür ya da None)]; 'fizzle out' gibi phrasal'lar birleşik."""
    sonuc, i = [], 0
    while i < len(parcalar):
        p = parcalar[i]
        # İki parçalı phrasal verb: ikinci parça bir parçacıksa birleştir
        if i + 1 < len(parcalar) and parcalar[i + 1] in ("out", "over", "up", "off", "down", "in", "on"):
            p, i = f"{p} {parcalar[i + 1]}", i + 1
        kelime, _, tur = p.partition(":")
        sonuc.append((kelime, tur or None))
        i += 1
    return sonuc


def c2_kararlari():
    """{'K': [...], 'A': [...]} — C2'deki kelimeler için."""
    kararlar = {"K": [], "A": []}
    for satir in _ogeler((KLASOR / "karar_c2_mevcut.txt").read_text(encoding="utf-8")):
        kod, _, geri = satir.partition(" ")
        kararlar[kod] += _cozumle(geri.split())
    return kararlar


def tasinacaklar():
    ogeler = []
    for satir in _ogeler((KLASOR / "c2ye_tasi.txt").read_text(encoding="utf-8")):
        ogeler += _cozumle(satir.split())
    return ogeler


def _kayitlar(qs, kelime, tur):
    qs = qs.filter(text=kelime)
    return qs.filter(pos=tur) if tur else qs


def c2_duzelt(kuru=False, kayit=True):
    def is_():
        sayac, degisen, eslesmeyen = Counter(), [], []
        for kelime, tur in c2_kararlari()["A"]:
            bulunan = list(_kayitlar(Word.objects.filter(cefr="C2"), kelime, tur))
            if not bulunan:
                eslesmeyen.append(f"A {kelime}")
            for w in bulunan:
                if w.az_kullanilan:
                    sayac["zaten az kullanılan"] += 1
                    continue
                w.az_kullanilan = True
                w.save(update_fields=["az_kullanilan"])
                sayac["az kullanılan"] += 1
                degisen.append((w.pk, w.text, w.pos, "C2", "C2", "az kullanılan"))

        aday = (Word.objects.filter(cefr__in=("B2", "C1"), cefr_kaynak="learnvocab")
                .exclude(pos__in=DILBILGISI_TURLERI))
        for kelime, tur in tasinacaklar():
            bulunan = list(_kayitlar(aday, kelime, tur))
            if not bulunan:
                if _kayitlar(Word.objects.filter(cefr="C2"), kelime, tur).exists():
                    sayac["zaten C2"] += 1
                else:
                    eslesmeyen.append(f"C2 {kelime}")
                continue
            for w in bulunan:
                degisen.append((w.pk, w.text, w.pos, w.cefr, "C2", "C2'ye taşındı"))
                sayac[f"{w.cefr} -> C2"] += 1
                w.cefr = "C2"
                w.save(update_fields=["cefr"])

        if not kuru and kayit and degisen:
            yeni = not UYGULANAN.exists()
            with open(UYGULANAN, "a", encoding="utf-8", newline="") as f:
                yazici = csv.writer(f, delimiter="\t")
                if yeni:
                    yazici.writerow(["word_id", "kelime", "tür", "eski", "yeni", "işlem"])
                yazici.writerows(degisen)
        sayac["eşleşmeyen"] = len(eslesmeyen)
        if eslesmeyen:
            sayac["eşleşmeyenler: " + ", ".join(eslesmeyen)] = 1
        return sayac
    return _calistir(is_, kuru)
