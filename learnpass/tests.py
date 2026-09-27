"""
Öğren-Geç testleri.

En çok korunması gereken kural: kullanıcı kararını ANLAMI GÖRMEDEN veriyor.
Kartın ilk hâlinde anlam sunucudan gelse bile ekranda kapalı duruyor; bu
yüzden burada hem veri akışı hem de sınıflandırmanın sonuçları test ediliyor.
"""

import json
import random

from django.test import TestCase
from django.urls import reverse

from users.models import User
from words.models import UserWordLink, Word

from learnpass import selection
from learnpass.models import Declaration, EncounterLog, WordEncounter


def kelime_yap(englishWord="immaculate", **kwargs):
    """Yeni modelde kelime kurar (bkz. words/testing.py)."""
    from words.testing import make_word

    kwargs.setdefault("meaning", "tertemiz")
    kwargs.setdefault("sentences", [f"Her kitchen was {englishWord}."])
    return make_word(englishWord, **kwargs)


class WordEncounterModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="ogrenci", password="Sifre1234")
        self.word = kelime_yap()

    def test_unknown_verdict_does_not_mark_learned(self):
        kayit = WordEncounter.record(self.user, self.word, WordEncounter.UNKNOWN, "new")
        self.assertFalse(kayit.is_learned)
        self.assertEqual(kayit.times_seen, 1)

    def test_confirmed_known_marks_learned(self):
        kayit = WordEncounter.record(self.user, self.word, WordEncounter.KNOWN, "mine")
        self.assertTrue(kayit.is_learned)

    def test_misjudged_is_counted_and_clears_learned(self):
        """Bir kez 'biliyorum' demiş olmak kelimeyi sonsuza kadar gizlememeli."""
        WordEncounter.record(self.user, self.word, WordEncounter.KNOWN, "mine")
        kayit = WordEncounter.record(self.user, self.word, WordEncounter.MISJUDGED, "mine")
        self.assertFalse(kayit.is_learned)
        self.assertEqual(kayit.misjudged_count, 1)
        self.assertTrue(kayit.was_misjudged)

    def test_one_row_per_user_and_word(self):
        WordEncounter.record(self.user, self.word, WordEncounter.UNKNOWN, "new")
        WordEncounter.record(self.user, self.word, WordEncounter.UNKNOWN, "new")
        self.assertEqual(WordEncounter.objects.filter(user=self.user, word=self.word).count(), 1)
        self.assertEqual(WordEncounter.objects.get(user=self.user, word=self.word).times_seen, 2)


class SelectionTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="secim", password="Sifre1234")

    def test_new_mode_skips_words_already_in_the_list(self):
        listemde = kelime_yap("alreadyhere")
        UserWordLink.objects.create(user=self.user, word=listemde)
        disarida = kelime_yap("fresh")

        havuz = list(selection.new_words_qs(self.user))
        self.assertIn(disarida, havuz)
        self.assertNotIn(listemde, havuz)

    def test_new_mode_skips_words_already_seen(self):
        kelime = kelime_yap("seenbefore")
        WordEncounter.record(self.user, kelime, WordEncounter.KNOWN, "new")
        self.assertNotIn(kelime, selection.new_words_qs(self.user))

    def test_new_mode_ignores_private_words_of_other_users(self):
        baskasi = User.objects.create_user(username="baska", password="Sifre1234")
        gizli = kelime_yap("secret", is_base=False,
                           visibility="private", owner=baskasi)
        self.assertNotIn(gizli, selection.new_words_qs(self.user))

    def test_own_mode_skips_learned_words(self):
        ogrenildi = kelime_yap("mastered")
        kalan = kelime_yap("stillhard")
        UserWordLink.objects.create(user=self.user, word=ogrenildi)
        UserWordLink.objects.create(user=self.user, word=kalan)
        WordEncounter.record(self.user, ogrenildi, WordEncounter.KNOWN, "mine")

        havuz = list(selection.own_words_qs(self.user))
        self.assertIn(kalan, havuz)
        self.assertNotIn(ogrenildi, havuz)

    def test_own_mode_prefers_the_word_user_struggles_with(self):
        """
        Sıra artık "en uzun süredir görülmeyen" değil, EN ÇOK ZORLANILAN.

        Eski davranış Öğren-Geç'i bir liste gezme aracına çeviriyordu.
        Bölümün işi ölçüm: "kullanıcı bu kelimeyi bildiğini düşünüyor mu"
        sorusunu iyi bildiği kelimede sormanın bilgi değeri yok.
        """
        kolay = kelime_yap("easyone")
        zor = kelime_yap("hardone")
        for kelime in (kolay, zor):
            UserWordLink.objects.create(user=self.user, word=kelime)

        # Kolay kelime: üç kez görüldü, üçünde de bilindi ama "öğrendim"
        # denmediği için havuzda; zor kelime: üç kez görüldü, üçünde de yanıldı.
        for _ in range(3):
            WordEncounter.record(self.user, zor, WordEncounter.MISJUDGED, "mine")
        for _ in range(3):
            WordEncounter.record(self.user, kolay, WordEncounter.UNKNOWN, "mine")
        # kolay'ın oranını düşür: çok sayıda doğru karşılaşma ekle
        for _ in range(12):
            WordEncounter.record(self.user, kolay, WordEncounter.KNOWN, "mine")
        WordEncounter.objects.filter(user=self.user, word=kolay).update(is_learned=False)

        puanlar = selection.struggle_scores(self.user)
        self.assertGreater(puanlar[zor.id], puanlar[kolay.id])

    def test_stuck_declaration_outranks_everything(self):
        """
        "Hâlâ öğrenemedim" beyanı diğer bütün sinyallerin önüne geçmeli:
        bu bilgi başka hiçbir yerden gelmiyor.
        """
        beyanli = kelime_yap("declaredstuck")
        cok_yanlis = kelime_yap("manymisses")
        for kelime in (beyanli, cok_yanlis):
            UserWordLink.objects.create(user=self.user, word=kelime)

        for _ in range(10):
            WordEncounter.record(self.user, cok_yanlis, WordEncounter.MISJUDGED, "mine")
        for _ in range(3):
            WordEncounter.record(self.user, beyanli, WordEncounter.UNKNOWN, "mine")
        WordEncounter.objects.get(user=self.user, word=beyanli).declare(Declaration.STUCK)

        puanlar = selection.struggle_scores(self.user)
        self.assertGreater(puanlar[beyanli.id], puanlar[cok_yanlis.id])

    def test_words_with_no_data_sit_in_the_middle(self):
        """
        Hiç verisi olmayan kelime ne en önde ne en arkada olmalı:
        önde olsa gerçekten zorlandıkları geri düşer, arkada olsa
        kullanıcı o kelimeyle hiç karşılaşmaz.
        """
        bos = kelime_yap("nodata")
        zor = kelime_yap("struggling")
        kolay = kelime_yap("wellknown")
        for kelime in (bos, zor, kolay):
            UserWordLink.objects.create(user=self.user, word=kelime)

        for _ in range(4):
            WordEncounter.record(self.user, zor, WordEncounter.UNKNOWN, "mine")
        for _ in range(4):
            WordEncounter.record(self.user, kolay, WordEncounter.KNOWN, "mine")
        WordEncounter.objects.filter(user=self.user, word=kolay).update(is_learned=False)

        puanlar = selection.struggle_scores(self.user)
        bos_puan = puanlar.get(bos.id, selection.NOTR_PUAN)
        self.assertGreater(puanlar[zor.id], bos_puan)
        self.assertGreater(bos_puan, puanlar.get(kolay.id, 0.0))

    def test_empty_pool_returns_none(self):
        self.assertIsNone(selection.pick_own_word(self.user))
        self.assertIsNone(selection.pick_new_word(self.user))


