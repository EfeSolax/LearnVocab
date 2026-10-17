"""
Yazma bölümü testleri (ürün raporu 9).

Gerçek Gemini çağrısı YAPILMAZ: `LearnVocab.gemini.generate` ya da istemci
mock'lanır (başarılı JSON, bozuk JSON, kota hatası, yeniden deneme).
"""

import json
from datetime import timedelta
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from LearnVocab import gemini
from texts import degerlendirme as dg
from texts import diyalog as dy
from texts import limits, sinyaller
from texts.models import (
    Diyalog, DiyalogCevabi, Sertlik, Text, YaziDurumu, YaziTuru, YazmaAyari,
)
from texts.views import _degerlendirme_isi
from users.models import User
from words.models import Meaning, UserWordLink, Word, WordFamily

TEST_MODEL = "gemini-test-model"
FALLBACK_MODEL = "gemini-test-fallback"

# Varsayılan: tekrar deneme yok, yedek model yok, bekleme yok, yoğunluk
# sınırı kapalı (sayaç süreçler arası paylaşılan cache'te; paralel testler
# birbirini etkilemesin).
HIZLI = dict(
    GEMINI_API_TOKEN="dummy-key",
    GEMINI_MODEL=TEST_MODEL,
    GEMINI_FALLBACK_MODELS=[],
    GEMINI_MAX_RETRIES=0,
    GEMINI_RETRY_BACKOFF_SECONDS=0,
    GEMINI_TIMEOUT_SECONDS=5,
    GEMINI_MIN_SECONDS_BETWEEN_REQUESTS=0,
    YAZMA_DAKIKADA_EN_COK=0,
    TEXT_DAILY_LIMIT=0,
)

METIN = (
    "Last weekend I visit my grandmother in Izmir. "
    "We cooked dinner together and she told me old stories. "
    "I decided to postpone my homework because the day was so nice. "
    "It was a lovely weekend."
)


def cevap(veri):
    """generate() dönüşünü taklit eder: .text içinde model çıktısı."""
    nesne = MagicMock()
    nesne.text = veri if isinstance(veri, str) else json.dumps(veri, ensure_ascii=False)
    return nesne


def iyi_cevap(**ek):
    veri = {
        "puan": 3.5,
        "iyi": [{"alinti": "We cooked dinner together",
                 "aciklama": "Geçmiş zamanı doğru kullanıp olayı akıcı anlatmışsın."}],
        "hatalar": [{"alinti": "I visit my grandmother",
                     "dogrusu": "I visited my grandmother",
                     "neden": "Geçmişte olan bir olay için fiilin geçmiş hâli kullanılır."}],
        "kullanilan_kelimeler": ["postpone"],
    }
    veri.update(ek)
    return veri


def kelime_olustur(text, pos="verb", anlam="", v2=None, v3=None):
    aile, _ = WordFamily.objects.get_or_create(root=f"{text}-{pos}")
    kelime = Word.objects.create(family=aile, text=text, pos=pos, v2Form=v2, v3Form=v3, cefr="B1")
    if anlam:
        Meaning.objects.create(word=kelime, meaning_tr=anlam)
    return kelime


def diyalog_olustur(kelime, cevap_="postponed", denetlendi=True, **ek):
    satirlar = [
        {"kisi": "A", "metin": "Are we still meeting on Friday?"},
        {"kisi": "B", "metin": f"No, the manager {Diyalog.BOSLUK} it until next week."},
        {"kisi": "A", "metin": "Oh, why?"},
        {"kisi": "B", "metin": "Half of the team is away."},
    ]
    return Diyalog.objects.create(
        word=kelime, satirlar=satirlar, cevap=cevap_, ipucu="ertelemek",
        denetlendi=denetlendi, anahtar=f"{kelime.pk}-{cevap_}-{Diyalog.objects.count()}", **ek)


# ===========================================================================
# Prompt
# ===========================================================================

class PromptTests(TestCase):
    def test_contains_text_words_and_topic(self):
        p = dg.prompt_olustur("My text here.", Sertlik.NORMAL, ["aim", "decide"], "Hafta sonum")
        self.assertIn("My text here.", p)
        self.assertIn("aim, decide", p)
        self.assertIn("Hafta sonum", p)
        self.assertIn("Write about what you did last weekend.", p)

    def test_changes_with_severity(self):
        nazik = dg.prompt_olustur("x", Sertlik.NAZIK)
        normal = dg.prompt_olustur("x", Sertlik.NORMAL)
        titiz = dg.prompt_olustur("x", Sertlik.TITIZ)
        self.assertEqual(len({nazik, normal, titiz}), 3)
        self.assertIn("SERTLİK: NAZİK", nazik)
        self.assertIn("ANLAMI BOZAN", nazik)
        self.assertIn("En çok 3", nazik)
        self.assertIn("SERTLİK: NORMAL", normal)
        self.assertIn("En çok 6", normal)
        self.assertIn("SERTLİK: TİTİZ", titiz)
        self.assertIn("noktalama", titiz)

    def test_unknown_severity_falls_back_to_normal(self):
        self.assertIn("SERTLİK: NORMAL", dg.prompt_olustur("x", "cok-sert"))

    def test_score_bands_are_the_same_for_every_severity(self):
        bant = "3.5 = ortalama"
        for s in Sertlik.values:
            with self.subTest(sertlik=s):
                self.assertIn(bant, dg.prompt_olustur("x", s))

    def test_asks_for_json_in_turkish_without_old_rubric(self):
        p = dg.prompt_olustur("x")
        for parca in ('"puan"', '"iyi"', '"hatalar"', '"kullanilan_kelimeler"', "TÜRKÇE"):
            self.assertIn(parca, p)
        for eski in ("major", "minor", "100 puan", "summary", "Geliştirilebilir\":"):
            self.assertNotIn(eski, p)
        self.assertIn("Üslup tercihi", p)


