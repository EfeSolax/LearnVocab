"""
Günlük Learn & Pass hatırlatması (rapor 10).

Bugün L&P'de hiç kaydırma yapmamış abonelere günde EN ÇOK BİR bildirim
gönderir. Cron ile her akşam bir kez çalıştırılır (bkz. bildirimler/CRON.md):

    0 19 * * *  ... manage.py bildirim_gonder_hatirlatma

Aynı gün ikinci kez çalışsa bile kimseye ikinci bildirim gitmez
(GunlukHatirlatma kaydı). Yanlış saatte (gece) çalıştırılırsa hiçbir şey
göndermez; bunu aşmak için --saat-kontrolu-yok.
"""

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from bildirimler import ayar, gonder
from bildirimler.models import GunlukHatirlatma, PushAboneligi
from learnpass.models import EncounterLog

# Yerel saat (Europe/Istanbul) bu aralığın dışındaysa gönderilmez.
EN_ERKEN_SAAT = 9
EN_GEC_SAAT = 22   # 22:00'den önce

BASLIK = "LearnVocab"
GOVDE = "Birkaç kelimeye göz atmaya ne dersin? İki dakika yeter."


def bugun_bekleyenler(simdi=None):
    """(kullanıcı kimlikleri, gün): aboneliği olan, bugün L&P'de kaydırma
    yapmamış ve bugün hatırlatma almamış kullanıcılar."""
    simdi = timezone.localtime(simdi or timezone.now())
    gun = simdi.date()
    gun_basi = simdi.replace(hour=0, minute=0, second=0, microsecond=0)

    kaydiranlar = (EncounterLog.objects
                   .filter(kind=EncounterLog.VERDICT, created_at__gte=gun_basi)
                   .values("user_id"))
    hatirlatilanlar = GunlukHatirlatma.objects.filter(gun=gun).values("user_id")
    return list(
        PushAboneligi.objects
        .exclude(user_id__in=kaydiranlar)
        .exclude(user_id__in=hatirlatilanlar)
        .values_list("user_id", flat=True)
        .distinct()
        .order_by("user_id")
    ), gun


class Command(BaseCommand):
    help = "Bugün Learn & Pass'e girmemiş abonelere günde bir hatırlatma gönderir."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Yalnızca kaç kişiye gönderileceğini yaz.")
        parser.add_argument("--saat-kontrolu-yok", action="store_true",
                            help=f"{EN_ERKEN_SAAT}:00–{EN_GEC_SAAT}:00 dışında da gönder.")

    def handle(self, *args, **opts):
        if not ayar.acik():
            self.stdout.write("VAPID anahtarı yok; bildirimler kapalı, hiçbir şey gönderilmedi.")
            return

        simdi = timezone.localtime()
        if not opts["saat_kontrolu_yok"] and not (EN_ERKEN_SAAT <= simdi.hour < EN_GEC_SAAT):
            self.stdout.write(f"Saat {simdi:%H:%M}: hatırlatma için uygun değil, gönderilmedi.")
            return

        kullanicilar, gun = bugun_bekleyenler(simdi)
        if opts["dry_run"]:
            self.stdout.write(f"{len(kullanicilar)} kullanıcıya hatırlatma gidecekti (dry-run).")
            return

        from django.contrib.auth import get_user_model
        User = get_user_model()
        url = reverse("learn_pass_page")
        ulasan = 0
        for user in User.objects.filter(id__in=kullanicilar):
            # Önce kayıt: iki çalıştırma üst üste binse bile ikinci bildirim gitmez.
            try:
                with transaction.atomic():
                    kayit = GunlukHatirlatma.objects.create(user=user, gun=gun)
            except IntegrityError:
                continue
            kayit.gonderilen = gonder.kullaniciya(user, BASLIK, GOVDE, url)
            kayit.save(update_fields=["gonderilen"])
            ulasan += bool(kayit.gonderilen)

        self.stdout.write(f"Hatırlatma: {len(kullanicilar)} aday, {ulasan} kullanıcıya ulaştı.")
