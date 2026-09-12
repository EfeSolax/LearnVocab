# -*- coding: utf-8 -*-
"""
Modelin çıktısını denetleyen deterministik katman.

Buradaki hiçbir kontrol modele bir şey sormaz; hepsi kodla ölçülebilir
şeylerdir. "Model hatasını fark edecek kadar zeki mi" sorusuna güvenmek
yerine, hatayı burada yakalıyoruz.

İki seviye var:

    HATA   - bu parça veritabanına giremez. Tek bir anlamı düşürebilir,
             ya da kelimenin tamamını reddedebilir.
    UYARI  - veri yazılır ama işaretlenir; sen gözden geçirirsin.

Denetim aynı zamanda ONARIR: bozuk bir collocation yüzünden 5 iyi cümleyi
çöpe atmak anlamsız. Bozuk parça düşürülür, kalanı yazılır, ne düşürüldüğü
raporlanır.
"""

import re
from dataclasses import dataclass, field

from words import inflect

# İngilizce cümlede Türkçe metin var mı? Yalnızca İngilizcede HİÇ geçmeyen
# harfler sayılır. "ç", "ö", "ü" alıntı kelimelerde geçebiliyor ("façade",
# "über") ve bunları elemek iyi cümleleri çöpe atıyordu.
TURKCE_HARFLER = set("ğışĞİŞ")

# Model alan adlarını bazen İngilizce yazıyor. Listeyi Türkçe verdiğimiz hâlde
# oluyor bu; reddetmek yerine karşılığına çeviriyoruz.
ALAN_KARSILIKLARI = {
    "academic": "Akademik", "everyday": "Gündelik", "general": "Gündelik",
    "daily life": "Gündelik", "psychology": "Psikoloji", "sociology": "Sosyoloji",
    "economics": "Ekonomi", "economy": "Ekonomi", "geography": "Coğrafya",
    "law": "Hukuk", "legal": "Hukuk", "medicine": "Tıp", "medical": "Tıp",
    "history": "Tarih", "politics": "Siyaset", "education": "Eğitim",
    "technology": "Teknoloji", "environment": "Çevre", "business": "İş Dünyası",
    "science": "Bilim", "literature": "Edebiyat",
}

# Collocation değil KALIP olduğunu ele veren yer tutucular. "make a decision"
# somut bir collocation'dır; "be ambiguous about + noun" bir gramer kalıbıdır
# ve hiçbir cümlede birebir geçemez.
YER_TUTUCULAR = ("sth", "sb", "something", "somebody", "someone", "one's",
                 "oneself", "+ noun", "+ verb", "+ adj", "doing sth", "to do sth",
                 "...", "[", "]", "(", ")")

CUMLE_EN_AZ_KELIME = 6
CUMLE_EN_COK_KELIME = 28
EN_COK_ANLAM = 3
BEKLENEN_CUMLE = 5

# Kök olamayacak şeyler: bunlar önek, kelime değil. "undermine" ailesinin
# kökü "under" DEĞİLDİR; öyle sayarsak undermine, understand ve undergo aynı
# aileye düşer ve aile mekanizması anlamını kaybeder.
# Bir phrasal verb FİİLLE başlar: "carry out", "point out". Bunlarla
# başlayan çok kelimeli girdiler ise deyim ya da bağlayıcı ifadedir:
# "in the long run", "on the other hand", "by and large". Onlar `Word`
# değil `Expression` kaydıdır ve kendi hattını bekliyor.
IFADE_BASLANGICLARI = {
    "in", "on", "at", "by", "to", "as", "for", "with", "from", "of", "off",
    "the", "a", "an", "all", "no", "not", "more", "less", "such", "so",
}


def ifade_mi(metin, pos_ipucu=""):
    """
    Çok kelimeli girdi phrasal verb DEĞİL, deyim/bağlayıcı ifade mi?

    Model çağrılmadan önce bakılabilsin diye ayrı bir fonksiyon: böyle bir
    girdi için istek göndermek hem para hem de yanlış veri demek.
    """
    parcalar = (metin or "").strip().lower().split()
    if len(parcalar) < 2:
        return False
    if pos_ipucu == "phrasal_verb":
        return False
    if pos_ipucu:
        return True
    return parcalar[0] in IFADE_BASLANGICLARI


# Anlamı KOPARAN önekler: bunlarla kurulan kelime taban fiilin ailesine
# girmez. "undertake" ile "take", "overcome" ile "come" arasında öğrenciye
# yardımcı olacak bir anlam bağı yok; ama "encourage" ile "courage",
# "disagree" ile "agree" arasında var. Ayrımı buraya koyuyoruz.
#
# Anlamı KORUYAN önekler (un-, dis-, in-, re-, en-, mis-, non-…) burada YOK:
# onlarla kurulanlar taban kelimenin ailesinde kalır.
KOPARAN_ONEKLER = ("under", "over", "with", "fore", "out", "up", "off",
                   "be", "a")