class AkademikPromptTests(TestCase):
    """Akademik tür (Efe, 17 Ekim; Forefront kriterleri)."""

    def test_akademik_prompt_kurallari_ve_konusu(self):
        p = dg.prompt_olustur("x", Sertlik.NORMAL, [], "Zorunlu İngilizce", tur=YaziTuru.AKADEMIK)
        for parca in ("AKADEMİK", "A1. Kısaltmalar", "I argue that", "Mantık hataları", "AKADEMİK yazı ölçütüne",
                      "En çok 8", "Should English be a compulsory subject"):
            self.assertIn(parca, p)
        self.assertNotIn("Akademik yazı BEKLENMİYOR", p)
        self.assertNotIn("YALNIZCA GERÇEK HATALAR", p)

    def test_gunluk_prompt_akademik_kural_icermez(self):
        p = dg.prompt_olustur("x", Sertlik.NORMAL, tur=YaziTuru.GUNLUK)
        self.assertIn("Akademik yazı BEKLENMİYOR", p)
        self.assertNotIn("A1. Kısaltmalar", p)
        self.assertEqual(p, dg.prompt_olustur("x", Sertlik.NORMAL, tur="bilinmeyen"))

    def test_hata_siniri_ture_gore(self):
        hatalar = [{"alinti": f"word{i}", "dogrusu": f"fixed{i}", "neden": "n"} for i in range(15)]
        metin = " ".join(f"word{i}" for i in range(15))
        veri = {"puan": 3, "iyi": [], "hatalar": hatalar}
        self.assertEqual(len(dg.cevabi_coz(veri, metin, Sertlik.TITIZ)["hatalar"]), 10)
        self.assertEqual(len(dg.cevabi_coz(veri, metin, Sertlik.TITIZ, tur=YaziTuru.AKADEMIK)["hatalar"]), 12)
        self.assertEqual(len(dg.cevabi_coz(veri, metin, Sertlik.NAZIK, tur=YaziTuru.AKADEMIK)["hatalar"]), 4)


# ===========================================================================
# Cevabın doğrulanması
# ===========================================================================

class PuanYuvarlaTests(TestCase):
    def test_half_steps(self):
        for girdi, beklenen in ((3.2, 3.0), (3.25, 3.5), (3.74, 3.5), (3.75, 4.0),
                                (4.5, 4.5), (2, 2.0)):
            with self.subTest(girdi=girdi):
                self.assertEqual(dg.puan_yuvarla(girdi), beklenen)

    def test_clamped_to_one_and_five(self):
        self.assertEqual(dg.puan_yuvarla(0.3), 1.0)
        self.assertEqual(dg.puan_yuvarla(7), 5.0)

    def test_string_scores_are_read(self):
        self.assertEqual(dg.cevabi_coz({**iyi_cevap(), "puan": "3,5"}, METIN)["puan"], 3.5)
        self.assertEqual(dg.cevabi_coz({**iyi_cevap(), "puan": "4/5"}, METIN)["puan"], 4.0)
        self.assertEqual(dg.cevabi_coz({**iyi_cevap(), "puan": 12}, METIN)["puan"], 5.0)

    def test_score_label_and_text(self):
        self.assertEqual(dg.puan_yazisi(3.5), "3,5")
        self.assertEqual(dg.puan_yazisi(4.0), "4")
        self.assertEqual(dg.puan_etiketi(3.5), "Ortalama")
        self.assertEqual(dg.puan_etiketi(5.0), "Çok iyi")


class CevabiCozTests(TestCase):
    def test_valid_json(self):
        s = dg.cevabi_coz(json.dumps(iyi_cevap()), METIN)
        self.assertEqual(s["puan"], 3.5)
        self.assertEqual(len(s["iyi"]), 1)
        self.assertEqual(s["hatalar"][0]["dogrusu"], "I visited my grandmother")

    def test_json_inside_prose_and_code_fence(self):
        ham = "Tabii! İşte sonuç:\n```json\n" + json.dumps(iyi_cevap()) + "\n```\nBaşarılar."
        self.assertEqual(dg.cevabi_coz(ham, METIN)["puan"], 3.5)

    def test_non_json_raises(self):
        for ham in ("Bu metin güzel.", "", "{bozuk json", "[1, 2]"):
            with self.subTest(ham=ham):
                with self.assertRaises(dg.GecersizCevap):
                    dg.cevabi_coz(ham, METIN)

    def test_missing_score_raises(self):
        veri = iyi_cevap()
        del veri["puan"]
        with self.assertRaises(dg.GecersizCevap):
            dg.cevabi_coz(veri, METIN)
        with self.assertRaises(dg.GecersizCevap):
            dg.cevabi_coz({**iyi_cevap(), "puan": "harika"}, METIN)

    def test_missing_lists_are_tolerated(self):
        s = dg.cevabi_coz({"puan": 4}, METIN)
        self.assertEqual((s["iyi"], s["hatalar"]), ([], []))

    def test_quote_not_in_text_is_dropped(self):
        veri = iyi_cevap(hatalar=[
            {"alinti": "she go to market", "dogrusu": "she goes to market", "neden": "Uydurma."},
            {"alinti": "I visit my grandmother", "dogrusu": "I visited my grandmother", "neden": "Geçmiş zaman."},
        ], iyi=[{"alinti": "not in the text", "aciklama": "x"}])
        s = dg.cevabi_coz(veri, METIN)
        self.assertEqual([h["alinti"] for h in s["hatalar"]], ["I visit my grandmother"])
        self.assertEqual(s["iyi"], [])

    def test_incomplete_items_are_dropped(self):
        veri = iyi_cevap(hatalar=[
            {"alinti": "I visit my grandmother", "dogrusu": "", "neden": "x"},
            {"alinti": "I visit my grandmother", "dogrusu": "I visited"},
            "düz metin",
            {"alinti": "so nice", "dogrusu": "so nice", "neden": "Aynı; hata değil."},
        ])
        self.assertEqual(dg.cevabi_coz(veri, METIN)["hatalar"], [])

    def test_quote_is_taken_from_the_text(self):
        veri = iyi_cevap(hatalar=[{"alinti": "i  VISIT my grandmother", "dogrusu": "I visited my grandmother",
                                   "neden": "Geçmiş zaman."}])
        self.assertEqual(dg.cevabi_coz(veri, METIN)["hatalar"][0]["alinti"], "I visit my grandmother")

    def test_duplicate_errors_are_merged(self):
        h = {"alinti": "I visit my grandmother", "dogrusu": "I visited my grandmother", "neden": "x"}
        self.assertEqual(len(dg.cevabi_coz(iyi_cevap(hatalar=[h, h]), METIN)["hatalar"]), 1)

    def test_error_count_is_capped_by_severity(self):
        metin = " ".join(f"word{i} is wrong." for i in range(12))
        hatalar = [{"alinti": f"word{i} is", "dogrusu": f"word{i} are", "neden": "x"} for i in range(12)]
        veri = {"puan": 3, "iyi": [], "hatalar": hatalar}
        self.assertEqual(len(dg.cevabi_coz(veri, metin, Sertlik.NAZIK)["hatalar"]), 3)
        self.assertEqual(len(dg.cevabi_coz(veri, metin, Sertlik.NORMAL)["hatalar"]), 6)
        self.assertEqual(len(dg.cevabi_coz(veri, metin, Sertlik.TITIZ)["hatalar"]), 10)

    def test_good_points_are_capped_at_four(self):
        iyi = [{"alinti": "It was a lovely weekend", "aciklama": f"açıklama {i}"} for i in range(6)]
        self.assertEqual(len(dg.cevabi_coz(iyi_cevap(iyi=iyi), METIN)["iyi"]), 4)

    def test_zero_score_means_not_evaluable(self):
        self.assertEqual(dg.cevabi_coz({"puan": 0, "iyi": [], "hatalar": []}, "asdf"), {"uygun_degil": True})

    def test_markdown_is_stripped_from_fields(self):
        veri = iyi_cevap(hatalar=[{"alinti": "I visit my grandmother", "dogrusu": "**I visited my grandmother**",
                                   "neden": "`Geçmiş` zaman."}])
        h = dg.cevabi_coz(veri, METIN)["hatalar"][0]
        self.assertEqual((h["dogrusu"], h["neden"]), ("I visited my grandmother", "Geçmiş zaman."))

    def test_used_words_come_from_suggestions_and_inflections(self):
        postpone = kelime_olustur("postpone")
        decide = kelime_olustur("decide")
        aim = kelime_olustur("aim")
        # Model "aim" dese de metinde yok ama öneride var -> modelin sözü alınır;
        # "decide" modelin listesinde yok ama "decided" metinde geçiyor.
        s = dg.cevabi_coz(iyi_cevap(kullanilan_kelimeler=["postpone", "unrelated"]),
                          METIN, kelimeler=[postpone, decide, aim])
        self.assertEqual(s["kullanilan_kelimeler"], ["postpone", "decide"])


