"""
Sözlük (ürün raporu 4) ve Listem (rapor 5).

Modüller: words/arama.py, words/listem.py, words/hazir_liste.py, words/sozluk_views.py
"""

import json
import os
import re
import tempfile
from datetime import date, timedelta
from io import StringIO

from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from learnpass.models import Declaration, WordEncounter
from users.models import User
from words import arama, hazir_liste
from words.models import (
    BulunamayanArama, Expression, ExpressionExample, HazirListe, HazirListeKelimesi,
    HazirListeSecimi, UserWordLink, WordFamily,
)
from words.testing import make_word


def _html(cevap):
    return cevap.content.decode()


class AramaTemeli(TestCase):
    """Küçük bir sözlük: aim (isim+fiil), go/went, child/children, receive, bitirmek…"""

    def setUp(self):
        aile = WordFamily.objects.create(root="aim")
        self.aim_n = make_word("aim", family=aile, meaning="amaç, hedef", level="B1")
        self.aim_v = make_word("aim", pos="verb", family=aile, meaning="hedeflemek",
                               v2="aimed", v3="aimed", level="B2")
        self.aimless = make_word("aimless", pos="adjective", family=aile, meaning="amaçsız", level="C1")
        self.aim_at = make_word("aim at", pos="phrasal_verb", meaning="-i hedef almak", level="B2")
        self.go = make_word("go", pos="verb", v2="went", v3="gone", meaning="gitmek", level="A1")
        self.child = make_word("child", meaning="çocuk", level="A1")
        self.receive = make_word("receive", pos="verb", meaning="almak", level="B1")
        self.finish = make_word("finish", pos="verb", meaning="bitirmek, sona erdirmek",
                                definition="to end something", level="A2")
        self.end = make_word("end", pos="verb", meaning="bitirmek", level="A2")
        self.complete = make_word("complete", pos="verb", meaning="tamamlamak, bitirmek", level="B1")
        self.light = make_word("light", meaning="ışık", level="A2")
        self.carpet = make_word("carpet", meaning="halı", level="B1")
        self.user = User.objects.create_user(username="efe", password="Sifre1234")

    def ara(self, q, **kw):
        cevap = self.client.get(reverse("sozluk"), {"q": q, **kw})
        self.assertEqual(cevap.status_code, 200)
        return cevap


class InglizceAramaTests(AramaTemeli):

    def test_tam_eslesme_her_tur_ayri_kart_ilki_acik(self):
        cevap = self.ara("aim")
        kartlar = cevap.context["kartlar"]
        self.assertEqual([k.id for k in kartlar], [self.aim_n.id, self.aim_v.id])  # yaygın (B1) önce
        durumlar = re.findall(r'x-data="\{ acik: (true|false) \}"', _html(cevap))
        self.assertEqual(durumlar[:2], ["true", "false"])

    def test_buyuk_harf_ve_turkce_klavye(self):
        self.assertEqual(len(self.ara("AIM").context["kartlar"]), 2)
        self.assertEqual(len(self.ara("  Aim ").context["kartlar"]), 2)
        # Türkçe klavyede büyük I: "İ" -> i
        make_word("idea", meaning="fikir")
        self.assertEqual([k.text for k in self.ara("İDEA").context["kartlar"]], ["idea"])

    def test_diger_sonuclar_once_onekliler_sonra_ifadeler(self):
        Expression.objects.create(text="take aim", meaning_tr="nişan almak", visibility="public", cefr="B2")
        sonuc = self.ara("aim").context["sonuc"]
        metinler = [s["metin"] for s in sonuc.digerleri]
        self.assertEqual(metinler[0], "aimless")
        self.assertIn("aim at", metinler)
        self.assertIn("take aim", metinler)
        self.assertLessEqual(len(metinler), 8)
        html = _html(self.ara("aim"))
        self.assertIn("Diğer sonuçlar", html)
        self.assertIn(f'data-kart-ac="{self.aimless.id}"', html)

    def test_diger_sonuclar_en_cok_sekiz(self):
        for i in range(12):
            make_word(f"aimz{i:02d}", meaning="x")
        self.assertLessEqual(len(self.ara("aim").context["sonuc"].digerleri), 8)

    def test_gizli_kelime_gelmez(self):
        diger = User.objects.create_user(username="diger", password="Sifre1234")
        make_word("secretword", is_base=False, visibility="private", owner=diger)
        cevap = self.ara("secretword")
        self.assertEqual(cevap.context["kartlar"], [])

    def test_ifade_tam_eslesme(self):
        e = Expression.objects.create(text="on the other hand", meaning_tr="öte yandan",
                                      visibility="public", cefr="B1")
        ExpressionExample.objects.create(expression=e, text="On the other hand, it is cheap.")
        html = _html(self.ara("on the other hand"))
        self.assertIn("data-ifade-karti", html)
        self.assertIn("öte yandan", html)
        self.assertIn("On the other hand, it is cheap.", html)
        self.assertFalse(BulunamayanArama.objects.exists())

    def test_seo_baslik_aciklama(self):
        html = _html(self.ara("aim"))
        self.assertIn("<title>aim ne demek?", html)
        self.assertIn('name="description"', html)
        self.assertIn("amaç, hedef", html)
        self.assertNotIn('content="noindex"', html)


