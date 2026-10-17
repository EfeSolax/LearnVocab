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

    # --- tireli yazım ---------------------------------------------------
    def test_tireli_yazim_sozlukte_yoksa_dokunulan_parca_aranir(self):
        s = self.api(q="bank-decided", parca="bank")
        self.assertTrue(s["bulundu"])
        self.assertEqual((s["q"], s["kok"]), ("bank", "bank"))

    def test_parca_verilmezse_son_parca_aranir(self):
        s = self.api(q="hen-decided")
        self.assertEqual(s["kok"], "decide")

    def test_tireli_madde_sozlukte_varsa_butunu_gelir(self):
        make_word("self-conscious", pos=PartOfSpeech.ADJECTIVE, meaning="çekingen")
        s = self.api(q="self-conscious", parca="self")
        self.assertEqual((s["kok"], s["anlamlar"][0]["tr"]), ("self-conscious", "çekingen"))

    def test_hicbiri_yoksa_butun_bulunamadi_olarak_doner(self):
        s = self.api(q="zzq-xxw", parca="zzq")
        self.assertFalse(s["bulundu"])
        self.assertEqual(s["q"], "zzq-xxw")

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

        metin = self.client.get(reverse("readings_library_text", args=[ReadingText.objects.get(number=7).slug]))
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
        sayfa = self.client.get(reverse("readings"))
        self.assertEqual(sayfa.context["metinlerim"], [])
        # Çöp kutusunda durur: geri alınabilir ya da kalıcı silinebilir (rapor 18.24)
        self.assertEqual([m.id for m in sayfa.context["cop"]], [self.alinin.id])
        self.assertContains(sayfa, "data-cop-kutusu")
        self.assertContains(sayfa, "7 gün kaldı")
        self.assertContains(sayfa, reverse("readings_user_text_purge", args=[self.alinin.id]))
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

    def test_cop_bir_hafta_sonra_temizlenir(self):
        from readings import depo
        dosya = self.alinin.dosya
        self.assertEqual(depo.oku(dosya), "Private text here.")
        self.alinin.deleted_at = timezone.now() - timedelta(days=6)
        self.alinin.save()
        self.client.force_login(self.ali)
        self.client.get(reverse("readings"))
        self.assertTrue(UserText.objects.filter(pk=self.alinin.pk).exists())     # 6 gün: duruyor

        UserText.objects.filter(pk=self.alinin.pk).update(deleted_at=timezone.now() - timedelta(days=8))
        self.client.get(reverse("readings"))
        self.assertFalse(UserText.objects.filter(pk=self.alinin.pk).exists())
        self.assertEqual(depo.oku(dosya), "")                                    # dosyası da gitti

    def test_kalici_silme_yalnizca_coptekine_ve_sahibine(self):
        self.client.force_login(self.ali)
        adres = reverse("readings_user_text_purge", args=[self.alinin.id])
        self.assertEqual(self.client.post(adres).status_code, 404)               # çöpte değil
        self.alinin.deleted_at = timezone.now()
        self.alinin.save()
        self.client.force_login(self.veli)
        self.assertEqual(self.client.post(adres).status_code, 404)               # başkasının
        self.client.force_login(self.ali)
        self.assertRedirects(self.client.post(adres), reverse("readings"))
        self.assertFalse(UserText.objects.filter(pk=self.alinin.pk).exists())

    def test_govde_veritabaninda_degil_diskte_sikistirilmis(self):
        from django.conf import settings
        from readings import depo
        uzun = "The quick brown fox jumps over the lazy dog. " * 400
        m = UserText.objects.create(owner=self.ali, title="Uzun", body=uzun, source_kind="paste")
        self.assertFalse(any(f.name == "body" for f in UserText._meta.get_fields()))
        self.assertTrue(m.dosya.startswith(f"okumalar/{self.ali.id}/"))
        yol = settings.OZEL_DEPO / m.dosya
        self.assertLess(yol.stat().st_size, len(uzun) / 3)                      # sıkıştırılmış
        self.assertEqual(UserText.objects.get(pk=m.pk).body, uzun)              # okurken açılır
        with self.assertRaises(ValueError):
            depo.yaz("../disari.txt", "x")

    def test_en_cok_15_pdf_ama_yapistirma_serbest(self):
        from readings import views
        for i in range(views.EN_COK_PDF):
            UserText.objects.create(owner=self.ali, title=f"p{i}", body="x", source_kind="pdf")
        self.client.force_login(self.ali)
        cevap = self.client.post(reverse("readings_add"), {"tur": "pdf"})
        self.assertEqual(cevap.status_code, 400)
        self.assertContains(cevap, "En çok 15 PDF", status_code=400)
        cevap = self.client.post(reverse("readings_add"), {
            "tur": "yapistir", "metin": "This is a pasted text that is long enough to read."})
        self.assertEqual(cevap.status_code, 302)
        # Çöpteki PDF sınıra sayılmaz
        UserText.objects.filter(owner=self.ali, title="p0").update(deleted_at=timezone.now())
        cevap = self.client.post(reverse("readings_add"), {"tur": "pdf"})
        self.assertContains(cevap, "Bir PDF dosyası seçer misin?", status_code=400)

    def test_uzun_metin_bolum_bolum(self):
        from readings import views
        paragraf = " ".join(["word"] * 500)
        m = UserText.objects.create(owner=self.ali, title="Kitap", source_kind="pdf",
                                    body="\n\n".join([paragraf] * 7), word_count=3500)
        self.assertEqual([len(b) for b in views.bolumle(m.paragraphs)], [3, 3, 1])
        self.client.force_login(self.ali)
        adres = reverse("readings_user_text", args=[m.id])
        ilk = self.client.get(adres)
        self.assertEqual((ilk.context["bolum"], ilk.context["bolum_sayisi"], len(ilk.context["paragraflar"])),
                         (1, 3, 3))
        self.assertContains(ilk, "Bölüm 1 / 3")
        self.assertContains(ilk, 'rel="next" href="?bolum=2"')
        son = self.client.get(adres, {"bolum": 99})
        self.assertEqual((son.context["bolum"], len(son.context["paragraflar"])), (3, 1))
        # Kısa metinde bölüm çubuğu yok
        self.assertNotContains(self.client.get(reverse("readings_user_text", args=[self.alinin.id])),
                               "data-bolumler")

    def test_silme_get_ile_olmaz(self):
        self.client.force_login(self.ali)
        adres = reverse("readings_user_text_delete", args=[self.alinin.id])
        self.assertEqual(self.client.get(adres).status_code, 405)