class AlintiVeParcalarTests(TestCase):
    def test_find_is_forgiving_and_returns_first(self):
        metin = "It’s fine. it's fine again."
        self.assertEqual(dg.alinti_bul(metin, "it's fine"), (0, 9))
        self.assertIsNone(dg.alinti_bul(metin, "not here"))
        self.assertIsNone(dg.alinti_bul(metin, ""))

    def test_segments_underline_errors(self):
        hatalar = [{"alinti": "I visit my grandmother"}, {"alinti": "so nice"}]
        parcalar = dg.metin_parcalari(METIN, hatalar)
        self.assertEqual("".join(p["metin"] for p in parcalar), METIN)
        cizili = [(p["metin"], p["hata"]) for p in parcalar if p["hata"] is not None]
        self.assertEqual(cizili, [("I visit my grandmother", 0), ("so nice", 1)])

    def test_repeated_quote_underlines_the_first(self):
        metin = "He go home. He go school."
        parcalar = dg.metin_parcalari(metin, [{"alinti": "He go"}])
        self.assertEqual(parcalar[0], {"metin": "He go", "hata": 0})
        self.assertEqual(sum(1 for p in parcalar if p["hata"] is not None), 1)

    def test_overlapping_quotes_are_not_drawn_twice(self):
        metin = "I visit my grandmother yesterday."
        parcalar = dg.metin_parcalari(metin, [{"alinti": "visit my"}, {"alinti": "my grandmother"}])
        self.assertEqual([p["hata"] for p in parcalar if p["hata"] is not None], [0])
        self.assertEqual("".join(p["metin"] for p in parcalar), metin)


# ===========================================================================
# Değerlendirme (Gemini mock'lu)
# ===========================================================================

@override_settings(**HIZLI)
class DegerlendirTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="yazar", password="Sifre1234")

    def _yazi(self, **ek):
        return Text.objects.create(owner=self.user, content=METIN, **ek)

    def test_success_saves_feedback(self):
        yazi = self._yazi(sertlik=Sertlik.NAZIK)
        with patch("LearnVocab.gemini.generate", return_value=cevap(iyi_cevap(puan=3.3))) as gen:
            self.assertEqual(dg.degerlendir(yazi), dg.TAMAM)
        yazi.refresh_from_db()
        self.assertEqual(yazi.durum, YaziDurumu.TAMAM)
        self.assertEqual(yazi.puan, 3.5)
        self.assertEqual(len(yazi.geri_bildirim["hatalar"]), 1)
        self.assertIn("Puan: 3,5 / 5", yazi.response)
        self.assertIs(gen.call_args.kwargs["response_schema"], dg.DegerlendirmeSemasi)
        self.assertIn("SERTLİK: NAZİK", gen.call_args.args[0])

    def test_quota_keeps_text_waiting(self):
        yazi = self._yazi()
        with patch("LearnVocab.gemini.generate", side_effect=gemini.GeminiRateLimit("429")):
            self.assertEqual(dg.degerlendir(yazi), dg.KOTA)
        yazi.refresh_from_db()
        self.assertEqual(yazi.durum, YaziDurumu.BEKLIYOR)
        self.assertEqual(yazi.deneme_sayisi, 1)
        self.assertIsNotNone(yazi.son_deneme)

    def test_broken_json_keeps_text_waiting(self):
        yazi = self._yazi()
        with patch("LearnVocab.gemini.generate", return_value=cevap("Harika bir metin!")):
            with self.assertLogs("texts.degerlendirme", level="WARNING"):
                self.assertEqual(dg.degerlendir(yazi), dg.BOZUK)
        self.assertEqual(Text.objects.get(pk=yazi.pk).durum, YaziDurumu.BEKLIYOR)

    def test_unavailable_and_unconfigured(self):
        yazi = self._yazi()
        with patch("LearnVocab.gemini.generate", side_effect=gemini.GeminiUnavailable("503")):
            self.assertEqual(dg.degerlendir(yazi), dg.SERVIS)
        with patch("LearnVocab.gemini.generate", side_effect=gemini.GeminiUnconfigured("yok")):
            self.assertEqual(dg.degerlendir(yazi), dg.YAPILANDIRMA)

    def test_not_evaluable(self):
        yazi = self._yazi()
        with patch("LearnVocab.gemini.generate", return_value=cevap({"puan": 0, "iyi": [], "hatalar": []})):
            self.assertEqual(dg.degerlendir(yazi), dg.UYGUN_DEGIL)
        self.assertEqual(Text.objects.get(pk=yazi.pk).durum, YaziDurumu.UYGUN_DEGIL)

    def test_hook_is_called_on_completion(self):
        yazi = self._yazi()
        alinan = []

        def alici(sender, yazi, arka_planda, **kw):
            alinan.append((yazi.pk, arka_planda))

        sinyaller.yazi_degerlendirildi.connect(alici)
        try:
            with patch("LearnVocab.gemini.generate", return_value=cevap(iyi_cevap())):
                dg.degerlendir(yazi, arka_planda=True)
        finally:
            sinyaller.yazi_degerlendirildi.disconnect(alici)
        self.assertEqual(alinan, [(yazi.pk, True)])

    def test_already_evaluated_text_is_not_sent_again(self):
        yazi = self._yazi(durum=YaziDurumu.TAMAM, puan=4)
        with patch("LearnVocab.gemini.generate") as gen:
            self.assertEqual(dg.degerlendir(yazi), dg.TAMAM)
        gen.assert_not_called()

    @override_settings(YAZMA_DAKIKADA_EN_COK=1,
                       CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                                           "LOCATION": "yazma-yogunluk"}})
    def test_busy_minute_does_not_call_gemini(self):
        limits.yogunluk_sifirla()
        with patch("LearnVocab.gemini.generate", return_value=cevap(iyi_cevap())) as gen:
            self.assertEqual(dg.degerlendir(self._yazi()), dg.TAMAM)
            self.assertTrue(limits.yogun_mu())
            ikinci = self._yazi()
            self.assertEqual(dg.degerlendir(ikinci), dg.YOGUN)
        self.assertEqual(gen.call_count, 1)
        self.assertEqual(Text.objects.get(pk=ikinci.pk).durum, YaziDurumu.BEKLIYOR)
        limits.yogunluk_sifirla()


