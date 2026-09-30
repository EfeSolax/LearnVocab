"""
Admin istatistik ekranı (rapor 18.31): /admin/istatistik/ (yalnızca yönetici).

Amaç: tekrar biriminin (1 gün, rapor 18.2) ve genel kullanımın doğru çalışıp
çalışmadığını görmek.

GİZLİLİK: Ekranda YALNIZCA TOPLU SAYILAR vardır. Kullanıcı adı, e-posta,
metin ya da kişi bazında satır yoktur. Bir göstergenin arkasında 5'ten az
kişi varsa oran gösterilmez; 5'ten küçük sayılar "<5" yazılır.

Göstergeler:
  1. Aktif kullanıcılar (günlük / haftalık / aylık) ve son 14 gün
  2. Tekrar basamağı başına unutma oranı (1 · 3 · 7 · 21 gün)
  3. Günün tamamlanma oranı (son 30 gün)
  4. Yarıda bırakma: L&P'de 10 karta ulaşmayan günler; egzersiz oturumları
  5. Seri uzunluğu dağılımı
  6. Bildirim izni: ölçütü sağlayanların yüzde kaçı bildirimi açtı
Kaynak: learnpass.EncounterLog (son 90 gün) + KarsilasmaOzeti (daha eskisi).
"""

from collections import defaultdict
from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, F, Q, Sum
from django.shortcuts import render
from django.utils import timezone

EN_AZ_KISI = 5

BILINDI = ("known", "dogru")
BILINMEDI = ("unknown", "misjudged", "yanlis")
BASAMAK_ADLARI = {1: "1. tekrar (1 gün sonra)", 2: "2. tekrar (3 gün sonra)",
                  3: "3. tekrar (7 gün sonra)", 4: "4. tekrar (21 gün sonra)",
                  5: "5. ve sonrası (21 günde bir)"}


def sayi(n):
    """Küçük sayılar kişiyi belli edebilir: 1–4 -> '<5'."""
    return f"<{EN_AZ_KISI}" if 0 < n < EN_AZ_KISI else str(n)


def oran(pay, payda, kisi):
    """Yüzde; arkasında 5'ten az kişi varsa None (gösterilmez)."""
    if kisi < EN_AZ_KISI or not payda:
        return None
    return round(100 * pay / payda)


def aktif_kullanicilar(bugun):
    from seri.models import GunlukCalisma
    aktif = GunlukCalisma.objects.filter(Q(lp__gt=0) | Q(egzersiz__gt=0) | Q(metin__gt=0) | Q(diyalog__gt=0))

    def kac(gun_sayisi):
        return aktif.filter(gun__gt=bugun - timedelta(days=gun_sayisi)).values("user").distinct().count()

    gunluk = dict(aktif.filter(gun__gt=bugun - timedelta(days=14))
                  .values_list("gun").annotate(n=Count("user", distinct=True)))
    return {
        "gunluk": sayi(kac(1)), "haftalik": sayi(kac(7)), "aylik": sayi(kac(30)),
        "son_14_gun": [(bugun - timedelta(days=i), sayi(gunluk.get(bugun - timedelta(days=i), 0)))
                       for i in range(13, -1, -1)],
    }


def unutma_oranlari():
    from learnpass.models import EncounterLog, KarsilasmaOzeti
    sayac = defaultdict(lambda: [0, 0])          # basamak -> [toplam, bilinmedi]

    def ekle(basamak, verdict, n):
        if basamak < 1 or verdict not in BILINDI + BILINMEDI:
            return
        b = min(basamak, 5)
        sayac[b][0] += n
        if verdict in BILINMEDI:
            sayac[b][1] += n

    for r in EncounterLog.objects.values("basamak_once", "verdict").annotate(n=Count("id")):
        ekle(r["basamak_once"], r["verdict"], r["n"])
    for r in KarsilasmaOzeti.objects.values("basamak_once", "verdict").annotate(n=Sum("sayi")):
        ekle(r["basamak_once"], r["verdict"], r["n"])
    kisi = (EncounterLog.objects.filter(basamak_once__gte=1).values("user").distinct().count())
    return [{"ad": BASAMAK_ADLARI[b], "toplam": sayi(sayac[b][0]),
             "oran": oran(sayac[b][1], sayac[b][0], kisi)} for b in range(1, 6)], kisi


