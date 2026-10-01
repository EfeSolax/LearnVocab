"""Adresler ve SEO (rapor 18.15): LearnVocab/seo.py, seo_views.py, eski_adresler.py, words/dizine_alma.py."""

import json
import re
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from readings.models import ReadingText
from users.models import User
from words import dizine_alma
from words.adres import kelime_adresi, slug_yap
from words.models import Expression, ExpressionExample, HazirListe, Word
from words.testing import make_word

SITE = "https://www.learnvocab.com.tr"


def _html(cevap):
    return cevap.content.decode()


class SlugTests(TestCase):
    def test_slug_bicimi(self):
        self.assertEqual(slug_yap("give up"), "give-up")
        self.assertEqual(slug_yap("o'clock"), "o-clock")
        self.assertEqual(slug_yap("either … or"), "either-or")
        self.assertEqual(slug_yap("İDEA"), "idea")
        self.assertEqual(slug_yap("e.g."), "e-g")

    def test_kaydederken_dolar_ve_metinle_degisir(self):
        w = make_word("give up", pos="verb")
        self.assertEqual(w.slug, "give-up")
        w.text = "give in"
        w.save(update_fields=["text"])
        self.assertEqual(Word.objects.get(pk=w.pk).slug, "give-in")
        self.assertEqual(kelime_adresi("give in"), "/sozluk/give-in/")


@override_settings(SITE_ADRESI=SITE)
class KelimeSayfasiTests(TestCase):
    def setUp(self):
        self.isim = make_word("bank", meaning="banka", level="A1", siklik=5.0,
                              sentences=["I went to the bank."])
        self.fiil = make_word("bank", pos="verb", meaning="bankaya yatırmak", level="B2",
                              family=self.isim.family, siklik=5.0)

    def _sayfa(self, slug="bank"):
        return self.client.get(reverse("sozluk_kelime", args=[slug]))

    def test_butun_turler_tek_sayfada_ayni_arayuz(self):
        cevap = self._sayfa()
        self.assertEqual([k.id for k in cevap.context["kartlar"]], [self.isim.id, self.fiil.id])
        html = _html(cevap)
        self.assertIn('id="sozluk-ara"', html)          # üstte arama kutusu duruyor
        self.assertIn('value="bank"', html)
        self.assertIn("<title>bank ne demek? Türkçe anlamı ve cümle içinde kullanımı", html)

    def test_acilmamis_sayfa_noindex_acilinca_canonical(self):
        html = _html(self._sayfa())
        self.assertIn('<meta name="robots" content="noindex">', html)
        self.assertNotIn('rel="canonical"', html)

        Word.objects.filter(pk=self.isim.pk).update(dizinde=True)     # türlerden biri yeter
        cevap = self._sayfa()
        html = _html(cevap)
        self.assertNotIn('content="noindex"', html)
        self.assertNotIn("X-Robots-Tag", cevap.headers)
        self.assertIn(f'<link rel="canonical" href="{SITE}/sozluk/bank/">', html)
        self.assertIn('<meta name="description" content="bank ne demek? Türkçe anlamı: banka, '
                      'bankaya yatırmak.', html)

    def test_yapisal_veri_sayfada_gorunen_icerigi_anlatir(self):
        html = _html(self._sayfa())
        bloklar = [json.loads(b) for b in
                   re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]
        terim, kirinti = bloklar
        self.assertEqual((terim["@type"], terim["name"], terim["url"]),
                         ("DefinedTerm", "bank", f"{SITE}/sozluk/bank/"))
        self.assertEqual(terim["description"], "banka, bankaya yatırmak")
        self.assertEqual([a["name"] for a in kirinti["itemListElement"]],
                         ["Sözlük", "A1 kelimeleri", "bank"])
        self.assertEqual(kirinti["itemListElement"][1]["item"], f"{SITE}/sozluk/seviye/a1/")
        # Aynı adımlar sayfada da görünür.
        self.assertIn("data-ekmek-kirintisi", html)
        self.assertIn('href="/sozluk/seviye/a1/"', html)

    def test_arama_tam_eslesmede_kalici_adrese_301(self):
        cevap = self.client.get(reverse("sozluk"), {"q": "Bank"})
        self.assertRedirects(cevap, "/sozluk/bank/", status_code=301)

    def test_buyuk_harfli_adres_kucuge_301(self):
        self.assertRedirects(self.client.get("/sozluk/Bank/"), "/sozluk/bank/", status_code=301)

    def test_olmayan_kelime_404_ve_noindex(self):
        cevap = self._sayfa("bnak")
        self.assertEqual(cevap.status_code, 404)
        self.assertIn('content="noindex"', _html(cevap))
        self.assertEqual(cevap.headers["X-Robots-Tag"], "noindex")

    def test_ifade_sayfasi(self):
        e = Expression.objects.create(text="on the other hand", meaning_tr="öte yandan",
                                      visibility="public", cefr="B1", dizinde=True)
        ExpressionExample.objects.create(expression=e, text="On the other hand, it is cheap.")
        cevap = self.client.get("/sozluk/on-the-other-hand/")
        html = _html(cevap)
        self.assertIn("data-ifade-karti", html)
        self.assertIn(f'href="{SITE}/sozluk/on-the-other-hand/"', html)
        self.assertRedirects(self.client.get(reverse("sozluk"), {"q": "on the other hand"}),
                             "/sozluk/on-the-other-hand/", status_code=301)

    def test_cekimli_hal_ve_turkce_arama_yonlenmez_noindex(self):
        make_word("go", pos="verb", v2="went", v3="gone", meaning="gitmek", level="A1")
        for sorgu in ("went", "banka"):
            cevap = self.client.get(reverse("sozluk"), {"q": sorgu})
            self.assertEqual(cevap.status_code, 200)
            self.assertIn('content="noindex"', _html(cevap))

    def test_ornek_cumlede_cift_tiklama_aramasi(self):
        """Örnek cümledeki kelimeye çift tıklanınca o kelime aranır (rapor 4.3)."""
        html = _html(self._sayfa())
        self.assertRegex(html, r'<p lang="en" data-cift-tikla-ara[^>]*>I went to the bank\.</p>')
        self.assertIn("addEventListener('dblclick'", html)

    def test_cipler_ve_satirlar_kalici_adrese_baglanir(self):
        make_word("banker", meaning="bankacı", level="B1")
        html = _html(self._sayfa())
        self.assertIn('href="/sozluk/banker/"', html)
        self.assertNotIn("/sozluk/?q=", html)


