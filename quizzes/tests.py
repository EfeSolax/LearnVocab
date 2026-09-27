"""
Çalışma sisteminin testleri.

Testlerin çoğu "şu kural gerçekten uygulanıyor mu" sorusunu soruyor,
"kod çalışıyor mu" sorusunu değil. Sebebi bu sistemde hataların
SESSİZ olması: yanlış zamanlanmış bir kart hata vermez, yalnızca
öğrenci o kelimeyi unutur ve kimse fark etmez.

Kelime hattında (KELIME-HATTI-DEVAM.txt §8) bulunan bugların çoğu tam
olarak bu türdendi; buradaki testler aynı sınıftan hataları yakalamak
için yazıldı.
"""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import User
from usersettings.models import UserSettings
from words.models import (
    Category, Collocation, CollocationKind, ExampleSentence, FalseFriend,
    Meaning, PartOfSpeech, RelationType, Sentiment, UsagePattern,
    UserWordLink, Word, WordFamily, WordForm, WordRelation,
)

from . import aspects, build, distractors, masking, questions, scheduler
from . import session as oturum
from .aspects import Aspect, Format
from .models import (
    ItemState, ReviewItem, ReviewLog, SessionMode, StudySession,
    knowledge_score, study_streak,
)


# ----------------------------------------------------------------------
# Yardımcılar
# ----------------------------------------------------------------------

def kelime_kur(text, pos=PartOfSpeech.NOUN, aile=None, anlam="anlam",
               cumleler=(), cefr="B2", v2=None, v3=None,
               sentiment=Sentiment.NEUTRAL):
    aile = aile or WordFamily.objects.create(root=text)
    kelime = Word.objects.create(
        family=aile, text=text, pos=pos, cefr=cefr, v2Form=v2, v3Form=v3,
    )
    WordForm.objects.create(word=kelime, surface=text, kind="other")
    if v2:
        WordForm.objects.create(word=kelime, surface=v2, kind="past")
    m = Meaning.objects.create(word=kelime, meaning_tr=anlam,
                               definition=f"{text} tanımı",
                               sentiment=sentiment)
    for i, c in enumerate(cumleler):
        ExampleSentence.objects.create(meaning=m, text=c, sort_order=i)
    return kelime, m


class TemelKurulum(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="efe", password="x")
        UserSettings.objects.create(user=self.user, dailyGoal=10)

    def listeye_ekle(self, kelime):
        UserWordLink.objects.get_or_create(user=self.user, word=kelime)
        return kelime


# ----------------------------------------------------------------------
# Zamanlayıcı
# ----------------------------------------------------------------------

