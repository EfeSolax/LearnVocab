"""
Quiz sistemi için temel regresyon testleri.

Buradaki testlerin çoğu, daha önce sessizce yanlış çalışan iki davranışı korumak
için yazıldı:

1. `UserWordLink.wrongRatio` bir YÜZDE (0-100) döndürür; öncelik eşikleri de
   yüzde cinsinden olmalıdır.
2. `MatchingQuestion.check_answer` istatistikleri SADECE BİR KEZ saymalıdır.
"""

import re

from django.conf import settings
from django.test import TestCase
from unittest import skipUnless
from django.urls import reverse

from users.models import User
from words.models import Word, UserWordLink
from quizzes.models import (
    QuizAttempt,
    QuizType,
    MatchingQuestion,
    MultipleChoiceQuestion,
    WritingQuestion,
    SynonymAntonymQuestion,
    FillInTheBlankQuestion,
)
from quizzes.views import classify_links_by_priority
from quizzes.question_generator import (
    generate_mc_question,
    generate_synonym_antonym_question,
)


def make_word(english, meaning, **extra):
    """Testler için eksiksiz bir Word üretir (bkz. words/testing.py)."""
    from words.testing import make_word as _yeni

    extra.setdefault("sentences", [f"This is an example with {english}."])
    extra.setdefault("is_base", False)
    return _yeni(english, meaning=meaning, **extra)


class WrongRatioTests(TestCase):
    """wrongRatio'nun yüzde döndürdüğünü sabitler."""

    def setUp(self):
        self.user = User.objects.create_user(username="ratio_user", password="Sifre1234")
        self.word = make_word("obtain", "elde etmek")
        self.link = UserWordLink.objects.create(user=self.user, word=self.word)

    def test_wrong_ratio_is_percentage(self):
        self.link.correctCount = 1
        self.link.wrongCount = 1
        self.assertEqual(self.link.totalAttempts, 2)
        self.assertEqual(self.link.wrongRatio, 50.0)

    def test_wrong_ratio_without_attempts_is_zero(self):
        self.assertEqual(self.link.wrongRatio, 0)


class ClassifyLinksByPriorityTests(TestCase):
    """
    Öncelik gruplaması testi.

    Eski kodda `wrongRatio >= 0.50` yazdığı için tek bir yanlışı olan kelime bile
    priority1'e düşüyordu. Bu testler o hatanın geri gelmesini engeller.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="prio_user", password="Sifre1234")

    def _link(self, name, correct, wrong):
        word = make_word(name, f"{name}-tr")
        return UserWordLink.objects.create(
            user=self.user, word=word, correctCount=correct, wrongCount=wrong
        )

    def test_new_word_goes_to_priority1(self):
        link = self._link("fresh", 1, 0)  # 1 deneme
        p1, p2, p3 = classify_links_by_priority([link])
        self.assertIn(link, p1)

    def test_mostly_correct_word_is_not_priority1(self):
        # 4 deneme, 1 yanlış -> %25. Eski hatalı kodda priority1'e düşüyordu.
        link = self._link("known", 3, 1)
        p1, p2, p3 = classify_links_by_priority([link])
        self.assertNotIn(link, p1)
        self.assertIn(link, p2)

    def test_well_known_word_goes_to_priority3(self):
        # 8 deneme, 1 yanlış -> %12.5
        link = self._link("mastered", 7, 1)
        p1, p2, p3 = classify_links_by_priority([link])
        self.assertIn(link, p3)

    def test_weak_word_goes_to_priority1(self):
        # 8 deneme, 5 yanlış -> %62.5
        link = self._link("weak", 3, 5)
        p1, p2, p3 = classify_links_by_priority([link])
        self.assertIn(link, p1)

    def test_priority1_is_sorted_by_fewest_attempts_first(self):
        few = self._link("few", 1, 0)      # 1 deneme
        none_yet = self._link("none", 0, 0)  # 0 deneme
        p1, _, _ = classify_links_by_priority([few, none_yet])
        self.assertEqual(p1[0], none_yet)


@skipUnless(settings.QUIZZES_ENABLED,
            "Quizler yeni kelime modeline taşınana kadar kapalı "
            "(settings.QUIZZES_ENABLED). Soru üreteçleri eski alan adlarını kullanıyor.")
class MatchingQuestionStatsTests(TestCase):
    """
    Eşleştirme sorusu istatistikleri tam olarak bir kez sayılmalı.

    Eski kodda check_answer'ın ikinci yarısı (kopyalanmış eski blok) tekrar
    update_word_stats() çağırdığı için sayaçlar iki kez artıyordu.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="match_user", password="Sifre1234")
        self.words = [make_word(f"word{i}", f"kelime{i}") for i in range(5)]
        self.links = [
            UserWordLink.objects.create(user=self.user, word=w) for w in self.words
        ]
        self.attempt = QuizAttempt.objects.create(
            owner=self.user, totalQuestion=5, quizType=QuizType.MATCHING
        )
        self.question = MatchingQuestion.objects.create(
            attempt=self.attempt,
            right_col_order_ids=";".join(str(w.id) for w in self.words),
            word_count=len(self.words),
        )
        self.question.words.set(self.words)

    def _refresh(self):
        return {
            link.word_id: UserWordLink.objects.get(pk=link.pk) for link in self.links
        }

    def test_fully_correct_answer_counts_each_word_once(self):
        answer = ";".join(f"{w.id}:{w.id}" for w in self.words)
        self.question.check_answer(answer)

        self.question.refresh_from_db()
        self.assertTrue(self.question.is_correct)
        self.assertEqual(self.question.correct_matches, 5)
        self.assertEqual(self.question.wrong_matches, 0)

        for link in self._refresh().values():
            self.assertEqual(link.correctCount, 1)
            self.assertEqual(link.wrongCount, 0)

    def test_partially_correct_answer_is_scored_per_word(self):
        # İlk 3 kelime doğru, son 2 kelime birbirine karışmış olsun
        pairs = [f"{w.id}:{w.id}" for w in self.words[:3]]
        pairs.append(f"{self.words[3].id}:{self.words[4].id}")
        pairs.append(f"{self.words[4].id}:{self.words[3].id}")
        self.question.check_answer(";".join(pairs))

        self.question.refresh_from_db()
        self.assertFalse(self.question.is_correct)
        self.assertEqual(self.question.correct_matches, 3)
        self.assertEqual(self.question.wrong_matches, 2)

        links = self._refresh()
        for word in self.words[:3]:
            self.assertEqual(links[word.id].correctCount, 1)
            self.assertEqual(links[word.id].wrongCount, 0, "doğru kelime yanlış sayılmamalı")
        for word in self.words[3:]:
            self.assertEqual(links[word.id].wrongCount, 1)
            self.assertEqual(links[word.id].correctCount, 0)

    def test_empty_answer_marks_all_words_wrong_once(self):
        self.question.check_answer("")
        links = self._refresh()
        for link in links.values():
            self.assertEqual(link.wrongCount, 1)
            self.assertEqual(link.correctCount, 0)


