"""Ağır işler (rapor 18.37): eşzamanlı iş sınırı, takılan iş, PDF sınırı, cron kilidi."""
import time
from io import StringIO
from unittest.mock import patch

from django.core.cache import caches
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from LearnVocab import progress, sinir
from texts import degerlendirme as dg
from texts.models import Text, YaziDurumu
from texts.tests import METIN
from users.models import User

SINIRLI = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "a"},
           "sinir": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "b"}}


@override_settings(CACHES=SINIRLI)
class SinirYardimcilariTests(TestCase):
    def setUp(self):
        caches["sinir"].clear()

    def test_pencere_her_istekte_uzamaz(self):
        with patch("LearnVocab.sinir.time.time", return_value=1000.0):
            sinir.say("x", 60)
        with patch("LearnVocab.sinir.time.time", return_value=1050.0):
            self.assertEqual(sinir.say("x", 60), 2)
        with patch("LearnVocab.sinir.time.time", return_value=1061.0):
            self.assertEqual(sinir.oku("x"), 0)
            self.assertEqual(sinir.say("x", 60), 1)   # yeni pencere

    def test_yer_sinirli_ve_birakilinca_bosalir(self):
        a = sinir.yer_al("is", 2, 60)
        b = sinir.yer_al("is", 2, 60)
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        self.assertIsNone(sinir.yer_al("is", 2, 60))
        sinir.yer_birak("is", a)
        self.assertIsNotNone(sinir.yer_al("is", 2, 60))

    def test_suresi_gecen_yer_sayilmaz(self):
        sinir.yer_al("is", 1, 60)
        with patch("LearnVocab.sinir.time.time", return_value=time.time() + 61):
            self.assertIsNotNone(sinir.yer_al("is", 1, 60))


@override_settings(CACHES=SINIRLI, TEXT_DAILY_LIMIT=0, YAZMA_DAKIKADA_EN_COK=0,
                   GEMINI_MIN_SECONDS_BETWEEN_REQUESTS=0)
class DegerlendirmeYukuTests(TestCase):
    def setUp(self):
        caches["sinir"].clear()
        caches["default"].clear()
        self.user = User.objects.create_user(username="yazar", password="Sifre1234")
        self.client.login(username="yazar", password="Sifre1234")

    def _ajax_gonder(self):
        return self.client.post(reverse("create_text"), {"user_text": METIN},
                                HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    def test_yer_yoksa_yogun_der_metin_kalir(self):
        with patch("texts.views.ESZAMANLI_DEGERLENDIRME", 0), \
                patch("texts.views.threading.Thread") as thread:
            job_id = self._ajax_gonder().json()["job_id"]
        thread.assert_not_called()
        self.assertEqual(progress.read(job_id)["state"], progress.STATE_DONE)
        self.assertEqual(Text.objects.get().durum, YaziDurumu.BEKLIYOR)
        bitis = self.client.post(reverse("create_text_finish", args=[job_id]))
        self.assertEqual(bitis.json()["redirect"], reverse("review_text", args=[Text.objects.get().pk]))

    def test_sesi_kesilen_is_takili_kalmaz(self):
        with patch("texts.views.threading.Thread"):
            job_id = self._ajax_gonder().json()["job_id"]
        self.assertEqual(self.client.get(reverse("create_text_progress", args=[job_id])).json()["state"],
                         progress.STATE_RUNNING)
        with patch("texts.views.time.time", return_value=time.time() + 181):
            durum = self.client.get(reverse("create_text_progress", args=[job_id])).json()
        self.assertEqual(durum["state"], progress.STATE_DONE)
        bitis = self.client.post(reverse("create_text_finish", args=[job_id]))
        self.assertEqual(bitis.json()["redirect"], reverse("review_text", args=[Text.objects.get().pk]))

    def test_kullanici_beklerken_uyunmaz(self):
        yazi = Text.objects.create(owner=self.user, content=METIN)
        with patch("LearnVocab.gemini.generate", side_effect=Exception("x")) as uret:
            dg.degerlendir(yazi)
        self.assertIs(uret.call_args.kwargs["bekle"], False)

    def test_cron_onceki_calisma_surerken_atlar(self):
        Text.objects.create(owner=self.user, content=METIN)
        sinir.yer_al("cron-yazilar", 1, 600)
        cikti = StringIO()
        with patch("LearnVocab.gemini.generate") as uret:
            call_command("yazilari_yeniden_dene", stdout=cikti)
        uret.assert_not_called()
        self.assertIn("atlandı", cikti.getvalue())


@override_settings(CACHES=SINIRLI)
class PdfYukuTests(TestCase):
    def setUp(self):
        caches["sinir"].clear()
        self.user = User.objects.create_user(username="okur", password="Sifre1234")
        self.client.login(username="okur", password="Sifre1234")

    def _yukle(self):
        dosya = SimpleUploadedFile("deneme.pdf", b"%PDF-1.4 deneme", content_type="application/pdf")
        return self.client.post(reverse("readings_add"), {"tur": "pdf", "dosya": dosya})

    def test_saatlik_pdf_siniri_ve_esszamanli_yer(self):
        okunan = ("Scholars read the text carefully. " * 5, {"sayfa": 1, "baslik": "", "kesildi": False})
        with patch("readings.views.pdf_okuyucu.pdf_metni", return_value=okunan), \
                patch("readings.views.PDF_SAATTE", 1):
            self.assertEqual(self._yukle().status_code, 302)
            self.assertEqual(self._yukle().status_code, 400)       # saatlik sınır
        caches["sinir"].clear()
        with patch("readings.views.pdf_okuyucu.pdf_metni", return_value=okunan), \
                patch("readings.views.ESZAMANLI_PDF", 0):
            self.assertEqual(self._yukle().status_code, 400)       # yer yok
        self.assertEqual(sinir._yerler("yer:pdf"), {})              # yer geri bırakıldı
