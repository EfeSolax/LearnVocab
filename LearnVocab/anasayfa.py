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

Girişsiz ziyaretçi: kısa tanıtım, Learn & Pass'e başla (misafir), Sözlük'te
ara, günün kelimesi (B1) ve günün ifadesi.
"""

from django.shortcuts import render

from seri import hesap as seri_hesap
from words import gunun
from words.models import UserWordLink


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
    return render(request, "pages/index.html", baglam)
