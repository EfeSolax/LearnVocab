"""201/202: kalın yok, maddeler kalıp. Kalıptaki bütün içerik kelimeleri (Efe'nin kararı: A); be/have/do/get atlanır."""
import json, re, sqlite3, sys, os
S, hedef = sys.argv[1], sys.argv[2]
db = sqlite3.connect("file:db.sqlite3?mode=ro", uri=True)
VAR = {}
for t, p in db.execute("select lower(text), pos from words_word"):
    VAR.setdefault(t, set()).add(p)
FORM = {}
for s_, t in db.execute("select lower(f.surface), lower(w.text) from words_wordform f join words_word w on w.id=f.word_id"):
    FORM.setdefault(s_, t)
ETIKET = r"\(\s*((?:v|n|adj|adv|pre|prep|conj)(?:\s*phr)?|phr\s*v|phr)\s*\)"
TAG = re.compile(ETIKET, re.I)
POS = {"v": "verb", "n": "noun", "adj": "adjective", "adv": "adverb", "prep": "preposition", "pre": "preposition", "conj": "conjunction"}
ATLA = set("""a an the to of in on at for with from by into about as up out off over down back away through
across along around after before under between among against without within than and or but so if that
sth sb sb's sth's one's oneself yourself someone something somebody s v etc x it its their his her my your our
be am is are was were been being have has had do does did get gets got getting can could will would
this these those there here very more most much many some any no not""".split())
INGILIZ = {"colour": "color", "favourite": "favorite", "neighbour": "neighbor", "theatre": "theater",
           "centre": "center", "maths": "math", "labour": "labor", "behaviour": "behavior", "travelling": "traveling"}
BASLIK = re.compile(r"^\s*(WEEK|MTR|RHO|R\d|REVISION|Additional|METU|DBE|SPAN|The following|\d+\s+[A-Z]|adv:|phr|n:|v:|adj:|pre:|sb:|sth:|NOTE|Jobs)", re.I)
ADLAR = {1: "odtu-201-span-1", 2: "odtu-201-span-2", 3: "odtu-202-span-3", 4: "odtu-202-span-4"}

def kok(w):
    w = INGILIZ.get(w, w)
    return w if w in VAR else FORM.get(w)

def kelimeler(metin, tur):
    """Maddedeki içerik kelimeleri: [(kelime, tür ya da None)]."""
    tekli = tur in POS.values()
    # satır içi etiket: "to need (v) sth", "a strange (adj) mask"
    satir_ici = {}
    for m in re.finditer(r"([A-Za-z][A-Za-z'\-]*)\s*" + ETIKET, metin, re.I):
        e = m.group(2).lower().replace(" ", "")
        if e in POS: satir_ici[m.group(1).lower()] = POS[e]
    metin = TAG.sub(" ", metin).replace("’", "'").replace("≈", " ").replace("+", " ")
    toks = re.findall(r"[A-Za-z][A-Za-z'\-]*", metin)
    out = []
    for i, t in enumerate(toks):
        w = t.lower()
        if w.endswith("'s"): w = w[:-2]
        if w in ATLA or len(w) < 2: continue
        k = kok(w)
        if not k: out.append((w, None, False)); continue
        pos = satir_ici.get(w)
        if not pos and tekli: pos = tur
        if not pos and i and toks[i - 1].lower() == "to" and "verb" in VAR.get(k, set()): pos = "verb"
        out.append((w, pos, True))
    return out

eksik = {}
for i, ad in ADLAR.items():
    paras = json.load(open(f"{S}/kalin{i}.json"))
    satirlar, hafta, yazilan, eks, grup = [], None, None, [], []
    for p in paras:
        t = p["t"].strip()
        m = re.match(r"WEEK\s*(\d+)", t, re.I)
        if m: hafta = m.group(1); grup = []; continue
        tag = re.search(ETIKET + r"\s*$", t, re.I)
        yalniz_tag = re.fullmatch(ETIKET, t, re.I)
        # grup ("white", "a teacher", "to work as" … sonra tek başına "(adj)"): kısa, etiketsiz, nokta yok
        if (not re.search(ETIKET, t, re.I) and not BASLIK.match(t) and len(t.split()) <= 5
                and not t.rstrip().endswith((".", ":")) and not t[:1].isdigit()):
            grup.append(t.lstrip("-– ")); continue
        if yalniz_tag:
            e = yalniz_tag.group(1).lower().replace(" ", "")
            if len(grup) > 1 and grup[0][:1].isupper() and grup[1][:1].islower():
                grup = grup[1:]                 # "Basic colors" gibi grup başlığı
            maddeler = [(g, POS.get(e)) for g in grup]; grup = []
        elif tag and not BASLIK.match(t) or (re.search(ETIKET, t, re.I) and not BASLIK.match(t)):
            e = (tag or re.search(ETIKET, t, re.I)).group(1).lower().replace(" ", "")
            maddeler = [(t, POS.get(e))]; grup = []
            if e in ("phrv", "phr") or e.startswith("phr"):
                maddeler = [(t, "PHRASAL")]
        else:
            if not re.match(r"^[-–]", t): grup = []
            continue
        for metin, tur in maddeler:
            if tur == "PHRASAL":
                ham = re.sub(r"^\s*to\s+", "", TAG.sub("", metin)).strip(" .")
                eks.append(ham.lower()); continue
            for w, pos, var in kelimeler(metin, tur):
                if not var:
                    eks.append(w); continue
                if hafta != yazilan:
                    satirlar.append(f"## {hafta}"); yazilan = hafta
                satirlar.append(f"{w}:{pos}" if pos and w in VAR and pos in VAR.get(w, set()) else w)
    with open(os.path.join(hedef, f"{ad}.txt"), "w") as f:
        f.write(f"# ODTÜ DBE {ad[5:8]} · Span {i} · 2025-26 aktif kelime listesi; ## = hafta. Kalıplardaki içerik kelimeleri (be/have/do/get hariç).\n")
        f.write("\n".join(satirlar) + "\n")
    eksik[ad] = list(dict.fromkeys(eks))
    print(ad, sum(1 for s in satirlar if not s.startswith("##")), "satır; haftalar", [s[3:] for s in satirlar if s.startswith("##")])
    print("   sözlükte yok", len(eksik[ad]), ":", ", ".join(eksik[ad][:60]))
with open(os.path.join(hedef, "odtu-201-sozlukte-yok.txt"), "w") as f:
    f.write("# ODTÜ 201/202 listelerinde olup sözlükte bulunmayanlar (rapor 18.38).\n")
    for ad, v in eksik.items():
        f.write(f"\n# {ad}\n" + "\n".join(v) + "\n")
