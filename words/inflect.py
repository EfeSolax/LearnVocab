"""
Çekim biçimi üretimi.

Metinde "encouraged", "families", "ran", "slower" geçer; sözlükte
"encourage", "family", "run", "slow" vardır. Bu modül aradaki köprüyü kuran
`WordForm` satırlarını üretir.

İki kaynak kullanılıyor:

  KURAL   — düzenli çekimler: decide -> decides / deciding / decided
  VERİ    — düzensizler: go -> went / gone, child -> children, good -> better
            Düzensizler kuralla üretilemez. Fiillerde kaynak, kelimenin
            kendi v2Form/v3Form alanları; isim ve sıfatlarda aşağıdaki
            tablolar.

Önemli: çekim yeni bir kelime DEĞİLDİR. "encouraged"ın ayrı bir anlamı,
açıklaması, örnek cümlesi olmaz. Ama `slower` anlam taşır (karşılaştırma)
ve sınavda sorulabilir — bu yüzden her biçim türüyle birlikte kaydedilir.
"""

import re


SESLI = "aeiou"

# Kuralla üretilemeyen çoğullar
DUZENSIZ_COGUL = {
    "child": "children", "man": "men", "woman": "women", "person": "people",
    "foot": "feet", "tooth": "teeth", "goose": "geese", "mouse": "mice",
    "ox": "oxen", "louse": "lice",
    # Akademik metinlerde sık geçen Latince/Yunanca kalıplar
    "analysis": "analyses", "basis": "bases", "crisis": "crises",
    "thesis": "theses", "hypothesis": "hypotheses", "diagnosis": "diagnoses",
    "criterion": "criteria", "phenomenon": "phenomena", "datum": "data",
    "medium": "media", "curriculum": "curricula", "index": "indices",
    "appendix": "appendices", "stimulus": "stimuli", "nucleus": "nuclei",
}

# Çoğulu tekiliyle aynı olanlar
COGULSUZ = {"sheep", "series", "species", "means", "deer", "fish", "aircraft",
            "information", "advice", "research", "evidence", "knowledge"}

DUZENSIZ_SIFAT = {
    "good": ("better", "best"),
    "bad": ("worse", "worst"),
    "far": ("further", "furthest"),
    "little": ("less", "least"),
    "many": ("more", "most"),
    "much": ("more", "most"),
}

# -er/-est almayan, "more/most" ile derecelenen sıfatların tipik sonları.
# Bunlar tek kelimelik çekim üretmez.
UZUN_SIFAT_SONLARI = ("ous", "ful", "less", "ive", "able", "ible", "al", "ic",
                      "ing", "ed", "ish", "ent", "ant", "ary", "ory")


# Son ünsüzü İKİLEYEN çok heceli fiiller. Kural aslında vurguya bağlı
# ("perMIT" -> permitting ama "OFfer" -> offering) ve vurgu bilgisi elimizde
# yok. Tek heceliler her zaman ikiler; çok hecelilerde yalnızca bu liste
# ikiler. Liste dışı kalan bir fiil yanlış çekilirse buraya eklenir.
IKILEYEN = {
    "begin", "forget", "occur", "permit", "prefer", "refer", "regret",
    "admit", "commit", "control", "omit", "submit", "transmit", "upset",
    "equip", "propel", "compel", "rebel", "expel", "patrol", "recur",
    "incur", "deter", "infer", "confer", "transfer", "acquit", "allot",
    "forbid", "forget", "outfit", "unwrap", "kidnap", "worship",
}


def _hece_sayisi(kok):
    """Kaba hece sayımı: ünlü öbeği sayısı."""
    return len(re.findall(r"[aeiouy]+", kok))


def _ikilenir_mi(kok):
    """
    Son ünsüz ikilenmeli mi?

    Eski hâli yalnızca ünsüz-ünlü-ünsüz kalıbına bakıyordu ve çok heceli
    kelimeleri bozuyordu: "misinterpret" -> "misinterpretting". Metinde geçen
    "misinterpreting" yazımı böylece hiçbir kelimeye bağlanamıyordu.
    """
    if not _cvc_mi(kok):
        return False
    if kok in IKILEYEN:
        return True
    return _hece_sayisi(kok) <= 1


def _cvc_mi(kok):
    """
    Son üç harf ünsüz-ünlü-ünsüz mü? Öyleyse son harf ikilenir:
    stop -> stopped, big -> bigger. w/x/y bu kuralın dışında.
    """
    if len(kok) < 3:
        return False
    a, b, c = kok[-3], kok[-2], kok[-1]
    return (a not in SESLI and b in SESLI and c not in SESLI and c not in "wxy")


def _s_eki(kok):
    """Fiilde 3. tekil, isimde çoğul için ortak -s / -es / -ies kuralı."""
    if re.search(r"(s|x|z|ch|sh)$", kok):
        return kok + "es"
    if kok.endswith("o") and not kok.endswith(("oo", "eo")):
        return kok + "es"
    if kok.endswith("y") and len(kok) > 1 and kok[-2] not in SESLI:
        return kok[:-1] + "ies"
    return kok + "s"


