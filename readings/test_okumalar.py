"""
Okumalar (rapor 8): kelime sorgulama API'si, kendi metinlerim, PDF, silme.

Önbellek her test sınıfında ayrı bir bellek önbelleğine yönlendiriliyor:
sorgu sonuçları önbelleğe yazıldığı için testler birbirinin sonucunu
görmesin.
"""

import io
import json
import os
import tempfile
from datetime import timedelta
from unittest import mock

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from readings import pdf as pdf_okuyucu
from readings.kelime_sorgu import sorgula, temizle
from readings.models import ReadingText, UserText
from users.models import User
from words.models import PartOfSpeech, UserWordLink, WordForm
from words.testing import make_word


BELLEK = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                      "LOCATION": "okumalar-testleri"}}


def pdf_uret(sayfalar):
    """pymupdf ile küçük bir test PDF'i. sayfalar: her sayfanın metni ("" = boş sayfa)."""
    import pymupdf
    belge = pymupdf.open()
    for yazi in sayfalar:
        sayfa = belge.new_page()
        if yazi:
            sayfa.insert_textbox(pymupdf.Rect(72, 72, 520, 770), yazi, fontsize=11)
    veri = belge.tobytes()
    belge.close()
    return veri


@override_settings(CACHES=BELLEK)
class KelimeSorguTests(TestCase):

    def setUp(self):
        cache.clear()
        self.decide = make_word("decide", pos=PartOfSpeech.VERB, meaning="karar vermek")
        self.decided = make_word("decided", pos=PartOfSpeech.ADJECTIVE, meaning="kesin")
        self.bank = make_word("bank", meaning="banka",
                              extra_meanings=[("nehir kıyısı", "land beside a river")])
        self.bank_v = make_word("bank", pos=PartOfSpeech.VERB, meaning="para yatırmak")
        self.give = make_word("give", pos=PartOfSpeech.VERB, meaning="vermek",
                              v2="gave", v3="given")
        self.give_up = make_word("give up", pos=PartOfSpeech.PHRASAL_VERB,
                                 meaning="vazgeçmek", family="give")
        self.url = reverse("kelime_api")

    def api(self, **p):
        cevap = self.client.get(self.url, p)
        self.assertEqual(cevap.status_code, 200)
        return cevap.json()

    # --- yazım ---------------------------------------------------------

    def test_yazim_temizlenir(self):
        self.assertEqual(temizle("Decided,"), "decided")
        self.assertEqual(temizle("“Bank”"), "bank")
        self.assertEqual(temizle("government’s"), "government")
        self.assertEqual(temizle("..."), "")

    # --- kök -----------------------------------------------------------

    def test_cekimli_bicim_koke_baglanir(self):
        """decided -> decide (WordForm); decided · sıfat da ayrıca döner."""
        self.assertTrue(WordForm.objects.filter(surface="decided", word=self.decide).exists())
        s = self.api(q="decided")
        self.assertTrue(s["bulundu"])
        self.assertEqual(s["kok"], "decide")
        self.assertEqual(s["word_id"], self.decide.id)
        self.assertEqual(s["anlamlar"][0]["tr"], "karar vermek")
        self.assertEqual([m["kok"] for m in s["digerleri"]], ["decided"])

    def test_duzensiz_bicim(self):
        s = self.api(q="Gave")
        self.assertEqual(s["kok"], "give")

    def test_wordformda_olmayan_bicim_kuralla_bulunur(self):
        WordForm.objects.filter(surface="banks").delete()
        s = self.api(q="banks")
        self.assertTrue(s["bulundu"])
        self.assertEqual(s["kok"], "bank")

    # --- çok anlamlı ---------------------------------------------------

    def test_cok_anlamli_hepsi_sirali(self):
        """Tüm anlamlar, en yaygın (sort_order) üstte; türler tek listede, isim önce."""
        s = self.api(q="bank")
        self.assertEqual([a["tr"] for a in s["anlamlar"]],
                         ["banka", "nehir kıyısı", "para yatırmak"])
        self.assertEqual(s["word_id"], self.bank.id)

    def test_sort_order_uyulur(self):
        anlamlar = list(self.bank.meanings.order_by("sort_order"))
        anlamlar[0].sort_order, anlamlar[1].sort_order = 5, 0
        for a in anlamlar:
            a.save()
        s = self.api(q="bank")
        self.assertEqual(s["anlamlar"][0]["tr"], "nehir kıyısı")

    def test_cekim_turu_one_gecer(self):
        """banked fiil çekimi: fiil anlamı üstte."""
        WordForm.objects.get_or_create(word=self.bank_v, surface="banked", defaults={"kind": "past"})
        s = self.api(q="banked")
        self.assertEqual(s["word_id"], self.bank_v.id)
        self.assertEqual(s["anlamlar"][0]["tr"], "para yatırmak")

    # --- bulunamayan ---------------------------------------------------

    def test_bulunamayan(self):
        s = self.api(q="gskjengkwng")
        self.assertFalse(s["bulundu"])
        self.assertEqual(s["anlamlar"], [])
        self.assertIsNone(s["word_id"])
        self.assertFalse(s["listede"])

    def test_bos_sorgu(self):
        self.assertFalse(self.api(q="")["bulundu"])

    def test_bulunamayan_kaydedilir(self):
        """Sözlük'ün bulunamayan kaydı (kaynak=okuma); bulunan ve işlev kelimesi yazılmaz."""
        try:
            from words.models import BulunamayanArama
        except ImportError:
            self.skipTest("words.models.BulunamayanArama yok")
        self.api(q="gskjengkwng")
        self.api(q="the")
        self.api(q="bank")
        self.assertEqual(list(BulunamayanArama.objects.values_list("sorgu", "kaynak")),
                         [("gskjengkwng", "okuma")])

    def test_kayit_hatasi_cevabi_bozmaz(self):
        with mock.patch("words.arama.bulunamayan_kaydet", side_effect=RuntimeError("x")):
            with self.assertLogs("readings.api", level="ERROR"):
                self.assertFalse(self.api(q="gskjengkwng")["bulundu"])

    # --- phrasal -------------------------------------------------------

    def test_phrasal_bitisik(self):
        s = self.api(q="gave", sonra="up smoking")
        self.assertEqual(s["phrasal"]["kok"], "give up")
        self.assertEqual(s["phrasal"]["anlamlar"][0]["tr"], "vazgeçmek")
        self.assertEqual(s["kok"], "give")      # kelimenin kendisi de döner

    def test_phrasal_araya_kelime_girmis(self):
        s = self.api(q="gave", sonra="it up")
        self.assertEqual(s["phrasal"]["kok"], "give up")

    def test_phrasal_parcacika_dokununca(self):
        s = self.api(q="up", once="gave it")
        self.assertEqual(s["phrasal"]["kok"], "give up")

    def test_araya_giren_kelimede_phrasal_yok(self):
        self.assertIsNone(self.api(q="it", once="gave", sonra="up")["phrasal"])

    def test_uzak_parcacik_phrasal_degil(self):
        self.assertIsNone(self.api(q="gave", sonra="the old book up")["phrasal"])

    def test_baglamsiz_phrasal_yok(self):
        self.assertIsNone(self.api(q="gave")["phrasal"])

    # --- liste, görünürlük, hız ------------------------------------------

    def test_misafirde_listede_false_ve_onbellek(self):
        cevap = self.client.get(self.url, {"q": "decide"})
        self.assertFalse(cevap.json()["listede"])
        self.assertIn("public", cevap["Cache-Control"])

    def test_girisli_listede(self):
        user = User.objects.create_user(username="okur", password="Sifre1234")
        UserWordLink.objects.create(user=user, word=self.decide)
        self.client.force_login(user)
        cevap = self.client.get(self.url, {"q": "decided"})
        s = cevap.json()
        self.assertTrue(s["listede"])
        self.assertFalse(s["digerleri"][0]["listede"])
        self.assertIn("private", cevap["Cache-Control"])

    def test_gizli_kelime_gorunmez(self):
        sahip = User.objects.create_user(username="sahip", password="Sifre1234")
        make_word("secretword", is_base=False, visibility="private", owner=sahip)
        self.assertFalse(self.api(q="secretword")["bulundu"])

    def test_sorgu_sayisi_az_ve_onbellekli(self):
        with self.assertNumQueries(5):          # çekim, kelime, anlam, phrasal, anlam
            sorgula("gave", sonra="it up")
        with self.assertNumQueries(0):
            sorgula("gave", sonra="it up")

    def test_cors_ayarla_acilir(self):
        cevap = self.client.get(self.url, {"q": "bank"}, HTTP_ORIGIN="chrome-extension://abc")
        self.assertNotIn("Access-Control-Allow-Origin", cevap)
        with self.settings(KELIME_API_CORS_ORIGINS=["chrome-extension://abc"]):
            cevap = self.client.get(self.url, {"q": "bank"}, HTTP_ORIGIN="chrome-extension://abc")
        self.assertEqual(cevap["Access-Control-Allow-Origin"], "chrome-extension://abc")

    def test_yalnizca_get(self):
        self.assertEqual(self.client.post(self.url, {"q": "bank"}).status_code, 405)


