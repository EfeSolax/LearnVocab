"""
Egzersizler testleri (ürün raporu 6.2, 12.1).

Her soru tipinin üreteci: tek doğru şık, tür etiketi yok. Hızlı Egzersiz
10 soru / kısa liste / boş liste. Düzensiz fiil. Boş havuzda tipin
atlanması. Bitiş, yanlışları tekrar, sayfa yenileme. Girişsiz yönlendirme.
"""

import io
import json
import os
import random
import re
import tempfile

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

import egzersizler
from users.models import User
from words.models import Collocation, RelationType, UserWordLink, WordFamily, WordRelation
from words.testing import make_word

from . import seviye as seviye_mod
from . import sorular as S
from .models import BaglacCumlesi, EgzersizCevabi, EgzersizOturumu, EsdizimCeldiricisi

TUR_ETIKETLERI = ("isim", "fiil", "sıfat", "zarf", "phrasal verb", "edat", "bağlaç")

# Çeldirici havuzu: birbirine karışmayan anlamlar.
HAVUZ = [
    ("table", "masa"), ("window", "pencere"), ("river", "nehir"), ("cloud", "bulut"),
    ("garden", "bahçe"), ("bridge", "köprü"), ("pencil", "kurşun kalem"), ("mirror", "ayna"),
    ("pillow", "yastık"), ("ladder", "merdiven"), ("candle", "mum"), ("basket", "sepet"),
    ("kettle", "çaydanlık"), ("wallet", "cüzdan"), ("island", "ada"), ("forest", "orman"),
]


def tur_etiketi_yok(testcase, soru):
    metinler = []
    for k, v in soru.items():
        if k == "tip":          # iç anahtar, ekranda yazmaz
            continue
        if isinstance(v, str):
            metinler.append(v)
        elif isinstance(v, list):
            for x in v:
                if isinstance(x, str):
                    metinler.append(x)
                elif isinstance(x, dict):
                    metinler.extend(str(y) for y in x.values())
    for metin in metinler:
        for etiket in TUR_ETIKETLERI:
            testcase.assertIsNone(re.search(rf"(?<!\w){etiket}(?!\w)", metin.lower()),
                                  f"tür etiketi göründü: {etiket!r} ← {metin!r}")


class Kurulum(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="egz", password="Sifre1234")
        self.havuz = [make_word(t, meaning=m, level="B1", definition=f"a thing called {t}")
                      for t, m in HAVUZ]

    def listeye(self, *kelimeler):
        for w in kelimeler:
            UserWordLink.objects.get_or_create(user=self.user, word=w)

    def giris(self):
        self.client.login(username="egz", password="Sifre1234")


# ----------------------------------------------------------------------
# Üreteçler
# ----------------------------------------------------------------------

