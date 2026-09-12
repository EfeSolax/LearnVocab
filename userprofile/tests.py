"""
Kelime ekleme / düzenleme formları için testler.

Özellikle collocation (kullanım kalıpları) alanının form -> view -> model
zincirinin tamamında çalıştığını doğrular. Bu alan Alpine.js ile birden çok
input olarak gönderilip view'da virgülle birleştiriliyor; zincirin bir halkası
kopsa sayfa yine 200 döner ama veri sessizce kaybolurdu.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse

from users.models import User
from words.models import Meaning, Word
from userprofile.views import _satirlari_coz
from words.models import UserWordLink
from words.models import WordList
from words.testing import make_word


class WordFormTests(TestCase):
    """
    Kelime ekleme/düzenleme formu — yeni modele göre.

    Eskiden form tek bir Word satırına yazıyordu; artık aile, anlam,
    örnek cümle ve bağlar ayrı kayıtlar. Test bunların hepsinin gerçekten
    oluştuğunu doğruluyor.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="formuser", password="Sifre1234")
        self.client.login(username="formuser", password="Sifre1234")

    def _payload(self, **overrides):
        data = {
            "text": "retain",
            "pos": "verb",
            "family_root": "retain",
            "meaning_1": "elde tutmak",
            "definition_1": "to keep something",
            "sentence_1_1": "They retain full control.",
            "sentence_1_2": "The soil retains water.",
            "note": "sınavda çok çıkıyor",
            "visibility": "private",
            "level": "Belirtilmemiş",
        }
        data.update(overrides)
        return data

    def _retain(self):
        return Word.objects.get(text="retain", pos="verb")

    # --- ekleme ---

    def test_add_page_renders_the_new_fields(self):
        response = self.client.get(reverse("add_word"))
        self.assertEqual(response.status_code, 200)
        for alan in ('name="text"', 'name="pos"', 'name="family_root"',
                     'name="meaning_1"', 'name="simpler"', 'name="note"'):
            with self.subTest(alan=alan):
                self.assertContains(response, alan)

    def test_add_page_renders_five_sentence_fields(self):
        response = self.client.get(reverse("add_word"))
        for i in range(1, Meaning.EXAMPLE_SENTENCE_COUNT + 1):
            with self.subTest(i=i):
                self.assertContains(response, f'name="sentence_1_{i}"')
        self.assertNotContains(response, 'name="sentence_1_6"')

    def test_word_is_created_with_its_family(self):
        self.client.post(reverse("add_word"), self._payload())
        kelime = self._retain()
        self.assertEqual(kelime.family.root, "retain")
        self.assertEqual(kelime.pos, "verb")

    def test_meaning_and_definition_become_a_meaning_row(self):
        self.client.post(reverse("add_word"), self._payload())
        anlam = self._retain().primary_meaning
        self.assertEqual(anlam.meaning_tr, "elde tutmak")
        self.assertEqual(anlam.definition, "to keep something")

    def test_sentences_become_rows_in_order(self):
        self.client.post(reverse("add_word"), self._payload())
        self.assertEqual(
            self._retain().example_sentences,
            ["They retain full control.", "The soil retains water."],
        )

    def test_blank_sentences_are_simply_not_created(self):
        self.client.post(reverse("add_word"), self._payload(sentence_1_2=""))
        self.assertEqual(len(self._retain().example_sentences), 1)

    def test_second_meaning_is_optional_and_kept(self):
        self.client.post(reverse("add_word"), self._payload(
            meaning_2="akılda tutmak", definition_2="to remember",
        ))
        anlamlar = list(self._retain().meanings.all())
        self.assertEqual(len(anlamlar), 2)
        self.assertEqual(anlamlar[1].meaning_tr, "akılda tutmak")

    def test_inflected_forms_are_generated(self):
        """Çekim biçimleri elle girilmez, kelimeden üretilir."""
        self.client.post(reverse("add_word"), self._payload())
        yuzeyler = set(self._retain().forms.values_list("surface", flat=True))
        self.assertTrue({"retains", "retaining", "retained"} <= yuzeyler)

    def test_irregular_verb_forms_come_from_the_form(self):
        self.client.post(reverse("add_word"), self._payload(
            text="go", family_root="go", meaning_1="gitmek", v2="went", v3="gone",
            sentence_1_1="They go home.",
        ))
        kelime = Word.objects.get(text="go", pos="verb")
        yuzeyler = set(kelime.forms.values_list("surface", flat=True))
        self.assertIn("went", yuzeyler)
        self.assertIn("gone", yuzeyler)

    def test_personal_note_goes_to_the_user_layer_not_the_word(self):
        """
        Eskiden 'not' paylaşılan Word satırının üstünde bir alandı; yani
        kişisel değildi. Artık kullanıcıya ait ayrı bir kayıt.
        """
        self.client.post(reverse("add_word"), self._payload())
        kelime = self._retain()
        self.assertFalse(hasattr(kelime, "note"))
        self.assertEqual(kelime.note_of(self.user).note, "sınavda çok çıkıyor")

    def test_another_user_does_not_see_that_note(self):
        self.client.post(reverse("add_word"), self._payload())
        baskasi = User.objects.create_user(username="digeri", password="Sifre1234")
        self.assertIsNone(self._retain().note_of(baskasi))

    def test_same_word_different_pos_is_allowed(self):
        """progress (isim) ve progress (fiil) ayrı kayıtlardır."""
        self.client.post(reverse("add_word"), self._payload(
            text="progress", family_root="progress", pos="noun",
            meaning_1="ilerleme", sentence_1_1="She made progress."))
        self.client.post(reverse("add_word"), self._payload(
            text="progress", family_root="progress", pos="verb",
            meaning_1="ilerlemek", sentence_1_1="The work progressed."))
        self.assertEqual(Word.objects.filter(text="progress").count(), 2)

    def test_same_word_same_pos_is_refused(self):
        self.client.post(reverse("add_word"), self._payload())
        self.client.post(reverse("add_word"), self._payload())
        self.assertEqual(Word.objects.filter(text="retain", pos="verb").count(), 1)

    def test_word_without_a_meaning_is_refused(self):
        self.client.post(reverse("add_word"), self._payload(meaning_1=""))
        self.assertFalse(Word.objects.filter(text="retain").exists())

    # --- bağlar ---

    def test_relations_are_created_for_existing_words(self):
        make_word("keep", pos="verb", meaning="tutmak")
        self.client.post(reverse("add_word"), self._payload(simpler="keep"))

        bag = self._retain().simpler_words.first()
        self.assertIsNotNone(bag)
        self.assertEqual(bag.to_word.text, "keep")

    def test_unknown_relation_targets_are_reported_not_dropped_silently(self):
        cevap = self.client.post(reverse("add_word"),
                                 self._payload(synonyms="boylebirkelimeyok"), follow=True)
        self.assertContains(cevap, "boylebirkelimeyok")
        self.assertEqual(self._retain().synonyms.count(), 0)

    # --- düzenleme ---

    def test_edit_page_prefills_every_field(self):
        self.client.post(reverse("add_word"), self._payload())
        cevap = self.client.get(reverse("edit_word", args=[self._retain().id]))
        html = cevap.content.decode()
        self.assertIn('value="retain"', html)
        self.assertIn("elde tutmak", html)
        self.assertIn("They retain full control.", html)
        self.assertIn("sınavda çok çıkıyor", html)

    def test_edit_replaces_meanings_and_sentences(self):
        self.client.post(reverse("add_word"), self._payload())
        kelime = self._retain()
        self.client.post(reverse("edit_word", args=[kelime.id]), self._payload(
            meaning_1="muhafaza etmek", sentence_1_1="They retained it.", sentence_1_2="",
        ))
        kelime.refresh_from_db()
        self.assertEqual(kelime.meaningTr, "muhafaza etmek")
        self.assertEqual(kelime.example_sentences, ["They retained it."])

    def test_base_words_cannot_be_edited_by_ordinary_users(self):
        kur_kelimesi = make_word("inherent", is_base=True)
        cevap = self.client.post(reverse("edit_word", args=[kur_kelimesi.id]),
                                 self._payload(text="degistirildi"))
        kur_kelimesi.refresh_from_db()
        self.assertEqual(kur_kelimesi.text, "inherent")
        self.assertEqual(cevap.status_code, 302)


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
            word = make_word(name, owner=self.user, is_base=False)
            link = UserWordLink.objects.create(user=self.user, word=word)
            UserWordLink.objects.filter(pk=link.pk).update(
                dateAdded=timezone.now() - timedelta(days=10 - offset * 5)
            )
            self.words[name] = word

    def _listed(self, **params):
        response = self.client.get(reverse("profile_words"), params)
        self.assertEqual(response.status_code, 200)
        return [w.text for w in response.context["page_obj"].object_list]

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
        orphan = make_word("orphan", owner=self.user, is_base=False)
        Word.objects.filter(pk=orphan.pk).update(
            createdAt=timezone.now() - timedelta(days=100)
        )
        self.assertEqual(self._listed(sort="old")[0], "orphan")