class CekimVeYazimTests(AramaTemeli):

    def test_went_go(self):
        cevap = self.ara("went")
        self.assertEqual([k.id for k in cevap.context["kartlar"]], [self.go.id])
        self.assertIn("went, go kelimesinin geçmiş hâli", _html(cevap))
        self.assertFalse(BulunamayanArama.objects.exists())

    def test_children_child(self):
        cevap = self.ara("children")
        self.assertEqual([k.id for k in cevap.context["kartlar"]], [self.child.id])
        self.assertIn("children, child kelimesinin çoğulu", _html(cevap))

    def test_recieve_bunu_mu_demek_istediniz(self):
        cevap = self.ara("recieve")
        html = _html(cevap)
        self.assertIn("Bunu mu demek istediniz?", html)
        self.assertEqual(cevap.context["sonuc"].oneriler[0]["metin"], "receive")
        kayit = BulunamayanArama.objects.get(sorgu="recieve")
        self.assertTrue(kayit.oneri_vardi)
        self.assertIn('content="noindex"', html)

    def test_hic_yoksa_henuz_sozlugumuzde_yok_ve_kayit(self):
        html = _html(self.ara("gskjengkwng"))
        self.assertIn("Henüz sözlüğümüzde yok.", html)
        self.ara("GSKJENGKWNG")
        kayit = BulunamayanArama.objects.get(sorgu="gskjengkwng")
        self.assertEqual(kayit.sayi, 2)
        self.assertFalse(kayit.oneri_vardi)

    def test_bulunan_arama_kaydedilmez_ve_anlamsiz_sorgu_yazilmaz(self):
        self.ara("aim")
        self.ara("12345")
        self.ara("?!")
        self.assertFalse(BulunamayanArama.objects.exists())


class TurkceAramaTests(AramaTemeli):

    def test_bitir_kompakt_kartlar_yayindan_nadire(self):
        cevap = self.ara("bitir")
        kartlar = cevap.context["turkce_kartlar"]
        metinler = [k.text for k in kartlar]
        self.assertEqual(set(metinler), {"finish", "end", "complete"})
        self.assertEqual(metinler[-1], "complete")          # B1, "bitirmek" 2. anlamda: en sonda
        html = _html(cevap)
        self.assertIn("<mark data-eslesen", html)
        self.assertIn("to end something", html)            # tek satır tanım
        self.assertIn("anlamındaki kelimeler", html)
        # Kapalı kompakt: hiçbiri açık başlamaz
        self.assertNotIn('x-data="{ acik: true }"', html)

    def test_sozcuk_basi_eslesmesi(self):
        """'bitir' sözcüğün başında aranır; 'tir' ile bitirmek gelmez."""
        self.assertEqual(self.ara("tir").context["turkce_kartlar"], [])

    def test_turkce_harfsiz_yazim_katlanir(self):
        self.assertEqual([k.text for k in self.ara("isik").context["turkce_kartlar"]], ["light"])
        self.assertEqual([k.text for k in self.ara("IŞIK").context["turkce_kartlar"]], ["light"])

    def test_turkce_harfli_sorgu_ingilizce_aramaz(self):
        sonuc = self.ara("ışık").context["sonuc"]
        self.assertEqual(sonuc.kelimeler, [])
        self.assertEqual(sonuc.digerleri, [])