def noun_forms(kok):
    """İsmin çoğulu. [(yüzey, tür)] döner."""
    kok = kok.strip().lower()
    if not kok or kok in COGULSUZ:
        return []
    if kok in DUZENSIZ_COGUL:
        return [(DUZENSIZ_COGUL[kok], "plural")]
    if kok.endswith("fe"):
        return [(kok[:-2] + "ves", "plural")]
    if kok.endswith("f") and not kok.endswith(("ff", "ef")):
        return [(kok[:-1] + "ves", "plural")]
    return [(_s_eki(kok), "plural")]


def verb_forms(kok, v2=None, v3=None):
    """
    Fiilin çekimleri. v2/v3 verilmişse düzensiz kabul edilip onlar kullanılır,
    verilmemişse düzenli çekim üretilir.
    """
    kok = kok.strip().lower()
    if not kok:
        return []

    bicimler = [(_s_eki(kok), "third_person")]

    # -ing
    if kok.endswith("ie"):
        bicimler.append((kok[:-2] + "ying", "present_participle"))   # lie -> lying
    elif kok.endswith("e") and not kok.endswith(("ee", "oe", "ye")):
        bicimler.append((kok[:-1] + "ing", "present_participle"))
    elif _ikilenir_mi(kok):
        bicimler.append((kok + kok[-1] + "ing", "present_participle"))
    else:
        bicimler.append((kok + "ing", "present_participle"))

    # 2. ve 3. hâl
    if v2:
        bicimler.append((v2.strip().lower(), "past"))
    if v3:
        bicimler.append((v3.strip().lower(), "past_participle"))

    if not v2 and not v3:
        if kok.endswith("e"):
            duzenli = kok + "d"
        elif kok.endswith("y") and len(kok) > 1 and kok[-2] not in SESLI:
            duzenli = kok[:-1] + "ied"
        elif _ikilenir_mi(kok):
            duzenli = kok + kok[-1] + "ed"
        else:
            duzenli = kok + "ed"
        bicimler.append((duzenli, "past"))
        bicimler.append((duzenli, "past_participle"))

    return bicimler


def _duzenli_gecmisler(kok):
    """
    Düzenli fiilin 2./3. hâli için kabul edilen yazımlar.

    Kural (verb_forms) ikilemeyi vurguya bağlı bilemiyor: embed -> embedded,
    format -> formatted, panic -> panicked. Bunlar yazım farkı, düzensizlik
    değil; hepsi -ed ailesinden sayılıyor.
    """
    kural = dict((tur, yuzey) for yuzey, tur in verb_forms(kok))
    kabul = {kural["past"], kok + "ed", kok + kok[-1] + "ed"}
    if kok.endswith("e"):
        kabul.add(kok + "d")
    if kok.endswith("y"):
        kabul.add(kok[:-1] + "ied")
    if kok.endswith("c"):
        kabul.add(kok + "ked")
    return kabul


def duzensiz_fiil_mi(text, v2=None, v3=None):
    """
    Fiil düzensiz mi? Veritabanında düzenli fiillerin de v2Form/v3Form alanı
    dolu (aimed/aimed); kelime kartı V2 · V3'ü yalnızca düzensizlerde
    gösteriyor (rapor 4.3). Kuralın ürettiğiyle karşılaştırılıyor:
    go/went/gone, cut/cut/cut, flee/fled/fled düzensiz; decide/decided,
    embed/embedded, panic/panicked düzenli.

    Phrasal verb'de ilk kelimeye bakılır: give up / gave up / given up.
    """
    kok = (text or "").strip().lower().split(" ")[0]
    if not kok:
        return False
    kabul = _duzenli_gecmisler(kok)
    for bicim in (v2, v3):
        bicim = (bicim or "").strip().lower().split(" ")[0]
        if bicim and bicim not in kabul:
            return True
    return False


def adjective_forms(kok):
    """
    Sıfatın karşılaştırma ve en üstünlük hâlleri.

    Yalnızca tek kelimeyle derecelenen kısa sıfatlar için üretilir;
    "more important / most important" iki kelime olduğu için biçim kaydı
    oluşturmaz (metinde tek token olarak aranmaz).
    """
    kok = kok.strip().lower()
    if not kok:
        return []
    if kok in DUZENSIZ_SIFAT:
        kars, ust = DUZENSIZ_SIFAT[kok]
        return [(kars, "comparative"), (ust, "superlative")]
    if kok.endswith(UZUN_SIFAT_SONLARI) or len(kok) > 8:
        return []

    if kok.endswith("e"):
        govde = kok[:-1]
    elif kok.endswith("y") and len(kok) > 1 and kok[-2] not in SESLI:
        govde = kok[:-1] + "i"
    elif _ikilenir_mi(kok):
        govde = kok + kok[-1]
    else:
        govde = kok

    return [(govde + "er", "comparative"), (govde + "est", "superlative")]