ONEK_KOKLERI = {
    "un", "in", "im", "ir", "il", "dis", "en", "em", "re", "mis", "non",
    "over", "under", "pre", "post", "anti", "sub", "inter", "trans", "super",
    "de", "co", "ex", "semi", "auto", "micro", "macro", "multi",
}

# Anlamın yanına düşülen tür notu: "savunmak, desteklemek (fiil)".
# Bu, modelin BAŞKA BİR TÜRÜN anlamını bu kayda tıkıştırdığını gösterir.
# `advocate` isim ve fiil olarak iki AYRI Word kaydıdır; fiil anlamı isim
# kaydına girerse örnek cümleler de kelimeyi çekimli kullanır ve kayıt bozulur.
TUR_NOTLARI = {
    "fiil": "verb", "f.": "verb", "eylem": "verb",
    "isim": "noun", "i.": "noun", "ad": "noun",
    "sıfat": "adjective", "s.": "adjective",
    "zarf": "adverb", "z.": "adverb",
}

# Sistem sözlüğü varsa kök gerçekten kelime mi diye bakılır. Yoksa bu denetim
# sessizce atlanır — macOS'ta ve çoğu Linux'ta bu dosya hazır gelir.
_SOZLUK = None


def _sozluk():
    """Sistem kelime listesini (varsa) bir kez yükler."""
    global _SOZLUK
    if _SOZLUK is None:
        _SOZLUK = set()
        for yol in ("/usr/share/dict/words", "/usr/dict/words"):
            try:
                with open(yol, encoding="utf-8", errors="ignore") as dosya:
                    _SOZLUK = {s.strip().lower() for s in dosya if s.strip()}
                break
            except OSError:
                continue
    return _SOZLUK


def _bilesik_parcasi_mi(kelime_metni, kok):
    """
    Kelime iki tam kelimenin birleşimi mi, ve kök bunlardan biri mi?

    "breakthrough" = break + through; ama anlamı "break"ten çıkmaz. Bileşik
    kelime kendi ailesini kurar, parçasının ailesine girmez. Aynı şey
    "framework" (frame+work), "long-term", "cost-effective" için de geçerli.

    Her iki parça da en az 4 harf olmalı: "outcome" (out+come) ya da
    "manhood" (man+hood) gibi ekleşmiş biçimler bileşik sayılmaz.
    """
    sozluk = _sozluk()
    if not sozluk:
        return False

    # "able", "less", "ward" sözlükte birer kelimedir ama "considerable"
    # bileşik değil türemiş bir kelimedir. Sağ taraf bir TÜRETME EKİ ise
    # bileşik saymıyoruz — yoksa bütün -able/-less/-ful kelimeleri kendi
    # ailelerinden kopardık.
    TURETME_EKLERI = {
        "able", "ible", "less", "ful", "ness", "ment", "ship", "hood",
        "ward", "wise", "like", "some", "ish", "ant", "ent", "age", "ate",
        "ive", "ous", "ical", "ism", "ist", "ity", "ance", "ence", "tion",
        "sion", "ing", "ally", "arily",
    }

    kucuk = kelime_metni.lower()
    for ayirac in ("-", ""):
        if ayirac and ayirac in kucuk:
            sol, _, sag = kucuk.partition(ayirac)
            parcalar = [(sol, sag)]
        elif not ayirac:
            parcalar = [(kucuk[:i], kucuk[i:]) for i in range(4, len(kucuk) - 3)]
        else:
            continue

        for sol, sag in parcalar:
            if len(sol) < 4 or len(sag) < 4:
                continue
            if sag in TURETME_EKLERI:
                continue
            if sol in sozluk and sag in sozluk and kok in (sol, sag):
                return True
    return False


def kok_gecerli_mi(kok, kelime_metni):
    """
    Aile kökü kabul edilebilir mi? (gecerli_mi, sebep)

    Model ek soyarken var olmayan kelimeler uydurabiliyor: inherent -> "herit",
    ambiguous -> "ambigu", scrutiny -> "scrutin". Bunlar aile adı olarak
    kaydedilirse sözlükte olmayan bir kök doğar ve bir daha düzelmez.
    """
    kok = (kok or "").strip().lower()
    if not kok:
        return False, "boş"
    if kok == kelime_metni.lower():
        return True, ""
    if kok in ONEK_KOKLERI:
        return False, f"'{kok}' bir önek, kök değil"

    # kelime = KOPARAN_ÖNEK + kök ise aynı aileye girmemeli.
    # Yalnızca tam sonekle bakmak yetmiyor: "outstanding" da "stand"a
    # bağlanıyor ama sonu "stand" değil "standing". Kökün kendisi öneki
    # İÇERİYORSA dokunmuyoruz — "overwhelming" -> "overwhelm" doğrudur.
    kucuk = kelime_metni.lower()
    for onek in KOPARAN_ONEKLER:
        if kucuk.startswith(onek) and not kok.startswith(onek) and kok in kucuk:
            return False, (f"'{onek}-' öneki anlamı koparıyor; "
                           f"'{kelime_metni}' '{kok}' ailesine girmez")

    if _bilesik_parcasi_mi(kelime_metni, kok):
        return False, (f"'{kelime_metni}' bileşik bir kelime; '{kok}' onun "
                       f"parçası, ailesi değil")

    from words.models import Word, WordFamily
    if WordFamily.objects.filter(root=kok).exists() or \
       Word.objects.filter(text=kok).exists():
        return True, ""

    sozluk = _sozluk()
    if sozluk and kok not in sozluk:
        return False, f"'{kok}' gerçek bir İngilizce kelime değil"

    return True, ""