class ZamanlayiciTests(TestCase):

    def test_kararlilik_tanimi_dogru(self):
        """R(S,S) tam olarak 0.9 olmalı — kararlılığın tanımı budur."""
        for s in (1.0, 5.0, 30.0, 200.0):
            self.assertAlmostEqual(scheduler.hatirlanabilirlik(s, s), 0.9, places=6)

    def test_hedef_090_iken_aralik_kararliliga_esit(self):
        self.assertAlmostEqual(scheduler.aralik(12.0, 0.9), 12.0, places=6)

    def test_daha_yuksek_hedef_daha_kisa_aralik(self):
        """%95 hatırlama istenirse kart daha SIK sorulmalı."""
        self.assertLess(scheduler.aralik(20.0, 0.95), scheduler.aralik(20.0, 0.90))

    def test_aralik_basarili_tekrarlarda_buyur(self):
        hafiza, gecen, araliklar = None, 0, []
        for _ in range(5):
            hafiza = scheduler.guncelle(hafiza, scheduler.IYI, gecen)
            gecen = scheduler.sonraki_aralik(hafiza)
            araliklar.append(gecen)
        self.assertEqual(araliklar, sorted(araliklar))
        self.assertGreater(araliklar[-1], araliklar[0] * 5)

    def test_unutma_kararliligi_dusurur_zorlugu_artirir(self):
        hafiza = scheduler.Hafiza(kararlilik=50.0, zorluk=5.0)
        yeni = scheduler.guncelle(hafiza, scheduler.YENIDEN, 50.0)
        self.assertLess(yeni.kararlilik, hafiza.kararlilik)
        self.assertGreater(yeni.zorluk, hafiza.zorluk)

    def test_unutma_kararliligi_sifirlamaz(self):
        """Bir kez öğrenilmiş kelime, hiç görülmemişten ileride kalır."""
        yeni = scheduler.guncelle(
            scheduler.Hafiza(kararlilik=50.0, zorluk=5.0),
            scheduler.YENIDEN, 50.0,
        )
        self.assertGreater(yeni.kararlilik, scheduler.EN_DUSUK_KARARLILIK)

    def test_dusuk_hatirlanabilirlikte_hatirlamak_daha_cok_kazandirir(self):
        """İstenen zorluk: zar zor hatırlanan kart daha çok iz bırakır."""
        hafiza = scheduler.Hafiza(kararlilik=10.0, zorluk=5.0)
        erken = scheduler.guncelle(hafiza, scheduler.IYI, 1.0)     # R yüksek
        gec = scheduler.guncelle(hafiza, scheduler.IYI, 20.0)      # R düşük
        self.assertGreater(gec.kararlilik, erken.kararlilik)

    def test_aralik_ust_sinira_takilir(self):
        hafiza = scheduler.Hafiza(kararlilik=10000.0, zorluk=5.0)
        self.assertLessEqual(scheduler.sonraki_aralik(hafiza),
                             scheduler.EN_UZUN_ARALIK)

    def test_not_uretimi(self):
        self.assertEqual(scheduler.not_uret(False, 2, 10), scheduler.YENIDEN)
        self.assertEqual(scheduler.not_uret(True, 30, 10), scheduler.ZOR)
        self.assertEqual(scheduler.not_uret(True, 8, 10), scheduler.IYI)
        self.assertEqual(scheduler.not_uret(True, 2, 10, uretim_mi=True),
                         scheduler.KOLAY)

    def test_ipucu_kullanan_en_fazla_zor_alir(self):
        self.assertEqual(
            scheduler.not_uret(True, 1, 10, ipucu_kullanildi=True, uretim_mi=True),
            scheduler.ZOR,
        )

    def test_sik_isaretlemede_kolay_notu_verilmez(self):
        """Dört şıktan birini hızlı seçmek akıcılık değil; eleme de hızlıdır."""
        self.assertEqual(scheduler.not_uret(True, 1, 10, uretim_mi=False),
                         scheduler.IYI)

    def test_yuksek_guvenli_hata_ayrimi(self):
        self.assertTrue(scheduler.yuksek_guvenli_hata(False, 2, 10))
        self.assertFalse(scheduler.yuksek_guvenli_hata(False, 30, 10))
        self.assertFalse(scheduler.yuksek_guvenli_hata(True, 2, 10))

    def test_sure_bilinmiyorsa_dogru_cevap_iyi_sayilir(self):
        self.assertEqual(scheduler.not_uret(True, None, 10), scheduler.IYI)


# ----------------------------------------------------------------------
# Maskeleme
# ----------------------------------------------------------------------

class MaskelemeTests(TestCase):

    def test_cekimli_bicim_maskelenir(self):
        maskeli, bulunan = masking.blank_word(
            "The company retained most of its customers.",
            ["retained", "retaining", "retain"],
        )
        self.assertIn(masking.BLANK, maskeli)
        self.assertEqual(bulunan, "retained")

    def test_phrasal_verb_araya_kelime_girse_de_bulunur(self):
        maskeli, bulunan = masking.blank_word(
            "He carried it out carefully.", ["carried out"],
        )
        self.assertIsNotNone(maskeli)
        self.assertEqual(bulunan, "carried it out")

    def test_bulunamayan_kelime_none_doner(self):
        """Yanlış maskelenmiş soru sormaktansa soru sormamak iyidir."""
        maskeli, _ = masking.blank_word("Nothing to see here.", ["retain"])
        self.assertIsNone(maskeli)

    def test_yazim_toleransi_yok(self):
        """retain / retail benzerliği %80'in üstünde — tolerans olsaydı geçerdi."""
        self.assertFalse(masking.answer_matches("retail", ["retain"]))

    def test_kabul_listesindeki_cekim_gecerli(self):
        self.assertTrue(masking.answer_matches("retain", ["retained", "retain"]))

    def test_yer_tutucular_yok_sayilir(self):
        self.assertTrue(masking.answer_matches("depend on", ["depend on sth"]))

    def test_noktalama_kirpilir(self):
        self.assertTrue(masking.answer_matches("  Retain. ", ["retain"]))

    def test_bos_cevap_yanlis(self):
        self.assertFalse(masking.answer_matches("", ["retain"]))

    def test_isaretleme_mark_ekler(self):
        sonuc = masking.highlight("They retain data.", ["retain"])
        self.assertIn("<mark>retain</mark>", sonuc)


# ----------------------------------------------------------------------
# Kart üretimi ve merdiven
# ----------------------------------------------------------------------