def forms_for(text, pos, v2=None, v3=None):
    """
    Bir kelimenin bütün çekim biçimleri: [(yüzey, tür)].
    Kelimenin kendisi listeye dahil edilir (tür: "other") ki metinde
    çekimsiz hâline dokunmak da çalışsın.
    """
    text = (text or "").strip().lower()
    if not text:
        return []

    uretilen = [(text, "other")]

    if pos == "noun":
        uretilen += noun_forms(text)
    elif pos == "phrasal_verb" and " " in text:
        # Phrasal verb'de yalnızca FİİL çekimlenir, edat sabit kalır:
        # "carry out" -> "carries out", "carried out", "carrying out".
        # Bütün ifadeye ek getirmek "carry outs" gibi olmayan biçimler üretir
        # ve okuma sayfasında kelimeye dokunmak çalışmaz.
        ilk, _, kalan = text.partition(" ")
        # v2/v3 bütün ifadeyle gelebilir ("carried out"); fiil kısmı yeter.
        v2_ilk = (v2 or "").strip().split(" ")[0] or None
        v3_ilk = (v3 or "").strip().split(" ")[0] or None
        for yuzey, tur in verb_forms(ilk, v2_ilk, v3_ilk):
            uretilen.append((f"{yuzey} {kalan}", tur))
    elif pos in ("verb", "phrasal_verb"):
        uretilen += verb_forms(text, v2, v3)
    elif pos == "adjective":
        uretilen += adjective_forms(text)

    # Aynı yüzey iki kez üretilebilir (düzenli fiillerde past = past_participle);
    # ilk görülen tür korunur.
    gorulen, sonuc = set(), []
    for yuzey, tur in uretilen:
        if yuzey and yuzey not in gorulen:
            gorulen.add(yuzey)
            sonuc.append((yuzey, tur))
    return sonuc


def rebuild_forms(word):
    """Bir Word kaydının WordForm satırlarını yeniden üretir."""
    from .models import WordForm

    word.forms.all().delete()
    WordForm.objects.bulk_create([
        WordForm(word=word, surface=yuzey, kind=tur)
        for yuzey, tur in forms_for(word.text, word.pos, word.v2Form, word.v3Form)
    ])


# ======================================================================
# OTOMATİK ÇEKİM — aile hattı için (manage.py aile_uret)
# ======================================================================
#
# Aile üretiminde model YALNIZCA kelimeyi ve türünü yazıyor. Fiilin v2/v3/
# -ing/-s hâlleri, ismin çoğulu, sıfatın comparative/superlative hâlleri
# buradan, kodla üretiliyor. Sebebi: bunlar muhakeme değil KURAL ve tablo
# işi. Modele yazdırmak hem token harcıyor hem de modelin arada bir
# "analysised" gibi bir şey yazma ihtimalini açık bırakıyor.
#
# İKİ KAYNAK, BİRİ ZORUNLU DEĞİL (words/extract/frequency.py ile aynı yapı):
#
#   1. `lemminflect` paketi (varsa): 100 binden fazla kelimelik bir
#      sözlükten çekim veriyor. Düzensizleri, çok heceli fiillerde ünsüz
#      ikilemeyi (permit -> permitted ama offer -> offered) ve sıfatın
#      -er alıp almadığını SÖZLÜKTEN biliyor. Yalnızca SÖZLÜK kısmı
#      kullanılıyor; sözlükte olmayan kelimede paketin tahmin kipi
#      "importanter" gibi şeyler ürettiği için ona hiç sorulmuyor.
#   2. Kurallar + aşağıdaki düzensiz fiil tablosu (her zaman var).
#
# Her sonuç KAYNAĞINI taşır ("sozluk" / "kural"). Kuralla üretilenler
# raporda ayrıca sayılıyor: kural çok heceli fiillerde yanılabiliyor
# (vurgu bilgisi yok, bkz. IKILEYEN) ve bunun sessiz kalmaması gerekiyor.

