"""
Seviye testi ekran kelimelerini seçer (veri işi D8). Kural: seviye/secim.py

    python manage.py seviye_kelimeleri_sec --dry-run              # önce gözden geçir
    python manage.py seviye_kelimeleri_sec --dry-run --json x.json   # dosyaya dök
    python manage.py seviye_kelimeleri_sec                        # tabloya yaz

Seçim deterministiktir: aynı veritabanı ve aynı wordfreq sürümüyle her
çalıştırmada aynı havuz çıkar. Gerçek yazımda SeviyeKelimesi tablosu baştan
kurulur (eski satırlar silinir). Tablo boşken test aynı kuralla anında seçer;
tabloya yazmanın faydası seçimi sabitlemek ve admin'den denetlenebilir
kılmak (beğenilmeyen bir kelime tablodan silinebilir).
"""

import json
from collections import Counter
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from seviye import secim
from seviye.models import Ekran, SeviyeKelimesi


class Command(BaseCommand):
    help = "Seviye testi ekran kelimelerini (D8) seçer ve SeviyeKelimesi tablosuna yazar."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Yazmadan özetle ve örnek göster.")
        parser.add_argument("--json", help="Seçimi bu JSON dosyasına da yaz (denetim için).")
        parser.add_argument("--wordfreq-yok", action="store_true",
                            help="wordfreq kurulu olsa bile sıklık bandını atla.")

    def handle(self, *args, **opts):
        zipf = None if opts["wordfreq_yok"] else secim.zipf_olcer()
        if zipf is None:
            self.stdout.write("wordfreq yok ya da kapalı: sıklık bandı atlanıyor.")
        adaylar = secim.adaylar(zipf)

        sayac = Counter((a.ekran, a.cefr) for a in adaylar)
        for ekran in Ekran:
            parca = ", ".join(f"{s}: {sayac[(ekran, s)]}" for s in secim.EKRAN_SEVIYELERI[ekran])
            self.stdout.write(f"{ekran.value}. ekran ({ekran.label}) — {parca}")
            ornek = [a.text for a in adaylar if a.ekran == ekran][:25]
            self.stdout.write("   " + ", ".join(ornek))
            if sum(sayac[(ekran, s)] for s in secim.EKRAN_SEVIYELERI[ekran]) < secim.EKRAN_BOYU:
                self.stdout.write(self.style.WARNING(f"   uyarı: havuz {secim.EKRAN_BOYU} kelimeden küçük"))

        if opts["json"]:
            veri = [{"ekran": a.ekran, "kelime": a.text, "cefr": a.cefr, "zipf": a.zipf,
                     "word_id": a.word_id} for a in adaylar]
            Path(opts["json"]).write_text(json.dumps(veri, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
            self.stdout.write(f"JSON yazıldı: {opts['json']} ({len(veri)} kelime)")

        if opts["dry_run"]:
            self.stdout.write(f"(dry-run) {len(adaylar)} kelime seçildi, tabloya yazılmadı.")
            return

        with transaction.atomic():
            SeviyeKelimesi.objects.all().delete()
            SeviyeKelimesi.objects.bulk_create([
                SeviyeKelimesi(ekran=a.ekran, word_id=a.word_id, cefr=a.cefr, zipf=a.zipf, sira=i)
                for i, a in enumerate(adaylar)
            ])
        self.stdout.write(self.style.SUCCESS(f"{len(adaylar)} kelime SeviyeKelimesi tablosuna yazıldı."))
