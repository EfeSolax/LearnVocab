"""
Öğren-Geç testleri.

En çok korunması gereken kurallar (rapor 6.1, 2.3): kullanıcı kararını
ANLAMI GÖRMEDEN verir; her kaydırma anında kaydedilir; bilinmeyenler listeye
kendiliğinden girmez; misafir için hiçbir şey kaydedilmez.
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
    """Uçtan uca akış: kaydırma -> anında kayıt -> sonraki kart (rapor 6.1)."""

    def setUp(self):
        self.user = User.objects.create_user(username="akis", password="Sifre1234")
        self.client.login(username="akis", password="Sifre1234")
        self.word = kelime_yap("candidate")
        self.other = kelime_yap("another")

    def _verdict(self, word, verdict, mode="new", kaynak=None):
        govde = {"word_id": word.id, "verdict": verdict, "mode": mode}
        if kaynak:
            govde["kaynak"] = kaynak
        return self.client.post(reverse("learn_pass_verdict"), data=json.dumps(govde),
                                content_type="application/json")

    def _undo(self, mode="new"):
        return self.client.post(reverse("learn_pass_undo"), data=json.dumps({"mode": mode}),
                                content_type="application/json")

    def test_her_kaydirma_aninda_kaydedilir(self):
        """Oturum yarıda kalsa da kayıp olmasın: tek kaydırma = kayıt + günlük satırı."""
        cevap = self._verdict(self.word, "known")
        self.assertEqual(cevap.status_code, 200)
        kayit = WordEncounter.objects.get(user=self.user, word=self.word)
        self.assertEqual(kayit.last_verdict, WordEncounter.KNOWN)
        self.assertEqual(EncounterLog.objects.filter(user=self.user, word=self.word).count(), 1)
        self.assertEqual(cevap.json()["stats"], {"seen": 1, "known": 1, "unknown": 0})

    def test_bilinmeyen_listeye_kendiliginden_eklenmez(self):
        cevap = self._verdict(self.word, "unknown")
        self.assertFalse(UserWordLink.objects.filter(user=self.user, word=self.word).exists())
        kayit = WordEncounter.objects.get(user=self.user, word=self.word)
        self.assertTrue(kayit.listeye_sorulacak)
        self.assertEqual(cevap.json()["stats"]["unknown"], 1)

    def test_listedeki_bilinmeyen_sorulmaz(self):
        UserWordLink.objects.create(user=self.user, word=self.word)
        self._verdict(self.word, "unknown", mode="mine")
        self.assertFalse(WordEncounter.objects.get(user=self.user, word=self.word).listeye_sorulacak)

    def test_sonradan_biliyorum_denirse_soru_isareti_kalkar(self):
        self._verdict(self.word, "unknown")
        WordEncounter.record(self.user, self.word, WordEncounter.KNOWN, "new")
        self.assertFalse(WordEncounter.objects.get(user=self.user, word=self.word).listeye_sorulacak)

    def test_kart_listede_olup_olmadigini_tasir(self):
        """Listedeki kelime oturum sonunda "ekleyelim mi?" diye sorulmamalı."""
        from learnpass.views import card_payload

        UserWordLink.objects.create(user=self.user, word=self.word)
        self.assertTrue(card_payload(self.word, self.user, "new")["listede"])
        self.assertFalse(card_payload(self.other, self.user, "new")["listede"])

    def test_karar_kartin_kaynagiyla_kaydedilir(self):
        self._verdict(self.word, "known", mode="karma", kaynak="mine")
        self.assertEqual(WordEncounter.objects.get(user=self.user, word=self.word).last_mode, "mine")

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

    def test_undo_reverts_the_record(self):
        self._verdict(self.word, "unknown")
        cevap = self._undo()
        self.assertEqual(cevap.status_code, 200)
        self.assertFalse(WordEncounter.objects.filter(user=self.user, word=self.word).exists())
        self.assertFalse(EncounterLog.objects.filter(user=self.user, word=self.word).exists())
        self.assertEqual(cevap.json()["card"]["id"], self.word.id)
        self.assertEqual(cevap.json()["stats"]["seen"], 0)

    def test_undo_restores_the_previous_verdict_instead_of_deleting(self):
        """Kelime daha önce görülmüşse geri al onu silmemeli, eski hâline döndürmeli."""
        self._verdict(self.word, "unknown")
        self._verdict(self.word, "known")
        self._undo()
        kayit = WordEncounter.objects.get(user=self.user, word=self.word)
        self.assertEqual(kayit.last_verdict, WordEncounter.UNKNOWN)
        self.assertFalse(kayit.is_learned)
        self.assertTrue(kayit.listeye_sorulacak)

    def test_undo_without_history_is_rejected(self):
        self.assertEqual(self._undo().status_code, 400)

    def test_undo_does_not_remove_a_word_that_was_already_in_the_list(self):
        UserWordLink.objects.create(user=self.user, word=self.word)
        self._verdict(self.word, "unknown", mode="mine")
        self._undo(mode="mine")
        self.assertTrue(UserWordLink.objects.filter(user=self.user, word=self.word).exists())

    def test_ayni_turda_ayni_kart_tekrar_gelmez(self):
        """Kendi listesinde bilinmeyen kelime havuzda kalır ama aynı turda yeniden gelmemeli."""
        for k in (self.word, self.other):
            UserWordLink.objects.create(user=self.user, word=k)
        self.client.get(reverse("learn_pass_run", kwargs={"mode": "mine"}))
        ilk = self.client.session["learnpass_shown_mine"][0]
        kelime = Word.objects.get(id=ilk)
        kart = self._verdict(kelime, "unknown", mode="mine").json()["card"]
        self.assertNotEqual(kart["id"], ilk)


class BilinmeyenlerTests(TestCase):
    """Oturum sonu "listene ekleyelim mi?" ve "geçen sefer" kartı."""

    def setUp(self):
        self.user = User.objects.create_user(username="bilmeyen", password="Sifre1234")
        self.client.login(username="bilmeyen", password="Sifre1234")
        self.a = kelime_yap("alpha")
        self.b = kelime_yap("bravo")
        for k in (self.a, self.b):
            self.client.post(reverse("learn_pass_verdict"),
                             data=json.dumps({"word_id": k.id, "verdict": "unknown", "mode": "karma",
                                              "kaynak": "new"}),
                             content_type="application/json")

    def _islem(self, islem, idler, **ek):
        return self.client.post(reverse("learn_pass_bilinmeyenler"),
                                data=json.dumps({"islem": islem, "word_ids": idler, **ek}),
                                content_type="application/json")

    def test_oturum_sonu_toplu_ekleme(self):
        cevap = self._islem("ekle", [self.a.id, self.b.id])
        self.assertEqual(cevap.status_code, 200)
        self.assertEqual(sorted(cevap.json()["eklenenler"]), sorted([self.a.id, self.b.id]))
        self.assertEqual(UserWordLink.objects.filter(user=self.user).count(), 2)
        self.assertFalse(WordEncounter.objects.filter(user=self.user, listeye_sorulacak=True).exists())

    def test_toplu_ekleme_geri_alinir(self):
        eklenenler = self._islem("ekle", [self.a.id, self.b.id]).json()["eklenenler"]
        self._islem("geri_al", [self.a.id, self.b.id], eklenenler=eklenenler)
        self.assertFalse(UserWordLink.objects.filter(user=self.user).exists())
        self.assertEqual(selection.bekleyen_bilinmeyenler(self.user).count(), 2)

    def test_simdilik_hayir_bir_daha_sormaz(self):
        self._islem("gec", [self.a.id, self.b.id])
        self.assertFalse(UserWordLink.objects.filter(user=self.user).exists())
        self.assertEqual(selection.bekleyen_bilinmeyenler(self.user).count(), 0)

    def test_karsilasilmamis_kelime_eklenemez(self):
        """Uç, keyfî kelimeleri listeye eklemenin arka kapısı olmamalı."""
        yabanci = kelime_yap("charlie")
        cevap = self._islem("ekle", [yabanci.id])
        self.assertEqual(cevap.json()["eklenenler"], [])
        self.assertFalse(UserWordLink.objects.filter(user=self.user, word=yabanci).exists())

    def test_gecersiz_islem_reddedilir(self):
        self.assertEqual(self._islem("sil", [self.a.id]).status_code, 400)

    def test_gecen_sefer_karti_acilista_cikar(self):
        """Oturum yarıda bırakıldı (soru cevaplanmadı): açılışta hatırlatılır."""
        html = self.client.get(reverse("learn_pass_page")).content.decode()
        self.assertIn("Geçen sefer bilmediğin 2 kelime", html)
        self.assertIn("alpha", html)

    def test_cevaplaninca_gecen_sefer_karti_kaybolur(self):
        self._islem("ekle", [self.a.id])
        html = self.client.get(reverse("learn_pass_page")).content.decode()
        self.assertIn("Geçen sefer bilmediğin 1 kelime", html)
        self._islem("gec", [self.b.id])
        html = self.client.get(reverse("learn_pass_page")).content.decode()
        self.assertNotIn("Geçen sefer bilmediğin", html)

    def test_listeye_baska_yoldan_eklenen_sorulmaz(self):
        UserWordLink.objects.create(user=self.user, word=self.a)
        self.assertEqual(list(selection.bekleyen_bilinmeyenler(self.user)), [self.b])

    def test_misafir_ucu_kullanamaz(self):
        self.client.logout()
        self.assertEqual(self._islem("ekle", [self.a.id]).status_code, 403)

    def test_zorlanilanlar(self):
        """Listem > Zorlandıklarım: L&P'de bilmiyorum denenler."""
        import learnpass

        bilinen = kelime_yap("delta")
        WordEncounter.record(self.user, bilinen, WordEncounter.KNOWN, "new")
        zor = set(learnpass.zorlanilanlar(self.user))
        self.assertEqual(zor, {self.a, self.b})
        baska = User.objects.create_user(username="baskasi", password="Sifre1234")
        self.assertFalse(learnpass.zorlanilanlar(baska).exists())


