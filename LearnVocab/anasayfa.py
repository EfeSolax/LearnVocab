"""
Ana Sayfa (ürün raporu 3; girişsiz ziyaretçi 2.3). Adres: "/" (url adı `index`).

Girişli kullanıcı:
  - Seri için yer (nasıl sayılacağı Bölüm 16'da; şimdilik nötr yer tutucu).
  - Listemdeki kelime sayısı: TEK sayısal gösterge ("öğrenilen kelime" yok, Bölüm 17).
  - Büyük "Bugünün çalışmasına başla" -> Learn & Pass.
  - Günün kelimesi ve günün ifadesi: Sözlük'teki kartların küçük hâli. İçerik
    Sözlük ile aynı kaynaktan (words.arama.gunun_kelimesi / gunun_ifadesi);
    dokununca Sözlük'te ilgili kart açılır (/sozluk/?q=…).
  - Seviyesi belirlenmemişse nazik bir seviye testi davet kartı (zorunlu değil).
  - Yardım bağlantısı (içerik Bölüm 16: şimdilik Hakkında sayfası).

Girişsiz ziyaretçi: kısa tanıtım, Learn & Pass'e başla (misafir), Sözlük'te
ara, günün kelimesi (B1).
"""

from django.shortcuts import render

from seviye.views import davet_gosterilsin_mi
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
            "seviye_daveti": davet_gosterilsin_mi(request),
        })
    return render(request, "pages/index.html", baglam)
