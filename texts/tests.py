"""
Gemini entegrasyonu testleri.

Gerçek API'ye istek atılmaz; istemci mock'lanır. Amaç, ağ olmadan da
şu yolların doğru çalıştığını garanti etmek:
  - anahtar / paket yoksa özellik sessizce devre dışı kalmalı, sayfa patlamamalı
  - geçici hata (503) ile kota hatası (429) ile kalıcı hata BİRBİRİNDEN ayrılmalı
    ve her biri kullanıcıya farklı, dürüst bir mesajla dönmeli
  - geçici hatada önce tekrar denenmeli, sonra yedek modele geçilmeli
  - kullanıcının metni ve kelimeleri prompt'a gerçekten girmeli
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.urls import reverse

from users.models import User
from words.models import Word, UserWordLink
from texts.models import Text
from texts.send_gemini import (
    RATE_LIMIT_RESPONSE,
    UNAVAILABLE_RESPONSE,
    _classify_error,
    _strip_formatting,
    _words_to_text,
    get_client,
    send_message_to_gemini,
)
from texts.views import _parse_gemini_scores

TEST_MODEL = "gemini-test-model"
FALLBACK_MODEL = "gemini-test-fallback"

# Testlerin varsayılanı: tekrar deneme yok, yedek model yok, bekleme yok.
# İhtiyacı olan testler bunları kendi içinde override ediyor.
FAST = dict(
    GEMINI_MODEL=TEST_MODEL,
    GEMINI_FALLBACK_MODELS=[],
    GEMINI_MAX_RETRIES=0,
    GEMINI_RETRY_BACKOFF_SECONDS=0,
    GEMINI_TIMEOUT_SECONDS=5,
    GEMINI_MIN_SECONDS_BETWEEN_REQUESTS=0,
)


def ok_response(text):
    response = MagicMock()
    response.text = text
    return response


def fake_client(responses):
    """
    generate_content çağrısını taklit eden istemci.

    `responses` bir liste: her eleman ya bir Exception (fırlatılır) ya da
    bir metin (başarılı cevap olarak döner). Çağrılar sırayla tüketilir.
    """
    client = MagicMock()

    def side_effect(*args, **kwargs):
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return ok_response(item)

    client.models.generate_content.side_effect = side_effect
    return client


def called_models(client):
    return [c.kwargs["model"] for c in client.models.generate_content.call_args_list]


class ClassifyErrorTests(TestCase):
    def test_quota_errors(self):
        self.assertEqual(_classify_error("429 RESOURCE_EXHAUSTED"), "rate_limit")
        self.assertEqual(_classify_error("quota exceeded"), "rate_limit")

    def test_transient_errors(self):
        self.assertEqual(
            _classify_error("503 UNAVAILABLE. This model is currently experiencing high demand."),
            "transient",
        )
        self.assertEqual(_classify_error("500 INTERNAL"), "transient")

    def test_fatal_errors(self):
        self.assertEqual(_classify_error("400 INVALID_ARGUMENT. API key not valid."), "fatal")
        self.assertEqual(_classify_error("404 NOT_FOUND. Model not found."), "fatal")


class WordsToTextTests(TestCase):
    def test_words_are_lowercased_and_joined(self):
        self.assertEqual(_words_to_text(["Retain", "OBTAIN"]), "retain, obtain")

    def test_blank_entries_are_dropped(self):
        self.assertEqual(_words_to_text(["retain", "  ", "", "obtain"]), "retain, obtain")

    def test_empty_list_gives_empty_string(self):
        self.assertEqual(_words_to_text([]), "")
        self.assertEqual(_words_to_text(None), "")


@override_settings(**FAST)
class SendMessageToGeminiTests(TestCase):
    @override_settings(GEMINI_API_TOKEN=None)
    def test_missing_api_key_disables_the_feature(self):
        with self.assertLogs("LearnVocab.gemini", level="ERROR"):
            self.assertIsNone(get_client())
        with self.assertLogs("LearnVocab.gemini", level="ERROR"):
            self.assertEqual(send_message_to_gemini("Some text.", ["retain"]), "")

    @override_settings(GEMINI_API_TOKEN="dummy-key")
    def test_successful_response_is_returned(self):
        with patch("LearnVocab.gemini.get_client", return_value=fake_client(["  Değerlendirme  "])):
            self.assertEqual(send_message_to_gemini("Some text.", ["retain"]), "Değerlendirme")

    @override_settings(GEMINI_API_TOKEN="dummy-key")
    def test_none_response_text_becomes_empty_string(self):
        """Güvenlik filtresine takılan cevaplarda .text None gelebiliyor."""
        with patch("LearnVocab.gemini.get_client", return_value=fake_client([None])):
            self.assertEqual(send_message_to_gemini("Some text.", ["retain"]), "")

    @override_settings(GEMINI_API_TOKEN="dummy-key")
    def test_quota_error_returns_rate_limit_marker(self):
        """
        Eski kodda `if "429" in e:` yazıyordu; `e` bir Exception olduğu için
        bu satır TypeError fırlatıyor ve kota aşımı hiç yakalanamıyordu.
        """
        error = Exception("429 RESOURCE_EXHAUSTED: quota exceeded")
        with patch("LearnVocab.gemini.get_client", return_value=fake_client([error])):
            with self.assertLogs("LearnVocab.gemini", level="WARNING"):
                self.assertEqual(
                    send_message_to_gemini("Some text.", ["retain"]), RATE_LIMIT_RESPONSE
                )

    @override_settings(GEMINI_API_TOKEN="dummy-key")
    def test_service_unavailable_returns_its_own_marker(self):
        """503, kullanıcının metniyle ilgili değil; ayrı bir mesajla dönmeli."""
        error = Exception("503 UNAVAILABLE. This model is currently experiencing high demand.")
        with patch("LearnVocab.gemini.get_client", return_value=fake_client([error])):
            with self.assertLogs("LearnVocab.gemini", level="WARNING"):
                self.assertEqual(
                    send_message_to_gemini("Some text.", ["retain"]), UNAVAILABLE_RESPONSE
                )

    @override_settings(GEMINI_API_TOKEN="dummy-key")
    def test_fatal_errors_return_empty_string(self):
        error = Exception("400 INVALID_ARGUMENT. API key not valid.")
        with patch("LearnVocab.gemini.get_client", return_value=fake_client([error])):
            with self.assertLogs("LearnVocab.gemini", level="WARNING"):
                self.assertEqual(send_message_to_gemini("Some text.", ["retain"]), "")

    @override_settings(GEMINI_API_TOKEN="dummy-key")
    def test_prompt_contains_user_text_and_words(self):
        client = fake_client(["ok"])
        with patch("LearnVocab.gemini.get_client", return_value=client):
            send_message_to_gemini("The company retained its staff.", ["Retain", "Obtain"])

        prompt = client.models.generate_content.call_args.kwargs["contents"]
        self.assertIn("The company retained its staff.", prompt)
        self.assertIn("retain, obtain", prompt)

    @override_settings(GEMINI_API_TOKEN="dummy-key")
    def test_model_comes_from_settings(self):
        """Model adı koda gömülü olmamalı; .env'den değiştirilebilmeli."""
        client = fake_client(["ok"])
        with patch("LearnVocab.gemini.get_client", return_value=client):
            send_message_to_gemini("Some text.", ["retain"])

        self.assertEqual(called_models(client), [TEST_MODEL])


