"""
Seviye testi (rapor 7, 18.27; D4, D8) ve kullanıcı seviyesi yardımcısı.
"""

import json
import random
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from users.models import User
from users.seviye import kullanici_seviyesi, seviyesi_belli_mi
from words.models import UserWordLink, Word
from words.testing import make_word

from . import secim, tahmin
from .duzeltme import seviyeyi_sessizce_duzelt
from .models import OkumaSorusu, SeviyeKelimesi, SeviyeTestiSonucu
from .views import OTURUM_ANAHTARI

SIFRE = "Sifre1234"
# Seviye başına harf öneki: kelimeler yalnızca a–z olmalı (secim._YAZIM).
ONEK = {"A1": "aa", "A2": "ab", "B1": "ba", "B2": "bb", "C1": "ca", "C2": "cb"}


# Test kelimeleri uydurma yazımlar ("aaab"): wordfreq sıklığı 0, bant dışı
# kalırlardı. Tablo boşken yapılan anında seçimde sıklık bandı kapatılır.
wordfreq_yok = mock.patch("seviye.secim.zipf_olcer", new=lambda: None)


def _harfler(i):
    return chr(97 + i // 26) + chr(97 + i % 26)


def kelimeler_kur(adet=12):
    """Her seviyeden `adet` gerçek (veritabanında) kelime: {seviye: [Word]}."""
    sonuc = {}
    for seviye, onek in ONEK.items():
        sonuc[seviye] = [make_word(f"{onek}{_harfler(i)}", level=seviye, forms=False)
                         for i in range(adet)]
    return sonuc


# ----------------------------------------------------------------------
# Kullanıcı seviyesi: tek kaynak
# ----------------------------------------------------------------------

class KullaniciSeviyesiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="sev", password=SIFRE)

    def test_varsayilan_b1(self):
        self.assertEqual(kullanici_seviyesi(self.user), "B1")      # level=1, cefr boş
        self.assertEqual(kullanici_seviyesi(AnonymousUser()), "B1")
        self.assertEqual(kullanici_seviyesi(None), "B1")
        self.assertFalse(seviyesi_belli_mi(self.user))

    def test_eski_kur_eslenir(self):
        for kur, cefr in ((101, "A1"), (201, "A2"), (301, "B1"), (401, "B2"), (501, "C1")):
            self.user.level = kur
            self.assertEqual(kullanici_seviyesi(self.user), cefr)
        self.assertFalse(seviyesi_belli_mi(self.user))

    def test_alan_eski_kurdan_once_gelir(self):
        self.user.level = 101
        self.user.cefr = "C1"
        self.assertEqual(kullanici_seviyesi(self.user), "C1")
        self.assertTrue(seviyesi_belli_mi(self.user))

    def test_uc_yer_ayni_yardimciyi_kullanir(self):
        from egzersizler import seviye as egz
        from words import arama
        self.user.cefr = "A2"
        self.assertEqual(egz.kullanici_seviyesi(self.user), "A2")
        self.assertEqual(arama.kullanici_seviyesi(self.user), "A2")
        self.assertIs(egz.kullanici_seviyesi, kullanici_seviyesi)
        self.assertIs(arama.kullanici_seviyesi, kullanici_seviyesi)


# ----------------------------------------------------------------------
# Tahmin kuralı
# ----------------------------------------------------------------------

def _e(bilinen, gosterilen=40):
    return {"gosterilen": gosterilen, "bilinen": bilinen}


# ----------------------------------------------------------------------
# D8: ekran kelimelerinin seçimi
# ----------------------------------------------------------------------

