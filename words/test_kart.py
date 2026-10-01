"""
Ortak kelime kartı (ürün raporu 4.3) ve Sözlük iskeleti.

Kart verisi: words/kart.py (kart_verisi)
Şablon:      templates/base/_kelimeKarti.html
"""

import json
import re
from datetime import timedelta

from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import User
from words import inflect
from words.kart import kart_verisi, tur_etiketi
from words.models import UserWordLink, WordFamily, WordRelation
from words.testing import make_word


def _bolum(html, oznitelik, deger):
    """<section data-anlam="…"> gibi bir bloğun içeriği (bir sonraki kardeşe kadar)."""
    basla = html.index(f'{oznitelik}="{deger}"')
    son = html.find("<section", basla + 1)
    return html[basla:son if son != -1 else len(html)]


class DuzensizFiilTests(TestCase):
    """V2 · V3 yalnızca düzensiz fiilde (rapor 4.3)."""

    def test_duzensizler(self):
        for kok, v2, v3 in (("go", "went", "gone"), ("cut", "cut", "cut"),
                            ("flee", "fled", "fled"), ("pay", "paid", "paid"),
                            ("hear", "heard", "heard"), ("give up", "gave up", "given up")):
            with self.subTest(kok=kok):
                self.assertTrue(inflect.duzensiz_fiil_mi(kok, v2, v3))

    def test_duzenliler(self):
        """Veritabanında düzenli fiillerin de v2/v3 alanı dolu; bunlar gösterilmez."""
        for kok, v2, v3 in (("decide", "decided", "decided"), ("aim", "aimed", "aimed"),
                            ("embed", "embedded", "embedded"), ("format", "formatted", "formatted"),
                            ("panic", "panicked", "panicked"), ("study", "studied", "studied"),
                            ("stop", "stopped", "stopped"), ("walk", None, None)):
            with self.subTest(kok=kok):
                self.assertFalse(inflect.duzensiz_fiil_mi(kok, v2, v3))


class KartVerisiTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="kartci", password="Sifre1234")
        # bank: 1. banka  2. nehir kıyısı — shore yalnızca ikincisinde (rapor 4.3, D1)
        self.bank = make_word("bank", meaning="banka", definition="a place for money",
                              extra_meanings=[("nehir kıyısı", "land beside a river")])
        self.banka, self.kiyi = list(self.bank.meanings.order_by("sort_order"))
        self.shore = make_word("shore", meaning="kıyı")
        self.lender = make_word("lender", meaning="borç veren")
        WordRelation.objects.create(from_word=self.bank, to_word=self.shore,
                                    type="synonym", meaning=self.kiyi)
        WordRelation.objects.create(from_word=self.bank, to_word=self.lender,
                                    type="synonym", meaning=self.banka)

    def test_bank_shore_yalnizca_nehir_kiyisi_anlaminda(self):
        kart, = kart_verisi([self.bank], self.user)
        banka, kiyi = kart.anlamlar
        self.assertEqual(kiyi.iliski_satirlari, [("Benzer", [self.shore])])
        self.assertEqual(banka.iliski_satirlari, [("Benzer", [self.lender])])

    def test_turkce_tur_ve_seviye(self):
        kart, = kart_verisi([self.bank])
        self.assertEqual(kart.tur, "isim")
        self.assertEqual(kart.cefr, "B2")
        self.assertEqual(tur_etiketi("verb"), "fiil")
        self.assertEqual(tur_etiketi("adjective"), "sıfat")
        self.assertEqual(tur_etiketi("adverb"), "zarf")

    def test_seviyesiz_kelimede_rozet_yok(self):
        k = make_word("thing", level="Belirtilmemiş")
        self.assertEqual(kart_verisi([k])[0].cefr, "")

    def test_duzensiz_fiilde_v2_v3_duzenlide_bos(self):
        go = make_word("go", pos="verb", v2="went", v3="gone")
        decide = make_word("decide", pos="verb", v2="decided", v3="decided")
        kgo, kdecide = kart_verisi([go, decide])
        self.assertEqual((kgo.v2, kgo.v3), ("went", "gone"))
        self.assertTrue(kgo.duzensiz)
        self.assertEqual((kdecide.v2, kdecide.v3), ("", ""))
        self.assertFalse(kdecide.duzensiz)

    def test_ornekler_ilk_ornek_ve_digerleri(self):
        k = make_word("tidy", sentences=["First.", "Second.", "Third."])
        kart, = kart_verisi([k])
        self.assertEqual(kart.anlamlar[0].ornek, "First.")
        self.assertEqual(kart.anlamlar[0].diger_ornekler, ["Second.", "Third."])

    def test_kaliplar_collocation_ve_kalip_birlikte(self):
        k = make_word("decision",
                      collocations=[{"pattern": "make a decision", "kind": "verb_noun",
                                     "meaning_tr": "karar vermek", "example": "We made a decision."}],
                      patterns=[{"pattern": "decision to do sth", "example": "The decision to leave."}])
        kaliplar = kart_verisi([k])[0].anlamlar[0].kaliplar
        self.assertEqual(kaliplar[0], {"metin": "make a decision", "anlam": "karar vermek",
                                       "ornek": "We made a decision."})
        self.assertEqual(kaliplar[1]["metin"], "decision to do sth")

    def test_aile_ayni_yazimi_ve_gizli_kelimeyi_gostermez(self):
        aile = WordFamily.objects.create(root="aim")
        isim = make_word("aim", family=aile)
        make_word("aim", pos="verb", family=aile, v2="aimed", v3="aimed")
        make_word("aimless", pos="adjective", family=aile)
        make_word("aimlessly", pos="adverb", family=aile)
        make_word("aimster", family=aile, is_base=False, visibility="private", owner=self.user)
        kart, = kart_verisi([isim])
        self.assertEqual([w.text for w in kart.aile], ["aimless", "aimlessly"])

    def test_liste_durumu(self):
        UserWordLink.objects.create(user=self.user, word=self.bank)
        kbank, kshore = kart_verisi([self.bank, self.shore], self.user)
        self.assertTrue(kbank.listede)
        self.assertFalse(kshore.listede)
        # girişsiz
        self.assertFalse(kart_verisi([self.bank])[0].listede)

    def test_sira_korunur_tekrar_atilir(self):
        kartlar = kart_verisi([self.shore.id, self.bank.id, self.shore.id])
        self.assertEqual([k.text for k in kartlar], ["shore", "bank"])
        self.assertEqual(kart_verisi([]), [])

    def test_sorgu_sayisi_kart_sayisina_bagli_degil(self):
        """N+1 yok: 1 kart da 12 kart da aynı sayıda sorgu (en çok 8)."""
        kelimeler = []
        aile = WordFamily.objects.create(root="ortak")
        for i in range(12):
            k = make_word(f"kelime{i}", family=aile, sentences=["A.", "B."],
                          extra_meanings=[(f"anlam{i}", "def")],
                          collocations=[(f"kalip {i}", "other")], patterns=[f"desen {i}"])
            WordRelation.objects.create(from_word=k, to_word=self.shore, type="synonym",
                                        meaning=k.meanings.first())
            WordRelation.objects.create(from_word=k, to_word=self.lender, type="antonym",
                                        meaning=k.meanings.last())
            kelimeler.append(k)
        UserWordLink.objects.create(user=self.user, word=kelimeler[0])

        with self.assertNumQueries(8):
            tek = kart_verisi(kelimeler[:1], self.user)
        with self.assertNumQueries(8):
            hepsi = kart_verisi(kelimeler, self.user)
        self.assertEqual(len(tek), 1)
        self.assertEqual(len(hepsi), 12)
        # Şablon ek sorgu yapmamalı
        with self.assertNumQueries(0):
            html = "".join(render_to_string("base/_kelimeKarti.html", {"kart": k, "kapali": False})
                           for k in hepsi)
        self.assertIn("kelime11", html)


# Sayfadaki gerçek liste düğmeleri (JS içindeki seçici yazıları sayılmasın)
LISTE_DUGMESI = re.compile(r"<button[^>]*\bdata-kelime-liste\b")


class KartSablonuTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="sablon", password="Sifre1234")
        self.bank = make_word("bank", meaning="banka", definition="a place for money",
                              sentences=["I went to the bank.", "The bank opened."],
                              extra_meanings=[("nehir kıyısı", "land beside a river")])
        self.banka, self.kiyi = list(self.bank.meanings.order_by("sort_order"))
        self.shore = make_word("shore", meaning="kıyı")
        WordRelation.objects.create(from_word=self.bank, to_word=self.shore,
                                    type="synonym", meaning=self.kiyi)

    def _sozluk(self, q, giris=False):
        if giris:
            self.client.login(username="sablon", password="Sifre1234")
        # Tam eşleşen arama kelimenin kalıcı sayfasına yönlenir (rapor 18.15).
        cevap = self.client.get(reverse("sozluk"), {"q": q}, follow=True)
        self.assertEqual(cevap.status_code, 200)
        return cevap.content.decode()

    def test_shore_cipi_yalnizca_nehir_kiyisi_blogunda(self):
        html = self._sozluk("bank")
        banka = _bolum(html, "data-anlam", self.banka.id)
        kiyi = _bolum(html, "data-anlam", self.kiyi.id)
        cip = 'href="/sozluk/shore/"'
        self.assertIn(cip, kiyi)
        self.assertNotIn(cip, banka)
        self.assertIn(">benzer:<", kiyi.replace("\n", ""))

    def test_bos_cip_satiri_gosterilmez(self):
        html = self._sozluk("bank")
        banka = _bolum(html, "data-anlam", self.banka.id)
        self.assertNotIn("data-iliski-satiri", banka)
        self.assertEqual(html.count('data-iliski-satiri="Benzer"'), 1)
        self.assertNotIn('data-iliski-satiri="Zıt"', html)
        self.assertNotIn('data-iliski-satiri="Daha basit"', html)

    def test_baslik_tur_seviye_ve_numarali_anlamlar(self):
        html = self._sozluk("bank")
        self.assertIn('data-tur>isim<', html)
        self.assertIn(">B2<", html)
        self.assertIn("nehir kıyısı", html)
        self.assertIn("a place for money", html)
        self.assertIn("I went to the bank.", html)            # ilk örnek
        self.assertIn("Daha fazla örnek", html)               # ikinci örnek kapalı
        self.assertIn(">1</span>", html)                    # el yazısı anlam numarası (defter)

    def test_duzensiz_fiil_basligi(self):
        make_word("go", pos="verb", v2="went", v3="gone")
        make_word("decide", pos="verb", v2="decided", v3="decided")
        self.assertIn("went · gone", self._sozluk("go"))
        self.assertNotIn("data-fiil-halleri>", self._sozluk("decide"))

    def test_kaliplar_turkce_anlamiyla(self):
        make_word("decision", collocations=[{"pattern": "make a decision", "kind": "verb_noun",
                                             "meaning_tr": "karar vermek", "example": "We made one."}])
        html = self._sozluk("decision")
        self.assertIn("Kalıplar", html)
        self.assertIn("make a decision", html)
        self.assertIn("karar vermek", html)

    def test_ilk_kart_acik_digerleri_kapali(self):
        aile = WordFamily.objects.create(root="aim")
        make_word("aim", family=aile, meaning="amaç")
        make_word("aim", pos="verb", family=aile, meaning="hedeflemek", v2="aimed", v3="aimed")
        make_word("aimless", pos="adjective", family=aile)
        html = self._sozluk("aim")
        # Kelime sayfası defter maddesidir (rapor 18.12): bütün türler açık.
        durumlar = re.findall(r'x-data="\{ acik: (true|false) \}"', html)
        self.assertEqual(durumlar, ["true", "true"])
        self.assertIn("Aile:", html)
        self.assertIn('href="/sozluk/aimless/"', html)
        # Kapalı hâlin tek satırı: kelime · tür · anlam · seviye
        self.assertIn("hedeflemek", html)
        self.assertIn(">fiil<", html)

    def test_girissiz_liste_dugmesi_yok(self):
        """Rapor 18.3 / 18.5: misafire "Listeme ekle" düğmesi hiç gösterilmez."""
        html = self._sozluk("bank")
        self.assertEqual(LISTE_DUGMESI.findall(html), [])
        self.assertNotIn('data-giris-gerekli="liste"', html)

    def test_kapali_kartta_da_ayni_liste_dugmesi(self):
        """Rapor 18.5: kapalı (tek satırlık) kartta da kare "+" değil "Listeme ekle +"."""
        aile = WordFamily.objects.create(root="aim")
        make_word("aim", family=aile, meaning="amaç")
        make_word("aim", pos="verb", family=aile, meaning="hedeflemek")
        html = self._sozluk("aim", giris=True)
        # Kelime sayfası (defter maddesi): her türün kendi düğmesi, hepsi yazılı
        self.assertEqual(len(LISTE_DUGMESI.findall(html)), 2)
        self.assertEqual(html.count("Listeme ekle <span"), 2)
        self.assertNotIn('<span class="sr-only">Listeme ekle</span>', html)

    def test_telaffuz_dugmeleri_iki_aksan(self):
        """Rapor 18.4: kartta Amerikan ve İngiliz aksanı düğmeleri, okunacak kelimeyle."""
        html = self._sozluk("bank")
        self.assertIn('data-telaffuz="en-US" data-metin="bank"', html)
        self.assertIn('data-telaffuz="en-GB" data-metin="bank"', html)

    def test_ingilizce_icerik_lang_en(self):
        html = self._sozluk("bank")
        self.assertIn('<html lang="tr">', html)
        self.assertIn('<h1 lang="en"', html)

    def test_girisli_dugme_listede_durumunu_gosterir(self):
        UserWordLink.objects.create(user=self.user, word=self.bank)
        html = self._sozluk("bank", giris=True)
        self.assertNotIn('data-giris-gerekli="', html)
        self.assertIn('data-listede="1"', html)
        self.assertIn(reverse("remove_from_my_list", args=[self.bank.id]), html)

    def test_karanlik_mod_siniflari(self):
        html = self._sozluk("bank")
        kart = html[html.index("<article"):html.index("</article>")]
        # Defter teması: .lv-* sınıfları koyu temayı CSS değişkenleriyle çözer.
        self.assertGreater(kart.count("dark:") + kart.count("lv-"), 15)