@override_settings(
    GEMINI_API_TOKEN="dummy-key",
    GEMINI_MODEL=TEST_MODEL,
    GEMINI_FALLBACK_MODELS=[FALLBACK_MODEL],
    GEMINI_MAX_RETRIES=1,
    GEMINI_RETRY_BACKOFF_SECONDS=0,
    GEMINI_TIMEOUT_SECONDS=5,
    GEMINI_MIN_SECONDS_BETWEEN_REQUESTS=0,
)
class RetryAndFallbackTests(TestCase):
    """Geçici hatalarda önce tekrar dene, sonra yedek modele geç."""

    def test_transient_error_is_retried_on_the_same_model(self):
        error = Exception("503 UNAVAILABLE. high demand")
        client = fake_client([error, "İkinci denemede geldi"])
        with patch("LearnVocab.gemini.get_client", return_value=client):
            with self.assertLogs("LearnVocab.gemini", level="WARNING"):
                result = send_message_to_gemini("Some text.", ["retain"])

        self.assertEqual(result, "İkinci denemede geldi")
        self.assertEqual(called_models(client), [TEST_MODEL, TEST_MODEL])

    def test_falls_back_to_the_next_model(self):
        error = Exception("503 UNAVAILABLE. high demand")
        client = fake_client([error, error, "Yedek modelden geldi"])
        with patch("LearnVocab.gemini.get_client", return_value=client):
            with self.assertLogs("LearnVocab.gemini", level="WARNING"):
                result = send_message_to_gemini("Some text.", ["retain"])

        self.assertEqual(result, "Yedek modelden geldi")
        # Asıl model 2 kez (1 deneme + 1 tekrar), yedek 1 kez denenmeli
        self.assertEqual(called_models(client), [TEST_MODEL, TEST_MODEL, FALLBACK_MODEL])

    def test_all_models_failing_returns_unavailable(self):
        error = Exception("503 UNAVAILABLE. high demand")
        client = fake_client([error, error, error])
        with patch("LearnVocab.gemini.get_client", return_value=client):
            with self.assertLogs("LearnVocab.gemini", level="WARNING"):
                result = send_message_to_gemini("Some text.", ["retain"])

        self.assertEqual(result, UNAVAILABLE_RESPONSE)

    def test_quota_error_does_not_try_other_models(self):
        """Kota hesaba bağlı; model değiştirmek boşuna istek harcar."""
        error = Exception("429 RESOURCE_EXHAUSTED")
        client = fake_client([error])
        with patch("LearnVocab.gemini.get_client", return_value=client):
            with self.assertLogs("LearnVocab.gemini", level="WARNING"):
                result = send_message_to_gemini("Some text.", ["retain"])

        self.assertEqual(result, RATE_LIMIT_RESPONSE)
        self.assertEqual(called_models(client), [TEST_MODEL])

    def test_fatal_error_does_not_retry_the_same_model(self):
        error = Exception("400 INVALID_ARGUMENT. API key not valid.")
        client = fake_client([error, error])
        with patch("LearnVocab.gemini.get_client", return_value=client):
            with self.assertLogs("LearnVocab.gemini", level="WARNING"):
                send_message_to_gemini("Some text.", ["retain"])

        # Asıl modelde tekrar denenmemeli; yedek yine de bir kez denenir
        self.assertEqual(called_models(client), [TEST_MODEL, FALLBACK_MODEL])


