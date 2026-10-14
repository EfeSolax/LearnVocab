"""
Cambridge A2 Key / B1 Preliminary listelerine göre bizim seviyelerimizi düzeltir (rapor 18.16/8, D7).

    python manage.py cambridge_cefr_uygula --dry-run
    python manage.py cambridge_cefr_uygula

Kural yalnızca aşağı doğrudur: A2 Key listesindeki kelime en çok A2, B1
Preliminary listesindeki en çok B1 olur. Yükseltilmez (B1 listesinde olmak
A2 olmadığı anlamına gelmez). Yalnızca cefr_kaynak = "learnvocab" olanlara
dokunulur; Oxford seviyeleri bir daha incelenmez. İnen ya da zaten liste
seviyesinde olan kelime "cambridge" kaynaklı olur. Liste dosyaları
araclar/cambridge_listesi.py ile üretilir; tekrar çalıştırmak güvenli.
Sonra siklik_hesapla çalıştırılmalı (nadir tür seviyeye bağlı).
"""

from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from words.hazir_liste import dosyadan_eslestir
from words.models import Word

LISTELER = (("veri/hazir_listeler/cambridge-b1-preliminary.txt", "B1"),
            ("veri/hazir_listeler/cambridge-a2-key.txt", "A2"))
SIRA = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}


def yeni_seviye(cefr, kaynak, liste_seviyesi):
    """(cefr, kaynak) -> yeni (cefr, kaynak); değişmiyorsa aynısı."""
    if kaynak != "learnvocab":
        return cefr, kaynak
    if SIRA.get(cefr, 99) >= SIRA[liste_seviyesi]:
        return liste_seviyesi, "cambridge"
    return cefr, kaynak


class Command(BaseCommand):
    help = "Cambridge A2 Key / B1 Preliminary listelerine göre bizim CEFR etiketlerimizi aşağı çeker."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, dry_run=False, **opts):
        hedef = {}
        for yol, seviye in LISTELER:  # A2 sonra gelir: iki listede olan A2 sayılır
            with open(yol, encoding="utf-8") as f:
                for w in dosyadan_eslestir(f.read().splitlines()).kelimeler:
                    hedef[w.id] = seviye

        degisen, dogrulanan, gecis, oxford_celiski = [], 0, Counter(), Counter()
        for w in Word.objects.filter(id__in=hedef).only("id", "text", "pos", "cefr", "cefr_kaynak"):
            seviye = hedef[w.id]
            if w.cefr_kaynak == "oxford" and SIRA.get(w.cefr, 0) > SIRA[seviye]:
                oxford_celiski[(w.cefr, seviye)] += 1
            yeni = yeni_seviye(w.cefr, w.cefr_kaynak, seviye)
            if yeni == (w.cefr, w.cefr_kaynak):
                continue
            if yeni[0] != w.cefr:
                gecis[(w.cefr, yeni[0])] += 1
            else:
                dogrulanan += 1
            w.cefr, w.cefr_kaynak = yeni
            degisen.append(w)

        self.stdout.write(f"Listelerde: {len(hedef)} kelime · seviyesi inecek: {sum(gecis.values())} "
                          f"· aynı seviyede, Cambridge'le doğrulanan: {dogrulanan}")
        for (eski, yeni), sayi in sorted(gecis.items()):
            self.stdout.write(f"  {eski} -> {yeni}: {sayi}")
        self.stdout.write(f"Oxford seviyesi listeden yüksek (dokunulmadı): {sum(oxford_celiski.values())} "
                          f"{dict(sorted(oxford_celiski.items()))}")
        if dry_run:
            self.stdout.write(self.style.WARNING("--dry-run: hiçbir şey yazılmadı."))
            return
        with transaction.atomic():
            Word.objects.bulk_update(degisen, ["cefr", "cefr_kaynak"], batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f"Yazıldı: {len(degisen)} kelime cambridge kaynaklı."))