class OtomatikOneriTests(AramaTemeli):

    def oneri(self, q):
        cevap = self.client.get(reverse("sozluk_oneri"), {"q": q})
        self.assertEqual(cevap.status_code, 200)
        return cevap.json()["oneriler"]

    def test_onek_yayindan_nadire_ve_satir_bicimi(self):
        satirlar = self.oneri("ai")
        self.assertEqual(satirlar[0]["metin"], "aim")
        self.assertEqual(satirlar[0]["anlam"], "amaç, hedef")
        self.assertEqual(satirlar[0]["adres"], f"{reverse('sozluk')}?q=aim")
        self.assertEqual([s["metin"] for s in satirlar].count("aim"), 1)   # tür başına değil, yazım başına
        self.assertIn("aimless", [s["metin"] for s in satirlar])

    def test_turkce_oneri(self):
        satirlar = self.oneri("bitir")
        self.assertEqual({s["metin"] for s in satirlar}, {"finish", "end", "complete"})
        self.assertTrue(all("bitir" in s["anlam"] for s in satirlar))

    def test_bos_ve_bilinmeyen(self):
        self.assertEqual(self.oneri(""), [])
        self.assertEqual(self.oneri("zzqx"), [])

    def test_dizin_yeni_kelimeyi_hemen_gorur(self):
        self.assertEqual(self.oneri("carpenter"), [])
        make_word("carpenter", meaning="marangoz")
        self.assertEqual(self.oneri("carpente")[0]["metin"], "carpenter")

    def test_sorgu_sayisi_az(self):
        self.oneri("ca")   # dizin kurulsun
        with CaptureQueriesContext(connection) as sorgular:
            self.oneri("car")
        self.assertLessEqual(len(sorgular), 3)


class KartParcasiTests(AramaTemeli):

    def test_kart_parcasi(self):
        cevap = self.client.get(reverse("sozluk_kart", args=[self.go.id]))
        self.assertEqual(cevap.status_code, 200)
        html = _html(cevap)
        self.assertIn(f'data-kelime-karti="{self.go.id}"', html)
        self.assertIn('x-data="{ acik: true }"', html)
        self.assertNotIn("<html", html)

    def test_kapat_olay(self):
        html = _html(self.client.get(reverse("sozluk_kart", args=[self.go.id]), {"kapat": "olay"}))
        self.assertIn("$dispatch('kart-kapat')", html)

    def test_gizli_kelime_404(self):
        diger = User.objects.create_user(username="diger", password="Sifre1234")
        gizli = make_word("hush", is_base=False, visibility="private", owner=diger)
        self.assertEqual(self.client.get(reverse("sozluk_kart", args=[gizli.id])).status_code, 404)

    def test_cipler_yerinde_acar(self):
        html = _html(self.ara("aim"))
        self.assertIn(f'data-kart-ac="{self.aimless.id}"', html)   # Aile çipi


class AramaSorguSayisiTests(AramaTemeli):

    def test_arama_sayfasi_sabit_sorgu(self):
        self.ara("aim")
        with CaptureQueriesContext(connection) as az:
            self.ara("aim")
        aile = self.aim_n.family
        for tur in ("adjective", "adverb", "preposition"):
            make_word("aim", pos=tur, family=aile, meaning="x")
        self.ara("aim")
        with CaptureQueriesContext(connection) as cok:
            self.ara("aim")
        self.assertEqual(len(az), len(cok))
        self.assertLessEqual(len(cok), 25)


class KesfetBosHalTests(AramaTemeli):

    def test_gunun_kelimesi_ve_ifadesi(self):
        Expression.objects.create(text="however", meaning_tr="ancak", visibility="public", cefr="B1")
        html = _html(self.client.get(reverse("sozluk")))
        self.assertIn("Günün Kelimesi", html)
        self.assertIn("Günün İfadesi", html)
        self.assertIn("however", html)
        self.assertIn("Hazır Listeler", html)
        self.assertIn("yakında burada", html)       # liste yokken sade boş hâl

    def test_gunun_kelimesi_gunluk_deterministik_ve_seviyeye_gore(self):
        gun = date(2026, 9, 28)
        self.assertEqual(arama.gunun_kelimesi(None, gun), arama.gunun_kelimesi(None, gun))
        self.assertEqual(arama.gunun_kelimesi(None, gun).cefr, "B1")   # girişsiz: B1
        self.user.level = 101                                         # eski kur: A1
        self.assertEqual(arama.gunun_kelimesi(self.user, gun).cefr, "A1")
        # Günler arasında değişebilir; en az bir günde farklı çıkmalı
        gunler = {arama.gunun_kelimesi(None, gun + timedelta(days=i)).id for i in range(20)}
        self.assertGreater(len(gunler), 1)

    def test_kullanici_seviyesi(self):
        self.assertEqual(arama.kullanici_seviyesi(self.user), "B1")   # level=1: bilinmiyor
        self.user.level = 401
        self.assertEqual(arama.kullanici_seviyesi(self.user), "B2")


