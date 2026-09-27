"""
Kelime çıkarma hattının testleri.

Odak "kod çalışıyor mu" değil, "süzgeç doğru şeyi mi eliyor". Bu hattın
hataları sessiz: yanlış elenen bir kelime hata vermez, sadece
veritabanında hiç görünmez ve kimse yokluğunu fark etmez.
"""

import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from words.extract import function_words, phrasal, pipeline
from words.extract.lemmatize import lemma
from words.models import PartOfSpeech, Word, WordFamily


def metin_yaz(klasor, ad, icerik):
    yol = Path(klasor) / ad
    yol.write_text(icerik, encoding="utf-8")
    return yol


class LemmaTests(TestCase):
    """Kök bulma. Yanlış kök = veritabanında yanlış madde."""

    def test_duzenli_cekimler(self):
        for yazim, beklenen in [
            ("studies", "study"), ("studied", "study"),
            ("running", "run"), ("stopped", "stop"),
            ("making", "make"), ("carries", "carry"),
            ("denied", "deny"), ("occurred", "occur"),
            ("happier", "happy"), ("biggest", "big"),
            ("businesses", "business"),
        ]:
            self.assertEqual(lemma(yazim), beklenen, yazim)

    def test_duzensiz_bicimler(self):
        for yazim, beklenen in [
            ("went", "go"), ("children", "child"), ("leaves", "leaf"),
            ("better", "good"), ("criteria", "criterion"),
            ("phenomena", "phenomenon"), ("indices", "index"),
            ("analyses", "analysis"), ("crises", "crisis"),
            ("stimuli", "stimulus"), ("matrices", "matrix"),
        ]:
            self.assertEqual(lemma(yazim), beklenen, yazim)

    def test_cekimli_bicim_kokten_sik_olsa_da_koke_iner(self):
        """
        `analysed` web metninde `analyse`den daha sık geçiyor. İlk
        sürümde aday kelimenin KENDİ sıklığıyla yarıştırılıyordu ve bu
        kelimeler hiç köke inmiyordu.
        """
        self.assertEqual(lemma("analysed"), "analyse")
        self.assertEqual(lemma("sustained"), "sustain")

    def test_parcalar_kok_sayilmaz(self):
        """
        Sıklık verisi web metninden geldiği için `analys`, `runn`, `mak`
        gibi PARÇALARIN da sıfırdan büyük bir sıklığı var. "İlk geçerli
        adayı al" yaklaşımı bu yüzden yanlıştı.
        """
        for yazim in ("analysing", "running", "making", "biggest"):
            self.assertNotIn(lemma(yazim), {"analys", "runn", "mak", "bigg"})

    def test_s_ile_biten_tekiller_korunur(self):
        for yazim in ("analysis", "basis", "crisis", "focus", "news",
                      "species", "process", "business", "various"):
            self.assertEqual(lemma(yazim), yazim, yazim)

    def test_turetme_geri_alinmaz(self):
        """
        Çekim geri alınır, TÜRETME alınmaz: `encouragement` kendi sözlük
        maddesidir (words/models.py açılış yorumu). Aileyi kurmak
        zenginleştirme hattının işi.
        """
        for yazim in ("encouragement", "considerable", "interpretation",
                      "psychological"):
            self.assertEqual(lemma(yazim), yazim, yazim)

    def test_data_ve_media_bozulmaz(self):
        self.assertEqual(lemma("data"), "data")
        self.assertEqual(lemma("media"), "media")


class IslevKelimeleriTests(TestCase):

    def test_edat_ve_baglaclar_yakalanir(self):
        for kelime in ("of", "through", "whereas", "notwithstanding",
                       "however", "therefore", "out", "upon"):
            self.assertTrue(function_words.islev_kelimesi_mi(kelime), kelime)

    def test_ogrenilecek_kelimeler_islev_sayilmaz(self):
        for kelime in ("analysis", "sustain", "resilient", "bias"):
            self.assertFalse(function_words.islev_kelimesi_mi(kelime), kelime)

    def test_seyrek_baglaclar_da_listede(self):
        """
        `albeit`, `notwithstanding` sıklık listesinde geride kalır; eşiğe
        bırakılsalardı "öğrenilmeye değer kelime" sayılıp geçerlerdi.
        Elle yazılmalarının sebebi bu.
        """
        for kelime in ("albeit", "notwithstanding", "thereby", "whereby"):
            self.assertTrue(function_words.islev_kelimesi_mi(kelime), kelime)