class TemizlikTests(TestCase):
    """Kendi metinlerimde bağlantı ve tekrar eden üst/alt bilgi ayıklama (readings/temizlik.py)."""

    def test_tekrar_eden_kisa_satir_atilir_bolum_basligi_kalir(self):
        from readings.temizlik import paragraflari_temizle
        p = ["Animal Farm", "Chapter 1", "Mr. Jones locked the hen-houses.", "12 Animal Farm",
             "Chapter 2", "The animals met in the barn.", "13 ANIMAL FARM", "Chapter 3"]
        self.assertEqual(paragraflari_temizle(p),
                         ["Chapter 1", "Mr. Jones locked the hen-houses.", "Chapter 2",
                          "The animals met in the barn.", "Chapter 3"])

    def test_sayfa_sonunda_bolunen_cumle_birlesir(self):
        from readings.temizlik import paragraflari_temizle
        p = ["He made his way up to bed, where Mrs. Jones was already", "Animal Farm by George Orwell",
             "snoring.", "Animal Farm by George Orwell", "Old Major spoke.", "Animal Farm by George Orwell"]
        self.assertEqual(paragraflari_temizle(p),
                         ["He made his way up to bed, where Mrs. Jones was already snoring.", "Old Major spoke."])

    def test_cumle_icindeki_alan_adi_korunur(self):
        from readings.temizlik import baglantilari_sil
        uzun = "He said that he had ordered every single one of the old books from Amazon.com last year."
        self.assertEqual(baglantilari_sil(uzun), uzun)
        self.assertEqual(baglantilari_sil("Visit www.example.org for more."), "")   # altbilgi kırıntısı
        self.assertEqual(baglantilari_sil("The full report, which is at https://example.org/report, was read by the board."),
                         "The full report, which is at, was read by the board.")

    def test_yapistirilan_metin_ve_eski_metin_temizlenir(self):
        from readings.models import UserText
        user = User.objects.create_user(username="temiz", password="Sifre1234")
        self.client.force_login(user)
        tekrar = "\n\n".join(f"Animal Farm\n\nThe pigs talked for a long time in part {i}." for i in range(4))
        with self.settings(CACHES=BELLEK):
            self.client.post(reverse("readings_add"), {"tur": "yapistir", "metin": tekrar + "\n\nhttps://x.com/y"})
        metin = UserText.objects.get(owner=user)
        self.assertNotIn("Animal Farm", metin.body)
        self.assertNotIn("https", metin.body)
        # Eski (temizlenmeden kaydedilmiş) metin okurken temizlenir.
        metin.body = tekrar
        metin.save()
        html = self.client.get(reverse("readings_user_text", args=[metin.pk])).content.decode()
        self.assertNotIn("Animal Farm</p>", html)
        self.assertIn("The pigs talked", html)


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
            with self.assertRaisesMessage(pdf_okuyucu.PdfOkunamadi, "50 MB"):
                pdf_okuyucu.pdf_metni(pdf_uret(["some text"]))

    def test_her_sayfadaki_kitap_ve_yazar_adi_atilir(self):
        govde = "Old Major was a prize Middle White boar who had a dream the night before."
        sayfalar = [f"ANIMAL FARM {i}\n\n{govde} Page {i} of the story goes on.\n\nGeorge Orwell"
                    for i in range(1, 6)]
        metin, _ = pdf_okuyucu.pdf_metni(pdf_uret(sayfalar))
        self.assertNotIn("ANIMAL FARM", metin)
        self.assertNotIn("George Orwell", metin)
        self.assertEqual(metin.count("Old Major"), 5)

    def test_baglantilar_atilir(self):
        metin, _ = pdf_okuyucu.pdf_metni(pdf_uret([
            "The farm was quiet (see https://example.com/animal-farm) that night.\n\n"
            "Free eBooks at www.planetebook.com"]))
        self.assertIn("The farm was quiet that night.", metin)
        self.assertNotIn("http", metin)
        self.assertNotIn("planetebook", metin)

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


class BuyukHarfTests(TestCase):
    """Rapor 18.16: sözlükte büyük harfle duran kelime metinde küçük yazılsa da bulunur."""

    def test_harf_duyarsiz(self):
        from readings.kelime_sorgu import sorgula
        from words.testing import make_word
        make_word("Arabic", meaning="Arapça", level="A2")
        for yazim in ("arabic", "Arabic", "ARABIC"):
            sonuc = sorgula(yazim)
            self.assertTrue(sonuc["bulundu"], yazim)
            self.assertEqual(sonuc["kok"], "Arabic")