class KartUretimiTests(TemelKurulum):

    def setUp(self):
        super().setUp()
        self.kelime, self.anlam = kelime_kur(
            "retain", PartOfSpeech.VERB, anlam="elde tutmak",
            cumleler=["The company retained most of its customers."],
            v2="retained", v3="retained",
        )
        self.listeye_ekle(self.kelime)

    def test_giris_kartlari_acilir(self):
        build.ensure_entry_items(self.user, self.kelime)
        self.assertTrue(ReviewItem.objects.filter(
            user=self.user, aspect=Aspect.RECOGNIZE).exists())

    def test_giris_kartlari_iki_kez_acilmaz(self):
        build.ensure_entry_items(self.user, self.kelime)
        ilk = ReviewItem.objects.filter(user=self.user).count()
        build.ensure_entry_items(self.user, self.kelime)
        self.assertEqual(ReviewItem.objects.filter(user=self.user).count(), ilk)

    def test_uretim_karti_baslangicta_yok(self):
        """Tanımadığı kelimeyi üretmesi istenmemeli."""
        build.ensure_entry_items(self.user, self.kelime)
        self.assertFalse(ReviewItem.objects.filter(
            user=self.user, aspect=Aspect.PRODUCE).exists())

    def test_uretim_karti_esik_asilinca_acilir(self):
        build.ensure_entry_items(self.user, self.kelime)
        kart = ReviewItem.objects.get(user=self.user, aspect=Aspect.RECOGNIZE)

        kart.stability = aspects.UNLOCK_PRODUCTION_STABILITY - 0.5
        kart.save()
        build.unlock_after_review(kart)
        self.assertFalse(ReviewItem.objects.filter(
            user=self.user, aspect=Aspect.PRODUCE).exists())

        kart.stability = aspects.UNLOCK_PRODUCTION_STABILITY + 0.5
        kart.save()
        build.unlock_after_review(kart)
        self.assertTrue(ReviewItem.objects.filter(
            user=self.user, aspect=Aspect.PRODUCE).exists())

    def test_kullanim_kartlari_uretimden_sonra_acilir(self):
        build.ensure_entry_items(self.user, self.kelime)
        tanima = ReviewItem.objects.get(user=self.user, aspect=Aspect.RECOGNIZE)
        tanima.stability = 10.0
        tanima.save()
        build.unlock_after_review(tanima)

        uretim = ReviewItem.objects.get(user=self.user, aspect=Aspect.PRODUCE)
        uretim.stability = aspects.UNLOCK_USE_STABILITY + 1
        uretim.save()
        build.unlock_after_review(uretim)

        self.assertTrue(ReviewItem.objects.filter(
            user=self.user, aspect=Aspect.CONTEXT).exists())

    def test_duzenli_fiile_cekim_karti_acilmaz(self):
        """walk -> walked kuraldan çıkıyor; ezberlenecek bir şey yok."""
        kelime, _ = kelime_kur("walk", PartOfSpeech.VERB, anlam="yürümek",
                               v2="walked", v3="walked")
        self.listeye_ekle(kelime)
        build.ensure_entry_items(self.user, kelime)
        kart = ReviewItem.objects.get(user=self.user, word=kelime,
                                      aspect=Aspect.RECOGNIZE)
        kart.stability = 10.0
        kart.save()
        build.unlock_after_review(kart)
        self.assertFalse(ReviewItem.objects.filter(
            user=self.user, word=kelime, aspect=Aspect.FORM).exists())

    def test_duzensiz_fiile_cekim_karti_acilir(self):
        kelime, _ = kelime_kur("go", PartOfSpeech.VERB, anlam="gitmek",
                               v2="went", v3="gone")
        self.listeye_ekle(kelime)
        build.ensure_entry_items(self.user, kelime)
        kart = ReviewItem.objects.get(user=self.user, word=kelime,
                                      aspect=Aspect.RECOGNIZE)
        kart.stability = 10.0
        kart.save()
        build.unlock_after_review(kart)
        self.assertTrue(ReviewItem.objects.filter(
            user=self.user, word=kelime, aspect=Aspect.FORM).exists())

    def test_aile_karti_aile_basina_bir_tane(self):
        aile = WordFamily.objects.create(root="analyse")
        for metin, tur in (("analyse", PartOfSpeech.VERB),
                           ("analysis", PartOfSpeech.NOUN),
                           ("analytical", PartOfSpeech.ADJECTIVE)):
            k, _ = kelime_kur(metin, tur, aile=aile, anlam=f"{metin} anlamı",
                              cumleler=[f"This is {metin} in a sentence."])
            self.listeye_ekle(k)

        for kelime in aile.words.all():
            build.ensure_entry_items(self.user, kelime)
            tanima = ReviewItem.objects.filter(
                user=self.user, word=kelime, aspect=Aspect.RECOGNIZE).first()
            tanima.stability = 10.0
            tanima.save()
            build.unlock_after_review(tanima)
            uretim = ReviewItem.objects.filter(
                user=self.user, word=kelime, aspect=Aspect.PRODUCE).first()
            uretim.stability = 20.0
            uretim.save()
            build.unlock_after_review(uretim)

        self.assertEqual(
            ReviewItem.objects.filter(user=self.user, aspect=Aspect.FAMILY).count(),
            1,
        )

    def test_notr_tonlu_anlama_ton_karti_acilmaz(self):
        build.ensure_entry_items(self.user, self.kelime)
        self.assertFalse(ReviewItem.objects.filter(
            user=self.user, aspect=Aspect.NUANCE).exists())

    def test_tonlu_anlama_ton_karti_acilir(self):
        kelime, _ = kelime_kur("notorious", PartOfSpeech.ADJECTIVE,
                               anlam="kötü ünlü",
                               sentiment=Sentiment.NEGATIVE)
        self.listeye_ekle(kelime)
        build.ensure_entry_items(self.user, kelime)
        self.assertTrue(ReviewItem.objects.filter(
            user=self.user, word=kelime, aspect=Aspect.NUANCE).exists())

    def test_yanlis_dost_karti_acilir(self):
        FalseFriend.objects.create(
            word=self.kelime, turkish_lookalike="retina",
            assumed_meaning="göz retinası", correct_english="retina",
        )
        build.ensure_entry_items(self.user, self.kelime)
        self.assertTrue(ReviewItem.objects.filter(
            user=self.user, aspect=Aspect.FALSE_FRIEND).exists())