class LevelWeightTests(TestCase):
    """Kur dağılımı: 401 %40, 301 %25, 501 %25, 101 %5, 201 %5."""

    def setUp(self):
        self.user = User.objects.create_user(username="dagilim", password="Sifre1234")
        for seviye in ("A1", "A2", "B1", "B2", "C1"):
            for i in range(40):
                kelime_yap(f"w{seviye}_{i}", level=seviye)

    def test_weights_sum_to_one_hundred(self):
        self.assertEqual(sum(agirlik for _, agirlik in selection.LEVEL_WEIGHTS), 100)

    def test_distribution_roughly_matches_the_weights(self):
        rng = random.Random(20260911)
        sayac = {seviye: 0 for seviye, _ in selection.LEVEL_WEIGHTS}
        tur = 600
        for _ in range(tur):
            kelime = selection.pick_new_word(self.user, rng=rng)
            sayac[kelime.cefr] += 1

        for seviye, agirlik in selection.LEVEL_WEIGHTS:
            oran = sayac[seviye] / tur * 100
            # Rastgelelik payı: 600 çekimde ±8 puan makul
            self.assertAlmostEqual(
                oran, agirlik, delta=8,
                msg=f"{seviye} seviyesi %{oran:.1f} çıktı, beklenen %{agirlik}")

    def test_falls_back_to_another_level_when_one_is_empty(self):
        """Seçilen seviyede kelime kalmadıysa kart gelmeye devam etmeli."""
        Word.objects.exclude(cefr="A1").delete()
        kelime = selection.pick_new_word(self.user)
        self.assertIsNotNone(kelime)
        self.assertEqual(kelime.cefr, "A1")


class LearnPassFlowTests(TestCase):
    """Uçtan uca akış: karar -> kayıt -> listeye ekleme -> sonraki kart."""

    def setUp(self):
        self.user = User.objects.create_user(username="akis", password="Sifre1234")
        self.client.login(username="akis", password="Sifre1234")
        self.word = kelime_yap("candidate")
        self.other = kelime_yap("another")

    def _verdict(self, word, verdict, mode="new"):
        return self.client.post(
            reverse("learn_pass_verdict"),
            data=json.dumps({"word_id": word.id, "verdict": verdict, "mode": mode}),
            content_type="application/json",
        )

    def test_unknown_adds_the_word_to_the_list(self):
        cevap = self._verdict(self.word, "unknown")
        self.assertEqual(cevap.status_code, 200)
        self.assertTrue(UserWordLink.objects.filter(user=self.user, word=self.word).exists())
        self.assertEqual(cevap.json()["stats"]["added"], 1)

    def test_confirmed_known_does_not_add_the_word(self):
        self._verdict(self.word, "known")
        self.assertFalse(UserWordLink.objects.filter(user=self.user, word=self.word).exists())

    def test_misjudged_adds_the_word_and_is_counted(self):
        cevap = self._verdict(self.word, "misjudged")
        self.assertTrue(UserWordLink.objects.filter(user=self.user, word=self.word).exists())
        self.assertEqual(cevap.json()["stats"]["misjudged"], 1)

    def test_response_carries_the_next_card(self):
        kart = self._verdict(self.word, "unknown").json()["card"]
        self.assertIsNotNone(kart)
        self.assertEqual(kart["id"], self.other.id)

    def test_pool_exhaustion_returns_no_card(self):
        self._verdict(self.word, "known")
        kart = self._verdict(self.other, "known").json()["card"]
        self.assertIsNone(kart)

    def test_invalid_verdict_is_rejected(self):
        self.assertEqual(self._verdict(self.word, "kesinlikle").status_code, 400)

    def test_undo_reverts_the_record_and_the_list(self):
        self._verdict(self.word, "unknown")
        cevap = self.client.post(
            reverse("learn_pass_undo"),
            data=json.dumps({"mode": "new"}),
            content_type="application/json",
        )
        self.assertEqual(cevap.status_code, 200)
        self.assertFalse(WordEncounter.objects.filter(user=self.user, word=self.word).exists())
        self.assertFalse(UserWordLink.objects.filter(user=self.user, word=self.word).exists())
        self.assertEqual(cevap.json()["card"]["id"], self.word.id)
        self.assertEqual(cevap.json()["stats"]["seen"], 0)

    def test_undo_restores_the_previous_verdict_instead_of_deleting(self):
        """Kelime daha önce görülmüşse geri al onu silmemeli, eski hâline döndürmeli."""
        WordEncounter.record(self.user, self.word, WordEncounter.UNKNOWN, "new")
        self._verdict(self.word, "known")
        self.client.post(reverse("learn_pass_undo"),
                         data=json.dumps({"mode": "new"}), content_type="application/json")

        kayit = WordEncounter.objects.get(user=self.user, word=self.word)
        self.assertEqual(kayit.last_verdict, WordEncounter.UNKNOWN)
        self.assertFalse(kayit.is_learned)

    def test_undo_without_history_is_rejected(self):
        cevap = self.client.post(reverse("learn_pass_undo"),
                                 data=json.dumps({"mode": "new"}),
                                 content_type="application/json")
        self.assertEqual(cevap.status_code, 400)

    def test_undo_does_not_remove_a_word_that_was_already_in_the_list(self):
        UserWordLink.objects.create(user=self.user, word=self.word)
        self._verdict(self.word, "unknown", mode="mine")
        self.client.post(reverse("learn_pass_undo"),
                         data=json.dumps({"mode": "mine"}), content_type="application/json")
        self.assertTrue(UserWordLink.objects.filter(user=self.user, word=self.word).exists())


class LearnPassPageTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="sayfa", password="Sifre1234")
        self.word = kelime_yap()

    def test_mode_picker_requires_login_but_does_not_redirect(self):
        cevap = self.client.get(reverse("learn_pass_page"))
        self.assertEqual(cevap.status_code, 200)
        self.assertIn("önce giriş yapın", cevap.content.decode())

    def test_mode_picker_lists_both_modes(self):
        self.client.login(username="sayfa", password="Sifre1234")
        html = self.client.get(reverse("learn_pass_page")).content.decode()
        self.assertIn("Kendi Kelimelerim", html)
        self.assertIn("Yeni Kelimeler", html)

    def test_unknown_mode_falls_back_to_the_picker(self):
        self.client.login(username="sayfa", password="Sifre1234")
        cevap = self.client.get(reverse("learn_pass_run", kwargs={"mode": "sacma"}))
        self.assertRedirects(cevap, reverse("learn_pass_page"))

    def test_card_screen_hides_the_meaning_until_a_decision_is_made(self):
        """
        Anlam sunucudan geliyor ama ekranda kapalı: açan blok 'hidden'.
        Bu testin amacı o sınıfın yanlışlıkla kaldırılmasını yakalamak.
        """
        self.client.login(username="sayfa", password="Sifre1234")
        html = self.client.get(reverse("learn_pass_run", kwargs={"mode": "new"})).content.decode()
        self.assertIn('id="card-reveal" class="hidden', html)
        self.assertIn("Aklındaki bu muydu?", html)
        self.assertIn("Bilmiyorum", html)

    def test_exercise_tabs_appear_on_both_pages(self):
        self.client.login(username="sayfa", password="Sifre1234")
        for url in (reverse("learn_pass_page"), reverse("profile_quizzes")):
            with self.subTest(url=url):
                html = self.client.get(url, follow=True).content.decode()
                self.assertIn("Öğren-Geç", html)
                # Sekmenin adı "Quizler" değil "Çalışma": bölüm artık quiz
                # üretmiyor, aralıklı tekrar yürütüyor.
                self.assertIn("Çalışma", html)

    def test_exercises_menu_opens_learn_pass_first(self):
        self.client.login(username="sayfa", password="Sifre1234")
        html = self.client.get(reverse("index")).content.decode()
        basla = html.index('<header id="navbar"')
        navbar = html[basla:html.index("</header>", basla)]
        self.assertIn(reverse("learn_pass_page"), navbar)


