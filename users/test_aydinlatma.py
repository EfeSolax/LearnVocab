"""KVKK aydınlatma metni (rapor 18.19): sayfa, kayıt onayı, Google ile ilk giriş."""
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from users.models import User
from users.sinyaller import ayarlari_olustur

VERI = {"first_name": "Ada", "last_name": "Yıldız", "email": "ada@example.com",
        "username": "ada", "password": "Sifre1234"}


@override_settings(KVKK_VERI_SORUMLUSU="Deneme Sorumlu", KVKK_ILETISIM_EPOSTASI="kvkk@example.com")
class AydinlatmaTests(TestCase):
    def test_sayfa_turkce_ve_ingilizce(self):
        html = self.client.get(reverse("gizlilik")).content.decode()
        for parca in ("Aydınlatma Metni", "Deneme Sorumlu", "mailto:kvkk@example.com", "Gemini", "m. 11"):
            self.assertIn(parca, html)
        with translation.override("en"):
            adres = reverse("gizlilik")
        self.assertTrue(adres.startswith("/en/"))
        self.assertIn("Privacy Notice", self.client.get(adres).content.decode())

    def test_kayit_sayfasinda_kutu_ve_baglanti(self):
        html = self.client.get(reverse("register")).content.decode()
        self.assertIn('name="aydinlatma"', html)
        self.assertIn(f'href="{reverse("gizlilik")}"', html)

    def test_onaysiz_kayit_acilmaz(self):
        cevap = self.client.post(reverse("register"), VERI)
        self.assertEqual(cevap.status_code, 400)
        self.assertIn("Aydınlatma Metni", cevap.content.decode())
        self.assertFalse(User.objects.filter(username="ada").exists())

    def test_onayli_kayit_ani_yazar(self):
        self.client.post(reverse("register"), {**VERI, "aydinlatma": "1"})
        self.assertIsNotNone(User.objects.get(username="ada").aydinlatma_okundu)

    def test_google_ile_ilk_giriste_ani_yazar(self):
        user = User.objects.create_user(username="g", email="g@example.com")
        ayarlari_olustur(sender=None, request=None, user=user)
        user.refresh_from_db()
        self.assertIsNotNone(user.aydinlatma_okundu)