# Düzensiz fiiller: kök -> (2. hâl, 3. hâl). "|" ile ayrılan ikinci yazım
# da kabul edilen bir biçim (learned|learnt); ilk yazılan esas alınıyor.
DUZENSIZ_FIIL_TABLOSU = {
    "arise": ("arose", "arisen"), "awake": ("awoke", "awoken"),
    "be": ("was", "been"), "bear": ("bore", "borne"),
    "beat": ("beat", "beaten"), "become": ("became", "become"),
    "begin": ("began", "begun"), "bend": ("bent", "bent"),
    "bet": ("bet", "bet"), "bid": ("bid", "bid"),
    "bind": ("bound", "bound"), "bite": ("bit", "bitten"),
    "bleed": ("bled", "bled"), "blow": ("blew", "blown"),
    "break": ("broke", "broken"), "breed": ("bred", "bred"),
    "bring": ("brought", "brought"), "broadcast": ("broadcast", "broadcast"),
    "build": ("built", "built"), "burn": ("burned|burnt", "burned|burnt"),
    "burst": ("burst", "burst"), "buy": ("bought", "bought"),
    "cast": ("cast", "cast"), "catch": ("caught", "caught"),
    "choose": ("chose", "chosen"), "cling": ("clung", "clung"),
    "come": ("came", "come"), "cost": ("cost", "cost"),
    "creep": ("crept", "crept"), "cut": ("cut", "cut"),
    "deal": ("dealt", "dealt"), "dig": ("dug", "dug"),
    "do": ("did", "done"), "draw": ("drew", "drawn"),
    "dream": ("dreamed|dreamt", "dreamed|dreamt"), "drink": ("drank", "drunk"),
    "drive": ("drove", "driven"), "dwell": ("dwelt|dwelled", "dwelt|dwelled"),
    "eat": ("ate", "eaten"), "fall": ("fell", "fallen"),
    "feed": ("fed", "fed"), "feel": ("felt", "felt"),
    "fight": ("fought", "fought"), "find": ("found", "found"),
    "flee": ("fled", "fled"), "fling": ("flung", "flung"),
    "fly": ("flew", "flown"), "forbid": ("forbade", "forbidden"),
    "forecast": ("forecast", "forecast"), "forget": ("forgot", "forgotten"),
    "forgive": ("forgave", "forgiven"), "forsake": ("forsook", "forsaken"),
    "freeze": ("froze", "frozen"), "get": ("got", "gotten|got"),
    "give": ("gave", "given"), "go": ("went", "gone"),
    "grind": ("ground", "ground"), "grow": ("grew", "grown"),
    "hang": ("hung", "hung"), "have": ("had", "had"),
    "hear": ("heard", "heard"), "hide": ("hid", "hidden"),
    "hit": ("hit", "hit"), "hold": ("held", "held"),
    "hurt": ("hurt", "hurt"), "keep": ("kept", "kept"),
    "kneel": ("knelt|kneeled", "knelt|kneeled"), "know": ("knew", "known"),
    "lay": ("laid", "laid"), "lead": ("led", "led"),
    "lean": ("leaned|leant", "leaned|leant"), "leap": ("leaped|leapt", "leaped|leapt"),
    "learn": ("learned|learnt", "learned|learnt"), "leave": ("left", "left"),
    "lend": ("lent", "lent"), "let": ("let", "let"),
    "lie": ("lay", "lain"), "light": ("lit|lighted", "lit|lighted"),
    "lose": ("lost", "lost"), "make": ("made", "made"),
    "mean": ("meant", "meant"), "meet": ("met", "met"),
    "mow": ("mowed", "mown|mowed"), "partake": ("partook", "partaken"),
    "pay": ("paid", "paid"), "prove": ("proved", "proven|proved"),
    "put": ("put", "put"), "quit": ("quit", "quit"),
    "read": ("read", "read"), "rid": ("rid", "rid"),
    "ride": ("rode", "ridden"), "ring": ("rang", "rung"),
    "rise": ("rose", "risen"), "run": ("ran", "run"),
    "say": ("said", "said"), "see": ("saw", "seen"),
    "seek": ("sought", "sought"), "sell": ("sold", "sold"),
    "send": ("sent", "sent"), "set": ("set", "set"),
    "sew": ("sewed", "sewn|sewed"), "shake": ("shook", "shaken"),
    "shed": ("shed", "shed"), "shine": ("shone", "shone"),
    "shoot": ("shot", "shot"), "show": ("showed", "shown|showed"),
    "shrink": ("shrank", "shrunk"), "shut": ("shut", "shut"),
    "sing": ("sang", "sung"), "sink": ("sank", "sunk"),
    "sit": ("sat", "sat"), "slay": ("slew", "slain"),
    "sleep": ("slept", "slept"), "slide": ("slid", "slid"),
    "smell": ("smelled|smelt", "smelled|smelt"), "sow": ("sowed", "sown|sowed"),
    "speak": ("spoke", "spoken"), "speed": ("sped", "sped"),
    "spell": ("spelled|spelt", "spelled|spelt"), "spend": ("spent", "spent"),
    "spill": ("spilled|spilt", "spilled|spilt"), "spin": ("spun", "spun"),
    "spit": ("spat", "spat"), "split": ("split", "split"),
    "spoil": ("spoiled|spoilt", "spoiled|spoilt"), "spread": ("spread", "spread"),
    "spring": ("sprang", "sprung"), "stand": ("stood", "stood"),
    "steal": ("stole", "stolen"), "stick": ("stuck", "stuck"),
    "sting": ("stung", "stung"), "stink": ("stank", "stunk"),
    "stride": ("strode", "stridden"), "strike": ("struck", "struck"),
    "string": ("strung", "strung"), "strive": ("strove", "striven"),
    "swear": ("swore", "sworn"), "sweep": ("swept", "swept"),
    "swell": ("swelled", "swollen|swelled"), "swim": ("swam", "swum"),
    "swing": ("swung", "swung"), "take": ("took", "taken"),
    "teach": ("taught", "taught"), "tear": ("tore", "torn"),
    "tell": ("told", "told"), "think": ("thought", "thought"),
    "throw": ("threw", "thrown"), "thrust": ("thrust", "thrust"),
    "tread": ("trod", "trodden"), "wake": ("woke", "woken"),
    "wear": ("wore", "worn"), "weave": ("wove", "woven"),
    "weep": ("wept", "wept"), "win": ("won", "won"),
    "wind": ("wound", "wound"), "wring": ("wrung", "wrung"),
    "write": ("wrote", "written"),
}