class AnlamSorusuTests(Kurulum):
    def setUp(self):
        super().setUp()
        self.aim = make_word("aim", meaning="amaç, hedef", level="B1",
                             definition="the purpose of doing aim things")
        # Tuzaklar: aynı anlamı taşıyan ve bağlı kelimeler ASLA çeldirici olmamalı.
        self.goal = make_word("goal", meaning="hedef", level="B1")
        self.gaye = make_word("objective", meaning="gaye", level="B1")
        WordRelation.objects.create(from_word=self.aim, to_word=self.gaye,
                                    type=RelationType.SYNONYM, meaning=self.aim.meanings.first())

    def test_en_tr_tek_dogru(self):
        for tohum in range(25):
            soru = S.anlam_sorusu(self.aim, random.Random(tohum), yon="en_tr")
            self.assertEqual(len(soru["secenekler"]), 4)
            self.assertEqual(soru["secenekler"][soru["dogru"]], "amaç, hedef")
            self.assertEqual(soru["etiket"], "Anlamını seç")
            self.assertNotIn("hedef", [s for i, s in enumerate(soru["secenekler"]) if i != soru["dogru"]])
            self.assertNotIn("gaye", soru["secenekler"])
            self.assertEqual(len(set(soru["secenekler"])), 4)
            tur_etiketi_yok(self, soru)

    def test_tr_en_tek_dogru(self):
        for tohum in range(25):
            soru = S.anlam_sorusu(self.aim, random.Random(tohum), yon="tr_en")
            self.assertEqual(soru["soru"], "amaç, hedef")
            self.assertEqual(soru["secenekler"][soru["dogru"]], "aim")
            self.assertNotIn("goal", soru["secenekler"])
            self.assertNotIn("objective", soru["secenekler"])
            self.assertEqual(soru["kelimeler"], [self.aim.id])
            tur_etiketi_yok(self, soru)

    def test_aciklama_iki_yon_ve_maske(self):
        for yon in ("tanim_kelime", "kelime_tanim"):
            soru = S.aciklama_sorusu(self.aim, random.Random(1), yon=yon)
            self.assertEqual(len(soru["secenekler"]), 4)
            dogru = soru["secenekler"][soru["dogru"]]
            if yon == "tanim_kelime":
                self.assertEqual(dogru, "aim")
                self.assertNotIn(" aim ", f" {soru['soru']} ")   # açıklama cevabı ele vermez
                self.assertIn(S.BOSLUK, soru["soru"])
            else:
                self.assertIn("purpose", dogru)
            self.assertNotIn("goal", soru["secenekler"])
            tur_etiketi_yok(self, soru)

    def test_istemciye_dogru_sik_gitmez(self):
        soru = S.anlam_sorusu(self.aim, random.Random(3), yon="en_tr")
        istemci = S.istemci_sorusu(soru)
        for alan in ("dogru", "aciklama", "kelimeler"):
            self.assertNotIn(alan, istemci)


class EslestirmeTests(Kurulum):
    def test_gruplar_karismaz_ve_degerlendirme(self):
        a = make_word("purpose", meaning="amaç", level="B1")
        b = make_word("aim", meaning="amaç, hedef", level="B1")   # a ile karışır: aynı gruba girmez
        kelimeler = [a, b] + self.havuz[:6]
        gruplar = S.eslestirme_gruplari(kelimeler, 5)
        for g in gruplar:
            self.assertEqual(len(g), 4)
            self.assertFalse({a, b} <= set(g))
        soru = S.eslestirme_sorusu(gruplar[0], random.Random(2))
        self.assertEqual(sorted(soru["eslesme"]), [0, 1, 2, 3])
        for i, w in enumerate(gruplar[0]):
            self.assertEqual(soru["sag"][soru["eslesme"][i]], w.meanings.first().meaning_tr)
        self.assertEqual(S.degerlendir(soru, soru["eslesme"])[0], True)
        ters = list(reversed(soru["eslesme"]))
        dogru_mu, sonuclar = S.degerlendir(soru, ters)
        self.assertFalse(dogru_mu)
        self.assertEqual(len(sonuclar), 4)
        self.assertIsNone(S.degerlendir(soru, 2))
        karisik = S.karistir(soru, random.Random(9))
        for i in range(4):
            self.assertEqual(karisik["sag"][karisik["eslesme"][i]], soru["sag"][soru["eslesme"][i]])
        tur_etiketi_yok(self, soru)


