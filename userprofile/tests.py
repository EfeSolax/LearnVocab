"""
Kelime ekleme / düzenleme formları için testler.

Özellikle collocation (kullanım kalıpları) alanının form -> view -> model
zincirinin tamamında çalıştığını doğrular. Bu alan Alpine.js ile birden çok
input olarak gönderilip view'da virgülle birleştiriliyor; zincirin bir halkası
kopsa sayfa yine 200 döner ama veri sessizce kaybolurdu.
"""

from django.test import TestCase
from django.urls import reverse

from users.models import User
from words.models import Word, UserWordLink


class WordFormCollocationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="formuser", password="Sifre1234")
        self.client.login(username="formuser", password="Sifre1234")

    def _payload(self, **overrides):
        data = {
            "word_text": "retain",
            "translation_tr": "elde tutmak",
            "description": "to keep something",
            "notes": "verb",
            "sentence_1": "They retain full control.",
            "visibility": "private",
            "level": "Belirtilmemiş",
            "synonym": ["keep", "hold"],
            "antonym": ["lose"],
            "collocation": ["retain information", " retain control ", ""],
        }
        data.update(overrides)
        return data

    def test_add_word_page_renders_collocation_inputs(self):
        response = self.client.get(reverse("add_word"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="collocation"')
        self.assertContains(response, "Kullanım Kalıpları")

    def test_add_word_saves_collocations(self):
        self.client.post(reverse("add_word"), self._payload())

        word = Word.objects.get(englishWord="retain")
        self.assertEqual(word.collocations, "retain information, retain control")
        self.assertEqual(
            word.collocations_list, ["retain information", "retain control"]
        )
        self.assertEqual(word.synonyms, "keep, hold")
        self.assertTrue(UserWordLink.objects.filter(user=self.user, word=word).exists())

    def test_add_word_without_collocations_stores_none(self):
        self.client.post(reverse("add_word"), self._payload(collocation=[]))
        word = Word.objects.get(englishWord="retain")
        self.assertIsNone(word.collocations)

    def test_edit_word_page_prefills_collocations(self):
        self.client.post(reverse("add_word"), self._payload())
        word = Word.objects.get(englishWord="retain")

        response = self.client.get(reverse("edit_word", args=[word.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "retain information")
        self.assertContains(response, 'name="collocation"')

    def test_edit_word_updates_collocations(self):
        self.client.post(reverse("add_word"), self._payload())
        word = Word.objects.get(englishWord="retain")

        self.client.post(
            reverse("edit_word", args=[word.id]),
            self._payload(collocation=["retain its shape"]),
        )

        word.refresh_from_db()
        self.assertEqual(word.collocations, "retain its shape")

    def test_word_detail_shows_collocations(self):
        self.client.post(reverse("add_word"), self._payload())
        word = Word.objects.get(englishWord="retain")

        response = self.client.get(reverse("word_detail", args=[word.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kullanım Kalıpları")
        self.assertContains(response, "retain information")


class WordFormExampleSentenceTests(TestCase):
    """Formdaki 10 örnek cümle alanı: 1'i zorunlu, 9'u açılır panelde."""

    def setUp(self):
        self.user = User.objects.create_user(username="sentenceuser", password="Sifre1234")
        self.client.login(username="sentenceuser", password="Sifre1234")

    def _payload(self, **overrides):
        data = {
            "word_text": "retain",
            "translation_tr": "elde tutmak",
            "description": "to keep something",
            "notes": "kişisel notum",
            "sentence_1": "They retain full control.",
            "visibility": "private",
            "level": "Belirtilmemiş",
        }
        data.update(overrides)
        return data

    def test_add_page_renders_all_ten_sentence_fields(self):
        response = self.client.get(reverse("add_word"))
        self.assertEqual(response.status_code, 200)
        for i in range(1, 11):
            self.assertContains(response, f'name="sentence_{i}"')
        self.assertContains(response, "showMoreSentences")
        self.assertContains(response, "Ek örnek cümle ekle")

    def test_all_sentences_are_saved(self):
        payload = self._payload()
        for i in range(2, 11):
            payload[f"sentence_{i}"] = f"Sentence number {i} about retain."
        self.client.post(reverse("add_word"), payload)

        word = Word.objects.get(englishWord="retain")
        self.assertEqual(len(word.example_sentences), 10)
        self.assertEqual(word.exampleSentence10, "Sentence number 10 about retain.")

    def test_blank_sentences_are_stored_as_none(self):
        self.client.post(
            reverse("add_word"),
            self._payload(sentence_4="   ", sentence_7="Only this extra one."),
        )
        word = Word.objects.get(englishWord="retain")
        self.assertIsNone(word.exampleSentence4)
        self.assertIsNone(word.exampleSentence2)
        self.assertEqual(word.exampleSentence7, "Only this extra one.")
        self.assertEqual(len(word.example_sentences), 2)

    def test_edit_page_prefills_and_opens_panel_when_extras_exist(self):
        self.client.post(
            reverse("add_word"), self._payload(sentence_5="An extra sentence to retain.")
        )
        word = Word.objects.get(englishWord="retain")

        response = self.client.get(reverse("edit_word", args=[word.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An extra sentence to retain.")
        self.assertContains(response, "showMoreSentences: true")

    def test_edit_page_keeps_panel_closed_without_extras(self):
        self.client.post(reverse("add_word"), self._payload())
        word = Word.objects.get(englishWord="retain")

        response = self.client.get(reverse("edit_word", args=[word.id]))
        self.assertContains(response, "showMoreSentences: false")

    def test_edit_can_clear_an_extra_sentence(self):
        self.client.post(
            reverse("add_word"), self._payload(sentence_5="An extra sentence to retain.")
        )
        word = Word.objects.get(englishWord="retain")

        self.client.post(reverse("edit_word", args=[word.id]), self._payload(sentence_5=""))
        word.refresh_from_db()
        self.assertIsNone(word.exampleSentence5)

    def test_personal_note_is_not_overwritten_by_the_example_sentence(self):
        """
        editWord.html'de 'Kişisel Not' alanı yanlışlıkla exampleSentence1 ile
        dolduruluyordu; sayfayı açıp kaydeden kullanıcı notunu kaybediyordu.
        """
        self.client.post(reverse("add_word"), self._payload())
        word = Word.objects.get(englishWord="retain")

        response = self.client.get(reverse("edit_word", args=[word.id]))

        # Not alanı kendi değeriyle dolmalı
        self.assertContains(response, "kişisel notum")

        # Örnek cümle sayfada YALNIZCA bir kez (sentence_1 alanında) geçmeli.
        # Hata varken hem sentence_1 hem de notes alanında görünüyordu.
        self.assertContains(response, "They retain full control.", count=1)


from datetime import timedelta

from django.utils import timezone


class WordSortingTests(TestCase):
    """
    Kelimelerim sayfasının sıralaması.

    "Eklenme tarihi" kelimenin oluşturulma tarihi değil, KULLANICININ onu
    listesine eklediği tarih: aynı kelime birden çok kullanıcıda olabiliyor.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="sortuser", password="Sifre1234")
        self.client.login(username="sortuser", password="Sifre1234")

        # eski -> yeni sırayla ekleniyor
        self.words = {}
        for offset, name in enumerate(["zeta", "alpha", "mu"]):
            word = Word.objects.create(
                owner=self.user, englishWord=name, meaningTr=f"{name}-tr",
                exampleSentence1=f"A sentence with {name}.",
            )
            link = UserWordLink.objects.create(user=self.user, word=word)
            UserWordLink.objects.filter(pk=link.pk).update(
                dateAdded=timezone.now() - timedelta(days=10 - offset * 5)
            )
            self.words[name] = word

    def _listed(self, **params):
        response = self.client.get(reverse("profile_words"), params)
        self.assertEqual(response.status_code, 200)
        return [w.englishWord for w in response.context["page_obj"].object_list]

    def test_default_sort_is_newest_first(self):
        self.assertEqual(self._listed(), ["mu", "alpha", "zeta"])

    def test_oldest_first(self):
        self.assertEqual(self._listed(sort="old"), ["zeta", "alpha", "mu"])

    def test_alphabetical(self):
        self.assertEqual(self._listed(sort="az"), ["alpha", "mu", "zeta"])

    def test_reverse_alphabetical(self):
        self.assertEqual(self._listed(sort="za"), ["zeta", "mu", "alpha"])

    def test_unknown_sort_falls_back_to_the_default(self):
        self.assertEqual(self._listed(sort="uydurma"), ["mu", "alpha", "zeta"])

    def test_sort_dropdown_is_rendered(self):
        response = self.client.get(reverse("profile_words"))
        self.assertContains(response, 'name="sort"')
        self.assertContains(response, "Önce en yeni")

    def test_sort_is_kept_in_pagination_links(self):
        response = self.client.get(reverse("profile_words"), {"sort": "az"})
        self.assertIn("sort=az", response.context["base_qs"])

    def test_default_sort_is_not_repeated_in_the_query_string(self):
        response = self.client.get(reverse("profile_words"))
        self.assertNotIn("sort=", response.context["base_qs"])

    def test_sort_works_together_with_search(self):
        self.assertEqual(self._listed(q="a", sort="az"), ["alpha", "zeta"])

    def test_word_without_a_link_falls_back_to_its_creation_date(self):
        """Bağlantısı olmayan kelime sıralamadan düşmemeli."""
        orphan = Word.objects.create(
            owner=self.user, englishWord="orphan", meaningTr="x",
            exampleSentence1="A sentence with orphan.",
        )
        Word.objects.filter(pk=orphan.pk).update(
            createdAt=timezone.now() - timedelta(days=100)
        )
        self.assertEqual(self._listed(sort="old")[0], "orphan")