@wordfreq_yok
class SecimTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.k = kelimeler_kur(6)
        # Elenmesi gerekenler
        make_word("Paris", level="A1", forms=False)                    # büyük harf
        make_word("ice cream", level="A1", forms=False)                # çok sözcüklü
        make_word("aabzz", level="A1", sentences=[], forms=False)      # örneksiz
        make_word("xxdog", level="C1", forms=False)                    # daha kolay türü var
        make_word("xxdog", pos="verb", level="A2", forms=False)
        make_word("aabyy", level="A2", is_base=False, forms=False)     # ortak sözlükte değil
        make_word("aabxx", level="A2", meaning="müstehcen söz", forms=False)   # hassas

    def test_adaylar_kurallara_uyar(self):
        adaylar = secim.adaylar()
        metinler = {a.text for a in adaylar}
        for elenen in ("Paris", "ice cream", "aabzz", "aabyy", "aabxx"):
            self.assertNotIn(elenen, metinler)
        # "xxdog" yalnızca en kolay seviyesiyle (A2) ve bir kez
        dog = [a for a in adaylar if a.text == "xxdog"]
        self.assertEqual([(a.cefr, a.ekran) for a in dog], [("A2", 1)])
        self.assertEqual(len(metinler), len(adaylar))

    def test_uydurma_kelime_yok(self):
        adaylar = secim.adaylar()
        idler = {a.word_id for a in adaylar}
        self.assertEqual(Word.objects.filter(id__in=idler, isBaseWord=True).count(), len(idler))
        for ekran in (1, 2, 3):
            ids = secim.ekran_kelimeleri(ekran, random.Random(ekran))
            self.assertTrue(ids)
            self.assertEqual(Word.objects.filter(id__in=ids, isBaseWord=True).count(), len(ids))

    def test_seviyeler_dogru_ekranda(self):
        seviyeler = dict(Word.objects.values_list("id", "cefr"))
        for ekran, beklenen in secim.EKRAN_SEVIYELERI.items():
            for wid in secim.ekran_kelimeleri(ekran, random.Random(1)):
                self.assertIn(seviyeler[wid], beklenen)

    def test_zipf_bandi(self):
        """Sıklık Word.siklik alanından okunur (manage.py siklik_hesapla)."""
        Word.objects.filter(text__endswith="aa").update(siklik=7.0)   # çok sık: bant dışı
        Word.objects.exclude(text__endswith="aa").update(siklik=4.2)
        adaylar = secim.adaylar()
        self.assertFalse(any(a.text.endswith("aa") and a.cefr in ("A1", "A2") for a in adaylar))
        self.assertTrue(all(a.zipf is not None for a in adaylar))

    def test_deterministik(self):
        self.assertEqual([a.text for a in secim.adaylar()], [a.text for a in secim.adaylar()])

    def test_iki_seviyeli_ekranda_esit_pay(self):
        ids = secim.ekran_kelimeleri(1, random.Random(3), adet=6)
        seviyeler = list(Word.objects.filter(id__in=ids).values_list("cefr", flat=True))
        self.assertEqual(sorted(seviyeler), ["A1"] * 3 + ["A2"] * 3)

    def test_tablo_doluysa_tablo_kullanilir(self):
        w = self.k["B1"][0]
        SeviyeKelimesi.objects.create(ekran=2, word=w, cefr="B1")
        self.assertEqual(secim.ekran_kelimeleri(2, random.Random(0)), [w.id])

    def test_komut_dry_run_yazmaz_gercek_yazar(self):
        with tempfile.TemporaryDirectory() as klasor:
            yol = Path(klasor) / "secim.json"
            cikti = StringIO()
            call_command("seviye_kelimeleri_sec", "--dry-run", "--json", str(yol), stdout=cikti)
            self.assertEqual(SeviyeKelimesi.objects.count(), 0)
            veri = json.loads(yol.read_text(encoding="utf-8"))
            self.assertEqual(len(veri), len(secim.adaylar()))
            self.assertIn("(dry-run)", cikti.getvalue())
        call_command("seviye_kelimeleri_sec", "--wordfreq-yok", stdout=StringIO())
        self.assertEqual(SeviyeKelimesi.objects.count(), len(secim.adaylar()))


