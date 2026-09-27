"""
Kelime çekirdeği testleri.

Kapsam: görünürlük, aile, tür, anlam, ton/üslup/alan, collocation,
kullanım kalıbı, örnek cümle, çekim biçimi, yanlış dost, deyim, kelime
bağları, kişisel anlam ve kişisel not — yani modelin her katmanı.
"""

import re

from django.contrib.auth.models import AnonymousUser
from django.core.management import call_command
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse, NoReverseMatch

from users.models import User
from words import inflect
from words.models import (
    CEFR_CHOICES, CEFR_LEVELS, Category, Collocation, ExampleSentence, Expression, FalseFriend, Meaning,
    Register, Sentiment, UsagePattern, UserMeaning, UserWordLink, UserWordNote,
    Word, WordFamily, WordRelation,
)
from words.testing import make_word
from words.views import can_view_word, visible_words_qs


class VisibilityTests(TestCase):
    """
    Görünürlük: kur kelimeleri ve "herkese açık" olanlar herkese; gizli
    kelimeler yalnızca sahibine ve listesine ekleyene.
    """

    def setUp(self):
        self.owner = User.objects.create_user(username="sahip", password="Sifre1234")
        self.stranger = User.objects.create_user(username="yabanci", password="Sifre1234")

        self.public_word = make_word("publicword", owner=self.owner,
                                     is_base=False, visibility="public")
        self.private_word = make_word("privateword", owner=self.owner,
                                      is_base=False, visibility="private")
        self.base_word = make_word("baseword", is_base=True, level="101")

    def test_owner_sees_everything_of_their_own(self):
        for word in (self.public_word, self.private_word):
            self.assertTrue(can_view_word(word, self.owner))

    def test_stranger_cannot_see_a_private_word(self):
        self.assertFalse(can_view_word(self.private_word, self.stranger))

    def test_everyone_sees_public_and_base_words(self):
        for word in (self.public_word, self.base_word):
            self.assertTrue(can_view_word(word, self.stranger))

    def test_anonymous_sees_only_public_and_base(self):
        anonim = AnonymousUser()
        self.assertTrue(can_view_word(self.public_word, anonim))
        self.assertTrue(can_view_word(self.base_word, anonim))
        self.assertFalse(can_view_word(self.private_word, anonim))

    def test_saving_a_word_grants_access(self):
        UserWordLink.objects.create(user=self.stranger, word=self.private_word)
        self.assertTrue(can_view_word(self.private_word, self.stranger))

    def test_visible_words_qs_matches_can_view_word(self):
        """Liste sorgusu ile tekil kontrol aynı sonucu vermeli."""
        for kullanici in (self.owner, self.stranger, AnonymousUser()):
            with self.subTest(kullanici=str(kullanici)):
                sorgudan = set(visible_words_qs(kullanici).values_list("id", flat=True))
                tekil = {w.id for w in Word.objects.all() if can_view_word(w, kullanici)}
                self.assertEqual(sorgudan, tekil)

    def test_word_detail_redirects_for_unauthorized_user(self):
        self.client.login(username="yabanci", password="Sifre1234")
        cevap = self.client.get(reverse("word_detail", args=[self.private_word.id]))
        self.assertEqual(cevap.status_code, 302)

    def test_word_detail_works_for_owner(self):
        self.client.login(username="sahip", password="Sifre1234")
        cevap = self.client.get(reverse("word_detail", args=[self.private_word.id]))
        self.assertEqual(cevap.status_code, 200)


class WordFamilyTests(TestCase):
    """Aile: öğrenmenin birimi tek kelime değil, türev ailesi."""

    def setUp(self):
        self.aile = WordFamily.objects.create(root="courage")
        self.courage = make_word("courage", family=self.aile, meaning="cesaret")
        self.encourage = make_word("encourage", pos="verb", family=self.aile,
                                   meaning="cesaretlendirmek")
        self.discourage = make_word("discourage", pos="verb", family=self.aile,
                                    meaning="cesaretini kırmak")

    def test_members_share_one_family(self):
        self.assertEqual(self.aile.words.count(), 3)
        self.assertEqual(self.encourage.family, self.courage.family)

    def test_root_comes_first_among_members(self):
        self.assertEqual(self.aile.members[0].text, "courage")

    def test_a_lonely_word_still_gets_a_family(self):
        yalniz = make_word("immaculate")
        self.assertIsNotNone(yalniz.family)
        self.assertEqual(yalniz.family.root, "immaculate")

    def test_detail_page_lists_the_other_members(self):
        html = self.client.get(reverse("word_detail", args=[self.encourage.id])).content.decode()
        self.assertIn("courage ailesi", html)
        self.assertIn("discourage", html)

    def test_deleting_the_family_removes_its_words(self):
        self.aile.delete()
        self.assertEqual(Word.objects.filter(text="encourage").count(), 0)


class PartOfSpeechTests(TestCase):
    """Aynı yazılış, farklı tür = ayrı kayıt."""

    def test_same_spelling_two_parts_of_speech(self):
        aile = WordFamily.objects.create(root="progress")
        isim = make_word("progress", pos="noun", family=aile, meaning="ilerleme")
        fiil = make_word("progress", pos="verb", family=aile, meaning="ilerlemek")

        self.assertNotEqual(isim.id, fiil.id)
        self.assertEqual(Word.objects.filter(text="progress").count(), 2)
        self.assertNotEqual(isim.meaningTr, fiil.meaningTr)

    def test_same_spelling_same_pos_is_not_allowed(self):
        from django.db import IntegrityError

        make_word("retain", pos="verb")
        with self.assertRaises(IntegrityError):
            Word.objects.create(family=WordFamily.objects.create(root="x"),
                                text="retain", pos="verb")


class MeaningTests(TestCase):
    """Kelime ≠ anlam: bank tek kelime, iki anlam."""

    def setUp(self):
        self.bank = make_word(
            "bank", meaning="banka",
            definition="an organization that keeps money",
            extra_meanings=[("nehir kıyısı", "the land along a river")],
        )

    def test_a_word_can_carry_several_meanings(self):
        self.assertEqual(self.bank.meanings.count(), 2)
        self.assertTrue(self.bank.has_multiple_meanings)

    def test_primary_meaning_is_the_first_one(self):
        self.assertEqual(self.bank.meaningTr, "banka")
        self.assertEqual(self.bank.explanation, "an organization that keeps money")

    def test_both_meanings_appear_on_the_detail_page(self):
        html = self.client.get(reverse("word_detail", args=[self.bank.id])).content.decode()
        self.assertIn("banka", html)
        self.assertIn("nehir kıyısı", html)

    def test_a_word_without_meanings_does_not_crash(self):
        bos = Word.objects.create(family=WordFamily.objects.create(root="bos"),
                                  text="bos", pos="noun")
        self.assertEqual(bos.meaningTr, "")
        self.assertEqual(bos.explanation, "")


class ExampleSentenceTests(TestCase):
    """
    Örnek cümleler artık kolon değil satır; ANLAM başına 5 tane.

    Bir kelime tek cümleden öğrenilmez — aynı kelimeyi farklı bağlamlarda
    görmek gerekiyor. Cümlenin kelimeye değil anlama bağlı olması da şart:
    `bank`ın "banka" cümleleriyle "nehir kıyısı" cümleleri aynı şey değil.
    """

    def test_model_allows_five_sentences(self):
        self.assertEqual(Meaning.EXAMPLE_SENTENCE_COUNT, 5)

    def test_sentences_hang_on_the_meaning_not_the_word(self):
        """Cümle satırının kelimeye giden bir alanı kalmadı."""
        alanlar = {f.name for f in ExampleSentence._meta.get_fields()}
        self.assertIn("meaning", alanlar)
        self.assertNotIn("word", alanlar)

    def test_sentences_keep_their_order(self):
        kelime = make_word("retain", sentences=["Birinci.", "İkinci.", "Üçüncü."])
        self.assertEqual(kelime.example_sentences, ["Birinci.", "İkinci.", "Üçüncü."])

    def test_extra_sentences_beyond_the_limit_are_dropped(self):
        kelime = make_word("retain", sentences=[f"Cümle {i}." for i in range(1, 9)])
        self.assertEqual(len(kelime.example_sentences), 5)

    def test_a_word_can_have_no_sentences(self):
        kelime = make_word("retain", sentences=[])
        self.assertEqual(kelime.example_sentences, [])

    def test_sentences_are_rows_not_columns(self):
        """Eski modelde exampleSentence1..10 kolonları vardı; artık yoklar."""
        alanlar = {f.name for f in Word._meta.get_fields()}
        for i in range(1, 11):
            self.assertNotIn(f"exampleSentence{i}", alanlar)