@skipUnless(settings.QUIZZES_ENABLED,
            "Quizler yeni kelime modeline taşınana kadar kapalı "
            "(settings.QUIZZES_ENABLED). Soru üreteçleri eski alan adlarını kullanıyor.")
class WritingQuestionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="write_user", password="Sifre1234")
        self.word = make_word("obtain", "elde etmek")
        UserWordLink.objects.create(user=self.user, word=self.word)
        self.attempt = QuizAttempt.objects.create(
            owner=self.user, totalQuestion=1, quizType=QuizType.WRITING
        )
        self.question = WritingQuestion.objects.create(
            attempt=self.attempt,
            question_text="Soru",
            correct_answer="obtain",
        )
        self.question.words.set([self.word])

    def test_case_and_whitespace_insensitive(self):
        self.question.check_answer("  Obtain ")
        self.assertTrue(self.question.is_correct)

    def test_clearly_wrong_answer_is_rejected(self):
        self.question.check_answer("banana")
        self.assertFalse(self.question.is_correct)

    def test_abbreviations_are_ignored(self):
        self.question.correct_answer = "give sth up"
        self.question.save()
        self.question.check_answer("give up")
        self.assertTrue(self.question.is_correct)


@skipUnless(settings.QUIZZES_ENABLED,
            "Quizler yeni kelime modeline taşınana kadar kapalı "
            "(settings.QUIZZES_ENABLED). Soru üreteçleri eski alan adlarını kullanıyor.")
class DistractorTests(TestCase):
    """Kullanıcıya asla 'Yanlış Seçenek 1' gibi sahte şık gösterilmemeli."""

    FAKE_MARKERS = ("Yanlış Seçenek", "—1—", "—2—", "—3—")

    def setUp(self):
        self.user = User.objects.create_user(username="dist_user", password="Sifre1234")
        # Kullanıcının listesinde SADECE 1 kelime var -> çeldirici havuzu boş
        self.word = make_word("obtain", "elde etmek", explanation="to get something")
        self.link = UserWordLink.objects.create(user=self.user, word=self.word)
        # Site genelinde base kelimeler var
        for i in range(10):
            make_word(f"base{i}", f"temel{i}", explanation=f"base explanation {i}",
                      isBaseWord=True, wordLevel="101")
        self.attempt = QuizAttempt.objects.create(
            owner=self.user, totalQuestion=1, quizType=QuizType.MULTIPLE_CHOICE
        )

    def _assert_no_fake_options(self, options):
        for _label, text in options:
            for marker in self.FAKE_MARKERS:
                self.assertNotIn(marker, text, f"sahte şık üretildi: {text}")

    def test_multiple_choice_has_no_fake_options(self):
        generate_mc_question(self.link, self.attempt, [self.word])
        question = MultipleChoiceQuestion.objects.get(attempt=self.attempt)
        options = question.options_as_list
        self.assertEqual(len(options), 4)
        self._assert_no_fake_options(options)
        # Şıklar birbirinden farklı olmalı
        self.assertEqual(len({text for _, text in options}), 4)

    def test_synonym_question_has_no_fake_options(self):
        self.word.synonyms = "acquire, gain"
        self.word.save()
        generate_synonym_antonym_question(self.link, self.attempt, [self.word])
        question = SynonymAntonymQuestion.objects.get(attempt=self.attempt)
        options = question.options_as_list
        self.assertEqual(len(options), 4)
        self._assert_no_fake_options(options)
        correct_text = dict(options)[question.correct_option]
        self.assertIn(correct_text, ("acquire", "gain"))

    def test_synonym_question_skipped_when_no_data(self):
        generate_synonym_antonym_question(self.link, self.attempt, [self.word])
        self.assertEqual(SynonymAntonymQuestion.objects.count(), 0)


