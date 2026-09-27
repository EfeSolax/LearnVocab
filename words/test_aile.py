"""
Aile hattının testleri (words/aile, inflect.cekimler, prompt.family_filling).

Buradaki testler "kod çalışıyor mu" değil "KURAL uygulanıyor mu" sorusunu
soruyor. Bu hattın hataları sessiz: uydurma bir kelime ya da yanlış
birleştirilmiş bir aile hiçbir hata vermez, yalnızca sözlüğe girer.
"""

import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from LearnVocab import llm
from words import inflect
from words.aile import birlestir, denetim
from words.aile.depo import Depo, liste_oku
from words.aile.schema import AileCevabi
from words.enrich import prompt
from words.extract import frequency

WORDFREQ = frequency.wordfreq_var_mi()


def cevap(kok, *uyeler):
    """AileCevabi kısayolu: cevap("expect", "expect:verb", "expectation:noun")"""
    return AileCevabi(root_word=kok, words=[
        {"word": u.split(":")[0], "type": u.split(":")[1]} for u in uyeler])


# ----------------------------------------------------------------------
# Prompt
# ----------------------------------------------------------------------

class AilePromptTests(SimpleTestCase):

    def _ornek_kelimeler(self):
        """family_filling'teki "AİLE ÜYELERİ:" satırlarındaki bütün kelimeler."""
        metin = prompt.family_filling
        bloklar = re.findall(r"AİLE ÜYELERİ:(.*?)(?:\n\n|$)", metin, flags=re.S)
        bloklar += re.findall(r"(?:Ailesi|halleri):(.*?)\n", metin)
        kelimeler = set()
        for blok in bloklar:
            kelimeler |= set(re.findall(r"([a-z][a-z\-]+) \(", blok))
        return kelimeler

    @unittest.skipUnless(WORDFREQ, "wordfreq kurulu değil")
    def test_ornek_ailelerde_olmayan_kelime_yok(self):
        """
        Model örnekleri kurallardan daha güçlü taklit eder. Eski prompt'ta
        "independing", "uneducating" gibi olmayan kelimeler vardı; bir daha
        girmesin.
        """
        kelimeler = self._ornek_kelimeler()
        self.assertGreater(len(kelimeler), 40)
        olmayanlar = sorted(k for k in kelimeler if frequency.zipf(k) == 0)
        self.assertEqual(olmayanlar, [])
        # Kodun "çok nadir" diye atacağı kelime örnekte de olmamalı; yoksa
        # prompt modele, kodun sonra sileceği şeyi öğretir (contrarily 1.99).
        nadirler = sorted(k for k in kelimeler
                          if frequency.zipf(k) < denetim.AYIKLAMA_ESIGI)
        self.assertEqual(nadirler, [])

    def test_deneme_listesi_prompt_ile_kesismiyor(self):
        """
        Ölçüm listesindeki hiçbir kelime ve beklenen kök prompt'ta geçmemeli:
        geçerse model cevabı prompt'tan kopyalar ve ölçtüğümüz şey genelleme
        değil ezber olur (ilk deneme listesinin sorunu buydu).
        """
        from words.aile.deneme import SURUMLER
        metin = prompt.AILE_SISTEM.lower()
        kesisen = set()
        for beklentiler in SURUMLER.values():
            for b in beklentiler:
                for kelime in [b["tohum"], *b["kok"]]:
                    if re.search(rf"\b{re.escape(kelime)}\b", metin):
                        kesisen.add(kelime)
        self.assertEqual(sorted(kesisen), [])

    def test_deneme_surumleri_birbirinden_farkli(self):
        """Her yeni sürüm öncekilerde hiç görülmemiş kelimelerle ölçer."""
        from words.aile.deneme import SURUMLER
        surumler = sorted(SURUMLER)
        for i, yeni in enumerate(surumler[1:], 1):
            onceki = {k for s in surumler[:i] for b in SURUMLER[s]
                      for k in [b["tohum"], *b["kok"]]}
            simdiki = {k for b in SURUMLER[yeni] for k in [b["tohum"], *b["kok"]]}
            self.assertEqual(sorted(onceki & simdiki), [], f"sürüm {yeni}")

    def test_ornek_ailelerde_cekim_uyesi_yok(self):
        """Örneklerde destroyed / educating gibi salt çekimler olmamalı."""
        kelimeler = self._ornek_kelimeler()
        izinli = {"expected", "educated", "unexpected", "uneducated"}  # bağımsız sıfatlar
        cekimler = sorted(k for k in kelimeler
                          if k.endswith(("ed", "ing")) and k not in izinli)
        self.assertEqual(cekimler, [])

    def test_model_yalnizca_kelime_ve_tur_yaziyor(self):
        """Çekim alanları şemada yok: model dolduramaz."""
        alanlar = set(AileCevabi.model_json_schema()["$defs"]["AileUyesi"]["properties"])
        self.assertEqual(alanlar, {"word", "type"})

    def test_turler_veritabani_ile_ayni(self):
        from words.models import PartOfSpeech
        sema = AileCevabi.model_json_schema()["$defs"]["AileUyesi"]["properties"]["type"]
        self.assertEqual(set(sema["enum"]), set(PartOfSpeech.values))

    def test_kullanici_metni(self):
        self.assertEqual(prompt.aile_kullanici_metni("decisively"), 'word: "decisively"')
        self.assertIn('type: "adverb"', prompt.aile_kullanici_metni("decisively", "adverb"))


# ----------------------------------------------------------------------
# Çekim üretimi
# ----------------------------------------------------------------------

class CekimTests(SimpleTestCase):

    def c(self, kelime, tur):
        return inflect.cekimler(kelime, tur)["cekim"]

    def test_duzensiz_fiil(self):
        self.assertEqual(self.c("go", "verb")["v2Form"], "went")
        self.assertEqual(self.c("go", "verb")["v3Form"], "gone")
        self.assertEqual(self.c("go", "verb")["sVersion"], "goes")

    def test_onekli_duzensiz_fiil(self):
        self.assertEqual(self.c("undertake", "verb")["v2Form"], "undertook")
        self.assertEqual(self.c("misunderstand", "verb")["v3Form"], "misunderstood")
        self.assertEqual(self.c("withdraw", "verb")["v3Form"], "withdrawn")

    def test_onek_gibi_gorunen_duzenli_fiil(self):
        """behave = be + have DEĞİL; relay = re + lay DEĞİL."""
        self.assertEqual(self.c("behave", "verb")["v2Form"], "behaved")
        self.assertEqual(self.c("relay", "verb")["v2Form"], "relayed")

    def test_phrasal_verb_yalnizca_fiil_cekimlenir(self):
        c = self.c("carry out", "phrasal_verb")
        self.assertEqual(c["v2Form"], "carried out")
        self.assertEqual(c["ingForm"], "carrying out")
        self.assertEqual(c["sVersion"], "carries out")
        self.assertEqual(self.c("give up", "phrasal_verb")["v3Form"], "given up")

    def test_isim_cogulu(self):
        self.assertEqual(self.c("child", "noun")["sVersion"], "children")
        self.assertEqual(self.c("analysis", "noun")["sVersion"], "analyses")
        self.assertEqual(self.c("policy", "noun")["sVersion"], "policies")

    def test_sayilamayan_isim_cogul_almaz(self):
        self.assertEqual(self.c("information", "noun")["sVersion"], "")
        self.assertEqual(self.c("research", "noun")["sVersion"], "")

    def test_sifat_derecesi(self):
        self.assertEqual(self.c("happy", "adjective")["comparative"], "happier")
        self.assertEqual(self.c("good", "adjective")["superlative"], "best")
        self.assertEqual(self.c("large", "adjective")["comparative"], "larger")

    def test_uzun_sifat_more_most_ile(self):
        """Efe'nin kuralı: more/most ile kuruluyorsa BİLE yazılır."""
        c = self.c("important", "adjective")
        self.assertEqual(c["comparative"], "more important")
        self.assertEqual(c["superlative"], "most important")
        self.assertEqual(self.c("interested", "adjective")["comparative"], "more interested")

    def test_ture_ait_olmayan_alanlar_bos(self):
        c = self.c("go", "verb")
        self.assertEqual(c["comparative"], "")
        self.assertEqual(self.c("quickly", "adverb"), inflect.BOS_CEKIM)

    def test_amerikan_yazimi(self):
        self.assertEqual(inflect.amerikan("analyse"), "analyze")
        self.assertEqual(inflect.amerikan("behaviour"), "behavior")
        self.assertEqual(inflect.amerikan("centre"), "center")
        self.assertEqual(inflect.amerikan("defence"), "defense")
        self.assertEqual(inflect.amerikan("theatre"), "theater")
        self.assertEqual(inflect.amerikan("organisation"), "organization")
        # Çevrilmemesi gerekenler: kural uyuyor ama Amerikan yazımı değil
        for kelime in ("promise", "exercise", "four", "tour", "genre", "acre"):
            self.assertEqual(inflect.amerikan(kelime), kelime)

    def test_cekimde_amerikan_yazimi_esas(self):
        c = self.c("travel", "verb")
        self.assertEqual(c["v2Form"], "traveled")
        self.assertIn("travelled", inflect.cekimler("travel", "verb")["diger_yazimlar"])
        self.assertEqual(self.c("get", "verb")["v3Form"], "gotten")

    def test_kural_kipi_paketsiz_de_calisir(self):
        """lemminflect kurulu olmasa da düzensizler ve sıfatlar doğru çıkmalı."""
        with mock.patch.object(inflect, "_li", return_value=None):
            self.assertEqual(self.c("understand", "verb")["v2Form"], "understood")
            self.assertEqual(self.c("behave", "verb")["v2Form"], "behaved")
            self.assertEqual(self.c("simple", "adjective")["comparative"], "simpler")
            self.assertEqual(self.c("tired", "adjective")["comparative"], "more tired")
            self.assertEqual(inflect.cekimler("go", "verb")["kaynak"], "kural")

    @unittest.skipUnless(inflect.lemminflect_var_mi(), "lemminflect kurulu değil")
    def test_tablo_sozlukle_uyusuyor(self):
        """
        Elle yazılmış düzensiz fiil tablosunu lemminflect sözlüğüyle
        karşılaştırır. Bilinen ayrışmalar dışında fark olmamalı.
        """
        import lemminflect
        bilinen = {"broadcast", "forecast", "leap", "lie", "prove"}
        farkli = []
        for fiil, (v2, _v3) in inflect.DUZENSIZ_FIIL_TABLOSU.items():
            sozluk = lemminflect.getAllInflections(fiil, "VERB").get("VBD", ())
            if v2.split("|")[0] not in sozluk and fiil not in bilinen:
                farkli.append(fiil)
        self.assertEqual(farkli, [])

    def test_quiz_duzensizlik_kontrolu_bozulmadi(self):
        """
        quizzes/build._duzensiz_mi, verb_forms'un KURAL çıktısına dayanıyor
        (go -> "goed"). Otomatik çekim eklenirken verb_forms'a dokunulmadı.
        """
        kural = dict((t, y) for y, t in inflect.verb_forms("go"))
        self.assertEqual(kural["past"], "goed")


