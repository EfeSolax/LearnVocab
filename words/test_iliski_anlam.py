"""
D1 — eş, zıt ve basit anlamlılar ANLAMA bağlı (WordRelation.meaning).

Rapor 4.3: "bank" için "shore" yalnızca "nehir kıyısı" anlamının altında
görünür. Bu dosya modeli, eşlemeyi, yükleyiciyi (bag_tamamla) ve geri
doldurma komutunu (iliskileri_anlama_bagla) sınar.
"""

import shutil
import tempfile
from io import StringIO

from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase

from words.aile import anlam as A
from words.aile.depo import Depo
from words.models import Meaning, WordRelation
from words.testing import make_word


def _anlam(meaning_tr, bags=(), definition="def"):
    """Depodaki cevap biçiminde bir anlam: bags = [(hedef, tür), …]."""
    return {"meaning_tr": meaning_tr, "definition": definition,
            "relations": [{"to_word": h, "type": t} for h, t in bags]}


def _kayit(word, pos, anlamlar, durum="yazildi"):
    return {"word": word, "type": pos, "durum": durum,
            "cevap": {"found": True, "word": word, "type": pos, "meanings": anlamlar}}


class BankOrnegi:
    """bank: 1. banka  2. nehir kıyısı. shore yalnızca ikincisinde."""

    def kur(self):
        self.bank = make_word("bank", meaning="banka", definition="a place for money",
                              extra_meanings=[("nehir kıyısı", "land beside a river")])
        self.banka, self.kiyi = list(self.bank.meanings.order_by("sort_order"))
        self.shore = make_word("shore", meaning="kıyı")
        self.lender = make_word("lender", meaning="borç veren")
        self.cevap = [_anlam("banka", [("lender", "synonym")], "a place for money"),
                      _anlam("nehir kıyısı", [("shore", "synonym")], "land beside a river")]


class ModelTests(BankOrnegi, TestCase):

    def setUp(self):
        self.kur()

    def test_bank_shore_yalnizca_nehir_kiyisi_anlaminda(self):
        WordRelation.objects.create(from_word=self.bank, to_word=self.shore,
                                    type="synonym", meaning=self.kiyi)
        self.assertEqual([b.to_word for b in self.kiyi.synonyms], [self.shore])
        self.assertFalse(self.banka.synonyms.exists())
        self.assertEqual(self.banka.iliski_satirlari(), [])

    def test_ayni_bag_farkli_anlamlarda_ayri_satir(self):
        for m in (self.banka, self.kiyi):
            WordRelation.objects.create(from_word=self.bank, to_word=self.shore,
                                        type="synonym", meaning=m)
        self.assertEqual(WordRelation.objects.count(), 2)
        # Kelime düzeyindeki görünüm hedefi bir kez gösterir.
        self.assertEqual([b.to_word for b in self.bank.synonyms], [self.shore])

    def test_ayni_anlamda_ayni_bag_iki_kez_yazilamaz(self):
        WordRelation.objects.create(from_word=self.bank, to_word=self.shore,
                                    type="synonym", meaning=self.kiyi)
        with self.assertRaises(IntegrityError), transaction.atomic():
            WordRelation.objects.create(from_word=self.bank, to_word=self.shore,
                                        type="synonym", meaning=self.kiyi)

    def test_anlamsiz_bag_de_iki_kez_yazilamaz(self):
        WordRelation.objects.create(from_word=self.bank, to_word=self.shore, type="synonym")
        with self.assertRaises(IntegrityError), transaction.atomic():
            WordRelation.objects.create(from_word=self.bank, to_word=self.shore, type="synonym")

    def test_anlam_silinince_baglari_da_gider(self):
        WordRelation.objects.create(from_word=self.bank, to_word=self.shore,
                                    type="synonym", meaning=self.kiyi)
        self.kiyi.delete()
        self.assertFalse(WordRelation.objects.exists())

    def test_iliski_satirlari_sirali_bos_satirsiz_ve_sinirli(self):
        for i in range(6):
            hedef = make_word(f"syn{i}", meaning=f"eş {i}")
            WordRelation.objects.create(from_word=self.bank, to_word=hedef,
                                        type="synonym", meaning=self.kiyi)
        WordRelation.objects.create(from_word=self.bank, to_word=self.lender,
                                    type="antonym", meaning=self.kiyi)
        m = Meaning.objects.prefetch_related("relations__to_word").get(pk=self.kiyi.pk)
        with self.assertNumQueries(0):
            satirlar = m.iliski_satirlari()
        self.assertEqual([etiket for etiket, _ in satirlar], ["Benzer", "Zıt"])
        self.assertEqual([w.text for w in satirlar[0][1]], ["syn0", "syn1", "syn2", "syn3"])
        self.assertEqual(len(m.iliski_satirlari(en_cok=3)[0][1]), 3)

    def test_karistirilan_anlam_satirlarina_girmez(self):
        WordRelation.objects.create(from_word=self.bank, to_word=self.shore,
                                    type="confused_with", meaning=self.kiyi)
        self.assertEqual(self.kiyi.iliski_satirlari(), [])


