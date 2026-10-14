"""Cambridge listelerine göre seviye düzeltme kuralı (rapor 18.16/8)."""

from django.test import SimpleTestCase

from words.management.commands.cambridge_cefr_uygula import yeni_seviye


class CambridgeSeviyeKuraliTests(SimpleTestCase):
    def test_yuksek_seviye_liste_seviyesine_iner(self):
        self.assertEqual(yeni_seviye("B2", "learnvocab", "A2"), ("A2", "cambridge"))
        self.assertEqual(yeni_seviye("C1", "learnvocab", "B1"), ("B1", "cambridge"))

    def test_ayni_seviye_cambridge_ile_dogrulanir(self):
        self.assertEqual(yeni_seviye("B1", "learnvocab", "B1"), ("B1", "cambridge"))

    def test_dusuk_seviye_yukseltilmez(self):
        self.assertEqual(yeni_seviye("A1", "learnvocab", "B1"), ("A1", "learnvocab"))

    def test_oxford_seviyesine_dokunulmaz(self):
        self.assertEqual(yeni_seviye("B2", "oxford", "A2"), ("B2", "oxford"))

    def test_seviyesiz_kelime_liste_seviyesini_alir(self):
        self.assertEqual(yeni_seviye("", "learnvocab", "A2"), ("A2", "cambridge"))