@override_settings(CACHES=BELLEK)
class OkumalarSayfasiTests(TestCase):

    def setUp(self):
        self.kutuphane = ReadingText.objects.create(
            number=7, topic="psikoloji", title="SIBLINGS",
            body="Brothers decided to share.\n\nThey gave it up.", word_count=9)
        self.ali = User.objects.create_user(username="ali", password="Sifre1234")
        self.veli = User.objects.create_user(username="veli", password="Sifre1234")
        self.alinin = UserText.objects.create(owner=self.ali, title="Ali'nin notu",
                                              body="Private text here.", source_kind="paste",
                                              word_count=3)

    def test_misafir_kutuphaneyi_gorur(self):
        cevap = self.client.get(reverse("readings"))
        self.assertEqual(cevap.status_code, 200)
        self.assertContains(cevap, "Siblings")
        self.assertContains(cevap, 'data-giris-gerekli="pdf"')
        self.assertContains(cevap, "PDF yükle")
        self.assertNotContains(cevap, "Ali&#x27;nin notu")

        metin = self.client.get(reverse("readings_library_text", args=[7]))
        self.assertEqual(metin.status_code, 200)
        self.assertContains(metin, "Brothers decided to share.")
        self.assertContains(metin, "data-okuma-metni")

    def test_bos_kutuphane_cesaretlendirir(self):
        ReadingText.objects.all().delete()
        self.assertContains(self.client.get(reverse("readings")), "Kütüphane hazırlanıyor")

    def test_konu_filtresi(self):
        ReadingText.objects.create(number=8, topic="hukuk", title="LAW TEXT", body="x", word_count=1)
        cevap = self.client.get(reverse("readings"), {"konu": "hukuk"})
        self.assertContains(cevap, "Law text")
        self.assertNotContains(cevap, "Siblings")

    def test_misafir_yukleyemez(self):
        cevap = self.client.get(reverse("readings_add"))
        self.assertContains(cevap, "giriş", status_code=200)
        self.assertNotContains(cevap, 'name="dosya"')
        cevap = self.client.post(reverse("readings_add"), {"tur": "yapistir", "metin": "x " * 50})
        self.assertEqual(UserText.objects.count(), 1)

    def test_kendi_metnim_yalnizca_sahibine(self):
        adres = reverse("readings_user_text", args=[self.alinin.id])
        self.client.force_login(self.veli)
        self.assertEqual(self.client.get(adres).status_code, 404)
        self.assertNotContains(self.client.get(reverse("readings")), "Ali&#x27;nin notu")

        self.client.force_login(self.ali)
        self.assertContains(self.client.get(adres), "Private text here.")
        self.assertContains(self.client.get(reverse("readings")), "Ali&#x27;nin notu")

    def test_baskasi_silemez(self):
        self.client.force_login(self.veli)
        cevap = self.client.post(reverse("readings_user_text_delete", args=[self.alinin.id]))
        self.assertEqual(cevap.status_code, 404)
        self.alinin.refresh_from_db()
        self.assertIsNone(self.alinin.deleted_at)

    def test_yapistir(self):
        self.client.force_login(self.ali)
        cevap = self.client.post(reverse("readings_add"), {
            "tur": "yapistir", "baslik": "",
            "metin": "First line of the text here.\r\nSecond line continues it."})
        yeni = UserText.objects.exclude(pk=self.alinin.pk).get()
        self.assertRedirects(cevap, reverse("readings_user_text", args=[yeni.id]))
        self.assertEqual(yeni.owner, self.ali)
        self.assertEqual(yeni.source_kind, "paste")
        self.assertEqual(len(yeni.paragraphs), 2)
        self.assertTrue(yeni.title.startswith("First line"))

    def test_cok_kisa_yapistirma_nazikce_reddedilir(self):
        self.client.force_login(self.ali)
        cevap = self.client.post(reverse("readings_add"), {"tur": "yapistir", "metin": "hi"})
        self.assertContains(cevap, "biraz daha uzun", status_code=400)

    def test_pdf_yukle(self):
        self.client.force_login(self.ali)
        dosya = SimpleUploadedFile("ders-notu.pdf", pdf_uret(["The committee decided to act quickly."]),
                                   content_type="application/pdf")
        cevap = self.client.post(reverse("readings_add"), {"tur": "pdf", "dosya": dosya})
        yeni = UserText.objects.exclude(pk=self.alinin.pk).get()
        self.assertRedirects(cevap, reverse("readings_user_text", args=[yeni.id]))
        self.assertEqual(yeni.title, "ders-notu")
        self.assertEqual(yeni.source_kind, "pdf")
        self.assertIn("decided to act", yeni.body)

    def test_taranmis_pdf_nazik_hata(self):
        self.client.force_login(self.ali)
        dosya = SimpleUploadedFile("tarama.pdf", pdf_uret(["", ""]), content_type="application/pdf")
        cevap = self.client.post(reverse("readings_add"), {"tur": "pdf", "dosya": dosya})
        self.assertContains(cevap, "okunabilir metin bulamadık", status_code=400)
        self.assertEqual(UserText.objects.count(), 1)

    def test_yumusak_silme_ve_geri_al(self):
        self.client.force_login(self.ali)
        cevap = self.client.post(reverse("readings_user_text_delete", args=[self.alinin.id]),
                                 HTTP_X_REQUESTED_WITH="fetch")
        veri = cevap.json()
        self.alinin.refresh_from_db()
        self.assertIsNotNone(self.alinin.deleted_at)
        self.assertNotContains(self.client.get(reverse("readings")), "Ali&#x27;nin notu")
        self.assertEqual(self.client.get(reverse("readings_user_text", args=[self.alinin.id])).status_code, 404)

        # Başkası geri alamaz
        self.client.force_login(self.veli)
        self.assertEqual(self.client.post(veri["geri_al_url"]).status_code, 404)

        self.client.force_login(self.ali)
        self.assertEqual(self.client.post(veri["geri_al_url"], HTTP_X_REQUESTED_WITH="fetch").json(),
                         {"ok": True})
        self.alinin.refresh_from_db()
        self.assertIsNone(self.alinin.deleted_at)
        self.assertContains(self.client.get(reverse("readings")), "Ali&#x27;nin notu")

    def test_eski_cop_temizlenir(self):
        self.alinin.deleted_at = timezone.now() - timedelta(days=2)
        self.alinin.save()
        self.client.force_login(self.ali)
        self.client.get(reverse("readings"))
        self.assertFalse(UserText.objects.filter(pk=self.alinin.pk).exists())

    def test_silme_get_ile_olmaz(self):
        self.client.force_login(self.ali)
        adres = reverse("readings_user_text_delete", args=[self.alinin.id])
        self.assertEqual(self.client.get(adres).status_code, 405)


