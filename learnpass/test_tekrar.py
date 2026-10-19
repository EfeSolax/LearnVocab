"""Tekrar kuralı (rapor 18.2): learnpass/tekrar.py."""

import json
import random
from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from learnpass import tekrar
from learnpass.models import EncounterLog, WordEncounter
from users.models import User
from words.models import UserWordLink
from words.testing import make_word

K, U, M = WordEncounter.KNOWN, WordEncounter.UNKNOWN, WordEncounter.MISJUDGED
D, Y = WordEncounter.DOGRU, WordEncounter.YANLIS


class KayitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tekrar", password="Sifre1234")
        self.w = make_word("scatter", level="B2")
        self.t0 = timezone.now()

    def _kaydet(self, sonuc, gun=0, mode="mine"):
        return tekrar.kaydet(self.user, self.w, sonuc, mode, simdi=self.t0 + timedelta(days=gun))

    def test_1_3_7_21_ve_21_de_bir(self):
        UserWordLink.objects.create(user=self.user, word=self.w)
        beklenen = [1, 3, 7, 21, 21, 21]
        gun = 0
        for aralik in beklenen:
            enc = self._kaydet(K, gun)
            self.assertEqual(enc.sonraki_tekrar - enc.son_bilinen_at, timedelta(days=aralik))
            gun += aralik
        self.assertEqual(enc.basamak, 6)

    def test_bilemeyince_ilerleme_sifirlanir_sayaclar_kalir(self):
        UserWordLink.objects.create(user=self.user, word=self.w)
        self._kaydet(K, 0)
        self._kaydet(K, 1)
        enc = self._kaydet(M, 4)
        self.assertEqual((enc.basamak, enc.son_basarili, enc.sonraki_tekrar), (0, False, None))
        self.assertEqual((enc.known_count, enc.misjudged_count, enc.times_seen), (2, 1, 3))
        self.assertTrue(tekrar.aday_mi(enc))   # zorlanan kelime her zaman aday
        enc = self._kaydet(K, 4)
        self.assertEqual(enc.sonraki_tekrar - enc.son_bilinen_at, timedelta(days=1))  # baştan

    def test_ilk_goruste_eminim_takibe_girmez(self):
        enc = self._kaydet(K, mode="new")
        self.assertFalse(enc.takipte)
        self.assertNotIn(self.w.id, tekrar.tekrar_sirasi(self.user, simdi=self.t0 + timedelta(days=30)))

    def test_bilinmeyen_yeni_kelime_listede_olmasa_da_takibe_girer(self):
        enc = self._kaydet(U, mode="new")
        self.assertTrue(enc.takipte)
        self.assertIn(self.w.id, tekrar.tekrar_sirasi(self.user))

    def test_egzersiz_dogrusu_yalnizca_adayken_ilerletir(self):
        UserWordLink.objects.create(user=self.user, word=self.w)
        self._kaydet(K, 0)                       # basamak 1, 1 gün sonra aday
        enc = self._kaydet(D, 0.5, mode="egzersiz")
        self.assertEqual(enc.basamak, 1)         # henüz aday değildi
        enc = self._kaydet(D, 1.5, mode="egzersiz")
        self.assertEqual(enc.basamak, 2)
        enc = self._kaydet(Y, 2, mode="egzersiz")  # yanlış her zaman sıfırlar
        self.assertEqual((enc.basamak, enc.egz_yanlis, enc.egz_dogru), (0, 1, 2))

    def test_gunluge_basamak_yazilir(self):
        UserWordLink.objects.create(user=self.user, word=self.w)
        self._kaydet(K, 0)
        self._kaydet(U, 1)
        self.assertEqual(list(EncounterLog.objects.order_by("id").values_list("basamak_once", flat=True)),
                         [0, 1])

    def test_birim_ayardan_degisir(self):
        UserWordLink.objects.create(user=self.user, word=self.w)
        with self.settings(TEKRAR_BIRIMI_SAAT=12):
            enc = self._kaydet(K)
        self.assertEqual(enc.sonraki_tekrar - enc.son_bilinen_at, timedelta(hours=12))


class SiralamaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="sira", password="Sifre1234")
        self.simdi = timezone.now()

    def _liste(self, ad):
        w = make_word(ad)
        UserWordLink.objects.create(user=self.user, word=w)
        return w

    def _gorulmus(self, w, dakika_once, sonuc=U, **alanlar):
        enc = tekrar.kaydet(self.user, w, sonuc, "mine")
        WordEncounter.objects.filter(pk=enc.pk).update(
            last_seen_at=self.simdi - timedelta(minutes=dakika_once), **alanlar)

    def test_hic_gorulmemis_once_sonra_en_eski(self):
        """Efe'nin örneği: 12.10'da görülenler 12.40'ta görülenlerden önce."""
        yeni = self._liste("never")
        eski, taze = self._liste("old"), self._liste("fresh")
        self._gorulmus(eski, 40)   # 12.10
        self._gorulmus(taze, 10)   # 12.40
        self.assertEqual(tekrar.tekrar_sirasi(self.user, simdi=self.simdi), [yeni.id, eski.id, taze.id])

    def test_ayni_dakikada_zorlanan_once(self):
        a, b = self._liste("alpha"), self._liste("beta")
        self._gorulmus(a, 20, unknown_count=1, times_seen=4)   # %25
        self._gorulmus(b, 20, unknown_count=3, times_seen=4)   # %75
        self.assertEqual(tekrar.tekrar_sirasi(self.user, simdi=self.simdi), [b.id, a.id])

    def test_araligi_dolmamis_bilinen_aday_degil(self):
        w = self._liste("known")
        tekrar.kaydet(self.user, w, K, "mine", simdi=self.simdi)
        self.assertEqual(tekrar.tekrar_sirasi(self.user, simdi=self.simdi), [])
        self.assertEqual(tekrar.tekrar_sirasi(self.user, simdi=self.simdi + timedelta(days=1, minutes=1)),
                         [w.id])

    def test_egzersiz_sirasi_once_adaylar_sonra_digerleri(self):
        bilinen, zor = self._liste("known"), self._liste("hard")
        tekrar.kaydet(self.user, bilinen, K, "mine")
        tekrar.kaydet(self.user, zor, U, "mine")
        self.assertEqual(tekrar.liste_sirasi(self.user), [zor.id, bilinen.id])


class YeniKelimeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="yeni", password="Sifre1234", cefr="B1")

    def test_gunluk_15_sinir(self):
        for i in range(20):
            make_word(f"new{i}", level="B1")
        for _ in range(tekrar.GUNLUK_YENI_SINIRI):
            w = tekrar.yeni_kelime(self.user)
            tekrar.kaydet(self.user, w, K, WordEncounter.MODE_NEW)
        self.assertIsNone(tekrar.yeni_kelime(self.user))

    def test_nadir_tur_c1_alti_kullaniciya_gelmez(self):
        make_word("dog", pos="verb", level="B1", nadir_tur=True)
        self.assertIsNone(tekrar.yeni_kelime(self.user))
        self.user.cefr = "C1"
        self.user.save()
        self.assertEqual(tekrar.yeni_kelime(self.user).text, "dog")

    def test_sik_kelime_daha_sik_gelir(self):
        make_word("house", level="B1", siklik=5.5)
        make_word("heath", level="B1", siklik=2.0)
        rng = random.Random(3)
        sayac = {"house": 0, "heath": 0}
        for _ in range(300):
            sayac[tekrar.yeni_kelime(self.user, rng=rng).text] += 1
        self.assertGreater(sayac["house"], sayac["heath"] * 5)

    def test_oncelikli_kelimeler_once_nadir_sona(self):
        # 40 kelime: öncelik 40 … 1. Seçim en öncelikli 30'un içinden olur; en alttakiler gelmez.
        for i in range(40):
            make_word(f"w{i:02d}", level="B1", oncelik=40 - i)
        rng = random.Random(5)
        secilenler = {tekrar.yeni_kelime(self.user, rng=rng).oncelik for _ in range(200)}
        self.assertGreaterEqual(min(secilenler), 40 - tekrar.PENCERE + 1)
        self.assertIn(40, secilenler)

    def test_zayif_seviye_guclu_komsunun_onune_gecmez(self):
        # C1 kullanıcı: "bir üst" C2'de yalnızca zayıf aday varsa C1'den gelir (Efe'ye corolla çıkıyordu)
        self.user.cefr = "C1"
        self.user.save()
        make_word("corolla", level="C2", oncelik=21.5)
        make_word("heritage", level="C1", oncelik=62.6)
        rng = random.Random(0)
        self.assertEqual({tekrar.yeni_kelime(self.user, rng=rng).text for _ in range(60)}, {"heritage"})

    def test_guclu_aday_kalmayinca_zayif_gelir(self):
        make_word("corolla", level="B1", oncelik=21.5)
        self.assertEqual(tekrar.yeni_kelime(self.user).text, "corolla")

    def test_hesaplanmamis_oncelik_sikliktan_tahmin_edilir(self):
        # oncelik_hesapla çalışmadan eklenen kelime sıklığıyla sıraya girer; sona atılmaz
        make_word("house", level="B1", siklik=5.5)
        for i in range(tekrar.PENCERE):
            make_word(f"seyrek{i}", level="B1", oncelik=5)
        rng = random.Random(1)
        self.assertIn("house", {tekrar.yeni_kelime(self.user, rng=rng).text for _ in range(50)})


