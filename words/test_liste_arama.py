"""Hazır listede arama (Efe'nin isteği, 10 Ekim): yalnızca o listenin kelimeleri, yazdıkça."""
from django.test import TestCase
from django.urls import reverse

from words.models import HazirListe, HazirListeKelimesi
from words.testing import make_word


class ListeAramaTests(TestCase):
    def setUp(self):
        self.liste = HazirListe.objects.create(ad="Bilkent Intermediate", slug="bilkent-intermediate")
        kelimeler = [make_word("cabin", level="B1", meaning="kulübe"),
                     make_word("abandon", level="B2", meaning="terk etmek"),
                     make_word("absorb", level="B2", meaning="emmek")]
        for i, w in enumerate(kelimeler, start=1):
            HazirListeKelimesi.objects.create(liste=self.liste, word=w, sira=i)
        make_word("abroad", level="A2", meaning="yurt dışı")      # listede yok
        self.adres = reverse("hazir_liste", args=["bilkent-intermediate"])

    def _metinler(self, **parametre):
        cevap = self.client.get(self.adres, {"parca": "1", **parametre})
        html = cevap.content.decode()
        sirali = sorted((html.find(f">{k}<"), k) for k in ("cabin", "abandon", "absorb", "abroad") if f">{k}<" in html)
        return cevap, [k for _, k in sirali]

    def test_sayfada_arama_kutusu(self):
        html = self.client.get(self.adres).content.decode()
        self.assertIn("data-liste-ara-girdi", html)
        self.assertIn("3 kelime", html)

    def test_yalnizca_listedekiler_ve_bastan_eslesen_once(self):
        cevap, bulunan = self._metinler(ara="ab")
        self.assertEqual(bulunan, ["abandon", "absorb", "cabin"])     # abroad listede değil
        self.assertEqual(cevap["X-Sonuc-Sayisi"], "3")

    def test_turkce_anlamda_arar(self):
        _, bulunan = self._metinler(ara="kulübe")
        self.assertEqual(bulunan, ["cabin"])

    def test_eslesme_yoksa_mesaj(self):
        cevap, bulunan = self._metinler(ara="zzz")
        self.assertEqual(bulunan, [])
        self.assertIn("eşleşen kelime yok", cevap.content.decode())

    def test_bos_arama_hepsini_liste_sirasiyla_verir(self):
        _, bulunan = self._metinler()
        self.assertEqual(bulunan, ["cabin", "abandon", "absorb"])