class PdfMetniTests(TestCase):

    def test_metin_cikar(self):
        metin, bilgi = pdf_okuyucu.pdf_metni(pdf_uret([
            "Researchers decided to look into the problem.", "Page two text continues here."]))
        self.assertIn("decided to look into", metin)
        self.assertIn("Page two text", metin)
        self.assertEqual(bilgi["sayfa"], 2)

    def test_taranmis(self):
        with self.assertRaisesMessage(pdf_okuyucu.PdfOkunamadi, "taranmış olabilir"):
            pdf_okuyucu.pdf_metni(pdf_uret([""]))

    def test_pdf_olmayan_dosya(self):
        with self.assertRaises(pdf_okuyucu.PdfOkunamadi):
            pdf_okuyucu.pdf_metni(b"merhaba, ben bir PDF degilim")

    def test_sayfa_siniri(self):
        with mock.patch.object(pdf_okuyucu, "EN_COK_SAYFA", 1):
            with self.assertRaisesMessage(pdf_okuyucu.PdfOkunamadi, "sayfa"):
                pdf_okuyucu.pdf_metni(pdf_uret(["one page here", "two"]))

    def test_boyut_siniri(self):
        with mock.patch.object(pdf_okuyucu, "EN_BUYUK_BOYUT", 10):
            with self.assertRaisesMessage(pdf_okuyucu.PdfOkunamadi, "10 MB"):
                pdf_okuyucu.pdf_metni(pdf_uret(["some text"]))

    def test_satir_sonu_tiresi_birlesir(self):
        metin, _ = pdf_okuyucu.pdf_metni(pdf_uret(["The environ-\nment matters a great deal to all of us."]))
        self.assertIn("environment", metin)