class EslemeTests(BankOrnegi, TestCase):

    def setUp(self):
        self.kur()

    def test_meaning_tr_ile_eslenir_sira_onemsiz(self):
        ters = list(reversed(self.cevap))
        self.assertEqual(A.anlam_eslemesi([self.banka, self.kiyi], ters),
                         [self.kiyi, self.banka])

    def test_buyuk_harf_ve_i_noktasi_eslesmeyi_bozmaz(self):
        self.kiyi.meaning_tr = "nehir kiyisi"
        self.kiyi.save()
        cevap = [_anlam("Nehir Kiyisi", definition="x")]
        self.assertEqual(A.anlam_eslemesi([self.banka, self.kiyi], cevap), [self.kiyi])
        cevap = [_anlam("i̇ade", definition="x")]
        iade = Meaning.objects.create(word=self.bank, meaning_tr="iade", sort_order=5)
        self.assertEqual(A.anlam_eslemesi([iade], cevap), [iade])

    def test_karsiligi_duzeltilen_anlam_aciklamadan_bulunur(self):
        self.kiyi.meaning_tr = "kıyı, sahil"      # elle düzeltildi
        self.kiyi.save()
        self.assertEqual(A.anlam_eslemesi([self.banka, self.kiyi], self.cevap),
                         [self.banka, self.kiyi])

    def test_silinen_anlam_none_doner(self):
        self.kiyi.delete()
        self.assertEqual(A.anlam_eslemesi([self.banka], self.cevap), [self.banka, None])


class BagTamamlaTests(BankOrnegi, TestCase):
    """Yükleyici artık bağları doğrudan anlama bağlayarak yazıyor."""

    def setUp(self):
        self.kur()

    def test_baglar_anlama_baglanir(self):
        sonuc = A.bag_tamamla([_kayit("bank", "noun", self.cevap)])
        self.assertEqual(sonuc["kurulan"], 2)
        self.assertEqual(WordRelation.objects.get(to_word=self.shore).meaning, self.kiyi)
        self.assertEqual(WordRelation.objects.get(to_word=self.lender).meaning, self.banka)
        # Tekrar çalıştırmak bir şey eklemez.
        self.assertEqual(A.bag_tamamla([_kayit("bank", "noun", self.cevap)])["kurulan"], 0)
        self.assertEqual(WordRelation.objects.count(), 2)

    def test_eski_bos_satir_yeniden_acilmaz_anlama_verilir(self):
        WordRelation.objects.create(from_word=self.bank, to_word=self.shore, type="synonym")
        A.bag_tamamla([_kayit("bank", "noun", self.cevap)])
        self.assertEqual(WordRelation.objects.filter(to_word=self.shore).count(), 1)
        self.assertEqual(WordRelation.objects.get(to_word=self.shore).meaning, self.kiyi)

    def test_silinen_anlamin_bagi_kurulmaz(self):
        self.kiyi.delete()
        sonuc = A.bag_tamamla([_kayit("bank", "noun", self.cevap)])
        self.assertEqual(sonuc["anlamsiz"], 1)
        self.assertFalse(WordRelation.objects.filter(to_word=self.shore).exists())

    def test_hedef_yoksa_bekler(self):
        cevap = [_anlam("banka", [("financier", "synonym")], "a place for money")]
        self.assertEqual(A.bag_tamamla([_kayit("bank", "noun", cevap)])["bekleyen"], 1)


