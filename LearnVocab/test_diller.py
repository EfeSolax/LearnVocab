"""
Dil seçeneği ve "Türkçe anlamlar" ayarı (rapor 18.22; LearnVocab/diller.py, usersettings/anlam.py).
"""

import json
import random

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from learnpass.views import card_payload
from users.models import User
from usersettings.models import UserSettings
from words.models import UserWordLink
from words.testing import make_word

UC_DIL = [("tr", "Türkçe"), ("en", "English"), ("de", "Deutsch")]
SIFRE = "Sifre1234"


@override_settings(LANGUAGES=UC_DIL)
class DilDugmesiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="dil", password=SIFRE, email="d@x.com")

    def test_ceviriler_yuklu(self):
        with translation.override("en"):
            self.assertEqual(translation.gettext("Sözlük"), "Dictionary")
        with translation.override("de"):
            self.assertEqual(translation.gettext("Sözlük"), "Wörterbuch")

    def test_ingilizce_sayfa_ingilizce(self):
        html = self.client.get("/en/sozluk/").content.decode()
        self.assertIn('<html lang="en"', html)
        self.assertIn("Dictionary", html)
        self.assertNotIn(">Sözlük<", html)

    def test_dugme_uc_dili_listeler(self):
        html = self.client.get("/sozluk/").content.decode()
        self.assertIn("data-dil-dugmesi", html)
        for ad in ("Türkçe", "English", "Deutsch"):
            self.assertIn(ad, html)

    def test_dil_degistir_ayni_sayfanin_o_dildeki_adresine_gider(self):
        cevap = self.client.post(reverse("dil_degistir"), {"dil": "de", "next": "/sozluk/"})
        self.assertRedirects(cevap, "/de/sozluk/", fetch_redirect_response=False)
        self.assertEqual(cevap.cookies["django_language"].value, "de")

    def test_onekli_sayfadan_her_dile_gecilir(self):
        # /dil/ öneksizdir; önekli sayfadan gelindiğinde adres yine de çevrilmeli (Efe, 5 Ekim).
        for sonraki, dil, beklenen in (("/en/sozluk/", "de", "/de/sozluk/"), ("/en/sozluk/", "tr", "/sozluk/"),
                                       ("/de/schreiben/", "en", "/en/writings/"), ("/de/", "tr", "/"),
                                       ("/en/sozluk/bank/", "de", "/de/sozluk/bank/")):
            with self.subTest(sonraki=sonraki, dil=dil):
                cevap = self.client.post(reverse("dil_degistir"), {"dil": dil, "next": sonraki})
                self.assertRedirects(cevap, beklenen, fetch_redirect_response=False)

    def test_yazilar_adresi_de_cevrilir(self):
        cevap = self.client.post(reverse("dil_degistir"), {"dil": "en", "next": "/yazilar/"})
        self.assertRedirects(cevap, "/en/writings/", fetch_redirect_response=False)

    def test_girisli_kullanicida_hesaba_yazilir_ve_giriste_kullanilir(self):
        self.client.login(username="dil", password=SIFRE)
        self.client.post(reverse("dil_degistir"), {"dil": "en", "next": "/"})
        self.assertEqual(UserSettings.objects.get(user=self.user).arayuz_dili, "en")
        self.client.logout()
        cevap = self.client.post(reverse("login"), {"username": "dil", "password": SIFRE})
        self.assertRedirects(cevap, "/en/", fetch_redirect_response=False)

    def test_gecersiz_dil_ve_dis_adres(self):
        cevap = self.client.post(reverse("dil_degistir"), {"dil": "xx", "next": "/sozluk/"})
        self.assertRedirects(cevap, "/sozluk/", fetch_redirect_response=False)
        cevap = self.client.post(reverse("dil_degistir"), {"dil": "en", "next": "https://kotu.example/"})
        self.assertRedirects(cevap, "/en/", fetch_redirect_response=False)

    def test_tarayici_dili_icin_yonlendirme_yok_yalnizca_oneri(self):
        cevap = self.client.get("/sozluk/", HTTP_ACCEPT_LANGUAGE="de-DE,de;q=0.9")
        self.assertEqual(cevap.status_code, 200)            # yönlendirme yok
        html = cevap.content.decode()
        self.assertIn("data-dil-onerisi", html)
        self.assertIn("Diese Seite gibt es auch auf Deutsch.", html)
        self.client.cookies["django_language"] = "tr"        # bir kez seçim yapıldıysa öneri yok
        html = self.client.get("/sozluk/", HTTP_ACCEPT_LANGUAGE="de").content.decode()
        self.assertNotIn("data-dil-onerisi", html)