# ----------------------------------------------------------------------
# 1. aşama denetimi
# ----------------------------------------------------------------------

@unittest.skipUnless(WORDFREQ, "wordfreq kurulu değil")
class DenetimTests(SimpleTestCase):

    def kodlar(self, taslak):
        return [s["kod"] for s in taslak["sorunlar"]]

    def metinler(self, taslak):
        return {u["word"] for u in taslak["uyeler"]}

    def test_temiz_aile(self):
        t = denetim.denetle(cevap("expect", "expect:verb", "expectation:noun",
                                  "unexpected:adjective"), "expectation")
        self.assertEqual(t["durum"], "tamam")
        self.assertEqual(t["kok"], "expect")
        self.assertEqual(t["uyeler"][0]["word"], "expect")    # kök önce
        self.assertEqual(t["uyeler"][0]["cekim"]["v2Form"], "expected")

    def test_olmayan_kelime_atilir(self):
        t = denetim.denetle(cevap("depend", "depend:verb", "independent:adjective",
                                  "independing:verb"), "depend")
        self.assertNotIn("independing", self.metinler(t))
        self.assertIn("olmayan_kelime", self.kodlar(t))
        self.assertEqual(t["ayiklanan"][0]["sebep"], "olmayan_kelime")

    def test_cok_nadir_kelime_atilir_ama_tohum_korunur(self):
        t = denetim.denetle(cevap("influence", "influence:verb", "influential:adjective",
                                  "influentially:adverb"), "influence")
        self.assertNotIn("influentially", self.metinler(t))
        t = denetim.denetle(cevap("influentially", "influentially:adverb"), "influentially")
        self.assertIn("influentially", self.metinler(t))

    def test_fiil_olarak_yazilmis_cekim_atilir(self):
        t = denetim.denetle(cevap("destroy", "destroy:verb", "destroyed:verb",
                                  "destroying:verb", "destruction:noun"), "destroy")
        self.assertEqual(self.metinler(t), {"destroy", "destruction"})
        self.assertEqual(self.kodlar(t).count("cekim_uyesi"), 2)

    def test_isim_cogulu_atilir(self):
        t = denetim.denetle(cevap("interest", "interest:noun", "interest:verb",
                                  "interests:noun", "interesting:adjective"), "interest")
        self.assertNotIn("interests", self.metinler(t))
        self.assertIn("cekim_uyesi", self.kodlar(t))

    def test_tekilinden_sik_cogul_bagimsiz_kelimedir(self):
        """ethics (etik bilimi) ethic'in çoğulu ama ondan daha sık: kalır."""
        t = denetim.denetle(cevap("ethic", "ethic:noun", "ethics:noun",
                                  "ethical:adjective"), "ethic")
        self.assertIn("ethics", self.metinler(t))

    def test_on_ek_ve_son_ek_birlikte(self):
        """unhappiness -> kök "happiness" yazılmışsa happy'ye iner (y -> i)."""
        t = denetim.denetle(cevap("happiness", "happy:adjective", "happiness:noun",
                                  "unhappiness:noun"), "unhappiness")
        self.assertEqual(t["kok"], "happy")

    def test_de_s_donusumu(self):
        """indecisive -> kök "decisive" yazılmışsa decide'a iner (decide -> decis-)."""
        t = denetim.denetle(cevap("decisive", "decide:verb", "decisive:adjective",
                                  "indecisive:adjective"), "indecisive")
        self.assertEqual(t["kok"], "decide")

    def test_ingiliz_yazimi_cevrilir(self):
        t = denetim.denetle(cevap("analyse", "analyse:verb", "analysis:noun",
                                  "analyst:noun"), "analyse")
        self.assertEqual(t["kok"], "analyze")
        self.assertIn("analyze", self.metinler(t))
        self.assertIn("amerikan_yazimi", self.kodlar(t))
        self.assertNotIn("tohum_ailede_yok", self.kodlar(t))

    def test_koparan_onekle_bulunan_kok_kusurlu(self):
        """withdraw -> kök "draw": with- anlamı koparır, taslak kusurlu."""
        t = denetim.denetle(cevap("draw", "draw:verb", "drawing:noun", "withdrawal:noun"),
                            "withdraw")
        self.assertEqual(t["durum"], "kusurlu")
        self.assertIn("koparan_onek", self.kodlar(t))

    def test_koparan_onekli_uye_atilir(self):
        """draw ailesinde withdraw olmamalı (kendi ailesi)."""
        t = denetim.denetle(cevap("draw", "draw:verb", "drawing:noun", "withdraw:verb"),
                            "draw")
        self.assertNotIn("withdraw", self.metinler(t))
        self.assertEqual(t["ayiklanan"][0]["sebep"], "koparan_onek")

    def test_aşırılık_oneki_koparan_degil(self):
        t = denetim.denetle(cevap("react", "react:verb", "overreact:verb"), "overreact")
        self.assertEqual(t["durum"], "tamam")
        self.assertIn("overreact", self.metinler(t))

    def test_sifati_ailede_olan_nadir_zarf_atilir(self):
        """comparably (2.47): comparable ailede, zarf atılır."""
        t = denetim.denetle(cevap("compare", "compare:verb", "comparable:adjective",
                                  "comparably:adverb"), "compare")
        self.assertNotIn("comparably", self.metinler(t))
        self.assertIn("nadir_zarf", self.kodlar(t))

    @unittest.skipUnless(inflect.lemminflect_var_mi(), "lemminflect kurulu değil")
    def test_uydurma_tur_atilir(self):
        """become (adjective), weak (noun): kelime gerçek, tür değil."""
        t = denetim.denetle(cevap("weak", "weak:adjective", "weak:noun", "weaken:verb",
                                  "weakness:noun"), "weakness")
        self.assertEqual({(u["word"], u["type"]) for u in t["uyeler"]},
                         {("weak", "adjective"), ("weaken", "verb"), ("weakness", "noun")})
        self.assertIn("supheli_tur", self.kodlar(t))

    @unittest.skipUnless(inflect.lemminflect_var_mi(), "lemminflect kurulu değil")
    def test_supheli_katilim_isaretlenir_atilmaz(self):
        t = denetim.denetle(cevap("pollute", "pollute:verb", "polluted:adjective",
                                  "pollution:noun"), "pollution")
        uye = next(u for u in t["uyeler"] if u["word"] == "polluted")
        self.assertTrue(uye.get("supheli_katilim"))
        interested = denetim.denetle(cevap("interest", "interest:verb",
                                           "interested:adjective"), "interest")
        self.assertFalse(next(u for u in interested["uyeler"]
                              if u["word"] == "interested").get("supheli_katilim"))

    def test_katilim_bilgi_seviyesinde(self):
        t = denetim.denetle(cevap("interest", "interest:verb", "interested:adjective"),
                            "interest")
        seviye = {s["kod"]: s["seviye"] for s in t["sorunlar"]}
        self.assertEqual(seviye["katilim_sifati"], "bilgi")

    def test_sifat_olarak_yazilmis_katilim_isaretlenir(self):
        t = denetim.denetle(cevap("interest", "interest:noun", "interest:verb",
                                  "interested:adjective"), "interest")
        self.assertIn("interested", self.metinler(t))
        self.assertIn("katilim_sifati", self.kodlar(t))

    def test_onekli_kok_duzeltilir(self):
        t = denetim.denetle(cevap("unhappy", "happy:adjective", "unhappy:adjective",
                                  "happiness:noun"), "unhappy")
        self.assertEqual(t["kok"], "happy")
        self.assertIn("onekli_kok_duzeltildi", self.kodlar(t))

    def test_onekle_baslayan_ama_bagimsiz_kok_kalir(self):
        """understand'da 'stand' ailede değil: kök değişmez."""
        t = denetim.denetle(cevap("understand", "understand:verb",
                                  "understanding:noun", "misunderstand:verb"), "understand")
        self.assertEqual(t["kok"], "understand")

    def test_onek_ve_turev_birlikte_duzeltilir(self):
        """independent -> dependent (önek) -> depend (türev)."""
        t = denetim.denetle(cevap("independent", "depend:verb", "dependent:adjective",
                                  "independent:adjective"), "dependent")
        self.assertEqual(t["kok"], "depend")
        kodlar = self.kodlar(t)
        self.assertIn("onekli_kok_duzeltildi", kodlar)
        self.assertIn("turemis_kok_duzeltildi", kodlar)

    def test_zarf_kok_duzeltilir(self):
        t = denetim.denetle(cevap("inevitably", "inevitable:adjective",
                                  "inevitably:adverb"), "inevitably")
        self.assertEqual(t["kok"], "inevitable")

    def test_kok_listede_yoksa_uyari(self):
        t = denetim.denetle(cevap("decide", "decision:noun", "decisive:adjective"), "decision")
        self.assertIn("kok_listede_yok", self.kodlar(t))

    def test_uydurma_kok_kusurlu(self):
        t = denetim.denetle(cevap("herit", "inherent:adjective", "inherently:adverb"),
                            "inherent")
        self.assertEqual(t["durum"], "kusurlu")
        self.assertIn("uydurma_kok", self.kodlar(t))

    def test_bos_cevap_bulunamadi(self):
        t = denetim.denetle(AileCevabi(root_word="", words=[]), "xyzqq")
        self.assertEqual(t["durum"], "bulunamadi")

    def test_cok_kelimeli_ifade_atilir_phrasal_verb_duzeltilir(self):
        t = denetim.denetle(cevap("carry", "carry:verb", "carry out:verb",
                                  "in the long run:adverb"), "carry")
        turler = {u["word"]: u["type"] for u in t["uyeler"]}
        self.assertEqual(turler["carry out"], "phrasal_verb")
        self.assertNotIn("in the long run", turler)

    def test_ayni_kelime_farkli_tur_ayri_uye(self):
        t = denetim.denetle(cevap("influence", "influence:verb", "influence:noun",
                                  "influence:noun"), "influence")
        self.assertEqual(sorted(u["type"] for u in t["uyeler"]), ["noun", "verb"])