class YeniAkisTests(TestCase):
    """Rapor 18.1: ikinci kaydırma "Hayır, yanılmışım" -> misjudged olarak kaydedilir."""

    def setUp(self):
        self.user = User.objects.create_user(username="akis2", password="Sifre1234")
        self.client.login(username="akis2", password="Sifre1234")
        self.w = make_word("candidate")

    def _post(self, verdict):
        return self.client.post(reverse("learn_pass_verdict"),
                                data=json.dumps({"word_id": self.w.id, "verdict": verdict, "mode": "new"}),
                                content_type="application/json")

    def test_yanilmisim_kaydedilir_ve_seriye_sayilir(self):
        cevap = self._post("misjudged")
        self.assertEqual(cevap.status_code, 200)
        enc = WordEncounter.objects.get(user=self.user, word=self.w)
        self.assertEqual((enc.last_verdict, enc.misjudged_count, enc.son_basarili), (M, 1, False))
        self.assertEqual(cevap.json()["seri"]["lp"], 1)

    def test_eski_beyan_ucu_yok(self):
        self.assertEqual(self.client.post("/exercises/learn/api/declare/").status_code, 404)

    def test_geri_al_tekrar_alanlarini_da_geri_getirir(self):
        UserWordLink.objects.create(user=self.user, word=self.w)
        self._post("known")
        onceki = WordEncounter.objects.get(user=self.user, word=self.w)
        self._post("unknown")
        self.client.post(reverse("learn_pass_undo"), data=json.dumps({"mode": "new"}),
                         content_type="application/json")
        enc = WordEncounter.objects.get(user=self.user, word=self.w)
        self.assertEqual((enc.basamak, enc.son_basarili, enc.sonraki_tekrar),
                         (onceki.basamak, True, onceki.sonraki_tekrar))

    def test_sayfada_ikinci_adim_dugmeleri(self):
        html = self.client.get(reverse("learn_pass_run", kwargs={"mode": "karma"})).content.decode()
        self.assertIn("Hayır, yanılmışım", html)
        self.assertIn("Evet, eminim", html)
        self.assertIn("Devam etmek için kaydır", html)
        self.assertIn('id="lp-alev"', html)


class EgzersizBaglantiTests(TestCase):
    """Egzersiz cevapları tekrar kuralına ve seriye işlenir; "tekrar çöz" turu işlenmez."""

    def setUp(self):
        from egzersizler.models import EgzersizOturumu
        self.user = User.objects.create_user(username="egz", password="Sifre1234")
        self.w = make_word("scatter")
        UserWordLink.objects.create(user=self.user, word=self.w)
        self.oturum = EgzersizOturumu.objects.create(user=self.user, tur="hizli", tip="anlam",
                                                     istenen=10, sorular=[])

    def test_yanlis_cevap_sifirlar_ve_seriye_sayilir(self):
        from egzersizler.kayit import cevaplari_kaydet
        seri = cevaplari_kaydet(self.user, self.oturum, "anlam", [(self.w.id, False)])
        enc = WordEncounter.objects.get(user=self.user, word=self.w)
        self.assertEqual((enc.egz_yanlis, enc.son_basarili, enc.last_mode), (1, False, "egzersiz"))
        self.assertEqual(seri["egzersiz"], 1)

    def test_tekrar_coz_turu_islenmez(self):
        from egzersizler.kayit import cevaplari_kaydet
        from egzersizler.models import EgzersizOturumu
        tekrar_turu = EgzersizOturumu.objects.create(user=self.user, tur="hizli", tip="anlam",
                                                     istenen=10, sorular=[], kaynak=self.oturum)
        self.assertIsNone(cevaplari_kaydet(self.user, tekrar_turu, "anlam", [(self.w.id, False)]))
        self.assertFalse(WordEncounter.objects.filter(user=self.user).exists())


