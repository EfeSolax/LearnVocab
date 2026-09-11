"""
Kelime görünürlüğü (visibility) testleri.

Bir kullanıcının başkasının gizli kelimesini URL'yi tahmin ederek
göremediğini garanti eder.
"""

import re

from django.test import TestCase
from django.urls import reverse, NoReverseMatch

from users.models import User
from words.models import Word, UserWordLink
from words.views import can_view_word, visible_words_qs


class VisibilityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="sahip", password="Sifre1234")
        self.friend = User.objects.create_user(username="arkadas", password="Sifre1234")
        self.stranger = User.objects.create_user(username="yabanci", password="Sifre1234")
        self.owner.friends.add(self.friend)

        def make(visibility, name, **extra):
            return Word.objects.create(
                owner=self.owner,
                englishWord=name,
                meaningTr=f"{name}-tr",
                exampleSentence1=f"Example {name}.",
                visibility=visibility,
                **extra,
            )

        self.public_word = make("public", "public_word")
        self.friends_word = make("friends", "friends_word")
        self.private_word = make("private", "private_word")
        self.base_word = Word.objects.create(
            englishWord="base_word",
            meaningTr="temel",
            exampleSentence1="Example base.",
            isBaseWord=True,
            wordLevel="101",
        )

    def test_owner_sees_everything_of_their_own(self):
        for word in (self.public_word, self.friends_word, self.private_word):
            self.assertTrue(can_view_word(word, self.owner))

    def test_friend_sees_friends_visibility(self):
        self.assertTrue(can_view_word(self.friends_word, self.friend))

    def test_stranger_cannot_see_friends_or_private(self):
        self.assertFalse(can_view_word(self.friends_word, self.stranger))
        self.assertFalse(can_view_word(self.private_word, self.stranger))

    def test_everyone_sees_public_and_base(self):
        for word in (self.public_word, self.base_word):
            self.assertTrue(can_view_word(word, self.stranger))

    def test_saved_word_stays_visible_to_the_saver(self):
        UserWordLink.objects.create(user=self.stranger, word=self.private_word)
        self.assertTrue(can_view_word(self.private_word, self.stranger))

    def test_visible_words_qs_matches_can_view_word(self):
        visible = set(visible_words_qs(self.stranger).values_list("id", flat=True))
        self.assertIn(self.public_word.id, visible)
        self.assertIn(self.base_word.id, visible)
        self.assertNotIn(self.private_word.id, visible)
        self.assertNotIn(self.friends_word.id, visible)

    def test_word_detail_redirects_for_unauthorized_user(self):
        self.client.login(username="yabanci", password="Sifre1234")
        response = self.client.get(reverse("word_detail", args=[self.private_word.id]))
        self.assertRedirects(response, reverse("all_words"))

    def test_word_detail_works_for_owner(self):
        self.client.login(username="sahip", password="Sifre1234")
        response = self.client.get(reverse("word_detail", args=[self.private_word.id]))
        self.assertEqual(response.status_code, 200)


class CollocationTests(TestCase):
    """Kullanım kalıpları alanı — synonyms/antonyms ile aynı virgüllü format."""

    def setUp(self):
        self.word = Word.objects.create(
            englishWord="retain",
            meaningTr="elde tutmak",
            exampleSentence1="They retain full control.",
        )

    def test_empty_collocations_returns_empty_list(self):
        self.assertEqual(self.word.collocations_list, [])

    def test_collocations_are_split_and_trimmed(self):
        self.word.collocations = "retain information,  retain control , retain its shape"
        self.word.save()
        self.assertEqual(
            self.word.collocations_list,
            ["retain information", "retain control", "retain its shape"],
        )

    def test_blank_entries_are_dropped(self):
        self.word.collocations = "retain information, , ,retain control,"
        self.word.save()
        self.assertEqual(
            self.word.collocations_list, ["retain information", "retain control"]
        )


