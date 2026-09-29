"""
Ana Sayfa (ürün raporu 3; girişsiz ziyaretçi 2.3). Adres: "/" (url adı `index`).

Girişli kullanıcı:
  - Seri (rapor 18.9): sayı + kapibara; dokununca takvimli kutu (seri/hesap.py).
  - Listemdeki kelime sayısı: TEK sayısal gösterge ("öğrenilen kelime" yok, Bölüm 17).
  - Büyük "Bugünün çalışmasına başla" -> Learn & Pass.
  - Günün kelimesi ve günün ifadesi: Sözlük'teki kartların küçük hâli. İçerik
    Sözlük ile aynı kaynaktan (words.arama.gunun_kelimesi / gunun_ifadesi);
    dokununca Sözlük'te ilgili kart açılır (/sozluk/?q=…).
  - Seviye testi daveti her sayfada ayrı çıkar (seviye/baglam.py, rapor 18.27).
  - Yardım bağlantısı (içerik Bölüm 16: şimdilik Hakkında sayfası).

Girişsiz ziyaretçi: kısa tanıtım, Learn & Pass'e başla (misafir), Sözlük'te
ara, günün kelimesi (B1).
"""

from django.shortcuts import render

from seri import hesap as seri_hesap
from words import arama
from words.kart import kart_verisi
from words.models import UserWordLink


def ana_sayfa(request):
    user = request.user
    kelime = arama.gunun_kelimesi(user)
    baglam = {
        "active_page": "Ana Sayfa",
        "gunun_karti": kart_verisi([kelime], user)[0] if kelime else None,
    }
    if user.is_authenticated:
        baglam.update({
            "liste_sayisi": UserWordLink.objects.filter(user=user).count(),
            "gunun_ifadesi": arama.gunun_ifadesi(user),
            "seri": seri_hesap.durum(user),
        })
    return render(request, "pages/index.html", baglam)