@override_settings(LANGUAGES=UC_DIL)
class HazirListeDiliTests(TestCase):
    def test_liste_adi_ve_aciklamasi_sayfanin_dilinde(self):
        from words.models import HazirListe
        HazirListe.objects.create(ad="Örnek", slug="ornek", aciklama="Türkçe açıklama", ad_en="Sample",
                                  aciklama_en="English description", yayinda=True)
        tr = self.client.get("/listeler/ornek/").content.decode()
        self.assertIn("Türkçe açıklama", tr)
        en = self.client.get("/en/listeler/ornek/").content.decode()
        self.assertIn(">Sample<", en)
        self.assertIn("English description", en)
        self.assertNotIn("Türkçe açıklama", en)
        de = self.client.get("/de/listeler/ornek/").content.decode()   # Almancası yok: Türkçesi
        self.assertIn(">Örnek<", de)


@override_settings(LANGUAGES=UC_DIL)
class OkumaKaynagiDiliTests(TestCase):
    def test_ornek_metin_kaynagi_sayfanin_dilinde(self):
        from readings.models import ReadingText
        ReadingText.objects.create(number=1, topic="bilim", title="Names", body="Text.",
                                   source="Örnek metin (LearnVocab, Claude tarafından yazıldı)")
        with translation.override("en"):
            self.assertEqual(str(ReadingText.objects.get().yerel_kaynak), "Sample text (LearnVocab, written by Claude)")
        with translation.override("tr"):
            self.assertIn("Claude tarafından", str(ReadingText.objects.get().yerel_kaynak))
        self.assertEqual(ReadingText(source="BBC").yerel_kaynak, "BBC")


@override_settings(LANGUAGES=UC_DIL)
class SiteHaritasiTests(TestCase):
    def test_her_dil_adresi_ve_hreflang(self):
        xml = self.client.get("/sitemap.xml").content.decode()
        self.assertIn('xmlns:xhtml="http://www.w3.org/1999/xhtml"', xml)
        for adres in ("/sozluk/", "/en/sozluk/", "/de/sozluk/"):
            self.assertIn(f"<loc>https://www.learnvocab.com.tr{adres}</loc>", xml)
        self.assertIn('hreflang="de" href="https://www.learnvocab.com.tr/de/sozluk/"', xml)
        self.assertIn('hreflang="x-default" href="https://www.learnvocab.com.tr/sozluk/"', xml)


class TekDilTests(TestCase):
    @override_settings(LANGUAGES=[("tr", "Türkçe")])
    def test_tek_dil_yayindayken_dugme_ve_oneri_yok(self):
        html = self.client.get("/sozluk/", HTTP_ACCEPT_LANGUAGE="en").content.decode()
        self.assertNotIn("data-dil-dugmesi", html)
        self.assertNotIn("data-dil-onerisi", html)


class TurkceAnlamlarTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="tr", password=SIFRE)
        cls.kelimeler = [make_word(f"kelime{chr(97 + i)}", meaning=f"türkçe{i}", definition=f"english definition {i}",
                                   sentences=["One.", "Two."]) for i in range(6)]
        for w in cls.kelimeler:
            UserWordLink.objects.create(user=cls.user, word=w)

    def _kapat(self):
        UserSettings.objects.update_or_create(user=self.user, defaults={"turkce_anlamlar": False})
        self.client.login(username="tr", password=SIFRE)

    def test_ayarlardan_kapatilir(self):
        self.client.login(username="tr", password=SIFRE)
        self.client.post(reverse("save_settings"), {})
        self.assertFalse(UserSettings.objects.get(user=self.user).turkce_anlamlar)
        self.client.post(reverse("save_settings"), {"turkce_anlamlar": "on"})
        self.assertTrue(UserSettings.objects.get(user=self.user).turkce_anlamlar)

    def test_ayarlar_kendiliginden_kaydedilir_ve_turkce_anlamlar_dilin_altinda(self):
        # Efe, 5 Ekim: kaydet düğmesi yok; "Türkçe anlamlar" görülsün diye Dil'in hemen altında.
        self.client.login(username="tr", password=SIFRE)
        html = self.client.get(reverse("settings_page")).content.decode()
        self.assertIn("data-otomatik-kayit", html)
        self.assertNotIn('<button type="submit" class="lv-dugme">', html.split("<noscript>")[0].split('id="ayarlar-formu"')[1])
        turkce = html.index("data-turkce-anlamlar-ayari")
        self.assertLess(turkce, html.index("data-seviye-ayari"))
        self.assertIn('name="turkce_anlamlar" class="peer sr-only" checked form="ayarlar-formu"', html)
        cevap = self.client.post(reverse("save_settings"), {"learnpass_yeni_orani": "40"},
                                 HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(cevap.json(), {"tamam": True})
        ayar = UserSettings.objects.get(user=self.user)
        self.assertEqual(ayar.learnpass_yeni_orani, 40)
        self.assertFalse(ayar.turkce_anlamlar)

    def test_kelime_sayfasinda_turkce_yok_aciklama_var(self):
        self.client.login(username="tr", password=SIFRE)
        self.assertIn("türkçe0", self.client.get("/sozluk/kelimea/").content.decode())
        self._kapat()
        html = self.client.get("/sozluk/kelimea/").content.decode()
        self.assertNotIn("türkçe0", html)
        self.assertIn("english definition 0", html)

    def test_listem_ve_learn_pass_aciklamayla(self):
        self._kapat()
        html = self.client.get(reverse("sozluk"), {"sekme": "listem"}).content.decode()
        self.assertNotIn("türkçe1", html)
        self.assertIn("english definition 1", html)
        self.user._turkce_anlamlar = None
        self.assertEqual(card_payload(self.kelimeler[1], self.user)["meanings"], ["english definition 1"])

    def test_kisa_sinav_aciklama_sorar_deneme_sinavi_anlam_tipini_kapatir(self):
        from egzersizler import sorular as S
        UserSettings.objects.update_or_create(user=self.user, defaults={"turkce_anlamlar": False})
        sorular = S.hizli_sorular(self.user, random.Random(1))
        self.assertTrue(sorular)
        self.assertTrue(all(s["tip"] == S.TIP_ACIKLAMA for s in sorular))
        self.assertNotIn("türkçe", json.dumps(sorular, ensure_ascii=False))
        durum = {d["anahtar"]: d for d in S.tip_durumlari(self.user)}
        self.assertFalse(durum[S.TIP_ANLAM]["aktif"])
        self.assertFalse(durum[S.TIP_ESLESTIRME]["aktif"])

    def test_okuma_baloncugu_aciklamayla(self):
        self._kapat()
        veri = self.client.get(reverse("kelime_api"), {"q": "kelimec"}).json()
        self.assertEqual([a["tr"] for a in veri["anlamlar"]], ["english definition 2"])

    def test_misafirde_her_zaman_acik(self):
        self.assertIn("türkçe3", self.client.get("/sozluk/kelimed/").content.decode())


@override_settings(LANGUAGES=UC_DIL)
class BildirimDiliTests(TestCase):
    def test_hatirlatma_alicinin_dilinde(self):
        from bildirimler.management.commands.bildirim_gonder_hatirlatma import mesaj
        from bildirimler.models import GunlukHatirlatma
        from LearnVocab.diller import kullanici_dilinde
        user = User.objects.create_user(username="bil", password=SIFRE)
        UserSettings.objects.update_or_create(user=user, defaults={"arayuz_dili": "de"})
        with kullanici_dilinde(user):
            metin = mesaj(user, GunlukHatirlatma.GECE, {"hak": 0, "mevcut": 4})
        self.assertIn("Mitternacht", metin)