class DilbilgisiTurleriTests(TestCase):
    """Rapor 18.36: the / I / can / hello Learn & Pass'in yeni kelime havuzuna girmez."""

    def test_yeni_havuza_girmez(self):
        from learnpass.tekrar import _yeni_havuz
        from words.testing import make_word
        the = make_word("the", pos="determiner", level="A1")
        kedi = make_word("cat", pos="noun", level="A1")
        havuz = set(_yeni_havuz(None, "A1").values_list("id", flat=True))
        self.assertIn(kedi.id, havuz)
        self.assertNotIn(the.id, havuz)


class AileAralamaTests(TestCase):
    """Aynı aileden (Word.family) kelimeler bir turda art arda gelmez."""

    def setUp(self):
        self.user = User.objects.create_user(username="aile", password="Sifre1234", cefr="B1")

    def test_yeni_kelime_turda_gorunen_ailenin_uyesini_secmez(self):
        decide = make_word("decide", level="B1", family="decide")
        decision = make_word("decision", level="B1", family="decide", siklik=7.0)
        baska = make_word("garden", level="B1", siklik=1.0)
        for tohum in range(20):
            secilen = tekrar.yeni_kelime(self.user, rng=random.Random(tohum), haric=[decide.id])
            self.assertEqual(secilen, baska)
        # Başka seçenek kalmayınca aynı aileden de gelir (oturum bitmez).
        self.assertEqual(tekrar.yeni_kelime(self.user, haric=[decide.id, baska.id]), decision)

    def test_tekrar_sirasi_aile_uyesini_arkaya_alir(self):
        t0 = timezone.now() - timedelta(days=2)
        decide = make_word("decide", level="B1", family="decide")
        decision = make_word("decision", level="B1", family="decide")
        garden = make_word("garden", level="B1")
        for w in (decision, garden):
            UserWordLink.objects.create(user=self.user, word=w)
        tekrar.kaydet(self.user, decision, U, "mine", simdi=t0)
        tekrar.kaydet(self.user, garden, U, "mine", simdi=t0)
        # decision en eski görülen: öncelikli
        WordEncounter.objects.filter(word=decision).update(last_seen_at=t0)
        WordEncounter.objects.filter(word=garden).update(last_seen_at=t0 + timedelta(hours=1))
        self.assertEqual(tekrar.siradaki_tekrar(self.user, haric=[]), decision)
        self.assertEqual(tekrar.siradaki_tekrar(self.user, haric=[decide.id]), garden)

    def test_hepsi_gorunmusse_ailesi_en_eski_gorunen_gelir(self):
        a1, a2 = make_word("act", family="act"), make_word("action", family="act")
        b1, b2 = make_word("bake", family="bake"), make_word("baker", family="bake")
        self.assertEqual(tekrar.aileye_gore_sirala([b2.id, a2.id], [a1.id, b1.id]), [a2.id, b2.id])

    def test_misafir_turu_aileleri_uzaga_dagitir(self):
        aile = [make_word(t, family="decide") for t in ("decide", "decision", "decisive")]
        digerleri = [make_word(f"word{i}") for i in range(6)]
        idler = [w.id for w in aile] + [w.id for w in digerleri]
        sira = tekrar.aileleri_arala(idler)
        self.assertEqual(sorted(sira), sorted(idler))
        yerler = sorted(sira.index(w.id) for w in aile)
        self.assertGreaterEqual(min(b - a for a, b in zip(yerler, yerler[1:])), 3)

    def test_oturumda_art_arda_ayni_aile_gelmez(self):
        """Uçtan uca: ilk kart decide ise ikinci kart decision olmaz."""
        decide = make_word("decide", level="B1", family="decide", siklik=7.0)
        make_word("decision", level="B1", family="decide", siklik=7.0)
        garden = make_word("garden", level="B1", siklik=1.0)
        self.client.force_login(self.user)
        with mock.patch("learnpass.selection.yeni_orani", return_value=1.0):
            self.client.get(reverse("learn_pass_run", kwargs={"mode": "karma"}))
            oturum = self.client.session
            oturum["learnpass_shown_karma"] = [decide.id]
            oturum.save()
            cevap = self.client.post(reverse("learn_pass_verdict"), json.dumps(
                {"mode": "karma", "word_id": decide.id, "verdict": U, "kaynak": "new"}),
                content_type="application/json")
        self.assertEqual(cevap.json()["card"]["id"], garden.id)