# Önek + düzensiz fiil: understand, overcome, withdraw, mislead, foresee…
# Kökün düzensiz hâllerine önek ekleniyor. Önek listesi KAPALI: açık
# bırakılsa "surprise" gibi kelimeler "surp + rise" diye bölünürdü.
DUZENSIZ_ONEKLERI = ("under", "over", "with", "out", "up", "fore", "re",
                     "mis", "un", "be", "off", "down", "by")

# Önek + tablodaki fiil gibi görünen ama DÜZENLİ çekilen fiiller.
# relay -> relayed (re + lay DEĞİL), behave -> behaved (be + have DEĞİL).
ONEKLI_DUZENLILER = {"relay", "belie", "belay", "behave", "bespeak"}

# Çoğulu olmayan (sayılamayan) isimler. inflect.COGULSUZ'a ek olarak
# akademik metinlerde sık geçenler. lemminflect bunlara "informations"
# gibi biçimler de veriyor; tablo onun önüne geçiyor.
SAYILAMAYANLAR = COGULSUZ | {
    "equipment", "feedback", "furniture", "homework", "luggage", "baggage",
    "wisdom", "progress", "traffic", "news", "machinery", "software",
    "hardware", "mathematics", "physics", "economics", "politics", "ethics",
    "linguistics", "statistics", "athletics", "data", "media", "criteria",
    "phenomena", "welfare", "health", "wealth", "poverty", "leisure",
    "violence", "courage", "honesty", "happiness", "justice", "safety",
    "pollution", "unemployment", "vocabulary", "grammar", "literature",
}

# Sıfatlarda -er/-est alan iki heceli sonlar (kural kipinde):
# happy -> happier, simple -> simpler, narrow -> narrower, clever -> cleverer
IKI_HECELI_ER_SONLARI = ("y", "le", "ow", "er")

# -er/-est ALMAYAN sıfat sonları: bunlar hep more/most ile derecelenir.
MORE_MOST_SONLARI = ("ed", "ing", "ful", "less", "ous", "ive", "al", "ic",
                     "ish", "able", "ible", "ant", "ent", "ary", "ory")


_lemminflect = None
_lemminflect_denendi = False


def _li():
    """lemminflect varsa döner, yoksa None. Bir kez denenir."""
    global _lemminflect, _lemminflect_denendi
    if not _lemminflect_denendi:
        _lemminflect_denendi = True
        try:
            import lemminflect
            _lemminflect = lemminflect
        except ImportError:
            _lemminflect = None
    return _lemminflect


def lemminflect_var_mi():
    return _li() is not None


def _sozlukten(kelime, upos):
    """
    lemminflect'in SÖZLÜĞÜNDEN çekimler; kelime sözlükte yoksa {}.

    Tireli varyantlar atılıyor ("over-came"): kelimenin kendisi tireli
    değilse bu yazım bizim için gürültü.
    """
    li = _li()
    if li is None:
        return {}
    try:
        ham = li.getAllInflections(kelime, upos=upos)
    except Exception:
        return {}
    temiz = {}
    for etiket, yazimlar in ham.items():
        liste = [y for y in yazimlar if y and ("-" not in y or "-" in kelime)]
        if liste:
            temiz[etiket] = liste
    return temiz


def _zipf(kelime):
    """Sıklık (varyantlar arasında seçim için). wordfreq yoksa 0."""
    try:
        from words.extract import frequency
        return frequency.zipf(kelime)
    except Exception:
        return 0.0


def _tablodan(fiil, derinlik=0):
    """
    Düzensiz fiil tablosu; önekli birleşikleri de çözer. Yoksa None.

    Önek iki kat olabilir: misunderstand = mis + under + stand.
    """
    if fiil in ONEKLI_DUZENLILER:
        return None
    if fiil in DUZENSIZ_FIIL_TABLOSU:
        return DUZENSIZ_FIIL_TABLOSU[fiil]
    if derinlik >= 2:
        return None
    for onek in DUZENSIZ_ONEKLERI:
        govde = fiil[len(onek):]
        if fiil.startswith(onek) and len(govde) >= 2:
            ic = _tablodan(govde, derinlik + 1)
            if ic:
                ekle = lambda b: "|".join(onek + p for p in b.split("|"))  # noqa: E731
                return ekle(ic[0]), ekle(ic[1])
    return None


