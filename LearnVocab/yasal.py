"""
KVKK aydınlatma metni ve gizlilik (rapor 18.19). Adres: /gizlilik/ (url adı `gizlilik`).

Metin hukuki bir belge olduğu için çeviri dosyasına (django.po) bölünmez: her dilin
kendi şablonu var (pages/yasal/aydinlatma_<dil>.html). Türkçe metin asıldır; diğer
diller bilgi içindir. Metin değişince GUNCELLEME tarihi de değişir.
"""

from django.conf import settings
from django.shortcuts import render
from django.utils.translation import get_language

GUNCELLEME = "10 Ekim 2026"
DILLER = {"tr", "en"}


def iletisim_epostasi():
    return settings.KVKK_ILETISIM_EPOSTASI or settings.DEFAULT_FROM_EMAIL or ""


def aydinlatma(request):
    dil = (get_language() or "tr")[:2]
    return render(request, f"pages/yasal/aydinlatma_{dil if dil in DILLER else 'tr'}.html", {
        "veri_sorumlusu": settings.KVKK_VERI_SORUMLUSU,
        "eposta": iletisim_epostasi(),
        "guncelleme": GUNCELLEME,
    })