class PhrasalTests(TestCase):

    def test_kuratorlu_liste_yakalanir(self):
        tokenler = "the study will carry out a survey and point out errors".split()
        bulunan, _ = phrasal.bul(tokenler, lemma)
        self.assertIn("carry out", bulunan)
        self.assertIn("point out", bulunan)

    def test_araya_kelime_girse_de_yakalanir(self):
        tokenler = "researchers carried it out carefully".split()
        bulunan, _ = phrasal.bul(tokenler, lemma)
        self.assertIn("carry out", bulunan)

    def test_listede_olmayanlar_aday_kalir(self):
        """Kural her zaman yanılır; aday listesi bir KARAR listesidir."""
        tokenler = "they increase in number".split()
        bulunan, adaylar = phrasal.bul(tokenler, lemma)
        self.assertEqual(bulunan, {})
        self.assertIn("increase in", adaylar)

    def test_yardimci_fiiller_aday_uretmez(self):
        tokenler = "the results are in the appendix".split()
        _, adaylar = phrasal.bul(tokenler, lemma)
        self.assertNotIn("be in", adaylar)


class PipelineTests(TestCase):

    def setUp(self):
        self.klasor = tempfile.mkdtemp()

    def _calistir(self, icerik, **secenekler):
        metin_yaz(self.klasor, "metin.txt", icerik)
        yollar = list(Path(self.klasor).glob("*.txt"))
        return pipeline.calistir(yollar, **secenekler)

    def _kelimeler(self, sonuc):
        return {k["word"] for k in sonuc["words"]}

    def test_sik_kelimeler_elenir(self):
        sonuc = self._calistir(
            "The people said that the important thing was different."
        )
        for kelime in ("people", "important", "different", "thing"):
            self.assertNotIn(kelime, self._kelimeler(sonuc), kelime)

    def test_islev_kelimeleri_elenir(self):
        sonuc = self._calistir(
            "Whereas the findings were notwithstanding the evidence, "
            "the researchers thereby concluded."
        )
        for kelime in ("whereas", "notwithstanding", "thereby"):
            self.assertNotIn(kelime, self._kelimeler(sonuc), kelime)

    def test_ogrenilecek_kelimeler_kalir(self):
        sonuc = self._calistir(
            "The ubiquitous bias undermines the resilient consensus. "
            "Researchers sustained the ubiquitous bias."
        )
        kalanlar = self._kelimeler(sonuc)
        for kelime in ("ubiquitous", "bias", "resilient", "consensus"):
            self.assertIn(kelime, kalanlar, kelime)

    def test_cekimli_bicimler_tek_satirda_toplanir(self):
        """
        Dört yazım bir satır olmalı. Olmazsa zenginleştirme hattı dördünü
        de üretir ve dört ayrı aile kurulur — §7'deki sessiz bozulmanın
        girişte tekrarı.
        """
        sonuc = self._calistir(
            "They analysed it. She is analysing it. "
            "He analyses it. The analysed data analysed again."
        )
        kayitlar = [k for k in sonuc["words"] if k["word"] == "analyse"]
        self.assertEqual(len(kayitlar), 1)
        self.assertGreaterEqual(kayitlar[0]["count"], 4)

    def test_ozel_isimler_elenir(self):
        sonuc = self._calistir(
            "According to Freud, the unconscious matters. "
            "Freud wrote about Vienna and Freud lived in Vienna."
        )
        kalanlar = self._kelimeler(sonuc)
        self.assertNotIn("freud", kalanlar)
        self.assertNotIn("vienna", kalanlar)

    def test_cumle_basindaki_buyuk_harf_ozel_isim_sayilmaz(self):
        sonuc = self._calistir(
            "Resilient people cope well. The resilient mind resists. "
            "Resilient systems endure."
        )
        self.assertIn("resilient", self._kelimeler(sonuc))

    def test_asiri_teknik_elenir(self):
        sonuc = self._calistir(
            "The heteroscedasticity of qwertyuiopasdf was measured."
        )
        self.assertNotIn("qwertyuiopasdf", self._kelimeler(sonuc))

    def test_veritabanindakiler_atlanir(self):
        aile = WordFamily.objects.create(root="bias")
        Word.objects.create(family=aile, text="bias", pos=PartOfSpeech.NOUN)
        sonuc = self._calistir(
            "The bias was ubiquitous and the bias persisted.",
            mevcut_kelimeler={"bias"},
        )
        kalanlar = self._kelimeler(sonuc)
        self.assertNotIn("bias", kalanlar)
        self.assertIn("ubiquitous", kalanlar)

    def test_phrasal_verbler_elenmez(self):
        """
        `out` tek başına elenir ama `carry out` kalmalı: anlamı
        parçalarından çıkmayan bir sözlük maddesidir.
        """
        sonuc = self._calistir(
            "Researchers carry out studies. They carried out the survey "
            "and will carry out more."
        )
        ifadeler = {p["phrase"] for p in sonuc["phrasal"]}
        self.assertIn("carry out", ifadeler)
        self.assertNotIn("out", self._kelimeler(sonuc))

    def test_min_count_esigi(self):
        sonuc = self._calistir(
            "The ubiquitous ubiquitous ubiquitous bias appeared.",
            min_count=2,
        )
        kalanlar = self._kelimeler(sonuc)
        self.assertIn("ubiquitous", kalanlar)
        self.assertNotIn("bias", kalanlar)

    def test_eleme_sebepleri_raporlanir(self):
        """Süzgeç sessizce yanlış çalışırsa kimse fark etmez."""
        sonuc = self._calistir("The people whereas Freud analysed things.")
        sebepler = " ".join(sonuc["dropped"].keys())
        self.assertIn("işlev kelimesi", sebepler)
        self.assertIn("özel isim", sebepler)
        self.assertIn("en sık", sebepler)

    def test_tur_tahmini_temkinli(self):
        """
        Tek bir `-ing` fiil iddiası için yetmiyor: `fingerprinting`,
        `tutoring` isimden türemiş olabilir. Yanlış tür yazmak, tür
        yazmamaktan kötüdür.
        """
        sonuc = self._calistir(
            "The fingerprinting method was used. Fingerprint evidence "
            "matters. A fingerprint is unique."
        )
        kayit = next(k for k in sonuc["words"] if k["word"] == "fingerprint")
        self.assertNotEqual(kayit["pos"], "verb")

    def test_tur_tahmini_gercek_fiili_yakalar(self):
        sonuc = self._calistir(
            "They sustained the effort. She is sustaining it. "
            "We sustained the growth."
        )
        kayit = next(k for k in sonuc["words"] if k["word"] == "sustain")
        self.assertEqual(kayit["pos"], "verb")

    def test_isim_sonekli_kelime_fiil_sayilmaz(self):
        sonuc = self._calistir(
            "The mediation was useful. Mediation helps. Mediation matters "
            "and mediation continues."
        )
        kayit = next(k for k in sonuc["words"] if k["word"] == "mediation")
        self.assertEqual(kayit["pos"], "noun")