@override_settings(**FAST, GEMINI_API_TOKEN="dummy-key")
class CreateTextViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="textuser", password="Sifre1234")
        self.client.login(username="textuser", password="Sifre1234")

        from words.testing import make_word

        word = make_word("retain", pos="verb", meaning="elde tutmak",
                         sentences=["They retain control."])
        UserWordLink.objects.create(user=self.user, word=word)

    def _post(self, text="This is my English paragraph about work."):
        return self.client.post(reverse("create_text"), {"user_text": text}, follow=True)

    def _messages(self, response):
        return " ".join(str(m) for m in response.context["messages"])

    def test_quota_error_shows_a_dedicated_message(self):
        with patch("texts.views.send_message_to_gemini", return_value=RATE_LIMIT_RESPONSE):
            response = self._post()

        self.assertIn("kota", self._messages(response).lower())
        self.assertEqual(Text.objects.count(), 0)

    def test_service_unavailable_does_not_blame_the_user(self):
        """
        503 alındığında kullanıcıya "geçerli bir İngilizce metin yazınız"
        denmesi yanlıştı: sorun kullanıcının metninde değil, serviste.
        """
        with patch("texts.views.send_message_to_gemini", return_value=UNAVAILABLE_RESPONSE):
            response = self._post()

        text = self._messages(response).lower()
        self.assertIn("yoğun", text)
        self.assertNotIn("ingilizce bir metin yazınız", text)
        self.assertEqual(Text.objects.count(), 0)

    def test_configuration_error_shows_a_service_message(self):
        with patch("texts.views.send_message_to_gemini", return_value=""):
            response = self._post()

        text = self._messages(response).lower()
        self.assertIn("ulaşılamıyor", text)
        self.assertNotIn("ingilizce bir metin yazınız", text)
        self.assertEqual(Text.objects.count(), 0)

    def test_model_refusing_to_grade_shows_the_user_message(self):
        """Bu mesaj artık YALNIZCA model 'değerlendirmedim' dediğinde çıkmalı."""
        with patch("texts.views.send_message_to_gemini", return_value="Bu metin değerlendirilmedi."):
            response = self._post()

        self.assertIn("İngilizce bir metin yazınız", self._messages(response))

    def test_malformed_response_does_not_create_a_text(self):
        with patch("texts.views.send_message_to_gemini", return_value="Değerlendirme ama puan yok"):
            with self.assertLogs("texts.views", level="WARNING"):
                self._post()
        self.assertEqual(Text.objects.count(), 0)

    def test_valid_response_creates_a_text_with_scores(self):
        answer = "Değerlendirme metni burada.\n[8,22,3,9,6,16,3,2,5,1]"
        with patch("texts.views.send_message_to_gemini", return_value=answer):
            self._post()

        text = Text.objects.get()
        self.assertEqual(text.score, 75)
        self.assertEqual(text.owner, self.user)
        self.assertIn("Değerlendirme metni burada.", text.response)
        self.assertNotIn("[8,22", text.response)

    def test_empty_user_text_is_rejected_without_calling_the_api(self):
        with patch("texts.views.send_message_to_gemini") as mocked:
            self._post(text="   ")
        mocked.assert_not_called()
        self.assertEqual(Text.objects.count(), 0)

    def test_failed_attempt_does_not_consume_the_daily_limit(self):
        """Servis hatası kullanıcının günlük hakkını yakmamalı."""
        with patch("texts.views.send_message_to_gemini", return_value=UNAVAILABLE_RESPONSE):
            self._post()

        answer = "Değerlendirme metni burada.\n[8,22,3,9,6,16,3,2,5,1]"
        with patch("texts.views.send_message_to_gemini", return_value=answer):
            self._post()

        self.assertEqual(Text.objects.count(), 1)


