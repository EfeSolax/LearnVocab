"""Ana Sayfa (rapor 3, 2.3) ve LOGIN_URL."""


from django.test import TestCase
from django.urls import reverse

from users.models import User
from words import arama
from words.models import Expression, UserWordLink
from words.testing import make_word

SIFRE = "Sifre1234"


class AnaSayfaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.b1 = make_word("tidy", level="B1", meaning="düzenli", forms=False)
        cls.c1 = make_word("ubiquitous", pos="adjective", level="C1", meaning="her yerde olan",
                           forms=False)
        Expression.objects.create(text="on the other hand", meaning_tr="öte yandan", cefr="B1",
                                  visibility="public")
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
        kelime = arama.gunun_kelimesi(self.user)
        self.assertIn(f'{reverse("sozluk_kelime", args=[kelime.slug])}" data-gunun-kelimesi', html)
        self.assertIn('/sozluk/on-the-other-hand/" data-gunun-ifadesi', html)

    def test_gunun_kelimesi_kullanicinin_seviyesinden(self):
        self.user.cefr = "C1"
        self.user.save()
        html = self._html(giris=True)
        self.assertIn("ubiquitous", html)

    def test_girissiz_karsilama(self):
        html = self._html()
        self.assertIn("Learn &amp; Pass'e başla", html)
        self.assertIn('data-misafir-basla', html)
        self.assertIn('action="/sozluk/"', html)
        self.assertIn('name="q"', html)
        self.assertIn("tidy", html)            # günün kelimesi B1
        self.assertNotIn("ubiquitous", html)
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
