# -*- coding: utf-8 -*-
"""
Küratörlü yanlış dost tablosunu veritabanındaki kelimelere uygular.

    python manage.py seed_false_friends
    python manage.py seed_false_friends --dry-run

Tablo (words/enrich/false_friends.py) zamanla büyüyecek. Bu komut tekrar
tekrar çalıştırılabilir: var olan kayıtlara dokunmaz, yalnızca eksikleri
ekler. Yeni bir yanlış dost eklediğinde çalıştırman yeterli — kelimeleri
baştan üretmene gerek yok.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from words.enrich import false_friends
from words.models import FalseFriend, Word


class Command(BaseCommand):
    help = "Küratörlü yanlış dostları mevcut kelimelere ekler."

    def add_arguments(self, cozumleyici):
        cozumleyici.add_argument("--dry-run", action="store_true",
                                 help="Hiçbir şey yazma, ne olacağını göster.")

    @transaction.atomic
    def handle(self, *args, **secenekler):
        kuru = secenekler["dry_run"]
        eklenen = kelime_sayisi = 0
        eslesmeyen = []

        for metin, kayitlar in sorted(false_friends.YANLIS_DOSTLAR.items()):
            kelimeler = list(Word.objects.filter(text=metin))
            if not kelimeler:
                eslesmeyen.append(metin)
                continue

            for kelime in kelimeler:
                yeni = 0
                for benzeyen, sanilan, dogru, not_ in kayitlar:
                    if FalseFriend.objects.filter(
                        word=kelime, turkish_lookalike=benzeyen
                    ).exists():
                        continue
                    if not kuru:
                        FalseFriend.objects.create(
                            word=kelime, turkish_lookalike=benzeyen,
                            assumed_meaning=sanilan or None,
                            correct_english=dogru or None,
                            note=not_ or None,
                        )
                    yeni += 1

                if yeni:
                    kelime_sayisi += 1
                    eklenen += yeni
                    self.stdout.write(
                        f"  {kelime.text} ({kelime.pos}): {yeni} yanlış dost")

        ozet = f"{eklenen} kayıt, {kelime_sayisi} kelimeye eklendi"
        if kuru:
            ozet += "  (DENEME: hiçbir şey yazılmadı)"
        self.stdout.write(self.style.SUCCESS(ozet))

        if eslesmeyen:
            self.stdout.write(
                f"Tabloda olup veritabanında bulunmayan {len(eslesmeyen)} kelime: "
                f"{', '.join(eslesmeyen[:15])}"
                + (" …" if len(eslesmeyen) > 15 else "")
            )
            self.stdout.write(
                "Bunlar eklendiğinde komutu tekrar çalıştırman yeterli.")