# ---------------------------------------------------------------------------
# Boşluk doldurma (cloze) soruları
# ---------------------------------------------------------------------------

from quizzes.models import FillInTheBlankQuestion
from quizzes.question_generator import (
    build_blank_for_word,
    can_generate_blank,
    generate_fill_blank_question,
    _surface_forms,
)

BLANK = FillInTheBlankQuestion.BLANK


@skipUnless(settings.QUIZZES_ENABLED,
            "Quizler yeni kelime modeline taşınana kadar kapalı "
            "(settings.QUIZZES_ENABLED). Soru üreteçleri eski alan adlarını kullanıyor.")
class MaskWordTests(TestCase):
    """
    Cümlede kelimeyi bulup boşluğa çevirme.

    Asıl zorluk: örnek cümlede kelimenin kök hâli değil çekimli hâli geçiyor
    olabilir. Kök hâli körü körüne aramak soruların çoğunu üretilemez yapardı.
    """

    def test_masks_base_form(self):
        word = make_word("retain", "elde tutmak",
                         exampleSentence1="They retain full control of the company.")
        masked, matched = build_blank_for_word(word)
        self.assertEqual(matched, "retain")
        self.assertIn(BLANK, masked)
        self.assertNotIn("retain", masked)

    def test_masks_past_tense(self):
        word = make_word("retain", "elde tutmak",
                         exampleSentence1="The company retained most of its customers.")
        masked, matched = build_blank_for_word(word)
        self.assertEqual(matched, "retained")
        self.assertEqual(masked, f"The company {BLANK} most of its customers.")

    def test_masks_doubled_consonant_form(self):
        word = make_word("stop", "durmak",
                         exampleSentence1="The bus stopped at the corner.")
        masked, matched = build_blank_for_word(word)
        self.assertEqual(matched, "stopped")

    def test_masks_y_to_ied_form(self):
        word = make_word("apply", "başvurmak",
                         exampleSentence1="She applied for the position last week.")
        masked, matched = build_blank_for_word(word)
        self.assertEqual(matched, "applied")

    def test_uses_v2_form_field(self):
        word = make_word("take", "almak", isVerb=True, v2Form="took", v3Form="taken",
                         exampleSentence1="He took the wrong bus this morning.")
        masked, matched = build_blank_for_word(word)
        self.assertEqual(matched, "took")

    def test_longer_form_wins_so_no_leftover_suffix(self):
        """'retain' önce eşleşirse cümlede ortada 'ed' kalıntısı kalırdı."""
        word = make_word("retain", "elde tutmak",
                         exampleSentence1="They retained it.")
        masked, _ = build_blank_for_word(word)
        self.assertNotIn("ed", masked.replace(BLANK, ""))

    def test_falls_back_to_second_sentence(self):
        word = make_word("obtain", "elde etmek",
                         exampleSentence1="No relevant word here at all.",
                         exampleSentence2="You can obtain a copy online.")
        masked, matched = build_blank_for_word(word)
        self.assertEqual(matched, "obtain")
        self.assertIn("copy online", masked)

    def test_falls_back_to_collocations(self):
        word = make_word("retain", "elde tutmak",
                         exampleSentence1="Nothing relevant in this sentence.",
                         collocations="retain information, retain control")
        masked, matched = build_blank_for_word(word)
        self.assertEqual(matched, "retain")
        # Collocation'lar da rastgele seçiliyor; ikisinden biri gelmeli
        self.assertIn(masked, (f"{BLANK} information", f"{BLANK} control"))

    def test_collocation_fallback_is_deterministic_when_not_randomized(self):
        word = make_word("retain", "elde tutmak",
                         exampleSentence1="Nothing relevant in this sentence.",
                         collocations="retain information, retain control")
        masked, _ = build_blank_for_word(word, randomize=False)
        self.assertEqual(masked, f"{BLANK} information")

    def test_returns_none_when_word_is_absent(self):
        word = make_word("obtain", "elde etmek",
                         exampleSentence1="Nothing relevant in this sentence.")
        self.assertIsNone(build_blank_for_word(word))
        self.assertFalse(can_generate_blank(word))

    def test_does_not_match_word_inside_another_word(self):
        """'ret' kelimesi 'return' içinde eşleşmemeli (word boundary)."""
        word = make_word("ret", "çürütmek",
                         exampleSentence1="They will return tomorrow.")
        self.assertIsNone(build_blank_for_word(word))

    def test_inflections_can_be_disabled(self):
        """Çoktan seçmeli cloze yalnızca kök hâli maskeler; şık boşluğa oturmalı."""
        word = make_word("retain", "elde tutmak",
                         exampleSentence1="The company retained its customers.")
        self.assertIsNone(build_blank_for_word(word, include_inflections=False))
        self.assertIsNotNone(build_blank_for_word(word, include_inflections=True))

    def test_surface_forms_are_sorted_longest_first(self):
        word = make_word("retain", "elde tutmak")
        forms = _surface_forms(word)
        self.assertEqual(forms, sorted(forms, key=len, reverse=True))


