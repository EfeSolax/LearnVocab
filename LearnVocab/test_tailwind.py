"""
Tailwind derlemesi (rapor 18.17): sayfalarda kullanılan her Tailwind sınıfı
static/css/site.css içinde üretilmiş olmalı. Şablona yeni bir sınıf eklenip
derleme unutulursa bu test düşer. Derleme komutu tailwind.config.js başında.
"""

import re
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from readings.models import ReadingText
from users.models import User
from words.models import UserWordLink
from words.testing import make_word

SIFRE = "Sifre1234"
CSS = (Path(settings.BASE_DIR) / "static" / "css" / "site.css")
DEFTER = (Path(settings.BASE_DIR) / "static" / "css" / "defter.css")

# CSS üretmeyen, yalnızca işaret ya da Alpine için kullanılan sınıflar.
ISARETLER = {"group", "peer", "telaffuz-dugmesi", "dark", "lv-tablo"}


def _kacis(sinif):
    """Tailwind'in seçicide kullandığı biçim: harf/rakam/-/_ dışındaki her karakterin önüne \\."""
    return re.sub(r"([^A-Za-z0-9_-])", r"\\\1", sinif).replace("\\,", "\\2c ")


def _siniflar(html):
    for deger in re.findall(r'(?<![:\w-])class="([^"]*)"', html):
        if "{" in deger:          # şablon ifadesi (render edilmemiş) ya da Alpine nesnesi
            continue
        # JS içindeki '…class="' + c + '"…' gibi birleştirmelerden gelen parçalar sınıf değildir.
        yield from (t for t in deger.split() if re.match(r"^[!-]?[A-Za-z\[]", t))


class TailwindDerlemesiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        zengin = dict(sentences=["One bank.", "Two banks."], siklik=4.0, collocations=[("a b", "verb_adj")])
        cls.bank = make_word("bank", level="A1", meaning="banka", **zengin)
        for i, ad in enumerate(("alpha", "bravo", "charlie", "delta", "echo")):
            make_word(ad, level="B1" if i < 2 else "B2", meaning=f"anlam {i}", **zengin)
        cls.user = User.objects.create_user(username="tw", password=SIFRE, first_name="Efe")
        UserWordLink.objects.create(user=cls.user, word=cls.bank)
        cls.metin = ReadingText.objects.create(number=1, topic="psikoloji", title="Why", body="One. Two.",
                                               word_count=2, cefr="B1", slug="why")

    def _eksikler(self, adresler):
        css = CSS.read_text()
        ozel = set(re.findall(r"\.(-?[A-Za-z_][\w-]*)", DEFTER.read_text()))
        eksik = set()
        for adres in adresler:
            cevap = self.client.get(adres, follow=True)
            html = cevap.content.decode()
            sayfa_ozel = set()
            for stil in re.findall(r"<style>(.*?)</style>", html, re.S):
                sayfa_ozel |= set(re.findall(r"\.(-?[A-Za-z_][\w-]*)", stil))
            for s in set(_siniflar(html)):
                cekirdek = s.split(":")[-1].lstrip("!")
                if s in ISARETLER or cekirdek in ozel or cekirdek in sayfa_ozel or s in ozel:
                    continue
                if "." + _kacis(s) not in css:
                    eksik.add(f"{adres}: {s}")
        return sorted(eksik)

    def test_misafir_sayfalari(self):
        adresler = [reverse("index"), reverse("sozluk"), "/sozluk/bank/", reverse("login"), reverse("register"),
                    reverse("readings"), "/okumalar/why/", reverse("learn_pass_page"), reverse("profile_texts"),
                    reverse("seviye_testi"), "/sozluk/seviye/b1/"]
        self.assertEqual(self._eksikler(adresler), [], "site.css yeniden derlenmeli")

    def test_girisli_sayfalar(self):
        self.client.login(username="tw", password=SIFRE)
        adresler = [reverse("index"), reverse("sozluk") + "?sekme=listem", reverse("learn_pass_page"),
                    reverse("exercises_page"), reverse("user_profile"), reverse("settings_page"),
                    reverse("profile_texts"), reverse("new_text_page"), reverse("readings_add"),
                    reverse("seviye_sec")]
        self.assertEqual(self._eksikler(adresler), [], "site.css yeniden derlenmeli")
