"""
Sıklık ve nadir tür (rapor 18.16).

  siklik_puani("bank")  -> wordfreq Zipf puanı (1 çok seyrek … 7 çok sık)
  nadir_tur_idleri(kelimeler) -> nadir tür sayılan Word id'leri

Sıklık ekranda HİÇ görünmez; yalnızca arka planda kullanılır.
"""

from collections import defaultdict

SEVIYE_SIRASI = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

# L&P'de yeni kelime ağırlığı (rapor 18.16/3): (max(zipf, 1,5) - 1)^2
AGIRLIK_TABAN = 1.5


def siklik_puani(metin):
    """wordfreq yoksa ya da metin boşsa None."""
    try:
        from wordfreq import zipf_frequency
    except ImportError:
        return None
    metin = (metin or "").strip()
    if not metin:
        return None
    return round(zipf_frequency(metin, "en"), 2)


def lp_agirligi(siklik):
    """Yeni kelimenin L&P'de çıkma ağırlığı; sıklığı bilinmeyen en düşük ağırlığı alır."""
    z = max(siklik if siklik is not None else AGIRLIK_TABAN, AGIRLIK_TABAN)
    return (z - 1) ** 2


def nadir_tur_idleri(kelimeler):
    """
    kelimeler: (id, text, pos, cefr) dörtlüleri.
    Aynı yazımın birden çok türü varsa ve temel (en düşük seviyeli) tür
    A1–B1 iken bir tür C1–C2 ise o tür nadirdir: dog (fiil) C1, dog (isim) A2.
    """
    gruplar = defaultdict(list)
    for id_, text, pos, cefr in kelimeler:
        gruplar[text.lower()].append((id_, SEVIYE_SIRASI.get(cefr)))
    nadir = set()
    for uyeler in gruplar.values():
        seviyeler = [s for _, s in uyeler if s]
        if len(uyeler) < 2 or not seviyeler:
            continue
        if min(seviyeler) > SEVIYE_SIRASI["B1"]:
            continue
        nadir.update(id_ for id_, s in uyeler if s and s >= SEVIYE_SIRASI["C1"])
    return nadir
