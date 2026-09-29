"""Oxford 3000/5000 okuyucusu (rapor 18.16/8)."""

from django.test import SimpleTestCase

from words.oxford import satirlari_coz

ORNEK = """© Oxford University Press
1 / 12
The Oxford 3000™ by CEFR level
A1
a, an indefinite article
answer n., v.
bank (money) n.
be v., auxiliary v.
another det./pron.
A2
back v.
B1
bank (river) n.
all right adj., adv.
"""


class OxfordOkuyucuTests(SimpleTestCase):
    def setUp(self):
        self.sonuc = satirlari_coz(ORNEK)

    def test_birden_cok_tur(self):
        self.assertEqual(self.sonuc[("answer", "noun")], "A1")
        self.assertEqual(self.sonuc[("answer", "verb")], "A1")

    def test_ayni_kelime_turun_en_dusuk_seviyesi(self):
        # bank (money) A1, bank (river) B1 -> A1
        self.assertEqual(self.sonuc[("bank", "noun")], "A1")

    def test_bizde_karsiligi_olmayan_turler_atlanir(self):
        self.assertEqual(self.sonuc[("be", "verb")], "A1")
        self.assertNotIn(("another", "noun"), self.sonuc)
        self.assertNotIn(("a", "noun"), self.sonuc)

    def test_cok_kelimeli_ve_sonraki_seviye(self):
        self.assertEqual(self.sonuc[("all right", "adjective")], "B1")
        self.assertEqual(self.sonuc[("back", "verb")], "A2")