class OranTests(TestCase):
    """Yeni/tekrar oranı: ~%30 yeni, tekrar birikirse azalır (rapor 6.1)."""

    def setUp(self):
        self.user = User.objects.create_user(username="oran", password="Sifre1234")

    def test_varsayilan_oran(self):
        self.assertAlmostEqual(selection.yeni_orani(self.user, bekleyen_tekrar=5), 0.30)

    def test_tekrar_birikince_yeni_orani_azalir(self):
        esik = selection.TEKRAR_BIRIKME_ESIGI
        az = selection.yeni_orani(self.user, bekleyen_tekrar=esik * 2)
        cok = selection.yeni_orani(self.user, bekleyen_tekrar=esik * 20)
        self.assertLess(az, 0.30)
        self.assertLess(cok, az)
        self.assertGreaterEqual(cok, selection.EN_AZ_YENI_ORANI)

    def test_karma_secim_orana_uyar(self):
        for i in range(15):
            UserWordLink.objects.create(user=self.user, word=kelime_yap(f"mine{i}"))
        for i in range(15):
            kelime_yap(f"new{i}")
        rng = random.Random(6)
        sayac = {"mine": 0, "new": 0}
        for _ in range(400):
            _, kaynak = selection.pick_mixed(self.user, rng=rng, oran=0.30)
            sayac[kaynak] += 1
        self.assertAlmostEqual(sayac["new"] / 400, 0.30, delta=0.07)

    def test_bir_havuz_bossa_oburune_gecer(self):
        kelime_yap("onlynew")
        kelime, kaynak = selection.pick_mixed(self.user, oran=0.0)
        self.assertEqual((kelime.text, kaynak), ("onlynew", "new"))

    def test_ayar_alani_varsa_okunur(self):
        from types import SimpleNamespace

        sahte = SimpleNamespace(mysettings=SimpleNamespace(learnpass_yeni_orani=50))
        self.assertAlmostEqual(selection.kullanici_yeni_orani(sahte), 0.5)


