"""
İskelet bileşenleri (uygulama planı adım 3): giriş gerektiren düğmeler ve
"Geri al" bildirimi. Menü testleri words/tests.py, kelime kartı testleri
words/test_kart.py içinde.
"""

from django.test import TestCase
from django.urls import reverse

from LearnVocab.authgate import GIRIS_NEDENLERI, giris_adresi
from users.models import User


class GirisGerekliTests(TestCase):
    """Rapor 2.3 / 12.6: düğmeler gizlenmez, basılınca açıklamayla girişe yönlendirir."""

    def setUp(self):
        self.user = User.objects.create_user(username="girisci", password="Sifre1234")

    def test_giris_adresi(self):
        self.assertEqual(giris_adresi(), reverse("login"))
        self.assertEqual(giris_adresi("/sozluk/?q=aim", "liste"),
                         f"{reverse('login')}?next=%2Fsozluk%2F%3Fq%3Daim&neden=liste")
        # Bilinmeyen neden eklenmez
        self.assertNotIn("neden", giris_adresi("/x/", "uydurma"))

    def test_ortak_js_her_sayfada(self):
        html = self.client.get(reverse("index")).content.decode()
        self.assertIn("window.girisGerekli", html)
        self.assertIn("closest('[data-giris-gerekli]')", html)

    def test_giris_sayfasi_nedeni_gosterir(self):
        html = self.client.get(reverse("login"), {"next": "/sozluk/", "neden": "liste"}).content.decode()
        self.assertIn("Önce giriş yapmalısın.", html)
        self.assertIn(str(GIRIS_NEDENLERI["liste"]), html)
        self.assertIn('name="next" value="/sozluk/"', html)

    def test_uydurma_neden_sayfaya_basilmaz(self):
        html = self.client.get(reverse("login"), {"neden": "Şifreni bize e-postala"}).content.decode()
        self.assertNotIn("Şifreni bize", html)
        self.assertNotIn("data-giris-notu", html)

    def test_girisle_geri_donulur(self):
        cevap = self.client.post(reverse("login"), {"username": "girisci", "password": "Sifre1234",
                                                    "next": "/sozluk/?q=aim"})
        self.assertRedirects(cevap, "/sozluk/?q=aim", fetch_redirect_response=False)

    def test_baska_siteye_yonlendirilmez(self):
        cevap = self.client.post(reverse("login"), {"username": "girisci", "password": "Sifre1234",
                                                    "next": "https://kotu.example.com/"})
        self.assertRedirects(cevap, reverse("index"), fetch_redirect_response=False)

    def test_hatali_giriste_next_kaybolmaz(self):
        cevap = self.client.post(reverse("login"), {"username": "girisci", "password": "yanlis",
                                                    "next": "/sozluk/", "neden": "liste"})
        self.assertEqual(cevap.status_code, 302)
        self.assertIn("next=%2Fsozluk%2F", cevap["Location"])
        self.assertIn("neden=liste", cevap["Location"])

    def test_egzersizler_ve_yazma_girissizken_yonlendirir(self):
        # Rapor 18.3: misafirde Egzersizler sekmesi yok, yerine tek davet; Yazılar misafire açık.
        html = self.client.get(reverse("learn_pass_page")).content.decode()
        self.assertIn("data-egzersiz-daveti", html)
        self.assertNotIn('data-giris-gerekli="yazma"', html)
        self.client.login(username="girisci", password="Sifre1234")
        html = self.client.get(reverse("learn_pass_page")).content.decode()
        self.assertNotIn('data-giris-gerekli="', html)

    def test_ayarlar_disli_ve_giris_dugmesi(self):
        html = self.client.get(reverse("sozluk")).content.decode()
        self.assertIn(f"{reverse('login')}?next=%2Fsozluk%2F", html)
        # giriş sayfasının kendisinde ?next= yok
        html = self.client.get(reverse("login")).content.decode()
        basla = html.index('<header id="navbar"')
        self.assertNotIn("?next=", html[basla:html.index("</header>", basla)])


class GeriAlBildirimiTests(TestCase):
    """Rapor 12.7: onay penceresi yerine birkaç saniyelik "Geri al" bildirimi."""

    def test_bilesen_her_sayfada_ve_alt_menunun_ustunde(self):
        html = self.client.get(reverse("index")).content.decode()
        self.assertIn('id="geri-al-kutusu"', html)
        self.assertIn("window.geriAl", html)
        self.assertIn("goster: goster", html)
        # Mobilde alt sekme çubuğunun (h ≈ 4rem) üstünde, masaüstünde altta
        self.assertIn("bottom-[calc(4.75rem+env(safe-area-inset-bottom))] lg:bottom-6", html)

    def test_listemden_cikar_geri_al_kullanir(self):
        html = self.client.get(reverse("index")).content.decode()
        self.assertIn("window.geriAl.goster(", html)
        self.assertIn("listenden çıkarıldı", html)
        self.assertIn('name="csrf-token"', html)