@override_settings(SITE_ADRESI=SITE)
class NoindexVeCanonicalTests(TestCase):
    def test_beyaz_listedeki_sayfalar_acik(self):
        for ad in ("index", "sozluk", "seviye_testi", "readings", "about"):
            with self.subTest(ad=ad):
                cevap = self.client.get(reverse(ad))
                self.assertEqual(cevap.status_code, 200)
                self.assertNotIn("X-Robots-Tag", cevap.headers)
                self.assertNotIn('content="noindex"', _html(cevap))
                self.assertIn(f'<link rel="canonical" href="{SITE}{reverse(ad)}">', _html(cevap))

    def test_diger_her_sey_kapali(self):
        for ad in ("login", "register", "forgot_password", "learn_pass_page", "exercises_page",
                   "profile_texts", "seviye_sec", "sozluk_oneri"):
            with self.subTest(ad=ad):
                cevap = self.client.get(reverse(ad))
                self.assertEqual(cevap.headers["X-Robots-Tag"], "noindex")
                if "text/html" in cevap.headers.get("Content-Type", "") and cevap.status_code == 200:
                    self.assertIn('content="noindex"', _html(cevap))
                    self.assertNotIn('rel="canonical"', _html(cevap))

    def test_canonical_istekten_degil_asil_adresten(self):
        html = _html(self.client.get(reverse("sozluk"), {"utm_source": "x"},
                                     HTTP_HOST="learnvocab.com.tr"))
        self.assertIn(f'<link rel="canonical" href="{SITE}/sozluk/">', html)

    def test_listem_sekmesi_noindex(self):
        User.objects.create_user(username="seo", password="Sifre1234")
        self.client.login(username="seo", password="Sifre1234")
        html = _html(self.client.get(reverse("sozluk"), {"sekme": "listem"}))
        self.assertIn('content="noindex"', html)

    def test_tek_dilde_hreflang_yok(self):
        self.assertNotIn("hreflang", _html(self.client.get(reverse("sozluk"))))

    @override_settings(LANGUAGES=[("tr", "Türkçe"), ("en", "English")])
    def test_ikinci_dil_acilinca_onekli_adres_ve_hreflang(self):
        html = _html(self.client.get("/sozluk/"))
        self.assertIn(f'hreflang="tr" href="{SITE}/sozluk/"', html)
        self.assertIn(f'hreflang="en" href="{SITE}/en/sozluk/"', html)
        self.assertIn(f'hreflang="x-default" href="{SITE}/sozluk/"', html)
        cevap = self.client.get("/en/sozluk/")
        self.assertEqual(cevap.status_code, 200)
        self.assertIn('<html lang="en">', _html(cevap))
        self.assertIn(f'<link rel="canonical" href="{SITE}/en/sozluk/">', _html(cevap))

    @override_settings(LANGUAGES=[("tr", "Türkçe"), ("en", "English")])
    def test_yazilar_ingilizcede_writings(self):
        """Efe, 30 Eylül: adres Türkçe /yazilar/, İngilizce /en/writings/; menüde Yazılar / Writings."""
        from django.utils import translation
        self.assertEqual(reverse("profile_texts"), "/yazilar/")
        with translation.override("en"):
            self.assertEqual(reverse("profile_texts"), "/en/writings/")
            self.assertEqual(reverse("diyalog_page"), "/en/writings/diyalog/")
        self.assertIn(">Yazılar<", _html(self.client.get("/sozluk/")))
        ingilizce = _html(self.client.get("/en/sozluk/"))
        self.assertIn(">Writings<", ingilizce)
        self.assertIn('href="/en/writings/"', ingilizce)
        self.assertEqual(self.client.get("/en/writings/").status_code, 200)
        self.assertEqual(self.client.get("/en/yazilar/").status_code, 404)
        self.assertEqual(self.client.get("/writings/")["Location"], "/en/writings/")

    def test_yayinda_olmayan_dil_oneki_404(self):
        self.assertEqual(self.client.get("/en/sozluk/").status_code, 404)


