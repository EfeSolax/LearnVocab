"""
reading-texts/ klasöründeki metinleri veritabanına alır.

Tekrar tekrar çalıştırılabilir: metinler kitaptaki sıra numarasına göre
eşleştiriliyor, var olan kayıt güncelleniyor, yeni olan ekleniyor.
Kaynak dosyalardan kaldırılmış bir metin varsa --prune ile silinebilir.

    python manage.py import_readings
    python manage.py import_readings --dry-run
    python manage.py import_readings --prune
"""

import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from readings.models import TOPIC_LABELS, ReadingText
from readings.parser import parse_directory


class Command(BaseCommand):
    help = "reading-texts/ klasöründeki okuma metinlerini içeri alır."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=None,
            help="Metinlerin bulunduğu klasör (varsayılan: proje kökündeki reading-texts).",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Hiçbir şey yazma, ne olacağını göster.",
        )
        parser.add_argument(
            "--prune", action="store_true",
            help="Kaynak dosyalarda artık bulunmayan metinleri sil.",
        )

    def handle(self, *args, **secenekler):
        klasor = secenekler["path"] or os.path.join(settings.BASE_DIR, "reading-texts")
        if not os.path.isdir(klasor):
            raise CommandError(f"Klasör bulunamadı: {klasor}")

        metinler = parse_directory(klasor)
        if not metinler:
            raise CommandError(f"{klasor} içinde okunabilir metin bulunamadı.")

        # Aynı numaranın iki dosyada birden çıkması sessiz veri kaybı olurdu
        gorulen = {}
        for metin in metinler:
            if metin["number"] in gorulen:
                raise CommandError(
                    "{} numarası iki dosyada birden geçiyor: {} ve {}".format(
                        metin["number"], gorulen[metin["number"]], metin["source_file"]
                    )
                )
            gorulen[metin["number"]] = metin["source_file"]

        bilinmeyen = {m["topic"] for m in metinler} - set(TOPIC_LABELS)
        if bilinmeyen:
            self.stdout.write(self.style.WARNING(
                "Uyarı: readings/models.py içindeki TOPICS listesinde olmayan konu(lar): "
                + ", ".join(sorted(bilinmeyen))
            ))

        eklenen = guncellenen = degismeyen = 0
        for metin in metinler:
            govde = "\n\n".join(metin["paragraphs"])
            alanlar = {
                "topic": metin["topic"],
                "title": metin["title"],
                "body": govde,
                "word_count": sum(len(p.split()) for p in metin["paragraphs"]),
            }

            mevcut = ReadingText.objects.filter(number=metin["number"]).first()
            if mevcut is None:
                eklenen += 1
                if not secenekler["dry_run"]:
                    ReadingText.objects.create(number=metin["number"], **alanlar)
            elif any(getattr(mevcut, ad) != deger for ad, deger in alanlar.items()):
                guncellenen += 1
                if not secenekler["dry_run"]:
                    for ad, deger in alanlar.items():
                        setattr(mevcut, ad, deger)
                    mevcut.save()
            else:
                degismeyen += 1

        silinen = 0
        if secenekler["prune"]:
            fazlalik = ReadingText.objects.exclude(number__in=gorulen)
            silinen = fazlalik.count()
            if not secenekler["dry_run"]:
                fazlalik.delete()

        ozet = (
            f"{len(metinler)} metin okundu — "
            f"{eklenen} eklendi, {guncellenen} güncellendi, {degismeyen} değişmedi"
        )
        if secenekler["prune"]:
            ozet += f", {silinen} silindi"
        if secenekler["dry_run"]:
            ozet += "  (DENEME: hiçbir şey yazılmadı)"

        self.stdout.write(self.style.SUCCESS(ozet))

        # Konu dağılımı
        for anahtar in sorted({m["topic"] for m in metinler}):
            grup = [m for m in metinler if m["topic"] == anahtar]
            kelime = sum(sum(len(p.split()) for p in m["paragraphs"]) for m in grup)
            ad = TOPIC_LABELS.get(anahtar, anahtar)
            self.stdout.write(f"  {ad:<14} {len(grup):>2} metin, {kelime:>6} kelime")
