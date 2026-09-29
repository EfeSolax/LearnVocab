"""
Seri hatırlatmaları (rapor 18.9, 18.32).

Günde iki zaman, kullanıcının YEREL saatiyle:
  12.00  "Günün kelimesi: … · Bugünün çalışması seni bekliyor"
  23.45  seriyi kaçırma uyarısı (dondurma hakkı varsa onu söyler)
Kullanıcı o günü tamamladıysa ya da serisi 0 ise bildirim gitmez.

Sunucuda cron en sık 15 dakikada bir çalışır (Veridyen), bu yüzden komut
her 15 dakikada bir çalıştırılır ve saati 12.00–12.15 ya da 23.45–24.00
aralığında olan kullanıcılara gönderir (bkz. bildirimler/CRON.md):

    */15 * * * *  ... manage.py bildirim_gonder_hatirlatma

Aynı gün aynı bildirim ikinci kez gitmez (GunlukHatirlatma kaydı).
"""

from datetime import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from bildirimler import ayar, gonder
from bildirimler.models import GunlukHatirlatma, PushAboneligi
from seri import hesap as seri_hesap
from seri.zaman import yerel_simdi

PENCERELER = {
    GunlukHatirlatma.OGLE: (time(12, 0), time(12, 15)),
    GunlukHatirlatma.GECE: (time(23, 45), time(23, 59, 59, 999999)),
}
BASLIK = "LearnVocab"


def zaman_dilimi(yerel):
    """Yerel saat bir bildirim penceresine düşüyorsa türü, yoksa None."""
    saat = yerel.timetz().replace(tzinfo=None)
    for tur, (bas, bit) in PENCERELER.items():
        if bas <= saat <= bit:
            return tur
    return None


def mesaj(user, tur, durum):
    if tur == GunlukHatirlatma.OGLE:
        from words.arama import gunun_kelimesi
        kelime = gunun_kelimesi(user)
        on = f"Günün kelimesi: {kelime.text} · " if kelime else ""
        return f"{on}Bugünün çalışması seni bekliyor."
    if durum["hak"] > 0:
        return "Bugün çalışmazsan 1 dondurma hakkın kullanılacak."
    return f"{durum['mevcut']} günlük serin gece yarısı bitiyor. Kısa bir tur yeter!"


def gonderilecekler(simdi=None):
    """[(user, tur, gun, govde)] — şu an bildirim alması gerekenler."""
    simdi = simdi or timezone.now()
    User = get_user_model()
    abone = PushAboneligi.objects.values("user_id").distinct()
    sonuc = []
    for user in User.objects.filter(id__in=abone):
        yerel = yerel_simdi(user, simdi)
        tur = zaman_dilimi(yerel)
        if tur is None:
            continue
        durum = seri_hesap.durum(user)
        if durum["mevcut"] == 0 or durum["bugun_tamam"]:
            continue
        if GunlukHatirlatma.objects.filter(user=user, gun=yerel.date(), tur=tur).exists():
            continue
        sonuc.append((user, tur, yerel.date(), mesaj(user, tur, durum)))
    return sonuc


class Command(BaseCommand):
    help = "Seri hatırlatmaları: yerel 12.00 ve 23.45 (her 15 dakikada bir çalıştır)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Yalnızca kime ne gideceğini yaz.")

    def handle(self, *args, **opts):
        if not ayar.acik():
            self.stdout.write("VAPID anahtarı yok; bildirimler kapalı, hiçbir şey gönderilmedi.")
            return
        liste = gonderilecekler()
        if opts["dry_run"]:
            for user, tur, _, govde in liste:
                self.stdout.write(f"{user} [{tur}]: {govde}")
            self.stdout.write(f"{len(liste)} bildirim gidecekti (dry-run).")
            return
        url = reverse("learn_pass_page")
        ulasan = 0
        for user, tur, gun, govde in liste:
            # Önce kayıt: iki çalıştırma üst üste binse bile ikinci bildirim gitmez.
            try:
                with transaction.atomic():
                    kayit = GunlukHatirlatma.objects.create(user=user, gun=gun, tur=tur)
            except IntegrityError:
                continue
            kayit.gonderilen = gonder.kullaniciya(user, BASLIK, govde, url)
            kayit.save(update_fields=["gonderilen"])
            ulasan += bool(kayit.gonderilen)
        self.stdout.write(f"Hatırlatma: {len(liste)} aday, {ulasan} kullanıcıya ulaştı.")