@skipUnless(settings.QUIZZES_ENABLED,
            "Quizler yeni kelime modeline taşınana kadar kapalı "
            "(settings.QUIZZES_ENABLED). Soru üreteçleri eski alan adlarını kullanıyor.")
class FillInTheBlankQuestionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="fb_user", password="Sifre1234")
        self.word = make_word("retain", "elde tutmak",
                              exampleSentence1="The company retained most of its customers.")
        self.link = UserWordLink.objects.create(user=self.user, word=self.word)
        self.attempt = QuizAttempt.objects.create(
            owner=self.user, totalQuestion=1, quizType=QuizType.FILL_BLANK
        )

    def _make_question(self):
        created = generate_fill_blank_question(self.link, self.attempt)
        self.assertTrue(created)
        return FillInTheBlankQuestion.objects.get(attempt=self.attempt)

    def test_question_is_created_with_both_forms_accepted(self):
        question = self._make_question()
        self.assertIn(BLANK, question.sentence_with_blank)
        self.assertEqual(question.correct_answer, "retained")
        self.assertIn("retain", question.accepted_answers_list)
        self.assertIn("retained", question.accepted_answers_list)
        self.assertEqual(question.hint, "elde tutmak")
        self.assertEqual(list(question.words.all()), [self.word])

    def test_base_form_is_accepted(self):
        question = self._make_question()
        question.check_answer("retain")
        self.assertTrue(question.is_correct)

    def test_inflected_form_is_accepted(self):
        question = self._make_question()
        question.check_answer("  Retained  ")
        self.assertTrue(question.is_correct)

    def test_trailing_punctuation_is_ignored(self):
        question = self._make_question()
        question.check_answer("retain.")
        self.assertTrue(question.is_correct)

    def test_similar_but_different_word_is_rejected(self):
        """'retail' ile 'retain' arasındaki benzerlik gerçek bir yazım hatasınınkiyle
        aynı seviyede; bu yüzden burada tolerans uygulanmıyor."""
        question = self._make_question()
        question.check_answer("retail")
        self.assertFalse(question.is_correct)

    def test_empty_answer_is_wrong(self):
        question = self._make_question()
        question.check_answer("")
        self.assertFalse(question.is_correct)

    def test_answer_updates_word_stats_once(self):
        question = self._make_question()
        question.check_answer("retain")
        link = UserWordLink.objects.get(pk=self.link.pk)
        self.assertEqual(link.correctCount, 1)
        self.assertEqual(link.wrongCount, 0)

    def test_generation_is_skipped_when_no_blank_possible(self):
        word = make_word("obtain", "elde etmek",
                         exampleSentence1="Nothing relevant in this sentence.")
        link = UserWordLink.objects.create(user=self.user, word=word)
        self.assertFalse(generate_fill_blank_question(link, self.attempt))
        self.assertEqual(FillInTheBlankQuestion.objects.count(), 0)

    def test_template_name_comes_from_the_class(self):
        question = self._make_question()
        self.assertEqual(question.template_name, "FillInTheBlankQuestion")


@skipUnless(settings.QUIZZES_ENABLED,
            "Quizler yeni kelime modeline taşınana kadar kapalı "
            "(settings.QUIZZES_ENABLED). Soru üreteçleri eski alan adlarını kullanıyor.")
