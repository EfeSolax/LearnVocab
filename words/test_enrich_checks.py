"""
Zenginleştirme denetim katmanının testleri.

Bu katmanın hiç birim testi yoktu: gerçek listeler çalıştırılıp raporlara
bakılarak geliştirilmişti (KELIME-HATTI-DEVAM.txt §8'deki bugların
bulunma biçimi de buydu). O yöntem işe yaradı ama her denemede model
çağrısı gerektiriyor ve bir kuralın sessizce bozulduğunu göstermiyor.

Buradaki testler model çağırmıyor: uydurma bir cevap kurup denetimden
geçiriyor. Asıl korudukları şey, çıktı kalitesi kurallarının zamanla
gevşemesi.
"""

from django.test import TestCase

from words.enrich import checks
from words.enrich.schema import Collocation as SCollocation
from words.enrich.schema import Meaning as SMeaning
from words.enrich.schema import Word as SWord


def esdizim(pattern, example="", meaning_tr=""):
    return SCollocation(pattern=pattern, kind="verb_noun",
                        meaning_tr=meaning_tr,
                        example=example or f"They {pattern} every day.")


def anlam(meaning_tr, esdizimler=(), cumleler=None, definition="a definition"):
    return SMeaning(
        meaning_tr=meaning_tr, definition=definition,
        sentiment="neutral", register="neutral", categories=[],
        collocations=list(esdizimler), patterns=[],
        sentences=list(cumleler or []),
    )


class TurkceKarsilikTests(TestCase):
    """
    Ölçüt: "örneği okumayan biri bunu anlayamaz."

    Öğrenci kelime listesine baktığında yanında cümle yok; karşılık
    kendi başına ayakta durmalı.
    """

    def _kodlar(self, metin, kelime="perspicacious"):
        rapor = checks.Rapor()
        checks._turkce_karsilik_denetle(metin, "anlam 1", kelime, rapor)
        return {sorun.kod for sorun in rapor.sorunlar}

    def test_iyelik_eki_dusmus_tamlama_yakalanir(self):
        """
        Gerçek hata: perspicacious -> "sezgi güçlü". Doğrusu "sezgisi
        güçlü"; Türkçede isim+sıfat birleşiğinde ilk öğe iyelik eki alır.
        """
        self.assertIn("turkce_tamlama", self._kodlar("sezgi güçlü, anlayışlı"))
        self.assertIn("turkce_tamlama", self._kodlar("hafıza zayıf"))

    def test_dogru_tamlama_uyari_uretmez(self):
        self.assertNotIn("turkce_tamlama", self._kodlar("sezgisi güçlü, anlayışlı"))
        self.assertNotIn("turkce_tamlama", self._kodlar("hafızası zayıf"))

    def test_sade_sifatlar_temiz_gecer(self):
        for metin in ("anlayışlı, kavrayışlı", "içkin, doğasında olan",
                      "titiz, özenli", "cesaret, yüreklilik"):
            self.assertEqual(self._kodlar(metin), set(), metin)

    def test_tanim_yazilmasi_yakalanir(self):
        """Madde başı yazıyoruz, tanım değil."""
        self.assertIn("karsilik_tanim",
                      self._kodlar("özünde var olan ve kalıcı bir parça"))
        self.assertIn("karsilik_tanim",
                      self._kodlar("bir şey için kullanılan araç"))

    def test_fazla_uzun_karsilik_yakalanir(self):
        uzun = "bir şeyin doğasında olan temel nitelik özellik durum"
        self.assertIn("karsilik_uzun", self._kodlar(uzun))

    def test_ingilizce_karsilik_yakalanir(self):
        self.assertIn("karsilik_ingilizce", self._kodlar("perspicacious"))

    def test_bos_karsilik_patlamaz(self):
        self.assertEqual(self._kodlar(""), set())


class IyelikOnerisiTests(TestCase):
    """
    Rapordaki düzeltme önerisi Türkçe olarak DOĞRU olmalı.

    "sezgisı güçlü" öneren bir rapor, kendi söylediği şeyi yapamıyor
    demektir ve okunmayı bırakır.
    """

    def test_unlu_uyumu(self):
        for govde, beklenen in [("sezgi", "sezgisi"), ("hafıza", "hafızası"),
                                ("göz", "gözü"), ("yorum", "yorumu"),
                                ("düzey", "düzeyi"), ("söz", "sözü")]:
            self.assertEqual(checks._iyelikli_oneri(govde), beklenen, govde)

    def test_unsuz_yumusamasi(self):
        """Çok heceli kelimede son ünsüz yumuşar: odak -> odağı."""
        self.assertEqual(checks._iyelikli_oneri("odak"), "odağı")
        self.assertEqual(checks._iyelikli_oneri("direnç"), "direnci")

    def test_tek_heceli_yumusamaz(self):
        self.assertEqual(checks._iyelikli_oneri("at"), "atı")
        self.assertEqual(checks._iyelikli_oneri("top"), "topu")

    def test_unlu_dusmesi(self):
        for govde, beklenen in [("akıl", "aklı"), ("fikir", "fikri"),
                                ("ağız", "ağzı"), ("şehir", "şehri")]:
            self.assertEqual(checks._iyelikli_oneri(govde), beklenen, govde)

    def test_bos_govde_patlamaz(self):
        self.assertEqual(checks._iyelikli_oneri(""), "")