class ListeUclariTests(TestCase):
    """Kartın "Listeme ekle" / "Listemden çıkar · Geri al" uçları (fetch ile)."""

    def setUp(self):
        self.user = User.objects.create_user(username="liste", password="Sifre1234")
        self.client.login(username="liste", password="Sifre1234")
        self.word = make_word("tidy")
        self.fetch = {"HTTP_X_REQUESTED_WITH": "fetch"}

    def test_ekle_ve_cikar_json(self):
        cevap = self.client.post(reverse("add_to_my_list", args=[self.word.id]), **self.fetch)
        self.assertEqual(cevap.json()["kayitli"], True)
        self.assertTrue(UserWordLink.objects.filter(user=self.user, word=self.word).exists())

        cevap = self.client.post(reverse("remove_from_my_list", args=[self.word.id]), **self.fetch)
        veri = cevap.json()
        self.assertFalse(veri["kayitli"])
        self.assertIn("dateAdded", veri["geri"])
        self.assertFalse(UserWordLink.objects.filter(user=self.user, word=self.word).exists())

    def test_geri_al_tarih_ve_sayaclari_korur(self):
        eski = timezone.now() - timedelta(days=10)
        bag = UserWordLink.objects.create(user=self.user, word=self.word, correctCount=3, wrongCount=2)
        UserWordLink.objects.filter(pk=bag.pk).update(dateAdded=eski)

        geri = self.client.post(reverse("remove_from_my_list", args=[self.word.id]),
                                **self.fetch).json()["geri"]
        self.client.post(reverse("add_to_my_list", args=[self.word.id]),
                         {"geri": json.dumps(geri)}, **self.fetch)
        bag = UserWordLink.objects.get(user=self.user, word=self.word)
        self.assertEqual((bag.correctCount, bag.wrongCount), (3, 2))
        self.assertEqual(bag.dateAdded, eski)

    def test_geri_verisi_gelecek_tarih_ve_bozuk_veri_kabul_edilmez(self):
        gelecek = (timezone.now() + timedelta(days=30)).isoformat()
        self.client.post(reverse("add_to_my_list", args=[self.word.id]),
                         {"geri": json.dumps({"dateAdded": gelecek, "correctCount": 1})}, **self.fetch)
        bag = UserWordLink.objects.get(user=self.user, word=self.word)
        self.assertLessEqual(bag.dateAdded, timezone.now())
        bag.delete()
        cevap = self.client.post(reverse("add_to_my_list", args=[self.word.id]),
                                 {"geri": "{bozuk"}, **self.fetch)
        self.assertEqual(cevap.status_code, 200)
        self.assertEqual(UserWordLink.objects.get(user=self.user, word=self.word).correctCount, 0)

    def test_girissiz_ekleme_yapilamaz(self):
        self.client.logout()
        cevap = self.client.post(reverse("add_to_my_list", args=[self.word.id]), **self.fetch)
        self.assertEqual(cevap.status_code, 302)
        self.assertFalse(UserWordLink.objects.exists())


class SozlukSayfasiTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="sozluk", password="Sifre1234")

    def test_girissiz_yalnizca_kesfet(self):
        html = self.client.get(reverse("sozluk")).content.decode()
        # Rapor 18.3: misafirde sekme çubuğu hiç yok; en üstte giriş daveti.
        self.assertNotIn('role="tablist"', html)
        self.assertIn("data-misafir-daveti", html)
        self.assertIn("Kelimelerini kaydetmek için", html)
        self.assertNotIn("?sekme=listem", html)
        self.assertIn("İngilizce veya Türkçe ara", html)
        # Adresle Listem istense bile Keşfet açılır
        cevap = self.client.get(reverse("sozluk"), {"sekme": "listem"})
        self.assertEqual(cevap.context["sekme"], "kesfet")

    def test_girisli_listem_sekmesi(self):
        self.client.login(username="sozluk", password="Sifre1234")
        html = self.client.get(reverse("sozluk")).content.decode()
        self.assertIn("?sekme=listem", html)
        html = self.client.get(reverse("sozluk"), {"sekme": "listem"}).content.decode()
        self.assertIn("Listen boş.", html)
        self.assertIn("Listende ara", html)

    def test_bulunamayan_sorgu(self):
        html = self.client.get(reverse("sozluk"), {"q": "gskjengkwng"}).content.decode()
        self.assertIn("Henüz sözlüğümüzde yok.", html)

    def test_gizli_kelime_kart_olarak_gelmez(self):
        diger = User.objects.create_user(username="diger", password="Sifre1234")
        make_word("secretword", is_base=False, visibility="private", owner=diger)
        cevap = self.client.get(reverse("sozluk"), {"q": "secretword"})
        self.assertEqual(cevap.context["kartlar"], [])


class TelaffuzDosyasiTests(TestCase):
    """Rapor 18.4: üretilmiş MP3 varsa düğme onu çalar, yoksa tarayıcı sesine döner."""

    def test_dosya_adi_kurali(self):
        from words.telaffuz import dosya_adi
        self.assertEqual(dosya_adi("Give up", "us"), "give-up_us.mp3")
        self.assertEqual(dosya_adi("it's", "uk"), "it-s_uk.mp3")
        self.assertEqual(dosya_adi("  ", "us"), None)
        self.assertEqual(dosya_adi("bank", "fr"), None)

    def test_dosya_varsa_dugme_adresi_tasir(self):
        import os
        import tempfile

        from django.test import override_settings

        make_word("bank", meaning="banka")
        with tempfile.TemporaryDirectory() as klasor:
            os.makedirs(os.path.join(klasor, "telaffuz"))
            open(os.path.join(klasor, "telaffuz", "bank_us.mp3"), "wb").close()
            with override_settings(MEDIA_ROOT=klasor):
                html = self.client.get(reverse("sozluk_kelime", args=["bank"])).content.decode()
        self.assertIn('data-telaffuz="en-US" data-metin="bank" data-ses="/media/telaffuz/bank_us.mp3"', html)
        # UK dosyası yok: düğme var ama adres taşımıyor (tarayıcı sesi yedek)
        self.assertIn('data-telaffuz="en-GB" data-metin="bank"\n', html)