# ----------------------------------------------------------------------
# Çeldiriciler
# ----------------------------------------------------------------------

class CeldiriciTests(TestCase):

    def test_ortusen_anlamlar_yakalanir(self):
        self.assertTrue(distractors.ortusuyor_mu("ders, konu", "konu, ders"))
        self.assertFalse(distractors.ortusuyor_mu("hesap", "koşmak"))

    def test_ortusen_celdirici_secilmez(self):
        """İki şıkkın da doğru olduğu soru, soru değildir."""
        _, dogru = kelime_kur("subject", anlam="ders, konu")
        kelime2, _ = kelime_kur("topic", anlam="konu, ders")
        kelime3, _ = kelime_kur("bridge", anlam="köprü")
        kelime4, _ = kelime_kur("stone", anlam="taş")
        kelime5, _ = kelime_kur("river", anlam="nehir")

        celdiriciler = distractors.meaning_distractors(dogru, count=3)
        metinler = [distractors.distractor_text(c) for c in celdiriciler]
        self.assertNotIn("konu, ders", metinler)

    def test_karistirilan_cift_celdirici_olarak_one_gecer(self):
        k1, m1 = kelime_kur("principle", anlam="ilke")
        k2, _ = kelime_kur("principal", anlam="müdür")
        WordRelation.objects.create(from_word=k1, to_word=k2,
                                    type=RelationType.CONFUSED_WITH)
        celdiriciler = distractors.meaning_distractors(m1, count=3)
        metinler = [distractors.distractor_text(c) for c in celdiriciler]
        self.assertIn("müdür", metinler)


# ----------------------------------------------------------------------
# Soru üretimi
# ----------------------------------------------------------------------

