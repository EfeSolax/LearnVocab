"""Kural tabanlı veri denetimi (rapor 18.6, 18.7)."""

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from words.models import WordRelation
from words.testing import make_word
from words.veri_kurallari import daha_basit_nedeni, es_zit_catismalari


class DahaBasitKuraliTests(SimpleTestCase):
    def test_hedef_a1_b1_ve_kaynaktan_alt_ise_kalir(self):
        self.assertIsNone(daha_basit_nedeni("B2", "B1"))
        self.assertIsNone(daha_basit_nedeni("B1", "A2"))

    def test_hedef_b2_ustu_silinir(self):
        self.assertEqual(daha_basit_nedeni("C1", "B2"), "hedef B2 ya da üstü")

    def test_ayni_ya_da_ust_seviye_silinir(self):
        # go (A1) -> leave (A1) / (A2)
        self.assertEqual(daha_basit_nedeni("A1", "A1"), "hedef kaynaktan alt seviyede değil")
        self.assertEqual(daha_basit_nedeni("A1", "A2"), "hedef kaynaktan alt seviyede değil")

    def test_seviyesiz(self):
        self.assertEqual(daha_basit_nedeni("B1", "Belirtilmemiş"), "hedefin seviyesi yok")


class VeriTaraKomutuTests(TestCase):
    def test_komut_yalnizca_kurala_uymayanlari_siler(self):
        kaynak = make_word("purchase", pos="verb", level="B2")
        buy = make_word("buy", pos="verb", level="A1")
        acquire = make_word("acquire", pos="verb", level="B2")
        anlam = kaynak.meanings.first()
        anlam.cefr = "B2"
        anlam.save()
        WordRelation.objects.create(from_word=kaynak, to_word=buy, type="simpler", meaning=anlam)
        WordRelation.objects.create(from_word=kaynak, to_word=acquire, type="simpler", meaning=anlam)
        call_command("veri_tara", stdout=open("/dev/null", "w"))
        kalan = set(WordRelation.objects.filter(type="simpler").values_list("to_word__text", flat=True))
        self.assertEqual(kalan, {"buy"})

    def test_es_zit_catismasi_bulunur(self):
        a = make_word("despairing", pos="adjective")
        b = make_word("hopeless", pos="adjective")
        anlam = a.meanings.first()
        WordRelation.objects.create(from_word=a, to_word=b, type="synonym", meaning=anlam)
        WordRelation.objects.create(from_word=a, to_word=b, type="antonym", meaning=anlam)
        self.assertEqual(es_zit_catismalari(), [(anlam.id, b.id)])