class FiilSorusuTests(Kurulum):
    def test_duzensiz_fiil_sorusu(self):
        go = make_word("go", pos="verb", meaning="gitmek", v2="went", v3="gone", level="A1")
        for tohum in range(10):
            soru = S.fiil_sorusu(go, random.Random(tohum), hangi="v2")
            self.assertEqual(soru["etiket"], "2. hâlini seç")
            self.assertEqual(soru["secenekler"][soru["dogru"]], "went")
            self.assertIn("gone", soru["secenekler"])
            self.assertNotIn("goed", soru["secenekler"])      # uydurma biçim yok
            self.assertEqual(soru["aciklama"], "go · went · gone")
            tur_etiketi_yok(self, soru)
        soru = S.fiil_sorusu(go, random.Random(0), hangi="v3")
        self.assertEqual(soru["secenekler"][soru["dogru"]], "gone")

    def test_kabul_edilen_bicim_celdirici_olmaz(self):
        get = make_word("get", pos="verb", meaning="almak", v2="got", v3="gotten", level="A2")
        for tohum in range(10):
            soru = S.fiil_sorusu(get, random.Random(tohum), hangi="v3")
            dogrular = [s for s in soru["secenekler"] if s in ("gotten", "got")]
            self.assertEqual(dogrular, ["gotten"])

    def test_uc_hali_ayni_fiil_de_sorulur(self):
        # Rapor 18.28: üç hâli aynı fiiller de sorulur; 3 gerçek şıkla (uydurma yok).
        cut = make_word("cut", pos="verb", meaning="kesmek", v2="cut", v3="cut", level="A2")
        soru = S.fiil_sorusu(cut, random.Random(0))
        self.assertIsNotNone(soru)
        self.assertEqual(sorted(soru["secenekler"]), ["cut", "cuts", "cutting"])
        self.assertEqual(soru["secenekler"][soru["dogru"]], "cut")
        self.assertNotIn("cutted", soru["secenekler"])

    def test_duzenli_fiil_ve_listeden_bagimsizlik(self):
        make_word("decide", pos="verb", meaning="karar vermek", v2="decided", v3="decided")
        make_word("go", pos="verb", meaning="gitmek", v2="went", v3="gone", level="A1")
        make_word("can", pos="verb", meaning="-ebilmek", v2="could", v3="could", level="A1")
        metinler = {w.text for w in S.duzensiz_fiiller()}
        self.assertEqual(metinler, {"go"})
        # Liste boşken de fiil sorusu gelir.
        sorular = S.tempolu_sorular(self.user, S.TIP_FIIL, 5, random.Random(1))
        self.assertEqual(len(sorular), 1)
        self.assertEqual(sorular[0]["tip"], S.TIP_FIIL)


class BicimSorusuTests(Kurulum):
    def setUp(self):
        super().setUp()
        aile = WordFamily.objects.create(root="decide")
        self.decision = make_word("decision", family=aile, meaning="karar", level="B1",
                                  sentences=["She made a decision quickly."])
        make_word("decide", pos="verb", family=aile, meaning="karar vermek", level="B2",
                  v2="decided", v3="decided")
        make_word("decisive", pos="adjective", family=aile, meaning="kararlı", level="B2")
        make_word("decisively", pos="adverb", family=aile, meaning="kararlılıkla", level="B2")

    def test_bicim_sorusu(self):
        soru = S.bicim_sorusu(self.decision, random.Random(4))
        self.assertEqual(soru["etiket"], "Boşluğa hangisi gelir?")
        self.assertTrue(soru["cumle"])
        self.assertEqual(soru["soru"], f"She made a {S.BOSLUK} quickly.")
        self.assertEqual(sorted(soru["secenekler"]), ["decide", "decision", "decisive", "decisively"])
        self.assertEqual(soru["secenekler"][soru["dogru"]], "decision")
        # Yanlışta şıklardaki bütün biçimler anlamlarıyla (sıra şıklarla aynı).
        self.assertEqual([b["metin"] for b in soru["bicimler"]], soru["secenekler"])
        self.assertIn({"metin": "decisive", "anlam": "kararlı"}, soru["bicimler"])
        tur_etiketi_yok(self, soru)
        yanlis = (soru["dogru"] + 1) % 4
        sonuc = S.sonuc_verisi(soru, {"secim": yanlis, "dogru_mu": False})
        self.assertEqual(len(sonuc["bicimler"]), 4)
        self.assertNotIn("bicimler", S.sonuc_verisi(soru, {"secim": soru["dogru"], "dogru_mu": True}))

    def test_seviyeden_uretilir(self):
        sorular = S.tip_sorulari(S.TIP_BICIM, self.user, "B1", random.Random(0), 3)
        self.assertEqual(len(sorular), 1)            # aile başına bir soru
        self.assertEqual(sorular[0]["kelimeler"], [self.decision.id])

    def test_hedef_turunde_de_kullanilan_uye_celdirici_olmaz(self):
        aile = WordFamily.objects.create(root="pass")
        tunel = make_word("underpass", family=aile, meaning="alt geçit",
                          sentences=["The underpass was dark."])
        make_word("pass", pos="verb", family=aile, meaning="geçmek")
        make_word("pass", family=WordFamily.objects.create(root="pass-isim"), meaning="geçit")
        make_word("passable", pos="adjective", family=aile, meaning="geçilebilir")
        make_word("passively", pos="adverb", family=aile, meaning="edilgen biçimde")
        self.assertIsNone(S.bicim_sorusu(tunel, random.Random(0)))

    def test_uc_turlu_ailede_soru_yok(self):
        aile = WordFamily.objects.create(root="happy")
        happy = make_word("happy", pos="adjective", family=aile, meaning="mutlu",
                          sentences=["I am happy today."])
        make_word("happiness", family=aile, meaning="mutluluk")
        make_word("happily", pos="adverb", family=aile, meaning="mutlulukla")
        self.assertIsNone(S.bicim_sorusu(happy, random.Random(0)))