class KomutTests(TestCase):

    def setUp(self):
        self.klasor = tempfile.mkdtemp()
        metin_yaz(self.klasor, "a.txt",
                  "The ubiquitous bias undermines resilient consensus. "
                  "Researchers carry out studies and carried out surveys. "
                  "The ubiquitous bias persisted.")

    def test_komut_liste_uretir(self):
        cikti = Path(self.klasor) / "liste.txt"
        call_command("extract_words", dir=self.klasor, out=str(cikti))
        icerik = cikti.read_text(encoding="utf-8")
        self.assertIn("ubiquitous", icerik)
        self.assertIn("carry out:phrasal_verb", icerik)

    def test_kuru_calistirma_dosya_yazmaz(self):
        cikti = Path(self.klasor) / "yok.txt"
        call_command("extract_words", dir=self.klasor, out=str(cikti),
                     dry_run=True)
        self.assertFalse(cikti.exists())

    def test_rapor_yazilir(self):
        cikti = Path(self.klasor) / "liste.txt"
        rapor = Path(self.klasor) / "rapor.json"
        call_command("extract_words", dir=self.klasor, out=str(cikti),
                     report=str(rapor))
        import json
        veri = json.loads(rapor.read_text(encoding="utf-8"))
        self.assertIn("words", veri)
        self.assertIn("dropped", veri)
        self.assertIn("stats", veri)

    def test_cikti_aile_uret_bicimine_uygun(self):
        """
        Biçim sözleşmesi: her satırda bir kelime, `kelime:tur`,
        `#` ile başlayanlar ve boş satırlar atlanır (aile_uret böyle
        okuyor). Bozulursa iki komut sessizce uyumsuz hâle gelir.
        """
        cikti = Path(self.klasor) / "liste.txt"
        call_command("extract_words", dir=self.klasor, out=str(cikti))
        gecerli_turler = set(PartOfSpeech.values)
        for satir in cikti.read_text(encoding="utf-8").splitlines():
            satir = satir.strip()
            if not satir or satir.startswith("#"):
                continue
            if ":" in satir:
                kelime, tur = satir.split(":", 1)
                self.assertTrue(kelime.strip())
                self.assertIn(tur.strip(), gecerli_turler, satir)


# ---------------------------------------------------------------------------
# PDF (words/extract/pdf.py) — 24 Eylül
# ---------------------------------------------------------------------------