class ScoringAcrossQuestionTypesTests(TestCase):
    """
    calculateScore artık QUESTION_RELATED_NAMES listesini dolaşıyor.
    Bu test, listeye eklenen bir tipin puanlamaya gerçekten dahil olduğunu
    ve eşleştirmenin kısmi puanının korunduğunu doğrular.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="score_user", password="Sifre1234")
        self.words = [
            make_word(f"scoreword{i}", f"anlam{i}",
                      exampleSentence1=f"We use scoreword{i} here.")
            for i in range(5)
        ]
        for word in self.words:
            UserWordLink.objects.create(user=self.user, word=word)
        self.attempt = QuizAttempt.objects.create(
            owner=self.user, totalQuestion=8, quizType=QuizType.MIXED
        )

    def test_score_includes_every_question_type(self):
        # 1 doğru çoktan seçmeli
        mc = MultipleChoiceQuestion.objects.create(
            attempt=self.attempt, question_text="s", options_data="A:x_#_B:y",
            correct_option="A", is_correct=True)
        mc.words.set([self.words[0]])

        # 1 yanlış yazma
        wq = WritingQuestion.objects.create(
            attempt=self.attempt, question_text="s", correct_answer="x", is_correct=False)
        wq.words.set([self.words[1]])

        # 1 doğru boşluk doldurma
        fb = FillInTheBlankQuestion.objects.create(
            attempt=self.attempt, sentence_with_blank=f"We use {BLANK} here.",
            correct_answer="scoreword2", is_correct=True)
        fb.words.set([self.words[2]])

        # 5'li eşleştirme: 3 doğru 2 yanlış
        mq = MatchingQuestion.objects.create(
            attempt=self.attempt, right_col_order_ids="1;2;3;4;5",
            word_count=5, correct_matches=3, wrong_matches=2)
        mq.words.set(self.words)

        self.attempt.calculateScore()

        self.assertEqual(self.attempt.totalCorrect, 1 + 0 + 1 + 3)
        self.assertEqual(self.attempt.totalWrong, 0 + 1 + 0 + 2)
        self.assertTrue(self.attempt.isCompleted)

    def test_all_questions_is_sorted_by_id(self):
        for i in range(3):
            q = WritingQuestion.objects.create(
                attempt=self.attempt, question_text=f"q{i}", correct_answer="x")
            q.words.set([self.words[i]])

        questions = self.attempt.all_questions()
        self.assertEqual([q.id for q in questions], sorted(q.id for q in questions))
        self.assertEqual(len(questions), 3)


@skipUnless(settings.QUIZZES_ENABLED,
            "Quizler yeni kelime modeline taşınana kadar kapalı "
            "(settings.QUIZZES_ENABLED). Soru üreteçleri eski alan adlarını kullanıyor.")
class ClozeMultipleChoiceTests(TestCase):
    """Katman 1: çoktan seçmeli içindeki boşluk doldurma biçimi."""

    def setUp(self):
        self.user = User.objects.create_user(username="cloze_user", password="Sifre1234")
        self.word = make_word("retain", "elde tutmak",
                              exampleSentence1="They retain full control of the company.")
        self.link = UserWordLink.objects.create(user=self.user, word=self.word)
        for i in range(10):
            make_word(f"base{i}", f"temel{i}", isBaseWord=True, wordLevel="101")
        self.attempt = QuizAttempt.objects.create(
            owner=self.user, totalQuestion=1, quizType=QuizType.MULTIPLE_CHOICE
        )

    def test_cloze_variant_can_be_generated(self):
        """20 denemede en az bir kez cloze biçimi seçilmeli."""
        seen_cloze = False
        for _ in range(20):
            attempt = QuizAttempt.objects.create(
                owner=self.user, totalQuestion=1, quizType=QuizType.MULTIPLE_CHOICE)
            generate_mc_question(self.link, attempt, [self.word])
            question = MultipleChoiceQuestion.objects.get(attempt=attempt)
            if BLANK in question.question_text:
                seen_cloze = True
                # Doğru şık kelimenin KÖK hâli olmalı ki boşluğa dilbilgisel otursun
                correct_text = dict(question.options_as_list)[question.correct_option]
                self.assertEqual(correct_text, "retain")
                break
        self.assertTrue(seen_cloze, "cloze biçimi hiç üretilmedi")


@skipUnless(settings.QUIZZES_ENABLED,
            "Quizler yeni kelime modeline taşınana kadar kapalı "
            "(settings.QUIZZES_ENABLED). Soru üreteçleri eski alan adlarını kullanıyor.")
class FillBlankQuizFlowTests(TestCase):
    """
    Uçtan uca akış: quiz oluşturma -> soru sayfası -> cevap -> sonuç sayfası.

    Bu test asıl olarak TEMPLATE'leri koruyor. Yeni bir soru tipi eklenirken
    quizPage.html veya quizComplete.html'de dal açmayı unutmak, birim
    testlerinden geçen ama tarayıcıda boş/patlak görünen bir sayfa üretir.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="flow_user", password="Sifre1234")
        self.client.login(username="flow_user", password="Sifre1234")

        self.words = []
        for i in range(5):
            word = make_word(
                f"flowword{i}", f"anlam{i}",
                exampleSentence1=f"The team flowword{i} the results carefully.",
                collocations=f"flowword{i} data, flowword{i} results",
            )
            UserWordLink.objects.create(user=self.user, word=word)
            self.words.append(word)

    def test_attempt_quiz_page_lists_the_new_type(self):
        response = self.client.get(reverse("attempt_quiz"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="fill_blank"')

    def test_full_fill_blank_quiz_flow(self):
        response = self.client.post(
            reverse("attempt_quiz"),
            {"quizType": "fill_blank", "totalQuestion": "5"},
        )
        self.assertEqual(response.status_code, 302)

        attempt = QuizAttempt.objects.get(owner=self.user)
        self.assertEqual(attempt.quizType, QuizType.FILL_BLANK)
        self.assertEqual(FillInTheBlankQuestion.objects.filter(attempt=attempt).count(), 5)

        questions = attempt.all_questions()

        for index, question in enumerate(questions, start=1):
            page = self.client.get(
                reverse("quiz_page", args=[attempt.id, index])
            )
            self.assertEqual(page.status_code, 200)
            self.assertContains(page, BLANK)
            self.assertContains(page, 'name="answer"')

            self.client.post(
                reverse("quiz_page", args=[attempt.id, index]),
                {"answer": question.correct_answer, "time_taken": "4.2"},
            )

        complete = self.client.get(reverse("quiz_complete", args=[attempt.id]))
        self.assertEqual(complete.status_code, 200)

        attempt.refresh_from_db()
        self.assertTrue(attempt.isCompleted)
        self.assertEqual(attempt.totalCorrect, 5)
        self.assertEqual(attempt.totalWrong, 0)
        self.assertContains(complete, "Boşluk Doldurma Sorusu")

    def test_quiz_is_refused_when_no_word_can_produce_a_blank(self):
        UserWordLink.objects.filter(user=self.user).delete()
        for i in range(5):
            word = make_word(f"absent{i}", f"anlam{i}",
                             exampleSentence1="Nothing relevant in this sentence.")
            UserWordLink.objects.create(user=self.user, word=word)

        response = self.client.post(
            reverse("attempt_quiz"),
            {"quizType": "fill_blank", "totalQuestion": "5"},
            follow=True,
        )
        self.assertEqual(QuizAttempt.objects.count(), 0)
        text = " ".join(str(m) for m in response.context["messages"])
        self.assertIn("yeterli kelime yok", text)

    def test_mixed_quiz_includes_fill_blank_questions(self):
        """Karma quiz'de üretim gerektiren soruların bir kısmı boşluk doldurma olmalı."""
        self.client.post(
            reverse("attempt_quiz"),
            {"quizType": "mixed", "totalQuestion": "5"},
        )
        attempt = QuizAttempt.objects.get(owner=self.user)

        self.assertGreaterEqual(
            FillInTheBlankQuestion.objects.filter(attempt=attempt).count(), 1
        )
        # Toplam soru sayısı bozulmamalı: boşluk doldurma, yazma sorularının
        # yerine geçiyor; üstüne eklenmiyor.
        self.assertEqual(len(attempt.all_questions()), 5)


@skipUnless(settings.QUIZZES_ENABLED,
            "Quizler yeni kelime modeline taşınana kadar kapalı "
            "(settings.QUIZZES_ENABLED). Soru üreteçleri eski alan adlarını kullanıyor.")
class BlankSentenceSelectionTests(TestCase):
    """Boşluk doldurma, kelimenin DOLU cümleleri arasından rastgele seçmeli."""

    def test_empty_sentence_slots_are_skipped(self):
        word = make_word(
            "retain", "elde tutmak",
            exampleSentence1="Nothing relevant in this first one.",
            exampleSentence2=None,
            exampleSentence3="   ",
            exampleSentence7="The board will retain the original plan.",
        )
        masked, matched = build_blank_for_word(word, randomize=False)
        self.assertEqual(matched, "retain")
        self.assertIn("original plan", masked)

    def test_selection_varies_across_generations(self):
        """
        Aynı kelime her sorulduğunda aynı cümle gelirse kelime tek bağlama
        bağlanır. Farklı cümlelerin seçilebildiğini doğruluyoruz.
        """
        word = make_word(
            "retain", "elde tutmak",
            exampleSentence1="Alpha will retain the title.",
            exampleSentence2="Beta managed to retain its lead.",
            exampleSentence3="Gamma could not retain the crowd.",
        )

        seen = set()
        for _ in range(40):
            masked, _matched = build_blank_for_word(word)
            seen.add(masked.split()[0])

        self.assertGreater(len(seen), 1, "her seferinde aynı cümle seçiliyor")
        self.assertLessEqual(seen, {"Alpha", "Beta", "Gamma"})

    def test_randomize_false_is_deterministic(self):
        word = make_word(
            "retain", "elde tutmak",
            exampleSentence1="Alpha will retain the title.",
            exampleSentence2="Beta managed to retain its lead.",
        )
        results = {build_blank_for_word(word, randomize=False)[0] for _ in range(10)}
        self.assertEqual(len(results), 1)

    def test_eligibility_check_uses_all_ten_slots(self):
        word = make_word(
            "obtain", "elde etmek",
            exampleSentence1="Nothing relevant here.",
            exampleSentence10="You can obtain a copy online.",
        )
        self.assertTrue(can_generate_blank(word))

    def test_word_absent_from_every_sentence_is_ineligible(self):
        word = make_word(
            "obtain", "elde etmek",
            exampleSentence1="Nothing relevant here.",
            exampleSentence5="Still nothing relevant.",
        )
        self.assertFalse(can_generate_blank(word))


class WordAnalysisTests(TestCase):
    """
    Bilgi Analizi: en çok yanlış yapılandan en iyi bilinene sıralı liste.
    """

    def setUp(self):
        from users.models import User

        self.user = User.objects.create_user(username="analiz", password="Sifre1234")
        self.client.login(username="analiz", password="Sifre1234")

    def _link(self, kelime_adi, correct, wrong, user=None):
        from words.models import UserWordLink, Word

        kelime = make_word(kelime_adi, "anlam", level="401",
                           is_base=True, visibility="public")
        return UserWordLink.objects.create(
            user=user or self.user, word=kelime,
            correctCount=correct, wrongCount=wrong,
        )

    def _rows(self):
        cevap = self.client.get(reverse("word_analysis"))
        self.assertEqual(cevap.status_code, 200)
        return cevap.context["rows"]

    def test_worst_words_come_first(self):
        self._link("iyi", correct=9, wrong=1)       # %90
        self._link("orta", correct=5, wrong=5)      # %50
        self._link("kotu", correct=1, wrong=9)      # %10

        siralama = [satir["word"].text for satir in self._rows()]
        self.assertEqual(siralama, ["kotu", "orta", "iyi"])

    def test_accuracy_is_a_percentage(self):
        self._link("yarim", correct=1, wrong=3)     # %25
        satir = self._rows()[0]
        self.assertEqual(satir["accuracy"], 25)
        self.assertEqual(satir["attempts"], 4)

    def test_equal_accuracy_puts_the_more_attempted_word_first(self):
        """20 denemede %50, 2 denemede %50'den daha güvenilir bir sinyal."""
        self._link("azdenenen", correct=1, wrong=1)
        self._link("cokdenenen", correct=10, wrong=10)

        siralama = [satir["word"].text for satir in self._rows()]
        self.assertEqual(siralama[0], "cokdenenen")

    def test_never_attempted_words_are_excluded_but_counted(self):
        self._link("calisilan", correct=2, wrong=1)
        self._link("hicbakilmayan", correct=0, wrong=0)

        cevap = self.client.get(reverse("word_analysis"))
        adlar = [satir["word"].text for satir in cevap.context["rows"]]
        self.assertEqual(adlar, ["calisilan"])
        self.assertEqual(cevap.context["untouched_count"], 1)

    def test_only_the_users_own_list_is_analysed(self):
        from users.models import User

        baskasi = User.objects.create_user(username="baska", password="Sifre1234")
        self._link("benimki", correct=1, wrong=1)
        self._link("onunki", correct=1, wrong=1, user=baskasi)

        adlar = [satir["word"].text for satir in self._rows()]
        self.assertEqual(adlar, ["benimki"])

    def test_colour_runs_from_red_to_green(self):
        self._link("sifir", correct=0, wrong=4)     # %0
        self._link("tam", correct=4, wrong=0)       # %100

        satirlar = {s["word"].text: s["hue"] for s in self._rows()}
        self.assertEqual(satirlar["sifir"], 0)                      # kırmızı
        self.assertEqual(satirlar["tam"], 130)                      # yeşil
        self.assertLess(satirlar["sifir"], satirlar["tam"])

    def test_summary_shows_total_attempts(self):
        """Oran tek başına yanıltıcı; toplam deneme sayısı da görünmeli."""
        self._link("bir", correct=3, wrong=1)
        self._link("iki", correct=1, wrong=1)

        cevap = self.client.get(reverse("word_analysis"))
        self.assertEqual(cevap.context["total_attempts"], 6)
        self.assertEqual(cevap.context["overall_accuracy"], 67)
        self.assertEqual(cevap.context["studied_count"], 2)

    def test_row_links_to_the_word(self):
        link = self._link("tiklanabilir", correct=1, wrong=1)
        html = self.client.get(reverse("word_analysis")).content.decode()
        self.assertIn(reverse("word_detail", args=[link.word.id]), html)

    def test_page_is_paginated(self):
        from quizzes.views import ANALYSIS_DEFAULT_PER_PAGE

        for i in range(ANALYSIS_DEFAULT_PER_PAGE + 5):
            self._link(f"kelime{i:03d}", correct=i % 4, wrong=1)

        cevap = self.client.get(reverse("word_analysis"))
        self.assertTrue(cevap.context["is_paginated"])
        self.assertEqual(len(cevap.context["rows"]), ANALYSIS_DEFAULT_PER_PAGE)

    def test_empty_state_when_nothing_studied(self):
        html = self.client.get(reverse("word_analysis")).content.decode()
        self.assertIn("Henüz analiz edilecek bir şey yok", html)

    def test_anonymous_user_sees_the_login_screen(self):
        self.client.logout()
        cevap = self.client.get(reverse("word_analysis"))
        self.assertEqual(cevap.status_code, 200)
        self.assertIn("önce giriş yapın", cevap.content.decode())

    def test_analysis_is_the_third_exercise_tab(self):
        for url in (reverse("learn_pass_page"), reverse("profile_quizzes"), reverse("word_analysis")):
            with self.subTest(url=url):
                html = self.client.get(url, follow=True).content.decode()
                self.assertIn(reverse("word_analysis"), html)
                self.assertIn(">Analiz<", re.sub(r">\s+", ">", re.sub(r"\s+<", "<", html)))


@skipUnless(settings.QUIZZES_ENABLED,
            "Quizler yeni kelime modeline taşınana kadar kapalı "
            "(settings.QUIZZES_ENABLED). Soru üreteçleri eski alan adlarını kullanıyor.")
class QuizStatsChartTests(TestCase):
    """İstatistik grafiği: beş soru tipi, renkleri ve doğruluk oranları."""

    def setUp(self):
        self.user = User.objects.create_user(username="grafik", password="Sifre1234")
        self.client.login(username="grafik", password="Sifre1234")

    def _attempt(self):
        return QuizAttempt.objects.create(owner=self.user, totalQuestion=4, isCompleted=True)

    def _word(self, ad="kelime"):
        return make_word(ad, "anlam", level="401", is_base=True, visibility="public")

    def _types(self):
        cevap = self.client.get(reverse("profile_quizzes"))
        self.assertEqual(cevap.status_code, 200)
        return {tip["key"]: tip for tip in cevap.context["quiz_types"]}

    def test_all_five_question_types_are_present(self):
        self.assertEqual(set(self._types()), {"mq", "mc", "wq", "sa", "fb"})

    def test_every_type_has_its_own_colour(self):
        renkler = [tip["color"] for tip in self._types().values()]
        self.assertEqual(len(renkler), len(set(renkler)), "Renkler birbirinden farklı olmalı")

    def test_synonym_antonym_counts_are_reported(self):
        deneme = self._attempt()
        SynonymAntonymQuestion.objects.create(
            attempt=deneme, question_text="?", options_data="A:x_#_B:y",
            correct_option="A", is_correct=True,
        )
        SynonymAntonymQuestion.objects.create(
            attempt=deneme, question_text="?", options_data="A:x_#_B:y",
            correct_option="A", is_correct=False,
        )
        sa = self._types()["sa"]
        self.assertEqual((sa["correct"], sa["wrong"]), (1, 1))

    def test_fill_in_the_blank_counts_are_reported(self):
        deneme = self._attempt()
        FillInTheBlankQuestion.objects.create(
            attempt=deneme, sentence_with_blank="A ____ sentence.",
            correct_answer="fb1", is_correct=True,
        )
        fb = self._types()["fb"]
        self.assertEqual((fb["correct"], fb["wrong"]), (1, 0))

    def test_accuracy_percentages_are_calculated(self):
        deneme = self._attempt()
        for dogru in (True, True, True, False):
            MultipleChoiceQuestion.objects.create(
                attempt=deneme, question_text="?", options_data="A:x_#_B:y",
                correct_option="A", is_correct=dogru,
            )
        mc = self._types()["mc"]
        self.assertEqual(mc["total"], 4)
        self.assertEqual(mc["correct_pct"], 75)
        self.assertEqual(mc["wrong_pct"], 25)

    def test_untouched_type_does_not_divide_by_zero(self):
        tip = self._types()["fb"]
        self.assertEqual((tip["total"], tip["correct_pct"], tip["wrong_pct"]), (0, 0, 0))

    def test_page_renders_a_chart_for_every_type_on_mobile(self):
        deneme = self._attempt()
        MultipleChoiceQuestion.objects.create(
            attempt=deneme, question_text="?", options_data="A:x_#_B:y",
            correct_option="A", is_correct=True,
        )
        html = self.client.get(reverse("profile_quizzes")).content.decode()
        for anahtar in ("mq", "mc", "wq", "sa", "fb"):
            with self.subTest(key=anahtar):
                self.assertIn(f'id="chart-{anahtar}"', html)
        self.assertIn('id="statsChart"', html)

    def test_empty_state_when_no_quiz_completed(self):
        cevap = self.client.get(reverse("profile_quizzes"))
        self.assertFalse(cevap.context["has_quiz_data"])
        self.assertIn("Henüz tamamlanmış bir quiz yok", cevap.content.decode())


@skipUnless(settings.QUIZZES_ENABLED,
            "Quizler yeni kelime modeline taşınana kadar kapalı "
            "(settings.QUIZZES_ENABLED). Soru üreteçleri eski alan adlarını kullanıyor.")
class QuizPageUsabilityTests(TestCase):
    """
    Quiz sayfası: tıklama alanı ve Enter kısayolu.

    Bunlar şablonda yaşayan davranışlar; testler o işaretlemenin yanlışlıkla
    geri alınmasını yakalıyor.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="quizkullanim", password="Sifre1234")
        self.client.login(username="quizkullanim", password="Sifre1234")

        self.word = make_word("immaculate", "tertemiz", level="401", is_base=True,
                              visibility="public")
        self.attempt = QuizAttempt.objects.create(owner=self.user, totalQuestion=1)
        soru = MultipleChoiceQuestion.objects.create(
            attempt=self.attempt, question_text="immaculate ne demek?",
            options_data="A:tertemiz_#_B:kirli_#_C:eski_#_D:yeni",
            correct_option="A",
        )
        soru.words.set([self.word])

    def _page(self):
        cevap = self.client.get(reverse("quiz_page", kwargs={
            "attempt_id": self.attempt.id, "question_index": 1,
        }))
        self.assertEqual(cevap.status_code, 200)
        return cevap.content.decode()

    def test_the_whole_bordered_box_is_the_click_target(self):
        """
        Kenarlık ve dolgu label'ın üzerinde olmalı. Eskiden kenarlık dıştaki
        div'de olduğu için kutunun iç boşluğuna yapılan tıklamalar boşa
        gidiyordu.
        """
        html = self._page()
        self.assertIn("<label class=\"mc-option-box", html)
        self.assertNotIn("<div class=\"mc-option-box", html)

    def test_option_box_carries_its_own_border_and_padding(self):
        html = self._page()
        kutu_baslangic = html.index('<label class="mc-option-box')
        kutu = html[kutu_baslangic:kutu_baslangic + 700]
        self.assertIn("border-2", kutu)
        self.assertIn("p-3", kutu)
        self.assertIn("touch-action: manipulation", kutu)

    def test_enter_shortcut_exists(self):
        html = self._page()
        self.assertIn("e.key !== 'Enter'", html)
        self.assertIn("function hasAnswer()", html)

    def test_hover_styles_do_not_eat_the_first_tap(self):
        """Dokunmatikte hover: sınıfları ilk dokunuşu yutuyordu."""
        html = self._page()
        self.assertIn("hoverOnlyWhenSupported: true", html)
