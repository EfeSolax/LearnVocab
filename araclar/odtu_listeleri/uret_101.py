"""101: OLR (altı çizili) + RHO (sözlük biçimi, kalın) -> ODTÜ 101 Span 1 (hafta hafta); Speakout -> ünite ünite."""
import json, re, sqlite3, sys, os, unicodedata
S, hedef = sys.argv[1], sys.argv[2]
db = sqlite3.connect("file:db.sqlite3?mode=ro", uri=True)
VAR = {}
for t, p in db.execute("select lower(text), pos from words_word"):
    VAR.setdefault(t, set()).add(p)
FORM = {}
for s_, t in db.execute("select lower(f.surface), lower(w.text) from words_wordform f join words_word w on w.id=f.word_id"):
    FORM.setdefault(s_, t)
ETIKET = re.compile(r"\(\s*(v|n|adj|adv|pre|prep|n phr|phr v|v phr)\s*\)", re.I)
POS = {"v": "verb", "n": "noun", "adj": "adjective", "adv": "adverb", "pre": "preposition", "prep": "preposition"}
ATLA = set("""a an the to of in on at for with from by into about as up out off over and or but so
sth sb sb's sth's someone something x it its be am is are was were been have has had do does did get can
this that these those there here very i you he she we they my your his her our their me him us them""".split())
KORU = {"with", "without", "by", "in", "on", "at", "to", "also", "too", "both", "next", "near", "together"}   # hedefse alınır
INGILIZ = {"neighbour": "neighbor", "favourite": "favorite", "colour": "color", "theatre": "theater", "centre": "center",
           "travelling": "traveling", "cosy": "cozy", "jewellery": "jewelry"}

def kok(w):
    w = INGILIZ.get(w, w)
    return (w, True) if w in VAR else ((w, True) if w in FORM else (w, False))

def kelimeler(parca, pos=None, hedef_mi=False):
    """Bir parçadan sözlük kelimeleri. Tek kelime hedefse işlev kelimesi de olsa alınır (with, also)."""
    parca = unicodedata.normalize("NFKD", ETIKET.sub(" ", parca).replace("’", "'"))
    parca = "".join(c for c in parca if not unicodedata.combining(c))       # café -> cafe
    parca = re.sub(r"\(.*?\)", " ", parca)
    toks = re.findall(r"[A-Za-z][A-Za-z'\-]*", parca.lower())
    if not toks: return []
    tam = " ".join(t for t in toks if t not in ("a", "an", "the", "to"))
    if " " in tam and tam in VAR: return [(tam, pos)]
    out = []
    for t in toks:
        if t.endswith("'s"): t = t[:-2]
        if t in ATLA and not (hedef_mi and len(toks) == 1 and t in KORU): continue
        w, var = kok(t)
        out.append((w, pos if var and pos in VAR.get(w, set()) else None, var))
    return [(w, p) for w, p, v in out if v] + [(w, "YOK") for w, p, v in out if not v]

def olr():
    bolumler = {}; hafta = None
    for x in json.load(open(f"{S}/olr.json")):
        m = re.match(r"\s*WEEK\s*(\d+)", x["t"], re.I)
        if m: hafta = m.group(1); continue
        if hafta is None or x["b"]: continue          # kalın = metin başlığı
        for u in x["u"]:
            for parca in re.split(r"\s*/\s*", u):
                bolumler.setdefault(hafta, []).extend(kelimeler(parca, hedef_mi=True))
    return bolumler

def rho():
    bolumler = {}; bolum = None
    for x in json.load(open(f"{S}/rho.json")):
        t = x["t"]
        m = re.search(r"Week\s*(\d+)", t, re.I) if t.upper().startswith("RHO") else None
        if m: bolum = m.group(1); continue
        if re.match(r"\s*Additional Vocabulary", t, re.I): bolum = "Additional Vocabulary"; continue
        if bolum is None or t.lstrip().startswith(("-", "Collocation")): continue
        for b in x["b"]:
            sonra = t[t.find(b) + len(b):] if b in t else ""
            e = ETIKET.search(b) or (ETIKET.match(sonra.lstrip()) if sonra else None)
            if not (e or b.rstrip().endswith(":")): continue
            pos = POS.get(e.group(1).lower()) if e else None
            for parca in re.split(r"\s*(?:/|,|\sX\s)\s*", b.rstrip(":")):
                fiil = parca.strip().lower().startswith("to ")
                bolumler.setdefault(bolum, []).extend(kelimeler(parca, pos or ("verb" if fiil else None), hedef_mi=True))
    return bolumler

