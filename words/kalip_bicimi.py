"""
Kalıp gösterimi (Efe'nin kararı, 7 Ekim; rapor 18.7): öğrenci sözlüklerindeki gibi
`depend on sb/sth`, `suggest doing sth`, `decide to do sth`, `insist that …`.

- "+" işareti ve "noun", "gerund", "verb-ing" gibi dilbilgisi terimleri kullanılmaz.
- Kişi için sb, şey için sth; ikisi de olabiliyorsa sb/sth.
- Yalnızca "bu kelime nesne alır" diyen kalıp (`repair sth`, `be stainless`) bilgi
  taşımaz, silinir. sb/sth ile yazılamayan yer tutucu (adjective, preposition,
  place…) içeren kalıp da silinir.

bicimle(kalip, kelime, ornek) -> (yeni kalıp, None) ya da (None, silme sebebi).
Saf fonksiyon; veritabanına dokunmaz.
"""
import re

KISI = set("""
me you him her us them someone somebody everyone everybody anyone anybody nobody people
person man woman men women child children kid kids boy boys girl girls baby babies
student students pupil pupils teacher teachers friend friends family families parent parents
mother father mom dad son daughter brother sister husband wife partner partners colleague
colleagues employee employees staff worker workers customer customers client clients patient
patients doctor doctors nurse nurses officer officers police manager managers boss leader
leaders member members player players fan fans audience crowd public citizen citizens voter
voters reader readers viewer viewers user users visitor visitors guest guests neighbor
neighbors neighbour neighbours stranger strangers owner owners driver drivers director
author authors writer writers artist artists candidate candidates suspect suspects victim
victims team government committee board jury court enemy enemies opponent opponents rival
rivals soldier soldiers troops king queen president minister ministers official officials
judge judges lawyer lawyers expert experts scientist scientists researcher researchers
volunteer volunteers residents resident tourists tourist passengers passenger crew relatives
relative grandparents grandmother grandfather uncle aunt cousin cousins guests mentor coach
classmates classmate teammates teammate peers peer adults adult teenagers teenager boys
""".split())

ATLA = {"a", "an", "the", "his", "her", "their", "my", "your", "our", "its", "this", "that",
        "these", "those", "some", "any", "every", "each", "all", "two", "three", "several",
        "many", "new", "young", "old", "local", "other"}

# Bu terimler sb/sth ile yazılamaz: kalıp silinir.
YAZILAMAZ = re.compile(
    r"^(adjectives?|adj|adverbs?|adv|prepositions?|prep|place|location|time|period|number|"
    r"amount|quantity|date|name|phrase|subject|pronoun|value|color|colour|language|size|"
    r"degree|direction|duration|measurement|unit|percentage|price|past participle|"
    r"participle|modal|article|determiner|conjunction|destination|year|age)$", re.I)

# "+ source", "+ topic" gibi genel ad yer tutucuları: sth olur.
GENEL = re.compile(
    r"^(the |a |an )?(source|field|topic|area|item|issue|problem|task|goal|target|situation|"
    r"idea|information|document|data|money|concept|matter|context|process|system|method|"
    r"product|service|material|substance|food|quality|action|activity|event|condition|cause|"
    r"result|feeling|emotion|reason|purpose|organization|organisation|group|company|"
    r"institution|object|thing|content|text|file|question|plan|project|work|effect)s?$", re.I)

_ISIM = re.compile(r"^(the |a |an )?(noun phrases?|nouns?|np|objects?|plural noun|"
                   r"something|thing|things|sth|sb/sth|someone/something|___+|"
                   r"(proper |countable |uncountable |abstract )?nouns?)$", re.I)
_KISI = re.compile(r"^(someone|somebody|person|people|sb|a person|the person)$", re.I)
_ING = re.compile(r"^(gerund|verb-?ing|v-?ing|-ing( form)?|doing( sth| something)?|"
                  r"verb \+ -?ing|present participle)$", re.I)
_MASTAR = re.compile(r"^(to[- ]infinitive|infinitive|to do( sth| something)?|to \+ verb|"
                     r"to verb)$", re.I)
_FIIL = re.compile(r"^(verb|base verb|bare infinitive|base form)$", re.I)
_YAN = re.compile(r"^(that[- ]clause|clause|wh-clause|wh- clause|sentence|statement)$", re.I)
_BAGLAC = ("that", "whether", "if", "how", "what", "who", "whom", "why", "when", "where",
           "which", "because", "although", "though", "unless", "until", "while", "as",
           "so", "once", "before", "after", "since", "than", "then", "and", "but", "or")