def _ilk(yazimlar):
    """ "learned|learnt" -> ("learned", ["learnt"]) """
    parcalar = [p for p in (yazimlar or "").split("|") if p]
    return (parcalar[0] if parcalar else ""), parcalar[1:]


def _fiil_cekimi(fiil):
    """
    Tek kelimelik fiilin çekimleri.

    Döner: (sonuc, diger_yazimlar, kaynak)
    """
    diger = []

    tablo = _tablodan(fiil)
    # Önek + düzensiz fiil gibi görünen düzenli fiillerde (relay) sözlük de
    # şaşırabiliyor ("relaid"); bunlar doğrudan kuralla çekiliyor.
    sozluk = {} if fiil in ONEKLI_DUZENLILER else _sozlukten(fiil, "VERB")

    if sozluk.get("VBD"):
        v2s = sozluk["VBD"]
        v3s = sozluk.get("VBN") or v2s
        ings = sozluk.get("VBG") or []
        ss = sozluk.get("VBZ") or []
        # Tablo ile sözlük ayrışırsa:
        #   - fiil tabloda BİREBİR varsa tablo kazanır. Tablo elle yazıldı ve
        #     sözlüğün eksiklerini kapatıyor (sözlükte broadcast -> yalnızca
        #     "broadcasted"); sözlüğün yazımı diğer yazım olarak saklanır.
        #   - fiil tabloya ÖNEK ÇÖZÜMÜYLE eşleştiyse sözlük kazanır: önek
        #     çözümü yanılabilir (be + have), sözlük yanılmaz. Tablonun
        #     yazımı ancak sözlük de kabul ediyorsa esas alınır.
        v2s, v3s = _amerikan_once(v2s), _amerikan_once(v3s)
        ings, ss = _amerikan_once(ings), _amerikan_once(ss)
        v2, v3 = v2s[0], v3s[0]
        if tablo:
            dogrudan = fiil in DUZENSIZ_FIIL_TABLOSU
            t2, t2_diger = _ilk(tablo[0])
            t3, t3_diger = _ilk(tablo[1])
            if dogrudan or t2 in v2s:
                v2 = t2
                diger += [y for y in t2_diger if dogrudan or y in v2s]
            if dogrudan or t3 in v3s:
                v3 = t3
                diger += [y for y in t3_diger if dogrudan or y in v3s]
        diger += [y for y in v2s + v3s if y not in (v2, v3)]
        ing = ings[0] if ings else ""
        s = ss[0] if ss else ""
        diger += [y for y in ings[1:] + ss[1:]]
        kaynak = "sozluk"
    else:
        kural = dict((tur, yuzey) for yuzey, tur in verb_forms(fiil))
        ing = kural.get("present_participle", "")
        s = kural.get("third_person", "")
        if tablo:
            v2, v2_diger = _ilk(tablo[0])
            v3, v3_diger = _ilk(tablo[1])
            diger += v2_diger + v3_diger
        else:
            v2, v3 = kural.get("past", ""), kural.get("past_participle", "")
        kaynak = "kural"

    gorulen, tekil = {v2, v3, ing, s, ""}, []
    for y in diger:
        if y not in gorulen:
            gorulen.add(y)
            tekil.append(y)
    return {"v2Form": v2, "v3Form": v3, "ingForm": ing, "sVersion": s}, tekil, kaynak


# ----------------------------------------------------------------------
# Amerikan yazımı
# ----------------------------------------------------------------------
#
# Veritabanı AMERİKAN yazımıyla tutuluyor (Efe'nin kararı, 19 Eylül):
# analyze, behavior, center, defense, traveled. İngiliz yazımıyla gelen
# kelime (listeden ya da modelden) buradan geçip çevriliyor.
#
# Kural "yazımı değiştir ve sıklığa bak": aday Amerikan yazımı İngilizcede
# İngiliz yazımından DAHA SIK geçiyorsa çevrilir. Sıklık bakılmadan
# çevrilseydi "promise -> promize", "four -> for" gibi şeyler olurdu.
# wordfreq yoksa hiçbir şey çevrilmez.

AMERIKAN_KURALLARI = (
    (r"isation(s?)$", r"ization\1"), (r"ise$", "ize"), (r"ised$", "ized"),
    (r"ising$", "izing"), (r"ises$", "izes"), (r"iser(s?)$", r"izer\1"),
    (r"yse$", "yze"), (r"ysed$", "yzed"), (r"ysing$", "yzing"), (r"yses$", "yzes"),
    (r"our$", "or"), (r"ours$", "ors"), (r"oured$", "ored"), (r"ouring$", "oring"),
    (r"ourable$", "orable"), (r"ourite$", "orite"), (r"ourful$", "orful"),
    (r"([tb])re$", r"\1er"), (r"([tb])res$", r"\1ers"),
    (r"ence$", "ense"),
    (r"lled$", "led"), (r"lling$", "ling"), (r"ller(s?)$", r"ler\1"),
    (r"logue$", "log"),
)
# Bu uzunluğun altındaki kelimelere dokunulmaz (four, tour, acre).
AMERIKAN_EN_KISA = 5

