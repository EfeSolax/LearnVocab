"""Ana Sayfa (rapor 3, 2.3) ve LOGIN_URL."""


from django.test import TestCase
from django.urls import reverse

from users.models import User
from words import gunun
from words.models import Expression, UserWordLink
from words.testing import make_word

SIFRE = "Sifre1234"


class AnaSayfaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Günün kelimesi olabilmek için (rapor 18.8): 2 örnek, bir eş dizim, sıklık.
        zengin = dict(sentences=["It is tidy.", "Keep it tidy."], siklik=4.0,
                      collocations=[("keep tidy", "verb_adj")], forms=False)
        cls.b1 = make_word("tidy", level="B1", meaning="düzenli", **zengin)
        cls.c1 = make_word("ubiquitous", pos="adjective", level="C1", meaning="her yerde olan", **zengin)
        Expression.objects.create(text="on the other hand", meaning_tr="öte yandan", cefr="B1",
                                  visibility="public", bilinirlik="az")
        cls.user = User.objects.create_user(username="ana", password=SIFRE, first_name="Efe")

    def _html(self, giris=False):
        if giris:
            self.client.login(username="ana", password=SIFRE)
        cevap = self.client.get(reverse("index"))
        self.assertEqual(cevap.status_code, 200)
        return cevap.content.decode()

    def test_girisli_icerik(self):
        UserWordLink.objects.create(user=self.user, word=self.b1)
        html = self._html(giris=True)
        self.assertIn("Merhaba, Efe", html)
        self.assertIn("Bugünün çalışmasına başla", html)
        self.assertIn(f'href="{reverse("learn_pass_page")}" data-bugunun-calismasi', html)
        self.assertIn("data-seri-kutusu", html)          # rapor 18.9
        self.assertIn("günlük seri", html)
        self.assertIn("Listemdeki kelime", html)
        liste = html[html.index("data-liste-sayisi"):]
        self.assertIn(">1<", liste[:liste.index("</a>")])
        self.assertIn(reverse("about"), html)   # yardım bağlantısı

    def test_gunun_kelimesi_ve_ifadesi_sozluge_gider(self):
        html = self._html(giris=True)
        kelime = gunun.gunun_kelimesi(self.user)
        self.assertIn(f'data-gunun-kelimesi="{kelime.id}"', html)
        self.assertIn(f'href="{reverse("sozluk_kelime", args=[kelime.slug])}"', html)
        self.assertIn('href="/sozluk/on-the-other-hand/"', html)
        self.assertIn("data-gunun-ifadesi", html)

    def test_gunun_kelimesi_kullanicinin_seviyesinden(self):
        self.user.cefr = "C1"
        self.user.save()
        html = self._html(giris=True)
        self.assertIn("ubiquitous", html)

    def test_girissiz_karsilama(self):
        html = self._html()
        self.assertIn("Hesap açmadan dene", html)     # defter teması (rapor 18.12)
        self.assertIn("data-defter-tablosu", html)
        self.assertIn('data-misafir-basla', html)
        self.assertIn('action="/sozluk/"', html)
        self.assertIn('name="q"', html)
        gunun = html[html.index("data-gunun-kelimesi"):]
        gunun = gunun[:gunun.index("</section>")]
        self.assertIn("tidy", gunun)           # günün kelimesi B1
        self.assertNotIn("ubiquitous", gunun)  # (defter tablosu komşu seviyeye kayabilir)
        self.assertIn(reverse("register"), html)
        self.assertNotIn("Bugünün çalışmasına başla", html)
        self.assertNotIn("data-seviye-daveti", html)

    def test_olmayan_ozelliklerden_soz_edilmez(self):
        for giris in (False, True):
            with self.subTest(giris=giris):
                html = self._html(giris=giris).lower()
                sayfa = html[html.index("data-ana-sayfa"):]
                for yasak in ("öğrenilen", "öğrendiğin", "topluluk", "herkese açık", "tamamen gizli",
                              "görünürlüğ", "puanlasın", "401", "501"):
                    self.assertNotIn(yasak, sayfa)


class LoginUrlTests(TestCase):
    def test_login_required_bizim_giris_sayfamiza_gider(self):
        cevap = self.client.get(reverse("seviye_sonuc"))
        self.assertEqual(cevap.status_code, 302)
        self.assertTrue(cevap["Location"].startswith(f"{reverse('login')}?next="))
        self.assertNotIn("/accounts/", cevap["Location"])


class DefterTablosuTests(TestCase):
    """Misafir ana sayfasındaki katlanan defter tablosu (rapor 18.12)."""

    @classmethod
    def setUpTestData(cls):
        zengin = dict(sentences=["One.", "Two."], siklik=4.0, collocations=[("a b", "verb_adj")], forms=False)
        for i, ad in enumerate(("alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf")):
            make_word(ad, level="B1" if i < 3 else "B2", meaning=f"anlam {i}", **zengin)

    def test_gunluk_bes_kelime_gunun_kelimesi_haric_ve_sabit(self):
        from django.core.cache import cache
        cache.clear()
        ilk = gunun.defter_kelimeleri()
        self.assertEqual(len(ilk), 5)
        self.assertNotIn(gunun.misafir_kelimesi(), ilk)
        self.assertEqual(gunun.defter_kelimeleri(), ilk)   # o gün herkese aynı

    def test_tablo_kelime_sayfasina_baglanir_ve_hicbir_sey_kaydetmez(self):
        html = self.client.get(reverse("index")).content.decode()
        tablo = html[html.index("data-defter-tablosu"):]
        tablo = tablo[:tablo.index("</section>")]
        self.assertEqual(tablo.count("data-satir"), 5)
        self.assertIn('href="/sozluk/', tablo)
        self.assertNotIn("<form", tablo)


class GirisliDefterTests(TestCase):
    """Girişli kullanıcı da zengin defter sayfasını kendi verisiyle görür (rapor 18.12)."""

    @classmethod
    def setUpTestData(cls):
        zengin = dict(sentences=["One.", "Two."], siklik=4.0, collocations=[("a b", "verb_adj")], forms=False)
        cls.kelime = make_word("sturdy", level="B1", meaning="sağlam", **zengin)
        cls.user = User.objects.create_user(username="defter", password=SIFRE, first_name="Efe")

    def _html(self):
        self.client.login(username="defter", password=SIFRE)
        return self.client.get(reverse("index")).content.decode()

    def test_tablo_listedeki_tekrar_kelimesinden_ve_kaydedilir(self):
        UserWordLink.objects.create(user=self.user, word=self.kelime)
        html = self._html()
        tablo = html[html.index("data-defter-tablosu"):]
        tablo = tablo[:tablo.index("</section>")]
        self.assertIn("sturdy", tablo)
        self.assertIn(f'data-kayit-url="{reverse("learn_pass_verdict")}"', tablo)
        self.assertIn('data-kaynak="mine"', tablo)
        self.assertIn("Bugünün tekrarı", html)

    def test_gercek_takvim_okumalar_ve_seviye_isareti(self):
        html = self._html()
        self.assertIn("son beş haftan", html)
        self.assertEqual(html.count('class="lv-bugun"'), 1)
        self.assertIn("sen buradasın", html)
        self.assertIn("Bugün başka ne yapsan?", html)
        self.assertNotIn("Aklına takılanlar", html)        # sık sorulanlar yalnızca misafirde