_EDAT = {"with", "to", "for", "on", "at", "about", "from", "of", "in", "into", "up", "down",
         "out", "off", "over", "by", "as", "against", "toward", "towards", "upon", "onto"}


def _parantez(m):
    ic = m.group(1).strip()
    if re.search(r"noun|verb|someone|something|clause|adjective|object|purpose|person|place|"
                 r"time|gerund|infinitive|sb|sth", ic, re.I):
        return f" + {ic} + "
    if all(x.strip().lower() in _EDAT for x in ic.split("/")):
        return ic.replace(" ", "")
    return ""


def _kok(kelime):
    return kelime.lower()[:max(3, len(kelime) - 2)]


def _kisi_mi(oncesi, ornek):
    """Yer tutucudan önceki sözcükleri örnekte bulur, ardındaki ilk sözcüğe bakar."""
    if not ornek or not oncesi:
        return None
    sozler = re.findall(r"[A-Za-z'-]+", ornek)
    kucuk = [s.lower() for s in sozler]
    son = oncesi[-1].lower()
    for i, s in enumerate(kucuk):
        if s == son or (len(son) > 3 and s.startswith(son[:max(3, len(son) - 2)])):
            for j in range(i + 1, min(i + 5, len(sozler))):
                if kucuk[j] in ATLA:
                    continue
                if kucuk[j] in KISI or (sozler[j][0].isupper() and j > 0):
                    return True
                return False
    return None


def _yer_tutucu(x):
    x = x.strip()
    if re.match(r"^pronoun$", x, re.I):
        return "sb"
    if _FIIL.match(x):
        return "do sth"
    if _KISI.match(x):
        return "sb"
    if _ISIM.match(x) or GENEL.match(x):
        return "ISIM"
    if _ING.match(x):
        return "doing sth"
    if _MASTAR.match(x):
        return "to do sth"
    return None


def _sb_sth(oncesi, ornek, kisi=False):
    if kisi:
        return "sb"
    karar = _kisi_mi(oncesi, ornek)
    if karar is True:
        return "sb"
    if karar is False:
        return "sth"
    return "sb/sth"


