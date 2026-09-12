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