# Sıklık kuralının çözemedikleri: iki yazım da web metninde çok geçiyor
# (theatre İngiliz metinlerinde theater'dan sık) ya da kural dışı.
AMERIKAN_TABLOSU = {
    "theatre": "theater", "theatres": "theaters", "catalogue": "catalog",
    "practise": "practice", "practised": "practiced", "practising": "practicing",
    "cancelled": "canceled", "cancelling": "canceling", "programme": "program",
    "programmes": "programs", "grey": "gray", "tyre": "tire", "jewellery": "jewelry",
    "analogue": "analog", "mould": "mold", "sceptical": "skeptical",
    "sceptic": "skeptic", "scepticism": "skepticism", "ageing": "aging",
    "manoeuvre": "maneuver", "judgement": "judgment", "fulfil": "fulfill",
    "fulfilment": "fulfillment", "enrol": "enroll", "enrolment": "enrollment",
    "counsellor": "counselor", "marvellous": "marvelous", "paediatric": "pediatric",
    "encyclopaedia": "encyclopedia", "aluminium": "aluminum", "plough": "plow",
    "storey": "story", "kerb": "curb", "draught": "draft",
    # 6. ölçüm: moustache kurallara uymuyor (ou -> u yalnızca -our sonunda).
    "moustache": "mustache", "moustaches": "mustaches", "pyjamas": "pajamas",
    "cosy": "cozy", "sulphur": "sulfur", "greyish": "grayish", "cheque": "check",
}


def amerikan(kelime):
    """İngiliz yazımını Amerikan yazımına çevirir; çevrilecek bir şey yoksa aynısı."""
    if kelime in AMERIKAN_TABLOSU:
        return AMERIKAN_TABLOSU[kelime]
    if not kelime or len(kelime) < AMERIKAN_EN_KISA:
        return kelime
    if " " in kelime:   # phrasal verb: yalnızca ilk kelime ("organise into")
        ilk, _, kalan = kelime.partition(" ")
        return f"{amerikan(ilk)} {kalan}"
    try:
        from words.extract import frequency
        if not frequency.wordfreq_var_mi():
            return kelime
    except Exception:
        return kelime
    asil = _zipf(kelime)
    en_iyi, en_iyi_z = kelime, asil
    for desen, yerine in AMERIKAN_KURALLARI:
        aday = re.sub(desen, yerine, kelime)
        if aday != kelime:
            z = _zipf(aday)
            if z > en_iyi_z:
                en_iyi, en_iyi_z = aday, z
    return en_iyi


def _amerikan_once(yazimlar):
    """Varyant listesinde Amerikan yazımını öne alır (travelled/traveled)."""
    yazimlar = list(yazimlar or [])
    for i, y in enumerate(yazimlar):
        if amerikan(y) == y:
            return [y] + yazimlar[:i] + yazimlar[i + 1:]
    return yazimlar


def _hece(kelime):
    """
    Sıfatlar için hece sayımı. _hece_sayisi'ndan farkı sondaki SESSİZ e'yi
    düşmesi: "large" iki değil bir hece, "simple" ise iki hece (-le).
    """
    sayi = len(re.findall(r"[aeiouy]+", kelime))
    if kelime.endswith("e") and not kelime.endswith(("le", "ee")) and sayi > 1:
        sayi -= 1
    return max(sayi, 1)


def _sifat_cekimi(sifat):
    """Döner: (sonuc, diger_yazimlar, kaynak)."""
    if sifat in DUZENSIZ_SIFAT:
        kars, ust = DUZENSIZ_SIFAT[sifat]
        return {"comparative": kars, "superlative": ust}, [], "kural"

    uzun = {"comparative": f"more {sifat}", "superlative": f"most {sifat}"}

    if _li() is not None:
        sozluk = _sozlukten(sifat, "ADJ")
        if sozluk.get("JJR") and sozluk.get("JJS"):
            sozluk["JJR"], sozluk["JJS"] = _amerikan_once(sozluk["JJR"]), \
                _amerikan_once(sozluk["JJS"])
            return ({"comparative": sozluk["JJR"][0], "superlative": sozluk["JJS"][0]},
                    sozluk["JJR"][1:] + sozluk["JJS"][1:], "sozluk")
        # Sözlükte -er hâli yoksa more/most. Tahmin kipine SORULMUYOR
        # ("importanter" üretiyor).
        return uzun, [], "sozluk"

    # --- kural kipi ---
    if " " in sifat or "-" in sifat or sifat.endswith(MORE_MOST_SONLARI):
        return uzun, [], "kural"
    hece = _hece(sifat)
    if hece == 1 or (hece == 2 and sifat.endswith(IKI_HECELI_ER_SONLARI)):
        bicimler = dict((tur, yuzey) for yuzey, tur in _kisa_sifat(sifat))
        return bicimler, [], "kural"
    return uzun, [], "kural"


