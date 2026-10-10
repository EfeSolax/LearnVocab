"""Hazır listede arama (Efe'nin isteği, 10 Ekim): yalnızca o listenin kelimeleri, yazdıkça."""
from django.test import TestCase
from django.urls import reverse

from words.models import HazirListe, HazirListeKelimesi
from words.testing import make_word


class ListeAramaTests(TestCase):
    def setUp(self):
        self.liste = HazirListe.objects.create(ad="Bilkent Intermediate", slug="bilkent-intermediate")
        kelimeler = [make_word("cabin", level="B1", meaning="kulübe"),
                     make_word("abandon", level="B2", meaning="terk etmek"),
                     make_word("absorb", level="B2", meaning="emmek")]
        for i, w in enumerate(kelimeler, start=1):
            HazirListeKelimesi.objects.create(liste=self.liste, word=w, sira=i)
        make_word("abroad", level="A2", meaning="yurt dışı")      # listede yok
        self.adres = reverse("hazir_liste", args=["bilkent-intermediate"])

    def _metinler(self, **parametre):
        cevap = self.client.get(self.adres, {"parca": "1", **parametre})
        html = cevap.content.decode()
        sirali = sorted((html.find(f">{k}<"), k) for k in ("cabin", "abandon", "absorb", "abroad") if f">{k}<" in html)
        return cevap, [k for _, k in sirali]

    def test_sayfada_arama_kutusu(self):
        html = self.client.get(self.adres).content.decode()
        self.assertIn("data-liste-ara-girdi", html)
        self.assertIn("3 kelime", html)

    def test_yalnizca_listedekiler_ve_bastan_eslesen_once(self):
        cevap, bulunan = self._metinler(ara="ab")
        self.assertEqual(bulunan, ["abandon", "absorb", "cabin"])     # abroad listede değil
        self.assertEqual(cevap["X-Sonuc-Sayisi"], "3")

    def test_turkce_anlamda_arar(self):
        _, bulunan = self._metinler(ara="kulübe")
        self.assertEqual(bulunan, ["cabin"])

    def test_eslesme_yoksa_mesaj(self):
        cevap, bulunan = self._metinler(ara="zzz")
        self.assertEqual(bulunan, [])
        self.assertIn("eşleşen kelime yok", cevap.content.decode())

    def test_bos_arama_hepsini_liste_sirasiyla_verir(self):
        _, bulunan = self._metinler()
        self.assertEqual(bulunan, ["cabin", "abandon", "absorb"])


class ListeBolumuTests(TestCase):
    """ODTÜ listeleri hafta hafta (Efe'nin kararı, 10 Ekim): '## 1' satırı bölüm başlatır."""

    def setUp(self):
        import tempfile
        from django.core.management import call_command
        for metin, anlam in (("alter", "değiştirmek"), ("attach", "eklemek"), ("remain", "kalmak"), ("boast", "övünmek")):
            make_word(metin, level="B1", meaning=anlam)
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("# deneme\n## 1\nalter\nattach\n## 2\nremain\nalter\n## 3\nboast\n")
        call_command("hazir_liste_yukle", f.name, ad="ODTÜ 401 Span 1", slug="odtu-401-span-1", stdout=open("/dev/null", "w"))
        self.adres = reverse("hazir_liste", args=["odtu-401-span-1"])

    def test_bolumler_kaydedilir_tekrar_ilk_haftada_kalir(self):
        liste = HazirListe.objects.get(slug="odtu-401-span-1")
        self.assertEqual(list(liste.uyelikler.order_by("sira").values_list("word__text", "bolum")),
                         [("alter", "1"), ("attach", "1"), ("remain", "2"), ("boast", "3")])

    def test_hafta_basliklari_bir_kez_ve_hafta_dugmeleri(self):
        html = self.client.get(self.adres).content.decode()
        for n in (1, 2, 3):
            self.assertEqual(html.count(f">{n}. hafta</h2>"), 1)
        self.assertIn('href="?bolum=2"', html)
        self.assertIn('aria-current="page">Hepsi', html)          # hafta seçilmeden "Hepsi" seçili

    def test_hafta_secilince_yalnizca_o_hafta(self):
        html = self.client.get(self.adres, {"bolum": "2"}).content.decode()
        self.assertIn(">remain<", html)
        self.assertNotIn(">alter<", html)

    def test_sonraki_parcada_ayni_baslik_tekrarlanmaz(self):
        from unittest.mock import patch
        with patch("words.sozluk_views.HAZIR_LISTE_SAYFA_BOYU", 1):
            ikinci = self.client.get(self.adres, {"sayfa": 2, "parca": 1}).content.decode()
            ucuncu = self.client.get(self.adres, {"sayfa": 3, "parca": 1}).content.decode()
        self.assertNotIn("1. hafta", ikinci)            # attach: hâlâ 1. hafta
        self.assertIn(">2. hafta</h2>", ucuncu)         # remain: yeni hafta


class KaynakAilesiTests(TestCase):
    """More to Read II: kartta sözlüğün ailesi değil, kaynağın ailesi (Efe'nin kararı, 10 Ekim)."""

    def setUp(self):
        import tempfile
        from django.core.management import call_command
        self.abandon = make_word("abandon", level="B2", meaning="terk etmek")
        make_word("abandonment", level="C1", meaning="terk")
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("## A\nabandon | abandoned, abandonment\n")
        call_command("hazir_liste_yukle", f.name, ad="More to Read II · Academic Word List",
                     slug="more-to-read-ii-awl", stdout=open("/dev/null", "w"))

    def test_aile_kaydedilir_ve_kartta_gorunur(self):
        uye = HazirListeKelimesi.objects.get(liste__slug="more-to-read-ii-awl")
        self.assertEqual(uye.aile, ["abandoned", "abandonment"])
        html = self.client.get(reverse("hazir_liste", args=["more-to-read-ii-awl"])).content.decode()
        self.assertIn(">abandoned</span>", html)                     # sözlükte yok: düz yazı
        self.assertRegex(html, r'data-kart-ac="\d+"\s+class="[^"]*">abandonment</a>')   # sözlükte var: kartı