@dataclass
class Sorun:
    seviye: str          # "hata" | "uyari"
    kod: str
    mesaj: str

    def __str__(self):
        isaret = "✗" if self.seviye == "hata" else "!"
        return f"{isaret} [{self.kod}] {self.mesaj}"


@dataclass
class Rapor:
    kabul: bool = True
    sorunlar: list = field(default_factory=list)

    def ekle(self, seviye, kod, mesaj):
        self.sorunlar.append(Sorun(seviye, kod, mesaj))
        if seviye == "hata":
            self.kabul = False

    @property
    def hatalar(self):
        return [s for s in self.sorunlar if s.seviye == "hata"]

    @property
    def uyarilar(self):
        return [s for s in self.sorunlar if s.seviye == "uyari"]


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------

# Model tipografik karakterler üretiyor: kıvrık tırnak, uzun tire, bölünmez
# boşluk. "decision‑making" içindeki tire normal tire DEĞİL; hem eşleştirmeyi
# bozuyor hem de veritabanına girdiğinde öğrencinin kopyaladığı metin
# aramalarda bulunamıyor. Girişte bir kez düzeltip kurtuluyoruz.
TIPOGRAFI = {
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"',
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-",
    "\u2014": "-", "\u2015": "-", "\u2212": "-",
    "\u00a0": " ", "\u2009": " ", "\u202f": " ", "\u200b": "",
    "\u2026": "...",
}


def duzelt_tipografi(metin):
    """Kıvrık tırnak, uzun tire ve bölünmez boşlukları düz karşılıklarına çevirir."""
    if not metin:
        return metin
    for eski, yeni in TIPOGRAFI.items():
        metin = metin.replace(eski, yeni)
    return metin


def _normalize(metin):
    """Karşılaştırma için sadeleştirir: küçük harf, tek boşluk, noktalama yok."""
    metin = (metin or "").lower().strip()
    metin = re.sub(r"[^\w\s]", " ", metin, flags=re.UNICODE)
    return re.sub(r"\s+", " ", metin).strip()


def _icerir_mi(cumle, ifade):
    """Cümle, ifadeyi kelime sınırlarına saygılı biçimde içeriyor mu?"""
    if not ifade:
        return False
    desen = r"\b" + r"\s+".join(re.escape(p) for p in ifade.lower().split()) + r"\b"
    return re.search(desen, cumle.lower()) is not None


ARTIKELLER = {"a", "an", "the"}

# Collocation'ların baş fiili çoğunlukla düzensizdir ve cümlede çekimli geçer:
# "make a decision" -> "made a difficult decision". Kural tabanlı gövde çıkarma
# bunları yakalayamaz (make -> mak, made -> mad), bu yüzden sık geçenler elle.
DUZENSIZ_FIILLER = {
    "make": "made|making|makes", "take": "took|taken|taking|takes",
    "give": "gave|given|giving|gives", "get": "got|gotten|getting|gets",
    "go": "went|gone|going|goes", "do": "did|done|doing|does",
    "have": "had|having|has", "put": "putting|puts",
    "bring": "brought|bringing|brings", "keep": "kept|keeping|keeps",
    "hold": "held|holding|holds", "draw": "drew|drawn|drawing|draws",
    "pay": "paid|paying|pays", "lose": "lost|losing|loses",
    "find": "found|finding|finds", "run": "ran|running|runs",
    "come": "came|coming|comes", "see": "saw|seen|seeing|sees",
    "meet": "met|meeting|meets", "set": "setting|sets",
    "lead": "led|leading|leads", "break": "broke|broken|breaking|breaks",
    "build": "built|building|builds", "feel": "felt|feeling|feels",
    "leave": "left|leaving|leaves", "send": "sent|sending|sends",
    "spend": "spent|spending|spends", "stand": "stood|standing|stands",
    "teach": "taught|teaching|teaches", "tell": "told|telling|tells",
    "think": "thought|thinking|thinks", "win": "won|winning|wins",
    "write": "wrote|written|writing|writes", "rise": "rose|risen|rising|rises",
    "fall": "fell|fallen|falling|falls", "grow": "grew|grown|growing|grows",
    "know": "knew|known|knowing|knows", "mean": "meant|meaning|means",
    "speak": "spoke|spoken|speaking|speaks", "be": "is|are|was|were|been|being",
    "lie": "lay|lain|lying|lies", "lay": "laid|laying|lays",
    "sit": "sat|sitting|sits", "rid": "ridding|rids",
    "read": "reading|reads", "hear": "heard|hearing|hears",
    "drive": "drove|driven|driving|drives", "eat": "ate|eaten|eating|eats",
    "choose": "chose|chosen|choosing|chooses", "seek": "sought|seeking|seeks",
    "bear": "bore|borne|bearing|bears", "catch": "caught|catching|catches",
    "cost": "costing|costs", "cut": "cutting|cuts",
    "deal": "dealt|dealing|deals", "fight": "fought|fighting|fights",
    "fly": "flew|flown|flying|flies", "forget": "forgot|forgotten|forgetting|forgets",
    "hide": "hid|hidden|hiding|hides", "hit": "hitting|hits",
    "hurt": "hurting|hurts", "let": "letting|lets",
    "quit": "quitting|quits", "ride": "rode|ridden|riding|rides",
    "sell": "sold|selling|sells", "shake": "shook|shaken|shaking|shakes",
    "shoot": "shot|shooting|shoots", "show": "showed|shown|showing|shows",
    "sleep": "slept|sleeping|sleeps", "spread": "spreading|spreads",
    "steal": "stole|stolen|stealing|steals", "stick": "stuck|sticking|sticks",
    "strike": "struck|striking|strikes", "swear": "swore|sworn|swearing|swears",
    "tear": "tore|torn|tearing|tears", "throw": "threw|thrown|throwing|throws",
    "wear": "wore|worn|wearing|wears", "withdraw": "withdrew|withdrawn|withdrawing|withdraws",
    "prove": "proved|proven|proving|proves", "hang": "hung|hanging|hangs",
    "flee": "fled|fleeing|flees", "freeze": "froze|frozen|freezing|freezes",
    "burst": "bursting|bursts", "cast": "casting|casts",
    "bind": "bound|binding|binds", "bend": "bent|bending|bends",
}

