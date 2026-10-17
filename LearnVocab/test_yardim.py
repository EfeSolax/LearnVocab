"""Yardım ve hakkında sayfası (rapor 18.33; LearnVocab/yardim.py)."""

from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from PIL import Image

from egzersizler.sorular import TIPLER
from LearnVocab import yardim

STATIK = Path(settings.BASE_DIR) / "static"


class YardimSayfasiTests(TestCase):
    def _html(self):
        cevap = self.client.get(reverse("about"))
        self.assertEqual(cevap.status_code, 200)
        return cevap.content.decode()

    def test_misafir_de_gorur_butun_rehberler_ve_hakkinda_var(self):
        html = self._html()
        for r in yardim.REHBERLER:
            self.assertIn(f'data-rehber="{r["kimlik"]}"', html)
        self.assertIn('id="hakkinda"', html)
        self.assertIn("mailto:", html)
        self.assertEqual(html.count('data-soru-tipleri'), 1)
        for t in TIPLER.values():
            self.assertIn(str(t["ad"]), html)

    def test_her_goruntu_iki_temada_da_var(self):
        for dil in yardim.GORUNTU_DILLERI:
            for r in yardim._rehberler(dil):
                for g in r["goruntuler"]:
                    for tema in ("acik", "koyu"):
                        self.assertTrue((STATIK / g[tema]).exists(), g[tema])

    def test_goruntu_boyu_tanimla_ayni(self):
        # Yükseklik sayfa yüklenirken yer ayırmak için yazılır; görüntü yeniden çekilince tutmalı.
        for dil in yardim.GORUNTU_DILLERI:
            for r in yardim.REHBERLER:
                for ad in r["goruntuler"]:
                    with Image.open(STATIK / f"img/yardim/{dil}/{ad}-acik.webp") as im:
                        self.assertEqual(im.size, (500, yardim.ISARETLER[dil][ad]["yukseklik"]), f"{dil}/{ad}")

    def test_isaretler_goruntunun_icinde(self):
        for dil in yardim.GORUNTU_DILLERI:
            for r in yardim.REHBERLER:
                for ad in r["goruntuler"]:
                    for x, y in yardim.ISARETLER[dil][ad]["isaretler"]:
                        self.assertTrue(0 <= x <= 100 and 0 <= y <= 100, f"{dil}/{ad}: {x}, {y}")

    def test_goruntuler_bir_solda_bir_sagda(self):
        yanlar = [g["sag"] for r in yardim._rehberler("tr") for g in r["goruntuler"]]
        self.assertEqual(yanlar, [i % 2 == 1 for i in range(len(yanlar))])

    @override_settings(LANGUAGES=[("tr", "Türkçe"), ("en", "English"), ("de", "Deutsch")])
    def test_her_dil_kendi_goruntusunu_gosterir(self):
        for dil in ("en", "de"):
            html = self.client.get(f"/{dil}/hakkinda/").content.decode()
            self.assertIn(f"img/yardim/{dil}/arama-acik.webp", html)
            self.assertNotIn("img/yardim/tr/", html)

    def test_her_adimin_goruntude_bir_isareti_var(self):
        for r in yardim._rehberler("tr"):
            self.assertEqual(r["kalan_adimlar"], [], r["kimlik"])

    def test_isaret_konumu_noktali_yazilir(self):
        # Türkçe yerelleştirme ondalığı virgülle yazar; CSS virgülü okuyamaz.
        html = self._html()
        self.assertIn("left: 2.9%", html)
        self.assertNotIn("left: 2,9%", html)

    def test_eski_adres_ve_ana_sayfa_baglantisi(self):
        self.assertEqual(reverse("about"), "/hakkinda/")
        self.assertIn(f'href="{reverse("about")}"', self.client.get(reverse("index")).content.decode())