class WordFormTests(TestCase):
    """
    Çekim biçimleri: metindeki yazımdan sözlük maddesine köprü.

    Çekim yeni bir kelime DEĞİLDİR — kendi anlamı, açıklaması, cümlesi olmaz.
    """

    def test_regular_verb_forms_are_generated(self):
        kelime = make_word("decide", pos="verb")
        yuzeyler = set(kelime.forms.values_list("surface", flat=True))
        self.assertEqual(yuzeyler, {"decide", "decides", "deciding", "decided"})

    def test_irregular_verb_forms_come_from_the_data(self):
        """went / gone kuralla üretilemez; v2/v3 alanlarından gelir."""
        kelime = make_word("go", pos="verb", v2="went", v3="gone")
        yuzeyler = set(kelime.forms.values_list("surface", flat=True))
        self.assertIn("went", yuzeyler)
        self.assertIn("gone", yuzeyler)

    def test_irregular_plural_comes_from_the_table(self):
        kelime = make_word("child", pos="noun")
        self.assertIn("children", kelime.forms.values_list("surface", flat=True))

    def test_adjective_degrees_are_generated(self):
        kelime = make_word("slow", pos="adjective")
        yuzeyler = set(kelime.forms.values_list("surface", flat=True))
        self.assertIn("slower", yuzeyler)
        self.assertIn("slowest", yuzeyler)

    def test_long_adjectives_get_no_single_word_degrees(self):
        """'more important' iki kelimedir, metinde tek token olarak aranmaz."""
        kelime = make_word("important", pos="adjective")
        self.assertEqual(set(kelime.forms.values_list("surface", flat=True)), {"important"})

    def test_form_kind_is_recorded(self):
        kelime = make_word("slow", pos="adjective")
        tur = kelime.forms.get(surface="slower").kind
        self.assertEqual(tur, "comparative")

    def test_the_word_itself_is_also_a_form(self):
        kelime = make_word("retain", pos="verb")
        self.assertIn("retain", kelime.forms.values_list("surface", flat=True))

    def test_forms_are_rebuilt_not_duplicated(self):
        kelime = make_word("decide", pos="verb")
        once = kelime.forms.count()
        inflect.rebuild_forms(kelime)
        self.assertEqual(kelime.forms.count(), once)


class WordRelationTests(TestCase):
    """Eş / zıt anlamlı ve "daha basit karşılığı" bağları."""

    def setUp(self):
        self.possess = make_word("possess", pos="verb", meaning="sahip olmak")
        self.have = make_word("have", pos="verb", meaning="sahip olmak")
        self.harmful = make_word("harmful", pos="adjective", meaning="zararlı")
        self.harmless = make_word("harmless", pos="adjective", meaning="zararsız")

    def test_simpler_relation_carries_a_nuance_note(self):
        WordRelation.objects.create(from_word=self.possess, to_word=self.have,
                                    type="simpler", note="daha resmî")
        bag = self.possess.simpler_words.first()
        self.assertEqual(bag.to_word, self.have)
        self.assertEqual(bag.note, "daha resmî")

    def test_relation_types_do_not_leak_into_each_other(self):
        WordRelation.objects.create(from_word=self.harmful, to_word=self.harmless,
                                    type="antonym")
        self.assertEqual(self.harmful.antonyms.count(), 1)
        self.assertEqual(self.harmful.synonyms.count(), 0)
        self.assertEqual(self.harmful.simpler_words.count(), 0)

    def test_the_same_relation_cannot_be_stored_twice(self):
        from django.db import IntegrityError

        WordRelation.objects.create(from_word=self.harmful, to_word=self.harmless, type="antonym")
        with self.assertRaises(IntegrityError):
            WordRelation.objects.create(from_word=self.harmful, to_word=self.harmless, type="antonym")

    def test_simpler_word_is_shown_on_the_detail_page(self):
        WordRelation.objects.create(from_word=self.possess, to_word=self.have,
                                    type="simpler", note="daha resmî")
        html = self.client.get(reverse("word_detail", args=[self.possess.id])).content.decode()
        self.assertIn("Daha basit karşılığı", html)
        self.assertIn("daha resmî", html)


class UserWordNoteTests(TestCase):
    """
    Kişisel not kullanıcıya ait, kelimeye değil.

    Eski modelde `note` paylaşılan Word satırının üstündeydi — iki kullanıcı
    aynı kelimeyi kaydettiğinde aynı notu paylaşıyorlardı.
    """

    def setUp(self):
        self.efe = User.objects.create_user(username="efe", password="Sifre1234")
        self.ayse = User.objects.create_user(username="ayse", password="Sifre1234")
        self.word = make_word("immaculate")

    def test_each_user_has_their_own_note(self):
        UserWordNote.objects.create(user=self.efe, word=self.word, note="benim notum")
        UserWordNote.objects.create(user=self.ayse, word=self.word, note="onun notu")

        self.assertEqual(self.word.note_of(self.efe).note, "benim notum")
        self.assertEqual(self.word.note_of(self.ayse).note, "onun notu")

    def test_missing_note_is_none(self):
        self.assertIsNone(self.word.note_of(self.efe))

    def test_note_is_saved_from_the_detail_page(self):
        self.client.login(username="efe", password="Sifre1234")
        self.client.post(reverse("word_detail", args=[self.word.id]), {"note": "unutma"})
        self.assertEqual(self.word.note_of(self.efe).note, "unutma")

    def test_clearing_the_note_deletes_it(self):
        UserWordNote.objects.create(user=self.efe, word=self.word, note="eski")
        self.client.login(username="efe", password="Sifre1234")
        self.client.post(reverse("word_detail", args=[self.word.id]), {"note": "  "})
        self.assertIsNone(self.word.note_of(self.efe))

    def test_the_core_word_has_no_note_field(self):
        self.assertNotIn("note", {f.name for f in Word._meta.get_fields()})


class AllWordsPaginationTests(TestCase):
    """
    "Tüm Kelimeler" sayfası artık "Kelimelerim" ile aynı esnek sayfalamayı
    kullanıyor: ilk/son, sayfa numaraları, sayfa başına adet ve doğrudan
    sayfaya atlama.
    """

    def setUp(self):
        for i in range(120):
            make_word(f"word{i:03}", meaning=f"anlam{i}", level="101", forms=False)

    def _get(self, **params):
        response = self.client.get(reverse("all_words"), params)
        self.assertEqual(response.status_code, 200)
        return response

    def test_page_numbers_are_rendered(self):
        response = self._get()
        self.assertTrue(response.context["is_paginated"])
        self.assertIn(1, response.context["page_window"])
        self.assertContains(response, "Son sayfa")

    def test_first_and_last_links_appear_off_the_first_page(self):
        response = self._get(page=2)
        self.assertContains(response, "İlk sayfa")
        self.assertContains(response, "Son sayfa")
        self.assertContains(response, "Önceki")

    def test_jump_to_page_form_is_rendered(self):
        response = self._get()
        self.assertContains(response, 'name="page"')
        self.assertContains(response, ">Git<")

    def test_per_page_can_be_changed(self):
        response = self._get(per_page=25)
        self.assertEqual(response.context["per_page"], 25)
        self.assertEqual(len(response.context["page_obj"].object_list), 25)

    def test_invalid_per_page_falls_back(self):
        response = self._get(per_page=999)
        self.assertEqual(response.context["per_page"], 50)

    def test_direct_page_access(self):
        response = self._get(page=3)
        self.assertEqual(response.context["page_obj"].number, 3)

    def test_filters_survive_pagination(self):
        response = self._get(q="word01", level=["B1", "B2"], per_page=25)
        base_qs = response.context["base_qs"]
        self.assertIn("q=word01", base_qs)
        self.assertIn("level=B1", base_qs)   # çoklu seçim korunur (25 Eylül)
        self.assertIn("level=B2", base_qs)
        self.assertIn("per_page=25", base_qs)
        # "page" parametresi bağlantıya şablon tarafından ekleniyor;
        # base_qs'de kendi başına bulunmamalı ("per_page" ile karışmasın)
        self.assertFalse(base_qs.startswith("page="))
        self.assertNotIn("&page=", base_qs)

    def test_default_level_is_not_added_to_links(self):
        response = self._get(level="all")
        self.assertNotIn("level=", response.context["base_qs"])


