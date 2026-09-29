"""Seri kuralı (rapor 18.9): seri/hesap.py, seri/views.py, texts/gecerlilik.py."""

import json
from datetime import datetime, timedelta
from unittest import mock
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import User

from . import hesap
from .models import GunlukCalisma, SeriDurumu

IST = ZoneInfo("Europe/Istanbul")
BASLANGIC = datetime(2026, 9, 1, 10, 0, tzinfo=IST)


class _Zamanli(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="seri", password="Sifre1234")
        self.simdi = BASLANGIC

    def gun(self, n, saat=10):
        """n. güne (1'den başlar) git."""
        self.simdi = (BASLANGIC + timedelta(days=n - 1)).replace(hour=saat)

    def _saatte(self, fn, *a):
        with mock.patch.object(timezone, "now", return_value=self.simdi):
            return fn(*a)

    def say(self, tur, adet=1):
        return self._saatte(hesap.say, self.user, tur, adet)

    def durum(self):
        return self._saatte(hesap.durum, self.user)

    def tamamla(self, n):
        self.gun(n)
        self.say(hesap.LP, 10)


class GunTamamlamaTests(_Zamanli):
    def test_10_lp_tamamlar_9_tamamlamaz(self):
        self.assertFalse(self.say(hesap.LP, 9)["tamamlandi"])
        sonuc = self.say(hesap.LP)
        self.assertTrue(sonuc["tamamlandi"])
        self.assertTrue(sonuc["yeni_tamamlandi"])
        self.assertEqual(sonuc["mevcut"], 1)

    def test_lp_ve_egzersiz_toplanmaz(self):
        self.say(hesap.LP, 6)
        self.assertFalse(self.say(hesap.EGZERSIZ, 4)["tamamlandi"])
        self.assertTrue(self.say(hesap.EGZERSIZ, 6)["tamamlandi"])

    def test_bir_metin_ya_da_bir_diyalog_yeter(self):
        self.assertTrue(self.say(hesap.METIN)["tamamlandi"])
        self.gun(2)
        self.assertTrue(self.say(hesap.DIYALOG)["tamamlandi"])
        self.assertEqual(self.durum()["mevcut"], 2)

    def test_ayni_gun_ikinci_tamamlama_seriyi_artirmaz(self):
        self.say(hesap.LP, 10)
        sonuc = self.say(hesap.LP, 10)
        self.assertFalse(sonuc["yeni_tamamlandi"])
        self.assertEqual(sonuc["mevcut"], 1)

    def test_geri_al_sayaci_duser_tamamlanan_gun_kalir(self):
        self.say(hesap.LP, 3)
        self.assertEqual(self._saatte(hesap.geri_al, self.user, hesap.LP)["lp"], 2)
        self.say(hesap.LP, 8)
        self.assertTrue(self._saatte(hesap.geri_al, self.user, hesap.LP)["tamamlandi"])


class DondurmaTests(_Zamanli):
    def test_herkes_bir_hakla_baslar(self):
        self.assertEqual(self.durum()["hak"], 1)

    def test_kacirilan_gun_hakla_dondurulur_seri_artmaz(self):
        self.tamamla(1)
        self.tamamla(2)
        self.gun(4)   # 3. gün kaçırıldı
        d = self.durum()
        self.assertEqual((d["mevcut"], d["hak"]), (2, 0))
        self.assertTrue(GunlukCalisma.objects.get(user=self.user, gun=datetime(2026, 9, 3).date()).dondurulan)

    def test_hak_yoksa_seri_bozulur(self):
        SeriDurumu.objects.create(user=self.user, hak=0)
        self.tamamla(1)
        self.gun(3)
        d = self.durum()
        self.assertEqual((d["mevcut"], d["bozuldu"]), (0, True))

    def test_birden_cok_kacirilan_gun_birden_cok_hak(self):
        SeriDurumu.objects.create(user=self.user, hak=2)
        self.tamamla(1)
        self.gun(4)   # 2 ve 3 kaçırıldı
        self.assertEqual((self.durum()["mevcut"], self.durum()["hak"]), (1, 0))
        self.gun(5)   # 4 de kaçırıldı, hak yok
        self.assertEqual(self.durum()["mevcut"], 0)

    def test_serisi_olmayan_hak_harcamaz(self):
        self.gun(1)
        self.durum()
        self.gun(5)
        self.assertEqual(self.durum()["hak"], 1)

    def test_efenin_ornegi_12_gunde_hak(self):
        """1–6 yapıldı (5. günde +1), 7 atlandı (dondurma), 8–12 yapıldı (12. günde +1)."""
        for n in range(1, 7):
            self.tamamla(n)
        self.assertEqual(self.durum()["hak"], 2)
        for n in range(8, 12):
            self.tamamla(n)
        d = self.durum()
        self.assertEqual((d["hak"], d["mevcut"]), (1, 10))   # 7. gün 1 hak harcadı
        self.tamamla(12)
        self.assertEqual(self.durum()["hak"], 2)
        self.assertEqual(self.durum()["en_uzun"], 11)

    def test_en_cok_uc_hak(self):
        for n in range(1, 31):
            self.tamamla(n)
        self.assertEqual(self.durum()["hak"], 3)