class HazirListeBaglantiTests(TestCase):
    """"Bu listeyle çalış" bağlantı noktası: modül yoksa seviye tabanlı kaynak."""

    def setUp(self):
        self.user = User.objects.create_user(username="hazir", password="Sifre1234")

    def test_modul_yoksa_seviyeye_duser(self):
        import sys
        from unittest import mock

        with mock.patch.dict(sys.modules, {"words.hazir_liste": None}):
            self.assertIsNone(selection.yeni_kelime_havuzu(self.user))

    def test_aktif_liste_varsa_ondan_gelir(self):
        import sys
        import types
        from unittest import mock

        listede = kelime_yap("listword", level="C1")
        kelime_yap("otherword", level="B1")
        sahte = types.ModuleType("words.hazir_liste")
        sahte.aktif_liste = lambda user: Word.objects.filter(id=listede.id)
        with mock.patch.dict(sys.modules, {"words.hazir_liste": sahte}):
            for _ in range(5):
                self.assertEqual(selection.pick_new_word(self.user), listede)


class LearnPassPageTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="sayfa", password="Sifre1234")
        self.word = kelime_yap()

    def test_acilis_ekrani(self):
        self.client.login(username="sayfa", password="Sifre1234")
        html = self.client.get(reverse("learn_pass_page")).content.decode()
        self.assertIn("Hemen Başla", html)
        self.assertIn(reverse("learn_pass_run", kwargs={"mode": "karma"}), html)
        self.assertIn("Neden işe yarar", html)
        self.assertIn("data-seri-yeri", html)
        self.assertIn("%70 tekrar", html)
        self.assertIn(reverse("user_profile"), html)   # oran notu -> ayarlar
        self.assertNotIn('data-giris-gerekli="', html)

    def test_misafir_acilis_ekrani_seviye_secer(self):
        html = self.client.get(reverse("learn_pass_page")).content.decode()
        self.assertIn("Hemen Başla", html)
        self.assertIn('name="seviye"', html)
        self.assertIn('<option value="B1" selected>', html)
        self.assertIn('data-giris-gerekli="egzersiz"', html)

    def test_unknown_mode_falls_back_to_the_picker(self):
        self.client.login(username="sayfa", password="Sifre1234")
        cevap = self.client.get(reverse("learn_pass_run", kwargs={"mode": "sacma"}))
        self.assertRedirects(cevap, reverse("learn_pass_page"))

    def test_kartta_tur_etiketi_yok(self):
        """Gramer etiketi yalnızca Sözlük kartında (rapor 12.1)."""
        from learnpass.views import card_payload

        fiil = kelime_yap("decide", pos="verb", meaning="karar vermek")
        kart = card_payload(fiil, self.user)
        self.assertNotIn("pos", kart)
        self.assertEqual(kart["meanings"], ["karar vermek"])
        self.client.login(username="sayfa", password="Sifre1234")
        html = self.client.get(reverse("learn_pass_run", kwargs={"mode": "karma"})).content.decode()
        for etiket in ("fiil", "isim", '"pos"', "noun", "verb"):
            self.assertNotIn(etiket, html)

    def test_kart_ekrani_yapisi(self):
        self.client.login(username="sayfa", password="Sifre1234")
        html = self.client.get(reverse("learn_pass_run", kwargs={"mode": "karma"})).content.decode()
        self.assertIn("Düşündüğün bu muydu?", html)
        self.assertIn("data-kapibara-yeri", html)
        self.assertIn('id="lp-acilim" class="lp-acilim"', html)   # kapalı başlıyor
        self.assertIn("Fredoka", html)
        self.assertIn(reverse("learn_pass_verdict"), html)

    def test_exercise_tabs_appear_on_both_pages(self):
        self.client.login(username="sayfa", password="Sifre1234")
        for url in (reverse("learn_pass_page"), reverse("exercises_page")):
            with self.subTest(url=url):
                html = self.client.get(url, follow=True).content.decode()
                self.assertIn("Learn &amp; Pass", html)
                self.assertNotIn("Öğren-Geç", html)
                self.assertIn("Egzersizler", html)
                self.assertIn(reverse("exercises_page"), html)

    def test_exercises_menu_opens_learn_pass_first(self):
        self.client.login(username="sayfa", password="Sifre1234")
        html = self.client.get(reverse("index")).content.decode()
        basla = html.index('<header id="navbar"')
        navbar = html[basla:html.index("</header>", basla)]
        self.assertIn(reverse("learn_pass_page"), navbar)


