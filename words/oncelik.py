"""
Öğrenme önceliği (Efe, 20 Ekim): bir kelimeyi öğrenmek ne kadar elzem?

L&P yeni kelimeyi seviyenin içinde en yüksek öncelikten aşağı doğru seçer (learnpass/tekrar.py);
nadir ve türetilmiş kelimeler sona kalır. Puan 0–100 arası, ekranda HİÇ görünmez.

  sıklık          Zipf 1 → 0 … Zipf 7 → 60
  resmî liste     Oxford 3000/5000 +20 · Cambridge +12 (bizim etiketimiz +0)
  hazır listeler  kelimeyi listesine almış her kurum +3 (Bilkent, ODTÜ, Cambridge…; en çok +15)
  türev cezası    ailesinde ondan çok daha sık (≥1 Zipf) bir kelime varsa −10 (lively varken liveliness)
  az kullanılan   Word.az_kullanilan ise puan 0 (L&P'ye zaten girmez)
  ikinci tür      aynı yazımın daha düşük seviyeli başka türü varsa −15: sıklık yazıma ait, iki türe
                  bölünmez (B1 "IT" A1 "it"nin sıklığını alıyordu; yazımı zaten bilinen kelimenin ikinci türü)

Hesaplama: manage.py oncelik_hesapla (sıklık, seviye kaynağı ya da hazır listeler değişince yeniden).
"""

from collections import defaultdict

SIKLIK_PAYI = 60
KAYNAK_PAYI = {"oxford": 20, "cambridge": 12}
KURUM_PAYI, EN_COK_KURUM = 3, 5
TUREV_FARKI, TUREV_CEZASI = 1.0, 10
IKINCI_TUR_CEZASI = 15
# Kurum sayılmayan liste: bütün phrasal verb'lerin dökümü, bir kurumun seçimi değil
KURUM_DISI = ("Phrasal",)


def oncelik_puani(siklik, cefr_kaynak="learnvocab", kurum_sayisi=0, aile_en_sik=None, ikinci_tur=False):
    z = min(max(siklik if siklik is not None else 1.0, 1.0), 7.0)
    puan = (z - 1) / 6 * SIKLIK_PAYI
    puan += KAYNAK_PAYI.get(cefr_kaynak, 0)
    puan += min(kurum_sayisi, EN_COK_KURUM) * KURUM_PAYI
    if aile_en_sik is not None and aile_en_sik - z >= TUREV_FARKI:
        puan -= TUREV_CEZASI
    if ikinci_tur:
        puan -= IKINCI_TUR_CEZASI
    return round(max(puan, 0.0), 1)


def kurum_adi(liste_adi):
    """'ODTÜ 202 Span 3' -> 'ODTÜ'; kurum sayılmayan liste için None."""
    ilk = (liste_adi or "").split(" ")[0]
    return None if not ilk or ilk in KURUM_DISI else ilk


def oncelikleri_hesapla():
    """{word_id: puan} — bütün kelimeler için, veritabanından."""
    from words.models import HazirListeKelimesi, Word
    from words.siklik import SEVIYE_SIRASI

    kurumlar = defaultdict(set)
    for wid, ad in HazirListeKelimesi.objects.values_list("word_id", "liste__ad"):
        kurum = kurum_adi(ad)
        if kurum:
            kurumlar[wid].add(kurum)

    kelimeler = list(Word.objects.values_list("id", "siklik", "cefr_kaynak", "family_id", "text", "cefr"))
    az = set(Word.objects.filter(az_kullanilan=True).values_list("id", flat=True))
    aile_en_sik, yazim_en_alt = {}, {}
    for _, siklik, _, fid, text, cefr in kelimeler:
        if fid is not None and siklik is not None:
            aile_en_sik[fid] = max(aile_en_sik.get(fid, siklik), siklik)
        sira = SEVIYE_SIRASI.get(cefr, 9)
        yazim_en_alt[text.lower()] = min(yazim_en_alt.get(text.lower(), sira), sira)
    return {wid: 0.0 if wid in az else
            oncelik_puani(siklik, kaynak, len(kurumlar.get(wid, ())), aile_en_sik.get(fid),
                          ikinci_tur=SEVIYE_SIRASI.get(cefr, 9) > yazim_en_alt[text.lower()])
            for wid, siklik, kaynak, fid, text, cefr in kelimeler}