@override_settings(SITE_ADRESI=SITE)
class GozatTests(TestCase):
    def setUp(self):
        self.apple = make_word("apple", meaning="elma", level="A1", siklik=4.5)
        make_word("avid", meaning="hevesli", level="C1", siklik=3.0)
        make_word("abseil", meaning="iple inmek", level="A1", siklik=1.5)   # çok seyrek

    def test_seviye_sayfasi_satirlarda_anlam_var(self):
        cevap = self.client.get("/sozluk/seviye/a1/")
        html = _html(cevap)
        self.assertEqual([s["metin"] for s in cevap.context["satirlar"]], ["apple"])
        self.assertIn("elma", html)
        self.assertIn('href="/sozluk/apple/"', html)
        self.assertIn("<title>A1 seviyesi İngilizce kelimeler", html)
        self.assertIn(f'<link rel="canonical" href="{SITE}/sozluk/seviye/a1/">', html)
        self.assertNotIn("abseil", html)

    def test_harf_sayfasi(self):
        cevap = self.client.get("/sozluk/harf/a/")
        self.assertEqual([s["metin"] for s in cevap.context["satirlar"]], ["apple", "avid"])
        self.assertEqual(self.client.get("/sozluk/harf/1/").status_code, 404)
        self.assertEqual(self.client.get("/sozluk/seviye/x9/").status_code, 404)
        self.assertRedirects(self.client.get("/sozluk/seviye/A1/"), "/sozluk/seviye/a1/", status_code=301)

    def test_sayfalama_canonical_sayfa_numarasini_tasir(self):
        for i in range(105):
            make_word(f"ab{i:03d}", meaning="x", level="A1", siklik=3.0, forms=False)
        html = _html(self.client.get("/sozluk/harf/a/", {"sayfa": 2}))
        self.assertIn(f'<link rel="canonical" href="{SITE}/sozluk/harf/a/?sayfa=2">', html)
        self.assertIn("(sayfa 2)", html)
        self.assertIn('rel="prev" href="/sozluk/harf/a/"', html)

    def test_kesfette_goz_atma_baglantilari(self):
        html = _html(self.client.get(reverse("sozluk")))
        self.assertIn("data-goz-at", html)
        self.assertIn('href="/sozluk/seviye/a1/"', html)
        self.assertIn('href="/sozluk/harf/a/"', html)


@override_settings(SITE_ADRESI=SITE)
class RobotsVeSitemapTests(TestCase):
    def test_robots(self):
        metin = _html(self.client.get("/robots.txt"))
        self.assertIn("Disallow: /api/", metin)
        self.assertIn("Disallow: /admin/", metin)
        self.assertIn(f"Sitemap: {SITE}/sitemap.xml", metin)
        self.assertNotIn("Disallow: /sozluk", metin)

    def test_sitemap_yalnizca_acik_sayfalar(self):
        make_word("open", meaning="açık", level="A1", siklik=5.0, dizinde=True)
        make_word("closed", meaning="kapalı", level="A1", siklik=5.0)
        HazirListe.objects.create(ad="ODTÜ 101", slug="odtu-101", yayinda=True)
        HazirListe.objects.create(ad="Taslak", slug="taslak", yayinda=False)
        ReadingText.objects.create(number=1, topic="hukuk", title="The Two Brothers", body="Once.")
        cevap = self.client.get("/sitemap.xml")
        self.assertEqual(cevap.headers["Content-Type"], "application/xml; charset=utf-8")
        xml = _html(cevap)
        for yol in ("/", "/sozluk/", "/seviye-testi/", "/okumalar/", "/sozluk/open/",
                    "/sozluk/seviye/a1/", "/sozluk/harf/o/", "/listeler/odtu-101/",
                    "/okumalar/the-two-brothers/"):
            self.assertIn(f"<loc>{SITE}{yol}</loc>", xml)
        for yol in ("/sozluk/closed/", "/listeler/taslak/", "/giris/", "/calismalar/"):
            self.assertNotIn(f"<loc>{SITE}{yol}</loc>", xml)


