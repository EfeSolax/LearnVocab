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
    CEFR_CHOICES, CEFR_LEVELS, Category, Collocation, ExampleSentence, Expression,
    FalseFriend, Meaning, Register, Sentiment, UsagePattern, UserWordLink, Word,
    WordFamily, WordRelation,
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
        html = self._html("sozluk")
        self.assertIn("darkMode: 'class'", html)

    def test_theme_script_runs_before_the_body(self):
        html = self._html("sozluk")
        script_index = html.index("localStorage.getItem('theme')")
        body_index = html.index("<body")
        self.assertLess(script_index, body_index,
                        "tema scripti body'den sonra çalışıyor, sayfa beyaz parlar")

    def test_system_preference_is_the_default(self):
        html = self._html("sozluk")
        self.assertIn("prefers-color-scheme: dark", html)

    def test_color_scheme_is_declared_for_native_controls(self):
        """Kaydırma çubuğu ve select açılır listesi de temaya uymalı."""
        html = self._html("sozluk")
        self.assertIn("color-scheme: dark", html)

    def test_tema_dugmesi_ust_cubukta_degil_ayarlarda(self):
        """Rapor 18.26: tema düğmesi üst çubuktan kalktı, Ayarlar sayfasında."""
        self.assertNotIn("data-theme-toggle", self._html("sozluk"))
        self.assertNotIn("data-tema-sec", self._html("sozluk").split("</header>")[0])

    def test_pages_carry_dark_variants(self):
        for url_name in ("sozluk", "index", "about", "login", "register"):
            with self.subTest(page=url_name):
                html = self._html(url_name)
                self.assertGreater(html.count("dark:"), 20,
                                   f"{url_name} sayfasında karanlık tema sınıfı yok denecek kadar az")

    def test_logged_in_pages_carry_dark_variants(self):
        self.client.login(username="temauser", password="Sifre1234")
        for url_name in ("exercises_page", "user_profile"):
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
    """
    Üst çubuk (rapor 2.1–2.2): beş bölüm bu sırayla, Ana Sayfa ortada;
    logo ana sayfaya; sağ üstte Ayarlar dişlisi ya da Giriş Yap.
    """

    SECTIONS = (">Sözlük<", ">Çalışmalar<", ">Ana Sayfa<", ">Okumalar<", ">Yazılar<")

    def setUp(self):
        self.user = User.objects.create_user(username="menuuser", password="Sifre1234")

    def _navbar(self, logged_in):
        if logged_in:
            self.client.login(username="menuuser", password="Sifre1234")
        html = self.client.get(reverse("index"), follow=True).content.decode()
        start = html.index('<header id="navbar"')
        return squash(html[start:html.index("</header>", start)])

    def test_logo_goes_home(self):
        navbar = self._navbar(logged_in=False)
        self.assertIn(reverse("index"), navbar)
        self.assertIn("Learn&nbsp;Vocab", navbar)  # logonun yanındaki isim

    def test_five_sections_in_order_for_everyone(self):
        """Sözlük · Çalışmalar · Ana Sayfa · Okumalar · Yazma — girişsiz de."""
        for logged_in in (False, True):
            navbar = self._navbar(logged_in=logged_in)
            with self.subTest(logged_in=logged_in):
                yerler = [navbar.index(etiket) for etiket in self.SECTIONS]
                self.assertEqual(yerler, sorted(yerler))

    def test_about_and_old_names_are_not_in_the_menu(self):
        navbar = self._navbar(logged_in=True)
        for eski in (">Hakkında<", ">Kelimeler<", ">Metinler<", ">Egzersizler<",
                     ">Tüm Kelimeler<", ">Kelimelerim<"):
            with self.subTest(eski=eski):
                self.assertNotIn(eski, navbar)
        self.assertNotIn(reverse("about"), navbar)

    def test_section_targets(self):
        navbar = self._navbar(logged_in=True)
        for ad in ("sozluk", "learn_pass_page", "index", "readings", "profile_texts"):
            with self.subTest(hedef=ad):
                self.assertIn(f'href="{reverse(ad)}"', navbar)

    def test_menu_does_not_point_to_old_word_pages(self):
        for giris in (False, True):
            with self.subTest(logged_in=giris):
                navbar = self._navbar(logged_in=giris)
                self.assertNotIn("/words/all-words/", navbar)
                self.assertNotIn("/profile/profile/words/", navbar)

    def test_profil_fotografi_hesaba_goturur(self):
        """Rapor 18.26: dişli yerine profil fotoğrafı; dokununca Hesap."""
        navbar = self._navbar(logged_in=True)
        self.assertIn("data-hesap-dugmesi", navbar)
        self.assertIn('title="Hesap"', navbar)
        self.assertNotIn('title="Ayarlar"', navbar)
        self.assertIn(reverse("user_profile"), navbar)
        self.assertNotIn("Giriş Yap", navbar)
        self.assertNotIn("Hoş geldin", navbar)

    def test_login_button_when_logged_out_returns_here(self):
        navbar = self._navbar(logged_in=False)
        self.assertIn("Giriş Yap", navbar)
        self.assertIn(f"{reverse('login')}?next=", navbar)
        self.assertNotIn("data-hesap-dugmesi", navbar)

    def test_logout_is_on_the_profile_page(self):
        """Üst çubukta çıkış yok; profil fotoğrafının açtığı Hesap sayfasında var."""
        navbar = self._navbar(logged_in=True)
        self.assertNotIn(">Çıkış Yap<", navbar)
        page = self.client.get(reverse("user_profile"), follow=True).content.decode()
        self.assertIn(reverse("logout"), page)

    def test_hamburger_menu_is_gone(self):
        navbar = self._navbar(logged_in=True)
        self.assertNotIn('id="mobile-menu"', navbar)

    def test_desktop_menu_is_hidden_on_mobile(self):
        self.assertIn("hidden lg:flex", self._navbar(logged_in=False))