class KomutTests(BankOrnegi, TestCase):
    """manage.py iliskileri_anlama_bagla — D1 geri doldurma."""

    def setUp(self):
        self.kur()
        self.klasor = tempfile.mkdtemp()
        depo = Depo(self.klasor)

        # aim: 1. amaç  2. nişan. goal ikisinde de geçiyor -> çoğaltılır.
        self.aim = make_word("aim", meaning="amaç", definition="purpose",
                             extra_meanings=[("nişan", "pointing a weapon")])
        self.amac, self.nisan = list(self.aim.meanings.order_by("sort_order"))
        self.goal = make_word("goal", meaning="hedef")
        self.target = make_word("target", meaning="hedef tahtası")
        depo.anlam_ekle(_kayit("aim", "noun", [
            _anlam("amaç", [("goal", "synonym")], "purpose"),
            _anlam("nişan", [("goal", "synonym"), ("target", "synonym")], "pointing a weapon"),
        ]))
        # bank: cevapta ayrıca silinmiş bir üçüncü anlam (bağı: lender, antonym)
        depo.anlam_ekle(_kayit("bank", "noun", self.cevap + [
            _anlam("silinmiş anlam", [("lender", "antonym")], "gone")]))
        # reddedilen kayıt dikkate alınmaz
        depo.anlam_ekle(_kayit("shore", "noun", [_anlam("kıyı", [("bank", "antonym")])],
                               durum="reddedildi"))

        # D1 öncesi hâl: bütün bağlar kelime düzeyinde (meaning boş).
        for kaynak, hedef, tur in (
                (self.bank, self.shore, "synonym"), (self.bank, self.lender, "synonym"),
                (self.bank, self.lender, "antonym"),                 # silinmiş anlamdan
                (self.aim, self.goal, "synonym"), (self.aim, self.target, "synonym"),
                (self.aim, self.lender, "simpler"),                  # depoda yok, çok anlamlı
                (self.shore, self.bank, "antonym"),                  # depoda yok, tek anlamlı
                (self.bank, self.shore, "confused_with")):
            WordRelation.objects.create(from_word=kaynak, to_word=hedef, type=tur)

    def tearDown(self):
        shutil.rmtree(self.klasor, ignore_errors=True)

    def calistir(self, **secenekler):
        cikti = StringIO()
        call_command("iliskileri_anlama_bagla", depo=self.klasor, stdout=cikti, **secenekler)
        return cikti.getvalue()

    def _anlam(self, kaynak, hedef, tur):
        return sorted(WordRelation.objects.filter(from_word=kaynak, to_word=hedef, type=tur)
                      .values_list("meaning__meaning_tr", flat=True), key=str)

    def test_dry_run_yazmaz(self):
        cikti = self.calistir(dry_run=True)
        self.assertIn("KURU ÇALIŞTIRMA", cikti)
        self.assertFalse(WordRelation.objects.filter(meaning__isnull=False).exists())
        self.assertEqual(WordRelation.objects.count(), 8)

    def test_bank_shore_yalnizca_nehir_kiyisina(self):
        self.calistir()
        self.assertEqual(self._anlam(self.bank, self.shore, "synonym"), ["nehir kıyısı"])
        self.assertEqual(self._anlam(self.bank, self.lender, "synonym"), ["banka"])
        self.assertEqual([b.to_word for b in self.kiyi.synonyms], [self.shore])
        self.assertEqual([b.to_word for b in self.banka.synonyms], [self.lender])

    def test_birden_cok_anlamda_gecen_bag_cogaltilir(self):
        cikti = self.calistir()
        self.assertEqual(self._anlam(self.aim, self.goal, "synonym"), ["amaç", "nişan"])
        self.assertEqual(self._anlam(self.aim, self.target, "synonym"), ["nişan"])
        self.assertIn("Çoğaltılan (yeni satır): 1", cikti)

    def test_eslesmeyenler_bos_kalir_ve_raporlanir(self):
        cikti = self.calistir()
        # silinmiş anlamdan gelen bağ başka anlama yapışmaz
        self.assertEqual(self._anlam(self.bank, self.lender, "antonym"), [None])
        # depoda olmayan çok anlamlı kelimenin bağı
        self.assertEqual(self._anlam(self.aim, self.lender, "simpler"), [None])
        self.assertIn("Eşleşmeyen (boş kaldı):  2", cikti)

    def test_tek_anlamli_kelimede_atama_otomatik(self):
        self.calistir()
        self.assertEqual(self._anlam(self.shore, self.bank, "antonym"), ["kıyı"])

    def test_karistirilan_kelime_duzeyinde_kalir(self):
        self.calistir()
        self.assertEqual(self._anlam(self.bank, self.shore, "confused_with"), [None])

    def test_ikinci_calistirma_bir_sey_degistirmez(self):
        self.calistir()
        once = sorted(WordRelation.objects.values_list(
            "from_word_id", "to_word_id", "type", "meaning_id"), key=str)
        cikti = self.calistir()
        sonra = sorted(WordRelation.objects.values_list(
            "from_word_id", "to_word_id", "type", "meaning_id"), key=str)
        self.assertEqual(once, sonra)
        self.assertIn("Anlama atanan:           0", cikti)
        self.assertIn("Çoğaltılan (yeni satır): 0", cikti)

    def test_kelime_secenegi_yalnizca_o_kelimeye_dokunur(self):
        self.calistir(kelime="aim")
        self.assertEqual(self._anlam(self.aim, self.goal, "synonym"), ["amaç", "nişan"])
        self.assertEqual(self._anlam(self.bank, self.shore, "synonym"), [None])