class IliskiSorusuTests(Kurulum):
    def setUp(self):
        super().setUp()
        self.bank = make_word("bank", meaning="banka", level="B1",
                              extra_meanings=[("nehir kıyısı", "land along a river")])
        self.kiyi = self.bank.meanings.get(meaning_tr="nehir kıyısı")
        self.shore = make_word("shore", meaning="kıyı, sahil", level="B1")
        self.coast = make_word("coast", meaning="sahil", level="B1")   # tuzak: aynı anlam
        WordRelation.objects.create(from_word=self.bank, to_word=self.shore,
                                    type=RelationType.SYNONYM, meaning=self.kiyi)

    def test_anlama_ozel_es_anlamli(self):
        bag = WordRelation.objects.get(from_word=self.bank, to_word=self.shore)
        for tohum in range(20):
            soru = S.iliski_sorusu(bag, random.Random(tohum))
            self.assertEqual(soru["etiket"], "Eş anlamlısını seç")
            self.assertEqual(soru["iliski"], "es")              # ekrandaki yeşil damga
            self.assertEqual(soru["soru"], "bank")
            self.assertEqual(soru["alt"], "nehir kıyısı")
            self.assertEqual(soru["secenekler"][soru["dogru"]], "shore")
            self.assertNotIn("coast", soru["secenekler"])
            tur_etiketi_yok(self, soru)

    def test_listedeki_kelime_sorulmaz(self):
        self.assertEqual(len(S.iliski_sorulari(self.user, "B1", random.Random(0), 5)), 1)
        self.listeye(self.bank)
        self.assertEqual(S.iliski_sorulari(self.user, "B1", random.Random(0), 5), [])

    def test_zit_anlamli_etiketi(self):
        cold = make_word("cold", pos="adjective", meaning="soğuk", level="B1")
        hot = make_word("hot", pos="adjective", meaning="sıcak", level="B1")
        for t, m in (("tall", "uzun boylu"), ("green", "yeşil"), ("empty", "boş"), ("soft", "yumuşak")):
            make_word(t, pos="adjective", meaning=m, level="B1")
        bag = WordRelation.objects.create(from_word=cold, to_word=hot, type=RelationType.ANTONYM,
                                          meaning=cold.meanings.first())
        soru = S.iliski_sorusu(bag, random.Random(0))
        self.assertEqual(soru["etiket"], "Zıt anlamlısını seç")
        self.assertEqual(soru["iliski"], "zit")                 # ekrandaki kırmızı damga
        self.assertEqual(soru["secenekler"][soru["dogru"]], "hot")

    def test_soru_ekraninda_buyuk_renkli_damga(self):
        """Efe, 2 Ekim: eş mi zıt mı istendiği hemen görülsün."""
        from django.template.loader import render_to_string
        bag = WordRelation.objects.get(from_word=self.bank, to_word=self.shore)
        soru = S.iliski_sorusu(bag, random.Random(0))
        html = render_to_string("pages/egzersizler/soru.html", {
            "soru": soru, "config": {}, "alev": {}, "sira_no": 1, "ilerleme": 0,
            "oturum": type("O", (), {"pk": 1, "soru_sayisi": 10, "sira": 0})(),
        })
        self.assertIn('data-iliski="es"', html)
        self.assertIn("EŞ ANLAMLISI", html)
        self.assertIn("eş anlamlısı</span>", html)