# ----------------------------------------------------------------------
# 2. aşama: birleştirme
# ----------------------------------------------------------------------

def taslak(tohum, kok, *kelimeler):
    """Birleştirme testleri için elle taslak. kelime ya da kelime:tür."""
    uyeler = []
    for k in kelimeler:
        metin, _, tur = k.partition(":")
        uyeler.append({"word": metin, "type": tur or "noun"})
    return {"tohum": tohum, "tur_ipucu": "", "kok": kok, "uyeler": uyeler,
            "sorunlar": [], "durum": "tamam"}


class BirlestirmeTests(SimpleTestCase):

    def aile(self, aileler, kok):
        return next(a for a in aileler if a["kok"] == kok)

    def test_kapsama_eksik_taslagi_anlasmazlik_saymaz(self):
        """react / overreact: biri ötekinden eksiksiz; Jaccard 0.44 diyordu."""
        a = {"overreact", "overreaction", "react", "reactant", "reaction", "reactive"}
        b = {"react", "reactance", "reactant", "reaction", "reactive", "reactivity", "reactor"}
        self.assertLess(birlestir.jaccard(a, b), 0.5)
        self.assertGreaterEqual(birlestir.kapsama(a, b), birlestir.ORTUSME_ESIGI)

    def test_kok_beraberliginde_turetme_karar_verir(self):
        """rely 2 - reliable 2: reliable rely'dan türemiş, kök rely."""
        aileler, _ = birlestir.birlestir([
            taslak("reliable", "rely", "rely", "reliable", "reliably", "reliance", "unreliable"),
            taslak("rely", "rely", "rely", "reliable", "reliably", "reliance", "unreliable"),
            taslak("reliability", "reliable", "reliable", "reliability", "reliably",
                   "unreliable"),
            taslak("unreliable", "reliable", "reliable", "reliability", "reliably",
                   "unreliable"),
        ])
        self.assertEqual(len(aileler), 1)
        self.assertEqual(aileler[0]["kok"], "rely")
        self.assertEqual(aileler[0]["durum"], "temiz")

    def test_ayni_koklu_taslaklar_tek_aile(self):
        aileler, _ = birlestir.birlestir([
            taslak("decisively", "decide", "decide", "decision", "decisive", "decisively",
                   "indecisive"),
            taslak("decision", "decide", "decide", "decision", "decisive", "decisively"),
        ])
        self.assertEqual(len(aileler), 1)
        aile = aileler[0]
        self.assertEqual(aile["durum"], "temiz")
        self.assertEqual(aile["ortusme"]["ortalama"], 1.0)   # küçük taslak büyüğün içinde
        self.assertEqual(aile["uyeler"][0]["word"], "decide")
        indecisive = next(u for u in aile["uyeler"] if u["word"] == "indecisive")
        self.assertEqual(indecisive["destek"], 0.5)

    def test_dusuk_ortusme_raporlanir(self):
        aileler, _ = birlestir.birlestir([
            taslak("a1", "form", "form", "formal", "formally"),
            taslak("a2", "form", "form", "formation", "transform", "reform", "formula"),
        ])
        aile = aileler[0]
        self.assertEqual(aile["durum"], "incelenecek")
        self.assertIn("dusuk_ortusme", [s["kod"] for s in aile["sorunlar"]])
        yalniz = {t["tohum"]: t["yalniz_bunda"] for t in aile["taslaklar"]}
        self.assertEqual(yalniz["a1"], ["formal", "formally"])

    def test_kokte_anlasamayan_ama_ortusen_taslaklar_cogunlukla_birlesir(self):
        aileler, _ = birlestir.birlestir([
            taslak("analysis", "analyse", "analyse", "analysis", "analyst", "analytical"),
            taslak("analytical", "analyse", "analyse", "analysis", "analyst", "analytical"),
            taslak("analyst", "analysis", "analyse", "analysis", "analyst", "analytical"),
        ])
        self.assertEqual(len(aileler), 1)
        self.assertEqual(aileler[0]["kok"], "analyse")
        self.assertEqual(aileler[0]["sorunlar"][0]["kod"], "kok_oylamasi")
        self.assertEqual(aileler[0]["durum"], "temiz")

    def test_kok_catismasi_otomatik_birlestirilmez(self):
        """consent ailesine consensus girmiş; consensus kendi ailesini kurmuş."""
        aileler, _ = birlestir.birlestir([
            taslak("consent", "consent", "consent", "consensual", "consensus"),
            taslak("consensus", "consensus", "consensus"),
        ])
        self.assertEqual({a["kok"] for a in aileler}, {"consent", "consensus"})
        for aile in aileler:
            self.assertEqual(aile["durum"], "incelenecek")
            self.assertIn("kok_catismasi", [s["kod"] for s in aile["sorunlar"]])
        # consensus kendi sorulduğunda kendi ailesine girdi: sahibi o.
        self.assertNotIn("consensus", {u["word"] for u in self.aile(aileler, "consent")["uyeler"]})

    def test_ayri_tut_karari(self):
        aileler, _ = birlestir.birlestir([
            taslak("consent", "consent", "consent", "consensual", "consensus"),
            taslak("consensus", "consensus", "consensus"),
        ], {"ayri_tut": [["consent", "consensus"]]})
        self.assertEqual({a["durum"] for a in aileler}, {"temiz"})
        self.assertNotIn("consensus", {u["word"] for u in self.aile(aileler, "consent")["uyeler"]})

    def test_kok_esle_karari(self):
        aileler, _ = birlestir.birlestir([
            taslak("analyse", "analyse", "analyse", "analyst"),
            taslak("analysis", "analysis", "analysis", "analytical"),
        ], {"kok_esle": {"analysis": "analyse"}})
        self.assertEqual(len(aileler), 1)
        self.assertEqual(aileler[0]["kok"], "analyse")
        self.assertEqual({u["word"] for u in aileler[0]["uyeler"]},
                         {"analyse", "analyst", "analysis", "analytical"})

    def test_cikar_ve_onayla_kararlari(self):
        aileler, _ = birlestir.birlestir([
            taslak("a1", "form", "form", "formal", "formally"),
            taslak("a2", "form", "form", "formation", "formula"),
        ], {"cikar": {"form": ["formula"]}, "onayla": ["form"]})
        aile = aileler[0]
        self.assertNotIn("formula", {u["word"] for u in aile["uyeler"]})
        self.assertEqual(aile["durum"], "temiz")

    def test_uye_ata_karari(self):
        aileler, _ = birlestir.birlestir([
            taslak("consent", "consent", "consent", "consensus"),
            taslak("agree", "agree", "agree", "consensus"),
        ], {"ayri_tut": [["consent", "agree"]], "uye_ata": {"consensus": "agree"}})
        self.assertIn("consensus", {u["word"] for u in self.aile(aileler, "agree")["uyeler"]})
        self.assertNotIn("consensus", {u["word"] for u in self.aile(aileler, "consent")["uyeler"]})

    def test_kusurlu_taslak_disarida_kalir(self):
        kusurlu = {**taslak("inherent", "herit", "inherent"), "durum": "kusurlu"}
        aileler, disarida = birlestir.birlestir([kusurlu])
        self.assertEqual(aileler, [])
        self.assertEqual(disarida, [kusurlu])

    def test_tur_farki_zayif_uye(self):
        aileler, _ = birlestir.birlestir([
            taslak("a", "influence", "influence:verb", "influence:noun", "influential:adjective"),
            taslak("b", "influence", "influence:verb", "influence:noun", "influential:adjective"),
            taslak("c", "influence", "influence:verb", "influence:noun", "influential:noun"),
        ])
        kodlar = [s["kod"] for s in aileler[0]["sorunlar"]]
        self.assertIn("zayif_uye", kodlar)