class SekmeTests(TestCase):

    def test_girissizde_listem_sekmesi_yok(self):
        html = _html(self.client.get(reverse("sozluk")))
        self.assertNotIn("?sekme=listem", html)
        cevap = self.client.get(reverse("sozluk"), {"sekme": "listem"})
        self.assertEqual(cevap.context["sekme"], "kesfet")
        self.assertNotIn("data-listem", _html(cevap))

    def test_listem_uclari_giris_ister(self):
        for ad in ("listem_oneri",):
            self.assertEqual(self.client.get(reverse(ad)).status_code, 302)
        for ad in ("listem_toplu_cikar", "listem_geri_yukle"):
            self.assertEqual(self.client.post(reverse(ad)).status_code, 302)


# ----------------------------------------------------------------------
# Hazır listeler
# ----------------------------------------------------------------------

class HazirListeTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="efe", password="Sifre1234")
        self.aim = make_word("aim", meaning="amaç")
        self.decide = make_word("decide", pos="verb", meaning="karar vermek")
        self.liste = HazirListe.objects.create(ad="ODTÜ 101", slug="odtu-101", kurum="ODTÜ")
        HazirListeKelimesi.objects.create(liste=self.liste, word=self.decide, sira=1)
        HazirListeKelimesi.objects.create(liste=self.liste, word=self.aim, sira=2)

    def test_kesfette_gorunur(self):
        html = _html(self.client.get(reverse("sozluk")))
        self.assertIn("ODTÜ 101", html)
        self.assertIn(reverse("hazir_liste", args=["odtu-101"]), html)
        HazirListe.objects.update(yayinda=False)
        self.assertNotIn("ODTÜ 101", _html(self.client.get(reverse("sozluk"))))

    def test_liste_sayfasi_kapali_kartlar_sirali_hepsini_ekle_yok(self):
        cevap = self.client.get(reverse("hazir_liste", args=["odtu-101"]))
        self.assertEqual([k.text for k in cevap.context["kartlar"]], ["decide", "aim"])
        html = _html(cevap)
        self.assertNotIn('x-data="{ acik: true }"', html)
        self.assertIn("Bu listeyle çalış", html)
        self.assertIn('data-giris-gerekli="calisma"', html)
        self.assertNotIn("hepsini", html.lower())

    def test_bu_listeyle_calis_ve_seviyeme_don(self):
        self.assertIsNone(hazir_liste.aktif_liste(self.user))
        self.client.login(username="efe", password="Sifre1234")
        self.client.post(reverse("hazir_liste_calis", args=["odtu-101"]))
        self.assertEqual(hazir_liste.aktif_liste(self.user), self.liste)
        self.assertEqual(list(hazir_liste.aktif_liste(self.user).sirali_kelimeler()),
                         [self.decide, self.aim])
        html = _html(self.client.get(reverse("hazir_liste", args=["odtu-101"])))
        self.assertIn("Bu listeyle çalışıyorsun", html)
        self.assertIn("Çalışıyorsun", _html(self.client.get(reverse("sozluk"))))
        # Başka listeye geçince tek seçim kalır
        diger = HazirListe.objects.create(ad="Cambridge B2", slug="cambridge-b2")
        self.client.post(reverse("hazir_liste_calis", args=["cambridge-b2"]))
        self.assertEqual(HazirListeSecimi.objects.filter(user=self.user).count(), 1)
        self.assertEqual(hazir_liste.aktif_liste(self.user), diger)
        self.client.post(reverse("hazir_liste_calis", args=["cambridge-b2"]), {"islem": "birak"})
        self.assertIsNone(hazir_liste.aktif_liste(self.user))

    def test_girissiz_calis_yapilamaz_ve_yayinda_olmayan_404(self):
        self.assertEqual(self.client.post(reverse("hazir_liste_calis", args=["odtu-101"])).status_code, 302)
        self.assertFalse(HazirListeSecimi.objects.exists())
        HazirListe.objects.update(yayinda=False)
        self.assertEqual(self.client.get(reverse("hazir_liste", args=["odtu-101"])).status_code, 404)
        self.assertIsNone(hazir_liste.aktif_liste(None))

    def test_yayindan_kalkan_liste_aktif_sayilmaz(self):
        hazir_liste.listeyle_calis(self.user, self.liste)
        HazirListe.objects.update(yayinda=False)
        self.assertIsNone(hazir_liste.aktif_liste(self.user))

    def test_sayfalama_parca(self):
        for i in range(45):
            w = make_word(f"word{i:02d}", meaning="x")
            HazirListeKelimesi.objects.create(liste=self.liste, word=w, sira=10 + i)
        html = _html(self.client.get(reverse("hazir_liste", args=["odtu-101"])))
        self.assertIn("data-hazir-liste-devam", html)
        parca = self.client.get(reverse("hazir_liste", args=["odtu-101"]), {"sayfa": 2, "parca": 1})
        self.assertEqual(len(parca.context["kartlar"]), 7)
        self.assertNotIn("<html", _html(parca))


