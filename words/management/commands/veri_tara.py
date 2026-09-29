"""
Kural tabanlı veri denetimi (rapor 18.7 A aşaması) ve "daha basit" kuralı (18.6).

    python manage.py veri_tara --dry-run   # yalnızca rapor
    python manage.py veri_tara             # "daha basit" kuralını uygular

Anlam hataları (bank -> zıt: borrower) kuralla yakalanamaz; onlar B
aşamasında elle taranır. Eş/zıt çakışmaları yalnızca raporlanır (hangisinin
doğru olduğunu kural bilemez); tek tek düzeltmeler words/duzeltmeler/'de.
"""

from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from words.models import WordRelation
from words.veri_kurallari import daha_basit_silinecekler, es_zit_catismalari


class Command(BaseCommand):
    help = "Kural tabanlı veri denetimi; 'daha basit' kuralını uygular."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, dry_run=False, **opts):
        toplam = WordRelation.objects.filter(type="simpler").count()
        silinecek = daha_basit_silinecekler()
        self.stdout.write(f"'Daha basit': {toplam} ilişki · {toplam - len(silinecek)} kalır · {len(silinecek)} silinir")
        for neden, sayi in Counter(n for _, n in silinecek).most_common():
            self.stdout.write(f"  {neden}: {sayi}")

        catisma = es_zit_catismalari()
        self.stdout.write(f"Eş/zıt çakışması (yalnızca rapor): {len(catisma)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("--dry-run: hiçbir şey silinmedi."))
            return
        with transaction.atomic():
            silinen, _ = WordRelation.objects.filter(id__in=[i for i, _ in silinecek]).delete()
        self.stdout.write(self.style.SUCCESS(f"Silindi: {silinen} 'daha basit' ilişkisi."))
