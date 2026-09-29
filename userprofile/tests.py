"""
Profil uygulamasının testleri.

Eski Kelimelerim sayfası, elle kelime ekleme/düzenleme formu, kelime
klasörleri ve toplu işlemler 29 Eylül'de kaldırıldı (rapor 18.13); onların
testleri de gitti. Kalan: Profilim sayfası (words/tests.py
MergedProfilePageTests) ve arkadaşlık için profil görüntüleme.
"""

from django.test import TestCase
from django.urls import reverse

from users.models import User


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="profiluser", password="Sifre1234")

    def test_profile_page_opens_for_its_owner(self):
        self.client.login(username="profiluser", password="Sifre1234")
        self.assertEqual(self.client.get(reverse("user_profile")).status_code, 200)

    def test_profile_page_is_gated_for_visitors(self):
        html = self.client.get(reverse("user_profile")).content.decode()
        self.assertIn("önce giriş yapın", html)

    def test_show_user_profile_still_resolves(self):
        cevap = self.client.get(reverse("show_user_profile", args=[self.user.id]))
        self.assertEqual(cevap.status_code, 200)