class HazirListeKomutuTests(TestCase):

    def setUp(self):
        aile = WordFamily.objects.create(root="aim")
        self.aim_n = make_word("aim", family=aile, meaning="amaç", level="B1")
        self.aim_v = make_word("aim", pos="verb", family=aile, meaning="hedeflemek", level="B2")
        self.go = make_word("go", pos="verb", v2="went", v3="gone", meaning="gitmek", level="A1")
        self.decide = make_word("decide", pos="verb", meaning="karar vermek")

    def yukle(self, icerik, *arg):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(icerik)
        self.addCleanup(os.remove, f.name)
        cikti = StringIO()
        call_command("hazir_liste_yukle", f.name, "--ad", "ODTÜ 101", *arg, stdout=cikti)
        return cikti.getvalue()

    def test_yukleme_ve_rapor(self):
        cikti = self.yukle("# yorum\naim\naim:fiil\n\nwent\ndecide:verb\nblorf\ndecide\ncarpet:xyz\n")
        liste = HazirListe.objects.get(slug="odtu-101")
        self.assertEqual(list(liste.sirali_kelimeler()), [self.aim_n, self.aim_v, self.go, self.decide])
        self.assertIn("blorf", cikti)
        self.assertIn("bilinmeyen tür: xyz", cikti)
        self.assertIn("went -> go", cikti)
        self.assertIn("en yaygını seçilen", cikti)
        self.assertIn("Tekrar eden", cikti)

    def test_dry_run_hicbir_sey_yazmaz(self):
        cikti = self.yukle("aim\n", "--dry-run")
        self.assertFalse(HazirListe.objects.exists())
        self.assertIn("dry-run", cikti)

    def test_ayni_slug_yenile_ister(self):
        self.yukle("aim\n", "--slug", "odtu-101")
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            self.yukle("go\n", "--slug", "odtu-101")
        self.yukle("go\n", "--slug", "odtu-101", "--yenile")
        self.assertEqual(list(HazirListe.objects.get().sirali_kelimeler()), [self.go])

    def test_eslesmeyenler_dosyasi(self):
        yol = tempfile.mktemp(suffix=".txt")
        self.addCleanup(lambda: os.path.exists(yol) and os.remove(yol))
        self.yukle("blorf\naim\n", "--eslesmeyenler", yol, "--dry-run")
        with open(yol, encoding="utf-8") as f:
            self.assertIn("blorf", f.read())


# ----------------------------------------------------------------------
# Listem
# ----------------------------------------------------------------------

class ListemTemeli(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="efe", password="Sifre1234")
        self.client.login(username="efe", password="Sifre1234")
        aile = WordFamily.objects.create(root="aim")
        self.aim_n = make_word("aim", family=aile, meaning="amaç, hedef",
                               extra_meanings=[("nişan", "a point aimed at")])
        self.aim_v = make_word("aim", pos="verb", family=aile, meaning="hedeflemek")
        self.decide = make_word("decide", pos="verb", meaning="karar vermek")
        self.zebra = make_word("zebra", meaning="zebra")
        simdi = timezone.now()
        self.baglar = {}
        for w, gun in ((self.zebra, 40), (self.decide, 10), (self.aim_n, 3), (self.aim_v, 1)):
            b = UserWordLink.objects.create(user=self.user, word=w)
            UserWordLink.objects.filter(pk=b.pk).update(dateAdded=simdi - timedelta(days=gun))
            self.baglar[w.id] = b

    def listem(self, **kw):
        cevap = self.client.get(reverse("sozluk"), {"sekme": "listem", **kw})
        self.assertEqual(cevap.status_code, 200)
        return cevap

    def idler(self, **kw):
        return [s.id for s in self.listem(**kw).context["satirlar"]]