# Önekli birleşikler: "overcome" cümlede "overcame" olarak geçiyor ama listede
# yalnızca "come" var. Öneki ayırıp kökün düzensiz hâllerine ekliyoruz.
# Önek listesi kapalı tutuluyor: açık bırakılsa "surprise" -> "surp"+"rose"
# gibi olmayan biçimler üretilir ve yanlış eşleşme doğar.
FIIL_ONEKLERI = ("a", "be", "over", "under", "with", "out", "up", "fore",
                 "re", "mis", "off", "in", "up")


def duzensiz_formlar(token):
    """Bir fiilin düzensiz biçimleri; önekli birleşikleri de çözer."""
    token = (token or "").lower()
    if token in DUZENSIZ_FIILLER:
        return [token] + DUZENSIZ_FIILLER[token].split("|")

    for kok, formlar in DUZENSIZ_FIILLER.items():
        if len(token) > len(kok) and token.endswith(kok):
            onek = token[: -len(kok)]
            if onek in FIIL_ONEKLERI:
                return [token] + [onek + f for f in formlar.split("|")]
    return []


def _token_deseni(token):
    """
    Tek bir kelimenin, ÇEKİMLİ hâllerini de yakalayan deseni.

    "sustain injuries" kalıbı cümlede "sustained serious injuries" olarak
    geçer: fiil çekimlenmiş, araya kelime girmiş. Birebir arayınca sağlam
    veriyi eliyorduk — kalıbı düşürmek değil, doğru aramak gerekiyordu.
    """
    if token in ARTIKELLER:
        return r"(?:a|an|the)"
    duzensiz = duzensiz_formlar(token)
    if duzensiz:
        return r"(?:" + "|".join(re.escape(f) for f in duzensiz) + r")"
    if len(token) > 3 and token[-1] in "ey":
        return re.escape(token[:-1]) + r"\w{0,4}"
    return re.escape(token) + r"\w{0,3}"


def _icerir_mi_esnek(cumle, ifade):
    """
    Collocation cümlede geçiyor mu — çekime ve araya giren 1-2 kelimeye
    izin vererek. "make a decision" için "made a difficult decision" geçerlidir.
    """
    if not ifade:
        return False
    parcalar = [p for p in re.split(r"\W+", ifade.lower()) if p]
    if not parcalar:
        return False
    # Araya girenler: en fazla 2 kelime ("made A DIFFICULT decision"), ve
    # ayırıcı boşluk olmak zorunda değil — "decision-making" tek kelime gibi
    # yazılıyor ama iki token. Aradaki kelime kesme işareti içerebilir
    # ("a TEACHER'S authority"), o yüzden \w+ değil \S+.
    desen = r"\b" + r"(?:\W+\w+){0,2}\W+".join(
        _token_deseni(p) for p in parcalar
    )
    return re.search(desen, cumle.lower()) is not None