def sahte_istemci(cevaplar):
    istemci = MagicMock()

    def yan_etki(*args, **kwargs):
        oge = cevaplar.pop(0)
        if isinstance(oge, Exception):
            raise oge
        return cevap(oge)

    istemci.models.generate_content.side_effect = yan_etki
    return istemci


@override_settings(**{**HIZLI, "GEMINI_FALLBACK_MODELS": [FALLBACK_MODEL], "GEMINI_MAX_RETRIES": 1})
class GeminiKatmaniTests(TestCase):
    """Gerçek gemini.generate + sahte istemci: tekrar deneme ve yedek model."""

    def setUp(self):
        self.user = User.objects.create_user(username="katman", password="Sifre1234")
        self.yazi = Text.objects.create(owner=self.user, content=METIN)

    def _modeller(self, istemci):
        return [c.kwargs["model"] for c in istemci.models.generate_content.call_args_list]

    def test_transient_error_is_retried_then_succeeds(self):
        istemci = sahte_istemci([Exception("503 UNAVAILABLE"), iyi_cevap()])
        with patch("LearnVocab.gemini.get_client", return_value=istemci):
            with self.assertLogs("LearnVocab.gemini", level="WARNING"):
                self.assertEqual(dg.degerlendir(self.yazi), dg.TAMAM)
        self.assertEqual(self._modeller(istemci), [TEST_MODEL, TEST_MODEL])

    def test_falls_back_to_next_model(self):
        hata = Exception("503 UNAVAILABLE")
        istemci = sahte_istemci([hata, hata, iyi_cevap()])
        with patch("LearnVocab.gemini.get_client", return_value=istemci):
            with self.assertLogs("LearnVocab.gemini", level="WARNING"):
                self.assertEqual(dg.degerlendir(self.yazi), dg.TAMAM)
        self.assertEqual(self._modeller(istemci), [TEST_MODEL, TEST_MODEL, FALLBACK_MODEL])

    def test_quota_tries_fallback_model(self):
        # Ücretsiz katmanda günlük kota model başına: asıl model doluysa yedek denenir (tekrar denemeden)
        istemci = sahte_istemci([Exception("429 RESOURCE_EXHAUSTED"), iyi_cevap()])
        with patch("LearnVocab.gemini.get_client", return_value=istemci):
            with self.assertLogs("LearnVocab.gemini", level="WARNING"):
                self.assertEqual(dg.degerlendir(self.yazi), dg.TAMAM)
        self.assertEqual(self._modeller(istemci), [TEST_MODEL, FALLBACK_MODEL])

    def test_quota_on_every_model(self):
        istemci = sahte_istemci([Exception("429 RESOURCE_EXHAUSTED"), Exception("429 RESOURCE_EXHAUSTED")])
        with patch("LearnVocab.gemini.get_client", return_value=istemci):
            with self.assertLogs("LearnVocab.gemini", level="WARNING"):
                self.assertEqual(dg.degerlendir(self.yazi), dg.KOTA)
        self.assertEqual(self._modeller(istemci), [TEST_MODEL, FALLBACK_MODEL])

    def test_missing_key_keeps_text(self):
        with override_settings(GEMINI_API_TOKEN=None):
            with self.assertLogs("LearnVocab.gemini", level="ERROR"):
                self.assertEqual(dg.degerlendir(self.yazi), dg.YAPILANDIRMA)
        self.assertEqual(Text.objects.get(pk=self.yazi.pk).durum, YaziDurumu.BEKLIYOR)


# ===========================================================================
# Sayfalar
# ===========================================================================