class ListemSatirTests(ListemTemeli):

    def test_varsayilan_en_yeni_ustte_ve_satir(self):
        self.assertEqual(self.idler(), [self.aim_v.id, self.aim_n.id, self.decide.id, self.zebra.id])
        html = _html(self.listem())
        self.assertIn("Listemden çıkar", html)
        self.assertIn(">1.</span> amaç, hedef", html)
        self.assertIn(">2.</span> nişan", html)

    def test_iki_tur_iki_satir_gri_tur_etiketi(self):
        satirlar = {s.id: s for s in self.listem().context["satirlar"]}
        self.assertEqual(satirlar[self.aim_n.id].tur, "isim")
        self.assertEqual(satirlar[self.aim_v.id].tur, "fiil")
        self.assertEqual(satirlar[self.decide.id].tur, "")

    def test_siralama(self):
        self.assertEqual(self.idler(sira="eski")[0], self.zebra.id)
        self.assertEqual(self.idler(sira="az")[-1], self.zebra.id)
        self.assertEqual(self.idler(sira="saçma")[0], self.aim_v.id)

    def test_zaman(self):
        self.assertEqual(set(self.idler(zaman="hafta")), {self.aim_n.id, self.aim_v.id})
        self.assertEqual(set(self.idler(zaman="ay")), {self.aim_n.id, self.aim_v.id, self.decide.id})

    def test_zorlandiklarim(self):
        self.assertEqual(self.idler(zor="1"), [])
        UserWordLink.objects.filter(pk=self.baglar[self.zebra.id].pk).update(wrongCount=2)
        WordEncounter.objects.create(user=self.user, word=self.decide, last_verdict="unknown",
                                     unknown_count=1)
        WordEncounter.objects.create(user=self.user, word=self.aim_v, last_verdict="known",
                                     known_count=3)     # bildi: zorlanmadı
        diger = User.objects.create_user(username="diger", password="x")
        WordEncounter.objects.create(user=diger, word=self.aim_n, last_verdict="unknown", unknown_count=1)
        self.assertEqual(set(self.idler(zor="1")), {self.zebra.id, self.decide.id})
        WordEncounter.objects.create(user=self.user, word=self.aim_n, last_verdict="known",
                                     declaration=Declaration.STUCK)
        self.assertIn(self.aim_n.id, self.idler(zor="1"))

    def test_listede_ara_ingilizce_ve_turkce(self):
        self.assertEqual(set(self.idler(ara="aim")), {self.aim_n.id, self.aim_v.id})
        self.assertEqual(self.idler(ara="hedef"), [self.aim_v.id, self.aim_n.id])
        self.assertEqual(self.idler(ara="KARAR"), [self.decide.id])

    def test_bos_liste_metni(self):
        UserWordLink.objects.all().delete()
        html = _html(self.listem())
        self.assertIn("Listen boş. Sözlük'te + ile ya da Learn &amp; Pass'te kelime ekleyebilirsin.", html)

    def test_filtre_bos_ama_liste_dolu(self):
        html = _html(self.listem(ara="qqq"))
        self.assertNotIn("Listen boş.", html)
        self.assertIn("data-filtre-bos", html)

    def test_seviye_filtresi_yok(self):
        html = _html(self.listem())
        self.assertNotIn("Seviye", html)
        self.assertIn("Zorlandıklarım", html)
        self.assertIn("En eski", html)
        self.assertIn("Son 1 hafta", html)

    def test_tumunu_sec_filtreye_uyar(self):
        cevap = self.listem(zaman="hafta")
        self.assertEqual(set(cevap.context["tum_idler"]), {self.aim_n.id, self.aim_v.id})
        self.assertIn('id="listem-idler"', _html(cevap))

    def test_sayfalama(self):
        for i in range(55):
            UserWordLink.objects.create(user=self.user, word=make_word(f"w{i:02d}", meaning="x"))
        cevap = self.listem()
        self.assertEqual(len(cevap.context["satirlar"]), 50)
        self.assertEqual(len(cevap.context["tum_idler"]), 59)
        self.assertIn("Daha fazla göster", _html(cevap))
        parca = self.listem(sayfa=2, parca=1)
        self.assertEqual(len(parca.context["satirlar"]), 9)
        self.assertNotIn("<html", _html(parca))

    def test_sorgu_sayisi_liste_buyudukce_artmaz(self):
        self.listem()
        with CaptureQueriesContext(connection) as az:
            self.listem()
        for i in range(20):
            UserWordLink.objects.create(user=self.user, word=make_word(f"q{i:02d}", meaning="x"))
        with CaptureQueriesContext(connection) as cok:
            self.listem()
        self.assertEqual(len(az), len(cok))

    def test_listem_onerisi_yalnizca_listeden(self):
        make_word("decimal", meaning="ondalık")
        satirlar = self.client.get(reverse("listem_oneri"), {"q": "dec"}).json()["oneriler"]
        self.assertEqual([s["metin"] for s in satirlar], ["decide"])
        self.assertIn("sekme=listem", satirlar[0]["adres"])
        satirlar = self.client.get(reverse("listem_oneri"), {"q": "hedef"}).json()["oneriler"]
        self.assertEqual([s["metin"] for s in satirlar], ["aim"])
        self.assertEqual(satirlar[0]["anlam"], "amaç, hedef")