class MobileTabBarTests(TestCase):
    """Mobil alt sekme çubuğu — aynı beş bölüm, aynı sıra, ikonlu."""

    def setUp(self):
        self.user = User.objects.create_user(username="mobileuser", password="Sifre1234")

    def _bar(self, url=None, logged_in=False):
        if logged_in:
            self.client.login(username="mobileuser", password="Sifre1234")
        html = self.client.get(url or reverse("index"), follow=True).content.decode()
        start = html.index('aria-label="Alt menü"')
        return squash(html[start:html.index("</nav>", start)])

    def test_bar_has_five_sections_in_order_for_anonymous_users(self):
        bar = self._bar()
        yerler = [bar.index(etiket) for etiket in NavbarMenuTests.SECTIONS]
        self.assertEqual(yerler, sorted(yerler))

    def test_home_is_in_the_middle(self):
        bar = self._bar()
        etiketler = re.findall(r'<span class="text-\[11px\][^"]*">([^<]+)</span>', bar)
        self.assertEqual(etiketler, ["Sözlük", "Çalışmalar", "Ana Sayfa", "Okumalar", "Yazılar"])
        self.assertEqual(etiketler[2], "Ana Sayfa")

    def test_every_section_has_an_icon(self):
        self.assertEqual(self._bar().count("<svg"), 5)

    def test_bar_is_hidden_on_desktop(self):
        self.assertIn("lg:hidden", self._bar())

    def test_active_section_is_marked(self):
        for ad, etiket in (("sozluk", "Sözlük"), ("readings", "Okumalar"), ("index", "Ana Sayfa")):
            with self.subTest(sayfa=ad):
                bar = self._bar(reverse(ad))
                self.assertEqual(bar.count('aria-current="page"'), 1)
                aktif = bar[bar.index('aria-current="page"'):]
                self.assertIn(f">{etiket}<", aktif[:aktif.index("</a>")])

    def test_content_is_not_covered_by_the_bar(self):
        html = self.client.get(reverse("index")).content.decode()
        self.assertIn("pb-20 lg:pb-0", html)

    def test_writing_section_requires_login_only_for_guests(self):
        """Yazma gizlenmez; girişsizken dokununca giriş sayfasına yönlendirir."""
        self.assertIn('data-giris-gerekli="yazma"', self._bar())
        self.assertNotIn("data-giris-gerekli", self._bar(logged_in=True))