class KutuphaneYukleTests(TestCase):
    """D5 için yükleme komutu (veri eklenmiyor, yalnızca altyapı)."""

    def _dosya(self, satirlar):
        yol = os.path.join(tempfile.mkdtemp(), "metinler.jsonl")
        with io.open(yol, "w", encoding="utf-8") as f:
            for s in satirlar:
                f.write((s if isinstance(s, str) else json.dumps(s, ensure_ascii=False)) + "\n")
        return yol

    def test_yukle_ve_tekrar_calistir(self):
        yol = self._dosya([
            {"number": 101, "title": "The Keeper", "topic": "sosyoloji", "cefr": "b1",
             "source": "Yapay zekâ", "paragraphs": ["One.", "Two words."]},
            {"title": "No Number", "topic": "hukuk", "body": "A.\n\nB."},
        ])
        call_command("kutuphane_yukle", yol, stdout=io.StringIO())
        metin = ReadingText.objects.get(number=101)
        self.assertEqual((metin.cefr, metin.source, metin.word_count), ("B1", "Yapay zekâ", 3))
        self.assertEqual(ReadingText.objects.get(title="No Number").number, 102)

        call_command("kutuphane_yukle", yol, stdout=io.StringIO())
        self.assertEqual(ReadingText.objects.count(), 2)

    def test_dry_run_yazmaz(self):
        yol = self._dosya([{"title": "T", "topic": "hukuk", "paragraphs": ["x"]}])
        call_command("kutuphane_yukle", yol, dry_run=True, stdout=io.StringIO())
        self.assertEqual(ReadingText.objects.count(), 0)

    def test_hatali_satir(self):
        for satir in ("{bozuk", {"title": "", "paragraphs": ["x"]},
                      {"title": "T", "paragraphs": ["x"], "cefr": "Z9"}):
            with self.subTest(satir=satir):
                with self.assertRaises(CommandError):
                    call_command("kutuphane_yukle", self._dosya([satir]), stdout=io.StringIO())