class ListemTopluTests(ListemTemeli):

    def post(self, ad, veri):
        return self.client.post(reverse(ad), json.dumps(veri), content_type="application/json",
                                HTTP_X_REQUESTED_WITH="fetch")

    def test_toplu_cikar_ve_geri_al_tarihleri_korur(self):
        UserWordLink.objects.filter(pk=self.baglar[self.decide.id].pk).update(wrongCount=4, correctCount=1)
        eski = {b.word_id: b.dateAdded for b in UserWordLink.objects.filter(user=self.user)}
        cevap = self.post("listem_toplu_cikar", {"idler": [self.decide.id, self.zebra.id, 99999]}).json()
        self.assertEqual(cevap["sayi"], 2)
        self.assertEqual(set(self.idler()), {self.aim_n.id, self.aim_v.id})

        self.assertEqual(self.post("listem_geri_yukle", {"geri": cevap["geri"]}).json()["sayi"], 2)
        yeni = {b.word_id: b for b in UserWordLink.objects.filter(user=self.user)}
        self.assertEqual(yeni[self.decide.id].dateAdded, eski[self.decide.id])
        self.assertEqual(yeni[self.zebra.id].dateAdded, eski[self.zebra.id])
        self.assertEqual((yeni[self.decide.id].correctCount, yeni[self.decide.id].wrongCount), (1, 4))
        self.assertEqual(self.idler()[-1], self.zebra.id)      # sıra da geri geldi

    def test_baskasinin_listesine_dokunmaz(self):
        diger = User.objects.create_user(username="diger", password="x")
        UserWordLink.objects.create(user=diger, word=self.decide)
        self.post("listem_toplu_cikar", {"idler": [self.decide.id]})
        self.assertTrue(UserWordLink.objects.filter(user=diger, word=self.decide).exists())

    def test_geri_al_bozuk_ve_gelecek_tarih(self):
        UserWordLink.objects.all().delete()
        gelecek = (timezone.now() + timedelta(days=30)).isoformat()
        saatsiz = "2026-01-01T10:00:00"
        sayi = self.post("listem_geri_yukle", {"geri": [
            {"word": self.decide.id, "dateAdded": gelecek},
            {"word": self.zebra.id, "dateAdded": saatsiz},
            {"word": "x"}, "bozuk",
        ]}).json()["sayi"]
        self.assertEqual(sayi, 1)
        self.assertLessEqual(UserWordLink.objects.get(word=self.decide).dateAdded, timezone.now())
        self.assertEqual(self.post("listem_geri_yukle", {"geri": "yok"}).json()["sayi"], 0)
        bozuk = self.client.post(reverse("listem_geri_yukle"), "{bozuk", content_type="application/json")
        self.assertEqual(bozuk.status_code, 200)

    def test_gorulemeyen_kelime_geri_konmaz(self):
        diger = User.objects.create_user(username="diger", password="x")
        gizli = make_word("hush", is_base=False, visibility="private", owner=diger)
        sayi = self.post("listem_geri_yukle", {"geri": [
            {"word": gizli.id, "dateAdded": timezone.now().isoformat()}]}).json()["sayi"]
        self.assertEqual(sayi, 0)