class SoruUretimiTests(TemelKurulum):

    def setUp(self):
        super().setUp()
        self.kelime, self.anlam = kelime_kur(
            "retain", PartOfSpeech.VERB, anlam="elde tutmak",
            cumleler=["The company retained most of its customers.",
                      "Plants retain water in their leaves."],
            v2="retained", v3="retained",
        )
        self.listeye_ekle(self.kelime)
        for metin, anlam in (("keep", "tutmak"), ("lose", "kaybetmek"),
                             ("hold", "tutmak, kavramak"), ("drop", "düşürmek")):
            kelime_kur(metin, PartOfSpeech.VERB, anlam=anlam)
        build.ensure_entry_items(self.user, self.kelime)

    def _kart(self, aspect):
        return ReviewItem.objects.filter(user=self.user, aspect=aspect).first()

    def test_tanima_sorusu_uretilir(self):
        soru = questions.build(self._kart(Aspect.RECOGNIZE))
        self.assertIsNotNone(soru)
        self.assertTrue(soru.options)
        self.assertTrue(soru.correct_key)

    def test_dogru_sik_gercekten_dogru(self):
        kart = self._kart(Aspect.RECOGNIZE)
        soru = questions.build(kart)
        dogru_metin = next(o["text"] for o in soru.options
                           if o["key"] == soru.correct_key)
        self.assertEqual(dogru_metin, self.anlam.meaning_tr)

    def test_soru_uretimi_tekrarlanabilir(self):
        """
        Aynı kart, aynı tekrarda AYNI soruyu vermeli.

        Soru iki kez üretiliyor: bir kez ekrana basarken, bir kez cevabı
        değerlendirirken. Rastgele tohumla şıklar yeniden karışır ve
        doğru cevap veren öğrenci yanlış yapmış sayılır.
        """
        kart = self._kart(Aspect.RECOGNIZE)
        ilk = questions.build(kart)
        ikinci = questions.build(kart)
        self.assertEqual(ilk.correct_key, ikinci.correct_key)
        self.assertEqual([o["text"] for o in ilk.options],
                         [o["text"] for o in ikinci.options])

    def test_tekrar_sayisi_degisince_soru_degisir(self):
        kart = self._kart(Aspect.RECOGNIZE)
        ilk = questions.build(kart)
        kart.reps = 1
        ilk_bicim = ilk.format
        ikinci = questions.build(kart)
        self.assertNotEqual(ilk_bicim, ikinci.format)

    def test_veri_yoksa_soru_uretilmez(self):
        kelime, _ = kelime_kur("bare", anlam="çıplak")   # cümlesi yok
        self.listeye_ekle(kelime)
        kart = ReviewItem.objects.create(
            user=self.user, word=kelime,
            meaning=kelime.primary_meaning, aspect=Aspect.CONTEXT,
        )
        self.assertIsNone(questions.build(kart))

    def test_baglam_sorusu_cumlede_kelimeyi_maskeler(self):
        kart = ReviewItem.objects.create(
            user=self.user, word=self.kelime, meaning=self.anlam,
            aspect=Aspect.CONTEXT,
        )
        soru = questions.build(kart)
        self.assertIsNotNone(soru)
        self.assertIn(masking.BLANK, soru.sentence)
        self.assertNotIn("retained", soru.sentence)

    def test_esdizim_sorusu_kelimeyi_degil_esini_maskeler(self):
        esdizim = Collocation.objects.create(
            meaning=self.anlam, pattern="retain customers",
            kind=CollocationKind.VERB_NOUN,
            example="The company retained customers last year.",
        )
        kart = ReviewItem.objects.create(
            user=self.user, word=self.kelime, meaning=self.anlam,
            aspect=Aspect.COLLOCATION, target_id=esdizim.id,
        )
        soru = questions.build(kart)
        self.assertIsNotNone(soru)
        # Maskelenen "customers" olmalı, "retained" değil.
        self.assertIn("retained", soru.sentence)
        self.assertNotIn("customers", soru.sentence)

    def test_yanlis_dost_dogru_yanlis_sorusu(self):
        yd = FalseFriend.objects.create(
            word=self.kelime, turkish_lookalike="retina",
            assumed_meaning="göz retinası",
        )
        kart = ReviewItem.objects.create(
            user=self.user, word=self.kelime,
            aspect=Aspect.FALSE_FRIEND, target_id=yd.id,
        )
        soru = questions.build(kart)
        self.assertIsNotNone(soru)
        self.assertEqual(soru.format, Format.TRUE_FALSE)
        # Doğru cevap her zaman "Yanlış": yanlış dost eşitliği kurulmaz.
        dogru_metin = next(o["text"] for o in soru.options
                           if o["key"] == soru.correct_key)
        self.assertEqual(dogru_metin, "Yanlış")

    def test_karistirilan_cift_iki_sikli(self):
        oteki, _ = kelime_kur("detain", PartOfSpeech.VERB, anlam="alıkoymak",
                              cumleler=["Police detained the suspect."])
        bag = WordRelation.objects.create(
            from_word=self.kelime, to_word=oteki,
            type=RelationType.CONFUSED_WITH,
        )
        kart = ReviewItem.objects.create(
            user=self.user, word=self.kelime,
            aspect=Aspect.CONFUSABLE, target_id=bag.id,
        )
        soru = questions.build(kart)
        self.assertIsNotNone(soru)
        self.assertEqual(len(soru.options), 2)

    def test_yazarak_cevap_kontrolu(self):
        kart = ReviewItem.objects.create(
            user=self.user, word=self.kelime, meaning=self.anlam,
            aspect=Aspect.PRODUCE,
        )
        kart.reps = 0          # ilk biçim: yazarak
        soru = questions.build(kart)
        self.assertTrue(soru.is_typed)
        self.assertTrue(soru.check("retain"))
        self.assertFalse(soru.check("retail"))


