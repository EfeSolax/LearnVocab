"""Öğrenme önceliği (words/oncelik.py, manage.py oncelik_hesapla)."""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from words.models import HazirListe, HazirListeKelimesi, Word
from words.oncelik import kurum_adi, oncelik_puani
from words.testing import make_word


class PuanTests(TestCase):
    def test_sik_ve_resmi_listedeki_kelime_one_gecer(self):
        self.assertGreater(oncelik_puani(5.5, "oxford"), oncelik_puani(5.5, "learnvocab"))
        self.assertGreater(oncelik_puani(5.5), oncelik_puani(2.5))
        self.assertGreater(oncelik_puani(4, "oxford"), oncelik_puani(4, "cambridge"))

    def test_kurum_payi_sinirli(self):
        self.assertEqual(oncelik_puani(4, kurum_sayisi=9) - oncelik_puani(4), 15)

    def test_turev_ve_ikinci_tur_cezasi(self):
        self.assertEqual(oncelik_puani(4, aile_en_sik=5.2), oncelik_puani(4) - 10)
        self.assertEqual(oncelik_puani(4, aile_en_sik=4.5), oncelik_puani(4))
        self.assertEqual(oncelik_puani(4, ikinci_tur=True), oncelik_puani(4) - 15)

    def test_sinirlar(self):
        self.assertEqual(oncelik_puani(None), 0)
        self.assertEqual(oncelik_puani(9, "oxford", 5), 95)

    def test_kurum_adi(self):
        self.assertEqual(kurum_adi("ODTÜ 202 Span 3"), "ODTÜ")
        self.assertIsNone(kurum_adi("Phrasal Verbs"))


class KomutTests(TestCase):
    def test_hesaplar_ve_yazar(self):
        lively = make_word("lively", level="B1", siklik=4.5, family="lively", cefr_kaynak="oxford")
        liveliness = make_word("liveliness", level="B2", siklik=2.5, family="lively")
        it = make_word("it", pos="pronoun", level="A1", siklik=7.0)
        it_kisaltma = make_word("IT", level="B1", siklik=7.0)
        for ad in ("ODTÜ 101 Span 1", "ODTÜ 201 Span 1", "Bilkent Elementary"):
            liste = HazirListe.objects.create(ad=ad, slug=ad.lower().replace(" ", "-"))
            HazirListeKelimesi.objects.create(liste=liste, word=lively)

        call_command("oncelik_hesapla", stdout=StringIO())
        p = dict(Word.objects.values_list("id", "oncelik"))
        self.assertEqual(p[lively.id], oncelik_puani(4.5, "oxford", kurum_sayisi=2))   # ODTÜ tek kurum
        self.assertEqual(p[liveliness.id], oncelik_puani(2.5, aile_en_sik=4.5))
        self.assertEqual(p[it_kisaltma.id], oncelik_puani(7.0, ikinci_tur=True))
        self.assertGreater(p[it.id], p[it_kisaltma.id])

    def test_dry_run_yazmaz(self):
        w = make_word("house", level="A1", siklik=5.5)
        call_command("oncelik_hesapla", "--dry-run", stdout=StringIO())
        w.refresh_from_db()
        self.assertIsNone(w.oncelik)