class BaglacVeEsdizimHavuzuTests(Kurulum):
    def test_bos_havuzda_tip_pasif_ve_karisikta_atlanir(self):
        durum = {d["anahtar"]: d for d in S.tip_durumlari(self.user)}
        self.assertFalse(durum[S.TIP_BAGLAC]["aktif"])
        self.assertEqual(durum[S.TIP_BAGLAC]["pasif_notu"], "Yakında")
        self.assertFalse(durum[S.TIP_ESDIZIM]["aktif"])
        self.assertFalse(durum[S.TIP_ESLESTIRME]["aktif"])       # liste boş
        make_word("go", pos="verb", meaning="gitmek", v2="went", v3="gone", level="A1")
        sorular = S.tempolu_sorular(self.user, S.KARISIK, 10, random.Random(5))
        self.assertTrue(sorular)
        self.assertFalse({s["tip"] for s in sorular} & {S.TIP_BAGLAC, S.TIP_ESDIZIM, S.TIP_ANLAM})
        # Tek tip olarak da seçilemez.
        self.assertEqual(S.tempolu_sorular(self.user, S.TIP_BAGLAC, 5, random.Random(0)), [])

    def test_denetlenmemis_baglac_kullanilmaz(self):
        BaglacCumlesi.objects.create(cumle="It rained. ___, we went out.", dogru="However",
                                     celdiriciler=["Therefore", "For example", "Similarly"],
                                     cefr="B1", denetlendi=False)
        self.assertFalse(S.baglac_havuzu().exists())
        BaglacCumlesi.objects.filter().update(denetlendi=True)
        soru = S.baglac_sorulari("B1", random.Random(0), 5)[0]
        self.assertEqual(soru["secenekler"][soru["dogru"]], "However")
        self.assertEqual(sorted(soru["secenekler"]), ["For example", "However", "Similarly", "Therefore"])
        self.assertIn(S.BOSLUK, soru["soru"])
        self.assertEqual(S.degerlendir(soru, soru["dogru"]), (True, [(None, True)]))

    def test_esdizim_yalnizca_dogrulanmis_celdirici(self):
        karar = make_word("decision", meaning="karar", level="B1",
                          collocations=[("make a decision", "verb_noun")])
        e = Collocation.objects.get(pattern="make a decision")
        e.meaning_tr = "karar vermek"
        e.save()
        EsdizimCeldiricisi.objects.create(collocation=e, celdirici="do", gercekten_yanlis=True)
        EsdizimCeldiricisi.objects.create(collocation=e, celdirici="give", gercekten_yanlis=True)
        EsdizimCeldiricisi.objects.create(collocation=e, celdirici="take", gercekten_yanlis=False)
        EsdizimCeldiricisi.objects.create(collocation=e, celdirici="have", gercekten_yanlis=None)
        self.assertFalse(S.esdizim_havuzu().exists())        # 2 doğrulanmış yetmez
        self.assertFalse({d["anahtar"]: d for d in S.tip_durumlari(self.user)}[S.TIP_ESDIZIM]["aktif"])
        EsdizimCeldiricisi.objects.filter(celdirici="have").update(gercekten_yanlis=True)
        sorular = S.esdizim_sorulari(self.user, "B1", random.Random(0), 3)
        self.assertEqual(len(sorular), 1)
        soru = sorular[0]
        self.assertEqual(soru["soru"], f"{S.BOSLUK} a decision")
        self.assertEqual(sorted(soru["secenekler"]), ["do", "give", "have", "make"])
        self.assertNotIn("take", soru["secenekler"])          # reddedilen çeldirici asla
        self.assertEqual(soru["secenekler"][soru["dogru"]], "make")
        self.assertEqual(soru["kelimeler"], [karar.id])
        tur_etiketi_yok(self, soru)


