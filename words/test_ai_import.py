"""
Yapay zeka ile kelime ekleme testleri.

Gemini'ye gerçek istek atılmaz; `LearnVocab.gemini.generate` mock'lanır.
Korunan davranışlar:
  - girdinin temizlenmesi (ayraçlar, tekrarlar, üst sınır)
  - Gemini cevabının Word alanlarına doğru çevrilmesi
  - İngilizce'de olmayan kelimelerin hiç işlenmemesi
  - yazım hatalarının düzeltilerek eklenmesi
  - alan uzunluk sınırlarının aşılmaması
  - kelimelerin kullanıcıya özel (private) ve seviyesiz eklenmesi
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.urls import reverse

from LearnVocab import gemini
from users.models import User
from words import ai_import
from words.ai_import import EnrichedWord, EnrichmentResponse, ExampleSentence
from words.models import Word, UserWordLink


def sentences(count=ai_import.SENTENCE_COUNT, prefix="They retain"):
    levels = []
    for level, repeat in ai_import.SENTENCE_PLAN:
        levels.extend([level] * repeat)
    return [
        ExampleSentence(level=levels[i], sentence=f"{prefix} number {i + 1}.")
        for i in range(count)
    ]


def enriched(**overrides):
    data = dict(
        requested="retain",
        found=True,
        english_word="retain",
        was_corrected=False,
        is_verb=True,
        meaning_tr="elde tutmak",
        explanation="to keep something",
        v2_form="retained",
        v3_form="retained",
        synonyms=["keep", "hold"],
        antonyms=["lose"],
        collocations=["retain control", "retain information"],
        example_sentences=sentences(),
    )
    data.update(overrides)
    return EnrichedWord(**data)


def fake_response(words):
    response = MagicMock()
    response.parsed = EnrichmentResponse(words=words)
    return response


class ParseInputWordsTests(TestCase):
    def test_splits_on_newlines_commas_and_semicolons(self):
        words, truncated = ai_import.parse_input_words("retain\nobtain, deliberate; undermine")
        self.assertEqual(words, ["retain", "obtain", "deliberate", "undermine"])
        self.assertFalse(truncated)

    def test_trims_and_drops_blanks(self):
        words, _ = ai_import.parse_input_words("  retain  \n\n   \n obtain \n")
        self.assertEqual(words, ["retain", "obtain"])

    def test_duplicates_are_removed_case_insensitively(self):
        words, _ = ai_import.parse_input_words("retain\nRetain\nRETAIN\nobtain")
        self.assertEqual(words, ["retain", "obtain"])

    def test_multiword_entries_are_kept(self):
        words, _ = ai_import.parse_input_words("give   up\ncarry out")
        self.assertEqual(words, ["give up", "carry out"])

    @override_settings(AI_WORD_IMPORT_MAX_WORDS=3)
    def test_limit_is_applied_and_reported(self):
        words, truncated = ai_import.parse_input_words("a\nb\nc\nd\ne")
        self.assertEqual(words, ["a", "b", "c"])
        self.assertTrue(truncated)

    def test_empty_input(self):
        self.assertEqual(ai_import.parse_input_words(""), ([], False))
        self.assertEqual(ai_import.parse_input_words(None), ([], False))


class BuildWordKwargsTests(TestCase):
    def test_maps_every_field(self):
        kwargs = ai_import.build_word_kwargs(enriched())

        self.assertEqual(kwargs["englishWord"], "retain")
        self.assertEqual(kwargs["meaningTr"], "elde tutmak")
        self.assertEqual(kwargs["explanation"], "to keep something")
        self.assertTrue(kwargs["isVerb"])
        self.assertEqual(kwargs["v2Form"], "retained")
        self.assertEqual(kwargs["synonyms"], "keep, hold")
        self.assertEqual(kwargs["collocations"], "retain control, retain information")

    def test_word_is_private_and_levelless(self):
        kwargs = ai_import.build_word_kwargs(enriched())
        self.assertEqual(kwargs["visibility"], "private")
        self.assertEqual(kwargs["wordLevel"], "Belirtilmemiş")
        self.assertFalse(kwargs["isBaseWord"])

    def test_sentences_fill_the_ten_fields_in_order(self):
        kwargs = ai_import.build_word_kwargs(enriched())
        self.assertEqual(kwargs["exampleSentence1"], "They retain number 1.")
        self.assertEqual(kwargs["exampleSentence10"], "They retain number 10.")

    def test_fewer_sentences_leave_the_rest_empty(self):
        kwargs = ai_import.build_word_kwargs(enriched(example_sentences=sentences(3)))
        self.assertEqual(kwargs["exampleSentence3"], "They retain number 3.")
        self.assertIsNone(kwargs["exampleSentence4"])

    def test_verb_forms_are_dropped_for_non_verbs(self):
        kwargs = ai_import.build_word_kwargs(
            enriched(is_verb=False, v2_form="nonsense", v3_form="nonsense")
        )
        self.assertIsNone(kwargs["v2Form"])
        self.assertIsNone(kwargs["v3Form"])

    def test_word_not_found_is_skipped(self):
        self.assertIsNone(ai_import.build_word_kwargs(enriched(found=False)))

    def test_word_without_sentences_is_skipped(self):
        """exampleSentence1 zorunlu alan; cümlesiz kelime kaydedilemez."""
        self.assertIsNone(ai_import.build_word_kwargs(enriched(example_sentences=[])))

    def test_word_without_meaning_is_skipped(self):
        self.assertIsNone(ai_import.build_word_kwargs(enriched(meaning_tr="   ")))

    def test_values_are_truncated_to_field_limits(self):
        """İki anlamlı kelimelerde model sınırı aşabiliyor; MySQL bunu reddeder."""
        kwargs = ai_import.build_word_kwargs(
            enriched(meaning_tr="a" * 400, explanation="b" * 500)
        )
        self.assertLessEqual(len(kwargs["meaningTr"]), 200)
        self.assertLessEqual(len(kwargs["explanation"]), 300)

    def test_duplicate_list_entries_are_removed(self):
        kwargs = ai_import.build_word_kwargs(enriched(synonyms=["keep", "Keep", "hold"]))
        self.assertEqual(kwargs["synonyms"], "keep, hold")

    def test_empty_lists_become_none(self):
        kwargs = ai_import.build_word_kwargs(enriched(antonyms=[], collocations=[]))
        self.assertIsNone(kwargs["antonyms"])
        self.assertIsNone(kwargs["collocations"])


class PromptTests(TestCase):
    def test_prompt_lists_the_requested_words(self):
        prompt = ai_import.build_prompt(["retain", "obtain"])
        self.assertIn("- retain", prompt)
        self.assertIn("- obtain", prompt)

    def test_prompt_states_the_rules(self):
        prompt = ai_import.build_prompt(["retain"])
        self.assertIn("found=false", prompt)          # olmayan kelime
        self.assertIn("was_corrected=true", prompt)   # yazım hatası
        self.assertIn("1. birinci anlam / 2. ikinci anlam", prompt)  # çok anlamlılık
        self.assertIn(str(ai_import.SENTENCE_COUNT), prompt)
        self.assertIn("C1", prompt)
        self.assertIn("Markdown", prompt)


@override_settings(AI_WORD_IMPORT_CHUNK_SIZE=2)
class EnrichWordsTests(TestCase):
    def test_words_are_sent_in_chunks(self):
        with patch("LearnVocab.gemini.generate",
                   return_value=fake_response([enriched()])) as generate:
            ai_import.enrich_words(["a", "b", "c", "d", "e"])

        # 5 kelime / 2'lik gruplar -> 3 istek
        self.assertEqual(generate.call_count, 3)

    def test_schema_is_passed_so_json_is_guaranteed(self):
        with patch("LearnVocab.gemini.generate",
                   return_value=fake_response([enriched()])) as generate:
            ai_import.enrich_words(["retain"])

        self.assertIs(generate.call_args.kwargs["response_schema"],
                      ai_import.EnrichmentResponse)

    def test_results_from_all_chunks_are_collected(self):
        with patch("LearnVocab.gemini.generate", return_value=fake_response([enriched()])):
            outcome = ai_import.enrich_words(["a", "b", "c"])

        self.assertEqual(len(outcome.words), 2)  # 2 grup x 1 kelime
        self.assertIsNone(outcome.error)

    def test_partial_failure_still_returns_the_successful_chunk(self):
        calls = [gemini.GeminiUnavailable("503"), fake_response([enriched()])]

        def side_effect(*args, **kwargs):
            item = calls.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        with patch("LearnVocab.gemini.generate", side_effect=side_effect):
            outcome = ai_import.enrich_words(["a", "b", "c"])

        self.assertEqual(len(outcome.words), 1)
        self.assertEqual(outcome.error, "unavailable")
        self.assertFalse(outcome.is_total_failure)

    def test_rate_limit_is_reported(self):
        with patch("LearnVocab.gemini.generate", side_effect=gemini.GeminiRateLimit("429")):
            outcome = ai_import.enrich_words(["retain"])

        self.assertEqual(outcome.error, "rate_limit")
        self.assertTrue(outcome.is_total_failure)

    def test_response_not_matching_the_schema_is_reported(self):
        response = MagicMock()
        response.parsed = None
        response.text = "bu JSON degil"
        with patch("LearnVocab.gemini.generate", return_value=response):
            with self.assertLogs("words.ai_import", level="WARNING"):
                outcome = ai_import.enrich_words(["retain"])

        self.assertEqual(outcome.error, "failed")

    def test_empty_word_list_makes_no_request(self):
        with patch("LearnVocab.gemini.generate") as generate:
            outcome = ai_import.enrich_words([])
        generate.assert_not_called()
        self.assertEqual(outcome.words, [])


class AiAddWordsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="aiuser", password="Sifre1234")
        self.client.login(username="aiuser", password="Sifre1234")

    def _post(self, words="retain"):
        return self.client.post(reverse("ai_add_words"), {"words": words}, follow=True)

    def _messages(self, response):
        return " ".join(str(m) for m in response.context["messages"])

    def test_page_renders(self):
        response = self.client.get(reverse("ai_add_words_page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="words"')

    def test_words_are_created_and_linked_to_the_user(self):
        with patch("LearnVocab.gemini.generate", return_value=fake_response([enriched()])):
            self._post()

        word = Word.objects.get(englishWord="retain")
        self.assertEqual(word.owner, self.user)
        self.assertEqual(word.visibility, "private")
        self.assertEqual(word.wordLevel, "Belirtilmemiş")
        self.assertEqual(len(word.example_sentences), ai_import.SENTENCE_COUNT)
        self.assertTrue(UserWordLink.objects.filter(user=self.user, word=word).exists())

    def test_missing_words_are_reported_and_skipped(self):
        response_words = [enriched(requested="asdqwe", found=False, english_word="")]
        with patch("LearnVocab.gemini.generate", return_value=fake_response(response_words)):
            response = self._post("asdqwe")

        self.assertEqual(Word.objects.count(), 0)
        self.assertIn("bulunamadığı için atlananlar", self._messages(response))

    def test_typos_are_corrected_and_reported(self):
        response_words = [enriched(requested="recieve", english_word="receive", was_corrected=True)]
        with patch("LearnVocab.gemini.generate", return_value=fake_response(response_words)):
            response = self._post("recieve")

        self.assertTrue(Word.objects.filter(englishWord="receive").exists())
        self.assertIn("recieve -> receive", self._messages(response))

    def test_words_already_in_the_list_are_skipped(self):
        existing = Word.objects.create(
            owner=self.user, englishWord="retain", meaningTr="elde tutmak",
            exampleSentence1="They retain control.",
        )
        UserWordLink.objects.create(user=self.user, word=existing)

        with patch("LearnVocab.gemini.generate", return_value=fake_response([enriched()])):
            response = self._post()

        self.assertEqual(Word.objects.filter(englishWord="retain").count(), 1)
        self.assertIn("Zaten listenizde", self._messages(response))

    def test_empty_input_is_rejected(self):
        with patch("LearnVocab.gemini.generate") as generate:
            response = self._post("   ")
        generate.assert_not_called()
        self.assertIn("en az bir kelime", self._messages(response))

    def test_rate_limit_shows_a_dedicated_message(self):
        with patch("LearnVocab.gemini.generate", side_effect=gemini.GeminiRateLimit("429")):
            response = self._post()

        self.assertIn("kota", self._messages(response).lower())
        self.assertEqual(Word.objects.count(), 0)

    def test_service_unavailable_shows_a_dedicated_message(self):
        with patch("LearnVocab.gemini.generate", side_effect=gemini.GeminiUnavailable("503")):
            response = self._post()

        self.assertIn("yoğun", self._messages(response).lower())

    def test_get_is_not_allowed(self):
        response = self.client.get(reverse("ai_add_words"))
        self.assertEqual(response.status_code, 405)

    def test_login_is_required(self):
        self.client.logout()
        response = self.client.post(reverse("ai_add_words"), {"words": "retain"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Word.objects.count(), 0)


@override_settings(AI_WORD_IMPORT_CHUNK_SIZE=2)
class QuotaFriendlyBehaviourTests(TestCase):
    """
    Ücretsiz katmanda model başına dakikada 5 istek var. Gruplar önce paralel
    gönderiliyordu ve bu sınıra anında çarpıp 429 aldırıyordu. Aşağıdaki
    testler kota dostu davranışı koruyor.
    """

    def test_requests_are_sequential_not_parallel(self):
        """Paralel gönderim ücretsiz katmanda anında 429 demekti."""
        active = {"now": 0, "max": 0}

        def side_effect(*args, **kwargs):
            active["now"] += 1
            active["max"] = max(active["max"], active["now"])
            active["now"] -= 1
            return fake_response([enriched()])

        with patch("LearnVocab.gemini.generate", side_effect=side_effect):
            ai_import.enrich_words(["a", "b", "c", "d"])

        self.assertEqual(active["max"], 1, "istekler paralel gönderiliyor")

    def test_same_model_is_not_retried(self):
        """Kota bütçesini korumak için grup başına tekrar deneme kapalı."""
        with patch("LearnVocab.gemini.generate",
                   return_value=fake_response([enriched()])) as generate:
            ai_import.enrich_words(["retain"])

        self.assertEqual(generate.call_args.kwargs["max_retries"], 0)

    def test_quota_error_stops_the_remaining_chunks(self):
        """Kota dolduysa kalan gruplar da kesin başarısız; boşuna istek atma."""
        with patch("LearnVocab.gemini.generate",
                   side_effect=gemini.GeminiRateLimit("429")) as generate:
            outcome = ai_import.enrich_words(["a", "b", "c", "d", "e", "f"])

        self.assertEqual(generate.call_count, 1, "kota hatasından sonra devam edilmiş")
        self.assertEqual(outcome.error, "rate_limit")

    def test_transient_error_does_not_stop_the_other_chunks(self):
        calls = [gemini.GeminiUnavailable("503"), fake_response([enriched()])]

        def side_effect(*args, **kwargs):
            item = calls.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        with patch("LearnVocab.gemini.generate", side_effect=side_effect):
            outcome = ai_import.enrich_words(["a", "b", "c"])

        self.assertEqual(len(outcome.words), 1)
        self.assertEqual(outcome.error, "unavailable")

    def test_quota_detail_reaches_the_outcome(self):
        error = gemini.GeminiRateLimit("429", detail="dakikalık istek kotası | sınır: 5")
        with patch("LearnVocab.gemini.generate", side_effect=error):
            outcome = ai_import.enrich_words(["retain"])

        self.assertIn("sınır: 5", outcome.detail)


class ThrottleTests(TestCase):
    """İstekler arası asgari boşluk."""

    def test_zero_disables_the_throttle(self):
        with override_settings(GEMINI_MIN_SECONDS_BETWEEN_REQUESTS=0):
            with patch("time.sleep") as sleep:
                gemini._throttle()
                gemini._throttle()
        sleep.assert_not_called()

    def test_consecutive_requests_are_spaced(self):
        with override_settings(GEMINI_MIN_SECONDS_BETWEEN_REQUESTS=13):
            with patch("time.sleep") as sleep:
                gemini._throttle()
                gemini._throttle()

        self.assertTrue(sleep.called, "ikinci istek beklemeden gitti")
        self.assertGreater(sleep.call_args.args[0], 10)

    def test_invalid_setting_is_treated_as_disabled(self):
        with override_settings(GEMINI_MIN_SECONDS_BETWEEN_REQUESTS="abc"):
            with patch("time.sleep") as sleep:
                gemini._throttle()
        sleep.assert_not_called()


class QuotaErrorDescriptionTests(TestCase):
    """429 gövdesinden okunur bir açıklama çıkarma."""

    SAMPLE = (
        "429 RESOURCE_EXHAUSTED. {'error': {'code': 429, "
        '"quotaId": "GenerateRequestsPerMinutePerProjectPerModel-FreeTier", '
        '"quotaValue": "5", "retryDelay": "34s"}}'
    )

    def test_extracts_quota_and_delay(self):
        detail = gemini.describe_quota_error(self.SAMPLE)
        self.assertIn("dakikalık istek kotası", detail)
        self.assertIn("34s", detail)
        self.assertIn("5", detail)

    def test_unknown_message_returns_empty(self):
        self.assertEqual(gemini.describe_quota_error("429 something else"), "")


class ErrorPreferenceTests(TestCase):
    """
    Yedek model listesinde ölü bir model varsa (artık kapatılmış bir sürüm
    404 dönerse) bu "kalıcı hata" sayılıp asıl sorunu -- servisin yoğun
    olmasını -- gizliyordu. Kullanıcı da "beklenmedik bir sorun" görüyordu.
    """

    @override_settings(
        GEMINI_API_TOKEN="dummy-key",
        GEMINI_MODEL="model-a",
        GEMINI_FALLBACK_MODELS=["model-b"],
        GEMINI_MAX_RETRIES=0,
        GEMINI_MIN_SECONDS_BETWEEN_REQUESTS=0,
        GEMINI_TIMEOUT_SECONDS=5,
    )
    def test_transient_error_wins_over_a_dead_fallback_model(self):
        client = MagicMock()
        client.models.generate_content.side_effect = [
            Exception("503 UNAVAILABLE. high demand"),
            Exception("404 NOT_FOUND. model is no longer available"),
        ]

        with patch("LearnVocab.gemini.get_client", return_value=client):
            with self.assertLogs("LearnVocab.gemini", level="WARNING"):
                with self.assertRaises(gemini.GeminiUnavailable):
                    gemini.generate("prompt")


class ImportTimeoutTests(TestCase):
    """Kelime zenginleştirme istekleri kendi (daha uzun) zaman aşımını kullanmalı."""

    @override_settings(AI_WORD_IMPORT_TIMEOUT_SECONDS=77)
    def test_timeout_is_passed_to_generate(self):
        with patch("LearnVocab.gemini.generate",
                   return_value=fake_response([enriched()])) as generate:
            ai_import.enrich_words(["retain"])

        self.assertEqual(generate.call_args.kwargs["timeout"], 77)


from django.core.cache import cache

from LearnVocab import progress
from words import views as word_views


class AiImportJobFlowTests(TestCase):
    """
    İlerleme çubuklu akış: başlat -> ilerlemeyi sor -> bitir.

    İş parçacığı testlerde belirsizlik yaratmasın diye başlatma ve iş
    gövdesi ayrı ayrı sınanıyor.
    """

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="jobuser", password="Sifre1234")
        self.other = User.objects.create_user(username="baskasi", password="Sifre1234")
        self.client.login(username="jobuser", password="Sifre1234")

    def _start(self, words="retain\nobtain"):
        return self.client.post(
            reverse("ai_add_words"),
            {"words": words},
            headers={"x-requested-with": "XMLHttpRequest"},
        )

    def test_ajax_start_returns_a_job_id_and_does_not_block(self):
        with patch("words.views.threading.Thread") as thread:
            response = self._start()

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("job_id", data)
        self.assertEqual(data["word_count"], 2)
        thread.assert_called_once()

        job = progress.read(data["job_id"])
        self.assertEqual(job["owner_id"], self.user.id)
        self.assertEqual(job["state"], progress.STATE_RUNNING)

    def test_ajax_start_rejects_empty_input(self):
        with patch("words.views.threading.Thread") as thread:
            response = self._start(words="   ")

        self.assertEqual(response.status_code, 400)
        thread.assert_not_called()

    @override_settings(AI_WORD_IMPORT_MAX_WORDS=1)
    def test_truncation_warning_is_returned_to_the_browser(self):
        with patch("words.views.threading.Thread"):
            response = self._start(words="retain\nobtain\nilluminate")

        self.assertIn("en fazla 1 kelime", response.json()["warning"])

    def test_progress_endpoint_reports_state(self):
        job_id = progress.create(self.user.id, message="Başladı", percent=10)
        response = self.client.get(reverse("ai_add_words_progress", args=[job_id]))

        data = response.json()
        self.assertEqual(data["state"], "running")
        self.assertEqual(data["percent"], 10)
        self.assertEqual(data["message"], "Başladı")

    def test_progress_of_another_user_is_not_visible(self):
        job_id = progress.create(self.other.id)
        response = self.client.get(reverse("ai_add_words_progress", args=[job_id]))
        self.assertEqual(response.status_code, 404)

    def test_progress_of_unknown_job_is_404(self):
        response = self.client.get(reverse("ai_add_words_progress", args=["yok"]))
        self.assertEqual(response.status_code, 404)

    def test_finish_turns_the_summary_into_messages(self):
        job_id = progress.create(self.user.id)
        progress.finish(job_id, {
            "added": ["retain"], "corrected": ["recieve -> receive"],
            "duplicates": [], "not_found": ["asdqwe"], "unusable": [],
            "error": None, "detail": "",
        })

        response = self.client.post(reverse("ai_add_words_finish", args=[job_id]))
        self.assertEqual(response.json()["redirect"], reverse("profile_words"))

        texts = [str(m) for m in response.wsgi_request._messages]
        birlesik = " ".join(texts)
        self.assertIn("1 kelime listenize eklendi", birlesik)
        self.assertIn("recieve -> receive", birlesik)
        self.assertIn("asdqwe", birlesik)

        # İş kaydı temizlenmeli
        self.assertIsNone(progress.read(job_id))

    def test_finish_reports_a_failed_job(self):
        job_id = progress.create(self.user.id)
        progress.fail(job_id, "Servis yoğun")

        response = self.client.post(reverse("ai_add_words_finish", args=[job_id]))
        self.assertEqual(response.json()["redirect"], reverse("ai_add_words_page"))
        self.assertIn("Servis yoğun",
                      " ".join(str(m) for m in response.wsgi_request._messages))

    def test_finish_refuses_while_still_running(self):
        job_id = progress.create(self.user.id)
        response = self.client.post(reverse("ai_add_words_finish", args=[job_id]))
        self.assertEqual(response.status_code, 409)

    def test_finish_of_another_user_is_404(self):
        job_id = progress.create(self.other.id)
        progress.finish(job_id, {"added": []})
        response = self.client.post(reverse("ai_add_words_finish", args=[job_id]))
        self.assertEqual(response.status_code, 404)


class AiImportJobBodyTests(TestCase):
    """Arka planda çalışan iş gövdesi."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="bodyuser", password="Sifre1234")

    def _run(self, words=("retain",)):
        job_id = progress.create(self.user.id)
        # connection.close() test işlemini bozmasın
        with patch("django.db.connection.close"):
            word_views._run_ai_import(job_id, self.user.id, list(words))
        return job_id

    def test_successful_run_saves_words_and_finishes(self):
        with patch("LearnVocab.gemini.generate", return_value=fake_response([enriched()])):
            job_id = self._run()

        job = progress.read(job_id)
        self.assertEqual(job["state"], progress.STATE_DONE)
        self.assertEqual(job["percent"], 100)
        self.assertEqual(job["result"]["added"], ["retain"])
        self.assertTrue(Word.objects.filter(englishWord="retain").exists())

    def test_failed_run_marks_the_job_failed(self):
        with patch("LearnVocab.gemini.generate", side_effect=gemini.GeminiRateLimit("429")):
            job_id = self._run()

        job = progress.read(job_id)
        self.assertEqual(job["state"], progress.STATE_FAILED)
        self.assertIn("kota", job["message"].lower())
        self.assertEqual(Word.objects.count(), 0)

    def test_progress_advances_during_the_run(self):
        gorulen = []

        def generate(*args, **kwargs):
            handler = kwargs.get("on_event")
            if handler:
                handler("attempt", {"model": "m1", "model_index": 0, "model_count": 2,
                                    "attempt": 1, "attempts": 1})
                gorulen.append(progress.read(self.job_id)["percent"])
                handler("error", {"model": "m1", "kind": "transient", "message": "503"})
                handler("attempt", {"model": "m2", "model_index": 1, "model_count": 2,
                                    "attempt": 1, "attempts": 1})
                gorulen.append(progress.read(self.job_id)["percent"])
            return fake_response([enriched()])

        self.job_id = progress.create(self.user.id)
        with patch("LearnVocab.gemini.generate", side_effect=generate):
            with patch("django.db.connection.close"):
                word_views._run_ai_import(self.job_id, self.user.id, ["retain"])

        self.assertEqual(len(gorulen), 2)
        self.assertGreater(gorulen[1], gorulen[0],
                           "yedek modele geçildiğinde çubuk ilerlemedi")
        self.assertEqual(progress.read(self.job_id)["percent"], 100)
