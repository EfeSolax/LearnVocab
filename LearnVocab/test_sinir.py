"""İstek sınırları (8 Ekim): herkese açık uçlar, giriş ve kayıt, bulunamayan kaydı."""
from unittest.mock import patch

from django.core.cache import caches
from django.test import TestCase, override_settings
from django.urls import reverse

from users.models import User
from words.models import BulunamayanArama

SINIRLI = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "v"},
           "sinir": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "s"}}


@override_settings(CACHES=SINIRLI)
class SinirTests(TestCase):
    def setUp(self):
        caches["sinir"].clear()
        caches["default"].clear()

    def test_kelime_api_dakikalik_sinir(self):
        with patch("readings.api.KELIME_SINIRI", 3):
            kodlar = [self.client.get("/api/kelime/?q=bank").status_code for _ in range(4)]
        self.assertEqual(kodlar[:3], [200, 200, 200])
        self.assertEqual(kodlar[3], 429)

    def test_bulunamayan_adres_basina_yeni_satir_sinirli(self):
        from words import arama
        with patch.object(arama, "BULUNAMAYAN_ADRES_SAATTE", 2):
            for i in range(5):
                arama.bulunamayan_kaydet(f"zzqword{i}", istemci="1.2.3.4")
            self.assertEqual(BulunamayanArama.objects.count(), 2)
            arama.bulunamayan_kaydet("zzqword0", istemci="1.2.3.4")   # var olan satır sayılır
        self.assertEqual(BulunamayanArama.objects.get(sorgu="zzqword0").sayi, 2)

    def test_hatali_giris_hesabi_kilitler(self):
        User.objects.create_user(username="ali", email="ali@example.com", password="Dogru1234")
        with patch("users.views.GIRIS_HESAP_SINIRI", 3):
            for _ in range(3):
                self.client.post(reverse("login"), {"username": "ali", "password": "yanlis"})
            # Sınırdan sonra doğru şifre de bir süre kabul edilmez.
            self.client.post(reverse("login"), {"username": "ali", "password": "Dogru1234"})
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_kayit_adres_sinir(self):
        with patch("users.views.KAYIT_ADRES_SINIRI", 1):
            self.client.post(reverse("register"), {"first_name": "a", "last_name": "b", "username": "u1",
                                                   "email": "u1@example.com", "password": "Sifre1234", "aydinlatma": "1"})
            cevap = self.client.post(reverse("register"), {"first_name": "a", "last_name": "b",
                                                           "username": "u2", "email": "u2@example.com",
                                                           "password": "Sifre1234", "aydinlatma": "1"})
        self.assertEqual(cevap.status_code, 429)
        self.assertFalse(User.objects.filter(username="u2").exists())