class StripFormattingTests(TestCase):
    """
    Cevap kullanıcıya `linebreaksbr` ile ham gösteriliyor; kaçan bir Markdown
    veya LaTeX işareti ekranda olduğu gibi görünüyor. Prompt modelden düz metin
    istiyor ama modeller bu alışkanlıktan tam vazgeçmiyor, o yüzden ikinci bir
    savunma katmanı olarak cevabı temizliyoruz.
    """

    def test_bold_and_italic_are_removed(self):
        self.assertEqual(_strip_formatting("**Genel:** Metin ***iyi*** yazılmış."),
                         "Genel: Metin iyi yazılmış.")
        self.assertEqual(_strip_formatting("_italik_ ve __kalın__"), "italik ve kalın")

    def test_word_internal_underscores_are_kept(self):
        self.assertEqual(_strip_formatting("değişken adı user_word_link olmalı"),
                         "değişken adı user_word_link olmalı")

    def test_latex_arrows_become_plain_arrows(self):
        self.assertEqual(_strip_formatting('"introvert" $\\rightarrow$ *introverted*.'),
                         '"introvert" -> introverted.')
        self.assertEqual(_strip_formatting("serbest \\rightarrow da olur"),
                         "serbest -> da olur")

    def test_dollar_amounts_are_not_eaten(self):
        """İki para birimi işareti LaTeX sanılıp aradaki metin yutulmamalı."""
        self.assertEqual(_strip_formatting("Fiyat $100 ve $200 arasında."),
                         "Fiyat $100 ve $200 arasında.")

    def test_headings_and_quotes_are_removed(self):
        self.assertEqual(_strip_formatting("### Dil Kullanımı\n> alıntı"),
                         "Dil Kullanımı\nalıntı")

    def test_bullets_are_normalised(self):
        self.assertEqual(_strip_formatting("* madde bir\n+ madde iki\n• madde üç"),
                         "- madde bir\n- madde iki\n- madde üç")

    def test_code_and_links_are_flattened(self):
        self.assertEqual(_strip_formatting("Bkz [kaynak](https://x.com) ve `kod`."),
                         "Bkz kaynak ve kod.")
        self.assertEqual(_strip_formatting("```\nkod bloğu\n```"), "kod bloğu")

    def test_excess_blank_lines_are_collapsed(self):
        self.assertEqual(_strip_formatting("bir\n\n\n\niki"), "bir\n\niki")

    def test_empty_input(self):
        self.assertEqual(_strip_formatting(""), "")
        self.assertEqual(_strip_formatting(None), "")

    def test_score_line_survives_and_still_parses(self):
        """Model puan satırını kalın yazsa bile parser'a uygun hâle gelmeli."""
        raw = "**Değerlendirme:** iyi.\n\n**[8,22,3,9,6,16,3,2,5,1]**"
        cleaned = _strip_formatting(raw)
        self.assertTrue(cleaned.endswith("[8,22,3,9,6,16,3,2,5,1]"))

        points, main_text = _parse_gemini_scores(cleaned)
        self.assertEqual(sum(points), 75)
        self.assertIn("Değerlendirme: iyi.", main_text)

    def test_real_world_sample(self):
        raw = (
            '* *Kalıp/Preposition hataları:* "make research" $\\rightarrow$ '
            '*conduct/carry out research*; "studying on how" $\\rightarrow$ *studying how*.'
        )
        self.assertEqual(
            _strip_formatting(raw),
            '- Kalıp/Preposition hataları: "make research" -> conduct/carry out research; '
            '"studying on how" -> studying how.',
        )


