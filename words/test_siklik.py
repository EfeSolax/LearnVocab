"""Sıklık ve nadir tür (rapor 18.16)."""

from django.core.management import call_command
from django.test import TestCase

from words.models import Word
from words.siklik import lp_agirligi, nadir_tur_idleri, siklik_puani
from words.testing import make_word


class SiklikTests(TestCase):
    def test_sik_kelime_seyrekten_yuksek(self):
        self.assertGreater(siklik_puani("house"), siklik_puani("perspire"))

    def test_bos_metin(self):
        self.assertIsNone(siklik_puani("  "))

    def test_lp_agirligi_sik_kelimeyi_one_alir(self):
        self.assertEqual(lp_agirligi(5), 16)
        self.assertEqual(lp_agirligi(2), 1)
        self.assertEqual(lp_agirligi(None), lp_agirligi(1.0))   # taban 1,5
        self.assertGreater(lp_agirligi(5) / lp_agirligi(2), 10)


class NadirTurTests(TestCase):
    def test_temel_tur_a1_b1_iken_c1_c2_tur_nadirdir(self):
        kelimeler = [(1, "dog", "noun", "A2"), (2, "dog", "verb", "C1"),
                     (3, "bank", "noun", "A1"), (4, "bank", "verb", "B2")]
        self.assertEqual(nadir_tur_idleri(kelimeler), {2})

    def test_tek_turlu_ya_da_temeli_yuksek_kelime_nadir_degil(self):
        kelimeler = [(1, "justice", "noun", "C1"),
                     (2, "notion", "noun", "B2"), (3, "notion", "verb", "C2")]
        self.assertEqual(nadir_tur_idleri(kelimeler), set())

    def test_komut_alanlari_doldurur(self):
        make_word("dog", level="A2")
        make_word("dog", pos="verb", level="C1")
        call_command("siklik_hesapla", stdout=open("/dev/null", "w"))
        isim, fiil = Word.objects.get(text="dog", pos="noun"), Word.objects.get(text="dog", pos="verb")
        self.assertIsNotNone(isim.siklik)
        self.assertFalse(isim.nadir_tur)
        self.assertTrue(fiil.nadir_tur)
        self.assertEqual(fiil.cefr_kaynak, "learnvocab")