import unittest  # noqa: E402
import tempfile as _tempfile  # noqa: E402
from pathlib import Path as _Path  # noqa: E402
from django.test import SimpleTestCase as _SimpleTestCase  # noqa: E402

try:
    import pymupdf as _pymupdf
except ImportError:          # pragma: no cover
    _pymupdf = None


@unittest.skipIf(_pymupdf is None, "pymupdf kurulu değil")
class PdfMetniTests(_SimpleTestCase):

    def _pdf(self, sayfalar, bos=False):
        yol = _Path(_tempfile.mkdtemp()) / "deneme.pdf"
        belge = _pymupdf.open()
        for i, govde in enumerate(sayfalar, 1):
            sayfa = belge.new_page()
            if not bos:
                sayfa.insert_text((72, 40), "Journal of Applied Linguistics · Vol. 7", fontsize=9)
                sayfa.insert_text((72, 100), govde, fontsize=11)
                sayfa.insert_text((300, 800), str(i), fontsize=9)
        belge.save(str(yol))
        return yol

    def test_temizlik(self):
        from words.extract import pdf
        yol = self._pdf([
            "Researchers argue that sustainable environ-\nmental policy requires a well-\n"
            "known consensus among stakeholders.",
            "The empirical evidence remains ambiguous and contested.",
            "The findings corroborate earlier hypotheses.\n\nReferences\n"
            "Zbigniewski, K. (2020). Proceedings of Obscure Studies."])
        metin, bilgi = pdf.pdf_metni(yol)
        self.assertIn("environmental", metin)          # satır sonu tiresi birleşti
        self.assertIn("well-known", metin)             # gerçek tire korundu
        self.assertNotIn("Journal of Applied", metin)  # tekrar eden başlık
        self.assertNotIn("Zbigniewski", metin)         # kaynakça kesildi
        self.assertTrue(bilgi["kaynakca_kesildi"])

    def test_taranmis_pdf_hata_verir(self):
        from words.extract import pdf
        with self.assertRaises(pdf.PdfHatasi):
            pdf.pdf_metni(self._pdf(["", ""], bos=True))

    def test_pipeline_pdf_okur(self):
        from words.extract import pipeline
        yol = self._pdf(["Scholars scrutinize the ambiguous methodology carefully.",
                         "Another page.", "Third page."])
        okunanlar, hatalar = pipeline.metinleri_oku([yol])
        self.assertEqual(hatalar, [])
        self.assertIn("scrutinize", okunanlar[0][1])


class OzelIsimTests(_SimpleTestCase):
    """24 Eylül: cümle başındaki isimler kaçıyor, "university" atılıyordu."""

    METIN = ("Vygotsky argued that learning is social. In a later study, Dr. Hendricks and "
             "Maria Gonzalez examined how Bourdieu saw capital. Piaget emphasized cognition. "
             "Researchers at Stanford University replicated it. Kahneman's work on heuristics "
             "remains influential. Brown and Smith disagreed. The Hendricks model is robust.")

    def test_cumle_basindaki_isimler_de_ayiklanir(self):
        oz = pipeline.ozel_isimleri_bul(self.METIN)
        for isim in ("vygotsky", "piaget", "kahneman", "maria", "hendricks", "stanford"):
            self.assertIn(isim, oz)

    def test_sozlukteki_kelime_isim_sayilmaz(self):
        oz = pipeline.ozel_isimleri_bul(self.METIN)
        for kelime in ("university", "brown", "smith", "researchers"):
            self.assertNotIn(kelime, oz)

    def test_kucuk_harfle_gecen_isim_sayilmaz(self):
        self.assertNotIn("robust", pipeline.ozel_isimleri_bul("Robust results. The model is robust."))


class LigaturTests(_SimpleTestCase):

    def test_eksik_fi_onarilir_kisaltma_dokunulmaz(self):
        from words.extract import pdf
        metin = ("The rst chapter was the nal one. " * 40) + "License: CC BY-NC-ND."
        yeni, sayi = pdf._ligatur_onar(metin)
        self.assertIn("The first chapter was the final one.", yeni)
        self.assertIn("BY-NC-ND", yeni)
        self.assertGreaterEqual(sayi, 60)

    def test_saglam_metne_dokunulmaz(self):
        from words.extract import pdf
        metin = "The first chapter was the final one. License: CC BY-NC-ND."
        self.assertEqual(pdf._ligatur_onar(metin), (metin, 0))


class ArkaikTests(_SimpleTestCase):
    def test_arkaik_zamirler_islev_kelimesi(self):
        for k in ("thou", "thee", "thy", "unto", "hath"):
            self.assertTrue(function_words.islev_kelimesi_mi(k))
        self.assertFalse(function_words.islev_kelimesi_mi("art"))
