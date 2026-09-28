"""Metin dışa aktarma: yeni Yazma kayıtları (rapor 9.1) doğru alanlarla yazılır."""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from texts.models import Text, YaziDurumu
from users.models import User

SIFRE = "Sifre1234"


class MetinDisaAktarmaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="yazar", password=SIFRE)
        self.client.login(username="yazar", password=SIFRE)

    def _indir(self, ad="export_mytexts"):
        cevap = self.client.get(reverse(ad))
        self.assertEqual(cevap.status_code, 200)
        return cevap.content.decode("utf-8")

    def test_yeni_kayit_puan_ve_iki_liste(self):
        Text.objects.create(
            owner=self.user, content="He go to school.", konu="Okul", durum=YaziDurumu.TAMAM,
            puan=3.5, geri_bildirim={
                "iyi": [{"alinti": "to school", "aciklama": "Edat doğru."}],
                "hatalar": [{"alinti": "he go", "dogrusu": "he goes", "neden": "Tekil öznede -s."}],
            })
        metin = self._indir()
        self.assertIn("Puanınız: 3,5 / 5", metin)
        self.assertNotIn("Puanınız: 0", metin)
        self.assertIn("Konu: Okul", metin)
        self.assertIn("Edat doğru.", metin)
        self.assertIn("he go → he goes · Tekil öznede -s.", metin)
        self.assertNotIn("Kriter Puanları", metin)

    def test_bekleyen_kayit_durumu_yazar(self):
        Text.objects.create(owner=self.user, content="Beklemede.", durum=YaziDurumu.BEKLIYOR)
        metin = self._indir()
        self.assertIn("Durum: Henüz değerlendirilmedi", metin)
        self.assertNotIn("Puanınız", metin)

    def test_eski_kayit_eski_alanlarla(self):
        Text.objects.create(owner=self.user, content="Eski.", durum=YaziDurumu.ESKI,
                            score=72, scores="7,8", response="Eski cevap")
        metin = self._indir()
        self.assertIn("Puanınız: 72 / 100", metin)
        self.assertIn("Eski cevap", metin)

    def test_silinen_metin_aktarilmaz(self):
        Text.objects.create(owner=self.user, content="Silinmiş metin", silindi=timezone.now())
        self.assertNotIn("Silinmiş metin", self._indir())

    def test_tum_verilerde_de_ayni_bicim(self):
        Text.objects.create(owner=self.user, content="Yeni.", durum=YaziDurumu.TAMAM, puan=4.0,
                            geri_bildirim={"iyi": [], "hatalar": []})
        metin = self._indir("export_all")
        self.assertIn("Puanınız: 4 / 5", metin)
        self.assertIn("Hata bulunmadı.", metin)
