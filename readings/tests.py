"""
Okuma metinleri: ayrıştırma ve içeri alma testleri.

Buradaki asıl risk sessiz veri kaybı: bir başlık kalıbı tutmazsa metin
gövdesine karışır, ya da iki dosyada aynı numara varsa biri diğerinin
üstüne yazar. Testler bu iki durumu da yakalıyor.
"""

import io
import os
import tempfile

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from readings import parser
from readings.models import ReadingText


ORNEK = """25 SIBLINGS

Birinci paragraf burada.

İkinci paragraf burada.

26 ARE WE LIVING IN A WALK-ON-BY SOCIETY?

Tek paragraf.
"""


class ParserTests(TestCase):

    def test_headings_and_paragraphs_are_separated(self):
        metinler = parser.parse_text_file(ORNEK)
        self.assertEqual([m["number"] for m in metinler], [25, 26])
        self.assertEqual(metinler[0]["title"], "SIBLINGS")
        self.assertEqual(len(metinler[0]["paragraphs"]), 2)
        self.assertEqual(len(metinler[1]["paragraphs"]), 1)

    def test_heading_never_leaks_into_the_body(self):
        metinler = parser.parse_text_file(ORNEK)
        for metin in metinler:
            for paragraf in metin["paragraphs"]:
                self.assertNotIn("SIBLINGS", paragraf)

    def test_punctuation_in_titles_is_kept(self):
        metinler = parser.parse_text_file(ORNEK)
        self.assertEqual(metinler[1]["title"], "ARE WE LIVING IN A WALK-ON-BY SOCIETY?")

    def test_text_before_the_first_heading_is_ignored(self):
        """Dosyanın başına düşen açıklama cümleleri metne karışmamalı."""
        kirli = "İstediğiniz gibi kitaptaki metinler aşağıdadır:\n\n" + ORNEK
        metinler = parser.parse_text_file(kirli)
        self.assertEqual(len(metinler), 2)
        self.assertNotIn("İstediğiniz", metinler[0]["paragraphs"][0])

    def test_a_heading_with_no_paragraphs_is_dropped(self):
        metinler = parser.parse_text_file("99 BOS BASLIK\n")
        self.assertEqual(metinler, [])

    def test_sentence_in_capitals_is_not_mistaken_for_a_heading(self):
        """Başlık kalıbı numara ile başlar; rakamsız büyük harfli satır paragraftır."""
        metinler = parser.parse_text_file("25 SIBLINGS\n\nTHIS IS A SHOUTED SENTENCE.\n")
        self.assertEqual(len(metinler), 1)
        self.assertEqual(metinler[0]["paragraphs"], ["THIS IS A SHOUTED SENTENCE."])

    def test_topic_comes_from_the_file_name(self):
        for dosya, beklenen in (
            ("1-10 Hukuk.txt", "Hukuk"),
            ("13-22-Psikoloji.txt", "Psikoloji"),
            ("52-56 Eğitim.txt", "Eğitim"),
            ("40-44 Antropoloji.txt", "Antropoloji"),
        ):
            with self.subTest(dosya=dosya):
                self.assertEqual(parser.topic_from_filename(dosya), beklenen)

    def test_topic_key_is_url_safe(self):
        self.assertEqual(parser.topic_key("Eğitim"), "egitim")
        self.assertEqual(parser.topic_key("Psikoloji"), "psikoloji")