class KurTopluIslemTests(TestCase):
    """
    CEFR seviyesine göre toplu ekleme/çıkarma.

    Eski sürümde bu uçlar Word.span ve ODTÜ kuruna göre filtreliyordu; ikisi
    de yeni modelde yok. Testler bir seviyenin tamamını ekleyip
    çıkarabildiğimizi ve eski kur kodunun artık geçmediğini sabitliyor.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="kur_kullanici", password="Sifre1234")
        self.client.login(username="kur_kullanici", password="Sifre1234")

        self.b2 = make_word("obtain", pos="verb", meaning="elde etmek", level="B2", is_base=True)
        self.c1 = make_word("ubiquitous", pos="adjective", meaning="her yerde olan",
                            level="C1", is_base=True)

    def _listemdeki(self):
        return set(
            UserWordLink.objects.filter(user=self.user).values_list("word__text", flat=True)
        )

    def test_bir_seviyenin_tamami_eklenir(self):
        self.client.post(reverse("add_all_words"), {"bulk_level": "B2"})
        self.assertEqual(self._listemdeki(), {"obtain"})

    def test_ayni_seviye_iki_kez_eklenince_cift_bag_olusmaz(self):
        self.client.post(reverse("add_all_words"), {"bulk_level": "B2"})
        self.client.post(reverse("add_all_words"), {"bulk_level": "B2"})
        self.assertEqual(UserWordLink.objects.filter(user=self.user).count(), 1)

    def test_seviye_listeden_cikarilir(self):
        self.client.post(reverse("add_all_words"), {"bulk_level": "B2"})
        self.client.post(reverse("add_all_words"), {"bulk_level": "C1"})
        self.client.post(reverse("delete_all_words"), {"bulk_level": "B2"})
        self.assertEqual(self._listemdeki(), {"ubiquitous"})

    def test_gecersiz_seviye_hicbir_sey_yapmaz(self):
        cevap = self.client.post(reverse("add_all_words"), {"bulk_level": "401"})
        self.assertEqual(cevap.status_code, 302)
        self.assertEqual(self._listemdeki(), set())

    def test_seviye_secilmeden_gonderilirse_hata_verir(self):
        cevap = self.client.post(reverse("add_all_words"), {})
        self.assertEqual(cevap.status_code, 302)
        self.assertEqual(self._listemdeki(), set())


class KelimelerimSayfaAraclariTests(TestCase):
    """
    Kelimelerim sayfasının toplu işlem araçları şablonda yaşıyor.

    Bu testler araçların yanlışlıkla düşürülmesini yakalıyor: sayfa bir kez
    bu formları kaybettiğinde arkadaki uçlar çalışsa bile kullanıcı onlara
    ulaşamıyor.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="arac_kullanici", password="Sifre1234")
        self.client.login(username="arac_kullanici", password="Sifre1234")
        self.word = make_word("obtain", pos="verb", meaning="elde etmek", owner=self.user)
        UserWordLink.objects.create(user=self.user, word=self.word)

    def _govde(self):
        cevap = self.client.get(reverse("profile_words"))
        self.assertEqual(cevap.status_code, 200)
        return cevap.content.decode()

    def test_sayfa_liste_olusturma_formunu_tasiyor(self):
        self.assertIn(reverse("wordlist_create"), self._govde())

    def test_sayfa_kur_ekle_ve_cikar_formlarini_tasiyor(self):
        govde = self._govde()
        self.assertIn(reverse("add_all_words"), govde)
        self.assertIn(reverse("delete_all_words"), govde)
        self.assertIn('name="bulk_level"', govde)
        self.assertIn('value="B2"', govde)   # seviyeler CEFR

    def test_sayfa_toplu_silme_formunu_tasiyor(self):
        self.assertIn(reverse("delete_selected_words"), self._govde())

    def test_secili_liste_icin_ad_degistir_ve_sil_gorunur(self):
        liste = WordList.objects.create(owner=self.user, name="Sınav")
        liste.words.add(self.word)   # seçim çubuğu ancak listede kelime varken çıkar
        cevap = self.client.get(reverse("profile_words"), {"list_id": liste.id})
        govde = cevap.content.decode()
        self.assertIn(reverse("wordlist_rename", kwargs={"list_id": liste.id}), govde)
        self.assertIn(reverse("wordlist_delete", kwargs={"list_id": liste.id}), govde)
        self.assertIn(reverse("wordlist_remove_words", kwargs={"list_id": liste.id}), govde)

    def test_liste_yokken_ad_degistirme_formu_cikmiyor(self):
        self.assertNotIn("wordlist_rename", self._govde())