def tamamla(b, t):
    """Yarım kalın ("ian" -> Argentinian, "isten" -> listen): satırdaki tam kelime."""
    ilk, _, kalan = b.strip().partition(" ")
    if kok(ilk.lower())[1]: return b
    m = re.search(r"([A-Za-zé]*" + re.escape(ilk) + r"[A-Za-zé]*)", t)
    return (m.group(1) + (" " + kalan if kalan else "")) if m else b

ULKE_YANLIS = {"polish", "turkey", "china", "south"}

def speakout():
    bolumler = {}; bolum = None
    for x in json.load(open(f"{S}/so.json")):
        t = x["t"].strip()
        m = re.match(r"UNIT\s*(\d+)", t, re.I)
        if m: bolum = f"Unit {m.group(1)}"; continue
        if re.match(r"LEAD-IN", t, re.I): bolum = "Lead-in"; continue
        if bolum is None or "(p." in t or t.lower().startswith(("legend", "n:")): continue
        if "plural forms" in t: continue
        if x["b"] and not (len(x["b"]) == 1 and x["b"][0] == t):
            for b in (tamamla(b, t) for b in x["b"]):
                e = ETIKET.search(t[t.find(b):t.find(b) + len(b) + 8]) if b in t else None
                for parca in re.split(r"\s*/\s*", b):
                    bolumler.setdefault(bolum, []).extend(kelimeler(parca, POS.get(e.group(1).lower()) if e else None, hedef_mi=True))
            continue
        if x["b"]: continue                                        # kalın başlık
        cumle = t.startswith("-") or t.endswith(("?", "!")) or (t[:1].isupper() and len(t.split()) > 3)
        if cumle or len(t.split()) > 6: continue
        for parca in re.split(r"\s*/\s*|\s{3,}", t.lstrip("* ")):
            # Ülke tablosu: Poland/Turkey/China başka anlamdaki kelimelerle eşleşmesin (polish, turkey, china)
            bolumler.setdefault(bolum, []).extend((w, p) for w, p in kelimeler(parca) if w not in ULKE_YANLIS)
    return bolumler

def yaz(ad, baslik, parcalar, sira_bolum):
    satirlar, eks, gorulen = [f"# {baslik}"], [], set()
    for bolum in sira_bolum:
        govde = []
        for w, p in sum((pr.get(bolum, []) for pr in parcalar), []):
            if p == "YOK": eks.append(w); continue
            govde.append(f"{w}:{p}" if p else w)
        if govde: satirlar += [f"## {bolum}"] + govde
    open(os.path.join(hedef, f"{ad}.txt"), "w").write("\n".join(satirlar) + "\n")
    eks = list(dict.fromkeys(eks))
    print(ad, sum(1 for s in satirlar if not s.startswith("#")), "satır; bölümler", [s[3:] for s in satirlar if s.startswith("##")])
    print("   sözlükte yok", len(eks), ":", ", ".join(eks))
    return eks

o, r_, so = olr(), rho(), speakout()
so = {k: [(w, p) for w, p in v if w not in ULKE_YANLIS] for k, v in so.items()}   # Polish -> polish (cilalamak) olmasın
haftalar = sorted(set(o) | {k for k in r_ if k.isdigit()}, key=int) + [k for k in r_ if not k.isdigit()]
e1 = yaz("odtu-101-span-1", "ODTÜ DBE 101 · Span 1 · 2025-26: OLR 0.5 (altı çizili) ve RHO'lar (kalın); ## = hafta.", [o, r_], haftalar)
e2 = yaz("speakout-a0-a1", "Speakout (A0–A1) · ODTÜ DBE 101 · 2025-26 aktif kelime listesi; ## = ünite.", [so], list(so))
with open(os.path.join(hedef, "odtu-101-sozlukte-yok.txt"), "w") as f:
    f.write("# ODTÜ 101 ve Speakout (A0–A1) listelerinde olup sözlükte bulunmayanlar (rapor 18.38).\n")
    f.write("\n# odtu-101-span-1\n" + "\n".join(e1) + "\n\n# speakout-a0-a1\n" + "\n".join(e2) + "\n")
