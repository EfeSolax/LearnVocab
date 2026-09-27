# -*- coding: utf-8 -*-
"""
Türkçe yazım denetimi için hunspell sözlüğünü indirir (words/aile/turkce.py).

    pip install spylls
    python manage.py turkce_sozluk_kur

LibreOffice'in tr_TR sözlüğü (~38 MB) words/aile/sozluk/ klasörüne iner.
Bir kez yapılır; klasör git'e girmez.
"""

import requests
from django.core.management.base import BaseCommand, CommandError

from words.aile import turkce


class Command(BaseCommand):
    help = "Türkçe yazım denetimi için tr_TR hunspell sözlüğünü indirir."

    def add_arguments(self, c):
        c.add_argument("--yeniden", action="store_true", help="Varsa da tekrar indir.")

    def handle(self, *args, **s):
        if turkce.kurulu_mu() and not s["yeniden"]:
            self.stdout.write(f"Sözlük zaten kurulu: {turkce.KLASOR}")
        else:
            turkce.KLASOR.mkdir(parents=True, exist_ok=True)
            for uzanti in ("aff", "dic"):
                ad = f"{turkce.AD}.{uzanti}"
                self.stdout.write(f"İndiriliyor: {ad} …")
                try:
                    cevap = requests.get(turkce.ADRES + ad, timeout=120)
                    cevap.raise_for_status()
                except requests.RequestException as hata:
                    raise CommandError(f"{ad} indirilemedi: {hata}") from hata
                (turkce.KLASOR / ad).write_bytes(cevap.content)
                self.stdout.write(f"  {len(cevap.content) / 1e6:.1f} MB")

        self.stdout.write("Deneme yükleniyor (~8 sn)…")
        hazir, aciklama = turkce.durum()
        if not hazir:
            raise CommandError(aciklama)
        ornek = "kirlilik kirlık teşeksiz evlat edinilmiş öngörülemezlik"
        self.stdout.write(f"'{ornek}' içinde tanınmayan: {turkce.bilinmeyenler(ornek)}")
        self.stdout.write(self.style.SUCCESS("Türkçe yazım denetimi hazır."))
