"""Konular arayüzü (rapor 18.39): Keşfet kutucukları, konu sayfası, kartta konu etiketi."""

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from words import konular
from words.models import Category
from words.testing import make_word


class KonuTests(TestCase):
    def setUp(self):
        cache.clear()
        self.hayvan = Category.objects.create(name="Hayvanlar", slug="hayvanlar")
        self.spor = Category.objects.create(name="Spor", slug="spor")
        Category.objects.create(name="Boş konu", slug="bos-konu")
        self.kedi = make_word("cat", meaning="kedi", level="A1")
        self.aslan = make_word("lion", meaning="aslan", level="B1")
        self.yarasa = make_word("bat", meaning="yarasa", level="B1", extra_meanings=[("sopa", "a stick")])
        self.kedi.meanings.first().categories.add(self.hayvan)
        self.aslan.meanings.first().categories.add(self.hayvan)
        anlamlar = list(self.yarasa.meanings.order_by("sort_order"))
        anlamlar[0].categories.add(self.hayvan)
        anlamlar[-1].categories.add(self.spor)

    def test_kesfette_kutucuklar_sirayla_bos_konu_yok(self):
        html = self.client.get(reverse("sozluk")).content.decode()
        bolum = html[html.index("data-konular"):]
        self.assertLess(bolum.index('data-konu="hayvanlar"'), bolum.index('data-konu="spor"'))
        self.assertNotIn("bos-konu", bolum)
        self.assertIn("🐾", bolum)
        self.assertLess(html.index("data-konular"), html.index("data-gunun-kelimesi") if "data-gunun-kelimesi" in html else len(html))

    def test_daha_fazla_goster_yalnizca_fazlasi_varsa(self):
        html = self.client.get(reverse("sozluk")).content.decode()
        self.assertNotIn("data-konu-dugme", html)                    # 2 konu < ONDE_GORUNEN
        for i in range(konular.ONDE_GORUNEN):
            k = Category.objects.create(name=f"Konu {i}", slug=f"konu-{i}")
            self.kedi.meanings.first().categories.add(k)
        html = self.client.get(reverse("sozluk")).content.decode()
        self.assertIn("data-konu-dugme", html)
        self.assertEqual(html.count("data-konu-gizli"), 2)            # 10 konudan 8'i görünür

    def test_konu_sayfasi_zordan_kolaya_ve_yanlis_anlam_yok(self):
        html = self.client.get(reverse("sozluk_konu", args=["hayvanlar"])).content.decode()
        self.assertIn("Hayvanlar", html)
        self.assertLess(html.index("lion"), html.index(">cat<"))             # B1 önce, A1 sonra
        self.assertIn("bat", html)
        spor = self.client.get(reverse("sozluk_konu", args=["spor"])).content.decode()
        self.assertIn("bat", spor)
        self.assertNotIn("lion", spor)
        self.assertEqual(self.client.get(reverse("sozluk_konu", args=["yok"])).status_code, 404)

    def test_kapali_kart_ozeti_konunun_anlami(self):
        # bat: ilk anlam "yarasa" (Hayvanlar), ikinci "sopa" (Spor); Spor'da özet "sopa" olmalı
        spor = self.client.get(reverse("sozluk_konu", args=["spor"]))
        self.assertEqual([k.ozet for k, _ in spor.context["ogeler"]], ["sopa"])
        hayvan = self.client.get(reverse("sozluk_konu", args=["hayvanlar"]))
        self.assertIn("yarasa", [k.ozet for k, _ in hayvan.context["ogeler"]])

    def test_konu_sayfasi_seviye_suzgeci(self):
        adres = reverse("sozluk_konu", args=["hayvanlar"])
        cevap = self.client.get(adres)
        self.assertEqual([(s, n) for s, n, _ in cevap.context["seviye_sayilari"]],
                         [("A1", 1), ("A2", 0), ("B1", 2), ("B2", 0), ("C1", 0), ("C2", 0)])
        self.assertNotIn('href="?bolum=A2"', cevap.content.decode())   # boş seviye tıklanmaz
        self.assertIn('href="?bolum=B1"', cevap.content.decode())
        b1 = self.client.get(adres, {"bolum": "b1"})
        self.assertCountEqual([k.text for k, _ in b1.context["ogeler"]], ["bat", "lion"])
        self.assertEqual(b1.context["toplam"], 3)                   # başlıktaki sayı konunun tamamı
        # Arama süzgeci korur; olmayan seviye yok sayılır
        parca = self.client.get(adres, {"bolum": "B1", "ara": "lion", "parca": 1})
        self.assertEqual(parca["X-Sonuc-Sayisi"], "1")
        self.assertEqual(len(self.client.get(adres, {"bolum": "C2"}).context["ogeler"]), 3)

    def test_kelime_sayfasinda_anlam_basina_konu(self):
        html = self.client.get(reverse("sozluk_kelime", args=["bat"])).content.decode()
        self.assertEqual(html.count("data-konu-etiketleri"), 2)
        self.assertIn('href="/sozluk/konu/hayvanlar/"', html)
        self.assertIn('href="/sozluk/konu/spor/"', html)

    def test_ingilizce_ad(self):
        html = self.client.get("/en/sozluk/").content.decode()
        self.assertIn("Animals", html)
        self.assertIn("browse by topic", html)

    def test_konu_sayfasinda_ara(self):
        adres = reverse("sozluk_konu", args=["hayvanlar"])
        self.assertIn("data-liste-ara-girdi", self.client.get(adres).content.decode())
        r = self.client.get(adres, {"ara": "aslan", "parca": "1"})                 # Türkçe anlamda
        self.assertEqual(r["X-Sonuc-Sayisi"], "1")
        self.assertIn("lion", r.content.decode())
        self.assertNotIn(">cat<", r.content.decode())
        r = self.client.get(adres, {"ara": "ca", "parca": "1"})                    # baştan eşleşen önce
        self.assertEqual(r["X-Sonuc-Sayisi"], "1")