class DizineAcTests(TestCase):
    def setUp(self):
        self.kolay = make_word("house", meaning="ev", level="A1", siklik=5.5, cefr_kaynak="oxford")
        self.zor = make_word("heath", meaning="fundalık", level="C1", siklik=3.0)
        self.seyrek = make_word("pillared", meaning="sütunlu", level="B1", siklik=1.8,
                                cefr_kaynak="oxford")
        self.orneksiz = make_word("bare", meaning="çıplak", level="A1", siklik=4.0,
                                  cefr_kaynak="oxford", sentences=[])

    def _komut(self, *args):
        cikti = StringIO()
        call_command("dizine_ac", *args, stdout=cikti)
        return cikti.getvalue()

    def _acik(self):
        return set(Word.objects.filter(dizinde=True).values_list("text", flat=True))

    def test_uygunluk_seyrek_ve_orneksiz_giremez(self):
        self.assertEqual(set(dizine_alma.uygun_kelimeler().values_list("text", flat=True)),
                         {"house", "heath"})

    def test_parti_secimi_ve_dry_run(self):
        self._komut("--seviye", "A1", "A2", "B1", "--kaynak", "oxford", "--dry-run")
        self.assertEqual(self._acik(), set())
        cikti = self._komut("--seviye", "A1", "A2", "B1", "--kaynak", "oxford")
        self.assertEqual(self._acik(), {"house"})
        self.assertIn("1 sayfa açıldı", cikti)
        self._komut("--kapat-hepsi")
        self.assertEqual(self._acik(), set())

    def test_en_cok_sik_olandan_baslar(self):
        make_word("home", meaning="ev", level="A1", siklik=6.0)
        self._komut("--seviye", "A1", "--en-cok", "1")
        self.assertEqual(self._acik(), {"home"})


class EskiAdresTests(TestCase):
    def test_eski_sayfalar_yenisine_301(self):
        ReadingText.objects.create(number=7, topic="hukuk", title="Siblings", body="Text.")
        HazirListe.objects.create(ad="ODTÜ 101", slug="odtu-101", yayinda=True)
        beklenen = {
            "/words/all-words/": "/sozluk/",
            "/words/word-detail/12/": "/sozluk/",
            "/sozluk/liste/odtu-101/": "/listeler/odtu-101/",
            "/exercises/learn/": "/calismalar/",
            "/exercises/learn/karma/": "/calismalar/learn-pass/karma/",
            "/egzersizler/": "/calismalar/egzersizler/",
            "/readings/": "/okumalar/",
            "/readings/kutuphane/7/": "/okumalar/siblings/",
            "/texts/": "/yazilar/",
            "/yazma/": "/yazilar/",
            "/writings/": "/yazilar/",
            "/seviye/": "/seviye-testi/",
            "/users/login/": "/giris/",
            "/users/register/": "/kayit/",
            "/profile/profile/": "/profil/",
            "/profile/profile/words/": "/sozluk/?sekme=listem",
            "/about/": "/hakkinda/",
        }
        for eski, yeni in beklenen.items():
            with self.subTest(eski=eski):
                cevap = self.client.get(eski)
                self.assertEqual(cevap.status_code, 301)
                self.assertEqual(cevap["Location"], yeni)

    def test_adres_semasi(self):
        beklenen = {
            "index": "/", "sozluk": "/sozluk/", "learn_pass_page": "/calismalar/",
            "exercises_page": "/calismalar/egzersizler/", "readings": "/okumalar/",
            "profile_texts": "/yazilar/", "diyalog_page": "/yazilar/diyalog/",
            "seviye_testi": "/seviye-testi/", "login": "/giris/", "register": "/kayit/",
            "user_profile": "/profil/", "sozluk_oneri": "/api/sozluk/oneri/",
            "learn_pass_verdict": "/api/learn-pass/verdict/", "seri_durum": "/api/seri/durum/",
            "service_worker": "/sw.js", "pwa_manifest": "/manifest.webmanifest",
        }
        for ad, yol in beklenen.items():
            self.assertEqual(reverse(ad), yol)