# ----------------------------------------------------------------------
# Hızlı Egzersiz
# ----------------------------------------------------------------------

class HizliEgzersizTests(Kurulum):
    def test_tam_on_soru_yalnizca_anlam_iki_yon(self):
        self.listeye(*self.havuz[:12])
        sorular = S.hizli_sorular(self.user, random.Random(0))
        self.assertEqual(len(sorular), 10)
        self.assertEqual({s["tip"] for s in sorular}, {S.TIP_ANLAM})
        self.assertEqual({s["etiket"] for s in sorular}, {"Anlamını seç", "Kelimesini seç"})
        liste = {w.id for w in self.havuz[:12]}
        for s in sorular:
            self.assertTrue(set(s["kelimeler"]) <= liste)
        self.assertEqual(len({s["kelimeler"][0] for s in sorular}), 10)

    def test_kisa_liste(self):
        self.listeye(*self.havuz[:3])
        self.assertEqual(len(S.hizli_sorular(self.user, random.Random(0))), 3)
        self.giris()
        html = self.client.get(reverse("exercises_page")).content.decode()
        self.assertIn("Listene kelime ekle", html)
        self.assertIn("3 soru", html)

    def test_bos_liste_cesaretlendirir(self):
        self.giris()
        html = self.client.get(reverse("exercises_page")).content.decode()
        self.assertIn("Listen seni bekliyor.", html)
        self.assertIn('data-pasif-tip="baglac"', html)
        cevap = self.client.post(reverse("egzersiz_basla"), {"tur": "hizli"}, follow=True)
        self.assertEqual(EgzersizOturumu.objects.count(), 0)
        self.assertContains(cevap, "Sözlük")


# ----------------------------------------------------------------------
# Akış: soru → cevap → devam → bitiş → yanlışları tekrar
# ----------------------------------------------------------------------

