# -*- coding: utf-8 -*-
"""
7 Ekim — tanım, kalıp ve örnek cümle kalitesi (rapor 18.7 B aşaması).

1. tanimlari_duzelt(): isim, sıfat ve zarf tanımlarındaki tür hataları. Sıfatlar
   "to be X", zarflar "to do something in a X manner", isimler fiil gibi ("to give
   formal approval") tanımlanmıştı. Claude 840 adayın hepsini okudu; değişen 667
   tanım veri/tanim_denetimi/tur-hatalari.tsv'de (eski -> yeni).
2. kaliplari_bicimle(): kalıp gösterimi (Efe'nin kararı, 7 Ekim): "+" yok, "noun",
   "gerund" gibi terimler yok; sb / sth / doing sth / to do sth / that … kullanılır.
   Kural words/kalip_bicimi.py'de. Bilgi taşımayan (repair sth, be stainless) ve
   sb/sth ile yazılamayan (nearly + adjective) kalıplar silinir; silinenler
   veri/kalip_denetimi/mekanik-silinen.tsv'ye yazılır.

Çalıştırma:
  python manage.py shell -c "from words.duzeltmeler import d_2026_10_07 as d; print(d.uygula())"
Tekrar çalıştırmak güvenli.
"""
import csv
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.db import transaction

from words.kalip_bicimi import bicimle
from words.models import ExampleSentence, Meaning, UsagePattern

VERI = Path(settings.BASE_DIR) / "veri"
TANIM_DOSYASI = VERI / "tanim_denetimi" / "tur-hatalari.tsv"
KALIP_KLASORU = VERI / "kalip_denetimi"


def _oku(yol):
    with open(yol, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def tanimlari_duzelt():
    sayac = Counter()
    for k in _oku(TANIM_DOSYASI):
        n = Meaning.objects.filter(word__text=k["kelime"], word__pos=k["tur"],
                                   meaning_tr=k["anlam"], definition=k["eski"]) \
            .update(definition=k["yeni"])
        sayac["tanım düzeltildi" if n else "tanım bulunamadı (önceden düzeltilmiş)"] += n or 1
    return sayac


def kaliplari_bicimle():
    sayac, silinenler, sil, degis = Counter(), [], [], {}
    kaliplar = (UsagePattern.objects.select_related("meaning__word")
                .order_by("meaning_id", "sort_order", "id"))
    gorulen = set()
    for k in kaliplar.iterator(chunk_size=2000):
        kelime = k.meaning.word
        yeni, sebep = bicimle(k.pattern, kelime.text, k.example or "", kelime.pos)
        anahtar = (k.meaning_id, (yeni or "").lower())
        if yeni and anahtar in gorulen:
            sebep = "aynı anlamda tekrar"
        if sebep:
            silinenler.append({"kelime": kelime.text, "tur": kelime.pos,
                               "anlam": k.meaning.meaning_tr, "kalip": k.pattern, "sebep": sebep})
            sil.append(k.id)
            continue
        gorulen.add(anahtar)
        if yeni != k.pattern:
            degis[k.id] = yeni
    for i in range(0, len(sil), 500):
        UsagePattern.objects.filter(id__in=sil[i:i + 500]).delete()
    sayac["kalıp silindi"] = len(sil)
    # İki aşamalı: yeni değer aynı anlamın henüz değişmemiş başka kalıbında duruyor olabilir.
    UsagePattern.objects.bulk_update(
        [UsagePattern(id=i, pattern=f"~{i}") for i in degis], ["pattern"], batch_size=1000)
    UsagePattern.objects.bulk_update(
        [UsagePattern(id=i, pattern=p) for i, p in degis.items()], ["pattern"], batch_size=1000)
    sayac["kalıp biçimlendi"] = len(degis)
    if silinenler:
        KALIP_KLASORU.mkdir(exist_ok=True)
        with open(KALIP_KLASORU / "mekanik-silinen.tsv", "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, ("kelime", "tur", "anlam", "kalip", "sebep"),
                               delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(silinenler)
    return sayac


ZAYIF_DOSYASI = Path(settings.BASE_DIR) / "ozetler" / "zayif-kaliplar.tsv"
ELLE_ALANLAR = ("nesne", "kelime", "tur", "anlam", "eski", "karar", "yeni", "yeni_ornek")


def _anlam_q(k):
    return {"meaning__word__text": k["kelime"], "meaning__word__pos": k["tur"],
            "meaning__meaning_tr": k["anlam"]}


def elle_kararlari(dosyalar=None):
    """Claude'un anlam başına okumasından çıkan kararlar (veri/kalip_denetimi/elle-*.tsv).

    nesne: kalip / ornek / anlam-tr / anlam-tanim; karar: sil / zayif / degistir.
    Türkçe karşılık değişiklikleri en sona bırakılır: öteki satırlar eski karşılığı anar.
    """
    yollar = ([KALIP_KLASORU / d for d in dosyalar] if dosyalar
              else sorted(KALIP_KLASORU.glob("elle-*.tsv")))
    satirlar = [k for y in yollar for k in _oku(y)]
    satirlar.sort(key=lambda k: k["nesne"] == "anlam-tr")
    sayac = Counter()
    for k in satirlar:
        nesne, karar = k["nesne"], k["karar"]
        if karar == "zayif":
            sayac["zayıf (dokunulmadı)"] += 1
            continue
        if nesne == "kalip":
            for p in UsagePattern.objects.filter(pattern=k["eski"], **_anlam_q(k)):
                if karar == "degistir" and k["yeni"] == p.pattern and not k["yeni_ornek"]:
                    continue
                if karar == "sil" or UsagePattern.objects.filter(
                        meaning_id=p.meaning_id, pattern=k["yeni"]).exclude(id=p.id).exists():
                    p.delete()
                    sayac["kalıp silindi"] += 1
                    continue
                p.pattern = k["yeni"]
                if k["yeni_ornek"]:
                    p.example = k["yeni_ornek"]
                p.save(update_fields=["pattern", "example"])
                sayac["kalıp düzeltildi"] += 1
        elif nesne == "ornek":
            for e in ExampleSentence.objects.filter(text=k["eski"], **_anlam_q(k)):
                if karar == "sil":
                    e.delete()
                    sayac["örnek silindi"] += 1
                else:
                    e.text = k["yeni"]
                    e.save(update_fields=["text"])
                    sayac["örnek yeniden yazıldı"] += 1
        else:
            q = Meaning.objects.filter(word__text=k["kelime"], word__pos=k["tur"],
                                       meaning_tr=k["anlam"])
            if nesne == "anlam-tr":
                sayac["Türkçe düzeltildi"] += q.update(meaning_tr=k["yeni"])
            else:
                sayac["tanım düzeltildi"] += q.update(definition=k["yeni"])
    sayac["zayıf dosyası"] = zayif_dosyasini_yaz()
    return sayac


def zayif_dosyasini_yaz():
    zayiflar = [k for y in sorted(KALIP_KLASORU.glob("elle-*.tsv")) for k in _oku(y)
                if k["karar"] == "zayif"]
    with open(ZAYIF_DOSYASI, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ELLE_ALANLAR[:5], delimiter="\t", lineterminator="\n",
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(zayiflar)
    return len(zayiflar)


def uygula(dosyalar=None):
    """Hepsi (tanım, mekanik kalıp, elle kararlar) ya da yalnızca verilen elle dosyaları."""
    with transaction.atomic():
        if dosyalar:
            return dict(elle_kararlari(dosyalar))
        sayac = tanimlari_duzelt()
        sayac.update(kaliplari_bicimle())
        sayac.update(elle_kararlari())
    return dict(sayac)