def bicimle(kalip, kelime, ornek="", tur=""):
    p = (kalip or "").strip()
    p = p.replace("“", '"').replace("”", '"')
    p = re.sub(r"\*{1,2}([^*]+)\*{1,2}|<([^>]+)>", lambda m: f" + {m.group(1) or m.group(2)} + ", p)
    p = p.replace("*", "")
    p = re.sub(r"\b(infinitive \(to\)|\(to\) infinitive|\(to\) verb)", " + to do sth + ", p, flags=re.I)
    p = re.sub(r"\((e\.g\.|eg|i\.e\.|such as)[^)]*\)", "", p, flags=re.I)
    p = re.sub(r"\[([^\]]+)\]", r"+ \1 +", p)
    p = re.sub(r"\(([^)]+)\)", _parantez, p)
    p = re.sub(r"\bverb\s*\+\s*-?ing\b", "+ verb-ing +", p, flags=re.I)
    p = re.sub(r"\(?verb\)?ing\b", "+ verb-ing +", p, flags=re.I)
    p = re.sub(r"\bto\s*\+\s*(verb|infinitive|base verb|base form)\b|\bto-infinitive\b",
               "+ to do sth +", p, flags=re.I)
    p = re.sub(r"\bthat\s*\+\s*clause\b|\bthat-clause\b", "that §", p, flags=re.I)
    p = re.sub(r"\b(in order|so as) to\s*(\.\.\.|…|_{2,})", r"\1 + to do sth + ", p, flags=re.I)
    baglac = "|".join(_BAGLAC + ("as if", "as though", "so that", "even if", "even though"))
    p = re.sub(rf"\b({baglac})\s*(\.\.\.|…)", r"\1 §", p, flags=re.I)
    p = re.sub(r"^(\.\.\.|…)\s*,", "§,", p)
    p = re.sub(r",\s*(\.\.\.|…)$", ", §", p)
    p = re.sub(r"\.\.\.|…|_{2,}", " + ___ + ", p)
    p = re.sub(r"(?<![\w'])([XYZ])(?![\w'])", r" + ___ + ", p)

    parcalar = [s.strip(" ") for s in p.split("+")]
    kok = [_kok(k) for k in kelime.split()]
    cikti = []
    for parca in parcalar:
        if not parca:
            continue
        oncesi = " ".join(cikti).split()
        if "/" in parca and all(_yer_tutucu(x) for x in parca.split("/")):
            secenek = []
            for x in parca.split("/"):
                y = _yer_tutucu(x)
                y = _sb_sth(oncesi, ornek) if y == "ISIM" else y
                if y not in secenek:
                    secenek.append(y)
            cikti.append("/".join(secenek))
            continue
        if YAZILAMAZ.match(parca) or re.match(r"^(the |a |an )?(adjective|adverb|preposition|"
                                              r"place|location)s?\s*(\(.*\))?$", parca, re.I):
            return None, f"yazılamayan yer tutucu: {parca}"
        if _KISI.match(parca):
            cikti.append("sb")
        elif _ISIM.match(parca):
            cikti.append(_sb_sth(oncesi, ornek))
        elif _ING.match(parca):
            cikti.append("doing sth")
        elif _MASTAR.match(parca):
            cikti.append("to do sth")
        elif _FIIL.match(parca):
            if not (oncesi and any(oncesi[-1].lower().startswith(k) for k in kok)):
                cikti.append("do sth")
        elif GENEL.match(parca):
            cikti.append("sth")
        elif _YAN.match(parca):
            onceki = oncesi[-1].lower() if oncesi else ""
            bag = ""
            if onceki and onceki not in _BAGLAC and not onceki.endswith((",", ";", ":")) \
                    and tur not in ("adverb", "conjunction", "preposition", "expression"):
                bag = "wh- " if parca.lower().startswith("wh") else "that "
            if cikti and onceki.endswith(","):
                cikti[-1] = cikti[-1]
            cikti.append(bag + "§")
        else:
            cikti.append(parca)
    p = " ".join(cikti)

    # Düz yazıdaki biçimler
    p = re.sub(r"\bto verb\b", "to do sth", p, flags=re.I)
    p = re.sub(r"\b(sb|sth)\.", r"\1", p)
    p = re.sub(r"\b(noun|pronoun)/(noun|pronoun)\b", "sb/sth", p, flags=re.I)
    p = re.sub(r"\b(someone|somebody)('s)?\b", lambda m: "sb" + (m.group(2) or ""), p, flags=re.I)
    p = re.sub(r"\bsomething\b", "sth", p, flags=re.I)
    p = re.sub(r"\bsb or sth\b|\bsomeone/something\b", "sb/sth", p)
    p = re.sub(r"\b(sth|sb|sb/sth)( (sth|sb|sb/sth))+\b(?! sth)", lambda m: m.group(0)
               if len(set(m.group(0).split())) > 1 else m.group(1), p)
    p = re.sub(r"\bdoing sth (sth|sb/sth)\b", "doing sth", p)
    p = re.sub(r"\bto do sth (sth|sb/sth)\b", "to do sth", p)
    p = p.replace("§", "…")
    p = re.sub(r"\s{2,}", " ", p).strip(" ,;.")
    if re.match(r"^to\s+(?!do\b|…)", p, re.I) and not p.lower().startswith(("to and", "to be sure")):
        p = p[3:].strip()
    if not p:
        return None, "boş"
    terim = re.search(r"\b(nouns?|verbs?|gerunds?|clauses?|adjectives?|adverbs?|infinitives?|"
                      r"pronouns?|participles?|phrasal|preposition)\b", p, re.I)
    if terim and terim.group(0).lower() not in kelime.lower():
        return None, f"dilbilgisi terimi kaldı: {terim.group(0)}"

    # Bilgi taşımayan kalıp: kelimenin kendisi, be/a/the ve yer tutuculardan ibaret.
    bos = {"be", "being", "been", "is", "are", "was", "a", "an", "the", "sb", "sth",
           "sb/sth", "…", "sb's", "one's", "very", "really", "so", "too", "quite"}
    kalan = []
    for i, t in enumerate(re.findall(r"[\w/'…-]+", p.lower())):
        if t in bos or any(t.startswith(k) for k in kok):
            continue
        if i == 0 and t == "do":
            continue
        kalan.append(t)
    if kalan in ([], ["do"]):
        return None, "bilgi taşımıyor"
    return p, None