class AlanAyiriciTests(TestCase):
    """
    Çok satırlı form alanlarında ayırıcı: boşluklu eğik çizgi (" / ").

    Düz "/" kullanılamaz, çünkü yapının KENDİSİNDE slash geçiyor:
    `harmful to sb/sth`, `sympathetic to/towards sb`. Bitişik çizgi yapının
    parçası, boşluklu çizgi ayırıcı. Bu ayrım bozulursa o kalıplar ikiye
    bölünür ve kullanıcı neden bozulduğunu anlamaz.
    """

    def test_a_spaced_slash_splits_the_line(self):
        self.assertEqual(
            _satirlari_coz("make a decision / karar vermek", 2),
            [["make a decision", "karar vermek"]],
        )

    def test_a_slash_inside_the_phrase_is_left_alone(self):
        self.assertEqual(
            _satirlari_coz("harmful to sb/sth", 2),
            [["harmful to sb/sth", ""]],
        )

    def test_both_kinds_of_slash_can_appear_on_one_line(self):
        self.assertEqual(
            _satirlari_coz("sympathetic to/towards sb / to ya da towards + kişi", 2),
            [["sympathetic to/towards sb", "to ya da towards + kişi"]],
        )

    def test_the_pipe_is_no_longer_a_separator(self):
        """Telefon klavyesinde zor bulunduğu için bırakıldı; artık düz metin."""
        self.assertEqual(
            _satirlari_coz("make a decision | karar vermek", 2),
            [["make a decision | karar vermek", ""]],
        )

    def test_three_fields_work_the_same_way(self):
        self.assertEqual(
            _satirlari_coz("sempatik / cana yakın / likeable, friendly", 3),
            [["sempatik", "cana yakın", "likeable, friendly"]],
        )

    def test_blank_lines_are_dropped(self):
        self.assertEqual(
            _satirlari_coz("a / b\n\n  \nc / d", 2),
            [["a", "b"], ["c", "d"]],
        )

    def test_repeats_in_the_unique_column_are_dropped(self):
        self.assertEqual(
            _satirlari_coz("make a decision / bir\nMAKE A DECISION / iki", 2),
            [["make a decision", "bir"]],
        )


