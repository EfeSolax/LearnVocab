"""
Ana Sayfa (ürün raporu 3; girişsiz ziyaretçi 2.3). Adres: "/" (url adı `index`).

Girişli kullanıcı:
  - Seri (rapor 18.9): sayı + kapibara; dokununca takvimli kutu (seri/hesap.py).
  - Listemdeki kelime sayısı: TEK sayısal gösterge ("öğrenilen kelime" yok, Bölüm 17).
  - Büyük "Bugünün çalışmasına başla" -> Learn & Pass.
  - Günün kelimesi ve günün ifadesi (rapor 18.8): iki ayrı kart; Sözlük ›
    Keşfet'tekiyle aynı (words/gunun.py, pages/gunun/). Misafir de görür.
  - Seviye testi daveti her sayfada ayrı çıkar (seviye/baglam.py, rapor 18.27).
  - Yardım bağlantısı (içerik Bölüm 16: şimdilik Hakkında sayfası).

Girişsiz ziyaretçi: defter temalı tanıtım sayfası (rapor 18.12; örnek
ozetler/tasarim-ornekleri/defter/index.html): başlık, misafir L&P, Sözlük'te
ara, katlanan defter tablosu (words.gunun.defter_kelimeleri), günün kelimesi
ve ifadesi, seri, "Defterin yapamadığı dört şey", kütüphaneden üç okuma,
A1–C2 sekmeleri, bir hazır liste, sık sorulanlar.
"""

from django.shortcuts import render

from readings.models import ReadingText
from seri import hesap as seri_hesap
from words import gunun
from words.kart import kart_verisi
from words.models import CEFR_LEVELS, HazirListe, UserWordLink

# Seviye sekmeleri (misafir ana sayfası): kısa, abartısız tarifler.
SEVIYE_TARIFLERI = {
    "A1": "en temel kelimeler", "A2": "günlük hayat", "B1": "hazırlığın ilk dönemi",
    "B2": "okuma metinleri, sınavlar", "C1": "akademik metinler", "C2": "ince ayrıntılar",
}


def ana_sayfa(request):
    user = request.user
    baglam = {
        "active_page": "Ana Sayfa",
        "gunun_kelimesi": gunun.kelime_durumu(user),
        "gunun_ifadesi": gunun.ifade_durumu(user),
    }
    if user.is_authenticated:
        baglam.update({
            "liste_sayisi": UserWordLink.objects.filter(user=user).count(),
            "seri": seri_hesap.durum(user),
        })
    else:
        baglam.update(_misafir_baglami())
    return render(request, "pages/index.html", baglam)


def _misafir_baglami():
    liste = HazirListe.objects.filter(yayinda=True).first()
    return {
        "defter_kartlari": kart_verisi(gunun.defter_kelimeleri()),
        "okumalar": list(ReadingText.objects.order_by("number")[:3]),
        "seviyeler": [(s, SEVIYE_TARIFLERI.get(s, "")) for s in CEFR_LEVELS],
        "hazir_liste": liste,
        "hazir_liste_kelimeleri": list(liste.kelimeler.order_by("hazir_liste_uyelikleri__sira")[:8]) if liste else [],
        "hazir_liste_sayisi": liste.kelimeler.count() if liste else 0,
    }
