"""
Hedefi yalnızca altı çizili, etiketsiz, hafta hafta listeler (ODTÜ 502 Span 3–4) → hazır liste dosyası.

    .venv/bin/python -I araclar/odtu_listeleri/docx_bicim.py "502 Span3.docx" <klasör>/s3.json
    python3 araclar/odtu_listeleri/uret_alti_cizili.py <klasör>/s3.json veri/hazir_listeler odtu-502-span-3

Altı çizili parça: "(in)convenient" -> convenient, inconvenient; "to occur" -> occur (fiil); tek başına
edat ("with", "for", "back") atlanır; kalıp ("have a profound impact on") sözlükte yoksa içindeki B1 ve
üstü kelimeler. Sözlükte olmayanlar <ad>-sozlukte-yok.txt'ye (18.38).
"""
import json
import os
import re
import sqlite3
import sys

BAS = {"to", "be", "become", "get", "have", "a", "an", "the", "some", "s.o", "so"}
EDAT = {"in", "on", "of", "to", "with", "about", "from", "for", "by", "into", "upon", "as", "at", "against",
        "back", "out", "up", "down", "off", "away", "over", "between", "among", "sth", "sb", "s", "o",
        "someone", "something", "and", "or", "the", "a", "an"}
SIRA = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}


def main(json_yolu, hedef, ad):
    db = sqlite3.connect("file:db.sqlite3?mode=ro", uri=True)
    var, seviye = {}, {}
    for t, p, c in db.execute("select lower(text), pos, cefr from words_word"):
        var.setdefault(t, set()).add(p)
        seviye[t] = min(seviye.get(t, 9), SIRA.get(c, 9))
    form = {s: t for s, t in db.execute(
        "select lower(f.surface), lower(w.text) from words_wordform f join words_word w on w.id=f.word_id")}

    def kok(w):
        return w if w in var else form.get(w)

    satirlar, yok, hafta = [], [], None
    for x in json.load(open(json_yolu)):
        m = re.match(r"\s*WEEK\s*(\d+)", x["t"], re.I)
        if m:
            hafta = m.group(1)
            satirlar.append(f"## {hafta}")
            continue
        if hafta is None or x["b"]:
            continue                                   # kalın: metin başlığı
        for u in x["u"]:
            u = u.replace("’", "'")
            u = re.sub(r"\((\w+)\)(\w+)", r"\2/\1\2", u)          # (in)convenient
            for parca in re.split(r"\s*/\s*", u):
                k = re.findall(r"[A-Za-z][A-Za-z'\-]*", parca.lower())
                fiil = bool(k) and k[0] == "to"
                while k and k[0] in BAS: k = k[1:]
                while k and k[-1] in EDAT: k = k[:-1]
                if not k:
                    continue
                metin = " ".join(k)
                if len(k) == 1 or metin in var:
                    w = kok(metin)
                    if not w:
                        yok.append(metin)
                        continue
                    satirlar.append(f"{metin}:verb" if fiil and len(k) == 1 and metin in var and "verb" in var[metin] else metin)
                    continue
                icerik = [kok(w) for w in k if w not in EDAT and w not in BAS]
                secilen = [w for w in icerik if w and seviye.get(w, 9) >= 3]
                if not secilen:
                    yok.append(metin)
                satirlar.extend(dict.fromkeys(secilen))

    baslik = f"ODTÜ DBE {ad[5:8]} · Span {ad[-1]} · 2025-26 aktif kelime listesi; ## = hafta. Belgedeki altı çizili kelimeler."
    with open(os.path.join(hedef, f"{ad}.txt"), "w") as f:
        f.write(f"# {baslik}\n" + "\n".join(satirlar) + "\n")
    with open(os.path.join(hedef, f"{ad}-sozlukte-yok.txt"), "w") as f:
        f.write(f"# {ad}: sözlükte bulunmayanlar (rapor 18.38).\n" + "\n".join(dict.fromkeys(yok)) + "\n")
    print(ad, sum(1 for s in satirlar if not s.startswith("##")), "satır; sözlükte yok:", ", ".join(dict.fromkeys(yok)))


if __name__ == "__main__":
    main(*sys.argv[1:4])