def _yakin_anlam(anahtar, gorulenler):
    """
    Bu anlam, daha önce görülmüş bir anlamla büyük ölçüde örtüşüyor mu?
    Örtüşen varsa onu döndürür. Ortak kelime oranı yarıdan fazlaysa yakın sayılır.
    """
    # "ve", "bir" gibi bağlayıcılar örtüşmeyi yapay olarak düşürüyor.
    dolgu = {"ve", "bir", "ile", "veya", "da", "de", "olan", "olarak"}
    kelimeler = set(anahtar.split()) - dolgu
    if not kelimeler:
        return ""
    for onceki in gorulenler:
        oncekiler = set(onceki.split()) - dolgu
        if not oncekiler:
            continue
        ortak = kelimeler & oncekiler
        if len(ortak) / min(len(kelimeler), len(oncekiler)) >= 0.5:
            return onceki
    return ""


def _ortak_onek(a, b):
    uzunluk = 0
    for x, y in zip(a, b):
        if x != y:
            break
        uzunluk += 1
    return uzunluk


def _bicimler(text, pos, v2, v3):
    """
    Cümlede aranacak yüzey biçimleri.

    Çok kelimeli maddelerde (phrasal verb, kalıp) tam eşleşme aranmaz:
    "be in line with sth" cümlede "is in line with" olarak geçer. Bu yüzden
    çok kelimelilerde İLK anlamlı kelimenin biçimleri aranır.
    """
    parcalar = text.split()
    if len(parcalar) > 1:
        cekirdek = parcalar[0]
        if cekirdek in ("be", "get", "have", "take", "make") and len(parcalar) > 1:
            # "be in line with" -> ikinci kelime daha ayırt edici
            cekirdek = parcalar[1]
        uretilen = [y for y, _t in inflect.forms_for(cekirdek, pos, v2, v3)]
        return list(dict.fromkeys(uretilen + duzensiz_formlar(cekirdek))) or [cekirdek]

    uretilen = [y for y, _t in inflect.forms_for(text, pos, v2, v3)]
    return list(dict.fromkeys(uretilen + duzensiz_formlar(text))) or [text.lower()]


# ---------------------------------------------------------------------------
# Ana denetim
# ---------------------------------------------------------------------------

def _tipografiyi_temizle(kelime):
    """Modelden gelen bütün serbest metin alanlarını düz karakterlere çevirir."""
    kelime.text = duzelt_tipografi(kelime.text)
    kelime.family_root = duzelt_tipografi(kelime.family_root)

    for anlam in kelime.meanings:
        anlam.meaning_tr = duzelt_tipografi(anlam.meaning_tr)
        anlam.definition = duzelt_tipografi(anlam.definition)
        anlam.sentences = [duzelt_tipografi(c) for c in anlam.sentences]
        for coll in anlam.collocations:
            coll.pattern = duzelt_tipografi(coll.pattern)
            coll.meaning_tr = duzelt_tipografi(coll.meaning_tr)
            coll.example = duzelt_tipografi(coll.example)
        for kalip in anlam.patterns:
            kalip.pattern = duzelt_tipografi(kalip.pattern)
            kalip.example = duzelt_tipografi(kalip.example)
            kalip.note = duzelt_tipografi(kalip.note)

    for dost in kelime.false_friends:
        dost.turkish_lookalike = duzelt_tipografi(dost.turkish_lookalike)
        dost.assumed_meaning = duzelt_tipografi(dost.assumed_meaning)
        dost.correct_english = duzelt_tipografi(dost.correct_english)
        dost.note = duzelt_tipografi(dost.note)

    for bag in kelime.relations:
        bag.to_word = duzelt_tipografi(bag.to_word)
        bag.note = duzelt_tipografi(bag.note)