# ----------------------------------------------------------------------
# Oturum motoru
# ----------------------------------------------------------------------

class OturumTests(TemelKurulum):

    def setUp(self):
        super().setUp()
        self.kelimeler = []
        for i in range(12):
            kelime, _ = kelime_kur(
                f"word{i}", anlam=f"anlam{i}",
                cumleler=[f"This is word{i} in a sentence here."],
            )
            self.listeye_ekle(kelime)
            self.kelimeler.append(kelime)

    def test_oturum_kuyrugu_kurulur(self):
        s = oturum.start(self.user)
        self.assertTrue(s.queue)
        self.assertEqual(s.planned_count, len(s.queue))

    def test_yeni_kart_gunluk_hedefle_sinirli(self):
        self.user.mysettings.dailyGoal = 3
        self.user.mysettings.save()
        s = oturum.start(self.user)
        self.assertLessEqual(len(s.queue), 3)

    def test_gunluk_hedef_sifirsa_yeni_kart_acilmaz(self):
        self.user.mysettings.dailyGoal = 0
        self.user.mysettings.save()
        s = oturum.start(self.user)
        self.assertEqual(len(s.queue), 0)

    def test_yeni_kartlar_merdiven_sirasiyla_gelir(self):
        """
        İlk oturumda yalnızca tanıma kartı olmalı.

        İlk sürümde bu sıralama `order_by("aspect")` idi ve alfabetik
        sıra yüzünden yeni kullanıcıya hiç tanımadığı kelimelerin
        EŞ DİZİMLERİ soruluyordu (collocation < recognize).
        """
        build.ensure_all_entry_items(self.user)
        for kart in ReviewItem.objects.filter(user=self.user,
                                              aspect=Aspect.RECOGNIZE):
            kart.stability = 30.0
            kart.difficulty = 5.0
            kart.save()
            build.unlock_after_review(kart)
        ReviewItem.objects.filter(user=self.user).update(
            state=ItemState.NEW, stability=None, difficulty=None, due_at=None)

        s = oturum.start(self.user)
        boyutlar = set(ReviewItem.objects.filter(id__in=s.queue)
                       .values_list("aspect", flat=True))
        self.assertEqual(boyutlar, {Aspect.RECOGNIZE})

    def test_ayni_kelime_arka_arkaya_gelmez(self):
        self.user.mysettings.dailyGoal = 30
        self.user.mysettings.save()
        s = oturum.start(self.user)
        kelime_idleri = list(
            ReviewItem.objects.filter(id__in=s.queue)
            .in_bulk(s.queue).get(k).word_id for k in s.queue
        )
        ardisik = sum(1 for a, b in zip(kelime_idleri, kelime_idleri[1:]) if a == b)
        self.assertEqual(ardisik, 0)

    def test_dogru_cevap_karti_ilerletir(self):
        s = oturum.start(self.user)
        item, soru = oturum.next_question(s)
        sonuc = oturum.answer(s, item, soru.correct_key, seconds=5)
        item.refresh_from_db()
        self.assertTrue(sonuc["correct"])
        self.assertEqual(item.state, ItemState.REVIEW)
        self.assertIsNotNone(item.due_at)
        self.assertGreater(item.stability, 0)

    def test_yanlis_cevap_karti_oturum_ici_kuyruga_geri_koyar(self):
        s = oturum.start(self.user)
        item, soru = oturum.next_question(s)
        yanlis = next(o["key"] for o in soru.options if o["key"] != soru.correct_key)
        oturum.answer(s, item, yanlis, seconds=15)
        s.refresh_from_db()
        self.assertIn(item.id, s.queue)
        self.assertIn(item.id, s.missed)

    def test_yuksek_guvenli_hata_bir_hafta_icinde_tekrar_ister(self):
        s = oturum.start(self.user)
        item, soru = oturum.next_question(s)
        yanlis = next(o["key"] for o in soru.options if o["key"] != soru.correct_key)
        oturum.answer(s, item, yanlis, seconds=1.0)   # hızlı ve yanlış
        item.refresh_from_db()
        self.assertIsNotNone(item.recheck_by)
        self.assertLessEqual(item.due_at, item.recheck_by)

    def test_zorunlu_tekrar_isareti_sonraki_tekrarda_kalkar(self):
        """
        İşaret kalkmazsa kart geçmiş bir tarihe kilitleniyor ve sonsuza
        kadar "sırası gelmiş" görünüyor. Kod hata vermiyor; kullanıcı
        yalnızca aynı kartı durmadan görüyor.
        """
        s = oturum.start(self.user)
        item, soru = oturum.next_question(s)
        yanlis = next(o["key"] for o in soru.options if o["key"] != soru.correct_key)
        oturum.answer(s, item, yanlis, seconds=1.0)      # hızlı + yanlış
        item.refresh_from_db()
        self.assertIsNotNone(item.recheck_by)

        # Aynı kart oturum içinde geri geldi; bu kez doğru cevaplanıyor.
        item, soru = oturum.next_question(s)
        while item.recheck_by is None:
            oturum.answer(s, item, soru.correct_key, seconds=5)
            item, soru = oturum.next_question(s)
            if soru is None:
                self.fail("işaretli kart kuyruğa geri dönmedi")
        oturum.answer(s, item, soru.correct_key, seconds=5)
        item.refresh_from_db()
        self.assertIsNone(item.recheck_by)
        self.assertGreater(item.due_at, timezone.now())

    def test_tereddutlu_hata_isaretlenmez(self):
        s = oturum.start(self.user)
        item, soru = oturum.next_question(s)
        yanlis = next(o["key"] for o in soru.options if o["key"] != soru.correct_key)
        oturum.answer(s, item, yanlis, seconds=60)    # yavaş ve yanlış
        item.refresh_from_db()
        self.assertIsNone(item.recheck_by)

    def test_her_cevap_kayit_birakir(self):
        s = oturum.start(self.user)
        item, soru = oturum.next_question(s)
        oturum.answer(s, item, soru.correct_key, seconds=5)
        kayit = ReviewLog.objects.get(user=self.user)
        self.assertEqual(kayit.word_text, item.word.text)
        self.assertTrue(kayit.is_correct)
        self.assertGreater(kayit.scheduled_days, 0)
        self.assertIsNotNone(kayit.stability_after)

    def test_kelime_sayaclari_da_guncellenir(self):
        """Analiz sayfası ve Öğren-Geç bu sayaçlara bakmaya devam ediyor."""
        from quizzes.views import _kelime_sayaclarini_guncelle

        s = oturum.start(self.user)
        item, soru = oturum.next_question(s)
        oturum.answer(s, item, soru.correct_key, seconds=5)
        _kelime_sayaclarini_guncelle(self.user, item, True)
        bag = UserWordLink.objects.get(user=self.user, word=item.word)
        self.assertEqual(bag.correctCount, 1)

    def test_birikmis_tekrar_yeni_kart_acmayi_durdurur(self):
        """Borç varken yeni borç açılmaz — bırakmanın bir numaralı sebebi."""
        from .models import DailyGoalDefaults

        gecmis = timezone.now() - timedelta(days=3)
        build.ensure_all_entry_items(self.user)
        kartlar = list(ReviewItem.objects.filter(user=self.user))
        for kart in kartlar:
            kart.state = ItemState.REVIEW
            kart.due_at = gecmis
            kart.stability = 2.0
            kart.difficulty = 5.0
            kart.save()
        # Eşiği aşacak kadar gecikmiş kart üret
        self.assertGreater(len(kartlar), 0)
        eski_esik = DailyGoalDefaults.BACKLOG_BLOCK_THRESHOLD
        DailyGoalDefaults.BACKLOG_BLOCK_THRESHOLD = 1
        try:
            self.assertEqual(oturum._yeni_kart_butcesi(self.user), 0)
        finally:
            DailyGoalDefaults.BACKLOG_BLOCK_THRESHOLD = eski_esik

    def test_oturum_ust_siniri_asilmaz(self):
        for i in range(100):
            kelime, _ = kelime_kur(f"extra{i}", anlam=f"ek{i}")
            self.listeye_ekle(kelime)
        self.user.mysettings.dailyGoal = 500
        self.user.mysettings.save()
        s = oturum.start(self.user)
        self.assertLessEqual(len(s.queue), oturum.OTURUM_UST_SINIRI)

    def test_kuyruk_bitince_soru_kalmaz(self):
        self.user.mysettings.dailyGoal = 2
        self.user.mysettings.save()
        s = oturum.start(self.user)
        for _ in range(30):
            item, soru = oturum.next_question(s)
            if soru is None:
                break
            oturum.answer(s, item, soru.correct_key, seconds=5)
        self.assertEqual(len(s.queue), 0)


