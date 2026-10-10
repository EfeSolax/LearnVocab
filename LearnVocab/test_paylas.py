"""Telefonda "Paylaş → LearnVocab" (rapor 11)."""
import json

from django.test import TestCase
from django.urls import reverse

from users.models import User


class PaylasTests(TestCase):
    def test_manifestte_paylasim_hedefi(self):
        veri = json.loads(self.client.get("/manifest.webmanifest").content)
        self.assertEqual(veri["share_target"]["action"], "/paylas/")
        self.assertEqual(veri["share_target"]["params"]["text"], "metin")

    def test_kisa_ifade_sozlukte_aranir(self):
        cevap = self.client.get("/paylas/", {"metin": '"Reshape" https://example.com/haber'})
        self.assertRedirects(cevap, f"{reverse('sozluk')}?q=reshape", fetch_redirect_response=False)
        cevap = self.client.get("/paylas/", {"metin": "give up"})
        self.assertEqual(cevap["Location"], f"{reverse('sozluk')}?q=give+up")

    def test_metin_yoksa_baslik_ya_da_sozluk(self):
        self.assertEqual(self.client.get("/paylas/", {"baslik": "memory"})["Location"],
                         f"{reverse('sozluk')}?q=memory")
        self.assertEqual(self.client.get("/paylas/", {"metin": "1234"})["Location"], reverse("sozluk"))

    def test_uzun_metin_kendi_metinlerime_gelir(self):
        User.objects.create_user(username="okur", password="Sifre1234")
        self.client.login(username="okur", password="Sifre1234")
        metin = "Scientists say the new findings could reshape how we think about memory."
        cevap = self.client.get("/paylas/", {"metin": metin})
        self.assertEqual(cevap["Location"], f"{reverse('readings_add')}?tur=yapistir")
        html = self.client.get(cevap["Location"]).content.decode()
        self.assertIn(metin, html)
        self.assertNotIn(metin, self.client.get(reverse("readings_add")).content.decode())  # bir kez
