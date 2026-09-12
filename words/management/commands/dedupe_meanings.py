# -*- coding: utf-8 -*-
"""
Bir kelimeye birden çok kez yazılmış, pratikte aynı olan anlamları bulur.

    python manage.py dedupe_meanings            # sadece göster
    python manage.py dedupe_meanings --apply    # zayıf olanı sil

Aynı listeyi iki kez çalıştırmak, tekilleştirme birebir karşılaştırma
yaptığı sürece "ders, konu" ile "konu, ders"i iki ayrı anlam sayıyordu.
Kontrol düzeltildi ama daha önce yazılmış kayıtlar duruyor; bu komut onları
toplar.

HANGİSİ KALIR: örnek cümlesi ve collocation'ı daha çok olan. Eşitlikte önce
yazılan. Silinen anlamın cümleleri de gider — taşımıyoruz, çünkü zaten
kalanın kendi cümleleri var ve karışık bir anlamda 10 cümle tutmak
öğrenciye bir şey kazandırmıyor.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from words.enrich.checks import _normalize, _yakin_anlam
from words.models import Word


class Command(BaseCommand):
    help = "Aynı kelimedeki örtüşen anlamları bulur ve isteğe bağlı siler."

    def add_arguments(self, cozumleyici):
        cozumleyici.add_argument("--apply", action="store_true",
                                 help="Bulunanları gerçekten sil.")

    @transaction.atomic
    def handle(self, *args, **secenekler):
        uygula = secenekler["apply"]
        silinecek, etkilenen = [], 0

        for kelime in Word.objects.filter(meanings__isnull=False).distinct():
            anlamlar = list(kelime.meanings.all())
            if len(anlamlar) < 2:
                continue

            tutulan, tutulan_anahtar = [], set()
            kelime_yazildi = False

            for anlam in anlamlar:
                anahtar = _normalize(anlam.meaning_tr)
                yakin = _yakin_anlam(anahtar, tutulan_anahtar)

                if not yakin:
                    tutulan.append(anlam)
                    tutulan_anahtar.add(anahtar)
                    continue

                # Örtüşme var: zengin olanı tut.
                esi = next(a for a in tutulan if _normalize(a.meaning_tr) == yakin)
                yeni_agirlik = anlam.examples.count() + anlam.collocations.count()
                eski_agirlik = esi.examples.count() + esi.collocations.count()

                if yeni_agirlik > eski_agirlik:
                    dusen, kalan = esi, anlam
                    tutulan[tutulan.index(esi)] = anlam
                    tutulan_anahtar.discard(yakin)
                    tutulan_anahtar.add(anahtar)
                else:
                    dusen, kalan = anlam, esi

                if not kelime_yazildi:
                    self.stdout.write(f"\n{kelime.text} ({kelime.pos}):")
                    kelime_yazildi = True
                    etkilenen += 1

                self.stdout.write(
                    f"  tut: '{kalan.meaning_tr}' "
                    f"({kalan.examples.count()} cümle, {kalan.collocations.count()} coll.)")
                self.stdout.write(self.style.WARNING(
                    f"  sil: '{dusen.meaning_tr}' "
                    f"({dusen.examples.count()} cümle, {dusen.collocations.count()} coll.)"))
                silinecek.append(dusen)

        self.stdout.write("")
        if not silinecek:
            self.stdout.write(self.style.SUCCESS("Örtüşen anlam bulunamadı."))
            return

        if uygula:
            for anlam in silinecek:
                anlam.delete()
            self.stdout.write(self.style.SUCCESS(
                f"{len(silinecek)} anlam silindi ({etkilenen} kelimede)."))
        else:
            self.stdout.write(self.style.WARNING(
                f"{len(silinecek)} anlam silinebilir ({etkilenen} kelimede). "
                f"Silmek için: --apply"))
