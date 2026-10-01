"""Günün kelimesi ve günün ifadesi (rapor 18.8): words/gunun.py."""

import random
from datetime import date, timedelta

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from learnpass.models import WordEncounter
from users.models import User
from words import gunun
from words.ifadeler.bilinirlik import bilinirlik
from words.models import Expression, ExpressionExample, GununKelimesi, UserExpressionLink, UserWordLink, Word
from words.testing import make_word


def zengin(text, level="B1", **ek):
    """Günün kelimesi olabilecek kelime: 2 örnek, bir eş dizim, sıklık."""
    ek.setdefault("siklik", 4.0)
    return make_word(text, level=level, meaning=f"{text}-tr",
                     sentences=[f"One {text}.", f"Two {text}."],
                     collocations=[(f"big {text}", "adj_noun")], forms=False, **ek)


class SecimTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="gk", password="Sifre1234", cefr="B1")

    def test_zayif_veri_gelmez(self):
        make_word("thin", level="B1", siklik=4.0, forms=False)                 # tek örnek, eş dizim yok
        zengin("rare", siklik=1.5)                                             # çok seyrek
        zengin("nadir", nadir_tur=True)
        zengin("give up", pos="phrasal_verb")                                  # tek sözcük değil
        self.assertIsNone(gunun.misafir_kelimesi())
        iyi = zengin("habit")
        self.assertEqual(gunun.misafir_kelimesi(date(2026, 10, 2)), iyi)

    def test_google_acik_ve_oxford_once(self):
        zengin("plain")
        acik = zengin("chosen", cefr_kaynak="oxford", dizinde=True)
        for i in range(10):
            self.assertEqual(gunun.misafir_kelimesi(date(2026, 10, 1) + timedelta(days=i)), acik)

    def test_misafire_herkese_ayni_ve_b1(self):
        zengin("bone", level="B1")
        zengin("cat", level="A1")
        gun = date(2026, 10, 5)
        self.assertEqual(gunun.misafir_kelimesi(gun), gunun.misafir_kelimesi(gun))
        self.assertEqual(gunun.misafir_kelimesi(gun).cefr, "B1")

    def test_kullaniciya_gorulmemis_ve_gun_boyu_ayni(self):
        gorulen = zengin("seen")
        listede = zengin("listed")
        yeni = zengin("fresh")
        WordEncounter.objects.create(user=self.user, word=gorulen, last_verdict="known")
        UserWordLink.objects.create(user=self.user, word=listede)
        self.assertEqual(gunun.gunun_kelimesi(self.user), yeni)
        self.assertEqual(gunun.gunun_kelimesi(self.user), yeni)
        self.assertEqual(GununKelimesi.objects.filter(user=self.user).count(), 1)

    def test_seviyeye_gore_ve_sik_olan_daha_sik(self):
        self.user.cefr = "C1"
        self.user.save()
        zengin("mundane", level="C1", siklik=2.5)
        zengin("notion", level="C1", siklik=4.5)
        zengin("bread", level="A1")
        sayac = {"mundane": 0, "notion": 0}
        rng = random.Random(1)
        for _ in range(200):
            satirlar = gunun._adaylar("C1")
            sayac[Word.objects.get(pk=gunun._agirlikli_sec(satirlar, rng)).text] += 1
        self.assertGreater(sayac["notion"], sayac["mundane"] * 2)


class KartTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="kart", password="Sifre1234", cefr="B1")
        self.kelime = zengin("habit")
        self.client.force_login(self.user)

    def _cevap(self, cevap):
        return self.client.post(reverse("gunun_kelimesi_cevap"), {"cevap": cevap},
                                HTTP_X_REQUESTED_WITH="fetch")

    def test_kart_ana_sayfada_ve_keşfette_ayni(self):
        for ad in ("index", "sozluk"):
            html = self.client.get(reverse(ad)).content.decode()
            self.assertIn(f'data-gunun-kelimesi="{self.kelime.id}"', html)
            self.assertIn("✓ biliyordum", html)
            self.assertIn("✗ bilmiyordum", html)
            self.assertIn('href="/sozluk/habit/"', html)
            self.assertIn("data-telaffuz-grubu", html)

    def test_biliyordum_kaydeder_ve_karti_kapatir(self):
        cevap = self._cevap("known").json()
        self.assertEqual((cevap["tamam"], cevap["cevap"]), (True, "known"))
        enc = WordEncounter.objects.get(user=self.user, word=self.kelime)
        self.assertEqual((enc.last_verdict, enc.last_mode, enc.takipte), ("known", "new", False))
        html = self.client.get(reverse("index")).content.decode()
        kart = html[html.index("data-gunun-kelimesi"):]
        self.assertIn("Bugünün kelimesi tamam ✓, yarın yenisi gelecek.", kart[:kart.index("data-gunun-icerik")])
        self.assertIn('data-gunun-icerik hidden', kart)

    def test_bilmiyordum_takibe_alir_kart_acik_kalir(self):
        cevap = self._cevap("unknown").json()
        self.assertEqual(cevap["tamam"], False)
        enc = WordEncounter.objects.get(user=self.user, word=self.kelime)
        self.assertTrue(enc.takipte)
        html = self.client.get(reverse("index")).content.decode()
        self.assertNotIn('data-gunun-cevap="', html)                    # bir kez cevaplanır
        self.assertIn("Tekrarlarına eklendi", html)
        # İkinci cevap bir şey değiştirmez
        self._cevap("known")
        self.assertEqual(WordEncounter.objects.get(user=self.user, word=self.kelime).times_seen, 1)

    def test_listeye_eklenince_kapanir(self):
        self.assertEqual(gunun.gunun_kelimesi(self.user), self.kelime)
        UserWordLink.objects.create(user=self.user, word=self.kelime)
        self.assertTrue(gunun.kelime_durumu(self.user)["tamam"])

    def test_gecersiz_cevap_ve_misafir(self):
        self.assertEqual(self._cevap("belki").status_code, 400)
        self.client.logout()
        self.assertEqual(self._cevap("known").status_code, 302)
        html = self.client.get(reverse("index")).content.decode()
        self.assertIn("data-gunun-kelimesi", html)
        self.assertNotIn('data-gunun-cevap="', html)                    # misafirde düğme yok


class IfadeTests(TestCase):
    def setUp(self):
        self.yaygin = Expression.objects.create(text="however", meaning_tr="ancak", cefr="B1",
                                                visibility="public", bilinirlik="yaygin")
        self.az = [Expression.objects.create(text=f"az {i}", meaning_tr="x", cefr="C1",
                                             visibility="public", bilinirlik="az") for i in range(5)]

    def test_bilinirlik_kurali(self):
        self.assertEqual(bilinirlik("but", "A1"), "yaygin")
        self.assertEqual(bilinirlik("however", "B1"), "yaygin")
        self.assertEqual(bilinirlik("after all", "B1"), "az")
        self.assertEqual(bilinirlik("hence", "C1"), "az")

    def test_yalnizca_az_bilinen_ve_dongu(self):
        gun = date(2026, 10, 1)
        gorulen = [gunun.gunun_ifadesi(gun + timedelta(days=i)).id for i in range(5)]
        self.assertEqual(sorted(gorulen), sorted(e.id for e in self.az))    # 5 günde hepsi bir kez
        self.assertEqual(gunun.gunun_ifadesi(gun + timedelta(days=5)).id, gorulen[0])
        self.assertNotIn(self.yaygin.id, gorulen)

    def test_listeye_eklenince_kapanir(self):
        user = User.objects.create_user(username="ifade", password="Sifre1234")
        self.assertFalse(gunun.ifade_durumu(user)["tamam"])
        self.client.force_login(user)
        ifade = gunun.gunun_ifadesi()
        self.client.post(reverse("add_expression_to_my_list", args=[ifade.id]), HTTP_X_REQUESTED_WITH="fetch")
        self.assertTrue(UserExpressionLink.objects.filter(user=user, expression=ifade).exists())
        self.assertTrue(gunun.ifade_durumu(user)["tamam"])
        self.assertIn("Bugünün ifadesi tamam ✓", self.client.get(reverse("index")).content.decode())

    def test_ifade_sayfasi_iki_ornekle_acilir(self):
        from words.dizine_alma import uygun_ifadeler
        e = self.az[0]
        ExpressionExample.objects.create(expression=e, text="One.")
        self.assertNotIn(e, uygun_ifadeler())
        ExpressionExample.objects.create(expression=e, text="Two.")
        self.assertIn(e, uygun_ifadeler())
