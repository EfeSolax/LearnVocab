"""
Metnin seriye sayılıp sayılmayacağı (rapor 18.9).

Rastgele yazı yazıp günü tamamlamak engellenir. Kontroller Gemini'siz,
anında ve ücretsizdir. Geçmeyen metin yine gönderilir ve değerlendirilir;
yalnızca seriye SAYILMAZ ve kullanıcıya nedeni nazikçe söylenir.

  1. En az 5 cümle ve 50 kelime
  2. Kelimelerin en az %90'ı gerçek İngilizce kelime
  3. Aynı cümle ya da kelime kopyalanıp çoğaltılmamış
  4. Anlamsız harf dizileri yok ("asdfgh", "aaaaaa")
  5. Kullanıcının önceki bir metninin kopyası değil
"""

import re
from difflib import SequenceMatcher

EN_AZ_CUMLE = 5
EN_AZ_KELIME = 50
EN_AZ_INGILIZCE_ORANI = 0.90
EN_AZ_FARKLI_KELIME_ORANI = 0.40   # 50 kelimenin en az 20'si farklı olmalı
KOPYA_BENZERLIGI = 0.90

_KELIME = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
_CUMLE_SONU = re.compile(r"[.!?]+(?:\s|$)")
_ANLAMSIZ = re.compile(r"(.)\1{3,}|^[^aeiouy]{6,}$", re.IGNORECASE)


def _normal(metin):
    return " ".join(_KELIME.findall((metin or "").lower()))


def _ingilizce_mi(kelime):
    from wordfreq import zipf_frequency
    if zipf_frequency(kelime, "en") > 0:
        return True
    from words.models import Word, WordForm
    return (Word.objects.filter(text__iexact=kelime).exists()
            or WordForm.objects.filter(surface__iexact=kelime).exists())


def seriye_sayilir_mi(user, metin, haric_id=None):
    """(sayılır mı, neden) — neden kullanıcıya gösterilecek kısa Türkçe cümle."""
    kelimeler = _KELIME.findall(metin or "")
    cumleler = [c.strip() for c in _CUMLE_SONU.split(metin or "") if _KELIME.search(c)]

    if len(cumleler) < EN_AZ_CUMLE or len(kelimeler) < EN_AZ_KELIME:
        return False, (f"Metnin seriye sayılması için en az {EN_AZ_CUMLE} cümle ve "
                       f"{EN_AZ_KELIME} kelime olmalı.")

    kucuk = [k.lower() for k in kelimeler]
    if any(_ANLAMSIZ.search(k) for k in kucuk if len(k) >= 4):
        return False, "Metinde anlamsız harf dizileri var; bu yüzden seriye sayılmadı."

    farkli = set(kucuk)
    if len(farkli) / len(kucuk) < EN_AZ_FARKLI_KELIME_ORANI:
        return False, "Aynı kelimeler çok tekrar ediyor; bu yüzden seriye sayılmadı."
    normal_cumleler = [_normal(c) for c in cumleler]
    if len(set(normal_cumleler)) < len(normal_cumleler):
        return False, "Aynı cümle birden çok kez yazılmış; bu yüzden seriye sayılmadı."

    ingilizce = {k for k in farkli if _ingilizce_mi(k)}
    if sum(1 for k in kucuk if k in ingilizce) / len(kucuk) < EN_AZ_INGILIZCE_ORANI:
        return False, "Metnin çoğu İngilizce kelimelerden oluşmalı; bu yüzden seriye sayılmadı."

    from .models import Text
    yeni = _normal(metin)
    onceki = Text.objects.filter(owner=user)
    if haric_id:
        onceki = onceki.exclude(pk=haric_id)
    for eski in onceki.only("content").order_by("-id")[:200]:
        if SequenceMatcher(None, _normal(eski.content), yeni).ratio() >= KOPYA_BENZERLIGI:
            return False, "Bu metin daha önce yazdığın bir metne çok benziyor; seriye sayılmadı."
    return True, ""