# ----------------------------------------------------------------------
# Ölçüler
# ----------------------------------------------------------------------

class OlcuTests(TemelKurulum):

    def test_kalici_bilgi_zamanla_duser(self):
        """Sürekli artan bir sayaç öğrenciye yanlış güven verir."""
        kelime, _ = kelime_kur("decay", anlam="çürümek")
        self.listeye_ekle(kelime)
        kart = ReviewItem.objects.create(
            user=self.user, word=kelime, meaning=kelime.primary_meaning,
            aspect=Aspect.RECOGNIZE, stability=10.0, difficulty=5.0,
            state=ItemState.REVIEW, last_reviewed_at=timezone.now(),
        )
        taze = knowledge_score(self.user)

        kart.last_reviewed_at = timezone.now() - timedelta(days=60)
        kart.save()
        eskimis = knowledge_score(self.user)

        self.assertGreater(taze, eskimis)

    def test_seri_bugun_calisilmadiysa_hemen_sifirlanmaz(self):
        kelime, _ = kelime_kur("streak", anlam="seri")
        dun = timezone.now() - timedelta(days=1)
        kayit = ReviewLog.objects.create(
            user=self.user, word_text="streak", aspect=Aspect.RECOGNIZE,
            format=Format.CHOICE, is_correct=True, grade=3,
        )
        ReviewLog.objects.filter(id=kayit.id).update(answered_at=dun)
        self.assertEqual(study_streak(self.user), 1)

    def test_hic_calismamis_kullanicinin_serisi_sifir(self):
        self.assertEqual(study_streak(self.user), 0)


