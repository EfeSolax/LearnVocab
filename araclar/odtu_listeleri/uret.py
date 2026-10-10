"""301/302: kalın kelimelerden hazır liste. Bölümler: RHO n / Handout n / Unit n / More to Read II / hafta."""
import json, re, sqlite3, sys, os
S, hedef = sys.argv[1], sys.argv[2]
db = sqlite3.connect("file:db.sqlite3?mode=ro", uri=True)
VAR = {}
for t, p in db.execute("select lower(text), pos from words_word"):
    VAR.setdefault(t, set()).add(p)
SEVIYE = {}
SIRA = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
for t, c, f in db.execute("select lower(text), cefr, coalesce(siklik, 0) from words_word"):
    eski = SEVIYE.get(t)
    SEVIYE[t] = (min(SIRA.get(c, 9), eski[0]) if eski else SIRA.get(c, 9), max(f, eski[1]) if eski else f)
FORM = {}
for s_, t in db.execute("select lower(f.surface), lower(w.text) from words_wordform f join words_word w on w.id=f.word_id"):
    FORM.setdefault(s_, t)
TAG = re.compile(r"\((v|n|adj|adv|prep|conj|conjunction|phrasal v|phrasal verb|phr\.? ?v|phrase|idiom|n\.? ?phrase)\.?\)", re.I)
POS = {"v": "verb", "n": "noun", "adj": "adjective", "adv": "adverb", "prep": "preposition", "conj": "conjunction", "conjunction": "conjunction"}
PHRASAL = re.compile(r"phrasal|phr|idiom|phrase", re.I)
EDAT_FIIL = {"on", "of", "with", "to", "in", "by", "upon", "from", "for", "at", "about", "into"}
AYRI = {"carry on", "take on", "deal with", "hear of", "go on", "put up with", "come up with", "make use of",
        "get rid of", "set off", "take place", "make up", "come across", "look after", "hear about", "result in",
        "look for", "give up", "find out", "point out", "turn out", "set up", "bring up"}
INGILIZ = {"labour": "labor", "behaviour": "behavior", "favour": "favor", "colour": "color", "honour": "honor",
           "humour": "humor", "neighbour": "neighbor", "programme": "program", "theatre": "theater",
           "centre": "center", "defence": "defense", "offence": "offense", "organisation": "organization",
           "harbour": "harbor", "fulfil": "fulfill", "judgement": "judgment", "cousine": "cuisine",
           "emphatize": "empathize", "surunpredictableface": "surface"}
EDAT = {"in", "on", "of", "to", "with", "about", "from", "for", "by", "into", "upon", "as", "at", "against",
        "sth", "smt", "sb", "sb's", "sth's", "doing", "oneself", "yourself", "v1", "ving", "n"}
BASLIK_ATLA = re.compile(r"^\s*(TEXT|Text|READING|COLLOCATIONAL|METU|DBE|ACTIVE|SPAN|30[12]|20[12]|Suggested|Additional|MTR 1 WORD|Fall|Spring|20\d\d)", re.I)

def adaylar(b):
    b = TAG.sub(" ", b).replace("’", "'").rstrip(":")
    b = re.sub(r"\(\s*to\s*\)", " to ", b, flags=re.I)
    b = re.sub(r"\(\s*(\w+)\s*\)\s*(\w+)|\b(\w+)\)(\w+)", lambda m: f"{(m.group(2) or m.group(4))}/{(m.group(1) or m.group(3))}{(m.group(2) or m.group(4))}", b)
    b = re.sub(r"\(.*?\)", " ", b)
    out = []
    for parca in re.split(r"\s*(?:/|>|;|,|\s[xX]\s|\bor\b|\+)\s*", b):
        k = re.findall(r"[A-Za-z][A-Za-z'\-]*", parca.lower())
        while k and k[0] in ("to", "a", "an", "the", "be", "become", "of"): k = k[1:]
        while k and k[-1] in EDAT: k = k[:-1]
        if k: out.append(INGILIZ.get(" ".join(k), " ".join(k)))
    return out