@override_settings(**HIZLI)
class YazmaSayfalariTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="yazar", password="Sifre1234")
        self.client.login(username="yazar", password="Sifre1234")

    def _gonder(self, **ek):
        veri = {"user_text": METIN, "sertlik": "normal", **ek}
        return self.client.post(reverse("create_text"), veri)

    def test_guest_sees_login_gate(self):
        self.client.logout()
        # Yazılar ana sayfası ve diyalog misafire açık (rapor 18.3); serbest yazma kapalı.
        for ad, argumanlar in (("new_text_page", []), ("review_text", [1]), ("about_grading_page", [])):
            with self.subTest(sayfa=ad):
                html = self.client.get(reverse(ad, args=argumanlar)).content.decode()
                self.assertIn("önce giriş yapın", html)
        html = self.client.get(reverse("profile_texts")).content.decode()
        self.assertIn("data-misafir-yazilar", html)
        self.assertIn("yapay zekâ ile değerlendirilmesini istiyorsan", html)
        self.assertNotIn(reverse("new_text_page"), html.split("<main")[1])
        yanit = self.client.post(reverse("create_text"), {"user_text": METIN})
        self.assertEqual(yanit.status_code, 302)
        self.assertIn(reverse("login"), yanit["Location"])
        self.assertFalse(Text.objects.exists())

    def test_new_text_page_offers_topics_words_and_severity(self):
        kelime = kelime_olustur("postpone", anlam="ertelemek")
        UserWordLink.objects.create(user=self.user, word=kelime)
        YazmaAyari.objects.create(user=self.user, sertlik=Sertlik.TITIZ)
        html = self.client.get(reverse("new_text_page")).content.decode()
        self.assertIn("Kullanmayı dene", html)
        self.assertIn("postpone", html)
        self.assertIn("ertelemek", html)
        self.assertIn("Hafta sonum", html)  # konu listesi (json_script)
        self.assertIn('value="titiz" class="peer sr-only" checked', html)

    def test_suggestions_are_three_to_five_from_the_list(self):
        from texts.views import kullanmayi_dene
        for i in range(8):
            UserWordLink.objects.create(user=self.user, word=kelime_olustur(f"word{i}"))
        oneriler = kullanmayi_dene(self.user)
        self.assertEqual(len(oneriler), 5)
        self.assertEqual(len({k.id for k in oneriler}), 5)

    def test_successful_submission_shows_underlined_review(self):
        kelime = kelime_olustur("postpone")
        UserWordLink.objects.create(user=self.user, word=kelime)
        with patch("LearnVocab.gemini.generate", return_value=cevap(iyi_cevap())):
            yanit = self._gonder(konu="hafta-sonu", sertlik="nazik", kelimeler=[str(kelime.id), "999999"])
        yazi = Text.objects.get()
        self.assertRedirects(yanit, reverse("review_text", args=[yazi.id]))
        self.assertEqual((yazi.durum, yazi.sertlik, yazi.konu), ("tamam", "nazik", "Hafta sonum"))
        self.assertEqual(list(yazi.words.all()), [kelime])
        self.assertEqual(YazmaAyari.sertlik_of(self.user), "nazik")

        html = self.client.get(reverse("review_text", args=[yazi.id])).content.decode()
        self.assertIn('data-hata="0"', html)
        self.assertRegex(html, r'data-hata="0"[^>]*>I visit my grandmother</button>')
        self.assertIn("I visited my grandmother", html)
        self.assertIn("İyi yaptıkların", html)
        self.assertIn("3,5", html)
        self.assertIn("Ortalama", html)
        self.assertNotIn("Geliştirilebilir", html)

    def test_akademik_tur_kaydedilir_uzun_metin_kabul_ve_etiket(self):
        uzun = (METIN + " ") * 10
        self.assertTrue(1500 < len(uzun.strip()) < 3000)
        with patch("LearnVocab.gemini.generate") as gen:
            self._gonder(user_text=uzun)               # günlükte uzun metin reddedilir
        gen.assert_not_called()
        self.assertFalse(Text.objects.exists())
        with patch("LearnVocab.gemini.generate", return_value=cevap(iyi_cevap())) as gen:
            self._gonder(user_text=uzun, tur="akademik", konu="a-ingilizce")
        yazi = Text.objects.get()
        self.assertEqual((yazi.tur, yazi.konu), (YaziTuru.AKADEMIK, "Zorunlu İngilizce"))
        self.assertIn("A1. Kısaltmalar", gen.call_args.args[0])
        self.assertEqual(gen.call_args.kwargs["timeout"], dg.AKADEMIK_ZAMAN_ASIMI)
        html = self.client.get(reverse("review_text", args=[yazi.id])).content.decode()
        self.assertIn("data-akademik", html)
        self.assertIn("akademik puan", html)
        self.assertIn("Akademik", self.client.get(reverse("profile_texts")).content.decode())

    def test_yazma_ekraninda_tur_secimi_ayarda_yok(self):
        html = self.client.get(reverse("new_text_page")).content.decode()
        self.assertIn("data-yazi-turu", html)
        self.assertIn('name="tur" value="akademik"', html)
        self.assertIn("Should English be a compulsory subject", html)   # akademik konular sayfada
        self.assertNotIn("akademik", self.client.get(reverse("settings_page")).content.decode().lower())

    def test_short_or_empty_text_is_rejected_without_calling_gemini(self):
        with patch("LearnVocab.gemini.generate") as gen:
            self._gonder(user_text="Hi.")
        gen.assert_not_called()
        self.assertFalse(Text.objects.exists())

    def test_quota_then_command_retry_removes_yellow_label(self):
        with patch("LearnVocab.gemini.generate", side_effect=gemini.GeminiRateLimit("429")):
            yanit = self._gonder()
        yazi = Text.objects.get()
        self.assertEqual(yazi.durum, YaziDurumu.BEKLIYOR)
        self.assertRedirects(yanit, reverse("review_text", args=[yazi.id]), fetch_redirect_response=False)

        liste = self.client.get(reverse("profile_texts")).content.decode()
        self.assertIn("Henüz değerlendirilmedi", liste)
        self.assertIn('data-etiket="bekliyor"', liste)
        inceleme = self.client.get(reverse("review_text", args=[yazi.id])).content.decode()
        self.assertIn("Henüz değerlendirilmedi", inceleme)
        self.assertIn(METIN, inceleme)

        # Arka plan: cron komutu. Son denemenin üzerinden süre geçmiş olsun.
        Text.objects.filter(pk=yazi.pk).update(son_deneme=timezone.now() - timedelta(hours=1))
        alinan = []
        sinyaller.yazi_degerlendirildi.connect(lambda sender, yazi, arka_planda, **kw: alinan.append(arka_planda),
                                               weak=False, dispatch_uid="test-yazma")
        try:
            with patch("LearnVocab.gemini.generate", return_value=cevap(iyi_cevap())):
                call_command("yazilari_yeniden_dene", stdout=StringIO())
        finally:
            sinyaller.yazi_degerlendirildi.disconnect(dispatch_uid="test-yazma")

        yazi.refresh_from_db()
        self.assertEqual(yazi.durum, YaziDurumu.TAMAM)
        self.assertEqual(alinan, [True])
        liste = self.client.get(reverse("profile_texts")).content.decode()
        self.assertNotIn("Henüz değerlendirilmedi", liste)
        self.assertIn("3,5", liste)

    def test_retry_button(self):
        yazi = Text.objects.create(owner=self.user, content=METIN)
        with patch("LearnVocab.gemini.generate", return_value=cevap(iyi_cevap())):
            yanit = self.client.post(reverse("retry_text", args=[yazi.id]))
        self.assertRedirects(yanit, reverse("review_text", args=[yazi.id]))
        self.assertEqual(Text.objects.get(pk=yazi.pk).durum, YaziDurumu.TAMAM)

    def test_ajax_job_flow(self):
        with patch("texts.views.threading.Thread") as thread:
            yanit = self.client.post(reverse("create_text"), {"user_text": METIN},
                                     HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        job_id = yanit.json()["job_id"]
        thread.return_value.start.assert_called_once()
        yazi = Text.objects.get()
        self.assertEqual(yazi.durum, YaziDurumu.BEKLIYOR)  # kaydedildi, kaybolmaz

        with patch("LearnVocab.gemini.generate", side_effect=gemini.GeminiRateLimit("429")), \
                patch("django.db.connection.close"):
            _degerlendirme_isi(job_id, yazi.id)
        bitis = self.client.post(reverse("create_text_finish", args=[job_id]),
                                 HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(bitis.json()["redirect"], reverse("review_text", args=[yazi.id]))

    def test_old_records_are_shown_as_old_evaluation(self):
        eski = Text.objects.create(owner=self.user, content="Old academic essay.", score=72,
                                   scores="[8,22,3,9,6,16,3,2,2,1]", response="Konu: 8/10 ...",
                                   durum=YaziDurumu.ESKI)
        liste = self.client.get(reverse("profile_texts")).content.decode()
        self.assertIn("Eski değerlendirme · 72/100", liste)
        html = self.client.get(reverse("review_text", args=[eski.id])).content.decode()
        self.assertIn("Eski değerlendirme", html)
        self.assertIn("72/100", html)
        self.assertIn("Konu: 8/10", html)

    def test_other_users_text_is_hidden(self):
        baska = User.objects.create_user(username="baska", password="Sifre1234")
        yazi = Text.objects.create(owner=baska, content=METIN)
        self.assertEqual(self.client.get(reverse("review_text", args=[yazi.id])).status_code, 404)

    def test_delete_with_undo(self):
        yazi = Text.objects.create(owner=self.user, content=METIN, durum=YaziDurumu.TAMAM, puan=4)
        yanit = self.client.post(reverse("remove_text", args=[yazi.id]))
        self.assertRedirects(yanit, f"{reverse('profile_texts')}?silindi={yazi.id}")
        liste = self.client.get(yanit["Location"]).content.decode()
        self.assertIn("Yazı silindi", liste)
        self.assertIn(reverse("restore_text", args=[yazi.id]), liste)
        self.assertEqual(self.client.get(reverse("review_text", args=[yazi.id])).status_code, 404)

        self.client.post(reverse("restore_text", args=[yazi.id]))
        self.assertIsNone(Text.objects.get(pk=yazi.pk).silindi)

    def test_grading_page_describes_new_system(self):
        html = self.client.get(reverse("about_grading_page")).content.decode()
        self.assertIn("5 üzerinden", html)
        self.assertNotIn("/100", html)


# ===========================================================================
# Günlük sınır
# ===========================================================================

@override_settings(**{**HIZLI, "TEXT_DAILY_LIMIT": 2})
class GunlukSinirTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="sinir", password="Sifre1234")
        self.client.login(username="sinir", password="Sifre1234")

    def test_limit_counts_todays_texts(self):
        self.assertEqual(limits.kalan_hak(self.user), 2)
        Text.objects.create(owner=self.user, content=METIN)
        Text.objects.create(owner=self.user, content=METIN, durum=YaziDurumu.ESKI)  # eski sayılmaz
        self.assertEqual(limits.kalan_hak(self.user), 1)

    def test_yesterday_does_not_count(self):
        yazi = Text.objects.create(owner=self.user, content=METIN)
        Text.objects.filter(pk=yazi.pk).update(createdAt=timezone.now() - timedelta(days=2))
        self.assertEqual(limits.kalan_hak(self.user), 2)

    def test_third_submission_is_blocked_even_after_delete(self):
        with patch("LearnVocab.gemini.generate", return_value=cevap(iyi_cevap())):
            for _ in range(2):
                self.client.post(reverse("create_text"), {"user_text": METIN})
        ilk = Text.objects.first()
        self.client.post(reverse("remove_text", args=[ilk.id]))

        with patch("LearnVocab.gemini.generate") as gen:
            yanit = self.client.post(reverse("create_text"), {"user_text": METIN},
                                     HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(yanit.status_code, 429)
        self.assertIn("Bugünkü yazma hakkın doldu", yanit.json()["error"])
        gen.assert_not_called()
        self.assertEqual(Text.objects.count(), 2)

        sayfa = self.client.get(reverse("profile_texts")).content.decode()
        self.assertIn("Bugünkü yazma hakkın doldu", sayfa)
        self.assertIn("Bugünkü yazma hakkın doldu", self.client.get(reverse("new_text_page")).content.decode())

    def test_zero_disables_limit(self):
        with override_settings(TEXT_DAILY_LIMIT=0):
            self.assertIsNone(limits.kalan_hak(self.user))
            self.assertTrue(limits.yazabilir_mi(self.user))


# ===========================================================================
# Yeniden deneme komutu
# ===========================================================================

@override_settings(**HIZLI)
class YenidenDenemeKomutuTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cron", password="Sifre1234")
        eski = timezone.now() - timedelta(hours=2)
        self.yazilar = []
        for i in range(4):
            yazi = Text.objects.create(owner=self.user, content=METIN)
            Text.objects.filter(pk=yazi.pk).update(createdAt=eski + timedelta(minutes=i))
            self.yazilar.append(yazi)

    def _calistir(self, *args):
        cikti = StringIO()
        call_command("yazilari_yeniden_dene", *args, stdout=cikti)
        return cikti.getvalue()

    def test_respects_the_limit(self):
        with patch("LearnVocab.gemini.generate", return_value=cevap(iyi_cevap())) as gen:
            self._calistir("--limit", "2")
        self.assertEqual(gen.call_count, 2)
        self.assertEqual(Text.objects.filter(durum=YaziDurumu.TAMAM).count(), 2)
        # En eski ikisi
        self.assertEqual(set(Text.objects.filter(durum=YaziDurumu.TAMAM).values_list("pk", flat=True)),
                         {self.yazilar[0].pk, self.yazilar[1].pk})

    def test_stops_on_quota(self):
        with patch("LearnVocab.gemini.generate", side_effect=gemini.GeminiRateLimit("429")) as gen:
            cikti = self._calistir()
        self.assertEqual(gen.call_count, 1)
        self.assertIn("durduruldu", cikti)
        self.assertEqual(Text.objects.filter(durum=YaziDurumu.BEKLIYOR).count(), 4)

    def test_skips_recently_tried_and_deleted(self):
        Text.objects.filter(pk=self.yazilar[0].pk).update(son_deneme=timezone.now() - timedelta(minutes=5))
        Text.objects.filter(pk=self.yazilar[1].pk).update(silindi=timezone.now())
        with patch("LearnVocab.gemini.generate", return_value=cevap(iyi_cevap())) as gen:
            self._calistir()
        self.assertEqual(gen.call_count, 2)
        self.assertEqual(Text.objects.get(pk=self.yazilar[0].pk).durum, YaziDurumu.BEKLIYOR)

    def test_dry_run_calls_nothing(self):
        with patch("LearnVocab.gemini.generate") as gen:
            cikti = self._calistir("--dry-run")
        gen.assert_not_called()
        self.assertIn("4 metin denenecekti", cikti)

    def test_purges_old_deleted_texts(self):
        Text.objects.filter(pk=self.yazilar[0].pk).update(silindi=timezone.now() - timedelta(days=2))
        Text.objects.filter(pk=self.yazilar[1].pk).update(silindi=timezone.now())
        with patch("LearnVocab.gemini.generate", return_value=cevap(iyi_cevap())):
            cikti = self._calistir()
        self.assertFalse(Text.objects.filter(pk=self.yazilar[0].pk).exists())
        self.assertTrue(Text.objects.filter(pk=self.yazilar[1].pk).exists())
        self.assertIn("Temizlenen silinmiş kayıt: 1", cikti)


# ===========================================================================
# Diyalogda doğru kelime
# ===========================================================================

class TekHarfTests(TestCase):
    def test_one_edit(self):
        for a, b in (("postponed", "postpned"), ("postponed", "postponedd"), ("postponed", "postpaned"),
                     ("postponed", "postpnoed")):
            with self.subTest(a=a, b=b):
                self.assertTrue(dy.tek_harf_farki_mi(a, b))

    def test_not_one_edit(self):
        for a, b in (("postponed", "postponed"), ("postponed", "postpnd"), ("postponed", "delayed")):
            with self.subTest(a=a, b=b):
                self.assertFalse(dy.tek_harf_farki_mi(a, b))


class DiyalogCevabiTests(TestCase):
    def setUp(self):
        self.kelime = kelime_olustur("postpone", anlam="ertelemek")
        self.diyalog = diyalog_olustur(self.kelime)

    def test_exact_answer(self):
        self.assertEqual(dy.cevabi_degerlendir(self.diyalog, "  Postponed. ").durum, dy.DOGRU)

    def test_inflected_form_is_accepted(self):
        sonuc = dy.cevabi_degerlendir(self.diyalog, "postpone")
        self.assertEqual(sonuc.durum, dy.DOGRU)
        self.assertIn("Bu cümlede: postponed", sonuc.mesaj)
        self.assertEqual(dy.cevabi_degerlendir(self.diyalog, "postpones").durum, dy.DOGRU)

    def test_wordform_rows_are_used(self):
        from words.models import WordForm
        git = kelime_olustur("go", v2="went", v3="gone")
        WordForm.objects.create(word=git, surface="went")
        d = diyalog_olustur(git, cevap_="gone")
        self.assertEqual(dy.cevabi_degerlendir(d, "went").durum, dy.DOGRU)

    def test_one_letter_typo_is_almost(self):
        sonuc = dy.cevabi_degerlendir(self.diyalog, "postpned")
        self.assertEqual(sonuc.durum, dy.NEREDEYSE)
        self.assertEqual(sonuc.mesaj, "Neredeyse! Doğrusu: postponed")

    def test_wrong_answer(self):
        sonuc = dy.cevabi_degerlendir(self.diyalog, "cancelled")
        self.assertEqual(sonuc.durum, dy.YANLIS)
        self.assertIn("Doğrusu: postponed", sonuc.mesaj)

    def test_empty_answer(self):
        self.assertEqual(dy.cevabi_degerlendir(self.diyalog, "   ").durum, dy.BOS)

    def test_short_words_are_not_almost(self):
        d = diyalog_olustur(kelime_olustur("do", v2="did", v3="done"), cevap_="do")
        self.assertEqual(dy.cevabi_degerlendir(d, "go").durum, dy.YANLIS)

    def test_register_note(self):
        self.assertEqual(dy.register_notu(self.diyalog), "")
        d = diyalog_olustur(self.kelime, register="formal", sentiment="negative")
        self.assertEqual(dy.register_notu(d), "Üslup: resmî · Ton: olumsuz")
        d.not_metni = "Resmî bir kelime."
        self.assertEqual(dy.register_notu(d), "Resmî bir kelime.")


class DiyalogKapaliTests(TestCase):
    """Diyalog sonraki sürüme saklandı (settings.DIYALOG_ACIK = False, Efe 17 Ekim)."""

    def test_adresler_404_ve_yazilarda_iz_yok(self):
        User.objects.create_user(username="kapali", password="Sifre1234")
        d = diyalog_olustur(kelime_olustur("postpone", anlam="ertelemek"))
        for giris in (False, True):
            with self.subTest(giris=giris):
                if giris:
                    self.client.login(username="kapali", password="Sifre1234")
                self.assertEqual(self.client.get(reverse("diyalog_page")).status_code, 404)
                self.assertEqual(self.client.post(reverse("diyalog_cevap", args=[d.id]), {"cevap": "x"}).status_code, 404)
                html = self.client.get(reverse("profile_texts")).content.decode()
                self.assertNotIn(reverse("diyalog_page"), html)
                self.assertNotIn("Diyalogda doğru kelime", html)
        self.assertRedirects(self.client.get("/texts/diyalog/"), reverse("profile_texts"),
                             status_code=301, fetch_redirect_response=False)
        yardim = self.client.get(reverse("about")).content.decode()
        self.assertNotIn("Diyalogda doğru kelime", yardim)
        self.assertNotIn("1 diyalog", yardim)


@override_settings(DIYALOG_ACIK=True)
class DiyalogSayfasiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="diyalog", password="Sifre1234")
        self.client.login(username="diyalog", password="Sifre1234")
        self.kelime = kelime_olustur("postpone", anlam="ertelemek")

    def _html(self):
        return self.client.get(reverse("diyalog_page")).content.decode()

    def test_empty_pool_is_encouraging(self):
        UserWordLink.objects.create(user=self.user, word=self.kelime)
        html = self._html()
        self.assertIn('data-bos="havuz"', html)
        self.assertIn("Diyaloglar hazırlanıyor", html)

    def test_unreviewed_dialogs_do_not_count(self):
        UserWordLink.objects.create(user=self.user, word=self.kelime)
        diyalog_olustur(self.kelime, denetlendi=False)
        self.assertIn('data-bos="havuz"', self._html())

    def test_empty_list(self):
        diyalog_olustur(self.kelime)
        self.assertIn('data-bos="liste"', self._html())

    def test_no_dialog_for_listed_words(self):
        diyalog_olustur(self.kelime)
        UserWordLink.objects.create(user=self.user, word=kelime_olustur("decide"))
        html = self._html()
        self.assertIn('data-bos="kelime"', html)
        self.assertIn("Listendeki kelimeler için henüz diyalog yok", html)

    def test_dialog_is_shown_without_revealing_the_answer(self):
        d = diyalog_olustur(self.kelime)
        UserWordLink.objects.create(user=self.user, word=self.kelime)
        html = self._html()
        self.assertIn("ertelemek", html)
        self.assertIn("Are we still meeting on Friday?", html)
        self.assertIn("İlk harfi göster", html)
        self.assertNotIn("postponed", html)
        self.assertIn(reverse("diyalog_cevap", args=[d.id]), html)

    def test_answer_endpoint(self):
        d = diyalog_olustur(self.kelime, register="formal")
        yanit = self.client.post(reverse("diyalog_cevap", args=[d.id]), {"cevap": "postpned"})
        veri = yanit.json()
        self.assertEqual(veri["durum"], "neredeyse")
        self.assertEqual(veri["mesaj"], "Neredeyse! Doğrusu: postponed")
        self.assertEqual(veri["not"], "Üslup: resmî")
        self.assertEqual(DiyalogCevabi.objects.get().sonuc, "neredeyse")

    def test_unseen_dialogs_come_first(self):
        d1 = diyalog_olustur(self.kelime)
        d2 = diyalog_olustur(self.kelime)
        UserWordLink.objects.create(user=self.user, word=self.kelime)
        DiyalogCevabi.objects.create(user=self.user, diyalog=d1, girdi="postponed", sonuc="dogru")
        for _ in range(5):
            self.assertEqual(dy.siradaki(self.user), d2)

    def test_misafir_cevaplar_ama_kaydedilmez(self):
        """Rapor 18.3: misafir diyalog çözebilir; cevabı kaydedilmez, seriye sayılmaz."""
        d = diyalog_olustur(self.kelime)
        self.client.logout()
        yanit = self.client.post(reverse("diyalog_cevap", args=[d.id]), {"cevap": "postponed"})
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.json()["durum"], "dogru")
        self.assertNotIn("seri", yanit.json())
        self.assertFalse(DiyalogCevabi.objects.exists())

    def test_misafir_diyalog_sayfasi(self):
        d = diyalog_olustur(self.kelime)
        self.client.logout()
        cevap = self.client.get(reverse("diyalog_page"))
        self.assertEqual(cevap.status_code, 200)
        self.assertEqual(cevap.context["diyalog"], d)
        self.assertNotContains(cevap, "Serbest yazmaya geç")

    def test_misafir_dagilimi(self):
        import random
        from texts import diyalog as dy
        seviyeler = {}
        for seviye in ("B1", "B2", "C1"):
            w = kelime_olustur(f"w{seviye.lower()}", anlam="x")
            w.cefr = seviye
            w.save()
            seviyeler[seviye] = diyalog_olustur(w).id
        rng = random.Random(4)
        sayac = {s: 0 for s in seviyeler}
        ters = {v: k for k, v in seviyeler.items()}
        for _ in range(500):
            d = dy.misafir_siradaki(rng=rng)
            if d.id in ters:
                sayac[ters[d.id]] += 1
        self.assertGreater(sayac["B1"], 200)                            # ~%60
        self.assertGreater(sayac["B1"], sayac["B2"] + 100)
        self.assertGreater(sayac["B1"], sayac["C1"] + 100)