def denetle(kelime, istenen_metin, ozet, alanlar):
    """
    Modelin döndürdüğü `schema.Word`u denetler ve onarır.

    `kelime` yerinde değiştirilir (bozuk parçalar düşürülür).
    Döner: Rapor
    """
    rapor = Rapor()
    _tipografiyi_temizle(kelime)

    if not kelime.found:
        rapor.ekle("hata", "bulunamadi",
                   f"Model kelimeyi üretmedi: {kelime.skip_reason or 'sebep yok'}")
        return rapor

    # --- Kelimenin kendisi ---------------------------------------------
    kelime.text = (kelime.text or "").strip().lower()
    if not kelime.text:
        # Model text alanını boş bıraktı ama anlamları üretmiş olabilir.
        # İstediğimiz kelimeyi zaten biliyoruz; veriyi çöpe atmak yerine
        # onarıyoruz. Hiç anlam da yoksa kurtarılacak bir şey yok demektir.
        if kelime.meanings:
            kelime.text = istenen_metin.strip().lower()
            rapor.ekle("uyari", "bos_kelime",
                       "text alanı boştu; istenen kelime yazıldı.")
        else:
            rapor.ekle("hata", "bos_kelime", "text alanı boş ve hiç anlam yok.")
            return rapor

    if _normalize(kelime.text) != _normalize(istenen_metin):
        rapor.ekle("uyari", "farkli_yazim",
                   f"İstenen '{istenen_metin}', dönen '{kelime.text}'.")

    if kelime.pos not in ("verb", "phrasal_verb") and (kelime.v2Form or kelime.v3Form):
        rapor.ekle("uyari", "gereksiz_fiil_hali",
                   f"pos={kelime.pos} ama v2/v3 dolu; temizlendi.")
        kelime.v2Form = kelime.v3Form = ""
    if kelime.v3Form.strip().lower().endswith("ing"):
        rapor.ekle("uyari", "v3_ing",
                   f"v3Form '{kelime.v3Form}' -ing ile bitiyor; 3. hâl olamaz, temizlendi.")
        kelime.v3Form = ""

    if kelime.pos in ("verb", "phrasal_verb") and not (kelime.v2Form and kelime.v3Form):
        rapor.ekle("uyari", "eksik_fiil_hali", "Fiil ama v2/v3 eksik.")

    kok = kelime.family_root.strip().lower()
    # Gövde karşılaştırması: "reverse" kelimesi "irreversible" içinde birebir
    # geçmez ama gövdesi ("revers") geçer. Sondaki sesli harfi atmadan bakmak
    # doğru kökleri yanlış işaretliyordu.
    govde = kok[:-1] if len(kok) > 4 and kok[-1] in "ey" else kok
    if kok and kok != kelime.text and kok not in kelime.text and \
       govde not in kelime.text and kelime.text not in kok and \
       _ortak_onek(kok, kelime.text) < 2:
        # Sözlükte var ama kelimeyle hiçbir yazım bağı yok: "prevail" ile
        # "prevalent" beş harf paylaşır, ilgisiz bir kelime paylaşmaz.
        rapor.ekle("uyari", "kok_ilgisiz",
                   f"'{kok}' kökünün '{kelime.text}' ile yazım bağı zayıf; "
                   f"gözden geçir.")

    gecerli, sebep = kok_gecerli_mi(kelime.family_root, kelime.text)
    if not gecerli:
        rapor.ekle("uyari", "gecersiz_kok",
                   f"family_root '{kelime.family_root}' kabul edilmedi ({sebep}); "
                   f"'{kelime.text}' kullanıldı.")
        kelime.family_root = kelime.text

    # Çok kelimeli ama phrasal verb değil: bu bir deyim/bağlayıcı ifade.
    # `Expression` kaydı olmalı, `Word` değil. Zorla Word yazmak onu yanlış
    # bir aileye de sokuyor ("on the other hand" -> "on" ailesi).
    if " " in kelime.text and kelime.pos != "phrasal_verb":
        rapor.ekle("hata", "ifade",
                   f"'{kelime.text}' çok kelimeli ve phrasal verb değil "
                   f"(model {kelime.pos} dedi); deyim/bağlayıcı ifade olarak "
                   f"ayrı hatta işlenmeli.")
        return rapor

    bicimler = _bicimler(kelime.text, kelime.pos, kelime.v2Form, kelime.v3Form)

    # --- Zaten kayıtlı anlamlar ----------------------------------------
    mevcut = set()
    for var in ozet["var_olan"]:
        if var.pos == kelime.pos:
            mevcut |= {_normalize(a.meaning_tr) for a in var.meanings.all()}

    # --- Anlamlar -------------------------------------------------------
    if len(kelime.meanings) > EN_COK_ANLAM:
        rapor.ekle("uyari", "fazla_anlam",
                   f"{len(kelime.meanings)} anlam döndü; ilk {EN_COK_ANLAM} alındı.")
        kelime.meanings = kelime.meanings[:EN_COK_ANLAM]

    gorulen_anlam = set()
    saglam_anlamlar = []

    for sira, anlam in enumerate(kelime.meanings, 1):
        etiket = f"anlam {sira}"
        anlam_raporu = _anlami_denetle(anlam, etiket, bicimler, alanlar, rapor,
                                       kelime.pos, kelime.text)
        if not anlam_raporu:
            continue

        anahtar = _normalize(anlam.meaning_tr)
        if anahtar in mevcut:
            rapor.ekle("uyari", "zaten_var",
                       f"{etiket}: '{anlam.meaning_tr}' veritabanında zaten var; atlandı.")
            continue

        # Birebir değil ama pratikte aynı: "ders, konu" ile "konu, ders".
        # Birebir karşılaştırma bunları kaçırıyordu ve aynı listeyi ikinci kez
        # çalıştırmak sözlüğe çift anlam yazıyordu. Liste tekrar tekrar
        # çalıştırılacağı için bu sessizce biriken bir bozulmaydı.
        yakin_mevcut = _yakin_anlam(anahtar, mevcut)
        if yakin_mevcut:
            rapor.ekle("uyari", "zaten_var_yakin",
                       f"{etiket}: '{anlam.meaning_tr}' veritabanındaki "
                       f"'{yakin_mevcut}' ile örtüşüyor; atlandı.")
            continue
        if anahtar in gorulen_anlam:
            rapor.ekle("uyari", "yinelenen_anlam",
                       f"{etiket}: '{anlam.meaning_tr}' cevabın içinde tekrar etti; atlandı.")
            continue

        # Birebir aynı değil ama pratikte aynı olan anlamlar: "sıkıcı" ve
        # "uzun ve sıkıcı" iki satır olmamalı. Silmiyoruz — hangisinin doğru
        # olduğuna kod karar veremez — ama gözden geçirmen için işaretliyoruz.
        yakin = _yakin_anlam(anahtar, gorulen_anlam)
        if yakin:
            rapor.ekle("uyari", "yakin_anlam",
                       f"{etiket}: '{anlam.meaning_tr}' önceki anlamla büyük "
                       f"ölçüde örtüşüyor ('{yakin}'); tek anlam olabilir.")

        gorulen_anlam.add(anahtar)
        saglam_anlamlar.append(anlam)

    kelime.meanings = saglam_anlamlar

    if not kelime.meanings:
        if mevcut:
            rapor.ekle("uyari", "yeni_anlam_yok",
                       "Eklenecek yeni anlam yok; kelime zaten tam.")
        else:
            rapor.ekle("hata", "anlam_yok", "Hiç geçerli anlam üretilemedi.")

    # --- Yanlış dostlar --------------------------------------------------
    saglam_dostlar = []
    for dost in kelime.false_friends:
        if not dost.turkish_lookalike.strip():
            continue
        if _normalize(dost.turkish_lookalike) == _normalize(kelime.text):
            rapor.ekle("uyari", "sahte_yanlis_dost",
                       f"Yanlış dost kelimenin kendisiyle aynı: {dost.turkish_lookalike}")
            continue
        saglam_dostlar.append(dost)
    kelime.false_friends = saglam_dostlar

    # --- Bağlar ----------------------------------------------------------
    saglam_baglar = []
    for bag in kelime.relations:
        hedef = (bag.to_word or "").strip().lower()
        if not hedef:
            continue
        if hedef == kelime.text and bag.to_pos == kelime.pos:
            rapor.ekle("uyari", "kendine_bag", "Kelime kendine bağlanmış; atıldı.")
            continue
        bag.to_word = hedef
        saglam_baglar.append(bag)
    kelime.relations = saglam_baglar

    return rapor


