"""Admin istatistik ekranı (rapor 18.31) ve karşılaşma özetleri (rapor 18.32)."""

from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from learnpass import ozet
from learnpass.models import EncounterLog, KarsilasmaOzeti
from LearnVocab import istatistik
from users.models import User
from words.testing import make_word


class OzetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ozet", password="Sifre1234")
        self.w = make_word("scatter", forms=False)

    def _log(self, gun_once, verdict="known", basamak=1):
        log = EncounterLog.objects.create(user=self.user, word=self.w, word_text="scatter",
                                          verdict=verdict, mode="mine", basamak_once=basamak)
        EncounterLog.objects.filter(pk=log.pk).update(created_at=timezone.now() - timedelta(days=gun_once))

    def test_90_gunden_eski_kisisiz_ozete_doner(self):
        self._log(100); self._log(100, "unknown"); self._log(100); self._log(10)
        self.assertEqual(ozet.ozetle(dry_run=True)["ozetlenen"], 3)
        self.assertEqual(EncounterLog.objects.count(), 4)
        call_command("karsilasma_ozetle", stdout=StringIO())
        self.assertEqual(EncounterLog.objects.count(), 1)                 # 10 günlük kaldı
        self.assertEqual(dict(KarsilasmaOzeti.objects.values_list("verdict", "sayi")),
                         {"known": 2, "unknown": 1})
        self.assertFalse(any(f.name in ("user", "word", "word_text")
                             for f in KarsilasmaOzeti._meta.get_fields()))
        self._log(100)                                                     # ikinci çalıştırma toplar
        ozet.ozetle()
        self.assertEqual(KarsilasmaOzeti.objects.get(verdict="known").sayi, 3)


class IstatistikTests(TestCase):
    def setUp(self):
        self.yonetici = User.objects.create_superuser(username="yonetici", password="Sifre1234",
                                                      email="y@example.com")
        self.w = make_word("scatter", forms=False)

    def _kisiler(self, n):
        for i in range(n):
            u = User.objects.create_user(username=f"k{i}", password="Sifre1234",
                                         email=f"gizli{i}@example.com")
            for verdict in ("known", "known", "known", "unknown"):
                EncounterLog.objects.create(user=u, word=self.w, word_text="scatter",
                                            verdict=verdict, mode="mine", basamak_once=1)

    def test_yalnizca_yonetici(self):
        self.assertEqual(self.client.get(reverse("admin_istatistik")).status_code, 302)
        u = User.objects.create_user(username="normal", password="Sifre1234")
        self.client.force_login(u)
        self.assertEqual(self.client.get(reverse("admin_istatistik")).status_code, 302)

    def test_bes_kisiden_azsa_oran_yok(self):
        self._kisiler(4)
        satir = istatistik.unutma_oranlari()[0][0]
        self.assertIsNone(satir["oran"])
        self.assertEqual(satir["toplam"], "16")

    def test_toplu_sayilar_ve_kisi_bilgisi_yok(self):
        self._kisiler(5)
        self.assertEqual(istatistik.unutma_oranlari()[0][0]["oran"], 25)
        self.client.force_login(self.yonetici)
        html = self.client.get(reverse("admin_istatistik")).content.decode()
        self.assertIn("%25", html)
        for gizli in ("k0", "gizli0@example.com", "scatter"):
            self.assertNotIn(gizli, html)
        self.assertIn(reverse("admin_istatistik"), self.client.get("/admin/").content.decode())

    def test_kucuk_sayi_gizlenir(self):
        self.assertEqual(istatistik.sayi(3), "<5")
        self.assertEqual(istatistik.sayi(0), "0")
        self.assertEqual(istatistik.sayi(12), "12")