def gun_tamamlama(bugun):
    from seri.models import GunlukCalisma
    q = GunlukCalisma.objects.filter(gun__gt=bugun - timedelta(days=30), dondurulan=False) \
        .filter(Q(lp__gt=0) | Q(egzersiz__gt=0) | Q(metin__gt=0) | Q(diyalog__gt=0))
    kisi = q.values("user").distinct().count()
    toplam, tamam = q.count(), q.filter(tamamlandi=True).count()
    return {"gun": sayi(toplam), "oran": oran(tamam, toplam, kisi)}


def yarida_birakma(bugun):
    from egzersizler.models import EgzersizOturumu
    from seri.hesap import ESIK, LP
    from seri.models import GunlukCalisma
    lp = GunlukCalisma.objects.filter(gun__gt=bugun - timedelta(days=30), lp__gt=0)
    lp_kisi = lp.values("user").distinct().count()
    egz = EgzersizOturumu.objects.filter(durum__in=(EgzersizOturumu.DURUM_BITTI,
                                                    EgzersizOturumu.DURUM_BIRAKILDI))
    egz_kisi = egz.values("user").distinct().count()
    return {
        "lp_esik": ESIK[LP],
        "lp_gun": sayi(lp.count()),
        "lp_oran": oran(lp.filter(lp__lt=ESIK[LP]).count(), lp.count(), lp_kisi),
        "egz_oturum": sayi(egz.count()),
        "egz_oran": oran(egz.filter(durum=EgzersizOturumu.DURUM_BIRAKILDI).count(), egz.count(), egz_kisi),
    }


SERI_ARALIKLARI = ((0, 0, "0"), (1, 2, "1–2 gün"), (3, 6, "3–6 gün"), (7, 13, "1–2 hafta"),
                   (14, 29, "2–4 hafta"), (30, 10**9, "30 gün ve üstü"))


def seri_dagilimi():
    from seri.models import SeriDurumu
    q = SeriDurumu.objects.all()
    toplam = q.count()
    satirlar = [{"ad": ad, "sayi": sayi(q.filter(mevcut__gte=a, mevcut__lte=b).count())}
                for a, b, ad in SERI_ARALIKLARI]
    return {"kisi": sayi(toplam), "satirlar": satirlar if toplam >= EN_AZ_KISI else []}


def bildirim_kabulu():
    from bildirimler.baglam import EN_AZ_EGZERSIZ, EN_AZ_LP_KARTI
    from bildirimler.models import PushAboneligi
    from egzersizler.models import EgzersizOturumu
    from learnpass.models import WordEncounter
    egz = set(EgzersizOturumu.objects.filter(durum=EgzersizOturumu.DURUM_BITTI).values("user")
              .annotate(n=Count("id")).filter(n__gte=EN_AZ_EGZERSIZ).values_list("user", flat=True))
    lp = set(WordEncounter.objects.values("user")
             .annotate(n=Sum(F("known_count") + F("unknown_count") + F("misjudged_count")))
             .filter(n__gte=EN_AZ_LP_KARTI).values_list("user", flat=True))
    uygun = egz & lp
    acan = set(PushAboneligi.objects.filter(user__in=uygun).values_list("user", flat=True))
    return {"uygun": sayi(len(uygun)), "oran": oran(len(acan), len(uygun), len(uygun))}


def hesapla():
    bugun = timezone.localdate()
    unutma, unutma_kisi = unutma_oranlari()
    return {
        "aktif": aktif_kullanicilar(bugun),
        "unutma": unutma, "unutma_kisi": sayi(unutma_kisi),
        "tamamlama": gun_tamamlama(bugun),
        "birakma": yarida_birakma(bugun),
        "seri": seri_dagilimi(),
        "bildirim": bildirim_kabulu(),
        "en_az_kisi": EN_AZ_KISI,
    }


@staff_member_required
def istatistik(request):
    from django.contrib import admin
    return render(request, "admin/istatistik.html", {
        **admin.site.each_context(request),
        "title": "İstatistikler",
        "ist": hesapla(),
    })