class AkisTests(Kurulum):
    def setUp(self):
        super().setUp()
        self.listeye(*self.havuz[:4])
        self.giris()

    def basla(self):
        self.client.post(reverse("egzersiz_basla"), {"tur": "hizli"})
        return EgzersizOturumu.objects.get(user=self.user, durum="devam")

    def cevapla(self, o, dogru):
        o.refresh_from_db()
        soru = o.sorular[o.sira]
        secim = soru["dogru"] if dogru else (soru["dogru"] + 1) % 4
        return self.client.post(reverse("egzersiz_cevap", args=[o.pk]), json.dumps({"secim": secim}),
                                content_type="application/json")

    def test_tam_tur_bitis_ve_tekrar(self):
        o = self.basla()
        self.assertEqual(o.soru_sayisi, 4)
        sayfa = self.client.get(reverse("egzersiz_oturum", args=[o.pk]))
        self.assertContains(sayfa, "1/4")
        self.assertContains(sayfa, 'data-soru-etiketi')
        config = sayfa.context["config"]
        self.assertNotIn("dogru", config["soru"])
        self.assertIsNone(config["sonuc"])

        yanlis_kelime = o.sorular[0]["kelimeler"][0]
        r = self.cevapla(o, dogru=False)
        veri = r.json()
        self.assertFalse(veri["dogru_mu"])
        self.assertIn("aciklama", veri)
        # İkinci cevap sayılmaz.
        self.cevapla(o, dogru=True)
        self.assertEqual(EgzersizCevabi.objects.filter(user=self.user).count(), 1)
        self.assertEqual(UserWordLink.objects.get(user=self.user, word_id=yanlis_kelime).wrongCount, 1)

        # Sayfa yenilenirse cevaplanmış soru sonucuyla gelir.
        sayfa = self.client.get(reverse("egzersiz_oturum", args=[o.pk]))
        self.assertFalse(sayfa.context["config"]["sonuc"]["dogru_mu"])

        for i in range(4):
            if i:
                self.cevapla(o, dogru=True)
            self.client.post(reverse("egzersiz_ilerle", args=[o.pk]))
        o.refresh_from_db()
        self.assertEqual(o.durum, "bitti")
        bitis = self.client.get(reverse("egzersiz_oturum", args=[o.pk]))
        self.assertTemplateUsed(bitis, "pages/egzersizler/bitis.html")
        self.assertContains(bitis, "Yanlışları tekrar çöz")
        self.assertContains(bitis, "Yeni tur")
        self.assertContains(bitis, "Bitir")
        self.assertEqual(bitis.context["oturum"].dogru_sayisi, 3)
        self.assertEqual(len(bitis.context["yanlislar"]), 1)
        self.assertContains(bitis, "Listene kelime ekle")          # kısa liste daveti

        # Zorlandıklarım
        self.assertEqual(list(egzersizler.zorlanilanlar(self.user).values_list("id", flat=True)),
                         [yanlis_kelime])

        # Yanlışları tekrar çöz: yalnızca yanlış soru, yeni oturum.
        r = self.client.post(reverse("egzersiz_tekrar", args=[o.pk]))
        yeni = EgzersizOturumu.objects.get(kaynak=o)
        self.assertRedirects(r, reverse("egzersiz_oturum", args=[yeni.pk]))
        self.assertEqual(yeni.soru_sayisi, 1)
        self.assertEqual(yeni.sorular[0]["kelimeler"], [yanlis_kelime])

    def test_yeni_tur_ve_devam_karti(self):
        o = self.basla()
        html = self.client.get(reverse("exercises_page")).content.decode()
        self.assertIn("Yarım kalan bir turun var.", html)
        self.client.post(reverse("egzersiz_basla"), {"tur": "hizli"})
        o.refresh_from_db()
        self.assertEqual(o.durum, "birakildi")
        self.assertEqual(EgzersizOturumu.objects.filter(durum="devam").count(), 1)

    def test_baskasinin_oturumu_acilmaz(self):
        o = self.basla()
        User.objects.create_user(username="baska", password="Sifre1234")
        self.client.login(username="baska", password="Sifre1234")
        self.assertEqual(self.client.get(reverse("egzersiz_oturum", args=[o.pk])).status_code, 404)

    def test_tempolu_sayi_ve_tip(self):
        make_word("go", pos="verb", meaning="gitmek", v2="went", v3="gone", level="A1")
        self.client.post(reverse("egzersiz_basla"), {"tur": "tempolu", "tip": "karisik", "sayi": "5"})
        o = EgzersizOturumu.objects.get(durum="devam")
        self.assertEqual(o.tur, "tempolu")
        self.assertEqual(o.istenen, 5)
        self.assertLessEqual(o.soru_sayisi, 5)
        self.assertGreater(o.soru_sayisi, 0)

    def test_gecersiz_cevap(self):
        o = self.basla()
        r = self.client.post(reverse("egzersiz_cevap", args=[o.pk]), json.dumps({"secim": 9}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 400)


# ----------------------------------------------------------------------
# Giriş, seviye, komutlar
# ----------------------------------------------------------------------

class GirisTests(TestCase):
    def test_girissiz_yonlendirme(self):
        html = self.client.get(reverse("exercises_page")).content.decode()
        self.assertIn("önce giriş yapın", html)
        r = self.client.post(reverse("egzersiz_basla"), {"tur": "hizli"})
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r["Location"])
        self.assertIn("önce giriş yapın",
                      self.client.get(reverse("egzersiz_oturum", args=[1])).content.decode())

    def test_misafirde_sekme_yok_davet_var(self):
        """Rapor 18.3: misafirde Çalışmalar sekme çubuğu yok; tek bir giriş daveti."""
        html = self.client.get(reverse("learn_pass_page")).content.decode()
        self.assertNotIn(reverse("exercises_page") + '"', html.split('aria-label="Alt menü"')[0].split("<main")[1])
        self.assertIn("Kişisel egzersiz çözebilmek için giriş yap", html)