# ----------------------------------------------------------------------
# Ara depo
# ----------------------------------------------------------------------

class DepoTests(SimpleTestCase):

    def setUp(self):
        self.klasor = tempfile.mkdtemp()
        self.depo = Depo(self.klasor)

    def tearDown(self):
        shutil.rmtree(self.klasor, ignore_errors=True)

    def test_son_taslak_gecerli_gecmis_korunur(self):
        self.depo.taslak_ekle(taslak("analysis", "analysis", "analysis"))
        self.depo.taslak_ekle(taslak("analysis", "analyse", "analyse", "analysis"))
        self.assertEqual(len(self.depo.tum_taslaklar()), 2)
        guncel = self.depo.guncel_taslaklar()
        self.assertEqual(len(guncel), 1)
        self.assertEqual(guncel[0]["kok"], "analyse")

    def test_hata_alan_kelime_yeniden_sorulur(self):
        self.depo.taslak_ekle({"tohum": "x", "tur_ipucu": "", "durum": "hata"})
        self.depo.taslak_ekle(taslak("y", "y", "y"))
        self.assertEqual(self.depo.sorulmus_mu(), {("y", "")})

    def test_kararlar_sablonu_olusur(self):
        self.depo.hazirla()
        kararlar = self.depo.kararlar()
        self.assertEqual(set(kararlar), {"kok_esle", "ayri_tut", "cikar", "uye_ata", "onayla"})

    def test_bozuk_satir_depoyu_okunmaz_yapmaz(self):
        self.depo.taslak_ekle(taslak("a", "a", "a"))
        with (self.depo.yol / "taslaklar.jsonl").open("a", encoding="utf-8") as f:
            f.write('{"tohum": "yarim')
        self.assertEqual(len(self.depo.tum_taslaklar()), 2)

    def test_liste_oku(self):
        self.assertEqual(
            liste_oku(["# yorum", "", "decisively:adverb   # DB: decide",
                       "Analysis", "analysis", "carry out:phrasal verb"]),
            [("decisively", "adverb"), ("analysis", ""), ("carry out", "phrasal_verb")])


# ----------------------------------------------------------------------
# Komutlar (model taklit edilerek)
# ----------------------------------------------------------------------

SAHTE_CEVAPLAR = {
    "decisively": cevap("decide", "decide:verb", "decision:noun", "decisive:adjective",
                        "decisively:adverb", "indecisive:adjective"),
    "decision": cevap("decide", "decide:verb", "decision:noun", "decisive:adjective",
                      "decisively:adverb", "decided:verb"),
    "xyzqq": AileCevabi(root_word="", words=[]),
    "decide": cevap("decide", "decide:verb", "decision:noun", "decisive:adjective",
                    "decisively:adverb", "indecisive:adjective"),
    "withdraw": cevap("draw", "draw:verb", "drawing:noun", "withdrawal:noun"),
    "withdraw+uyari": cevap("withdraw", "withdraw:verb", "withdrawal:noun",
                            "withdrawn:adjective"),
}


def sahte_chat_json(system, user, schema, **_kw):
    tohum = re.search(r'word: "([^"]+)"', user).group(1)
    if "DİKKAT" in user and f"{tohum}+uyari" in SAHTE_CEVAPLAR:
        tohum += "+uyari"
    veri = SAHTE_CEVAPLAR[tohum]
    return llm.Result(data=veri, raw=veri.model_dump_json(),
                      usage=llm.Usage(prompt_tokens=100, completion_tokens=20, requests=1))


@unittest.skipUnless(WORDFREQ, "wordfreq kurulu değil")
class KomutTests(TestCase):

    def setUp(self):
        self.klasor = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.klasor, ignore_errors=True)

    def calistir(self, *argumanlar, **secenekler):
        cikti = StringIO()
        call_command(*argumanlar, stdout=cikti, stderr=StringIO(), **secenekler)
        return cikti.getvalue()

    @mock.patch("LearnVocab.llm.chat_json", side_effect=sahte_chat_json)
    def test_uret_ve_birlestir(self, _sahte):
        cikti = self.calistir("aile_uret", words="decisively,decision,xyzqq",
                              depo=self.klasor, workers=2)
        self.assertIn("3 tamam", cikti)          # 2 liste + 1 kök sorgusu (decide)
        self.assertIn("1 bulunamadı", cikti)
        self.assertIn("Kök sorgusu: 1 kök", cikti)

        depo = Depo(self.klasor)
        decision = next(t for t in depo.guncel_taslaklar() if t["tohum"] == "decision")
        # "decided (verb)" decide'ın çekimi: ayıklandı
        self.assertNotIn("decided", {u["word"] for u in decision["uyeler"]})
        self.assertEqual(decision["ayiklanan"][0]["sebep"], "cekim_uyesi")
        self.assertIn("ham", decision)

        cikti = self.calistir("aile_birlestir", depo=self.klasor)
        self.assertIn("1 aile", cikti)
        aile = depo.aileler()[0]
        self.assertEqual(aile["kok"], "decide")
        self.assertEqual(aile["taslak_sayisi"], 3)
        rapor = (depo.yol / "birlestirme-raporu.txt").read_text(encoding="utf-8")
        self.assertIn("xyzqq", rapor)     # bulunamayan raporda görünür

    @mock.patch("LearnVocab.llm.chat_json", side_effect=sahte_chat_json)
    def test_kaldigi_yerden_devam_eder(self, sahte):
        self.calistir("aile_uret", words="decisively", depo=self.klasor)
        self.assertEqual(sahte.call_count, 2)     # decisively + kök sorgusu (decide)
        self.calistir("aile_uret", words="decisively,decision", depo=self.klasor)
        self.assertEqual(sahte.call_count, 3)     # yalnızca decision; ikisi de depoda

    @mock.patch("LearnVocab.llm.chat_json", side_effect=sahte_chat_json)
    def test_koparan_onekte_uyariyla_tekrar_sorulur(self, sahte):
        self.calistir("aile_uret", words="withdraw", depo=self.klasor, kok_sorma=True)
        self.assertEqual(sahte.call_count, 2)
        t = Depo(self.klasor).guncel_taslaklar()[0]
        self.assertEqual(t["kok"], "withdraw")
        self.assertEqual(t["durum"], "tamam")
        self.assertIn("ikinci_deneme", [s["kod"] for s in t["sorunlar"]])

    @mock.patch("LearnVocab.llm.chat_json", side_effect=sahte_chat_json)
    def test_kok_sorgusu_kapatilabilir(self, sahte):
        self.calistir("aile_uret", words="decisively", depo=self.klasor, kok_sorma=True)
        self.assertEqual(sahte.call_count, 1)

    @mock.patch("LearnVocab.llm.chat_json", side_effect=sahte_chat_json)
    def test_dry_run_depoya_yazmaz(self, _sahte):
        self.calistir("aile_uret", words="decisively", depo=self.klasor, dry_run=True)
        self.assertEqual(Depo(self.klasor).tum_taslaklar(), [])


# ----------------------------------------------------------------------
# 3. aşama: anlam doldurma
# ----------------------------------------------------------------------

from words.aile import anlam as A  # noqa: E402
from words.enrich import checks  # noqa: E402