# ----------------------------------------------------------------------
# Sayfalar
# ----------------------------------------------------------------------

class SayfaTests(TemelKurulum):

    def setUp(self):
        super().setUp()
        for i in range(5):
            kelime, _ = kelime_kur(f"page{i}", anlam=f"sayfa{i}",
                                   cumleler=[f"A page{i} sentence goes here."])
            self.listeye_ekle(kelime)
        self.client.login(username="efe", password="x")

    def test_calisma_ana_sayfasi_acilir(self):
        cevap = self.client.get(reverse("study_home"))
        self.assertEqual(cevap.status_code, 200)

    def test_oturum_baslatilip_soru_gelir(self):
        cevap = self.client.post(reverse("study_start"), {"mode": "due"})
        self.assertEqual(cevap.status_code, 302)
        cevap = self.client.get(cevap.url)
        self.assertEqual(cevap.status_code, 200)
        self.assertIn("question", cevap.context)

    def test_cevap_gonderilince_geri_bildirim_gosterilir(self):
        self.client.post(reverse("study_start"), {"mode": "due"})
        s = StudySession.objects.filter(user=self.user).first()
        item, soru = oturum.next_question(s)
        cevap = self.client.post(
            reverse("study_run", kwargs={"session_id": s.id}),
            {"item_id": item.id, "answer": soru.correct_key, "seconds": "4.0"},
        )
        self.assertEqual(cevap.status_code, 200)
        self.assertTrue(cevap.context["feedback"]["correct"])

    def test_yanlis_cevap_sik_metniyle_gosterilir(self):
        """
        "Senin cevabın: A" hiçbir şey anlatmaz — öğrenci bir soru önce
        neyi işaretlediğini şıkkın harfiyle değil metniyle hatırlar.
        """
        self.client.post(reverse("study_start"), {"mode": "due"})
        s = StudySession.objects.filter(user=self.user).first()
        item, soru = oturum.next_question(s)
        yanlis = next(o for o in soru.options if o["key"] != soru.correct_key)
        cevap = self.client.post(
            reverse("study_run", kwargs={"session_id": s.id}),
            {"item_id": item.id, "answer": yanlis["key"], "seconds": "9.0"},
        )
        self.assertEqual(cevap.context["user_answer"], yanlis["text"])

    def test_baskasinin_oturumuna_erisilemez(self):
        baskasi = User.objects.create_user(username="baska", password="x")
        s = StudySession.objects.create(user=baskasi, queue=[])
        cevap = self.client.get(reverse("study_run", kwargs={"session_id": s.id}))
        self.assertEqual(cevap.status_code, 404)

    def test_ilerleme_sayfasi_acilir(self):
        cevap = self.client.get(reverse("study_progress"))
        self.assertEqual(cevap.status_code, 200)

    def test_analiz_sayfasi_acilir(self):
        cevap = self.client.get(reverse("word_analysis"))
        self.assertEqual(cevap.status_code, 200)

    def test_giris_yapmamis_kullaniciya_kapi_gosterilir(self):
        self.client.logout()
        cevap = self.client.get(reverse("study_home"))
        self.assertEqual(cevap.status_code, 200)
        self.assertContains(cevap, "giriş", status_code=200)