def _anlami_denetle(anlam, etiket, bicimler, alanlar, rapor, kelime_pos, kelime_metni):
    """Tek bir anlamı denetler ve onarır. Anlam kurtarılamazsa False döner."""

    if not anlam.meaning_tr.strip():
        rapor.ekle("uyari", "bos_anlam", f"{etiket}: meaning_tr boş; atlandı.")
        return False

    # Fiil anlamı mastar hâlinde olmalı: "yenmek" evet, "yendi" hayır.
    # Sözlük maddesi çekimli yazılırsa quiz üretimi de, öğrencinin ezberi de
    # bozuluyor — "overcome = yendi" diye öğrenen öğrenci cümlede kullanamaz.
    if kelime_pos in ("verb", "phrasal_verb"):
        parcalar = re.split(r"[,;/]", anlam.meaning_tr)
        if not any(p.strip().lower().endswith(("mak", "mek")) for p in parcalar if p.strip()):
            rapor.ekle("uyari", "mastar_degil",
                       f"{etiket}: fiil anlamı mastar hâlinde değil → "
                       f"'{anlam.meaning_tr}'")

    # Başka türe ait anlam mı? "(fiil)" notu bunu ele veriyor.
    not_eslesme = re.search(r"\(([^)]+)\)\s*$", anlam.meaning_tr)
    if not_eslesme:
        etiket_metni = not_eslesme.group(1).strip().lower()
        baska_tur = TUR_NOTLARI.get(etiket_metni)
        if baska_tur and baska_tur != kelime_pos:
            rapor.ekle("uyari", "baska_tur",
                       f"{etiket}: '{anlam.meaning_tr}' {baska_tur} anlamı ama kayıt "
                       f"{kelime_pos}; atlandı. Ayrıca ekle: "
                       f"{kelime_metni}:{baska_tur}")
            return False
        if baska_tur:
            anlam.meaning_tr = anlam.meaning_tr[:not_eslesme.start()].strip()

    if re.match(r"^\s*\d+\s*[.)]", anlam.meaning_tr):
        anlam.meaning_tr = re.sub(r"^\s*\d+\s*[.)]\s*", "", anlam.meaning_tr)
        rapor.ekle("uyari", "numarali_anlam", f"{etiket}: baştaki numara temizlendi.")

    # --- Alanlar ---------------------------------------------------------
    izinli = {a.lower(): a for a in alanlar}
    gecerli, atilan = [], []
    for ad in anlam.categories:
        anahtar = ad.strip().lower()
        if anahtar in izinli:
            gecerli.append(izinli[anahtar])
        elif ALAN_KARSILIKLARI.get(anahtar, "").lower() in izinli:
            gecerli.append(izinli[ALAN_KARSILIKLARI[anahtar].lower()])
        else:
            atilan.append(ad)
    if atilan:
        rapor.ekle("uyari", "bilinmeyen_alan",
                   f"{etiket}: listede olmayan alan(lar) atıldı: {', '.join(atilan)}")
    # Aynı alan iki kez eşleşmiş olabilir.
    anlam.categories = list(dict.fromkeys(gecerli))

    # --- Cümleler --------------------------------------------------------
    cumleler = [c.strip() for c in anlam.sentences if c and c.strip()]

    if len(cumleler) != BEKLENEN_CUMLE:
        rapor.ekle("uyari", "cumle_sayisi",
                   f"{etiket}: {len(cumleler)} cümle döndü ({BEKLENEN_CUMLE} bekleniyordu).")

    saglam_cumleler, gorulen = [], set()
    for cumle in cumleler:
        anahtar = _normalize(cumle)

        if anahtar in gorulen:
            rapor.ekle("uyari", "yinelenen_cumle", f"{etiket}: aynı cümle iki kez geldi.")
            continue
        if not any(_icerir_mi(cumle, bicim) for bicim in bicimler):
            rapor.ekle("uyari", "kelimesiz_cumle",
                       f"{etiket}: cümlede kelimenin hiçbir biçimi yok → \"{cumle[:70]}\"")
            continue
        if TURKCE_HARFLER & set(cumle):
            rapor.ekle("uyari", "turkce_cumle",
                       f"{etiket}: İngilizce cümlede Türkçe harf var → \"{cumle[:70]}\"")
            continue

        uzunluk = len(cumle.split())
        if uzunluk < CUMLE_EN_AZ_KELIME or uzunluk > CUMLE_EN_COK_KELIME:
            rapor.ekle("uyari", "cumle_uzunlugu",
                       f"{etiket}: {uzunluk} kelimelik cümle → \"{cumle[:70]}\"")

        gorulen.add(anahtar)
        saglam_cumleler.append(cumle)

    anlam.sentences = saglam_cumleler

    if len(saglam_cumleler) < 2:
        rapor.ekle("uyari", "cumlesiz_anlam",
                   f"{etiket}: 2'den az geçerli cümle kaldı; anlam atlandı.")
        return False

    # --- Collocation'lar -------------------------------------------------
    # Yer tutucu içeren bir ifade collocation değil KALIP'tır: "make a decision"
    # cümlede birebir geçer, "be ambiguous about + noun" hiçbir cümlede geçemez.
    # Modelin bu ikisini karıştırması sık; atmak yerine doğru rafa taşıyoruz.
    from words.enrich.schema import UsagePattern as _Kalip

    saglam_coll, gorulen_coll, tasinan = [], set(), []
    for coll in anlam.collocations:
        desen = coll.pattern.strip()
        if not desen or _normalize(desen) in gorulen_coll:
            continue
        gorulen_coll.add(_normalize(desen))
        coll.pattern = desen

        if any(yt in desen.lower() for yt in YER_TUTUCULAR):
            tasinan.append(_Kalip(pattern=desen, kind="structure",
                                  example=coll.example or "",
                                  note=coll.meaning_tr or ""))
            rapor.ekle("uyari", "collocation_kalipti",
                       f"{etiket}: '{desen}' yer tutucu içeriyor; kalıplara taşındı.")
            continue

        if coll.example and not _icerir_mi_esnek(coll.example, desen):
            rapor.ekle("uyari", "collocation_ornegi",
                       f"{etiket}: '{desen}' örnekte geçmiyor → \"{coll.example[:80]}\"; "
                       f"örnek silindi.")
            coll.example = ""
        saglam_coll.append(coll)

    anlam.collocations = saglam_coll
    anlam.patterns = list(anlam.patterns) + tasinan

    # Collocation yalnızca içerik kelimelerinde anlamlı. "whereas" ya da
    # "albeit" için "sık kullanılan kelime eşleşmesi" diye bir şey yok —
    # onların taşıdığı bilgi KALIP'tır. Kalıp üretilmişse de uyarmıyoruz:
    # bilgi kaybolmuş değil, doğru rafa gitmiş.
    ISLEV_TURLERI = ("adverb", "preposition", "conjunction")
    if not saglam_coll and kelime_pos not in ISLEV_TURLERI and not anlam.patterns:
        rapor.ekle("uyari", "collocation_yok", f"{etiket}: hiç collocation üretilmedi.")

    # --- Kalıplar ---------------------------------------------------------
    coll_desenleri = {_normalize(c.pattern) for c in saglam_coll}
    saglam_kalip, gorulen_kalip = [], set()
    for kalip in anlam.patterns:
        desen = kalip.pattern.strip()
        if not desen or _normalize(desen) in gorulen_kalip:
            continue
        if _normalize(desen) in coll_desenleri:
            rapor.ekle("uyari", "kalip_collocation_ayni",
                       f"{etiket}: '{desen}' hem collocation hem kalıp olarak geldi; kalıp atıldı.")
            continue
        gorulen_kalip.add(_normalize(desen))
        kalip.pattern = desen
        saglam_kalip.append(kalip)
    anlam.patterns = saglam_kalip

    return True