def _kisa_sifat(kok):
    """-er/-est ile derecelenen sıfatın biçimleri (uzunluk sınırı yok)."""
    if kok.endswith("e"):
        govde = kok[:-1]
    elif kok.endswith("y") and len(kok) > 1 and kok[-2] not in SESLI:
        govde = kok[:-1] + "i"
    elif _cvc_mi(kok) and _hece(kok) == 1:
        govde = kok + kok[-1]
    else:
        govde = kok
    return [(govde + "er", "comparative"), (govde + "est", "superlative")]


def _isim_cekimi(isim):
    """Döner: (sonuc, diger_yazimlar, kaynak). Sayılamayanda sVersion boş."""
    if isim in SAYILAMAYANLAR:
        return {"sVersion": ""}, [], "kural"

    sozluk = _sozlukten(isim, "NOUN")
    if sozluk.get("NNS"):
        adaylar = [y for y in sozluk["NNS"] if y != isim]
        if not adaylar:
            # Sözlük yalnızca tekil biçimi veriyor: ethics, species, data.
            return {"sVersion": ""}, [], "sozluk"
        # Birden çok çoğul varsa en sık kullanılan esas: criteria > criterions.
        adaylar.sort(key=_zipf, reverse=True)
        return {"sVersion": adaylar[0]}, adaylar[1:], "sozluk"

    bicimler = noun_forms(isim)
    return {"sVersion": bicimler[0][0] if bicimler else ""}, [], "kural"


BOS_CEKIM = {"v2Form": "", "v3Form": "", "ingForm": "", "sVersion": "",
             "comparative": "", "superlative": ""}


def cekimler(text, pos):
    """
    Bir kelimenin bütün çekimleri, kullanıcının şemasındaki alan adlarıyla:

        v2Form, v3Form, ingForm, sVersion   (fiil; isimde sVersion = çoğul)
        comparative, superlative            (sıfat; gerekirse "more X")

    Döner: {"cekim": {...6 alan...}, "diger_yazimlar": [...], "kaynak": ...}

    Türe ait olmayan alanlar boş kalır. Phrasal verb'de yalnızca fiil
    çekimlenir, edat sabit kalır: carry out -> carried out.
    """
    text = (text or "").strip().lower()
    sonuc = dict(BOS_CEKIM)
    if not text:
        return {"cekim": sonuc, "diger_yazimlar": [], "kaynak": ""}

    diger, kaynak = [], ""

    if pos == "phrasal_verb" and " " in text:
        fiil, _, kalan = text.partition(" ")
        bicimler, diger, kaynak = _fiil_cekimi(fiil)
        for alan, yuzey in bicimler.items():
            sonuc[alan] = f"{yuzey} {kalan}" if yuzey else ""
        diger = [f"{y} {kalan}" for y in diger]
    elif pos in ("verb", "phrasal_verb"):
        bicimler, diger, kaynak = _fiil_cekimi(text)
        sonuc.update(bicimler)
    elif pos == "noun":
        bicimler, diger, kaynak = _isim_cekimi(text)
        sonuc.update(bicimler)
    elif pos == "adjective":
        bicimler, diger, kaynak = _sifat_cekimi(text)
        sonuc.update(bicimler)

    return {"cekim": sonuc, "diger_yazimlar": diger, "kaynak": kaynak}


# ----------------------------------------------------------------------
# Tür denetimi
# ----------------------------------------------------------------------

_UPOS = {"noun": "NOUN", "verb": "VERB", "adjective": "ADJ", "adverb": "ADV"}


def tur_sozlukte(kelime, tur):
    """
    lemminflect sözlüğü bu kelimeyi BU TÜRDE tanıyor mu?

      True   tanıyor
      False  kelimeyi tanıyor ama bu türde değil (become -> adjective)
      None   karar verilemiyor: paket yok, kelime sözlükte yok ya da tür
             denetlenmeyen bir tür (phrasal_verb, preposition…)

    3. denemede model "become (adjective)", "weak (noun)", "existent (noun)"
    gibi türler uydurdu. Kelime gerçek olduğu için varlık denetimi bunları
    yakalamıyordu; bu fonksiyon yakalıyor.
    """
    li = _li()
    upos = _UPOS.get(tur)
    if li is None or upos is None or " " in (kelime or ""):
        return None
    try:
        lemmalar = li.getAllLemmas(kelime)
    except Exception:
        return None
    if not lemmalar:
        return None
    return upos in lemmalar
