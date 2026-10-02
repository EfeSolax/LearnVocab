"""
Ana Sayfa (ürün raporu 3; girişsiz ziyaretçi 2.3; defter teması 18.12).
Adres: "/" (url adı `index`). Örnek tasarım: ozetler/tasarim-ornekleri/defter/index.html

Misafir de girişli kullanıcı da AYNI zengin defter sayfasını görür; girişlide
bölümler kendi verisiyle dolar:

  Giriş          misafir: "Kelime defterin, bu sefer yarıda kalmasın."
                 girişli: selam, bekleyen tekrar sayısı, seri, "Bugünün çalışmasına başla"
  Defter tablosu misafir: o günün 5 kelimesi (words.gunun.defter_kelimeleri), kaydedilmez
                 girişli: tekrar sırasındaki ilk 5 kelime (yoksa günün 5 kelimesi);
                 "biliyordum / bilmiyordum" Learn & Pass'e kaydedilir (learn_pass_verdict)
  Bugünün sayfası günün kelimesi ve ifadesi (rapor 18.8), yapışkan not
  Seri           misafir: açıkça "örnek" yazan takvim; girişli: gerçek son beş hafta (18.9)
  Misafir        "Defterin yapamadığı dört şey"; girişli: "Bugün başka ne yapsan?"
  Okumalar       kütüphaneden üç metin
  Seviye         A1–C2 sekmeleri (girişlide kendi seviyesi işaretli) + seviye testi
  Hazır liste    yayındaki ilk liste
  Misafir        sık sorulanlar ve hesap çağrısı

Bölüm 17 gereği "öğrenilen kelime" gibi sayılardan söz edilmez.
"""

import random
from datetime import timedelta

from django.db.models import Q
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from readings.models import ReadingText
from seri import hesap as seri_hesap
from users.seviye import kullanici_seviyesi
from words import gunun
from words.kart import kart_verisi
from words.models import CEFR_LEVELS, HazirListe, UserWordLink

# Seviye sekmeleri: kısa, abartısız tarifler.
SEVIYE_TARIFLERI = {
    "A1": _("en temel kelimeler"), "A2": _("günlük hayat"), "B1": _("hazırlığın ilk dönemi"),
    "B2": _("okuma metinleri, sınavlar"), "C1": _("akademik metinler"), "C2": _("ince ayrıntılar"),
}
TABLO_ADET = 5
TAKVIM_HAFTA = 5


def ana_sayfa(request):
    user = request.user
    liste = HazirListe.objects.filter(yayinda=True).first()
    baglam = {
        "active_page": "Ana Sayfa",
        "gunun_kelimesi": gunun.kelime_durumu(user),
        "gunun_ifadesi": gunun.ifade_durumu(user),
        "okumalar": list(ReadingText.objects.order_by("number")[:3]),
        "seviyeler": [(s, SEVIYE_TARIFLERI.get(s, "")) for s in CEFR_LEVELS],
        "hazir_liste": liste,
        "hazir_liste_kelimeleri": (list(liste.kelimeler.order_by("hazir_liste_uyelikleri__sira")[:8])
                                   if liste else []),
        "hazir_liste_sayisi": liste.kelimeler.count() if liste else 0,
    }
    if user.is_authenticated:
        baglam.update(_girisli_baglam(user))
    else:
        baglam["defter_kartlari"] = kart_verisi(gunun.defter_kelimeleri())
        baglam["defter_kaynak"] = ""
    return render(request, "pages/index.html", baglam)


def _girisli_baglam(user):
    from learnpass import tekrar
    from learnpass.models import WordEncounter
    from seri.models import GunlukCalisma
    from seri.zaman import yerel_gun

    # Defter tablosu: bugünün tekrarı. Sıra gün boyunca sabit kalsın diye tohumlu.
    bugun = yerel_gun(user)
    sira = tekrar.tekrar_sirasi(user, rng=random.Random(f"{user.pk}:{bugun.isoformat()}"))[:TABLO_ADET]
    if sira:
        kartlar, kaynak = kart_verisi(sira, user), WordEncounter.MODE_MINE
    else:
        kartlar, kaynak = kart_verisi(gunun.defter_kelimeleri(), user), WordEncounter.MODE_NEW

    # Seri takvimi: son beş hafta (pazartesiden başlar), gerçek günler.
    bas = bugun - timedelta(days=bugun.weekday() + 7 * (TAKVIM_HAFTA - 1))
    durumlar = {g.gun: ("tamam" if g.tamamlandi else "dondurulan")
                for g in GunlukCalisma.objects.filter(user=user, gun__gte=bas, gun__lte=bugun)
                .filter(Q(tamamlandi=True) | Q(dondurulan=True))}
    takvim = []
    for i in range(7 * TAKVIM_HAFTA):
        gun = bas + timedelta(days=i)
        takvim.append({"gun": gun.day, "durum": durumlar.get(gun, ""),
                       "bugun": gun == bugun, "gelecek": gun > bugun})

    return {
        "defter_kartlari": kartlar,
        "defter_kaynak": kaynak,
        "liste_sayisi": UserWordLink.objects.filter(user=user).count(),
        "bekleyen_tekrar": tekrar.bekleyen_tekrar_sayisi(user),
        "seri": seri_hesap.durum(user),
        "takvim": takvim,
        "kullanici_seviyesi": kullanici_seviyesi(user),
    }