CUMLELER = {
    "pollute": ["Factories pollute the river with chemical waste every year.",
                "Cars pollute the air in big cities during rush hour.",
                "The company was fined because it continued to pollute the lake.",
                "Plastic bags pollute beaches all around the Mediterranean coast.",
                "Industries that pollute heavily should pay higher environmental taxes."],
    "pollution": ["Air pollution is a serious problem in many large cities.",
                  "The government introduced new laws to reduce pollution quickly.",
                  "Noise pollution near the airport keeps residents awake at night.",
                  "Scientists measured the level of pollution in the river water.",
                  "Pollution from coal plants contributes significantly to climate change."],
}


def anlam_cevabi(kelime, tur, meaning_tr, cefr="B1", baglar=(), found=True, sebep=""):
    if not found:
        return A.KelimeCevabi(found=False, skip_reason=sebep, word=kelime, type=tur, meanings=[])
    return A.KelimeCevabi(found=True, skip_reason="", word=kelime, type=tur, meanings=[{
        "meaning_tr": meaning_tr, "definition": f"definition of {kelime}",
        "sentiment": "negative", "register": "general", "cefr": cefr,
        "categories": ["Environment"],
        "collocations": [{"collocation": ("air pollution" if tur == "noun" else "pollute the air"),
                          "meaning_tr": "hava kirliliği",
                          "example": CUMLELER[kelime][0] if tur == "noun" else CUMLELER[kelime][1]}],
        "patterns": [{"pattern": "pollute sth with sth", "example": CUMLELER.get(kelime, [""])[0],
                      "note": ""}] if tur == "verb" else [],
        "sentences": CUMLELER[kelime],
        "relations": [{"to_word": b, "type": "synonym"} for b in baglar],
    }])


class AnlamDenetimTests(SimpleTestCase):

    def test_reddedilen_kelime_yazilmaz(self):
        cevap = anlam_cevabi("polluted", "adjective", "", found=False, sebep="fiilin çekimi")
        rapor = A.denetle(cevap, "polluted", "adjective")
        self.assertFalse(rapor.kabul)
        self.assertEqual(rapor.hatalar[0].kod, "fiil_cekimi")

    def test_listede_olmayan_kategori_semaya_uymaz(self):
        from pydantic import ValidationError
        veri = anlam_cevabi("pollution", "noun", "kirlilik").model_dump()
        veri["meanings"][0]["categories"] = ["Uydurma Alan"]
        with self.assertRaises(ValidationError):
            A.KelimeCevabi.model_validate(veri)
        sema = A.KelimeCevabi.model_json_schema()
        self.assertIn("Psychology", str(sema))

    def test_kategori_listesi_prompttan(self):
        self.assertGreater(len(A.KATEGORILER), 100)
        for ad in ("Success & Failure", "Psychology", "Sociology", "Anthropology",
                   "Linguistics", "Statistics"):
            self.assertIn(ad, A.KATEGORILER)

    def test_katilimin_fiil_anlami_atilir(self):
        """polluted = "kirletilmiş": fiilin kendi anlamı, kelime düşer."""
        cevap = anlam_cevabi("pollution", "noun", "kirletilmiş, kirli")
        cevap.word, cevap.type = "polluted", "adjective"
        for anlam in cevap.meanings:
            anlam.sentences = [c.replace("pollution", "polluted").replace("Pollution", "Polluted")
                               for c in anlam.sentences]
        rapor = A.denetle(cevap, "polluted", "adjective", supheli_katilim=True)
        self.assertFalse(rapor.kabul)
        self.assertEqual(rapor.hatalar[0].kod, "fiil_cekimi")

    def test_bagimsiz_katilim_kalir(self):
        """collected = "sakin": fiilden ayrı anlam, kalır (-mış değil)."""
        self.assertIsNone(A._MIS.search("sakin"))
        self.assertIsNotNone(A._MIS.search("kirletilmiş"))
        self.assertIsNotNone(A._MIS.search("zayıflamış"))

    def test_fiilde_mastarsiz_anlam_atilir(self):
        cevap = anlam_cevabi("pollute", "verb", "kirletmek, kirletmek")
        ikinci = cevap.meanings[0].model_copy(deep=True)
        ikinci.meaning_tr = "sebze, meyve gibi gıdalar"
        ikinci.collocations = []
        cevap.meanings.append(ikinci)
        rapor = A.denetle(cevap, "pollute", "verb")
        self.assertEqual([a.meaning_tr for a in cevap.meanings], ["kirletmek"])  # tekrar da gitti
        self.assertIn("mastar_degil", [s.kod for s in rapor.sorunlar])

    def test_yinelenen_anlam_atilir(self):
        cevap = anlam_cevabi("pollution", "noun", "kirlilik")
        cevap.meanings.append(cevap.meanings[0].model_copy(deep=True))
        A.denetle(cevap, "pollution", "noun")
        self.assertEqual(len(cevap.meanings), 1)

    def test_esdizim_turu(self):
        self.assertEqual(A.esdizim_turu("make a decision", "decision", "noun"), "verb_noun")
        self.assertEqual(A.esdizim_turu("important decision", "decision", "noun"), "adj_noun")
        self.assertEqual(A.esdizim_turu("heavily dependent", "dependent", "adjective"), "adv_adj")

    def test_kalip_turu(self):
        self.assertEqual(A.kalip_turu("depend on sth"), "preposition")
        self.assertEqual(A.kalip_turu("suggest doing sth"), "verb_form")
        self.assertEqual(A.kalip_turu("insist that sb do sth"), "clause")


def sahte_anlam_json(system, user, schema, **_kw):
    kelime = re.search(r'word: "([^"]+)", type: "([^"]+)"', user)
    metin, tur = kelime.group(1), kelime.group(2)
    if metin == "pollution" and "DİKKAT" not in user:
        # İlk cevap bozuk Türkçe: tanım gibi ve uzun -> uyarıyla tekrar sorulmalı
        veri = anlam_cevabi(metin, tur, "havanın ya da suyun zararlı maddelerle kirlenmesi durumu")
    elif metin == "polluted":
        assert "fiilin çekimi olabilir" in user     # şüpheli katılım uyarısı gitti
        veri = anlam_cevabi(metin, tur, "", found=False, sebep="fiilin çekimi")
    elif metin == "pollute":
        veri = anlam_cevabi(metin, tur, "kirletmek", "B1", baglar=["contaminate", "pollution"])
    else:
        veri = anlam_cevabi(metin, tur, "kirlilik", "A2")
    return llm.Result(data=veri, raw=veri.model_dump_json(),
                      usage=llm.Usage(prompt_tokens=100, completion_tokens=50, requests=1))


# Kontrol modeli .env'de ayarlıyken bu testler onu da çağırıp sahte üretici
# cevabını kontrolcü kararı sanıyordu. Kontrol aşaması KontrolUygulaTests'te.
@override_settings(LLM_KONTROL_MODEL="")
class AileDoldurTests(TestCase):

    def setUp(self):
        self.klasor = tempfile.mkdtemp()
        self.depo = Depo(self.klasor)
        uyeler = []
        for metin, tur, supheli in (("pollute", "verb", False), ("pollution", "noun", False),
                                    ("polluted", "adjective", True)):
            sonuc = inflect.cekimler(metin, tur)
            uyeler.append({"word": metin, "type": tur, "cekim": sonuc["cekim"],
                           "diger_yazimlar": sonuc["diger_yazimlar"],
                           **({"supheli_katilim": True} if supheli else {})})
        aile = {"kok": "pollute", "durum": "temiz", "uyeler": uyeler, "tohumlar": ["pollution"],
                "taslak_sayisi": 2, "ortusme": None, "sorunlar": [], "taslaklar": [],
                "taslak_uyarilari": []}
        self.depo.aileleri_yaz([aile], {}, "")

    def tearDown(self):
        shutil.rmtree(self.klasor, ignore_errors=True)

    def calistir(self, **secenekler):
        cikti = StringIO()
        call_command("aile_doldur", depo=self.klasor, stdout=cikti, stderr=StringIO(),
                     **secenekler)
        return cikti.getvalue()

    @mock.patch("LearnVocab.llm.chat_json", side_effect=sahte_anlam_json)
    def test_aile_yazilir(self, sahte):
        from words.models import Meaning, Word, WordFamily
        cikti = self.calistir()
        self.assertIn("2 kelime yazıldı", cikti)
        self.assertEqual(WordFamily.objects.get().root, "pollute")
        self.assertFalse(Word.objects.filter(text="polluted").exists())    # reddedildi
        fiil = Word.objects.get(text="pollute")
        self.assertEqual(fiil.v2Form, "polluted")
        self.assertEqual(fiil.cefr, "B1")
        anlam = fiil.meanings.get()
        self.assertEqual(anlam.register, "neutral")                          # general -> neutral
        self.assertEqual(anlam.cefr, "B1")
        self.assertEqual([c.name for c in anlam.categories.all()], ["Environment"])
        self.assertEqual(anlam.examples.count(), 5)
        self.assertEqual(anlam.patterns.get().kind, "preposition")
        self.assertEqual(anlam.collocations.get().kind, "verb_noun")
        self.assertTrue(fiil.forms.filter(surface="pollutes").exists())
        self.assertEqual(Word.objects.get(text="pollution").cefr, "A2")
        # pollute -> pollution bağı (hedef aynı çalıştırmada yazıldı); contaminate yok
        self.assertTrue(fiil.relations_from.filter(to_word__text="pollution").exists())
        self.assertIn("1 bağın hedefi henüz yok", cikti)
        self.assertEqual(Meaning.objects.count(), 2)
        # pollution ilk cevapta bozuk Türkçe verdi; ikinci cevap yazıldı
        self.assertEqual(Word.objects.get(text="pollution").meanings.get().meaning_tr, "kirlilik")
        self.assertIn("1 kelime sorunları yüzünden tekrar soruldu", cikti)

    @mock.patch("LearnVocab.llm.chat_json", side_effect=sahte_anlam_json)
    def test_dry_run_yazmaz_ve_cevap_tekrar_sorulmaz(self, sahte):
        from words.models import Word
        self.calistir(dry_run=True)
        self.assertEqual(Word.objects.count(), 0)
        self.assertEqual(sahte.call_count, 4)          # 3 kelime + pollution'ın ikinci denemesi
        self.calistir()
        self.assertEqual(sahte.call_count, 4)          # depodaki cevaplar kullanıldı
        self.assertEqual(Word.objects.count(), 2)

    @mock.patch("LearnVocab.llm.chat_json", side_effect=sahte_anlam_json)
    def test_ikinci_calistirma_bir_sey_yazmaz(self, sahte):
        from words.models import Meaning
        self.calistir()
        self.calistir()
        self.assertEqual(Meaning.objects.count(), 2)


    @mock.patch("LearnVocab.llm.chat_json", side_effect=sahte_anlam_json)
    def test_aile_sil(self, _sahte):
        from words.models import Category, Word, WordFamily
        self.calistir()
        cikti = StringIO()
        call_command("aile_sil", depo=self.klasor, stdout=cikti)
        self.assertIn("Hiçbir şey silinmedi", cikti.getvalue())
        self.assertEqual(WordFamily.objects.count(), 1)
        call_command("aile_sil", depo=self.klasor, evet=True, stdout=StringIO())
        self.assertEqual(WordFamily.objects.count(), 0)
        self.assertEqual(Word.objects.count(), 0)
        self.assertEqual(Category.objects.count(), 0)