class MisafirTests(TestCase):
    """Girişsiz ziyaretçi: yalnızca kaydırır, hiçbir şey kaydedilmez (rapor 2.3)."""

    def setUp(self):
        for seviye in ("A2", "B1", "B2"):
            for i in range(25):
                kelime_yap(f"g{seviye}{i}", level=seviye)

    def _kartlar(self, cevap):
        html = cevap.content.decode()
        basla = html.index('id="lp-kartlar"')
        ham = html[html.index(">", basla) + 1:html.index("</script>", basla)]
        return json.loads(ham)

    def test_misafir_kart_ekranini_acabilir(self):
        cevap = self.client.get(reverse("learn_pass_run", kwargs={"mode": "karma"}))
        self.assertEqual(cevap.status_code, 200)
        self.assertNotIn("önce giriş yapın", cevap.content.decode())
        kartlar = self._kartlar(cevap)
        self.assertEqual(len(kartlar), 20)
        self.assertTrue(all(Word.objects.get(id=k["id"]).cefr == "B1" for k in kartlar))

    def test_seviyeni_sec_parametresi(self):
        cevap = self.client.get(reverse("learn_pass_run", kwargs={"mode": "karma"}) + "?seviye=a2")
        self.assertTrue(all(Word.objects.get(id=k["id"]).cefr == "A2" for k in self._kartlar(cevap)))

    def test_misafir_hicbir_sey_kaydetmez(self):
        from django.contrib.sessions.models import Session

        self.client.get(reverse("learn_pass_page"))
        cevap = self.client.get(reverse("learn_pass_run", kwargs={"mode": "karma"}))
        html = cevap.content.decode()
        self.assertNotIn(reverse("learn_pass_verdict"), html)   # tarayıcı istek atmaz
        kelime = Word.objects.first()
        self.assertEqual(self.client.post(
            reverse("learn_pass_verdict"),
            data=json.dumps({"word_id": kelime.id, "verdict": "unknown"}),
            content_type="application/json").status_code, 403)
        self.assertEqual(WordEncounter.objects.count(), 0)
        self.assertEqual(EncounterLog.objects.count(), 0)
        self.assertEqual(UserWordLink.objects.count(), 0)
        self.assertEqual(Session.objects.count(), 0)

    def test_misafir_sayfasi_az_sorguyla_acilir(self):
        with self.assertNumQueries(4):   # id listesi + kelimeler + anlamlar + örnekler
            self.client.get(reverse("learn_pass_run", kwargs={"mode": "karma"}))

    def test_misafirin_kendi_listesi_yok(self):
        cevap = self.client.get(reverse("learn_pass_run", kwargs={"mode": "mine"}))
        self.assertRedirects(cevap, reverse("learn_pass_run", kwargs={"mode": "karma"}))


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
