"""
High Note ders kitabı kelime listesi (ODTÜ DBE; PDF) → hazır liste dosyası, ünite ünite (rapor 13.3, D7).

    .venv/bin/python -I araclar/odtu_listeleri/pdf_kalin.py HighNote5.pdf <klasör>/hn.json
    python3 araclar/odtu_listeleri/high_note.py <klasör>/hn.json veri/hazir_listeler high-note-5

Her satır "kelime (tür) /fonetik/". Türü yazan tek kelimeler listeye girer (İngiliz yazımı Amerikan
karşılığına bağlanır); deyimler ve kalıplar ("get cold feet", "in a nutshell") <ad>-deyimler.txt'ye,
sözlükte olmayan kelimeler <ad>-sozlukte-yok.txt'ye yazılır (18.38). Fonetik alınmaz.
"""
import json
import os
import re
import sqlite3
import sys

ETIKET = re.compile(r"\((n|v|adj|adv|phr v|prep|conj)\)\s*$", re.I)
POS = {"n": "noun", "v": "verb", "adj": "adjective", "adv": "adverb", "prep": "preposition", "conj": "conjunction"}
EK = re.compile(r"(\s+(about|into|for|with|on|of|to|in|at|by|from|over))?\s+(sb|sth|sb/sth|someone|something|yourself|oneself)\b.*$", re.I)


def amerikan(w):
    """subsidise -> subsidize, centred -> centered, colour -> color (yalnızca sözlükte varsa kullanılır)."""
    adaylar = [w]
    adaylar.append(re.sub(r"is(e|ed|es|ing|ation)$", r"iz\1", w))
    adaylar.append(re.sub(r"tre(d)?$", r"ter\1", w))
    adaylar.append(w.replace("our", "or"))
    adaylar.append(re.sub(r"ll(ed|ing|er)$", r"l\1", w))
    adaylar.append(w.replace("ould", "old"))
    return adaylar


def main(json_yolu, hedef, ad):
    db = sqlite3.connect("file:db.sqlite3?mode=ro", uri=True)
    var = {}
    for t, p in db.execute("select lower(text), pos from words_word"):
        var.setdefault(t, set()).add(p)
    formlar = {s for (s,) in db.execute("select lower(surface) from words_wordform")}

    satirlar, deyimler, yok, unite = [], [], [], None
    for x in json.load(open(json_yolu)):
        t = x["t"].strip()
        m = re.match(r"UNIT\s*(\d+)\s*$", t)
        if m:
            unite = m.group(1)
            satirlar.append(f"## Unit {unite}")
            deyimler.append(f"\n## Unit {unite}")
            continue
        if unite is None or not re.match(r"^[A-Za-z(]", t) or " /" not in t:
            continue                       # başlık, sayfa no, fonetiğin devam satırı
        bas = t.split(" /")[0].strip().replace("’", "'")
        etiket = ETIKET.search(bas)
        if not etiket:
            deyimler.append(bas)
            continue
        tur = etiket.group(1).lower()
        metin = EK.sub("", ETIKET.sub("", bas)).strip()
        metin = re.sub(r"\s*\(.*?\)\s*", " ", metin).strip().lower()
        if tur == "phr v" or " " in metin:
            (deyimler if tur == "phr v" else yok).append(bas)
            continue
        kelime = next((a for a in amerikan(metin) if a in var or a in formlar), None)
        if not kelime:
            yok.append(bas)
            continue
        pos = POS.get(tur)
        satirlar.append(f"{kelime}:{pos}" if pos in var.get(kelime, set()) else kelime)

    baslik = ad.replace("-", " ").title()
    with open(os.path.join(hedef, f"{ad}.txt"), "w") as f:
        f.write(f"# {baslik} (ODTÜ DBE 501, 2025-26) aktif kelime listesi; ## = ünite. Türü yazan tek kelimeler.\n")
        f.write("\n".join(satirlar) + "\n")
    with open(os.path.join(hedef, f"{ad}-deyimler.txt"), "w") as f:
        f.write(f"# {baslik}: deyimler, kalıplar ve phrasal verb'ler (sözlüğe ifade olarak eklenecek; rapor 18.38).\n")
        f.write("\n".join(deyimler).lstrip("\n") + "\n")
    with open(os.path.join(hedef, f"{ad}-sozlukte-yok.txt"), "w") as f:
        f.write(f"# {baslik}: türü yazan ama sözlükte olmayan kelimeler (rapor 18.38).\n")
        f.write("\n".join(yok) + "\n")
    print(f"{ad}: {sum(1 for s in satirlar if not s.startswith('##'))} kelime, "
          f"{sum(1 for d in deyimler if d and not d.startswith(chr(10)))} deyim/kalıp, {len(yok)} sözlükte yok")


if __name__ == "__main__":
    main(*sys.argv[1:4])