# ----------------------------------------------------------------------
# Türkçe yazım denetimi ve kontrol modeli
# ----------------------------------------------------------------------

from django.test import override_settings  # noqa: E402

from words.aile import kontrol as K  # noqa: E402
from words.aile import turkce  # noqa: E402

TURKCE = turkce.durum()[0]


@unittest.skipUnless(TURKCE, "Türkçe sözlük kurulu değil (manage.py turkce_sozluk_kur)")
class TurkceYazimTests(SimpleTestCase):

    def test_olmayan_kelimeler_yakalanir(self):
        self.assertEqual(turkce.bilinmeyenler("kirlık, çevre kirliliği"), ["kirlık"])
        self.assertEqual(turkce.bilinmeyenler("teşeksiz, minnet duymayan"), ["teşeksiz"])

    def test_cekimli_ve_turemis_kelimeler_tanınır(self):
        self.assertEqual(turkce.bilinmeyenler(
            "öngörülemezlik, evlat edinilmiş, kirletmek, dikkatlice, İstanbul, hâkim"), [])

    def test_yasakli_yazimlar(self):
        """Hunspell 'kirlendirmek'i tanıyor ama Türkçesi 'kirletmek'."""
        self.assertEqual(turkce.bilinmeyenler("kirlendirmek, kirletmek"), ["kirlendirmek"])

    def test_gercek_verideki_yazim_hatalari(self):
        """2. doldurma denemesinde veritabanına giren yazım hataları."""
        self.assertEqual(turkce.bilinmeyenler("varolmama, mizahcı"), ["varolmama", "mizahcı"])

    def test_turkce_kucuk_harf(self):
        self.assertEqual(turkce.turkce_kucuk("IŞIK İzmir"), "ışık izmir")

    def test_yanlis_yazilan_karsilik_atilir(self):
        cevap = anlam_cevabi("pollution", "noun", "kirlık, çevre kirliliği")
        rapor = A.denetle(cevap, "pollution", "noun")
        self.assertEqual(cevap.meanings[0].meaning_tr, "çevre kirliliği")
        self.assertIn("turkce_yazim", [s.kod for s in A.yeniden_sorulmali(rapor)])


def karar(*kararlar, gecerli=True, sebep="", eksik=""):
    return K.KontrolCevabi(word_valid=gecerli, word_reason=sebep, missing_meaning=eksik, meanings=[
        {"index": i, "verdict": v, "reason": "gerekçe", "correct_tr": duzeltme,
         "cefr": cefr, "bad_sentences": list(cumle), "bad_collocations": []}
        for i, v, duzeltme, cefr, cumle in kararlar])


class KontrolUygulaTests(SimpleTestCase):

    def cevap(self):
        return anlam_cevabi("pollute", "verb", "kirletmek", "B1")

    def test_dogru_anlam_kalir_seviye_duzelir(self):
        cevap, rapor = self.cevap(), checks.Rapor()
        s = K.uygula(cevap, karar((1, "dogru", "", "C1", ())), "verb", rapor)
        self.assertEqual(s["dogru"], 1)
        self.assertEqual(cevap.meanings[0].cefr, "C1")
        self.assertTrue(rapor.kabul)

    def test_tek_basamak_seviye_farki_yok_sayilir(self):
        """B1 -> B2 zevk meselesi; üreticinin seviyesi kalır."""
        cevap, rapor = self.cevap(), checks.Rapor()
        s = K.uygula(cevap, karar((1, "dogru", "", "B2", ())), "verb", rapor)
        self.assertEqual(cevap.meanings[0].cefr, "B1")
        self.assertEqual(s["cefr_degisti"], 0)

    def test_a_seviyesi_tek_basamak_yukari_kabul(self):
        """Üretici A1-A2'de cömert (overpay A2): yukarı tek basamak da kabul."""
        cevap, rapor = anlam_cevabi("pollute", "verb", "kirletmek", "A2"), checks.Rapor()
        s = K.uygula(cevap, karar((1, "dogru", "", "B1", ())), "verb", rapor)
        self.assertEqual(cevap.meanings[0].cefr, "B1")
        self.assertEqual(s["cefr_degisti"], 1)

    def test_a_seviyesi_asagi_tek_basamak_yok_sayilir(self):
        cevap, rapor = anlam_cevabi("pollute", "verb", "kirletmek", "A2"), checks.Rapor()
        K.uygula(cevap, karar((1, "dogru", "", "A1", ())), "verb", rapor)
        self.assertEqual(cevap.meanings[0].cefr, "A2")

    def test_eksik_anlam_raporlanir_anlam_kalir(self):
        cevap, rapor = self.cevap(), checks.Rapor()
        s = K.uygula(cevap, karar((1, "dogru", "", "B1", ()), eksik="bozmak"), "verb", rapor)
        self.assertEqual(s["eksik"], "bozmak")
        self.assertEqual(len(cevap.meanings), 1)
        self.assertIn("kontrol_eksik_anlam", [u.kod for u in rapor.uyarilar])

    def test_eski_onbellek_cevabi_okunur(self):
        """missing_meaning alanı olmayan eski kontrol cevapları bozulmaz."""
        eski = '{"word_valid": true, "word_reason": "", "meanings": []}'
        self.assertEqual(K.KontrolCevabi.model_validate_json(eski).missing_meaning, "")

    def test_yanlis_karsilik_duzeltilir(self):
        cevap, rapor = self.cevap(), checks.Rapor()
        K.uygula(cevap, karar((1, "karsilik_yanlis", "kirletmek, bozmak", "B1", ())),
                 "verb", rapor)
        self.assertEqual(cevap.meanings[0].meaning_tr, "kirletmek, bozmak")

    def test_denetimden_gecmeyen_duzeltme_anlami_siler(self):
        """Fiile mastarsız karşılık öneren kontrolcüye de güvenilmez."""
        cevap, rapor = self.cevap(), checks.Rapor()
        s = K.uygula(cevap, karar((1, "karsilik_yanlis", "kirlilik", "B1", ())), "verb", rapor)
        self.assertEqual(s["anlam_silindi"], 1)
        self.assertFalse(rapor.kabul)

    def test_anlam_yanlis_silinir(self):
        cevap, rapor = self.cevap(), checks.Rapor()
        s = K.uygula(cevap, karar((1, "anlam_yanlis", "", "B1", ())), "verb", rapor)
        self.assertEqual(cevap.meanings, [])
        self.assertEqual(s["gerekceler"], ["'kirletmek': gerekçe"])

    def test_hatali_cumleler_silinir(self):
        cevap, rapor = self.cevap(), checks.Rapor()
        K.uygula(cevap, karar((1, "dogru", "", "B1", (1, 2))), "verb", rapor)
        self.assertEqual(len(cevap.meanings[0].sentences), 3)

    @mock.patch("words.inflect.tur_sozlukte", return_value=None)
    def test_gecersiz_kelime_reddedilir(self, _):
        cevap, rapor = self.cevap(), checks.Rapor()
        K.uygula(cevap, karar(gecerli=False, sebep="bu türde kullanılmaz"), "verb", rapor)
        self.assertFalse(rapor.kabul)
        self.assertEqual(rapor.hatalar[0].kod, "kontrol_kelime_ret")

    @mock.patch("words.inflect.tur_sozlukte", return_value=True)
    def test_sozlukteki_kelimenin_reddi_yok_sayilir(self, _):
        """5. ölçüm: overthrow (isim), moral (isim) kontrolcü tarafından silindi."""
        cevap, rapor = self.cevap(), checks.Rapor()
        s = K.uygula(cevap, karar((1, "dogru", "", "B1", ()), gecerli=False, sebep="yok"),
                     "verb", rapor)
        self.assertTrue(rapor.kabul)
        self.assertEqual(len(cevap.meanings), 1)
        self.assertTrue(s["sozlukte_var"])
        self.assertIn("kontrol_kelime_ret_yok_sayildi", [u.kod for u in rapor.uyarilar])

    @mock.patch("words.inflect.tur_sozlukte", return_value=True)
    def test_sozlukteki_kelimenin_tum_anlamlari_silinirse_tartismali(self, _):
        cevap, rapor = self.cevap(), checks.Rapor()
        K.uygula(cevap, karar((1, "anlam_yanlis", "", "B1", ())), "verb", rapor)
        self.assertFalse(rapor.kabul)
        self.assertEqual(rapor.hatalar[0].kod, "kontrol_ret_tartismali")

    def test_cumleleri_kotu_anlam_listelenir(self):
        cevap, rapor = self.cevap(), checks.Rapor()
        s = K.uygula(cevap, karar((1, "dogru", "", "B1", (1, 2, 3, 4))), "verb", rapor)
        self.assertEqual(s["cumlesiz"], ["kirletmek"])
        self.assertIn("HATALIYDI", K.eksik_anlam_notu("", s["cumlesiz"]))

    def test_duzeltme_sonrasi_ayni_anlam_atilir(self):
        cevap = anlam_cevabi("pollute", "verb", "kirletmek")
        ikinci = cevap.meanings[0].model_copy(deep=True)
        ikinci.meaning_tr = "bozmak"
        cevap.meanings.append(ikinci)
        rapor = checks.Rapor()
        K.uygula(cevap, karar((1, "dogru", "", "B1", ()),
                              (2, "karsilik_yanlis", "kirletmek", "B1", ())), "verb", rapor)
        self.assertEqual([a.meaning_tr for a in cevap.meanings], ["kirletmek"])

    def test_kontrolcu_duzeltmesindeki_parantez_atilir(self):
        cevap, rapor = self.cevap(), checks.Rapor()
        K.uygula(cevap, karar((1, "karsilik_yanlis", "kirletmek (çevre)", "B1", ())),
                 "verb", rapor)
        self.assertEqual(cevap.meanings[0].meaning_tr, "kirletmek")