def bolum_adi(t):
    t = t.strip().lstrip("#").strip()
    m = re.match(r"WEEK\s*(\d+)", t, re.I)
    if m: return m.group(1)
    m = re.match(r"RHO\s*(\d+)", t, re.I)
    if m: return f"RHO {m.group(1)}"
    m = re.match(r"Vocabulary List for (?:Reading )?Handout\s*(\d+)", t, re.I)
    if m: return f"Handout {m.group(1)}"
    m = re.match(r"UNIT\s*(\d+)", t, re.I)
    if m: return f"Unit {m.group(1)}"
    if re.match(r"(MTR II|MORE TO READ II)\s*$", t, re.I): return "More to Read II"
    return None

def uret(i, ad, bas_bolum):
    paras = json.load(open(f"{S}/kalin{i}.json"))
    # Bölümlere ayır; sözlük biçimli bölüm: "kelime (n):" satırları çok.
    bolumler, bolum, cari = [], bas_bolum, []
    for p in paras:
        b = bolum_adi(p["t"])
        if b:
            bolumler.append((bolum, cari)); bolum, cari = b, []; continue
        cari.append(p)
    bolumler.append((bolum, cari))
    satirlar, eks, yazilan = [], [], None
    for bolum, ps in bolumler:
        sozluk = sum(1 for p in ps if re.search(r"\)\s*:", p["t"]) or re.search(r"^\S.*\w:\s", p["t"])) >= 5
        bekleyen = []
        def bosalt(liste, tur_varsayilan=None):
            nonlocal yazilan
            for v, pos in liste:
                if " " in v and v not in VAR:
                    uyan = [w for w in v.split() if pos and pos in VAR.get(w, set()) and w not in EDAT]
                    if len(uyan) == 1:
                        v = uyan[0]
                    else:
                        # Kalın kalıp: içindeki B1 ve üstü kelimeler; yoksa en seyreği. Kalıp 18.38 için not edilir.
                        icerik = [INGILIZ.get(w, w) for w in v.split() if w not in EDAT]
                        icerik = [w if w in VAR else FORM.get(w) for w in icerik]
                        icerik = [w for w in icerik if w]
                        secilen = [w for w in icerik if SEVIYE.get(w, (9, 0))[0] >= 3]
                        if not secilen and icerik:
                            secilen = [min(icerik, key=lambda w: SEVIYE.get(w, (9, 0))[1])]
                        if not secilen:
                            eks.append(v); continue
                        bosalt([(w, None) for w in dict.fromkeys(secilen)]); continue
                kok = v if v in VAR else FORM.get(v)
                if not kok:
                    eks.append(v); continue
                satir = f"{v}:{pos}" if pos and pos in VAR.get(kok, set()) else v
                if bolum != yazilan:
                    satirlar.append(f"## {bolum}"); yazilan = bolum
                satirlar.append(satir)
        for p in ps:
            t = p["t"]
            if BASLIK_ATLA.match(t) or t.startswith("*"):
                continue
            etiketler = TAG.findall(t)
            tur = POS.get(etiketler[-1].lower().rstrip(".")) if etiketler else None
            if etiketler and PHRASAL.search(etiketler[-1]) and p["b"]:
                ham = re.sub(r"\s+", " ", TAG.sub("", " ".join(p["b"]))).strip(" .,;:").lower()
                ham = re.sub(r"^\(?to\)?\s+", "", ham)
                parca = ham.split()
                ilk_iki = " ".join([parca[0], parca[1].split("/")[0]]) if len(parca) >= 2 else ham
                deyim = etiketler[-1].lower().startswith(("idiom", "phrase", "n"))
                if not deyim and len(parca) == 1 and "verb" in VAR.get(parca[0], set()):
                    bekleyen.append((parca[0], "verb"))
                elif (not deyim and len(parca) >= 2 and parca[1].split("/")[0] in EDAT_FIIL
                      and ilk_iki not in AYRI and "verb" in VAR.get(parca[0], set())):
                    bekleyen.append((parca[0], "verb"))
                else:
                    eks.append(ham)
                bosalt(bekleyen); bekleyen = []; continue
            kalinlar = p["b"]
            if p.get("u") and any(" " in TAG.sub("", b).strip() for b in p["b"]):
                kalinlar = p["u"]          # kalın kalıp, altı çizili hedef (302 Span 4)
            for b in kalinlar:
                if sozluk:
                    # Sözlük biçimi: yalnızca başlık kelimeleri (yanında tür ya da tanım olan); eş dizimler değil.
                    sonra = t[t.find(b) + len(b):] if b in t else ""
                    if not (TAG.search(b) or b.rstrip().endswith(":") or re.match(r"\s*(\(\w+\.?\))", sonra)):
                        continue
                    btur = TAG.search(b) or TAG.search(sonra[:12])
                    btur = POS.get(btur.group(1).lower().rstrip(".")) if btur else None
                    fiil = bool(re.match(r"\s*\(?to\)?\s", b.lower()))
                    for n_, v in enumerate(adaylar(b)):
                        if fiil and n_ > 0: break          # "to look for sth/a job": yalnızca fiil
                        if fiil and " " in v: v = v.split()[0]
                        bekleyen.append((v, btur or ("verb" if fiil else None)))
                    continue
                for v in adaylar(b):
                    if len(v) > 40: continue
                    if " " not in v:
                        # kalın yarıda kesilmiş ("ethica", "(r)evolutionary"): metindeki tam kelime
                        tam = re.search(r"([a-z]*" + re.escape(v) + r"[a-z]*)", t.lower())
                        if tam and tam.group(1) != v and (tam.group(1) in VAR or tam.group(1) in FORM): v = tam.group(1)
                    fiil = (" " not in v) and re.search(r"\(?\bto\)?\s+" + re.escape(b.strip()), t) is not None
                    bekleyen.append((v, "verb" if fiil else None))
            if sozluk or etiketler or not p["b"] or not any(TAG.search(q["t"]) for q in ps):
                # etiketli satırda ya da hiç etiket olmayan bölümde hemen yaz
                bosalt([(v, f or tur) for v, f in bekleyen]); bekleyen = []
        bosalt(bekleyen)
    with open(os.path.join(hedef, f"{ad}.txt"), "w") as f:
        f.write(f"# ODTÜ DBE {ad[5:8]} · Span {i} · 2025-26 aktif kelime listesi; ## = bölüm (hafta / RHO / handout / ünite). Belgedeki kalın kelimeler.\n")
        f.write("\n".join(satirlar) + "\n")
    eks = list(dict.fromkeys(eks))
    print(ad, sum(1 for s in satirlar if not s.startswith("##")), "satır;", "bölümler:", [s[3:] for s in satirlar if s.startswith("##")])
    print("   sözlükte yok", len(eks), ":", ", ".join(eks))
    return eks

eksik = {}
for i, ad, bas in ((1, "odtu-301-span-1", "RHO 1"), (2, "odtu-301-span-2", "Handout 8"),
                   (3, "odtu-302-span-3", "More to Read II"), (4, "odtu-302-span-4", "Unit 6")):
    eksik[ad] = uret(i, ad, bas)
with open(os.path.join(hedef, "odtu-301-sozlukte-yok.txt"), "w") as f:
    f.write("# ODTÜ 301/302 listelerinde (belgedeki kalın kelimeler) olup sözlükte bulunmayanlar (rapor 18.38).\n")
    for ad, v in eksik.items():
        f.write(f"\n# {ad}\n" + "\n".join(v) + "\n")