class ImportCommandTests(TestCase):

    def _klasor(self, dosyalar):
        gecici = tempfile.mkdtemp()
        for ad, icerik in dosyalar.items():
            with io.open(os.path.join(gecici, ad), "w", encoding="utf-8") as f:
                f.write(icerik)
        return gecici

    def test_import_creates_texts(self):
        klasor = self._klasor({"25-26 Sosyoloji.txt": ORNEK})
        call_command("import_readings", path=klasor, verbosity=0)

        self.assertEqual(ReadingText.objects.count(), 2)
        metin = ReadingText.objects.get(number=25)
        self.assertEqual(metin.title, "SIBLINGS")
        self.assertEqual(metin.topic, "sosyoloji")
        self.assertEqual(len(metin.paragraphs), 2)
        self.assertEqual(metin.word_count, 6)

    def test_running_twice_changes_nothing(self):
        klasor = self._klasor({"25-26 Sosyoloji.txt": ORNEK})
        call_command("import_readings", path=klasor, verbosity=0)
        once = ReadingText.objects.get(number=25).updatedAt

        call_command("import_readings", path=klasor, verbosity=0)
        self.assertEqual(ReadingText.objects.count(), 2)
        self.assertEqual(ReadingText.objects.get(number=25).updatedAt, once)

    def test_changed_source_updates_the_record(self):
        klasor = self._klasor({"25-26 Sosyoloji.txt": ORNEK})
        call_command("import_readings", path=klasor, verbosity=0)

        yeni = ORNEK.replace("Birinci paragraf burada.", "Düzeltilmiş paragraf.")
        with io.open(os.path.join(klasor, "25-26 Sosyoloji.txt"), "w", encoding="utf-8") as f:
            f.write(yeni)
        call_command("import_readings", path=klasor, verbosity=0)

        self.assertIn("Düzeltilmiş", ReadingText.objects.get(number=25).body)
        self.assertEqual(ReadingText.objects.count(), 2)

    def test_dry_run_writes_nothing(self):
        klasor = self._klasor({"25-26 Sosyoloji.txt": ORNEK})
        call_command("import_readings", path=klasor, dry_run=True, verbosity=0)
        self.assertEqual(ReadingText.objects.count(), 0)

    def test_duplicate_number_across_files_is_refused(self):
        """Aynı numara iki dosyada varsa biri diğerinin üstüne yazardı."""
        klasor = self._klasor({
            "25-26 Sosyoloji.txt": ORNEK,
            "25-26 Psikoloji.txt": ORNEK,
        })
        with self.assertRaises(CommandError) as hata:
            call_command("import_readings", path=klasor, verbosity=0)
        self.assertIn("25", str(hata.exception))

    def test_prune_removes_texts_no_longer_in_the_source(self):
        klasor = self._klasor({"25-26 Sosyoloji.txt": ORNEK})
        call_command("import_readings", path=klasor, verbosity=0)
        ReadingText.objects.create(number=99, topic="hukuk", title="ESKI", body="x", word_count=1)

        call_command("import_readings", path=klasor, prune=True, verbosity=0)
        self.assertFalse(ReadingText.objects.filter(number=99).exists())
        self.assertEqual(ReadingText.objects.count(), 2)

    def test_missing_folder_is_reported(self):
        with self.assertRaises(CommandError):
            call_command("import_readings", path="/yok/boyle/bir/yer", verbosity=0)

    def test_empty_folder_is_reported(self):
        with self.assertRaises(CommandError):
            call_command("import_readings", path=tempfile.mkdtemp(), verbosity=0)


class ReadingTextModelTests(TestCase):

    def test_reading_time_is_never_zero(self):
        kisa = ReadingText.objects.create(number=1, topic="hukuk", title="A",
                                          body="tek kelime", word_count=2)
        self.assertEqual(kisa.reading_minutes, 1)

    def test_reading_time_scales_with_length(self):
        uzun = ReadingText.objects.create(number=2, topic="hukuk", title="B",
                                          body="x", word_count=750)
        self.assertEqual(uzun.reading_minutes, 5)

    def test_paragraphs_survive_a_round_trip(self):
        metin = ReadingText.objects.create(number=3, topic="hukuk", title="C",
                                           body="Bir.\n\nİki.\n\nÜç.", word_count=3)
        self.assertEqual(metin.paragraphs, ["Bir.", "İki.", "Üç."])


class RealSourceFilesTests(TestCase):
    """
    Gerçek reading-texts/ klasörü. Dosyalar projeye dahil olduğu için
    bozulmalarını da test etmeye değer.
    """

    def setUp(self):
        from django.conf import settings

        self.klasor = os.path.join(settings.BASE_DIR, "reading-texts")
        if not os.path.isdir(self.klasor):
            self.skipTest("reading-texts klasörü yok")

    def test_all_forty_texts_parse(self):
        metinler = parser.parse_directory(self.klasor)
        self.assertEqual(len(metinler), 40)

    def test_every_topic_is_declared_in_the_model(self):
        from readings.models import TOPIC_LABELS

        konular = {m["topic"] for m in parser.parse_directory(self.klasor)}
        self.assertEqual(konular - set(TOPIC_LABELS), set(),
                         "TOPICS listesine eklenmemiş konu var")

    def test_numbers_are_unique(self):
        numaralar = [m["number"] for m in parser.parse_directory(self.klasor)]
        self.assertEqual(len(numaralar), len(set(numaralar)))

    def test_no_turkish_leftovers_from_the_source_chat(self):
        for metin in parser.parse_directory(self.klasor):
            govde = " ".join(metin["paragraphs"])
            for kalinti in ("İstediğiniz", "sunulmuştur", "aşağıda sırasıyla"):
                with self.subTest(metin=metin["number"], kalinti=kalinti):
                    self.assertNotIn(kalinti, govde)