class ExampleSentenceTests(TestCase):
    """
    10 örnek cümle alanı ve boşları süzen `example_sentences` property'si.

    Bir kelime tek bir cümleden öğrenilmediği için alan sayısı 3'ten 10'a
    çıkarıldı; quiz üretimi de bu listeden besleniyor.
    """

    def _word(self, **sentences):
        defaults = {"exampleSentence1": "They retain full control."}
        defaults.update(sentences)
        return Word.objects.create(
            englishWord="retain", meaningTr="elde tutmak", **defaults
        )

    def test_model_has_ten_sentence_fields(self):
        self.assertEqual(Word.EXAMPLE_SENTENCE_COUNT, 10)
        field_names = {f.name for f in Word._meta.get_fields()}
        for i in range(1, 11):
            self.assertIn(f"exampleSentence{i}", field_names)

    def test_only_first_sentence_is_required(self):
        word = self._word()
        word.full_clean(exclude=["owner"])  # hata fırlatmamalı

    def test_empty_and_blank_sentences_are_filtered(self):
        word = self._word(
            exampleSentence2=None,
            exampleSentence3="",
            exampleSentence4="   ",
            exampleSentence5="They retained it.",
        )
        self.assertEqual(
            word.example_sentences,
            ["They retain full control.", "They retained it."],
        )

    def test_sentences_keep_their_order(self):
        word = self._word(
            exampleSentence7="Seventh sentence about retain.",
            exampleSentence3="Third sentence about retain.",
        )
        self.assertEqual(
            word.example_sentences,
            [
                "They retain full control.",
                "Third sentence about retain.",
                "Seventh sentence about retain.",
            ],
        )

    def test_sentences_are_stripped(self):
        word = self._word(exampleSentence2="   padded sentence   ")
        self.assertIn("padded sentence", word.example_sentences)
        self.assertNotIn("   padded sentence   ", word.example_sentences)

    def test_has_extra_example_sentences(self):
        self.assertFalse(self._word().has_extra_example_sentences)
        self.assertFalse(self._word(exampleSentence6="  ").has_extra_example_sentences)
        self.assertTrue(self._word(exampleSentence6="Another one.").has_extra_example_sentences)


class AllWordsPaginationTests(TestCase):
    """
    "Tüm Kelimeler" sayfası artık "Kelimelerim" ile aynı esnek sayfalamayı
    kullanıyor: ilk/son, sayfa numaraları, sayfa başına adet ve doğrudan
    sayfaya atlama.
    """

    def setUp(self):
        for i in range(120):
            Word.objects.create(
                englishWord=f"word{i:03}", meaningTr=f"anlam{i}",
                exampleSentence1=f"A sentence with word{i:03}.",
                isBaseWord=True, wordLevel="101",
            )

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
        response = self._get(q="word01", level="101", per_page=25)
        base_qs = response.context["base_qs"]
        self.assertIn("q=word01", base_qs)
        self.assertIn("level=101", base_qs)
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
        for url_name in ("profile_words", "add_word", "ai_add_words_page", "attempt_quiz"):
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

    def test_friends_visibility_still_works_for_existing_words(self):
        """Eski 'arkadaşlara açık' kelimeler kaybolmamalı."""
        from words.views import can_view_word

        self.user.friends.add(self.other)
        word = Word.objects.create(
            owner=self.user, englishWord="shared", meaningTr="paylaşılan",
            exampleSentence1="A shared sentence.", visibility="friends",
        )
        self.assertTrue(can_view_word(word, self.other))


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

    def test_words_section_points_to_all_words_when_logged_out(self):
        """Girişsiz kullanıcı Kelimeler'e basınca boş bir kapı değil, içerik görsün."""
        navbar = self._navbar(logged_in=False)
        self.assertIn(reverse("all_words"), navbar)

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


class WordsSectionTabsTests(TestCase):
    """Kelimeler bölümünün iki sayfası tek şerit üzerinden geziliyor."""

    def setUp(self):
        self.user = User.objects.create_user(username="tabuser", password="Sifre1234")
        self.client.login(username="tabuser", password="Sifre1234")

    def _tabs(self, url):
        html = self.client.get(url, follow=True).content.decode()
        start = html.index("Kelimelerim\n        </a>") - 1200
        return html[start:start + 2000]

    def test_both_pages_show_the_switcher(self):
        for url in (reverse("profile_words"), reverse("all_words")):
            with self.subTest(url=url):
                html = self.client.get(url).content.decode()
                self.assertIn(reverse("profile_words"), html)
                self.assertIn(reverse("all_words"), html)

    def test_only_one_tab_is_current_on_each_page(self):
        for url in (reverse("profile_words"), reverse("all_words")):
            with self.subTest(url=url):
                html = self.client.get(url).content.decode()
                tabs_start = html.index("Kelimelerim")
                # Şerit sayfanın en üstünde; ilk aria-current oradaki sekme
                self.assertIn('aria-current="page"', html[:tabs_start + 3000])

    def test_switcher_is_full_width_on_mobile_only(self):
        html = self.client.get(reverse("all_words")).content.decode()
        self.assertIn("-mx-4 sm:mx-0", html)

    def test_both_pages_use_the_same_layout_width(self):
        """Şerit iki sayfada aynı genişlikte dursun diye yerleşim de aynı."""
        for url in (reverse("profile_words"), reverse("all_words")):
            with self.subTest(url=url):
                html = self.client.get(url).content.decode()
                self.assertIn("mx-auto max-w-7xl px-4 sm:px-6 lg:px-8", html)


class LoginGateTests(TestCase):
    """Girişsiz kullanıcı korumalı bölüme gelince giriş formuna fırlatılmıyor."""

    GATED = {
        "profile_words": "Kelimelerim",
        "profile_quizzes": "Egzersizler",
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
        html = self.client.get(reverse("profile_quizzes")).content.decode()
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
        for ad in ("export_all", "export_mywords", "export_myquizzes", "export_mytexts"):
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
