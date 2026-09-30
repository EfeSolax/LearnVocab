"""
90 günden eski karşılaşma kayıtlarını kişisiz günlük özetlere çevirir (rapor 18.32).

    manage.py karsilasma_ozetle --dry-run
    manage.py karsilasma_ozetle

Cron: günde bir, gece (bildirimler/CRON.md). Tekrar çalıştırmak güvenlidir.
"""

from django.core.management.base import BaseCommand

from learnpass import ozet


class Command(BaseCommand):
    help = "90 günden eski EncounterLog kayıtlarını günlük özetlere çevirip siler."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Yazmadan yalnızca say.")

    def handle(self, *args, **o):
        sonuc = ozet.ozetle(dry_run=o["dry_run"])
        fiil = "özetlenecek" if o["dry_run"] else "özetlendi ve silindi"
        self.stdout.write(f"{sonuc['ozetlenen']} kayıt ({sonuc['gun']} gün) {fiil}.")