class DarkThemeTests(TestCase):
    """
    Karanlık tema altyapısı.

    Temanın sayfa boyanmadan önce uygulanması kritik: script body'den sonra
    çalışırsa karanlık temada bile sayfa bir an beyaz parlar.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="temauser", password="Sifre1234")

    def _html(self, url_name, *args):
        response = self.client.get(reverse(url_name, args=args), follow=True)
        self.assertEqual(response.status_code, 200)
        return response.content.decode("utf-8")

    def test_tailwind_is_configured_for_class_strategy(self):
        html = self._html("all_words")
        self.assertIn("darkMode: 'class'", html)

    def test_theme_script_runs_before_the_body(self):
        html = self._html("all_words")
        script_index = html.index("localStorage.getItem('theme')")
        body_index = html.index("<body")
        self.assertLess(script_index, body_index,
                        "tema scripti body'den sonra çalışıyor, sayfa beyaz parlar")

    def test_system_preference_is_the_default(self):
        html = self._html("all_words")
        self.assertIn("prefers-color-scheme: dark", html)

    def test_color_scheme_is_declared_for_native_controls(self):
        """Kaydırma çubuğu ve select açılır listesi de temaya uymalı."""
        html = self._html("all_words")
        self.assertIn("color-scheme: dark", html)

    def test_toggle_button_is_present(self):
        html = self._html("all_words")
        self.assertIn("data-theme-toggle", html)

    def test_pages_carry_dark_variants(self):
        for url_name in ("all_words", "index", "about", "login", "register"):
            with self.subTest(page=url_name):
                html = self._html(url_name)
                self.assertGreater(html.count("dark:"), 20,
                                   f"{url_name} sayfasında karanlık tema sınıfı yok denecek kadar az")

    def test_logged_in_pages_carry_dark_variants(self):
        self.client.login(username="temauser", password="Sifre1234")
        for url_name in ("profile_words", "add_word", "ai_add_words_page", "exercises_page"):
            with self.subTest(page=url_name):
                html = self._html(url_name)
                self.assertGreater(html.count("dark:"), 20)


class FriendsFeatureDisabledTests(TestCase):
    """
    Arkadaşlık özelliği kapalı ama ALTYAPI duruyor.

    Amaç: kullanıcıya hiçbir yerden görünmemesi ve doğrudan adresle de
    erişilememesi; buna karşılık model alanları, view'lar ve şablon yerinde
    durduğu için özelliği geri açmak tek satırlık bir iş olmalı.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="arkadasuser", password="Sifre1234")
        self.other = User.objects.create_user(username="digeri", password="Sifre1234")
        self.client.login(username="arkadasuser", password="Sifre1234")

    # ---- Kapalı olması ----

    def test_friend_urls_cannot_be_reversed(self):
        for name in ("friends", "send_request", "accept_request",
                     "decline_request", "remove_friend", "cancel_request"):
            with self.subTest(url=name):
                with self.assertRaises(NoReverseMatch):
                    reverse(name)

    def test_friends_page_is_not_reachable(self):
        self.assertEqual(self.client.get("/friends/").status_code, 404)

    def test_friend_request_endpoint_is_not_reachable(self):
        response = self.client.get(f"/friends/send-request/{self.other.id}")
        self.assertEqual(response.status_code, 404)

    def test_navbar_has_no_friends_link(self):
        html = self.client.get(reverse("index"), follow=True).content.decode()
        self.assertNotIn("Arkadaşlar</a>", html)

    def test_profile_does_not_show_the_friend_count(self):
        html = self.client.get(reverse("user_profile"), follow=True).content.decode()
        self.assertNotIn(">Arkadaş<", html)

    def test_other_user_profile_page_still_works(self):
        """Bu sayfada arkadaşlar sayfasına dönüş linki vardı; kaldırılmazsa 500 verirdi."""
        response = self.client.get(
            reverse("show_user_profile", args=[self.other.id]), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Arkadaşlar Sayfasına Git", response.content.decode())

    # ---- Altyapının durması ----

    def test_model_fields_are_intact(self):
        self.user.friends.add(self.other)
        self.assertIn(self.other, self.user.friends.all())
        self.assertIn(self.user, self.other.friends.all())

    def test_views_and_template_are_intact(self):
        from django.template.loader import get_template
        import friends.urls
        import friends.views

        self.assertTrue(hasattr(friends.views, "listFriends"))
        self.assertEqual(len(friends.urls.urlpatterns), 6)
        self.assertIsNotNone(get_template("pages/friends.html"))

    def test_friends_visibility_option_is_gone(self):
        """
        Arkadaşlık kapalı olduğu için "arkadaşlara açık" görünürlüğü de
        kaldırıldı; geriye yalnızca gizli / herkese açık kaldı.
        """
        from words.models import VISIBILITY_CHOICES

        self.assertEqual({d for d, _ in VISIBILITY_CHOICES}, {"private", "public"})


class CommentsFeatureDisabledTests(TestCase):
    """Yorumlar özelliği kapalı; altyapı (model, view, şablon) duruyor."""

    def setUp(self):
        self.user = User.objects.create_user(username="yorumuser", password="Sifre1234")
        self.client.login(username="yorumuser", password="Sifre1234")

    def test_comment_urls_cannot_be_reversed(self):
        for name in ("show_comments_page", "remove_comment", "like_comment", "dislike_comment"):
            with self.subTest(url=name):
                with self.assertRaises(NoReverseMatch):
                    reverse(name)

    def test_comments_page_is_not_reachable(self):
        self.assertEqual(self.client.get("/comments/").status_code, 404)

    def test_navbar_has_no_comments_link(self):
        html = self.client.get(reverse("index"), follow=True).content.decode()
        self.assertNotIn(">Yorumlar<", html)

    def test_model_and_views_are_intact(self):
        from django.template.loader import get_template
        import comments.urls
        import comments.views
        from comments.models import Comment

        comment = Comment.objects.create(owner=self.user, content="deneme")
        self.assertEqual(Comment.objects.count(), 1)
        self.assertTrue(hasattr(comments.views, "showComments"))
        self.assertEqual(len(comments.urls.urlpatterns), 4)
        self.assertIsNotNone(get_template("pages/comments.html"))


def squash(html):
    """
    Etiketler arasındaki boşlukları temizler.

    Şablonlarda etiket metni çoğu zaman kendi satırında duruyor
    (">\n    Kelimeler\n</a>"); testlerin ">Kelimeler<" diye
    yazılabilmesi için arada kalan boşluk siliniyor.
    """
    return re.sub(r">\s+", ">", re.sub(r"\s+<", "<", html))


class NavbarMenuTests(TestCase):
    """Üst çubuk: beş bölüm, logo ana sayfaya, sağ üstte hesap."""

    SECTIONS = (">Kelimeler<", ">Okumalar<", ">Hakkında<", ">Egzersizler<", ">Metinler<")

    def setUp(self):
        self.user = User.objects.create_user(username="menuuser", password="Sifre1234")

    def _navbar(self, logged_in):
        if logged_in:
            self.client.login(username="menuuser", password="Sifre1234")
        html = self.client.get(reverse("index"), follow=True).content.decode()
        start = html.index('<header id="navbar"')
        return squash(html[start:html.index("</header>", start)])

    def test_home_link_is_removed_logo_is_the_way_home(self):
        navbar = self._navbar(logged_in=False)
        self.assertNotIn(">Ana Sayfa<", navbar)
        self.assertIn(reverse("index"), navbar)
        self.assertIn("Learn&nbsp;Vocab", navbar)  # logonun yanındaki isim

    def test_five_sections_are_shown_to_everyone(self):
        """Bölümler girişsiz de görünüyor; korumalı olanlar giriş ekranına düşüyor."""
        for logged_in in (False, True):
            navbar = self._navbar(logged_in=logged_in)
            for etiket in self.SECTIONS:
                with self.subTest(logged_in=logged_in, etiket=etiket):
                    self.assertIn(etiket, navbar)

    def test_word_pages_are_one_section(self):
        """Tüm Kelimeler / Kelimelerim ayrı menü başlığı değil."""
        navbar = self._navbar(logged_in=True)
        self.assertNotIn(">Tüm Kelimeler<", navbar)
        self.assertNotIn(">Kelimelerim<", navbar)

    def test_words_section_points_to_my_words_when_logged_in(self):
        navbar = self._navbar(logged_in=True)
        self.assertIn(reverse("profile_words"), navbar)

    def test_words_section_does_not_point_to_all_words(self):
        """Tüm Kelimeler arayüzden kaldırıldı; girişsiz kullanıcı da oraya gitmez."""
        for giris in (False, True):
            with self.subTest(logged_in=giris):
                navbar = self._navbar(logged_in=giris)
                self.assertNotIn(reverse("all_words"), navbar)
                self.assertIn(reverse("profile_words"), navbar)

    def test_account_is_an_avatar_when_logged_in(self):
        navbar = self._navbar(logged_in=True)
        self.assertIn('title="Profilim"', navbar)
        self.assertIn(reverse("user_profile"), navbar)
        self.assertNotIn(">Profilim<", navbar)
        self.assertNotIn(">Hesabım<", navbar)
        self.assertNotIn("Hoş geldin", navbar)

    def test_account_is_a_login_button_when_logged_out(self):
        navbar = self._navbar(logged_in=False)
        self.assertIn("Giriş Yap", navbar)
        self.assertNotIn('title="Profilim"', navbar)

    def test_logout_moved_to_the_profile_page(self):
        """Üst çubukta çıkış yok; profil sayfasında var."""
        navbar = self._navbar(logged_in=True)
        self.assertNotIn(">Çıkış Yap<", navbar)
        page = self.client.get(reverse("user_profile"), follow=True).content.decode()
        self.assertIn(reverse("logout"), page)

    def test_hamburger_menu_is_gone(self):
        navbar = self._navbar(logged_in=True)
        self.assertNotIn('id="mobile-menu"', navbar)


class MobileTabBarTests(TestCase):
    """Mobil alt sekme çubuğu — beş bölüm, ikonlu."""

    def setUp(self):
        self.user = User.objects.create_user(username="mobileuser", password="Sifre1234")

    def _bar(self, logged_in=False):
        if logged_in:
            self.client.login(username="mobileuser", password="Sifre1234")
        html = self.client.get(reverse("index"), follow=True).content.decode()
        start = html.index('aria-label="Alt menü"')
        return squash(html[start:html.index("</nav>", start)])

    def test_bar_has_five_sections_for_anonymous_users(self):
        bar = self._bar()
        for etiket in NavbarMenuTests.SECTIONS:
            with self.subTest(etiket=etiket):
                self.assertIn(etiket, bar)

    def test_every_section_has_an_icon(self):
        bar = self._bar()
        self.assertEqual(bar.count("<svg"), 5)

    def test_bar_is_hidden_on_desktop(self):
        self.assertIn("lg:hidden", self._bar())

    def test_active_section_is_marked(self):
        html = self.client.get(reverse("about")).content.decode()
        start = html.index('aria-label="Alt menü"')
        bar = squash(html[start:html.index("</nav>", start)])
        self.assertEqual(bar.count('aria-current="page"'), 1)

    def test_content_is_not_covered_by_the_bar(self):
        html = self.client.get(reverse("index")).content.decode()
        self.assertIn("pb-20 lg:pb-0", html)


class NavigationSectionTests(TestCase):
    """Hangi sayfa hangi bölümü aktif yapıyor (LearnVocab/navigation.py)."""

    def _section_of(self, url):
        response = self.client.get(url, follow=True)
        return response.context["nav_section"]

    def test_word_pages_map_to_the_words_section(self):
        self.assertEqual(self._section_of(reverse("all_words")), "words")

    def test_about_maps_to_its_own_section(self):
        self.assertEqual(self._section_of(reverse("about")), "about")

    def test_readings_placeholder_exists(self):
        response = self.client.get(reverse("readings"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["nav_section"], "readings")

    def test_home_page_belongs_to_no_section(self):
        self.assertIsNone(self._section_of(reverse("index")))


class OldPagesRemovedFromUITests(TestCase):
    """
    Tüm Kelimeler sayfası ve filtre paneli arayüzden kaldırıldı (ürün
    raporu, Bölüm 17). Kodları duruyor ama hiçbir sayfa oraya bağlanmıyor.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="tabuser", password="Sifre1234")

    def test_no_page_links_to_all_words(self):
        adresler = ("index", "readings", "about", "profile_words", "learn_pass_page",
                    "exercises_page", "profile_texts")
        for giris in (False, True):
            if giris:
                self.client.login(username="tabuser", password="Sifre1234")
            for ad in adresler:
                with self.subTest(page=ad, logged_in=giris):
                    html = self.client.get(reverse(ad), follow=True).content.decode()
                    self.assertNotIn(reverse("all_words"), html)

    def test_my_words_has_no_all_words_switcher(self):
        self.client.login(username="tabuser", password="Sifre1234")
        html = self.client.get(reverse("profile_words")).content.decode()
        self.assertNotIn("Tüm Kelimeler", html)


class LoginGateTests(TestCase):
    """Girişsiz kullanıcı korumalı bölüme gelince giriş formuna fırlatılmıyor."""

    GATED = {
        "profile_words": "Kelimelerim",
        "exercises_page": "Egzersizler",
        "profile_texts": "Metinler",
        "user_profile": "Profilim",
    }

    def test_gated_pages_explain_instead_of_redirecting(self):
        for name, etiket in self.GATED.items():
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                self.assertIn("önce giriş yapın", html)
                self.assertIn(etiket, html)
                self.assertIn(reverse("login"), html)

    def test_gate_keeps_the_menu_visible(self):
        html = self.client.get(reverse("exercises_page")).content.decode()
        self.assertIn('aria-label="Alt menü"', html)

    def test_all_words_stays_public(self):
        response = self.client.get(reverse("all_words"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("önce giriş yapın", response.content.decode())

    def test_logged_in_users_are_not_gated(self):
        User.objects.create_user(username="gateuser", password="Sifre1234")
        self.client.login(username="gateuser", password="Sifre1234")
        for name in self.GATED:
            with self.subTest(page=name):
                html = self.client.get(reverse(name), follow=True).content.decode()
                self.assertNotIn("önce giriş yapın", html)


class MergedProfilePageTests(TestCase):
    """Hesap bilgileri + ayarlar tek sayfada."""

    def setUp(self):
        from usersettings.models import UserSettings

        self.user = User.objects.create_user(
            username="profiluser", password="Sifre1234", email="eski@x.com"
        )
        UserSettings.objects.create(user=self.user)
        self.client.login(username="profiluser", password="Sifre1234")

    def _page(self):
        response = self.client.get(reverse("user_profile"), follow=True)
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_page_contains_every_section(self):
        html = self._page()
        for parca in ("Hesap Bilgileri", "Öğrenme", "E-posta Bildirimleri",
                      "Verilerim", "Tehlikeli Bölge", "Parolamı Değiştir"):
            with self.subTest(bolum=parca):
                self.assertIn(parca, html)

    def test_every_setting_field_survived_the_redesign(self):
        """Tasarım değişti, alanlar aynı kalmalı: form adları korunuyor mu?"""
        html = self._page()
        for alan in ('name="first_name"', 'name="last_name"', 'name="email"',
                     'name="username"', 'name="profile_pic"', 'name="dailyGoal"',
                     'name="audio"', 'name="dailyGoalsMail"', 'name="featuresMail"',
                     'name="improvementsMail"', 'name="confirm_password"'):
            with self.subTest(alan=alan):
                self.assertIn(alan, html)

    def test_dangerous_actions_still_ask_for_the_password(self):
        html = self._page()
        self.assertEqual(html.count('name="confirm_password"'), 2)
        self.assertIn(reverse("remove_all_words"), html)
        self.assertIn(reverse("delete_myaccount"), html)

    def test_export_links_are_all_present(self):
        html = self._page()
        for ad in ("export_all", "export_mywords", "export_mytexts"):
            with self.subTest(baglanti=ad):
                self.assertIn(reverse(ad), html)

    def test_old_urls_redirect_to_the_merged_page(self):
        for name in ("profile_myaccount", "profile_settings"):
            with self.subTest(url=name):
                response = self.client.get(reverse(name))
                self.assertRedirects(response, reverse("user_profile"))

    def test_account_form_posts_to_a_url_that_actually_saves(self):
        """
        Formun action'ı gerçekten kaydeden adrese gitmeli.

        Sayfalar birleştirilirken 'profile_myaccount' salt yönlendirmeye
        dönüştü; form hâlâ oraya POST ediyorsa 302 sonrası tarayıcı GET ile
        geri geliyor ve kullanıcının yazdıkları sessizce kayboluyor.
        """
        html = self._page()
        self.assertIn('action="%s"' % reverse("user_profile"), html)

        cevap = self.client.post(reverse("profile_myaccount"), {
            "email": "kaybolmasin@x.com", "first_name": "Efe", "last_name": "Solmaz",
        })
        self.user.refresh_from_db()
        self.assertNotEqual(
            self.user.email, "eski@x.com",
            "profile_myaccount'a yapılan POST veriyi düşürüyor (durum: %s)" % cevap.status_code,
        )

    def test_account_form_saves_from_the_merged_page(self):
        self.client.post(reverse("user_profile"), {
            "email": "yeni@x.com", "first_name": "Efe", "last_name": "Solmaz",
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "yeni@x.com")
        self.assertEqual(self.user.first_name, "Efe")

    def test_page_has_no_left_sidebar(self):
        """Sol menü tamamen kaldırıldı; sayfa tam genişlikte."""
        html = self._page()
        self.assertNotIn('id="mobile-sidebar"', html)
        self.assertNotIn(">Ayarlar</span>", html)
        self.assertNotIn(">Hesap Bilgilerim</span>", html)

    def test_comment_controls_are_hidden(self):
        """Yorumlar kapalıyken 'yorumlarımı sil' düğmesi görünmemeli."""
        html = self._page()
        self.assertNotIn("Yorumları Kaldır", html)
        self.assertNotIn("Tüm Yorumlarımı Dışa Aktar", html)

    def test_daily_goal_can_be_set_back_to_zero(self):
        """
        "Yok" seçeneği hedefi gerçekten sıfırlamalı.

        Kaydeden view'daki if/elif zincirinde 0 için bir dal yoktu; kullanıcı
        "Yok" seçtiğinde eski hedefi sessizce olduğu gibi kalıyordu.
        """
        from usersettings.models import UserSettings

        ayar = UserSettings.objects.get(user=self.user)
        ayar.dailyGoal = 15
        ayar.save()

        self.client.post(reverse("save_settings"), {"dailyGoal": "0"})
        ayar.refresh_from_db()
        self.assertEqual(ayar.dailyGoal, 0)

    def test_daily_goal_ignores_values_outside_the_options(self):
        from usersettings.models import UserSettings

        ayar = UserSettings.objects.get(user=self.user)
        ayar.dailyGoal = 10
        ayar.save()

        self.client.post(reverse("save_settings"), {"dailyGoal": "999"})
        ayar.refresh_from_db()
        self.assertEqual(ayar.dailyGoal, 10)

    def test_saving_settings_returns_to_the_merged_page(self):
        response = self.client.post(reverse("save_settings"), {"dailyGoal": "7"})
        self.assertRedirects(response, reverse("user_profile"))


class TemplateCommentSyntaxTests(TestCase):
    """
    Çok satıra yayılan {# ... #} Django yorumu DEĞİLDİR: şablon onu yorum
    saymaz ve metin olarak sayfaya basar. Bu hata daha önce iki kez sayfaya
    sızdığı için bütün şablonlar burada taranıyor. Çok satırlı açıklama için
    {% comment %} ... {% endcomment %} kullanılmalı.
    """

    def test_no_multiline_hash_comments_in_templates(self):
        import os
        from django.conf import settings

        hatalar = []
        for kok in settings.TEMPLATES[0]["DIRS"]:
            for klasor, _, dosyalar in os.walk(kok):
                if "_arsiv" in klasor:
                    continue
                for dosya in dosyalar:
                    if not dosya.endswith(".html"):
                        continue
                    yol = os.path.join(klasor, dosya)
                    with open(yol, encoding="utf-8") as f:
                        icerik = f.read()
                    for eslesme in re.finditer(r"\{#(.*?)#\}", icerik, re.S):
                        if "\n" in eslesme.group(1):
                            hatalar.append(
                                "%s: %s..." % (os.path.relpath(yol, kok),
                                               eslesme.group(0)[:50].replace("\n", " "))
                            )
        self.assertEqual(hatalar, [], "Çok satırlı {# #} yorumu sayfaya basılır:\n" + "\n".join(hatalar))

class CefrLevelTests(TestCase):
    """
    Seviye artık ODTÜ kuru (101–501) değil, CEFR (A1–C2).

    Kur, kelimenin bir özelliği değil; kelimeye takılan bir liste etiketi
    olacak. Bu testler eski alanın geri dönmediğini sabitliyor.
    """

    def test_word_level_field_is_gone(self):
        alanlar = {f.name for f in Word._meta.get_fields()}
        self.assertIn("cefr", alanlar)
        self.assertNotIn("wordLevel", alanlar)

    def test_cefr_choices_are_the_six_levels(self):
        kodlar = [kod for kod, _ in CEFR_CHOICES if kod != "Belirtilmemiş"]
        self.assertEqual(kodlar, ["A1", "A2", "B1", "B2", "C1", "C2"])

    def test_old_course_codes_are_not_valid_levels(self):
        for eski in ("101", "201", "301", "401", "501"):
            with self.subTest(eski=eski):
                self.assertNotIn(eski, CEFR_LEVELS)

    def test_level_is_unspecified_by_default(self):
        kelime = Word.objects.create(
            family=WordFamily.objects.create(root="seviyesiz"),
            text="seviyesiz", pos="noun",
        )
        self.assertEqual(kelime.cefr, "Belirtilmemiş")


class SentimentAndRegisterTests(TestCase):
    """
    Ton ve üslup.

    Bu iki alan var çünkü TÜRKÇE KARŞILIK bu bilgiyi siliyor: `notorious`
    ile `famous` sözlükte ikisi de "ünlü"; `possess` ile `have` ikisi de
    "sahip olmak". Fark ancak burada duruyor.
    """

    def test_defaults_are_neutral(self):
        anlam = make_word("word").primary_meaning
        self.assertEqual(anlam.sentiment, Sentiment.NEUTRAL)
        self.assertEqual(anlam.register, Register.NEUTRAL)

    def test_two_words_with_the_same_turkish_meaning_differ_in_tone(self):
        unlu = make_word("famous", meaning="ünlü", sentiment=Sentiment.POSITIVE)
        kotu_unlu = make_word("notorious", meaning="ünlü", sentiment=Sentiment.NEGATIVE)
        self.assertEqual(unlu.meaningTr, kotu_unlu.meaningTr)
        self.assertNotEqual(unlu.primary_meaning.sentiment,
                            kotu_unlu.primary_meaning.sentiment)

    def test_register_is_recorded_on_the_meaning(self):
        kelime = make_word("possess", pos="verb", meaning="sahip olmak",
                           register=Register.FORMAL)
        self.assertEqual(kelime.primary_meaning.register, Register.FORMAL)

    def test_is_marked_only_when_something_is_not_neutral(self):
        duz = make_word("plain").primary_meaning
        isaretli = make_word("detrimental", sentiment=Sentiment.NEGATIVE).primary_meaning
        self.assertFalse(duz.is_marked)
        self.assertTrue(isaretli.is_marked)

    def test_tone_badge_shows_up_on_the_family_page(self):
        kelime = make_word("detrimental", pos="adjective", meaning="zararlı",
                           sentiment=Sentiment.NEGATIVE, register=Register.ACADEMIC)
        html = self.client.get(reverse("word_detail", args=[kelime.id])).content.decode()
        self.assertIn("olumsuz", html)
        self.assertIn("akademik", html)


class CategoryTests(TestCase):
    """Alan (konu) etiketi anlama takılıyor; okuma metinleriyle bağlanacak yer burası."""

    def test_categories_attach_to_the_meaning(self):
        kelime = make_word("inflation", meaning="enflasyon", categories=["Ekonomi"])
        self.assertEqual([k.name for k in kelime.primary_meaning.categories.all()],
                         ["Ekonomi"])

    def test_word_level_shortcut_collects_categories_without_repeats(self):
        kelime = make_word("bank", meaning="banka", categories=["Ekonomi"])
        ikinci = Meaning.objects.create(word=kelime, meaning_tr="nehir kıyısı", sort_order=1)
        ikinci.categories.add(Category.objects.get(slug="ekonomi"))
        self.assertEqual([k.name for k in kelime.categories], ["Ekonomi"])

    def test_a_category_is_reused_not_duplicated(self):
        make_word("inflation", meaning="enflasyon", categories=["Ekonomi"])
        make_word("recession", meaning="durgunluk", categories=["Ekonomi"])
        self.assertEqual(Category.objects.filter(name="Ekonomi").count(), 1)


class MeaningLevelDataTests(TestCase):
    """
    Collocation, kalıp ve cümleler ANLAMA bağlı, kelimeye değil.

    `bank` bunun kanıtı: "open a bank account" yalnızca "banka" anlamına
    aittir. Kelime seviyesinde tutulsalardı iki anlamın verisi karışırdı.
    """

    def setUp(self):
        self.bank = make_word("bank", meaning="banka", sentences=["I went to the bank."],
                              categories=["Ekonomi"],
                              collocations=[("open a bank account", "verb_noun")])
        self.kiyi = Meaning.objects.create(word=self.bank, meaning_tr="nehir kıyısı",
                                           sort_order=1)
        ExampleSentence.objects.create(meaning=self.kiyi, text="We sat on the bank.")
        Collocation.objects.create(meaning=self.kiyi, pattern="the river bank",
                                   kind="noun_noun")

    def test_each_meaning_keeps_its_own_collocations(self):
        self.assertEqual([c.pattern for c in self.bank.primary_meaning.collocations.all()],
                         ["open a bank account"])
        self.assertEqual([c.pattern for c in self.kiyi.collocations.all()],
                         ["the river bank"])

    def test_each_meaning_keeps_its_own_sentences(self):
        self.assertEqual([c.text for c in self.kiyi.examples.all()],
                         ["We sat on the bank."])

    def test_word_shortcut_flattens_in_meaning_order(self):
        self.assertEqual(self.bank.example_sentences,
                         ["I went to the bank.", "We sat on the bank."])
        self.assertEqual([c.pattern for c in self.bank.collocations],
                         ["open a bank account", "the river bank"])

    def test_the_same_collocation_cannot_be_added_twice_to_one_meaning(self):
        with self.assertRaises(IntegrityError):
            Collocation.objects.create(meaning=self.kiyi, pattern="the river bank")

    def test_deleting_a_meaning_takes_its_rows_with_it(self):
        self.kiyi.delete()
        self.assertEqual(ExampleSentence.objects.filter(text="We sat on the bank.").count(), 0)
        self.assertEqual(Collocation.objects.filter(pattern="the river bank").count(), 0)

    def test_collocations_appear_on_the_family_page(self):
        html = self.client.get(reverse("word_detail", args=[self.bank.id])).content.decode()
        self.assertIn("open a bank account", html)
        self.assertIn("the river bank", html)


class UsagePatternTests(TestCase):
    """
    Kalıp collocation değil, gramer: `decide to do` ama `suggest doing`.

    Ayrı tutulmalarının sebebi quizlerinin de ayrı olması: collocation'da
    eksik kelime, kalıpta eksik edat ya da fiil biçimi sorulur.
    """

    def test_patterns_hang_on_the_meaning(self):
        kelime = make_word("decide", pos="verb", meaning="karar vermek",
                           patterns=[("decide to do sth", "verb_form")])
        self.assertEqual([k.pattern for k in kelime.primary_meaning.patterns.all()],
                         ["decide to do sth"])

    def test_a_pattern_carries_its_kind(self):
        kelime = make_word("depend", pos="verb", meaning="bağlı olmak",
                           patterns=[("depend on sth", "preposition")])
        self.assertEqual(kelime.patterns.first().kind, "preposition")

    def test_pattern_note_survives_to_the_page(self):
        kelime = make_word("discourage", pos="verb", meaning="caydırmak")
        UsagePattern.objects.create(
            meaning=kelime.primary_meaning, pattern="discourage sb from doing sth",
            kind="preposition", note="from + -ing; from to DEĞİL",
        )
        html = self.client.get(reverse("word_detail", args=[kelime.id])).content.decode()
        self.assertIn("discourage sb from doing sth", html)
        self.assertIn("from + -ing", html)


class FalseFriendTests(TestCase):
    """
    Yanlış dost: Türkçeye benzediği için yanlış anlaşılan kelime.

    `sympathetic` "sempatik" değildir. Bu hata Türkçe konuşanda sistematik
    olduğu için veri olarak tutulabilir.
    """

    def setUp(self):
        self.kelime = make_word("sympathetic", pos="adjective", meaning="anlayışlı")
        FalseFriend.objects.create(
            word=self.kelime, turkish_lookalike="sempatik",
            assumed_meaning="cana yakın, hoş", correct_english="likeable, friendly",
        )

    def test_the_false_friend_is_attached_to_the_word(self):
        self.assertEqual(self.kelime.false_friends.count(), 1)

    def test_the_same_lookalike_cannot_be_repeated(self):
        with self.assertRaises(IntegrityError):
            FalseFriend.objects.create(word=self.kelime, turkish_lookalike="sempatik")

    def test_the_warning_reaches_the_family_page(self):
        html = self.client.get(reverse("word_detail", args=[self.kelime.id])).content.decode()
        self.assertIn("sempatik", html)
        self.assertIn("likeable, friendly", html)


class ConfusedWithTests(TestCase):
    """affect/effect, sensible/sensitive: eş anlamlı değil, karıştırılan."""

    def test_confusable_is_its_own_relation_type(self):
        a = make_word("sensible", pos="adjective", meaning="mantıklı")
        b = make_word("sensitive", pos="adjective", meaning="duyarlı")
        WordRelation.objects.create(from_word=a, to_word=b, type="confused_with",
                                    note="Aynı kökten, zıt yönlere.")
        self.assertEqual(a.confusables.count(), 1)
        self.assertEqual(a.synonyms.count(), 0)

    def test_it_shows_on_the_page_as_a_warning_not_as_a_synonym(self):
        a = make_word("sensible", pos="adjective", meaning="mantıklı")
        b = make_word("sensitive", pos="adjective", meaning="duyarlı")
        WordRelation.objects.create(from_word=a, to_word=b, type="confused_with")
        html = self.client.get(reverse("word_detail", args=[a.id])).content.decode()
        self.assertIn("Sık karıştırılır", html)


class ExpressionTests(TestCase):
    """
    Deyim ve kalıp ifadeler kelime değil ama öğrenilen birimler.

    "in the long run" anlamı parçalarından çıkmaz; Word + WordForm bunu
    çözemez, kendi satırı olmak zorunda.
    """

    def test_an_expression_can_stand_alone(self):
        ifade = Expression.objects.create(text="by and large", meaning_tr="genel olarak")
        self.assertEqual(ifade.words.count(), 0)

    def test_an_expression_can_hang_on_more_than_one_word(self):
        karar = make_word("decision", meaning="karar")
        vermek = make_word("decide", pos="verb", meaning="karar vermek")
        ifade = Expression.objects.create(text="come to a decision", meaning_tr="karara varmak")
        ifade.words.set([karar, vermek])
        self.assertEqual(karar.expressions.count(), 1)
        self.assertEqual(vermek.expressions.count(), 1)

    def test_it_appears_on_the_pages_of_the_words_it_hangs_on(self):
        karar = make_word("decision", meaning="karar")
        ifade = Expression.objects.create(text="come to a decision",
                                          meaning_tr="bir karara varmak")
        ifade.words.add(karar)
        html = self.client.get(reverse("word_detail", args=[karar.id])).content.decode()
        self.assertIn("come to a decision", html)
        self.assertIn("bir karara varmak", html)

    def test_expression_text_is_unique(self):
        Expression.objects.create(text="in the long run", meaning_tr="uzun vadede")
        with self.assertRaises(IntegrityError):
            Expression.objects.create(text="in the long run", meaning_tr="başka")


class UserMeaningTests(TestCase):
    """
    Kullanıcının kendi eklediği anlam.

    Çekirdek sözlük hiçbir zaman tamamlanmaz; öğrenci kelimeyi listedeki
    anlamlarına uymayan bir yerde görür. Eklediği anlam yalnızca ona
    görünür ve çekirdeğe dokunmaz.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="anlamci", password="Sifre1234")
        self.baskasi = User.objects.create_user(username="digeri", password="Sifre1234")
        self.kelime = make_word("bank", meaning="banka")
        self.client.login(username="anlamci", password="Sifre1234")

    def _ekle(self, anlam="sıra, kuyruk", aciklama=""):
        return self.client.post(reverse("word_detail", args=[self.kelime.id]), {
            "form": "meaning", "meaning_tr": anlam, "definition": aciklama,
        }, follow=True)

    def test_user_can_add_a_meaning(self):
        self._ekle()
        self.assertEqual(UserMeaning.objects.filter(user=self.user).count(), 1)

    def test_the_core_word_is_untouched(self):
        self._ekle()
        self.assertEqual(self.kelime.meanings.count(), 1)
        self.assertEqual(self.kelime.meaningTr, "banka")

    def test_an_empty_meaning_is_refused(self):
        self._ekle(anlam="   ")
        self.assertEqual(UserMeaning.objects.count(), 0)

    def test_more_than_one_personal_meaning_is_allowed(self):
        self._ekle(anlam="sıra")
        self._ekle(anlam="küme")
        self.assertEqual(self.kelime.meanings_of(self.user).count(), 2)

    def test_only_its_owner_sees_it(self):
        self._ekle()
        self.assertEqual(self.kelime.meanings_of(self.baskasi).count(), 0)

    def test_it_shows_on_the_page_for_its_owner(self):
        self._ekle(anlam="sıra, kuyruk")
        html = self.client.get(reverse("word_detail", args=[self.kelime.id])).content.decode()
        self.assertIn("sıra, kuyruk", html)

    def test_another_user_does_not_see_it_on_the_page(self):
        self._ekle(anlam="sıra, kuyruk")
        self.client.login(username="digeri", password="Sifre1234")
        html = self.client.get(reverse("word_detail", args=[self.kelime.id])).content.decode()
        self.assertNotIn("sıra, kuyruk", html)

    def test_user_can_delete_their_own_meaning(self):
        self._ekle()
        anlam = UserMeaning.objects.get()
        self.client.post(reverse("word_detail", args=[self.kelime.id]),
                         {"form": "meaning_delete", "meaning_id": anlam.id})
        self.assertEqual(UserMeaning.objects.count(), 0)

    def test_a_user_cannot_delete_someone_elses_meaning(self):
        self._ekle()
        anlam = UserMeaning.objects.get()
        self.client.login(username="digeri", password="Sifre1234")
        self.client.post(reverse("word_detail", args=[self.kelime.id]),
                         {"form": "meaning_delete", "meaning_id": anlam.id})
        self.assertEqual(UserMeaning.objects.count(), 1)

    def test_the_note_form_still_works_beside_it(self):
        """İki form da aynı adrese POST ediyor; ayırt edilmezlerse biri diğerini siler."""
        self.client.post(reverse("word_detail", args=[self.kelime.id]),
                         {"form": "note", "note": "metinde gördüm"})
        self.assertEqual(self.kelime.note_of(self.user).note, "metinde gördüm")
        self.assertEqual(UserMeaning.objects.count(), 0)


class SeedDataTests(TestCase):
    """
    Tohum veri yalnızca örnek değil; modelin her kararının ekranda
    görünebildiğinin kanıtı. Bozulursa hiçbir ekran gerçekten denenemez.
    """

    @classmethod
    def setUpTestData(cls):
        call_command("seed_words", verbosity=0)

    def test_every_word_has_a_level_and_a_meaning(self):
        for kelime in Word.objects.all():
            with self.subTest(kelime=kelime.text):
                self.assertIn(kelime.cefr, CEFR_LEVELS)
                self.assertTrue(kelime.meanings.exists())

    def test_every_meaning_has_sentences(self):
        for anlam in Meaning.objects.all():
            with self.subTest(anlam=str(anlam)):
                self.assertTrue(anlam.examples.exists())
                self.assertLessEqual(anlam.examples.count(),
                                     Meaning.EXAMPLE_SENTENCE_COUNT)

    def test_bank_has_two_meanings_with_separate_sentences(self):
        bank = Word.objects.get(text="bank", pos="noun")
        anlamlar = list(bank.meanings.all())
        self.assertEqual(len(anlamlar), 2)
        self.assertNotEqual([c.text for c in anlamlar[0].examples.all()],
                            [c.text for c in anlamlar[1].examples.all()])

    def test_the_seed_shows_every_new_feature(self):
        self.assertTrue(Collocation.objects.exists())
        self.assertTrue(UsagePattern.objects.exists())
        self.assertTrue(FalseFriend.objects.exists())
        self.assertTrue(Expression.objects.exists())
        self.assertTrue(Category.objects.exists())
        self.assertTrue(WordRelation.objects.filter(type="confused_with").exists())
        self.assertTrue(Meaning.objects.exclude(sentiment="neutral").exists())
        self.assertTrue(Meaning.objects.exclude(register="neutral").exists())

    def test_running_it_twice_does_not_duplicate(self):
        onceki = Word.objects.count()
        call_command("seed_words", verbosity=0)
        self.assertEqual(Word.objects.count(), onceki)

class CoreEditPermissionTests(TestCase):
    """
    Çekirdek alanları kim değiştirebilir?

    Kural POZİTİF: yalnızca kelimeyi kendi ekleyen kişi. Eskiden kural
    olumsuzdu ("sahibi varsa ve o değilse engelle"), bu yüzden sahibi BOŞ
    olan kelimeleri listesine ekleyen herkes ortak sözlüğü değiştirebiliyordu.
    """

    def setUp(self):
        self.sahip = User.objects.create_user(username="sahibi", password="Sifre1234")
        self.baskasi = User.objects.create_user(username="baskasi", password="Sifre1234")

        self.benim = make_word("retain", pos="verb", meaning="elde tutmak",
                               owner=self.sahip, is_base=False)
        self.sahipsiz = make_word("obtain", pos="verb", meaning="elde etmek",
                                  owner=None, is_base=False)
        self.kur = make_word("inherent", pos="adjective", meaning="doğasında olan",
                             owner=None, is_base=True)

    # --- model kuralı ---

    def test_owner_can_edit_their_own_word(self):
        self.assertTrue(self.benim.is_editable_by(self.sahip))

    def test_someone_else_cannot(self):
        self.assertFalse(self.benim.is_editable_by(self.baskasi))

    def test_an_ownerless_word_is_editable_by_nobody(self):
        """Eski kuraldaki delik: sahibi boş olan kelime herkese açıktı."""
        self.assertFalse(self.sahipsiz.is_editable_by(self.sahip))
        self.assertFalse(self.sahipsiz.is_editable_by(self.baskasi))

    def test_a_base_word_is_locked_even_for_its_owner(self):
        kur = make_word("ubiquitous", owner=self.sahip, is_base=True)
        self.assertFalse(kur.is_editable_by(self.sahip))

    def test_an_anonymous_visitor_cannot_edit(self):
        self.assertFalse(self.benim.is_editable_by(AnonymousUser()))

    def test_a_superuser_does_not_bypass_the_form(self):
        """Ortak sözlüğün bakımı Django admin'den yapılır, kullanıcı formundan değil."""
        yonetici = User.objects.create_superuser(username="yonetici", password="Sifre1234")
        self.assertFalse(self.kur.is_editable_by(yonetici))

    # --- uç davranışı ---

    def test_adding_a_word_to_your_list_does_not_let_you_edit_it(self):
        UserWordLink.objects.create(user=self.baskasi, word=self.sahipsiz)
        self.client.login(username="baskasi", password="Sifre1234")
        cevap = self.client.get(reverse("edit_word", args=[self.sahipsiz.id]))
        self.assertEqual(cevap.status_code, 302)
        self.assertIn("#kisisel", cevap.url)

    def test_a_post_from_a_non_owner_changes_nothing(self):
        UserWordLink.objects.create(user=self.baskasi, word=self.sahipsiz)
        self.client.login(username="baskasi", password="Sifre1234")
        self.client.post(reverse("edit_word", args=[self.sahipsiz.id]), {
            "text": "ELE GECIRILDI", "pos": "noun", "meaning_1": "çalındı",
            "visibility": "private", "level": "A1",
        })
        self.sahipsiz.refresh_from_db()
        self.assertEqual(self.sahipsiz.text, "obtain")
        self.assertEqual(self.sahipsiz.pos, "verb")
        self.assertEqual(self.sahipsiz.meaningTr, "elde etmek")

    def test_the_owner_can_still_edit(self):
        self.client.login(username="sahibi", password="Sifre1234")
        cevap = self.client.get(reverse("edit_word", args=[self.benim.id]))
        self.assertEqual(cevap.status_code, 200)
        self.assertContains(cevap, 'name="meaning_1"')

    def test_the_redirect_explains_what_the_user_can_do_instead(self):
        self.client.login(username="baskasi", password="Sifre1234")
        cevap = self.client.get(reverse("edit_word", args=[self.sahipsiz.id]), follow=True)
        self.assertContains(cevap, "Kendi anlamını")

    # --- listedeki simge ---

    def test_the_pencil_is_hidden_for_words_you_do_not_own(self):
        """Düzenleyemediğin kelimede kalem göstermek tuzak olurdu."""
        UserWordLink.objects.create(user=self.baskasi, word=self.sahipsiz)
        self.client.login(username="baskasi", password="Sifre1234")
        html = self.client.get(reverse("profile_words")).content.decode()
        self.assertNotIn(reverse("edit_word", args=[self.sahipsiz.id]), html)
        self.assertIn(f'{reverse("word_detail", args=[self.sahipsiz.id])}#kisisel', html)

    def test_the_pencil_is_there_for_your_own_word(self):
        UserWordLink.objects.create(user=self.sahip, word=self.benim)
        self.client.login(username="sahibi", password="Sifre1234")
        html = self.client.get(reverse("profile_words")).content.decode()
        self.assertIn(reverse("edit_word", args=[self.benim.id]), html)

    def test_the_detail_page_shows_edit_only_to_the_owner(self):
        self.client.login(username="sahibi", password="Sifre1234")
        html = self.client.get(reverse("word_detail", args=[self.benim.id])).content.decode()
        self.assertIn(reverse("edit_word", args=[self.benim.id]), html)

        self.client.login(username="baskasi", password="Sifre1234")
        html = self.client.get(reverse("word_detail", args=[self.benim.id])).content.decode()
        self.assertNotIn(reverse("edit_word", args=[self.benim.id]), html)


class SharedWordWarningTests(TestCase):
    """Kelimeyi başkaları da listesine almışsa sahibi bunu bilerek kaydetsin."""

    def setUp(self):
        self.sahip = User.objects.create_user(username="sahibi2", password="Sifre1234")
        self.kelime = make_word("retain", pos="verb", meaning="elde tutmak",
                                owner=self.sahip, is_base=False, visibility="public")
        self.client.login(username="sahibi2", password="Sifre1234")

    def test_no_warning_when_nobody_else_has_it(self):
        UserWordLink.objects.create(user=self.sahip, word=self.kelime)
        html = self.client.get(reverse("edit_word", args=[self.kelime.id])).content.decode()
        self.assertNotIn("listesine eklemiş", html)

    def test_the_warning_counts_only_other_people(self):
        UserWordLink.objects.create(user=self.sahip, word=self.kelime)
        for ad in ("a", "b"):
            UserWordLink.objects.create(
                user=User.objects.create_user(username=ad, password="Sifre1234"),
                word=self.kelime,
            )
        html = self.client.get(reverse("edit_word", args=[self.kelime.id])).content.decode()
        self.assertIn("2 kişi daha listesine eklemiş", html)


class PersonalMeaningVisibilityTests(TestCase):
    """
    Kullanıcının eklediği anlam ORTAK sözlüğe yazılmaz ve dipnot da değildir:
    çekirdek anlamların yanında, "sadece sen görürsün" rozetiyle durur.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="okur", password="Sifre1234")
        self.baskasi = User.objects.create_user(username="okur2", password="Sifre1234")
        self.kelime = make_word("bank", meaning="banka", owner=None, is_base=True)
        self.client.login(username="okur", password="Sifre1234")
        self.client.post(reverse("word_detail", args=[self.kelime.id]), {
            "form": "meaning", "meaning_tr": "sıra, kuyruk",
            "definition": "a bank of seats",
        })

    def test_it_is_not_written_into_the_shared_dictionary(self):
        self.assertEqual(self.kelime.meanings.count(), 1)
        self.assertEqual(UserMeaning.objects.count(), 1)

    def test_the_owner_sees_it_marked_as_private(self):
        html = self.client.get(reverse("word_detail", args=[self.kelime.id])).content.decode()
        self.assertIn("sıra, kuyruk", html)
        self.assertIn("sadece sen görürsün", html)

    def test_nobody_else_sees_it(self):
        self.client.login(username="okur2", password="Sifre1234")
        html = self.client.get(reverse("word_detail", args=[self.kelime.id])).content.decode()
        self.assertNotIn("sıra, kuyruk", html)

    def test_an_anonymous_visitor_does_not_see_it(self):
        self.client.logout()
        html = self.client.get(reverse("word_detail", args=[self.kelime.id])).content.decode()
        self.assertNotIn("sıra, kuyruk", html)

    def test_the_personal_section_is_linkable(self):
        """Düzenle bağlantısı buraya yönlendiriyor; çapa kaybolursa sayfa başına düşer."""
        html = self.client.get(reverse("word_detail", args=[self.kelime.id])).content.decode()
        self.assertIn('id="kisisel"', html)

    def test_a_locked_word_explains_why_the_fields_cannot_change(self):
        html = self.client.get(reverse("word_detail", args=[self.kelime.id])).content.decode()
        self.assertIn("ortak sözlüğe ait", html)


class AileListesiTests(TestCase):
    """
    Tüm Kelimeler aile listesi (24 Eylül): satır = aile; kapalıyken kök ve
    anlamı, açılınca diğer kelimeler; her kelimenin ve ailenin ekle düğmesi.
    """

    def setUp(self):
        make_word("perceive", pos="verb", meaning="algılamak", family="perceive")
        make_word("perception", meaning="algı", family="perceive")
        make_word("perceptive", pos="adjective", meaning="sezgili", family="perceive")
        make_word("vast", pos="adjective", meaning="engin", family="vast")
        self.user = User.objects.create_user(username="aileci", password="Sifre1234")

    def _html(self, **params):
        r = self.client.get(reverse("all_words"), params)
        self.assertEqual(r.status_code, 200)
        return r, r.content.decode()

    def test_satir_aile_basina_kok_ve_anlami(self):
        r, html = self._html()
        self.assertEqual(r.context["paginator"].count, 2)          # 2 aile
        self.assertEqual(r.context["kelime_sayisi"], 4)
        perceive = next(s for s in r.context["aileler"] if s["aile"].root == "perceive")
        self.assertEqual(perceive["kok_anlam"], "algılamak")
        self.assertEqual([u["w"].text for u in perceive["uyeler"]], ["perception", "perceptive"])
        self.assertIn("<details", html)

    def test_tek_kelimelik_ailede_acilir_menu_yok(self):
        r, _ = self._html()
        vast = next(s for s in r.context["aileler"] if s["aile"].root == "vast")
        self.assertEqual(vast["uyeler"], [])

    def test_tum_aileyi_listeme_ekle(self):
        self.client.force_login(self.user)
        aile = WordFamily.objects.get(root="perceive")
        r = self.client.post(reverse("add_family_to_my_list", args=[aile.id]),
                             {"kapsam": "hepsi", "geri": "q=per"})
        self.assertRedirects(r, reverse("all_words") + f"?q=per#family-{aile.id}",
                             fetch_redirect_response=False)
        self.assertEqual(UserWordLink.objects.filter(user=self.user).count(), 3)

    def test_kok_dugmesi_yalnizca_koku_ekler(self):
        self.client.force_login(self.user)
        aile = WordFamily.objects.get(root="perceive")
        self.client.post(reverse("add_family_to_my_list", args=[aile.id]), {"kapsam": "kok"})
        self.assertEqual(list(UserWordLink.objects.filter(user=self.user)
                              .values_list("word__text", flat=True)), ["perceive"])

    def test_aile_ekleme_giris_ister(self):
        aile = WordFamily.objects.get(root="perceive")
        self.client.post(reverse("add_family_to_my_list", args=[aile.id]), {"kapsam": "hepsi"})
        self.assertEqual(UserWordLink.objects.count(), 0)


class AramaTests(TestCase):
    """25 Eylül: canlı arama, filtre paneli, bağımsız sonuçlar, öneriler."""

    def setUp(self):
        make_word("perceive", pos="verb", meaning="algılamak", family="perceive", level="B1")
        make_word("perception", meaning="algı", family="perceive", level="B2")
        make_word("perceptive", pos="adjective", meaning="sezgili", family="perceive", level="C1")
        make_word("vast", pos="adjective", meaning="engin", family="vast", level="B2")
        self.user = User.objects.create_user(username="arayan", password="Sifre1234")

    def _get(self, **params):
        r = self.client.get(reverse("all_words"), params)
        self.assertEqual(r.status_code, 200)
        return r

    def test_aramada_kelimeler_ailesinden_bagimsiz(self):
        r = self._get(q="percep")
        self.assertTrue(r.context["duz"])
        self.assertEqual([x["w"].text for x in r.context["satirlar"]], ["perception", "perceptive"])

    def test_tam_eslesme_en_ustte(self):
        make_word("perceiver", meaning="algılayan", family="perceive")
        r = self._get(q="perceive")
        self.assertEqual(r.context["satirlar"][0]["w"].text, "perceive")

    def test_filtre_varken_de_bagimsiz_liste(self):
        r = self._get(level=["B2"])
        self.assertTrue(r.context["duz"])
        self.assertEqual(sorted(x["w"].text for x in r.context["satirlar"]), ["perception", "vast"])

    def test_coklu_tur_ve_seviye(self):
        r = self._get(pos=["verb", "adjective"], level=["B1", "C1"])
        self.assertEqual(sorted(x["w"].text for x in r.context["satirlar"]),
                         ["perceive", "perceptive"])

    def test_nerede_aransin_alani(self):
        self.assertEqual(self._get(q="algı", alan=["kelime"]).context["kelime_sayisi"], 0)
        self.assertEqual(self._get(q="algı", alan=["anlam"]).context["kelime_sayisi"], 2)

    def test_eski_filter_by_baglantisi_calisir(self):
        r = self._get(q="engin", filter_by="meaning")
        self.assertEqual([x["w"].text for x in r.context["satirlar"]], ["vast"])

    def test_partial_yalnizca_sonuc_bolumu(self):
        r = self._get(q="vast", partial=1)
        html = r.content.decode()
        self.assertNotIn("arama-formu", html)
        self.assertIn("vast", html)

    def test_bulunamayinca_oneri(self):
        r = self._get(q="percepton")          # yazım hatası
        self.assertEqual(r.context["kelime_sayisi"], 0)
        self.assertIn("perception", [x["w"].text for x in r.context["oneriler"]])
        self.assertContains(r, "Bu aradığınız sanırım bizde yok")

    def test_oneri_turkce_anlamdan(self):
        r = self._get(q="engim")               # "engin" yanlış yazılmış
        self.assertIn("vast", [x["w"].text for x in r.context["oneriler"]])

    def test_filtre_yuzunden_bos_ise_soylenir(self):
        r = self._get(q="vast", level=["A1"])
        self.assertEqual(r.context["filtresiz_sayi"], 1)

    def test_listeme_ekle_ajax_sayfa_yenilemez(self):
        self.client.force_login(self.user)
        w = Word.objects.get(text="vast")
        r = self.client.get(reverse("add_to_my_list", args=[w.id]), HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["kayitli"])
        self.assertIn("remove-from-my-list", r.json()["html"])
        r = self.client.get(reverse("remove_from_my_list", args=[w.id]), HTTP_X_REQUESTED_WITH="fetch")
        self.assertFalse(r.json()["kayitli"])

    def test_kok_dugmesi_ekle_ve_cikar_ajax(self):
        self.client.force_login(self.user)
        aile = WordFamily.objects.get(root="perceive")
        url = reverse("add_family_to_my_list", args=[aile.id])
        d = self.client.post(url, {"kapsam": "kok"}, HTTP_X_REQUESTED_WITH="fetch").json()
        self.assertIn('value="cikar"', d["kok_html"])
        self.client.post(url, {"kapsam": "kok", "islem": "cikar"}, HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(UserWordLink.objects.filter(user=self.user).count(), 0)


class IfadeTests(TestCase):
    """25 Eylül: ifadeler — işlev grupları, benzerler, İçerik filtresi, ifade listesi, detay."""

    @classmethod
    def setUpTestData(cls):
        from io import StringIO
        call_command("ifadeleri_yukle", stdout=StringIO())
        make_word("perceive", pos="verb", meaning="algılamak", family="perceive", level="B1")
        cls.user = User.objects.create_user(username="ifadeci", password="Sifre1234")

    def _ifade(self, metin):
        from words.models import Expression
        return Expression.objects.get(text=metin)

    def test_yukleme_gruplar_ve_ifadeler(self):
        from words.models import Expression, ExpressionGroup
        self.assertEqual(ExpressionGroup.objects.count(), 21)
        self.assertGreaterEqual(Expression.objects.filter(visibility="public").count(), 280)
        self.assertEqual(self._ifade("however").group.slug, "karsitlik")
        # "while" iki işlevde: tek kayıt, ek işlevle
        self.assertTrue(self._ifade("while").extra_groups.exists())

    def test_yukleme_tekrar_calisinca_cogaltmaz(self):
        from io import StringIO
        from words.models import Expression
        once = Expression.objects.count()
        call_command("ifadeleri_yukle", stdout=StringIO())
        self.assertEqual(Expression.objects.count(), once)

    def test_ayni_isi_yapanlar_birbirini_gorur(self):
        benzer = set(self._ifade("but").similar.values_list("text", flat=True))
        self.assertTrue({"however", "nevertheless", "nonetheless"} <= benzer)
        self.assertNotIn("but", benzer)
        self.assertIn("but", set(self._ifade("however").similar.values_list("text", flat=True)))

    def test_her_ifadenin_ornegi_ve_noktalamasi_var(self):
        from words.models import Expression, ExampleKind
        for e in Expression.objects.filter(group__isnull=False):
            self.assertTrue(e.examples.filter(kind=ExampleKind.EXAMPLE).exists(), e.text)
            self.assertTrue(e.punctuation_note, e.text)

    def test_aramasiz_konu_konu_listelenir(self):
        r = self.client.get(reverse("all_words"))
        bloklar = r.context["ifade_bloklari"]
        self.assertEqual(bloklar[0]["grup"].slug, "karsitlik")
        self.assertIn("Anlamı tersine çevirenler", r.content.decode())
        self.assertFalse(r.context["ifade_acik"])          # kelimeler de açıkken kapalı gelir
        self.assertTrue(r.context["aileler"])

    def test_yalnizca_ifadeler(self):
        r = self.client.get(reverse("all_words"), {"icerik": "ifade"})
        self.assertTrue(r.context["ifade_acik"])
        self.assertFalse(r.context["aileler"])
        self.assertNotIn("Henüz kelime yok", r.content.decode())

    def test_yalnizca_kelimeler(self):
        r = self.client.get(reverse("all_words"), {"icerik": "kelime"})
        self.assertNotIn("ifade_bloklari", r.context)
        r = self.client.get(reverse("all_words"), {"icerik": "kelime", "q": "however"})
        self.assertNotIn("ifade_satirlari", r.context)

    def test_aramada_ifade_bulunur_tam_eslesme_once(self):
        r = self.client.get(reverse("all_words"), {"q": "however"})
        self.assertEqual(r.context["ifade_satirlari"][0]["e"].text, "however")
        self.assertIsNone(r.context.get("oneriler"))
        self.assertIn("ifade bulundu", r.content.decode())
        self.assertNotIn("Sonuç yok", r.content.decode())

    def test_anlamda_arama_ifade_bulur(self):
        r = self.client.get(reverse("all_words"), {"q": "örneğin", "alan": ["anlam"]})
        self.assertIn("for example", [x["e"].text for x in r.context["ifade_satirlari"]])

    def test_detay_sayfasi(self):
        e = self._ifade("however")
        r = self.client.get(reverse("expression_detail", args=[e.id]))
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        for parca in ("Noktalama", "Örnek cümleler", "Aynı işi yapan ifadeler", "nevertheless", "Yönü: Karşıtlık"):
            self.assertIn(parca, html)
        self.assertTrue(r.context["dogrular"])
        self.assertTrue(r.context["yanlislar"])

    def test_ifade_listesi_ajax(self):
        from words.models import UserExpressionLink
        e = self._ifade("however")
        self.client.login(username="ifadeci", password="Sifre1234")
        d = self.client.get(reverse("add_expression_to_my_list", args=[e.id]),
                            {"boyut": "k"}, HTTP_X_REQUESTED_WITH="fetch").json()
        self.assertTrue(d["kayitli"])
        self.assertIn("remove-expression-from-my-list", d["html"])
        self.assertEqual(UserExpressionLink.objects.filter(user=self.user).count(), 1)
        self.assertEqual(UserWordLink.objects.filter(user=self.user).count(), 0)   # kelime listesi ayrı
        self.client.get(reverse("remove_expression_from_my_list", args=[e.id]), HTTP_X_REQUESTED_WITH="fetch")
        self.assertFalse(UserExpressionLink.objects.filter(user=self.user).exists())

    def test_ifade_listesi_jssiz_geri_doner(self):
        e = self._ifade("however")
        self.client.login(username="ifadeci", password="Sifre1234")
        r = self.client.get(reverse("add_expression_to_my_list", args=[e.id]), {"q": "how"})
        self.assertRedirects(r, reverse("all_words") + f"?q=how#expr-{e.id}", fetch_redirect_response=False)
        r = self.client.get(reverse("add_expression_to_my_list", args=[e.id]), {"next": "detay"})
        self.assertRedirects(r, reverse("expression_detail", args=[e.id]), fetch_redirect_response=False)

    def test_giris_yapmadan_eklenemez(self):
        e = self._ifade("however")
        r = self.client.get(reverse("add_expression_to_my_list", args=[e.id]))
        self.assertEqual(r.status_code, 302)
        self.assertIn("login", r.url)