# ----------------------------------------------------------------------
# Akış
# ----------------------------------------------------------------------

@wordfreq_yok
class SeviyeTestiAkisTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.k = kelimeler_kur(12)

    def setUp(self):
        self.user = User.objects.create_user(username="testci", password=SIFRE)
        self.client.login(username="testci", password=SIFRE)

    def _durum(self):
        return self.client.session[OTURUM_ANAHTARI]

    def _gonder(self, ekran, oran):
        gosterilen = self._durum()["gosterilen"][str(ekran)]
        bilinen = gosterilen[:round(len(gosterilen) * oran)]
        return self.client.post(reverse("seviye_ekran", args=[ekran]), {"bilinen": bilinen}), \
            gosterilen, bilinen

    def test_girissiz_aciklama_ekrani(self):
        self.client.logout()
        cevap = self.client.get(reverse("seviye_testi"))
        self.assertEqual(cevap.status_code, 200)
        self.assertContains(cevap, "Seviye testi")

    def test_giris_sayfasi_kacis_yollari(self):
        cevap = self.client.get(reverse("seviye_testi"))
        self.assertContains(cevap, "Seviyemi kendim seçeyim")
        self.assertContains(cevap, "Şimdi değil")

    def test_kolay_ekranda_az_bilinirse_zor_ekran_gosterilmez(self):
        self.client.post(reverse("seviye_basla"))
        cevap, gosterilen, bilinen = self._gonder(1, 0.25)
        self.assertRedirects(cevap, reverse("seviye_sonuc"))
        sonuc = SeviyeTestiSonucu.objects.get(user=self.user)
        self.assertEqual(list(sonuc.ekranlar), ["1"])
        self.assertEqual(sonuc.tahmin, "A1")
        self.user.refresh_from_db()
        self.assertEqual(self.user.cefr, "A1")

    def test_ilk_liste_dokunulmayanlardir(self):
        onceden = Word.objects.get(text=ONEK["A1"] + _harfler(0))
        UserWordLink.objects.create(user=self.user, word=onceden)
        self.client.post(reverse("seviye_basla"))
        _, gosterilen, bilinen = self._gonder(1, 0.25)
        dokunulmayan = [w for w in gosterilen if w not in bilinen]
        sonuc = SeviyeTestiSonucu.objects.get(user=self.user)
        self.assertEqual(sonuc.eklenen, [w for w in dokunulmayan if w != onceden.id])
        listede = set(UserWordLink.objects.filter(user=self.user).values_list("word_id", flat=True))
        self.assertEqual(listede, set(dokunulmayan) | {onceden.id})
        self.assertFalse(listede & set(bilinen) - {onceden.id})

        html = self.client.get(reverse("seviye_sonuc")).content.decode()
        self.assertIn(f"{len(sonuc.eklenen)} kelime listene eklendi", html)
        self.assertIn("Geri al", html)

    def test_geri_al_yalnizca_test_eklediklerini_cikarir(self):
        onceden = Word.objects.get(text=ONEK["A2"] + _harfler(0))
        UserWordLink.objects.create(user=self.user, word=onceden)
        self.client.post(reverse("seviye_basla"))
        self._gonder(1, 0)
        cevap = self.client.post(reverse("seviye_geri_al"), HTTP_X_REQUESTED_WITH="fetch")
        self.assertTrue(cevap.json()["ok"])
        self.assertEqual(list(UserWordLink.objects.filter(user=self.user)
                              .values_list("word_id", flat=True)), [onceden.id])
        self.assertTrue(SeviyeTestiSonucu.objects.get(user=self.user).geri_alindi)
        self.assertNotIn("listene eklendi", self.client.get(reverse("seviye_sonuc")).content.decode())

    def test_tam_akis_b2_ve_bos_d4_havuzunda_okuma_atlanir(self):
        self.client.post(reverse("seviye_basla"))
        cevap, *_ = self._gonder(1, 1)
        self.assertRedirects(cevap, reverse("seviye_ekran", args=[2]))
        cevap, *_ = self._gonder(2, 0.75)
        self.assertRedirects(cevap, reverse("seviye_ekran", args=[3]))
        cevap, *_ = self._gonder(3, 0.6)   # tam %60: geçilemez (üstü gerekir)
        self.assertRedirects(cevap, reverse("seviye_sonuc"))   # okuma havuzu boş
        sonuc = SeviyeTestiSonucu.objects.get(user=self.user)
        self.assertEqual(sonuc.tahmin, "B2")                    # son geçilen ekranın üstü
        self.assertIsNone(sonuc.okuma)
        # İlk liste B2'nin ekranından (2. ekran: B1–B2) dokunulmayanlar
        durum_2 = sonuc.ekranlar["2"]
        self.assertEqual(len(sonuc.eklenen), durum_2["gosterilen"] - durum_2["bilinen"])
        self.assertNotIn(OTURUM_ANAHTARI, self.client.session)

    def test_ekran_sayfasi_yalnizca_kelimeyi_gosterir(self):
        self.client.post(reverse("seviye_basla"))
        html = self.client.get(reverse("seviye_ekran", args=[1])).content.decode()
        self.assertIn('name="bilinen"', html)
        for wid in self._durum()["gosterilen"]["1"]:
            self.assertIn(f'value="{wid}"', html)
        self.assertNotIn("isim", html.split('data-seviye-ekrani', 1)[1].split("</form>")[0])

    def test_baska_ekran_kelimesi_sayilmaz(self):
        self.client.post(reverse("seviye_basla"))
        self.client.post(reverse("seviye_ekran", args=[1]), {"bilinen": [999999, "x"]})
        sonuc = SeviyeTestiSonucu.objects.get(user=self.user)
        self.assertEqual(sonuc.ekranlar["1"]["bilinen"], 0)

    def test_oturum_yokken_ekran_girise_doner(self):
        self.assertRedirects(self.client.get(reverse("seviye_ekran", args=[2])),
                             reverse("seviye_testi"))

    def test_kendim_secerim(self):
        cevap = self.client.post(reverse("seviye_sec"), {"seviye": "B2"})
        self.assertRedirects(cevap, reverse("index"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.cefr, "B2")
        self.client.post(reverse("seviye_sec"), {"seviye": "Z9"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.cefr, "B2")


@wordfreq_yok


class OkumaYukleKomutuTests(TestCase):
    def _yukle(self, kayitlar, *secenekler):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(kayitlar, f)
        cikti = StringIO()
        call_command("seviye_okuma_yukle", f.name, *secenekler, stdout=cikti)
        Path(f.name).unlink()
        return cikti.getvalue()

    def _kayit(self, **degisen):
        kayit = {"cefr": "A2",
                 "metin": "Tom works in a bakery. He starts at five. He makes bread. He goes home at two.",
                 "dogru": "Tom is a baker who starts early.",
                 "celdiriciler": ["Tom buys bread.", "Tom hates his job.", "Tom sleeps at work."],
                 "denetlendi": True}
        kayit.update(degisen)
        return kayit

    def test_dry_run_yazmaz(self):
        cikti = self._yukle([self._kayit()], "--dry-run")
        self.assertIn("1 yeni", cikti)
        self.assertEqual(OkumaSorusu.objects.count(), 0)

    def test_yukler_ve_gunceller(self):
        self._yukle([self._kayit()])
        self._yukle([self._kayit(dogru="Tom is an early-rising baker.")])
        self.assertEqual(OkumaSorusu.objects.count(), 1)
        self.assertEqual(OkumaSorusu.objects.get().dogru, "Tom is an early-rising baker.")

    def test_hatali_kayitlar_atlanir(self):
        cikti = self._yukle([
            self._kayit(cefr="Z9"),
            self._kayit(metin="Too short."),
            self._kayit(celdiriciler=["only one"]),
            self._kayit(celdiriciler=["Tom is a baker who starts early.", "x y"]),
        ])
        self.assertIn("4 atlandı", cikti)
        self.assertEqual(OkumaSorusu.objects.count(), 0)


# ----------------------------------------------------------------------
# Davet kartı
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# Tahmin kuralı (rapor 18.27)
# ----------------------------------------------------------------------

def _e(*oranlar):
    return {str(i + 1): {"gosterilen": 40, "bilinen": round(40 * o)} for i, o in enumerate(oranlar)}


class TahminKuraliTests(TestCase):
    def test_gecmek_icin_yuzde_60_in_ustu(self):
        self.assertFalse(tahmin.gecti_mi({"gosterilen": 40, "bilinen": 24}))   # tam %60
        self.assertTrue(tahmin.gecti_mi({"gosterilen": 40, "bilinen": 25}))
        self.assertIsNone(tahmin.sonraki_ekran(1, {"gosterilen": 40, "bilinen": 24}))
        self.assertEqual(tahmin.sonraki_ekran(1, {"gosterilen": 40, "bilinen": 25}), 2)

    def test_efenin_dort_ornegi_sorulacak_seviyeler(self):
        self.assertEqual(tahmin.sorulacak_seviyeler(_e(0.3)), ["A1", "A2"])
        self.assertEqual(tahmin.sorulacak_seviyeler(_e(0.9, 0.3)), ["A2", "B1"])
        self.assertEqual(tahmin.sorulacak_seviyeler(_e(0.9, 0.9, 0.3)), ["A2", "B2", "C1"])
        self.assertEqual(tahmin.sorulacak_seviyeler(_e(0.9, 0.9, 0.9)), ["A2", "B2", "C2"])

    def test_sonuc_dogru_cevaplanan_en_yuksek_seviye(self):
        sorulan = ["A2", "B1"]
        self.assertEqual(tahmin.sonuc_seviyesi("A2", sorulan, ["A2", "B1"]), "B1")
        self.assertEqual(tahmin.sonuc_seviyesi("A2", sorulan, ["A2"]), "A2")
        self.assertEqual(tahmin.sonuc_seviyesi("A2", sorulan, []), "A2")   # sorulan en düşük
        self.assertEqual(tahmin.sonuc_seviyesi("A1", ["A1", "A2"], []), "A1")

    def test_soru_yoksa_kelime_tahmini(self):
        self.assertEqual(tahmin.kelime_tahmini(_e(0.3)), "A1")
        self.assertEqual(tahmin.kelime_tahmini(_e(0.9, 0.3)), "A2")
        self.assertEqual(tahmin.kelime_tahmini(_e(0.9, 0.9, 0.9)), "C2")
        self.assertEqual(tahmin.sonuc_seviyesi("B2", [], []), "B2")

    def test_ilk_liste_seviyenin_ekranindaki_dokunulmayanlar(self):
        self.assertEqual(tahmin.ilk_liste("B2", {"1": [1, 2], "2": [3, 4, 5]}, {"2": [4]}), [3, 5])
        self.assertEqual(tahmin.ilk_liste("C1", {"1": [1, 2], "2": [3, 4]}, {"2": [4]}), [3])


class OkumaKismiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.k = kelimeler_kur(24)
        for seviye in ("A1", "A2", "B1", "B2", "C1", "C2"):
            OkumaSorusu.objects.create(cefr=seviye, metin=f"Paragraph {seviye}.", dogru=f"Doğru {seviye}",
                                       celdiriciler=["Yanlış 1", "Yanlış 2", "Yanlış 3"],
                                       denetlendi=True, anahtar=f"k{seviye}")

    def setUp(self):
        self.user = User.objects.create_user(username="okur", password=SIFRE)
        self.client.login(username="okur", password=SIFRE)

    def _ekran(self, ekran, oran):
        gosterilen = self.client.session[OTURUM_ANAHTARI]["gosterilen"][str(ekran)]
        return self.client.post(reverse("seviye_ekran", args=[ekran]),
                                {"bilinen": gosterilen[:round(len(gosterilen) * oran)]})

    def _okuma(self, dogru_seviyeler):
        sorular = self.client.session[OTURUM_ANAHTARI]["okuma"]
        veri = {f"soru_{s['id']}": (f"Doğru {s['cefr']}" if s["cefr"] in dogru_seviyeler else "Yanlış 1")
                for s in sorular}
        return [s["cefr"] for s in sorular], self.client.post(reverse("seviye_okuma"), veri)

    def _a2_b1_yolu(self):
        self.client.post(reverse("seviye_basla"))
        self._ekran(1, 0.9)
        cevap = self._ekran(2, 0.3)
        self.assertRedirects(cevap, reverse("seviye_okuma"))

    def test_sorular_kelime_sonucuna_gore_ve_sonuc_en_yuksek_dogru(self):
        self._a2_b1_yolu()
        sorulan, _ = self._okuma({"A2", "B1"})
        self.assertEqual(sorulan, ["A2", "B1"])
        self.user.refresh_from_db()
        self.assertEqual(self.user.cefr, "B1")

    def test_yalnizca_a2_dogru(self):
        self._a2_b1_yolu()
        self._okuma({"A2"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.cefr, "A2")

    def test_hic_dogru_yoksa_sorulan_en_dusuk(self):
        self._a2_b1_yolu()
        self._okuma(set())
        self.user.refresh_from_db()
        self.assertEqual(self.user.cefr, "A2")

    def test_ilk_ekran_gecilemezse_a1_ve_a2_sorulur(self):
        self.client.post(reverse("seviye_basla"))
        self._ekran(1, 0.3)
        sorulan, _ = self._okuma({"A1"})
        self.assertEqual(sorulan, ["A1", "A2"])

    def test_dogru_cevap_ve_sayisi_gosterilmez(self):
        self._a2_b1_yolu()
        _, cevap = self._okuma({"A2"})
        html = self.client.get(reverse("seviye_sonuc")).content.decode()
        self.assertNotIn("Doğru A2", html)
        self.assertNotIn("doğru özeti", html)

    def test_denetlenmemis_soru_sorulmaz(self):
        OkumaSorusu.objects.filter(cefr="B1").update(denetlendi=False)
        self._a2_b1_yolu()
        sorulan, _ = self._okuma(set())
        self.assertEqual(sorulan, ["A2"])


class C2YuvasiTests(TestCase):
    def test_c2_yuvasi_resmi_c2_yoksa_en_zor_oxford_c1(self):
        for i in range(40):
            make_word(f"ca{_harfler(i)}", level="C1", forms=False, siklik=3.0 + i / 100,
                      cefr_kaynak="oxford")
        c2 = [a for a in secim.adaylar() if a.cefr == "C2"]
        self.assertEqual(len(c2), secim.HAVUZ_BOYU["C2"])
        c1 = {a.word_id for a in secim.adaylar() if a.cefr == "C1"}
        self.assertFalse(c1 & {a.word_id for a in c2})


# ----------------------------------------------------------------------
# Davet (rapor 18.27: her sayfada, oturumlarda değil)
# ----------------------------------------------------------------------

class DavetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="davet", password=SIFRE)
        self.client.login(username="davet", password=SIFRE)

    def test_her_sayfada_davet(self):
        for ad in ("index", "sozluk", "readings", "learn_pass_page"):
            with self.subTest(sayfa=ad):
                cevap = self.client.get(reverse(ad))
                self.assertContains(cevap, "data-seviye-daveti")
                self.assertContains(cevap, reverse("seviye_sec"))

    def test_oturumlarda_ve_test_sayfalarinda_davet_yok(self):
        for url in (reverse("learn_pass_run", kwargs={"mode": "karma"}), reverse("seviye_testi"),
                    reverse("seviye_sec")):
            with self.subTest(url=url):
                self.assertNotContains(self.client.get(url), "data-seviye-daveti")

    def test_simdi_degil_kalkti(self):
        self.assertEqual(self.client.post("/seviye/simdi-degil/").status_code, 404)

    def test_seviye_secilince_davet_durur_ve_kucuk_not(self):
        html = self.client.get(reverse("seviye_sec")).content.decode()
        self.assertIn("data-ayarlar-notu", html)
        self.assertIn('value="C2"', html)
        cevap = self.client.post(reverse("seviye_sec"), {"seviye": "B2"}, follow=True)
        self.assertContains(cevap, "Ayarlar&#x27;dan değiştirebilirsin")
        self.assertNotContains(self.client.get(reverse("index")), "data-seviye-daveti")

    def test_misafire_davet_yok(self):
        self.client.logout()
        self.assertNotContains(self.client.get(reverse("index")), "data-seviye-daveti")

    def test_profilde_testi_tekrarla_baglantisi(self):
        self.user.cefr = "B1"
        self.user.save()
        cevap = self.client.get(reverse("user_profile"))
        self.assertContains(cevap, "Seviye testini tekrarla")
        self.assertContains(cevap, reverse("seviye_testi"))


# ----------------------------------------------------------------------
# Seviyenin kendiliğinden düzelmesi (rapor 18.27)
# ----------------------------------------------------------------------

class SeviyeDuzeltmeTests(TestCase):
    def setUp(self):
        from .duzeltme import hedef_seviye, gosterdigi_seviye
        self.hedef, self.gosterdigi = hedef_seviye, gosterdigi_seviye

    def test_seviye_basina_kural(self):
        self.assertEqual(self.gosterdigi("B1", 38, 40), 3)    # %75 üstü -> B2
        self.assertEqual(self.gosterdigi("B1", 20, 40), 2)    # arada -> B1
        self.assertEqual(self.gosterdigi("B1", 5, 40), 1)     # %35 altı -> A2

    def test_agirlikli_ortalama(self):
        ozet = {"B1": {"gorulen": 90, "bilinen": 85}, "B2": {"gorulen": 30, "bilinen": 15}}
        self.assertEqual(self.hedef(ozet), "B2")   # (3*90 + 3*30)/120 = 3 -> B2

    def test_az_veride_dokunulmaz(self):
        self.assertIsNone(self.hedef({"B1": {"gorulen": 40, "bilinen": 40}}))    # toplam < 50
        self.assertIsNone(self.hedef({"B1": {"gorulen": 19, "bilinen": 19},
                                      "B2": {"gorulen": 19, "bilinen": 19},
                                      "C1": {"gorulen": 19, "bilinen": 19}}))   # hiçbiri >= 20

    def test_haftada_bir_basamak_ve_seviyesiz_kullaniciya_dokunmaz(self):
        from learnpass import tekrar
        from learnpass.models import WordEncounter
        user = User.objects.create_user(username="duz", password=SIFRE)
        kelimeler = [make_word(f"ba{_harfler(i)}", level="B1", forms=False) for i in range(60)]
        for w in kelimeler:
            tekrar.kaydet(user, w, WordEncounter.KNOWN, "new")
        self.assertIsNone(seviyeyi_sessizce_duzelt(user))      # seviyesi belli değil
        user.cefr = "A1"
        user.save()
        self.assertEqual(seviyeyi_sessizce_duzelt(user), "A2")  # hedef B2, tek basamak
        self.assertIsNone(seviyeyi_sessizce_duzelt(user))      # bir hafta dolmadı
        user.refresh_from_db()
        self.assertEqual(user.cefr, "A2")
