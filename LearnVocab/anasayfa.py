"""
Ana Sayfa (ürün raporu 3; girişsiz ziyaretçi 2.3; defter teması 18.12).
Adres: "/" (url adı `index`). Örnek tasarım: ozetler/tasarim-ornekleri/defter/index.html

Misafir de girişli kullanıcı da AYNI zengin defter sayfasını görür; girişlide
bölümler kendi verisiyle dolar:

  Giriş          tarih, "Yardım ve hakkında" (hep görünür), selam ya da misafir başlığı, kelime ara
  Seri kartı     kapibara + seri (dokununca takvim) + bu hafta; girişli: bekleyen tekrar ve
                 "Bugünün çalışmasına başla"; misafir: "Hesap açmadan dene" ve örnek hafta
  Bugünün sayfası günün kelimesi ve ifadesi (rapor 18.8), yapışkan not
  Hemen başla    dört kutu: Sözlük · Çalış · Oku · Yaz (tek satır açıklamalı)
  Defter tablosu misafir: o günün 5 kelimesi (words.gunun.defter_kelimeleri), kaydedilmez
                 girişli: tekrar sırasındaki ilk 5 kelime (yoksa günün 5 kelimesi);
                 "biliyordum / bilmiyordum" Learn & Pass'e kaydedilir (learn_pass_verdict)
  Eklenti        Chrome eklentisi: çift tıkla, anlamı gör (rapor 11; Web Store adresi EKLENTI_ADRESI)
  Okumalar       kütüphaneden üç metin
  Hazır liste    iki örnek yan yana: Academic Word List ve Cambridge B1 Preliminary
  Seviye         A1–C2 sekmeleri (girişlide kendi seviyesi işaretli) + seviye testi
  Misafir        sık sorulanlar ve hesap çağrısı

Bölüm 17 gereği "öğrenilen kelime" gibi sayılardan söz edilmez.
"""

import random
from datetime import timedelta

from django.conf import settings
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
# Ana sayfadaki örnek hazır listeler, soldan sağa (Efe, 17 Ekim).
ORNEK_LISTELER = ("more-to-read-ii-awl", "cambridge-b1-preliminary")
ORNEK_KELIME = 8
TAKVIM_HAFTA = 5


def ana_sayfa(request):
    user = request.user
    baglam = {
        "eklenti_adresi": settings.EKLENTI_ADRESI,      # rapor 11: Chrome eklentisi bölümü
        "active_page": "Ana Sayfa",
        "gunun_kelimesi": gunun.kelime_durumu(user),
        "gunun_ifadesi": gunun.ifade_durumu(user),
        "okumalar": list(ReadingText.objects.order_by("number")[:3]),
        "seviyeler": [(s, SEVIYE_TARIFLERI.get(s, "")) for s in CEFR_LEVELS],
        "ornek_listeler": _ornek_listeler(),
    }
    if user.is_authenticated:
        baglam.update(_girisli_baglam(user))
    else:
        baglam["defter_kartlari"] = kart_verisi(gunun.defter_kelimeleri())
        baglam["defter_kaynak"] = ""
    return render(request, "pages/index.html", baglam)


def _ornek_listeler():
    """[{"liste", "kelimeler" (ilk 8), "kalan"}]; örneklerin hiçbiri yayında değilse yayındaki ilk liste."""
    yayinda = HazirListe.objects.filter(yayinda=True)
    listeler = {l.slug: l for l in yayinda.filter(slug__in=ORNEK_LISTELER)}
    sirali = [listeler[s] for s in ORNEK_LISTELER if s in listeler] or list(yayinda[:1])
    sonuc = []
    for l in sirali:
        kelimeler, gorulen = [], set()      # aynı yazımın iki türü (about edat/zarf) bir kez
        for w in l.kelimeler.order_by("hazir_liste_uyelikleri__sira")[:ORNEK_KELIME * 3]:
            if w.text.lower() not in gorulen and len(kelimeler) < ORNEK_KELIME:
                gorulen.add(w.text.lower())
                kelimeler.append(w)
        sonuc.append({"liste": l, "kelimeler": kelimeler,
                      "kalan": max(l.kelimeler.count() - len(kelimeler), 0)})
    return sonuc


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