class ParantezTests(SimpleTestCase):
    """5. ölçüm: "oynamak (spor, oyun)" mastar değil diye silindi."""

    def test_parantez_ici_atilir(self):
        self.assertEqual(A.parantezsiz("oynamak (spor, oyun)"), "oynamak")
        self.assertEqual(A.parantezsiz("canlandırmak, oynamak (rol/tiyatro)"),
                         "canlandırmak, oynamak")

    def test_bas_harf_kuculur_ozel_ad_kalir(self):
        self.assertEqual(A.parantezsiz("Ayarlayıcı (bir şeyi ayarlayan kişi)"), "ayarlayıcı")
        self.assertEqual(A.parantezsiz("İngiliz Seti"), "İngiliz Seti")

    def test_hassas_anlam_atilir_kelime_kalir(self):
        cevap = anlam_cevabi("pollute", "verb", "kirletmek")
        ikinci = cevap.meanings[0].model_copy(deep=True)
        ikinci.meaning_tr, ikinci.definition = "cinsel oyuncak", "a sex toy"
        cevap.meanings.append(ikinci)
        rapor = A.denetle(cevap, "pollute", "verb")
        self.assertEqual([a.meaning_tr for a in cevap.meanings], ["kirletmek"])
        self.assertIn("hassas_anlam", [u.kod for u in rapor.uyarilar])

    def test_akademik_cinsel_kullanim_hassas_sayilmaz(self):
        cevap = anlam_cevabi("pollution", "noun", "cinsel taciz, taciz")
        cevap.meanings[0].definition = "unwanted sexual behaviour at work"
        self.assertFalse(A.hassas_mi(cevap.meanings[0]))

    def test_tanim_gibi_parca_atilir(self):
        self.assertEqual(A.tanimsiz("yok edici, eleyici, ortadan kaldıran şey veya kimse"),
                         "yok edici, eleyici")
        # Temiz parça yoksa dokunulmaz (karsilik_tanim yeniden sordurur)
        self.assertEqual(A.tanimsiz("şey veya kimse"), "şey veya kimse")

    def test_parantezli_fiil_anlami_korunur(self):
        cevap = anlam_cevabi("pollute", "verb", "kirletmek (çevreyi)")
        rapor = A.denetle(cevap, "pollute", "verb")
        self.assertEqual(cevap.meanings[0].meaning_tr, "kirletmek")
        self.assertIn("parantez_atildi", [u.kod for u in rapor.uyarilar])


class GercekMaliyetTests(SimpleTestCase):

    def test_openrouter_faturasi_okunur(self):
        yakalanan = {}

        class Cevap:
            status_code = 200
            def json(self):
                return {"choices": [{"message": {"content":
                        '{"word_valid": true, "word_reason": "", "missing_meaning": "", '
                        '"meanings": []}'}}],
                        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.0021}}

        def post(url, json=None, **kw):
            yakalanan.update(json)
            return Cevap()
        with override_settings(LLM_BASE_URL="http://x", LLM_MODEL="m"), \
                mock.patch("LearnVocab.llm.requests.post", side_effect=post):
            sonuc = llm.chat_json("s", "u", K.KontrolCevabi, max_retries=0)
        self.assertEqual(yakalanan["usage"], {"include": True})
        self.assertAlmostEqual(sonuc.usage.real_cost, 0.0021)
        toplam = llm.Usage()
        toplam += sonuc.usage
        toplam += sonuc.usage
        self.assertAlmostEqual(toplam.real_cost, 0.0042)


class KontrolPromptTests(SimpleTestCase):

    def test_kontrol_prompti_olcum_listeleriyle_kesismiyor(self):
        from words.aile.deneme import SURUMLER
        metin = prompt.KONTROL_SISTEM.lower()
        kesisen = {k for bek in SURUMLER.values() for b in bek
                   for k in [b["tohum"], *b["kok"]]
                   if re.search(rf"\b{re.escape(k)}\b", metin)}
        self.assertEqual(sorted(kesisen), [])

    @override_settings(LLM_KONTROL_MODEL="m", LLM_KONTROL_REASONING_EFFORT="low")
    def test_kontrolcuye_sicaklik_gonderilmez(self):
        """GPT-5 düşünen modelleri temperature kabul etmiyor (OpenRouter 404)."""
        with mock.patch("LearnVocab.llm.chat_json") as sahte:
            sahte.return_value = "tamam"
            K.sor("pollute", "verb", [], anlam_cevabi("pollute", "verb", "kirletmek").meanings)
        self.assertIs(sahte.call_args.kwargs["sicaklik_gonder"], False)
        self.assertEqual(sahte.call_args.kwargs["reasoning"], "low")
        self.assertEqual(K.kimlik(), "m|low")

    def test_sicaklik_gonder_false_govdeye_girmez(self):
        yakalanan = {}

        class Cevap:
            status_code = 200
            def json(self):
                return {"choices": [{"message": {"content": "{}"}}], "usage": {}}

        def post(url, json=None, **kw):
            yakalanan.update(json)
            return Cevap()
        with override_settings(LLM_BASE_URL="http://x", LLM_MODEL="m"), \
                mock.patch("LearnVocab.llm.requests.post", side_effect=post):
            try:
                llm.chat_json("s", "u", K.KontrolCevabi, sicaklik_gonder=False, max_retries=0)
            except llm.LLMError:
                pass
        self.assertIn("messages", yakalanan)
        self.assertNotIn("temperature", yakalanan)

    def test_kullanici_metni_numarali(self):
        cevap = anlam_cevabi("pollute", "verb", "kirletmek")
        metin = prompt.kontrol_kullanici_metni("pollute", "verb", [("pollution", "noun")],
                                               cevap.meanings)
        self.assertIn("index: 1", metin)
        self.assertIn("    1. Factories pollute", metin)
        self.assertIn("family: pollution (noun)", metin)


def sahte_kontrollu_json(system, user, schema, **kw):
    """Üretici çağrılarını sahte_anlam_json'a, kontrol çağrılarını buraya yönlendirir."""
    if schema is not K.KontrolCevabi:
        return sahte_anlam_json(system, user, schema, **kw)
    assert kw.get("model") == "kontrol-model"
    kelime = re.search(r'word: "([^"]+)"', user).group(1)
    if kelime == "pollute":
        veri = karar((1, "karsilik_yanlis", "kirletmek, pisletmek", "C1", ()))
    else:
        veri = karar((1, "dogru", "", "A2", (5,)))
    return llm.Result(data=veri, raw=veri.model_dump_json(),
                      usage=llm.Usage(prompt_tokens=200, completion_tokens=30, requests=1))