class SlashSeparatorRoundTripTests(TestCase):
    """
    Formdan kaydedilen satır, düzenleme formuna aynı şekilde geri gelmeli.

    Gidiş " / " ile ayrılıp dönüş "|" ile birleştirilseydi kullanıcı kaydettiği
    şeyi bir daha kaydedemezdi — sessizce tek alana düşerdi.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="slashci", password="Sifre1234")
        self.client.login(username="slashci", password="Sifre1234")

    def _kaydet(self, **ek):
        veri = {
            "text": "harm", "pos": "noun", "family_root": "harm",
            "meaning_1": "zarar", "sentence_1_1": "It caused great harm.",
            "visibility": "private", "level": "B2",
        }
        veri.update(ek)
        self.client.post(reverse("add_word"), veri)
        return Word.objects.get(text="harm", pos="noun")

    def test_a_collocation_survives_save_and_reload(self):
        kelime = self._kaydet(collocations_1="cause harm / zarar vermek")
        yapi = kelime.collocations.get()
        self.assertEqual(yapi.pattern, "cause harm")
        self.assertEqual(yapi.meaning_tr, "zarar vermek")

        html = self.client.get(reverse("edit_word", args=[kelime.id])).content.decode()
        self.assertIn("cause harm / zarar vermek", html)

    def test_a_pattern_keeps_its_inner_slash(self):
        kelime = self._kaydet(patterns_1="harmful to sb/sth / to + isim")
        kalip = kelime.patterns.get()
        self.assertEqual(kalip.pattern, "harmful to sb/sth")
        self.assertEqual(kalip.note, "to + isim")

        html = self.client.get(reverse("edit_word", args=[kelime.id])).content.decode()
        self.assertIn("harmful to sb/sth / to + isim", html)

    def test_a_false_friend_round_trips_with_three_fields(self):
        kelime = self._kaydet(false_friends="harem / zararlı / harmful")
        yanlis = kelime.false_friends.get()
        self.assertEqual(
            (yanlis.turkish_lookalike, yanlis.assumed_meaning, yanlis.correct_english),
            ("harem", "zararlı", "harmful"),
        )

        html = self.client.get(reverse("edit_word", args=[kelime.id])).content.decode()
        self.assertIn("harem / zararlı / harmful", html)


class FormHelpTextTests(TestCase):
    """Formdaki açıklama metni gerçekten geçerli olan ayırıcıyı anlatmalı."""

    def setUp(self):
        self.user = User.objects.create_user(username="yardim", password="Sifre1234")
        self.client.login(username="yardim", password="Sifre1234")

    def test_the_form_shows_the_slash_not_the_pipe(self):
        html = self.client.get(reverse("add_word")).content.decode()
        self.assertIn("make a decision / karar vermek", html)
        self.assertIn("sempatik / cana yakın, hoş / likeable, friendly", html)
        self.assertNotIn("make a decision | karar vermek", html)
        self.assertNotIn("benzeyen Türkçe | sanılan anlam", html)