class QuizPriorityIntegrationTests(TestCase):
    """Öğren-Geç sinyalleri quiz sırasını değiştiriyor mu?"""

    def setUp(self):
        self.user = User.objects.create_user(username="oncelik", password="Sifre1234")

    def _link(self, word, correct, wrong):
        return UserWordLink.objects.create(user=self.user, word=word,
                                           correctCount=correct, wrongCount=wrong)

    def test_misjudged_word_jumps_to_the_first_priority(self):
        from quizzes.views import classify_links_by_priority, encounter_signals

        kelime = kelime_yap("thoughtiknew")
        # Quiz istatistiklerine göre bu kelime "iyi biliniyor" sayılırdı
        link = self._link(kelime, correct=20, wrong=0)
        WordEncounter.record(self.user, kelime, WordEncounter.MISJUDGED, "mine")

        misjudged, learned = encounter_signals(self.user)
        p1, p2, p3 = classify_links_by_priority([link], misjudged, learned)
        self.assertIn(link, p1)

    def test_learned_word_drops_to_the_last_priority(self):
        from quizzes.views import classify_links_by_priority, encounter_signals

        kelime = kelime_yap("reallyknown")
        # Hiç denenmemiş: normalde priority1 olurdu
        link = self._link(kelime, correct=0, wrong=0)
        WordEncounter.record(self.user, kelime, WordEncounter.KNOWN, "mine")

        misjudged, learned = encounter_signals(self.user)
        p1, p2, p3 = classify_links_by_priority([link], misjudged, learned)
        self.assertIn(link, p3)

    def test_without_signals_the_old_behaviour_is_kept(self):
        from quizzes.views import classify_links_by_priority

        link = self._link(kelime_yap("plain"), correct=0, wrong=0)
        p1, _, _ = classify_links_by_priority([link])
        self.assertIn(link, p1)


