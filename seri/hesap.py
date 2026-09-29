"""
Seri kuralı (rapor 18.9).

Günü tamamlayan (seriyi devam ettiren) şeyler, başka hiçbir şey sayılmaz:
  - 10 L&P kartı  YA DA  10 egzersiz sorusu (toplanmaz; biri tek başına 10)
  - YA DA 1 geçerli metin (texts/gecerlilik.py)  YA DA 1 cevaplanan diyalog
Gün kullanıcının YEREL saatiyle 00.00'da biter (seri/zaman.py).

Dondurma hakkı: herkes 1 ile başlar; ardışık 5 tamamlanan günde +1; en çok 3.
Kaçırılan gün, hak varsa otomatik dondurulur (seri bozulmaz ama artmaz) ve
ardışık sayacı sıfırlar. Hak yoksa seri bozulur. Serisi 0 olan kullanıcının
kaçırdığı gün hak harcatmaz (koruyacak seri yok).

İşleme tembel: kaçırılan günler bir sonraki okumada (durum / say) işlenir;
tamamlanan gün, tamamlandığı anda işlenir.
"""

from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import GunlukCalisma, SeriDurumu
from .zaman import yerel_gun

LP, EGZERSIZ, METIN, DIYALOG = "lp", "egzersiz", "metin", "diyalog"
ESIK = {LP: 10, EGZERSIZ: 10, METIN: 1, DIYALOG: 1}
EN_COK_HAK = 3
HAK_ICIN_ARDISIK = 5


def _durum_satiri(user):
    durum, _ = SeriDurumu.objects.get_or_create(user=user)
    return durum


def _tamam_mi(satir):
    return any(getattr(satir, tur) >= esik for tur, esik in ESIK.items())


def _gunu_isle_tamam(durum, gun):
    durum.mevcut += 1
    durum.en_uzun = max(durum.en_uzun, durum.mevcut)
    durum.ardisik += 1
    if durum.ardisik >= HAK_ICIN_ARDISIK:
        durum.hak = min(EN_COK_HAK, durum.hak + 1)
        durum.ardisik = 0
    durum.son_islenen_gun = gun


def guncelle(user, bugun=None):
    """Son işlenen günden dünkü güne kadar kaçırılan günleri işler."""
    bugun = bugun or yerel_gun(user)
    with transaction.atomic():
        durum = SeriDurumu.objects.select_for_update().get_or_create(user=user)[0]
        if durum.son_islenen_gun is None:
            # İlk kez: geçmiş yok, bugünden başlanır.
            durum.son_islenen_gun = bugun - timedelta(days=1)
            durum.save()
            return durum
        gun = durum.son_islenen_gun + timedelta(days=1)
        degisti = False
        while gun < bugun:
            if durum.mevcut > 0:
                if durum.hak > 0:
                    durum.hak -= 1
                    GunlukCalisma.objects.update_or_create(user=user, gun=gun,
                                                           defaults={"dondurulan": True})
                else:
                    durum.mevcut = 0
            durum.ardisik = 0
            durum.son_islenen_gun = gun
            degisti = True
            gun += timedelta(days=1)
        if degisti:
            durum.save()
        return durum


def bugun(user):
    """Bugünkü sayaçlar (alevli çubuk için): {lp, egzersiz, tamamlandi, esik}."""
    satir = GunlukCalisma.objects.filter(user=user, gun=yerel_gun(user)).first()
    return {
        "lp": satir.lp if satir else 0,
        "egzersiz": satir.egzersiz if satir else 0,
        "tamamlandi": bool(satir and satir.tamamlandi),
        "esik": ESIK[LP],
    }


def say(user, tur, adet=1):
    """
    Bir çalışmayı bugüne sayar; gün bu sayede tamamlandıysa seriyi işler.
    Döner: bugün() + {"yeni_tamamlandi": bool, "mevcut": seri}.
    """
    gun = yerel_gun(user)
    durum = guncelle(user, gun)
    yeni_tamamlandi = False
    with transaction.atomic():
        satir, _ = GunlukCalisma.objects.select_for_update().get_or_create(user=user, gun=gun)
        GunlukCalisma.objects.filter(pk=satir.pk).update(**{tur: F(tur) + adet})
        satir.refresh_from_db()
        if not satir.tamamlandi and _tamam_mi(satir):
            satir.tamamlandi = True
            satir.tamamlandi_at = timezone.now()
            satir.dondurulan = False
            satir.save(update_fields=["tamamlandi", "tamamlandi_at", "dondurulan"])
            durum = SeriDurumu.objects.select_for_update().get(pk=durum.pk)
            if durum.son_islenen_gun != gun:
                _gunu_isle_tamam(durum, gun)
                durum.save()
            yeni_tamamlandi = True
    sonuc = bugun(user)
    sonuc.update({"yeni_tamamlandi": yeni_tamamlandi,
                  "mevcut": SeriDurumu.objects.get(user=user).mevcut})
    return sonuc


def geri_al(user, tur, adet=1):
    """Geri alınan bir çalışmayı sayaçtan düşer; tamamlanmış gün geri alınmaz."""
    GunlukCalisma.objects.filter(user=user, gun=yerel_gun(user), **{f"{tur}__gte": adet}).update(
        **{tur: F(tur) - adet})
    return bugun(user)


def durum(user):
    """Ana Sayfa'daki seri kutusu ve açılır kutu için özet."""
    d = guncelle(user)
    b = bugun(user)
    return {
        "mevcut": d.mevcut,
        "en_uzun": d.en_uzun,
        "hak": d.hak,
        "en_cok_hak": EN_COK_HAK,
        "bugun_tamam": b["tamamlandi"],
        "bozuldu": d.mevcut == 0,
    }


def takvim(user, yil, ay):
    """{gün numarası: "tamam" | "dondurulan"} — takvimde renkler (18.9)."""
    satirlar = GunlukCalisma.objects.filter(user=user, gun__year=yil, gun__month=ay).filter(
        tamamlandi=True) | GunlukCalisma.objects.filter(
        user=user, gun__year=yil, gun__month=ay, dondurulan=True)
    return {s.gun.day: ("tamam" if s.tamamlandi else "dondurulan") for s in satirlar}
