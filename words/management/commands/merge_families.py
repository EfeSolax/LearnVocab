# -*- coding: utf-8 -*-
"""
İki aileyi birleştirir. Kuralla çözülemeyen durumlar için elle müdahale.

    python manage.py merge_families analyse analysis
    python manage.py merge_families analyse analysis --dry-run
    python manage.py merge_families --list          # tek üyeli aileleri göster

Kod, aileleri üç yoldan eşleştiriyor (kök arama, üyelik, türevden tabana) ve
yazım benzeyen adayları modele soruyor. Ama bazı çiftler bunların hiçbirine
uymuyor: `analyse` ile `analysis` yalnızca "analy" ön ekini paylaşır, ve aynı
ön eki paylaşan `conscience`/`conscious` AYRI ailelerdir. Kural yazmaya
çalışmak ikisinden birini mutlaka yanlış yapar — bu yüzden karar sende.

İlk ailenin kökü korunur, ikincisinin üyeleri ona taşınır ve ikinci aile
silinir.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from words.models import WordFamily


class Command(BaseCommand):
    help = "İki kelime ailesini tek ailede birleştirir."

    def add_arguments(self, cozumleyici):
        cozumleyici.add_argument("kalan", nargs="?", help="Kökü korunacak aile.")
        cozumleyici.add_argument("giden", nargs="?", help="Üyeleri taşınacak aile.")
        cozumleyici.add_argument("--dry-run", action="store_true")
        cozumleyici.add_argument("--list", action="store_true",
                                 help="Tek üyeli aileleri listele (birleşme adayları).")

    @transaction.atomic
    def handle(self, *args, **secenekler):
        if secenekler["list"]:
            self._adaylari_bas()
            return

        if not secenekler["kalan"] or not secenekler["giden"]:
            raise CommandError("İki aile kökü ver: manage.py merge_families <kalan> <giden>")

        kalan = WordFamily.objects.filter(root=secenekler["kalan"].lower()).first()
        giden = WordFamily.objects.filter(root=secenekler["giden"].lower()).first()

        if kalan is None:
            raise CommandError(f"Aile bulunamadı: {secenekler['kalan']}")
        if giden is None:
            raise CommandError(f"Aile bulunamadı: {secenekler['giden']}")
        if kalan.pk == giden.pk:
            raise CommandError("Aynı aile.")

        tasinan = list(giden.words.all())
        self.stdout.write(f"'{giden.root}' -> '{kalan.root}'")
        for kelime in tasinan:
            self.stdout.write(f"  taşınacak: {kelime.text} ({kelime.pos})")

        if secenekler["dry_run"]:
            self.stdout.write(self.style.WARNING(
                f"{len(tasinan)} kelime taşınabilir. (DENEME: hiçbir şey yazılmadı)"))
            return

        giden.words.update(family=kalan)
        giden.delete()
        self.stdout.write(self.style.SUCCESS(
            f"{len(tasinan)} kelime '{kalan.root}' ailesine taşındı; "
            f"'{giden.root}' ailesi silindi."))

    def _adaylari_bas(self):
        """Ortak ön ek paylaşan aileleri gruplayıp gösterir."""
        aileler = list(WordFamily.objects.all())
        gruplar = {}
        for aile in aileler:
            if len(aile.root) >= 5:
                gruplar.setdefault(aile.root[:5], []).append(aile)

        bulundu = False
        for onek, grup in sorted(gruplar.items()):
            if len(grup) < 2:
                continue
            bulundu = True
            self.stdout.write(f"\n'{onek}...' ile başlayanlar:")
            for aile in grup:
                uyeler = ", ".join(k.text for k in aile.words.all()) or "—"
                self.stdout.write(f"  {aile.root:20s} ({uyeler})")

        if not bulundu:
            self.stdout.write("Ortak ön ek paylaşan aile yok.")
        else:
            self.stdout.write(self.style.WARNING(
                "\nAynı kökten olanları birleştir: "
                "manage.py merge_families <kalan> <giden>"))