class DeclarationTests(TestCase):
    """
    Kullanıcının kendi beyanı — Öğren-Geç'in asıl ürünü.

    Karar (biliyorum/bilmiyorum) tek bir ana ait; beyan kullanıcının o
    kelimeyle kurduğu ilişkiye ait ve tekrar sayısını hesaba katıyor.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="beyan", password="Sifre1234")
        self.word = kelime_yap("stubborn")
        UserWordLink.objects.create(user=self.user, word=self.word)

    def _gor(self, kez, verdict=WordEncounter.UNKNOWN):
        for _ in range(kez):
            WordEncounter.record(self.user, self.word, verdict, "mine")
        return WordEncounter.objects.get(user=self.user, word=self.word)

    def test_beyan_esigin_altinda_sorulmaz(self):
        """"Bu kadar çok çıkmasına rağmen" ifadesi ilk karşılaşmada boştur."""
        kayit = self._gor(1)
        self.assertFalse(kayit.can_declare)
        kayit = self._gor(2)
        self.assertTrue(kayit.can_declare)

    def test_ogrendim_beyani_havuzdan_cikarir(self):
        kayit = self._gor(3)
        kayit.declare(Declaration.MASTERED)
        kayit.refresh_from_db()
        self.assertTrue(kayit.is_learned)
        self.assertNotIn(self.word, selection.own_words_qs(self.user))

    def test_ogrenemedim_beyani_havuzda_tutar_ve_one_alir(self):
        kayit = self._gor(3)
        kayit.declare(Declaration.STUCK)
        kayit.refresh_from_db()
        self.assertFalse(kayit.is_learned)
        self.assertIn(self.word, selection.own_words_qs(self.user))
        self.assertIn(self.word.id, selection.stuck_word_ids(self.user))

    def test_ogrendim_dedikten_sonra_bilemezse_beyan_duser(self):
        """Bir kez 'öğrendim' demek kelimeyi sonsuza kadar kapatmamalı."""
        kayit = self._gor(3)
        kayit.declare(Declaration.MASTERED)
        WordEncounter.record(self.user, self.word, WordEncounter.UNKNOWN, "mine")
        kayit.refresh_from_db()
        self.assertEqual(kayit.declaration, Declaration.NONE)
        self.assertFalse(kayit.is_learned)

    def test_ogrenemedim_dedikten_sonra_bilirse_beyan_duser(self):
        """Takıldığı yerden çıkmışsa eski beyanı onu zor kelime saymamalı."""
        kayit = self._gor(3)
        kayit.declare(Declaration.STUCK)
        WordEncounter.record(self.user, self.word, WordEncounter.KNOWN, "mine")
        kayit.refresh_from_db()
        self.assertEqual(kayit.declaration, Declaration.NONE)

    def test_her_karsilasma_gunluge_yaziliyor(self):
        """Geçmiş geriye dönük üretilemez; kayıt tutulmazsa o kapı kapanır."""
        self._gor(3)
        kayitlar = EncounterLog.objects.filter(user=self.user,
                                               kind=EncounterLog.VERDICT)
        self.assertEqual(kayitlar.count(), 3)
        self.assertEqual(list(kayitlar.order_by("id").values_list("seen_index", flat=True)),
                         [1, 2, 3])

    def test_beyan_da_gunluge_yaziliyor(self):
        kayit = self._gor(3)
        kayit.declare(Declaration.STUCK)
        gunluk = EncounterLog.objects.get(user=self.user,
                                          kind=EncounterLog.DECLARATION)
        self.assertEqual(gunluk.declaration, Declaration.STUCK)
        self.assertEqual(gunluk.seen_index, 3)

    def test_kacinci_karsilasmada_ogrendigini_soyledi(self):
        """İleride sorulacak asıl soru bu; alan o yüzden ayrıca tutuluyor."""
        kayit = self._gor(5, WordEncounter.KNOWN)
        kayit.declare(Declaration.MASTERED)
        kayit.refresh_from_db()
        self.assertEqual(kayit.declared_after_seen, 5)

    def test_zorlanma_orani_yanilmayi_agir_sayar(self):
        """
        Bildiğini sanıp yanılmak, düpedüz bilmemekten kötüdür.

        Karışık durumda ölçülüyor: her iki kelime de 6 kez görülmüş,
        birinde 3 kez yanılınmış, diğerinde 3 kez bilinmemiş. Hepsi
        kaçırılmış kelimelerde oran 1.0'da doyuyor ve ikisi eşit
        çıkıyor — doğrusu da bu, ikisi de azami derecede sorunlu.
        """
        kelime_b = kelime_yap("plainunknown")
        UserWordLink.objects.create(user=self.user, word=kelime_b)
        for _ in range(3):
            WordEncounter.record(self.user, self.word, WordEncounter.MISJUDGED, "mine")
            WordEncounter.record(self.user, self.word, WordEncounter.KNOWN, "mine")
            WordEncounter.record(self.user, kelime_b, WordEncounter.UNKNOWN, "mine")
            WordEncounter.record(self.user, kelime_b, WordEncounter.KNOWN, "mine")

        yanilan = WordEncounter.objects.get(user=self.user, word=self.word)
        bilmeyen = WordEncounter.objects.get(user=self.user, word=kelime_b)
        self.assertEqual(yanilan.times_seen, bilmeyen.times_seen)
        self.assertGreater(yanilan.miss_ratio, bilmeyen.miss_ratio)


class DeclarationEndpointTests(TestCase):
    """Beyan ucunun HTTP tarafı."""

    def setUp(self):
        self.user = User.objects.create_user(username="ucnokta", password="Sifre1234")
        self.word = kelime_yap("endpointword")
        UserWordLink.objects.create(user=self.user, word=self.word)
        self.client.login(username="ucnokta", password="Sifre1234")

    def _beyan(self, beyan):
        return self.client.post(
            reverse("learn_pass_declare"),
            data=json.dumps({"word_id": self.word.id, "declaration": beyan,
                             "mode": "mine"}),
            content_type="application/json",
        )

    def test_esik_altinda_reddedilir(self):
        WordEncounter.record(self.user, self.word, WordEncounter.UNKNOWN, "mine")
        self.assertEqual(self._beyan("stuck").status_code, 400)

    def test_gecerli_beyan_kaydedilir(self):
        for _ in range(3):
            WordEncounter.record(self.user, self.word, WordEncounter.UNKNOWN, "mine")
        cevap = self._beyan("stuck")
        self.assertEqual(cevap.status_code, 200)
        kayit = WordEncounter.objects.get(user=self.user, word=self.word)
        self.assertEqual(kayit.declaration, Declaration.STUCK)

    def test_gecersiz_beyan_reddedilir(self):
        for _ in range(3):
            WordEncounter.record(self.user, self.word, WordEncounter.UNKNOWN, "mine")
        self.assertEqual(self._beyan("banana").status_code, 400)

    def test_kart_beyan_bilgisini_tasiyor(self):
        """Kullanıcı kaçıncı kez gördüğünü görmeden beyan anlamsız."""
        for _ in range(3):
            WordEncounter.record(self.user, self.word, WordEncounter.UNKNOWN, "mine")
        from learnpass.views import card_payload
        kart = card_payload(self.word, self.user)
        self.assertEqual(kart["encounter"]["times_seen"], 3)
        self.assertTrue(kart["encounter"]["can_declare"])
