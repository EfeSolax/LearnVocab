# -*- coding: utf-8 -*-
"""
Depodaki bütün ailelerin bütün kelimelerini TEK bir txt'ye yazar ve her
kelimenin durumunu gösterir. Büyük çalıştırmada "nerede kaldık" dosyası.

    python manage.py kelime_listesi --depo ara-depo-tam
    python manage.py kelime_listesi --depo ara-depo-tam --out listeler/tum-kelimeler.txt

Durumlar:
    ✓  yazıldı       veritabanında var
    ✗  reddedildi    kontrol reddetti / modelin "böyle bir anlam yok" dediği
    ?  incelenecek   aile birleştirmede takıldı (kararlar.json)
    ·  bekliyor      henüz anlamı alınmadı (aile_doldur sıradaki işi bu)

Veritabanına yazmaz, para harcamaz; istediğin kadar çalıştırabilirsin.
"""

from collections import Counter
from pathlib import Path

from django.core.management.base import BaseCommand

from words.aile.depo import Depo
from words.models import Word

ISARET = {"yazildi": "✓", "reddedildi": "✗", "incelenecek": "?", "bekliyor": "·"}


class Command(BaseCommand):
    help = "Depodaki bütün kelimeleri durumlarıyla tek bir txt'ye yazar."

    def add_arguments(self, c):
        c.add_argument("--depo", default="ara-depo-tam")
        c.add_argument("--out", default="listeler/tum-kelimeler.txt")

    def handle(self, *args, **o):
        depo = Depo(o["depo"])
        aileler = depo.aileler()
        anlamlar = depo.anlamlar()
        dbde = set(Word.objects.values_list("text", "pos"))
        sayac, aile_sayac, satirlar = Counter(), Counter(), []
        for a in aileler:
            aile_durumlari = []
            satirlar.append(f"\n## {a['kok']}" + ("   [incelenecek]" if a.get("durum") == "incelenecek" else ""))
            for u in a.get("uyeler", []):
                anahtar = (u["word"], u["type"])
                if anahtar in dbde:
                    d = "yazildi"
                elif a.get("durum") == "incelenecek":
                    d = "incelenecek"
                elif (anlamlar.get(anahtar) or {}).get("durum") == "reddedildi":
                    d = "reddedildi"
                else:
                    d = "bekliyor"
                sayac[d] += 1
                aile_durumlari.append(d)
                satirlar.append(f"{ISARET[d]} {u['word']} ({u['type']})")
            aile_sayac["incelenecek" if a.get("durum") == "incelenecek"
                       else "bekliyor" if "bekliyor" in aile_durumlari else "bitti"] += 1
        toplam = sum(sayac.values())
        bas = [
            "# TÜM KELİMELER — `python manage.py kelime_listesi` üretir; her çalıştırmada güncellenir.",
            f"# Depo: {o['depo']}",
            f"# {len(aileler)} aile · {toplam} kelime",
            f"#   ✓ yazıldı {sayac['yazildi']} · · bekliyor {sayac['bekliyor']} · "
            f"✗ reddedildi {sayac['reddedildi']} · ? incelenecek {sayac['incelenecek']}",
            f"#   aile: {aile_sayac['bitti']} bitti · {aile_sayac['bekliyor']} bekliyor · "
            f"{aile_sayac['incelenecek']} incelenecek",
        ]
        Path(o["out"]).parent.mkdir(parents=True, exist_ok=True)
        Path(o["out"]).write_text("\n".join(bas + satirlar) + "\n", encoding="utf-8")
        for s in bas[2:]:
            self.stdout.write(s.lstrip("# "))
        self.stdout.write(self.style.SUCCESS(f"Yazıldı: {o['out']}"))