@override_settings(**FAST, GEMINI_API_TOKEN="dummy-key")
class ResponseIsCleanedTests(TestCase):
    def test_model_response_is_stripped_before_returning(self):
        raw = '**Değerlendirme:** "introvert" $\\rightarrow$ *introverted*.'
        with patch("LearnVocab.gemini.get_client", return_value=fake_client([raw])):
            result = send_message_to_gemini("Some text.", ["retain"])

        self.assertEqual(result, 'Değerlendirme: "introvert" -> introverted.')
        for marker in ("**", "$", "\\rightarrow"):
            self.assertNotIn(marker, result)

    def test_prompt_tells_the_model_to_use_plain_text(self):
        client = fake_client(["ok"])
        with patch("LearnVocab.gemini.get_client", return_value=client):
            send_message_to_gemini("Some text.", ["retain"])

        prompt = client.models.generate_content.call_args.kwargs["contents"]
        self.assertIn("plain text", prompt)
        self.assertIn("KESİNLİKLE KULLANMA", prompt)


# ---------------------------------------------------------------------------
# Metin yazma sıklığı kısıtı
# ---------------------------------------------------------------------------

from datetime import timedelta

from django.utils import timezone

from texts import limits


class HumanizeTests(TestCase):
    def test_minutes(self):
        self.assertEqual(limits.humanize(timedelta(minutes=5)), "5 dakika")

    def test_rounds_seconds_up(self):
        """'0 dakika kaldı' gibi bir mesaj çıkmamalı."""
        self.assertEqual(limits.humanize(timedelta(seconds=30)), "1 dakika")

    def test_hours_and_minutes(self):
        self.assertEqual(limits.humanize(timedelta(hours=2, minutes=5)), "2 saat 5 dakika")

    def test_one_day(self):
        self.assertEqual(limits.humanize(timedelta(days=1)), "1 gün")

    def test_more_than_a_day(self):
        """Eski elle biçimlendirme burada bozuluyordu ('1 day, 3:00:00')."""
        self.assertEqual(limits.humanize(timedelta(days=1, hours=3)), "1 gün 3 saat")

    def test_zero_and_none(self):
        self.assertEqual(limits.humanize(timedelta(0)), "0 dakika")
        self.assertEqual(limits.humanize(None), "")


class LimitSettingTests(TestCase):
    """Süre tek bir ayardan yönetilmeli."""

    def setUp(self):
        self.user = User.objects.create_user(username="limituser", password="Sifre1234")

    def _write_text(self, minutes_ago=0):
        text = Text.objects.create(owner=self.user, content="x", response="y")
        if minutes_ago:
            Text.objects.filter(pk=text.pk).update(
                createdAt=timezone.now() - timedelta(minutes=minutes_ago)
            )
        return text

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES=1440)
    def test_default_is_one_day(self):
        self.assertEqual(limits.interval(), timedelta(days=1))
        self.assertEqual(limits.interval_label(), "1 gün")

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES=5)
    def test_five_minute_interval(self):
        self.assertEqual(limits.interval(), timedelta(minutes=5))
        self.assertEqual(limits.interval_label(), "5 dakika")

        self._write_text(minutes_ago=1)
        self.assertFalse(limits.can_write_new_text(self.user))
        self.assertEqual(limits.remaining_label(self.user), "4 dakika")

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES=5)
    def test_interval_elapsed_allows_writing(self):
        self._write_text(minutes_ago=6)
        self.assertTrue(limits.can_write_new_text(self.user))
        self.assertIsNone(limits.remaining_for(self.user))

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES=0)
    def test_zero_disables_the_limit(self):
        self._write_text()
        self.assertFalse(limits.is_enabled())
        self.assertTrue(limits.can_write_new_text(self.user))
        self.assertEqual(limits.interval_label(), "")

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES=1440)
    def test_first_text_is_always_allowed(self):
        self.assertTrue(limits.can_write_new_text(self.user))

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES=1440)
    def test_delete_is_blocked_while_the_limit_is_active(self):
        text = self._write_text(minutes_ago=10)
        self.assertFalse(limits.can_delete(text))

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES=0)
    def test_delete_is_free_when_the_limit_is_off(self):
        text = self._write_text()
        self.assertTrue(limits.can_delete(text))

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES="bozuk-deger")
    def test_invalid_setting_falls_back_to_the_default(self):
        self.assertEqual(limits.interval(), timedelta(minutes=limits.DEFAULT_INTERVAL_MINUTES))


