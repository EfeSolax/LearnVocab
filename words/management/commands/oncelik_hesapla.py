"""
Kelimelerin öğrenme önceliğini (Word.oncelik) hesaplar (words/oncelik.py).

    python manage.py oncelik_hesapla --dry-run   # yalnızca özet ve örnekler
    python manage.py oncelik_hesapla

Her çalıştırmada baştan hesaplar; tekrar çalıştırmak güvenli. Önce siklik_hesapla çalışmış olmalı.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from words.models import Word
from words.oncelik import oncelikleri_hesapla

SEVIYELER = ("A1", "A2", "B1", "B2", "C1", "C2")


class Command(BaseCommand):
    help = "Word.oncelik alanını hesaplar."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="yazmadan özet göster")
        parser.add_argument("--ornek", type=int, default=15, help="seviye başına gösterilen ilk/son kelime")

    def handle(self, *args, dry_run=False, ornek=15, **opts):
        puanlar = oncelikleri_hesapla()
        kelimeler = list(Word.objects.only("id", "text", "pos", "cefr", "oncelik"))
        for w in kelimeler:
            w.oncelik = puanlar[w.id]

        self.stdout.write(f"{len(kelimeler)} kelime")
        for seviye in SEVIYELER:
            grup = sorted((w for w in kelimeler if w.cefr == seviye), key=lambda w: (-w.oncelik, w.text))
            if not grup:
                continue
            self.stdout.write(f"\n{seviye} ({len(grup)} kelime, ortanca {grup[len(grup) // 2].oncelik})")
            self.stdout.write("  ilk: " + ", ".join(f"{w.text} {w.oncelik:g}" for w in grup[:ornek]))
            self.stdout.write("  son: " + ", ".join(f"{w.text} {w.oncelik:g}" for w in grup[-ornek:]))

        if dry_run:
            self.stdout.write(self.style.WARNING("\n--dry-run: hiçbir şey yazılmadı."))
            return
        with transaction.atomic():
            Word.objects.bulk_update(kelimeler, ["oncelik"], batch_size=1000)
        self.stdout.write(self.style.SUCCESS("\nYazıldı."))