class DiyalogYukleTests(TestCase):
    def setUp(self):
        self.kelime = kelime_olustur("postpone", anlam="ertelemek")
        self.gecerli = {
            "kelime": "postpone", "tur": "verb", "anlam": "ertelemek",
            "satirlar": [
                {"kisi": "A", "metin": "Are we still meeting on Friday?"},
                {"kisi": "B", "metin": "No, the manager ___ it until next week."},
                {"kisi": "A", "metin": "Oh, why?"},
                {"kisi": "B", "metin": "Half of the team is away."},
            ],
            "cevap": "postponed", "ipucu": "ertelemek", "register": "formal", "denetlendi": True,
        }

    def _yukle(self, kayitlar, *args):
        with TemporaryDirectory() as klasor:
            yol = Path(klasor) / "havuz.json"
            yol.write_text(json.dumps(kayitlar, ensure_ascii=False), encoding="utf-8")
            cikti = StringIO()
            call_command("diyalog_yukle", str(yol), *args, stdout=cikti)
            return cikti.getvalue()

    def test_dry_run_writes_nothing(self):
        cikti = self._yukle([self.gecerli], "--dry-run")
        self.assertIn("1 yeni", cikti)
        self.assertFalse(Diyalog.objects.exists())

    def test_loads_and_is_idempotent(self):
        self._yukle([self.gecerli])
        d = Diyalog.objects.get()
        self.assertEqual((d.word, d.cevap, d.register, d.denetlendi), (self.kelime, "postponed", "formal", True))
        self.assertEqual(d.meaning.meaning_tr, "ertelemek")
        cikti = self._yukle([{**self.gecerli, "ipucu": "sonraya bırakmak"}])
        self.assertIn("1 güncellendi", cikti)
        self.assertEqual(Diyalog.objects.get().ipucu, "sonraya bırakmak")

    def test_invalid_records_are_skipped(self):
        iki_bosluk = {**self.gecerli, "satirlar": [dict(s, metin=s["metin"] + " ___") for s in self.gecerli["satirlar"]]}
        az_satir = {**self.gecerli, "satirlar": self.gecerli["satirlar"][:2]}
        yanlis_cevap = {**self.gecerli, "cevap": "cancelled"}
        yok = {**self.gecerli, "kelime": "flibbertigibbet"}
        cikti = self._yukle([iki_bosluk, az_satir, yanlis_cevap, yok, self.gecerli])
        self.assertIn("1 yeni", cikti)
        self.assertIn("4 atlandı", cikti)
        self.assertEqual(Diyalog.objects.count(), 1)

    def test_jsonl_is_accepted(self):
        with TemporaryDirectory() as klasor:
            yol = Path(klasor) / "havuz.jsonl"
            yol.write_text(json.dumps(self.gecerli, ensure_ascii=False) + "\n", encoding="utf-8")
            call_command("diyalog_yukle", str(yol), stdout=StringIO())
        self.assertEqual(Diyalog.objects.count(), 1)
