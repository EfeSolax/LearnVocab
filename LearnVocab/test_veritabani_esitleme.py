"""manage.py veritabani indir / yukle (LearnVocab/veritabani_esitleme.py)."""

import os
import tempfile
from io import StringIO

from django.core.management import call_command
from django.test import TransactionTestCase

from LearnVocab import veritabani_esitleme as ve
from users.models import User
from words.models import ExampleSentence, Meaning, UserWordLink, Word
from words.testing import make_word

class SiniflandirmaTests(TransactionTestCase):
    def test_her_tablo_icerik_ya_da_kullanici(self):
        self.assertEqual(ve.siniflandirilmamis(), [])
        self.assertFalse(ve.ICERIK & ve.KULLANICI)


class EsitlemeTests(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Araç dosya için geçici bağlantılar açar; Django'nun test yalıtımı izin listesine çalışma
        # anında baktığı için kurulumdan SONRA eklenir (test veritabanı kurulmaz, paralel işçiler etkilenmez).
        cls.databases = set(cls.databases) | {ve.DOSYA, "dosya_yedek"}

    def setUp(self):
        self.klasor = tempfile.TemporaryDirectory()
        self.dosya = os.path.join(self.klasor.name, "canli.sqlite3")
        self.user = User.objects.create_user(username="ogrenci", password="Sifre1234")
        self.kedi = make_word("cat", meaning="kedi", level="A1")
        self.kopek = make_word("dog", meaning="köpek", level="A1")
        UserWordLink.objects.create(user=self.user, word=self.kopek)
        ve.indir(self.dosya, rapor=lambda *_: None)

    def tearDown(self):
        self.klasor.cleanup()

    def _dosyada(self, islem):
        with ve.dosya_veritabani(self.dosya):
            islem()

    def _yukle(self, **ek):
        return ve.yukle(self.dosya, rapor=lambda *_: None,
                        yedek_klasoru=os.path.join(self.klasor.name, "yedek"), **ek)

    def test_indir_tam_kopya_ve_kunye(self):
        def kontrol():
            self.assertEqual(Word.objects.using(ve.DOSYA).count(), Word.objects.count())
            self.assertTrue(User.objects.using(ve.DOSYA).filter(username="ogrenci").exists())
            self.assertIn("words_word", ve._kunye_oku(ve.DOSYA)["parmak_izleri"])
        self._dosyada(kontrol)
        with self.assertRaises(ve.EsitlemeHatasi):              # var olan dosyanın üstüne yazmaz
            ve.indir(self.dosya, rapor=lambda *_: None)

    def test_yukle_icerigi_yazar_kullanici_verisini_korur(self):
        anlam = self.kedi.meanings.first()

        def duzenle():
            m = Meaning.objects.using(ve.DOSYA).get(pk=anlam.pk)
            m.meaning_tr = "kedi, pisi"
            m.save(using=ve.DOSYA)
            ExampleSentence.objects.using(ve.DOSYA).create(meaning=m, text="The cat sleeps.", sort_order=9)
            Word.objects.using(ve.DOSYA).filter(pk=self.kopek.pk).delete()
        self._dosyada(duzenle)
        # indirmeden sonra canlıda kullanıcı etkinliği: listesine kedi ekliyor
        UserWordLink.objects.create(user=self.user, word=self.kedi)

        kuru = self._yukle()                                     # kuru deneme: hiçbir şey değişmez
        self.assertEqual(kuru["ozet"]["words_meaning"][1], 1)
        self.assertEqual(Meaning.objects.get(pk=anlam.pk).meaning_tr, "kedi")
        self.assertTrue(Word.objects.filter(pk=self.kopek.pk).exists())

        sonuc = self._yukle(uygula=True)
        self.assertEqual(Meaning.objects.get(pk=anlam.pk).meaning_tr, "kedi, pisi")
        self.assertTrue(ExampleSentence.objects.filter(text="The cat sleeps.").exists())
        self.assertFalse(Word.objects.filter(pk=self.kopek.pk).exists())
        self.assertEqual(sonuc["etkiler"].get("words.UserWordLink"), 1)        # köpek listeden düştü
        self.assertEqual(list(UserWordLink.objects.values_list("word_id", flat=True)), [self.kedi.pk])
        self.assertEqual(len(os.listdir(os.path.join(self.klasor.name, "yedek"))), 1)
        # aynı dosya yeniden yüklenebilir (künye güncellendi), fark yok
        tekrar = self._yukle()
        self.assertFalse(any(e or g or s for e, g, s in tekrar["ozet"].values()))

    def test_canlida_degisen_icerik_varsa_durur(self):
        def duzenle():
            Meaning.objects.using(ve.DOSYA).filter(pk=self.kedi.meanings.first().pk).update(meaning_tr="pisi")
        self._dosyada(duzenle)
        Meaning.objects.filter(pk=self.kopek.meanings.first().pk).update(meaning_tr="it")   # canlıda başka düzenleme
        with self.assertRaises(ve.EsitlemeHatasi):
            self._yukle()
        self._yukle(zorla=True, uygula=True)
        self.assertEqual(self.kopek.meanings.first().meaning_tr, "köpek")    # dosyadaki kazandı

    def test_hepsi_butun_tablolari_dosyadakiyle_degistirir(self):
        User.objects.create_user(username="sonradan", password="Sifre1234")
        call_command("veritabani", "yukle", self.dosya, "--hepsi", "--uygula", "--evet",
                     "--yedek-klasoru", os.path.join(self.klasor.name, "yedek"), stdout=StringIO())
        self.assertFalse(User.objects.filter(username="sonradan").exists())
        self.assertTrue(UserWordLink.objects.filter(word=self.kopek).exists())

    def test_komut_kuru_deneme_raporu(self):
        cikti = StringIO()
        call_command("veritabani", "yukle", self.dosya, stdout=cikti)
        self.assertIn("KURU DENEME", cikti.getvalue())
