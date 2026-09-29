"""
Kelimelerin sıklık puanını (Word.siklik) ve nadir tür işaretini
(Word.nadir_tur) hesaplar (rapor 18.16).

    python manage.py siklik_hesapla --dry-run   # yalnızca özet
    python manage.py siklik_hesapla

Her çalıştırmada baştan hesaplar; tekrar çalıştırmak güvenli.
"""

from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from words.models import Word
from words.siklik import nadir_tur_idleri, siklik_puani


class Command(BaseCommand):
    help = "Word.siklik ve Word.nadir_tur alanlarını hesaplar."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="yazmadan özet göster")

    def handle(self, *args, dry_run=False, **opts):
        kelimeler = list(Word.objects.only("id", "text", "pos", "cefr", "siklik", "nadir_tur"))
        onbellek = {}
        for w in kelimeler:
            anahtar = w.text.lower()
            if anahtar not in onbellek:
                onbellek[anahtar] = siklik_puani(w.text)
            w.siklik = onbellek[anahtar]
        nadir = nadir_tur_idleri((w.id, w.text, w.pos, w.cefr) for w in kelimeler)
        for w in kelimeler:
            w.nadir_tur = w.id in nadir

        bolge = Counter()
        for w in kelimeler:
            z = w.siklik or 0
            bolge["<2,3 (Google'dan gizlenecek)" if z < 2.3 else "2,3–3,5" if z < 3.5 else "3,5–5" if z < 5 else "≥5"] += 1
        self.stdout.write(f"{len(kelimeler)} kelime · {len(nadir)} nadir tür")
        for ad, sayi in sorted(bolge.items()):
            self.stdout.write(f"  sıklık {ad}: {sayi}")
        ornek = sorted((w for w in kelimeler if w.nadir_tur), key=lambda w: -(w.siklik or 0))[:15]
        self.stdout.write("  nadir tür örnekleri: " + ", ".join(f"{w.text} ({w.pos}, {w.cefr})" for w in ornek))

        if dry_run:
            self.stdout.write(self.style.WARNING("--dry-run: hiçbir şey yazılmadı."))
            return
        with transaction.atomic():
            Word.objects.bulk_update(kelimeler, ["siklik", "nadir_tur"], batch_size=1000)
        self.stdout.write(self.style.SUCCESS("Yazıldı."))
