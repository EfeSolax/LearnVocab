"""
İlerleme takibi testleri.

İlerleme çubuğu bu kayıtlardan besleniyor; kayıt bozulursa kullanıcı donmuş
bir çubuğa bakar.
"""

from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from LearnVocab import gemini, progress


class ProgressStoreTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_create_and_read(self):
        job_id = progress.create(owner_id=7, message="Başlıyor")
        job = progress.read(job_id)

        self.assertEqual(job["owner_id"], 7)
        self.assertEqual(job["state"], progress.STATE_RUNNING)
        self.assertEqual(job["message"], "Başlıyor")

    def test_unknown_job_reads_as_none(self):
        self.assertIsNone(progress.read("boyle-bir-is-yok"))

    def test_percent_never_goes_backwards(self):
        """
        Farklı adımlar farklı tahminler üretiyor; çubuğun geri sarması
        kullanıcıya bir şeylerin bozulduğunu düşündürür.
        """
        job_id = progress.create(owner_id=1)
        progress.update(job_id, percent=60)
        progress.update(job_id, percent=30)

        self.assertEqual(progress.read(job_id)["percent"], 60)

    def test_percent_is_capped_at_hundred(self):
        job_id = progress.create(owner_id=1)
        progress.update(job_id, percent=250)
        self.assertEqual(progress.read(job_id)["percent"], 100)

    def test_finish_stores_the_result(self):
        job_id = progress.create(owner_id=1)
        progress.finish(job_id, {"added": ["retain"]}, "Bitti")

        job = progress.read(job_id)
        self.assertEqual(job["state"], progress.STATE_DONE)
        self.assertEqual(job["percent"], 100)
        self.assertEqual(job["result"], {"added": ["retain"]})

    def test_fail_stores_the_reason(self):
        job_id = progress.create(owner_id=1)
        progress.fail(job_id, "Servis yoğun")

        job = progress.read(job_id)
        self.assertEqual(job["state"], progress.STATE_FAILED)
        self.assertEqual(job["message"], "Servis yoğun")

    def test_delete(self):
        job_id = progress.create(owner_id=1)
        progress.delete(job_id)
        self.assertIsNone(progress.read(job_id))

    def test_update_on_missing_job_is_harmless(self):
        self.assertIsNone(progress.update("yok", percent=50))


class ReporterTests(TestCase):
    def setUp(self):
        cache.clear()
        self.job_id = progress.create(owner_id=1)

    def test_ratio_maps_into_the_range(self):
        reporter = progress.Reporter(self.job_id, 10, 90)
        reporter.set(0.5, "yarı")

        job = progress.read(self.job_id)
        self.assertEqual(job["percent"], 50)
        self.assertEqual(job["message"], "yarı")

    def test_ratio_is_clamped(self):
        reporter = progress.Reporter(self.job_id, 0, 50)
        reporter.set(5)
        self.assertEqual(progress.read(self.job_id)["percent"], 50)

    def test_slices_divide_the_range(self):
        reporter = progress.Reporter(self.job_id, 0, 100)

        first = reporter.slice_for(0, 2)
        second = reporter.slice_for(1, 2)

        self.assertEqual((first.start, first.end), (0, 50))
        self.assertEqual((second.start, second.end), (50, 100))

    def test_slice_reports_within_its_own_share(self):
        reporter = progress.Reporter(self.job_id, 0, 100)
        reporter.slice_for(1, 2).set(0.5)
        self.assertEqual(progress.read(self.job_id)["percent"], 75)

    def test_message_only_update(self):
        progress.Reporter(self.job_id).message("sadece mesaj")
        self.assertEqual(progress.read(self.job_id)["message"], "sadece mesaj")


@override_settings(
    GEMINI_API_TOKEN="dummy-key",
    GEMINI_MODEL="model-a",
    GEMINI_FALLBACK_MODELS=["model-b"],
    GEMINI_MAX_RETRIES=0,
    GEMINI_MIN_SECONDS_BETWEEN_REQUESTS=0,
    GEMINI_TIMEOUT_SECONDS=5,
)
class GeminiEventTests(TestCase):
    """
    İlerleme çubuğunun "anlamlı" olmasının kaynağı bu olaylar: ikinci istek
    gerçekten gittiğinde çubuk da gerçekten ilerliyor.
    """

    def _client(self, *side_effects):
        client = MagicMock()
        client.models.generate_content.side_effect = list(side_effects)
        return client

    def test_success_emits_attempt_and_success(self):
        events = []
        client = self._client(MagicMock())

        with patch("LearnVocab.gemini.get_client", return_value=client):
            gemini.generate("prompt", on_event=lambda n, i: events.append((n, i)))

        names = [name for name, _info in events]
        self.assertEqual(names, ["attempt", "success"])
        self.assertEqual(events[0][1]["model"], "model-a")
        self.assertEqual(events[0][1]["model_count"], 2)

    def test_fallback_emits_a_second_attempt(self):
        events = []
        client = self._client(Exception("503 UNAVAILABLE"), MagicMock())

        with patch("LearnVocab.gemini.get_client", return_value=client):
            with self.assertLogs("LearnVocab.gemini", level="WARNING"):
                gemini.generate("prompt", on_event=lambda n, i: events.append((n, i)))

        names = [name for name, _info in events]
        self.assertEqual(names, ["attempt", "error", "attempt", "success"])

        # İkinci deneme yedek modelde: çubuk buna göre ilerliyor
        self.assertEqual(events[2][1]["model"], "model-b")
        self.assertEqual(events[2][1]["model_index"], 1)
        self.assertEqual(events[1][1]["kind"], "transient")

    def test_broken_callback_does_not_break_the_request(self):
        """İlerleme bildirimi asıl işi bozmamalı."""
        client = self._client(MagicMock())

        def kirik(name, info):
            raise RuntimeError("patladım")

        with patch("LearnVocab.gemini.get_client", return_value=client):
            response = gemini.generate("prompt", on_event=kirik)

        self.assertIsNotNone(response)