class YerelSaatTests(_Zamanli):
    def test_gun_yerel_gece_yarisinda_biter(self):
        SeriDurumu.objects.create(user=self.user, saat_dilimi="America/New_York")
        # İstanbul 01.00 = New York'ta hâlâ bir önceki gün 18.00
        self.simdi = datetime(2026, 9, 2, 1, 0, tzinfo=IST)
        self.say(hesap.METIN)
        self.assertEqual(GunlukCalisma.objects.get(user=self.user).gun, datetime(2026, 9, 1).date())

    def test_saat_dilimi_ucu(self):
        self.client.login(username="seri", password="Sifre1234")
        url = reverse("seri_saat_dilimi")
        self.assertEqual(self.client.post(url, json.dumps({"saat_dilimi": "Mars/Olympus"}),
                                          content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post(url, json.dumps({"saat_dilimi": "Europe/London"}),
                                          content_type="application/json").status_code, 200)
        self.assertEqual(SeriDurumu.objects.get(user=self.user).saat_dilimi, "Europe/London")


class TakvimTests(_Zamanli):
    def test_durum_ucu_takvim_renkleri(self):
        self.tamamla(1)
        self.gun(3)   # 2 donduruldu
        self.client.login(username="seri", password="Sifre1234")
        with mock.patch.object(timezone, "now", return_value=self.simdi):
            veri = self.client.get(reverse("seri_durum"), {"yil": 2026, "ay": 9}).json()
        self.assertEqual(veri["gunler"], {"1": "tamam", "2": "dondurulan"})
        self.assertEqual((veri["mevcut"], veri["hak"], veri["en_uzun"]), (1, 0, 1))

    def test_ana_sayfada_seri_kutusu(self):
        self.tamamla(1)
        self.client.login(username="seri", password="Sifre1234")
        with mock.patch.object(timezone, "now", return_value=self.simdi):
            html = self.client.get(reverse("index")).content.decode()
        self.assertIn("data-seri-kutusu", html)
        self.assertIn("günlük seri", html)
        self.assertIn(reverse("seri_durum"), html)


IYI_METIN = (
    "Last summer I visited my grandmother in a small village near the sea. "
    "Every morning we walked to the market and bought fresh bread and fruit. "
    "In the afternoons I read books under an old tree in her garden. "
    "She told me many stories about her childhood and her friends. "
    "I learned how to cook a traditional soup with vegetables from her garden. "
    "It was a quiet holiday, but I will always remember those peaceful days."
)


class MetinGecerlilikTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="yazar", password="Sifre1234")

    def _kontrol(self, metin):
        from texts.gecerlilik import seriye_sayilir_mi
        return seriye_sayilir_mi(self.user, metin)

    def test_iyi_metin_sayilir(self):
        self.assertEqual(self._kontrol(IYI_METIN), (True, ""))

    def test_kisa_metin(self):
        self.assertFalse(self._kontrol("I like apples. They are good. Yes.")[0])

    def test_anlamsiz_harf_dizisi(self):
        self.assertFalse(self._kontrol(IYI_METIN + " Asdfghjkl qwrtzxcv aaaaaa.")[0])

    def test_ayni_cumle_tekrari(self):
        cumle = "I went to the market with my family and we bought many things. "
        self.assertFalse(self._kontrol(cumle * 6)[0])

    def test_ingilizce_olmayan_metin(self):
        turkce = ("Geçen yaz büyükannemi deniz kenarındaki küçük bir köyde ziyaret ettim. " * 1 +
                  "Her sabah pazara yürüdük ve taze ekmek aldık. Öğleden sonra kitap okudum. "
                  "Bana çocukluğunu anlattı. Bahçesinden sebzelerle çorba yapmayı öğrendim. "
                  "Sakin bir tatildi ama o günleri hep hatırlayacağım, gerçekten çok güzeldi.")
        self.assertFalse(self._kontrol(turkce)[0])

    def test_onceki_metnin_kopyasi(self):
        from texts.models import Text
        Text.objects.create(owner=self.user, content=IYI_METIN)
        self.assertFalse(self._kontrol(IYI_METIN)[0])