class AnlamSayisiTests(TestCase):
    """
    Model ikinci anlam üretmeye çok meyilli ve ürettiği ikinci anlam
    çoğu zaman birincinin başka sözcüklerle yazılmış hâli.
    """

    def test_ust_sinir_iki(self):
        self.assertEqual(checks.EN_COK_ANLAM, 2)

    def test_paylasilan_esdizim_ayni_anlam_demektir(self):
        """
        Prompt'un kendi ölçütü: "iki ayrı anlam ancak FARKLI
        collocation'larla kullanılıyorsa vardır." Ölçüt yazılıydı ama
        ölçülmüyordu.
        """
        birinci = anlam("titiz, özenli",
                        [esdizim("meticulous attention"),
                         esdizim("meticulous record")])
        ikinci = anlam("ayrıntıya önem veren",
                       [esdizim("meticulous attention")])
        self.assertEqual(
            checks._paylasilan_esdizim(ikinci, [birinci]),
            "meticulous attention",
        )

    def test_gercekten_farkli_anlamlar_esdizim_paylasmaz(self):
        banka = anlam("banka", [esdizim("open a bank account"),
                                esdizim("central bank")])
        kiyi = anlam("nehir kıyısı", [esdizim("the river bank"),
                                      esdizim("steep bank")])
        self.assertEqual(checks._paylasilan_esdizim(kiyi, [banka]), "")

    def test_esdizimsiz_anlam_paylasim_sayilmaz(self):
        """Eş dizimi olmayan anlam için bu testin söyleyeceği bir şey yok."""
        birinci = anlam("banka", [esdizim("open a bank account")])
        ikinci = anlam("nehir kıyısı", [])
        self.assertEqual(checks._paylasilan_esdizim(ikinci, [birinci]), "")


class YakinAnlamTests(TestCase):
    """
    `_yakin_anlam` NORMALİZE EDİLMİŞ metin bekliyor (çağıranlar öyle
    veriyor). Ham metinle çağrılırsa noktalama kelimeye yapışıyor ve
    "ders," ile "ders" eşleşmiyor — testler de bu sözleşmeye uymalı,
    yoksa çalışan kodu bozuk sanırız.
    """

    def _yakin(self, a, b):
        return checks._yakin_anlam(checks._normalize(a),
                                   {checks._normalize(b)})

    def test_ortusen_anlamlar_yakalanir(self):
        self.assertTrue(self._yakin("ders, konu", "konu, ders"))
        self.assertTrue(self._yakin("uzun ve sıkıcı", "sıkıcı"))

    def test_farkli_anlamlar_ortusmez(self):
        self.assertFalse(self._yakin("banka", "nehir kıyısı"))

    def test_normalize_noktalama_temizliyor(self):
        self.assertEqual(checks._normalize("ders, konu"), "ders konu")


class ListeAyristirmaTests(TestCase):
    """
    Kelime listesi biçimi: her satırda bir kelime, `kelime:tur`,
    `#` ile yorum.

    Satır SONUNDAKİ yorum önce atlanmıyordu ve sessizce türe yapışıyordu
    ("adverb   # DB: decide"). Model şemasındaki Literal'a uymadığı için
    kayıt çöpe gidiyordu — üstelik hata vermeden, kelime "üretilemedi"
    gibi görünerek. Listeyi elle gözden geçirirken satır sonuna not
    düşmek en doğal şey; biçim buna dayanıklı olmalı.
    """

    def _oku(self, icerik):
        # Liste okuyucu enrich_words silinince aile hattına taşındı.
        from words.aile.depo import liste_oku
        return liste_oku(icerik.splitlines())

    def test_satir_sonu_yorumu_atiliyor(self):
        istekler = self._oku("decisively:adverb   # DB: decide/decision\n")
        self.assertEqual(istekler, [("decisively", "adverb")])

    def test_tam_satir_yorumu_atlaniyor(self):
        istekler = self._oku("# başlık\n\nlucid:adjective\n")
        self.assertEqual(istekler, [("lucid", "adjective")])

    def test_tursuz_satir_calisiyor(self):
        self.assertEqual(self._oku("lucid\n"), [("lucid", "")])

    def test_yinelenen_satirlar_tekilleniyor(self):
        istekler = self._oku("lucid:adjective\nlucid:adjective\n")
        self.assertEqual(len(istekler), 1)

    def test_ayni_kelime_farkli_tur_iki_kayit(self):
        """`advocate` hem isim hem fiil — iki ayrı istektir."""
        istekler = self._oku("advocate:noun\nadvocate:verb\n")
        self.assertEqual(istekler, [("advocate", "noun"), ("advocate", "verb")])


class KalipBicimiTests(TestCase):
    """Modelden gelen kalıp yeni gösterime çevrilir (rapor 18.7): "+ noun" yok."""

    def test_kalip_bicimlenir_bilgisiz_kalip_atilir(self):
        from words.enrich.schema import UsagePattern
        a = anlam("ilgili", cumleler=[
            "She is very interested in modern art and history.",
            "He was interested in the job offer.",
            "They are interested in learning Spanish this year.",
            "Few people seemed interested in the old museum.",
            "I am interested in what you have to say.",
        ])
        a.patterns = [
            UsagePattern(pattern="interested in + noun", kind="preposition",
                         example="She is interested in art.", note=""),
            UsagePattern(pattern="be interested", kind="structure",
                         example="She is interested.", note=""),
        ]
        rapor = checks.Rapor()
        bicimler = checks._bicimler("interested", "adjective", "", "")
        self.assertTrue(checks._anlami_denetle(a, "1", bicimler, [], rapor,
                                               "adjective", "interested"))
        self.assertEqual([k.pattern for k in a.patterns], ["interested in sth"])
        self.assertIn("kalip_bicimi", [s.kod for s in rapor.sorunlar])
