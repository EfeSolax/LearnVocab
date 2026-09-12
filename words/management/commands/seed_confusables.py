# -*- coding: utf-8 -*-
"""
Küratörlü karıştırılan çiftleri veritabanındaki kelimelere uygular.

    python manage.py seed_confusables
    python manage.py seed_confusables --dry-run
    python manage.py seed_confusables --replace   # modelin uydurduklarını sil

Bir çiftin kurulabilmesi için İKİ kelimenin de veritabanında olması gerekir;
biri eksikse bağ kurulmaz ve raporlanır. Tabloya yeni çift eklediğinde ya da
eksik taraf sonradan üretildiğinde komutu tekrar çalıştırman yeterli.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from words.enrich import confusables
from words.models import Word, WordRelation


class Command(BaseCommand):
    help = "Küratörlü karıştırılan çiftleri mevcut kelimelere bağlar."

    def add_arguments(self, cozumleyici):
        cozumleyici.add_argument("--dry-run", action="store_true",
                                 help="Hiçbir şey yazma, ne olacağını göster.")
        cozumleyici.add_argument("--replace", action="store_true",
                                 help="Önce mevcut confused_with bağlarını sil "
                                      "(modelin uydurduklarını temizlemek için).")

    @transaction.atomic
    def handle(self, *args, **secenekler):
        kuru = secenekler["dry_run"]

        if secenekler["replace"] and not kuru:
            silinen = WordRelation.objects.filter(type="confused_with").delete()[0]
            self.stdout.write(self.style.WARNING(
                f"{silinen} mevcut confused_with bağı silindi."))

        kurulan = 0
        eksik = []

        for a, pos_a, b, pos_b, not_ in confusables.CIFTLER:
            kelime_a = Word.objects.filter(text=a, pos=pos_a).first() \
                    or Word.objects.filter(text=a).first()
            kelime_b = Word.objects.filter(text=b, pos=pos_b).first() \
                    or Word.objects.filter(text=b).first()

            if kelime_a is None or kelime_b is None:
                eksik.append(f"{a}/{b}")
                continue

            for kaynak, hedef in ((kelime_a, kelime_b), (kelime_b, kelime_a)):
                if WordRelation.objects.filter(
                    from_word=kaynak, to_word=hedef, type="confused_with"
                ).exists():
                    continue
                if not kuru:
                    WordRelation.objects.create(
                        from_word=kaynak, to_word=hedef,
                        type="confused_with", note=not_[:200],
                    )
                kurulan += 1
                self.stdout.write(f"  {kaynak.text} ↔ {hedef.text}")

        ozet = f"{kurulan} bağ kuruldu"
        if kuru:
            ozet += "  (DENEME: hiçbir şey yazılmadı)"
        self.stdout.write(self.style.SUCCESS(ozet))

        if eksik:
            self.stdout.write(
                f"İki tarafı da veritabanında olmayan {len(eksik)} çift: "
                f"{', '.join(eksik[:12])}" + (" …" if len(eksik) > 12 else ""))
            self.stdout.write("Eksik kelimeler üretilince komutu tekrar çalıştır.")