@override_settings(**FAST, GEMINI_API_TOKEN="dummy-key")
class LimitViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="limitview", password="Sifre1234")
        self.client.login(username="limitview", password="Sifre1234")

    def _existing_text(self, minutes_ago=0):
        text = Text.objects.create(owner=self.user, content="x", response="y")
        if minutes_ago:
            Text.objects.filter(pk=text.pk).update(
                createdAt=timezone.now() - timedelta(minutes=minutes_ago)
            )
        return text

    def _messages(self, response):
        return " ".join(str(m) for m in response.context["messages"])

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES=5)
    def test_new_text_page_explains_the_remaining_time(self):
        self._existing_text(minutes_ago=1)
        response = self.client.get(reverse("new_text_page"), follow=True)
        self.assertIn("4 dakika", self._messages(response))

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES=0)
    def test_new_text_page_is_open_when_the_limit_is_off(self):
        self._existing_text()
        response = self.client.get(reverse("new_text_page"))
        self.assertEqual(response.status_code, 200)

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES=0)
    def test_second_text_can_be_written_immediately(self):
        self._existing_text()
        answer = "Değerlendirme.\n[8,22,3,9,6,16,3,2,5,1]"
        with patch("texts.views.send_message_to_gemini", return_value=answer):
            self.client.post(reverse("create_text"), {"user_text": "My paragraph."}, follow=True)

        self.assertEqual(Text.objects.filter(owner=self.user).count(), 2)

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES=5)
    def test_create_is_blocked_within_the_interval(self):
        self._existing_text(minutes_ago=1)
        with patch("texts.views.send_message_to_gemini") as mocked:
            response = self.client.post(
                reverse("create_text"), {"user_text": "My paragraph."}, follow=True
            )
        mocked.assert_not_called()
        self.assertIn("4 dakika", self._messages(response))
        self.assertEqual(Text.objects.filter(owner=self.user).count(), 1)

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES=0)
    def test_delete_is_allowed_when_the_limit_is_off(self):
        text = self._existing_text()
        self.client.get(reverse("remove_text", args=[text.id]), follow=True)
        self.assertEqual(Text.objects.filter(pk=text.pk).count(), 0)

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES=1440)
    def test_delete_message_uses_the_configured_interval(self):
        text = self._existing_text(minutes_ago=10)
        response = self.client.get(reverse("remove_text", args=[text.id]), follow=True)
        self.assertIn("1 gün", self._messages(response))
        self.assertEqual(Text.objects.filter(pk=text.pk).count(), 1)

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES=5)
    def test_info_box_reflects_the_setting(self):
        response = self.client.get(reverse("profile_texts"))
        self.assertContains(response, "5 dakika")

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES=0)
    def test_info_box_hides_the_limit_line_when_off(self):
        response = self.client.get(reverse("profile_texts"))
        self.assertNotContains(response, "aralıklarla yazılabilmektedir")


from django.core.cache import cache as django_cache

from LearnVocab import progress
from texts import views as text_views


