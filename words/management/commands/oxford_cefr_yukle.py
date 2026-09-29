"""
Oxford 3000/5000 seviyelerini veritabanına işler (rapor 18.16/8).

    python manage.py oxford_cefr_yukle --dry-run
    python manage.py oxford_cefr_yukle

Oxford'da olan (kelime, tür) çiftleri o seviyeyi alır ve cefr_kaynak
"oxford" olur; bu etiketler bir daha incelenmez. Oxford'da olmayanlar
"learnvocab" (bizim etiketimiz) kalır. Sonra siklik_hesapla yeniden
çalıştırılmalı (nadir tür seviyeye bağlı).
"""

import os
from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from words.models import Word
from words.oxford import pdf_metni, satirlari_coz

DOSYALAR = ("The_Oxford_3000_by_CEFR_level.pdf", "The_Oxford_5000_by_CEFR_level.pdf")


class Command(BaseCommand):
    help = "Oxford 3000/5000 CEFR seviyelerini Word.cefr / cefr_kaynak alanlarına yazar."

    def add_arguments(self, parser):
        parser.add_argument("--klasor", default="pdfler")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, klasor, dry_run, **opts):
        oxford = {}
        for ad in DOSYALAR:
            parca = satirlari_coz(pdf_metni(os.path.join(klasor, ad)))
            for k, v in parca.items():
                oxford.setdefault(k, v)
        self.stdout.write(f"Oxford: {len(oxford)} (kelime, tür) çifti "
                          f"{dict(sorted(Counter(oxford.values()).items()))}")

        kelimeler = {(w.text.lower(), w.pos): w for w in Word.objects.only("id", "text", "pos", "cefr", "cefr_kaynak")}
        degisen, ayni, degisimler = [], 0, Counter()
        for anahtar, seviye in oxford.items():
            w = kelimeler.get(anahtar)
            if not w:
                continue
            if w.cefr != seviye:
                degisimler[(w.cefr, seviye)] += 1
                degisen.append((w, w.cefr, seviye))
            else:
                ayni += 1
            w.cefr, w.cefr_kaynak = seviye, "oxford"
        bulunamayan = [k for k in oxford if k not in kelimeler]

        self.stdout.write(f"Eşleşen: {ayni + len(degisen)} · aynı seviye: {ayni} · değişecek: {len(degisen)}")
        self.stdout.write(f"Oxford'da olup bizde olmayan: {len(bulunamayan)} (ör. {', '.join(f'{k} ({p})' for k, p in bulunamayan[:12])})")
        for (eski, yeni), sayi in degisimler.most_common(12):
            self.stdout.write(f"  {eski} -> {yeni}: {sayi}")
        self.stdout.write("  örnekler: " + ", ".join(f"{w.text} ({w.pos}) {e}->{y}" for w, e, y in degisen[:25]))

        if dry_run:
            self.stdout.write(self.style.WARNING("--dry-run: hiçbir şey yazılmadı."))
            return
        guncel = [w for k, w in kelimeler.items() if k in oxford]
        with transaction.atomic():
            Word.objects.bulk_update(guncel, ["cefr", "cefr_kaynak"], batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f"Yazıldı: {len(guncel)} kelime oxford kaynaklı."))