@override_settings(LLM_KONTROL_MODEL="kontrol-model")
class KontrolluDoldurTests(AileDoldurTests.__bases__[0]):
    """aile_doldur, kontrol modeli ayarlıyken."""

    setUp = AileDoldurTests.setUp
    tearDown = AileDoldurTests.tearDown
    calistir = AileDoldurTests.calistir

    @mock.patch("LearnVocab.llm.chat_json", side_effect=sahte_kontrollu_json)
    def test_kontrol_karari_uygulanir(self, sahte):
        from words.models import Word
        cikti = self.calistir()
        anlam = Word.objects.get(text="pollute").meanings.get()
        self.assertEqual(anlam.meaning_tr, "kirletmek, pisletmek")
        self.assertEqual(anlam.cefr, "C1")
        self.assertEqual(Word.objects.get(text="pollution").meanings.get().examples.count(), 4)
        self.assertIn("ÜRETİCİ HATA ORANI (kontrolcüye göre): 1/2", cikti)

    @mock.patch("LearnVocab.llm.chat_json", side_effect=sahte_kontrollu_json)
    def test_kontrol_sonucu_onbellekte(self, sahte):
        self.calistir(dry_run=True)
        ilk = sahte.call_count
        self.calistir()
        self.assertEqual(sahte.call_count, ilk)          # ne üretici ne kontrolcü

    @mock.patch("LearnVocab.llm.chat_json")
    def test_eksik_temel_anlam_bir_kez_yeniden_uretilir(self, sahte):
        sorulan = []

        def yan_etki(system, user, schema, **kw):
            if schema is K.KontrolCevabi:
                kelime = re.search(r'word: "([^"]+)"', user).group(1)
                # pollution her kontrolde "eksik" desin: sonsuz döngü olmamalı
                veri = karar((1, "dogru", "", "B1", ()),
                             eksik="çevre kirliliği" if kelime == "pollution" else "")
                return llm.Result(data=veri, raw=veri.model_dump_json(),
                                  usage=llm.Usage(prompt_tokens=200, completion_tokens=30,
                                                  requests=1))
            sorulan.append(user)
            return sahte_anlam_json(system, user, schema, **kw)
        sahte.side_effect = yan_etki
        cikti = self.calistir(dry_run=True)
        eksikli = [u for u in sorulan if "EKSİKTİ" in u]
        self.assertEqual(len(eksikli), 1)
        self.assertIn('word: "pollution"', eksikli[0])
        self.assertIn("çevre kirliliği", eksikli[0])
        self.assertIn("1 kelime eksik anlam yüzünden yeniden üretildi", cikti)

    @mock.patch("LearnVocab.llm.chat_json")
    def test_kontrol_hatasinda_kelime_yazilmaz(self, sahte):
        from words.models import Word

        def yan_etki(system, user, schema, **kw):
            if schema is K.KontrolCevabi:
                raise llm.LLMUnavailable("servis yok")
            return sahte_anlam_json(system, user, schema, **kw)
        sahte.side_effect = yan_etki
        self.calistir()
        self.assertEqual(Word.objects.count(), 0)


class KontrolKiyasTests(TestCase):
    """--kontrol-model ile iki modelin kararları ayrı depolara yazılır ve kıyaslanır."""

    def setUp(self):
        self.ana = tempfile.mkdtemp()
        AileDoldurTests.setUp(self)          # self.klasor'a aile yazar
        self.depolar = []
        for ad in ("a", "b"):
            hedef = Path(self.ana) / ad
            shutil.copytree(self.klasor, hedef)
            self.depolar.append(str(hedef))

    def tearDown(self):
        shutil.rmtree(self.ana, ignore_errors=True)
        shutil.rmtree(self.klasor, ignore_errors=True)

    def test_iki_model_kiyaslanir(self):
        from words.models import Word

        def model_a(system, user, schema, **kw):
            if schema is K.KontrolCevabi:
                assert kw["model"] == "model-a"
                veri = karar((1, "dogru", "", "B1", ()))
                return llm.Result(data=veri, raw=veri.model_dump_json(),
                                  usage=llm.Usage(prompt_tokens=1000, completion_tokens=100,
                                                  requests=1))
            return sahte_anlam_json(system, user, schema, **kw)

        def model_b(system, user, schema, **kw):
            if schema is K.KontrolCevabi:
                assert kw["model"] == "model-b"
                kelime = re.search(r'word: "([^"]+)"', user).group(1)
                veri = karar((1, "karsilik_yanlis" if kelime == "pollute" else "dogru",
                              "kirletmek, pisletmek", "B1", ()))
                return llm.Result(data=veri, raw=veri.model_dump_json(),
                                  usage=llm.Usage(prompt_tokens=1000, completion_tokens=300,
                                                  requests=1))
            return sahte_anlam_json(system, user, schema, **kw)

        # Önce üretim cevapları (kontrolsüz) ortak depoda; sonra kopyalar
        with mock.patch("LearnVocab.llm.chat_json", side_effect=model_a):
            call_command("aile_doldur", depo=self.depolar[0], dry_run=True, hepsi=True,
                         kontrol_model="model-a", kontrol_fiyat="0.75,3.75", stdout=StringIO())
        shutil.copy(Path(self.depolar[0]) / "anlamlar.jsonl", Path(self.depolar[1]))
        with mock.patch("LearnVocab.llm.chat_json", side_effect=model_b) as sahte:
            call_command("aile_doldur", depo=self.depolar[1], dry_run=True, hepsi=True,
                         kontrol_model="model-b", stdout=StringIO())
            # üretici çağrılmadı, yalnızca kontrolcü (2 kelime)
            self.assertTrue(all(c.args[2] is K.KontrolCevabi for c in sahte.call_args_list))
        self.assertEqual(Word.objects.count(), 0)

        cikti = StringIO()
        call_command("kontrol_kiyasla", depolar=",".join(self.depolar),
                     fiyatlar="0.75,3.75;0.2,1.2", stdout=cikti)
        metin = cikti.getvalue()
        self.assertIn("model-a", metin)
        self.assertIn("ANLAŞMA (model-a|low ↔ model-b|low): 1/2", metin)
        self.assertIn("pollute (verb) · anlam 1", metin)
        self.assertTrue((Path(self.depolar[0]) / "kontrol-kiyas.json").exists())

    def test_hepsi_yalnizca_dry_run_ile(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command("aile_doldur", depo=self.depolar[0], hepsi=True, stdout=StringIO())


class Duzeltme25EylulTests(SimpleTestCase):
    """25 Eylül partisi: haksız reddedilen kelimeleri doğuran üç kusur."""

    def test_duygu_sifatlari_katilim_sayilmaz(self):
        for k in ("confused", "satisfied", "terrified", "relieved", "divorced"):
            self.assertFalse(A.katilim_mi(k, "adjective"), k)
        self.assertTrue(A.katilim_mi("polluted", "adjective"))

    def test_iki_bicimli_gecmis_zaman(self):
        self.assertIn("leapt", checks._bicimler("leap", "verb", "leaped", "leaped"))
        self.assertIn("dreamt", checks._bicimler("dream", "verb", "dreamed", "dreamed"))
        self.assertIn("burned", checks._bicimler("burn", "verb", "burnt", "burnt"))

    def test_bitisik_birlesik_kelime(self):
        if not turkce.hazir_mi():
            self.skipTest("Türkçe sözlük yok")
        self.assertEqual(turkce.bilinmeyenler("köpekbalığı, gökkuşağı"), [])
        self.assertEqual(turkce.bilinmeyenler("teşeksiz kirlık"), ["teşeksiz", "kirlık"])

    def test_tekilin_cogulu_ayri_kelime_olmaz(self):
        cevap = anlam_cevabi("pollution", "noun", "kirlilikler")
        rapor = A.denetle(cevap, "pollutions", "noun")
        self.assertFalse(rapor.kabul)
        self.assertEqual(rapor.hatalar[0].kod, "cogul_cekimi")

    def test_hassas_anlam_yakalanir(self):
        from types import SimpleNamespace as N
        self.assertTrue(A.hassas_mi(N(meaning_tr="cinsel isteği artmış", definition="")))
        self.assertTrue(A.hassas_mi(N(meaning_tr="striptiz yapan kişi", definition="")))
        self.assertFalse(A.hassas_mi(N(meaning_tr="cinsel taciz", definition="sexual harassment")))

    def test_kontrolcu_cogul_retti_gecerli(self):
        from words.aile.kontrol import _tekilin_cogulu
        self.assertTrue(_tekilin_cogulu("participants"))
        self.assertTrue(_tekilin_cogulu("guidelines"))
        for k in ("news", "physics", "glasses", "stairs", "series", "class"):
            self.assertFalse(_tekilin_cogulu(k), k)
