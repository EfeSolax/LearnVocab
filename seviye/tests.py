"""
Seviye testi (rapor 7; D4, D8) ve kullanıcı seviyesi yardımcısı.
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
from .views import DAVET_CEREZI, OTURUM_ANAHTARI

SIFRE = "Sifre1234"
# Seviye başına harf öneki: kelimeler yalnızca a–z olmalı (secim._YAZIM).
ONEK = {"A1": "aa", "A2": "ab", "B1": "ba", "B2": "bb", "C1": "ca"}


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

    def test_duzeltme_kancasi_bir_sey_yapmaz(self):
        self.user.cefr = "B1"
        self.user.save()
        self.assertIsNone(seviyeyi_sessizce_duzelt(self.user, olay="lp"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.cefr, "B1")


# ----------------------------------------------------------------------
# Tahmin kuralı
# ----------------------------------------------------------------------

def _e(bilinen, gosterilen=40):
    return {"gosterilen": gosterilen, "bilinen": bilinen}


class TahminKuraliTests(TestCase):
    def test_ekran_atlama(self):
        self.assertIsNone(tahmin.sonraki_ekran(1, _e(19)))   # yarıdan az: zor ekran yok
        self.assertEqual(tahmin.sonraki_ekran(1, _e(20)), 2)
        self.assertIsNone(tahmin.sonraki_ekran(2, _e(5)))
        self.assertEqual(tahmin.sonraki_ekran(2, _e(30)), 3)
        self.assertIsNone(tahmin.sonraki_ekran(3, _e(40)))   # son ekran

    def test_kelime_tahmini(self):
        self.assertEqual(tahmin.kelime_tahmini({1: _e(10)}), "A1")
        self.assertEqual(tahmin.kelime_tahmini({1: _e(30), 2: _e(10)}), "A2")
        self.assertEqual(tahmin.kelime_tahmini({1: _e(38), 2: _e(25), 3: _e(12)}), "B1")
        self.assertEqual(tahmin.kelime_tahmini({"1": _e(40), "2": _e(35), "3": _e(25)}), "B2")
        self.assertEqual(tahmin.kelime_tahmini({1: _e(40), 2: _e(40), 3: _e(32)}), "C1")

    def test_okuma_yalnizca_uclarda_duzeltir(self):
        self.assertEqual(tahmin.okuma_duzeltmesi("B1", 3, 3), "B2")
        self.assertEqual(tahmin.okuma_duzeltmesi("B1", 0, 3), "A2")
        self.assertEqual(tahmin.okuma_duzeltmesi("B1", 2, 3), "B1")
        self.assertEqual(tahmin.okuma_duzeltmesi("C1", 3, 3), "C1")
        self.assertEqual(tahmin.okuma_duzeltmesi("A1", 0, 3), "A1")
        self.assertEqual(tahmin.okuma_duzeltmesi("B1", 0, 0), "B1")   # 2. kısım atlandı

    def test_ilk_liste_seviyenin_ekranindaki_dokunulmayanlar(self):
        gosterilen = {"1": [1, 2, 3], "2": [4, 5, 6], "3": [7, 8, 9]}
        bilinen = {"1": [1, 2, 3], "2": [4], "3": [7]}
        self.assertEqual(tahmin.ilk_liste("B1", gosterilen, bilinen), [5, 6])
        self.assertEqual(tahmin.ilk_liste("B2", gosterilen, bilinen), [8, 9])

    def test_ilk_liste_gosterilmeyen_ekranda_en_yakina_kayar(self):
        # A2 + okumada hepsi doğru -> B1; ama 2. ekran gösterilmedi.
        self.assertEqual(tahmin.ilk_liste("B1", {"1": [1, 2]}, {"1": [1]}), [2])


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
        def sahte(text):
            return 7.0 if text.endswith("aa") else 4.2   # "...aa" çok sık: band dışı
        adaylar = secim.adaylar(sahte)
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
        cevap, gosterilen, bilinen = self._gonder(3, 0.6)
        self.assertRedirects(cevap, reverse("seviye_sonuc"))   # okuma yok
        sonuc = SeviyeTestiSonucu.objects.get(user=self.user)
        self.assertEqual(sonuc.tahmin, "B2")
        self.assertIsNone(sonuc.okuma)
        self.assertEqual(set(sonuc.eklenen), set(gosterilen) - set(bilinen))
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
class OkumaKismiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.k = kelimeler_kur(4)
        metin = "One sentence here. Two sentences here. Three are here. Four is the last."
        for z in (1, 2, 3):
            OkumaSorusu.objects.create(zorluk=z, metin=f"{metin} ({z})", dogru=f"Doğru {z}",
                                       celdiriciler=[f"Yanlış {z}a", f"Yanlış {z}b"],
                                       denetlendi=True, anahtar=f"k{z}")

    def setUp(self):
        self.user = User.objects.create_user(username="okur", password=SIFRE)
        self.client.login(username="okur", password=SIFRE)

    def test_denetlenmemis_havuz_yok_sayilir(self):
        OkumaSorusu.objects.filter(zorluk=3).update(denetlendi=False)
        self.client.post(reverse("seviye_basla"))
        durum = self.client.session[OTURUM_ANAHTARI]
        cevap = self.client.post(reverse("seviye_ekran", args=[1]), {"bilinen": []})
        self.assertRedirects(cevap, reverse("seviye_sonuc"))
        self.assertTrue(durum)

    def test_okuma_hepsi_dogru_bir_seviye_ustu(self):
        self.client.post(reverse("seviye_basla"))
        cevap = self.client.post(reverse("seviye_ekran", args=[1]), {"bilinen": []})
        self.assertRedirects(cevap, reverse("seviye_okuma"))
        html = self.client.get(reverse("seviye_okuma")).content.decode()
        self.assertIn("en iyi özetleyen", html)
        veri = {f"soru_{s.id}": s.dogru for s in OkumaSorusu.objects.all()}
        self.assertRedirects(self.client.post(reverse("seviye_okuma"), veri), reverse("seviye_sonuc"))
        sonuc = SeviyeTestiSonucu.objects.get(user=self.user)
        self.assertEqual((sonuc.kelime_tahmini, sonuc.tahmin), ("A1", "A2"))
        self.assertEqual(sonuc.okuma, {"dogru": 3, "toplam": 3})


class OkumaYukleKomutuTests(TestCase):
    def _yukle(self, kayitlar, *secenekler):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(kayitlar, f)
        cikti = StringIO()
        call_command("seviye_okuma_yukle", f.name, *secenekler, stdout=cikti)
        Path(f.name).unlink()
        return cikti.getvalue()

    def _kayit(self, **degisen):
        kayit = {"zorluk": 1, "cefr": "A2",
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
            self._kayit(zorluk=5),
            self._kayit(metin="Too short."),
            self._kayit(celdiriciler=["only one"]),
            self._kayit(celdiriciler=["Tom is a baker who starts early.", "x y"]),
        ])
        self.assertIn("4 atlandı", cikti)
        self.assertEqual(OkumaSorusu.objects.count(), 0)


# ----------------------------------------------------------------------
# Davet kartı
# ----------------------------------------------------------------------

class DavetKartiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="davet", password=SIFRE)
        self.client.login(username="davet", password=SIFRE)

    def test_seviyesi_bossa_davet_var_zorla_yonlendirme_yok(self):
        cevap = self.client.get(reverse("index"))
        self.assertEqual(cevap.status_code, 200)
        self.assertContains(cevap, "data-seviye-daveti")
        self.assertContains(cevap, reverse("seviye_sec"))

    def test_simdi_degil_karti_gizler(self):
        cevap = self.client.post(reverse("seviye_simdi_degil"))
        self.assertRedirects(cevap, reverse("index"))
        self.assertEqual(cevap.cookies[DAVET_CEREZI].value, "kapali")
        self.assertNotContains(self.client.get(reverse("index")), "data-seviye-daveti")

    def test_seviyesi_belliyse_davet_yok(self):
        self.user.cefr = "B1"
        self.user.save()
        self.assertNotContains(self.client.get(reverse("index")), "data-seviye-daveti")

    def test_profilde_testi_tekrarla_baglantisi(self):
        self.user.cefr = "B1"
        self.user.save()
        cevap = self.client.get(reverse("user_profile"))
        self.assertContains(cevap, "Seviye testini tekrarla")
        self.assertContains(cevap, reverse("seviye_testi"))