@override_settings(**FAST, GEMINI_API_TOKEN="dummy-key", TEXT_SUBMISSION_INTERVAL_MINUTES=0)
class EvaluationJobFlowTests(TestCase):
    """Metin değerlendirmenin ilerleme çubuklu akışı."""

    def setUp(self):
        django_cache.clear()
        self.user = User.objects.create_user(username="jobtext", password="Sifre1234")
        self.other = User.objects.create_user(username="digeri", password="Sifre1234")
        self.client.login(username="jobtext", password="Sifre1234")

    def _start(self, text="My English paragraph about work."):
        return self.client.post(
            reverse("create_text"),
            {"user_text": text},
            headers={"x-requested-with": "XMLHttpRequest"},
        )

    def test_ajax_start_returns_a_job_id(self):
        with patch("texts.views.threading.Thread") as thread:
            response = self._start()

        self.assertEqual(response.status_code, 200)
        job_id = response.json()["job_id"]
        thread.assert_called_once()
        self.assertEqual(progress.read(job_id)["owner_id"], self.user.id)

    def test_ajax_start_rejects_empty_text(self):
        with patch("texts.views.threading.Thread") as thread:
            response = self._start(text="   ")
        self.assertEqual(response.status_code, 400)
        thread.assert_not_called()

    @override_settings(TEXT_SUBMISSION_INTERVAL_MINUTES=1440)
    def test_ajax_start_respects_the_interval(self):
        Text.objects.create(owner=self.user, content="x", response="y")
        with patch("texts.views.threading.Thread") as thread:
            response = self._start()

        self.assertEqual(response.status_code, 429)
        thread.assert_not_called()

    def test_progress_of_another_user_is_not_visible(self):
        job_id = progress.create(self.other.id)
        response = self.client.get(reverse("create_text_progress", args=[job_id]))
        self.assertEqual(response.status_code, 404)

    def test_successful_job_redirects_to_the_review_page(self):
        text = Text.objects.create(owner=self.user, content="x", response="y")
        job_id = progress.create(self.user.id)
        progress.finish(job_id, {"text_id": text.id})

        response = self.client.post(reverse("create_text_finish", args=[job_id]))
        self.assertEqual(response.json()["redirect"], reverse("review_text", args=[text.id]))
        self.assertIsNone(progress.read(job_id))

    def test_failed_job_reports_the_reason(self):
        job_id = progress.create(self.user.id)
        progress.fail(job_id, "Servis yoğun")

        response = self.client.post(reverse("create_text_finish", args=[job_id]))
        self.assertEqual(response.json()["redirect"], reverse("profile_texts"))
        self.assertIn("Servis yoğun",
                      " ".join(str(m) for m in response.wsgi_request._messages))

    def test_job_body_saves_the_text_and_finishes(self):
        answer = "Değerlendirme metni.\n[8,22,3,9,6,16,3,2,5,1]"
        job_id = progress.create(self.user.id)

        with patch("texts.views.send_message_to_gemini", return_value=answer):
            with patch("django.db.connection.close"):
                text_views._run_text_evaluation(job_id, self.user.id, "My paragraph.")

        job = progress.read(job_id)
        self.assertEqual(job["state"], progress.STATE_DONE)
        self.assertEqual(job["percent"], 100)
        self.assertEqual(Text.objects.get().score, 75)

    def test_job_body_marks_service_errors_as_failed(self):
        job_id = progress.create(self.user.id)

        with patch("texts.views.send_message_to_gemini", return_value=UNAVAILABLE_RESPONSE):
            with patch("django.db.connection.close"):
                text_views._run_text_evaluation(job_id, self.user.id, "My paragraph.")

        job = progress.read(job_id)
        self.assertEqual(job["state"], progress.STATE_FAILED)
        self.assertIn("yoğun", job["message"].lower())
        self.assertEqual(Text.objects.count(), 0)

    def test_progress_advances_when_a_fallback_model_is_tried(self):
        self.job_id = progress.create(self.user.id)
        gorulen = []

        def fake_send(text, words, on_event=None):
            if on_event:
                on_event("attempt", {"model": "m1", "model_index": 0, "model_count": 2,
                                     "attempt": 1, "attempts": 1})
                gorulen.append(progress.read(self.job_id)["percent"])
                on_event("error", {"model": "m1", "kind": "transient", "message": "503"})
                on_event("attempt", {"model": "m2", "model_index": 1, "model_count": 2,
                                     "attempt": 1, "attempts": 1})
                gorulen.append(progress.read(self.job_id)["percent"])
            return "Değerlendirme.\n[8,22,3,9,6,16,3,2,5,1]"

        with patch("texts.views.send_message_to_gemini", side_effect=fake_send):
            with patch("django.db.connection.close"):
                text_views._run_text_evaluation(self.job_id, self.user.id, "My paragraph.")

        self.assertGreater(gorulen[1], gorulen[0],
                           "yedek modele geçildiğinde çubuk ilerlemedi")