class SeviyeTests(TestCase):
    def test_seviye(self):
        u = User.objects.create_user(username="s", password="Sifre1234")
        self.assertEqual(seviye_mod.kullanici_seviyesi(u), "B1")      # seviye belirlenmemiş
        u.cefr = "B2"
        self.assertEqual(seviye_mod.kullanici_seviyesi(u), "B2")
        self.assertEqual(seviye_mod.bir_ust("B1"), "B2")
        self.assertEqual(seviye_mod.bir_ust("C2"), "C2")
        self.assertEqual(seviye_mod.komsular("B1")[:3], ["B1", "A2", "B2"])


class KomutTests(TestCase):
    def _dosya(self, veri):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(veri, f)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_baglac_havuzu_yukle(self):
        yol = self._dosya([
            {"cumle": "It rained. ___, we went out.", "dogru": "However",
             "celdiriciler": ["Therefore", "For example", "Similarly"], "cefr": "B1", "denetlendi": True},
            {"cumle": "Boşluksuz cümle.", "dogru": "But", "celdiriciler": ["So"], "cefr": "B1"},
        ])
        call_command("baglac_havuzu_yukle", yol, "--dry-run", stdout=io.StringIO())
        self.assertEqual(BaglacCumlesi.objects.count(), 0)
        call_command("baglac_havuzu_yukle", yol, stdout=io.StringIO())
        self.assertEqual(BaglacCumlesi.objects.count(), 1)
        self.assertTrue(BaglacCumlesi.objects.get().denetlendi)

    def test_esdizim_celdiricileri(self):
        make_word("decision", meaning="karar", collocations=[("make a decision", "verb_noun")])
        e = Collocation.objects.get()
        aday_yolu = self._dosya([])
        call_command("esdizim_celdiricileri", "--adaylari-yaz", aday_yolu, stdout=io.StringIO())
        with open(aday_yolu, encoding="utf-8") as f:
            adaylar = [json.loads(s) for s in f if s.strip()]
        self.assertEqual(sorted(a["celdirici"] for a in adaylar), ["do", "give", "have", "take"])
        yol = self._dosya([
            {"collocation_id": e.id, "celdirici": "do", "gercekten_yanlis": True, "kaynak": "test"},
            {"collocation_id": e.id, "celdirici": "take", "gercekten_yanlis": False},
            {"collocation_id": e.id, "celdirici": "make", "gercekten_yanlis": True},   # kendisi: atlanır
        ])
        call_command("esdizim_celdiricileri", "--yukle", yol, "--dry-run", stdout=io.StringIO())
        self.assertEqual(EsdizimCeldiricisi.objects.count(), 0)
        call_command("esdizim_celdiricileri", "--yukle", yol, stdout=io.StringIO())
        self.assertEqual(dict(EsdizimCeldiricisi.objects.values_list("celdirici", "gercekten_yanlis")),
                         {"do": True, "take": False})
