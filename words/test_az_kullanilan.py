"""Az kullanılan kelimeler ve C2 düzeltmesi (20 Ekim; Word.az_kullanilan, words/duzeltmeler/d_2026_10_20.py)."""

import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from learnpass import tekrar
from users.models import User
from words import gozat
from words.duzeltmeler import d_2026_10_20 as d
from words.kart import kart_verisi
from words.models import Word
from words.testing import make_word


class AzKullanilanTests(TestCase):
    def setUp(self):
        self.az = make_word("corolla", level="C2", siklik=3.2, az_kullanilan=True)

    def test_kartta_seviye_yerine_az_kullanilan(self):
        kart = kart_verisi([self.az.id])[0]
        self.assertEqual((kart.cefr, kart.az_kullanilan), ("", True))
        html = self.client.get(reverse("sozluk_kelime", args=[self.az.slug])).content.decode()
        self.assertIn("az kullanılan", html)
        self.assertNotIn('class="lv-seviye', html.split("<main", 1)[1].split("</header>", 1)[0])
        self.assertNotIn("C2 kelimeleri", html)   # yol çubuğu seviye sayfasına götürmez

    def test_learn_and_pass_ve_seviye_gozatmaya_girmez(self):
        user = User.objects.create_user(username="c2", password="Sifre1234x", cefr="C2")
        self.assertIsNone(tekrar.yeni_kelime(user))
        self.assertNotIn(self.az, list(gozat.seviye_kelimeleri("C2")))

    def test_oncelik_sifir(self):
        call_command("oncelik_hesapla", stdout=StringIO())
        self.az.refresh_from_db()
        self.assertEqual(self.az.oncelik, 0)


class C2DuzeltmeTests(TestCase):
    def test_karar_dosyalari_okunur(self):
        kararlar = d.c2_kararlari()
        self.assertIn(("corolla", None), kararlar["A"])
        self.assertIn(("penitent", "adjective"), kararlar["K"])
        self.assertIn(("mull over", None), d.tasinacaklar())
        self.assertIn(("purport", "verb"), d.tasinacaklar())

    def test_uygular_ve_tekrar_calistirmak_guvenli(self):
        corolla = make_word("corolla", level="C2")
        wan = make_word("wan", pos="adjective", level="C2")
        beseech = make_word("beseech", pos="verb", level="C1")
        resmi = make_word("abate", pos="verb", level="B2", cefr_kaynak="oxford")   # resmî etiket taşınmaz
        with tempfile.TemporaryDirectory() as dizin, \
                mock.patch.object(d, "UYGULANAN", Path(dizin) / "uygulanan.tsv"):
            d.c2_duzelt(kuru=True)
            corolla.refresh_from_db()
            self.assertFalse(corolla.az_kullanilan)          # kuru deneme yazmaz

            d.c2_duzelt()
            self.assertTrue((Path(dizin) / "uygulanan.tsv").exists())
            ikinci = d.c2_duzelt()
        sonuc = {w.text: (w.cefr, w.az_kullanilan) for w in Word.objects.filter(
            pk__in=[corolla.pk, wan.pk, beseech.pk, resmi.pk])}
        self.assertEqual(sonuc, {"corolla": ("C2", True), "wan": ("C2", False),
                                 "beseech": ("C2", False), "abate": ("B2", False)})
        self.assertNotIn("az kullanılan", ikinci)
        self.assertNotIn("C1 -> C2", ikinci)
