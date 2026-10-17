"""Chrome eklentisi (rapor 11): girişli bilgisi, Listeme ekle ucu ve kaynak denetimi."""
from django.test import TestCase, override_settings
from django.urls import reverse

from users.models import User
from words.models import UserWordLink
from words.testing import make_word

KAYNAK = "chrome-extension://abcdefghijklmnopabcdefghijklmnop"


@override_settings(EKLENTI_KAYNAKLARI=(KAYNAK,))
class EklentiTests(TestCase):
    def setUp(self):
        self.kelime = make_word("reshape", level="B2", meaning="yeniden şekillendirmek")
        self.user = User.objects.create_user(username="okur", password="Sifre1234")
        self.adres = reverse("eklenti_listem", args=[self.kelime.id])

    def test_kelime_cevabi_girisi_soyler(self):
        self.assertFalse(self.client.get("/api/kelime/?q=reshape").json()["girisli"])
        self.client.login(username="okur", password="Sifre1234")
        self.assertTrue(self.client.get("/api/kelime/?q=reshape").json()["girisli"])

    def test_eklentiden_ekler_ve_cikarir(self):
        self.client.login(username="okur", password="Sifre1234")
        cevap = self.client.post(self.adres, HTTP_ORIGIN=KAYNAK)
        self.assertEqual(cevap.json(), {"ok": True, "kayitli": True})
        self.assertTrue(UserWordLink.objects.filter(user=self.user, word=self.kelime).exists())
        cevap = self.client.delete(self.adres, HTTP_ORIGIN=KAYNAK)
        self.assertFalse(cevap.json()["kayitli"])
        self.assertFalse(UserWordLink.objects.filter(user=self.user).exists())

    def test_baska_kaynak_ve_kaynaksiz_istek_reddedilir(self):
        self.client.login(username="okur", password="Sifre1234")
        for kaynak in ("https://kotu.example", None):
            ek = {"HTTP_ORIGIN": kaynak} if kaynak else {}
            self.assertEqual(self.client.post(self.adres, **ek).status_code, 403)
        self.assertFalse(UserWordLink.objects.exists())

    def test_girissiz_401(self):
        cevap = self.client.post(self.adres, HTTP_ORIGIN=KAYNAK)
        self.assertEqual(cevap.status_code, 401)
        self.assertTrue(cevap.json()["giris"])

    def test_get_kabul_edilmez(self):
        self.assertEqual(self.client.get(self.adres, HTTP_ORIGIN=KAYNAK).status_code, 405)

    def test_ana_sayfada_eklenti_bolumu(self):
        html = self.client.get(reverse("index")).content.decode()
        self.assertIn('id="eklenti"', html)
        self.assertIn("Chrome Web Store", html)
        with self.settings(EKLENTI_ADRESI="https://chromewebstore.google.com/detail/learnvocab/x"):
            html = self.client.get(reverse("index")).content.decode()
        self.assertIn("https://chromewebstore.google.com/detail/learnvocab/x", html)