class NavigationSectionTests(TestCase):
    """Hangi sayfa hangi bölümü aktif yapıyor (LearnVocab/navigation.py)."""

    def setUp(self):
        self.user = User.objects.create_user(username="bolumuser", password="Sifre1234")

    def _section_of(self, url):
        response = self.client.get(url, follow=True)
        return response.context["nav_section"]

    def test_dictionary_maps_to_the_dictionary_section(self):
        self.client.login(username="bolumuser", password="Sifre1234")
        self.assertEqual(self._section_of(reverse("sozluk")), "sozluk")

    def test_study_pages_map_to_calismalar(self):
        self.client.login(username="bolumuser", password="Sifre1234")
        for ad in ("learn_pass_page", "exercises_page"):
            with self.subTest(sayfa=ad):
                self.assertEqual(self._section_of(reverse(ad)), "calismalar")

    def test_texts_map_to_yazma(self):
        self.client.login(username="bolumuser", password="Sifre1234")
        self.assertEqual(self._section_of(reverse("profile_texts")), "yazma")

    def test_readings_placeholder_exists(self):
        response = self.client.get(reverse("readings"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["nav_section"], "readings")

    def test_home_page_is_its_own_section(self):
        self.assertEqual(self._section_of(reverse("index")), "home")

    def test_about_belongs_to_no_section(self):
        self.assertIsNone(self._section_of(reverse("about")))


class OldPagesRemovedTests(TestCase):
    """
    Eski kelime sayfaları, yapay zekâ ile kelime ekleme ve eski profil
    alt sayfaları 29 Eylül'de tamamen kaldırıldı (rapor 18.13).
    """

    # İşlem uçları ve kaldırılan özellikler: 404. Eski SAYFA adresleri ise yeni
    # karşılıklarına 301 ile yönlenir (LearnVocab/test_seo.py, rapor 18.15).
    ESKI_ADRESLER = (
        "/words/add-all-words/", "/words/add-selected-to-my-list/",
        "/words/add-family-to-my-list/1/", "/words/ai-add/", "/words/ai-add/create/",
        "/profile/profile/words/add-word/", "/profile/delete-all-words/",
        "/words/add-to-my-list/1/", "/sozluk/kart/1/", "/exercises/learn/api/verdict/",
    )

    def test_old_addresses_are_gone(self):
        User.objects.create_user(username="eskiuser", password="Sifre1234")
        self.client.login(username="eskiuser", password="Sifre1234")
        for adres in self.ESKI_ADRESLER:
            with self.subTest(adres=adres):
                self.assertEqual(self.client.get(adres).status_code, 404)

class LoginGateTests(TestCase):
    """
    Girişsiz kullanıcı korumalı bir SAYFANIN adresini doğrudan açarsa giriş
    formuna fırlatılmıyor: açıklama ekranı ve menü yerinde kalıyor; oradaki
    "Giriş Yap" geri dönüş adresini (?next=) taşıyor.
    """

    GATED = {
        "exercises_page": "Egzersizler",
        "profile_texts": "Yazılar",
        "user_profile": "Hesap",
        "settings_page": "Ayarlar",
    }

    def test_gated_pages_explain_instead_of_redirecting(self):
        for name, etiket in self.GATED.items():
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                self.assertIn("önce giriş yapın", html)
                self.assertIn(etiket, html)
                self.assertIn(f"{reverse('login')}?next={reverse(name).replace('/', '%2F')}", html)

    def test_gate_keeps_the_menu_visible(self):
        html = self.client.get(reverse("exercises_page")).content.decode()
        self.assertIn('aria-label="Alt menü"', html)

    def test_open_sections_stay_public(self):
        """Sözlük (Keşfet), Learn & Pass ve Okumalar girişsiz açık (rapor 2.3)."""
        for ad in ("sozluk", "learn_pass_page", "readings"):
            with self.subTest(sayfa=ad):
                response = self.client.get(reverse(ad))
                self.assertEqual(response.status_code, 200)
                self.assertNotIn("önce giriş yapın", response.content.decode())

    def test_logged_in_users_are_not_gated(self):
        User.objects.create_user(username="gateuser", password="Sifre1234")
        self.client.login(username="gateuser", password="Sifre1234")
        for name in self.GATED:
            with self.subTest(page=name):
                html = self.client.get(reverse(name), follow=True).content.decode()
                self.assertNotIn("önce giriş yapın", html)


class HesapVeAyarlarTests(TestCase):
    """Rapor 18.26: Hesap (profil fotoğrafından açılır) ve ondan gidilen Ayarlar."""

    def setUp(self):
        from usersettings.models import UserSettings

        self.user = User.objects.create_user(
            username="profiluser", password="Sifre1234", email="eski@x.com"
        )
        UserSettings.objects.create(user=self.user)
        self.client.login(username="profiluser", password="Sifre1234")

    def _hesap(self):
        response = self.client.get(reverse("user_profile"))
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def _ayarlar(self):
        response = self.client.get(reverse("settings_page"))
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_hesap_sayfasi(self):
        html = self._hesap()
        for parca in ("Hesap Bilgileri", "Parolamı Değiştir", "Çıkış Yap", 'name="first_name"',
                      'name="last_name"', 'name="email"', 'name="username"', 'name="profile_pic"'):
            with self.subTest(parca=parca):
                self.assertIn(parca, html)
        # Ayarlar'a buradan gidilir; ayarların kendisi burada değil.
        self.assertIn(reverse("settings_page"), html)
        self.assertNotIn("Tehlikeli Bölge", html)
        self.assertIn('action="%s"' % reverse("user_profile"), html)

    def test_ayarlar_sayfasi(self):
        html = self._ayarlar()
        for parca in ("Görünüm", "Çalışma", "E-posta Bildirimleri", "Verilerim", "Tehlikeli Bölge",
                      'data-tema-sec="sistem"', 'data-tema-sec="light"', 'data-tema-sec="dark"',
                      'name="sertlik"', 'name="audio"', 'name="dailyGoalsMail"',
                      'name="featuresMail"', 'name="improvementsMail"', "data-seviye-ayari"):
            with self.subTest(parca=parca):
                self.assertIn(parca, html)
        self.assertIn(reverse("user_profile"), html)          # Hesap'a geri dönüş

    def test_oran_kaydirma_cubugu_ve_soru_sayisi(self):
        """Efe, 30 Eylül: oran %10'luk adımlarla kaydırma çubuğu; soru sayısı 5/10/15/20."""
        from egzersizler import sorular
        from learnpass import selection
        from usersettings.models import UserSettings
        html = self._ayarlar()
        self.assertIn('type="range" id="learnpass_yeni_orani" name="learnpass_yeni_orani" min="0" max="100" step="10"', html)
        for sayi in (5, 10, 15, 20):
            self.assertIn(f'name="egzersiz_soru_sayisi" value="{sayi}"', html)
        self.assertNotIn('name="egzersiz_soru_sayisi" value="25"', html)

        self.client.post(reverse("save_settings"), {"learnpass_yeni_orani": "70", "egzersiz_soru_sayisi": "15"})
        self.user.refresh_from_db()
        self.assertEqual(selection.kullanici_yeni_orani(self.user), 0.7)
        self.assertEqual(sorular.varsayilan_soru_sayisi(self.user), 15)

        # Adım dışı / seçenek dışı değerler yok sayılır
        self.client.post(reverse("save_settings"), {"learnpass_yeni_orani": "75", "egzersiz_soru_sayisi": "25"})
        ayar = UserSettings.objects.get(user=self.user)
        self.assertEqual((ayar.learnpass_yeni_orani, ayar.egzersiz_soru_sayisi), (70, 15))
        self.client.post(reverse("save_settings"), {"learnpass_yeni_orani": "0"})
        self.assertEqual(selection.kullanici_yeni_orani(User.objects.get(pk=self.user.pk)), 0.0)

    def test_gunluk_hedef_kalkti(self):
        """Rapor 18.23: günlük hedef ayarı yok; seri sabit kurallarla çalışır."""
        from usersettings.models import UserSettings
        self.assertNotIn("dailyGoal\"", self._ayarlar())
        self.assertNotIn("Günlük Soru Hedefi", self._ayarlar())
        self.assertFalse(hasattr(UserSettings, "dailyGoal"))

    def test_tehlikeli_islemler_parola_sorar(self):
        html = self._ayarlar()
        self.assertEqual(html.count('name="confirm_password"'), 2)
        self.assertIn(reverse("remove_all_words"), html)
        self.assertIn(reverse("delete_myaccount"), html)

    def test_disa_aktarma_baglantilari(self):
        html = self._ayarlar()
        for ad in ("export_all", "export_mywords", "export_mytexts"):
            with self.subTest(baglanti=ad):
                self.assertIn(reverse(ad), html)

    def test_hesap_formu_kaydeder(self):
        self.client.post(reverse("user_profile"), {
            "email": "yeni@x.com", "first_name": "Efe", "last_name": "Solmaz",
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "yeni@x.com")
        self.assertEqual(self.user.first_name, "Efe")

    def test_yorum_dugmeleri_gizli(self):
        """Yorumlar kapalıyken 'yorumlarımı sil' düğmesi görünmemeli."""
        html = self._ayarlar()
        self.assertNotIn("Yorumları Kaldır", html)
        self.assertNotIn("Tüm Yorumlarımı Dışa Aktar", html)

    def test_ayarlari_kaydetmek_ayarlara_doner_ve_sertligi_yazar(self):
        from texts.models import YazmaAyari
        from usersettings.models import UserSettings
        response = self.client.post(reverse("save_settings"), {"sertlik": "titiz", "audio": "on"})
        self.assertRedirects(response, reverse("settings_page"))
        self.assertEqual(YazmaAyari.sertlik_of(self.user), "titiz")
        ayar = UserSettings.objects.get(user=self.user)
        self.assertTrue(ayar.audio)
        self.assertFalse(ayar.featuresMail)


class KayitFormuTests(TestCase):
    """Rapor 18.23: ad, soyad, e-posta, kullanıcı adı, şifre (tek kez, göster/gizle)."""

    VERI = {"first_name": "Efe", "last_name": "Solmaz", "email": "Efe@Example.com",
            "username": "efes", "password": "Sifre1234"}

    def test_form_alanlari(self):
        html = self.client.get(reverse("register")).content.decode()
        for alan in ('name="first_name"', 'name="last_name"', 'name="email"', 'name="username"',
                     'name="password"', "data-sifre-goster"):
            self.assertIn(alan, html)
        for eski in ('name="level"', 'name="password2"', 'name="password1"', "Kur"):
            self.assertNotIn(eski, html)

    def test_kayit_olur(self):
        cevap = self.client.post(reverse("register"), self.VERI)
        self.assertRedirects(cevap, reverse("login"))
        u = User.objects.get(username="efes")
        self.assertEqual((u.first_name, u.last_name, u.email, u.cefr),
                         ("Efe", "Solmaz", "efe@example.com", ""))
        self.assertTrue(u.check_password("Sifre1234"))
        self.assertTrue(hasattr(u, "mysettings"))
        self.assertFalse(hasattr(u, "level"))

    def test_hata_olunca_yazilanlar_kalir(self):
        cevap = self.client.post(reverse("register"), {**self.VERI, "password": "kisa"})
        self.assertEqual(cevap.status_code, 400)
        html = cevap.content.decode()
        self.assertIn('value="Efe"', html)
        self.assertIn('value="efes"', html)
        self.assertIn("en az 8 karakter", html)
        self.assertNotIn("kisa", html)
        self.assertFalse(User.objects.filter(username="efes").exists())

    def test_ad_soyad_zorunlu_ve_kullanici_adi_tekil(self):
        self.assertEqual(self.client.post(reverse("register"), {**self.VERI, "last_name": ""}).status_code, 400)
        User.objects.create_user(username="EFES", password="Sifre1234")
        self.assertEqual(self.client.post(reverse("register"), self.VERI).status_code, 400)


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


class ConfusedWithTests(TestCase):
    """affect/effect, sensible/sensitive: eş anlamlı değil, karıştırılan."""

    def test_confusable_is_its_own_relation_type(self):
        a = make_word("sensible", pos="adjective", meaning="mantıklı")
        b = make_word("sensitive", pos="adjective", meaning="duyarlı")
        WordRelation.objects.create(from_word=a, to_word=b, type="confused_with",
                                    note="Aynı kökten, zıt yönlere.")
        self.assertEqual(a.confusables.count(), 1)
        self.assertEqual(a.synonyms.count(), 0)


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


    def test_expression_text_is_unique(self):
        Expression.objects.create(text="in the long run", meaning_tr="uzun vadede")
        with self.assertRaises(IntegrityError):
            Expression.objects.create(text="in the long run", meaning_tr="başka")


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


    # (Eski Kelimelerim listesindeki kalem simgesi testleri kaldırıldı: sayfa
    #  artık Sözlük › Listem'e yönlendiriyor, Listem'de düzenleme simgesi yok.)


class AramaTests(TestCase):
    """25 Eylül: canlı arama, filtre paneli, bağımsız sonuçlar, öneriler."""

    def setUp(self):
        make_word("perceive", pos="verb", meaning="algılamak", family="perceive", level="B1")
        make_word("perception", meaning="algı", family="perceive", level="B2")
        make_word("perceptive", pos="adjective", meaning="sezgili", family="perceive", level="C1")
        make_word("vast", pos="adjective", meaning="engin", family="vast", level="B2")
        self.user = User.objects.create_user(username="arayan", password="Sifre1234")


    def test_listeme_ekle_ajax_sayfa_yenilemez(self):
        self.client.force_login(self.user)
        w = Word.objects.get(text="vast")
        r = self.client.get(reverse("add_to_my_list", args=[w.id]), HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["kayitli"])
        r = self.client.get(reverse("remove_from_my_list", args=[w.id]), HTTP_X_REQUESTED_WITH="fetch")
        self.assertFalse(r.json()["kayitli"])


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


    def test_ifade_listesi_ajax(self):
        from words.models import UserExpressionLink
        e = self._ifade("however")
        self.client.login(username="ifadeci", password="Sifre1234")
        d = self.client.get(reverse("add_expression_to_my_list", args=[e.id]),
                            HTTP_X_REQUESTED_WITH="fetch").json()
        self.assertTrue(d["kayitli"])
        self.assertEqual(UserExpressionLink.objects.filter(user=self.user).count(), 1)
        self.assertEqual(UserWordLink.objects.filter(user=self.user).count(), 0)   # kelime listesi ayrı
        self.client.get(reverse("remove_expression_from_my_list", args=[e.id]), HTTP_X_REQUESTED_WITH="fetch")
        self.assertFalse(UserExpressionLink.objects.filter(user=self.user).exists())


    def test_giris_yapmadan_eklenemez(self):
        e = self._ifade("however")
        r = self.client.get(reverse("add_expression_to_my_list", args=[e.id]))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r.url)
