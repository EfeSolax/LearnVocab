"""
Cambridge Pre A1 Starters ve A1 Movers (Digital, 2024) kelime listelerini PDF'ten hazır liste
dosyalarına çevirir (rapor 4.1, D7). Tek PDF'te iki liste var; her birinin alfabetik listesi okunur
(konu listeleri ve örnek cümleler Cambridge'in içeriği, alınmaz).

    .venv/bin/python araclar/cambridge_a1_listesi.py ~/Desktop/"Kelime Listeler/Cambridge A1.pdf" veri/hazir_listeler

- Satır biçimi "kelime tür[ + tür]": "answer n + v", "a lot of det", "at prep of place".
  Parantezler: "(US color)" Amerikan yazımı olarak alınır, "(UK flat)", "(s + pl)", "(as sports
  equipment)", "(uncountable)" atılır; iki satıra bölünen parantez ve alt satıra düşen tür birleştirilir.
- Movers listesi yalnızca Movers'ta ilk kez çıkan kelimeleri içerir (PDF böyle).
- Alınmayanlar: kişi adları (yalnızca büyük harfle yazılan isimler: Adam, Max, Pat), unvanlar (Mr, Mrs),
  "phrase" türlü kalıplar (good for you, make friends), sayılar (18.16).
- Tür eşlemesi: det -> determiner, pron -> pronoun, poss adj -> determiner, excl -> exclamation;
  "int" (soru kelimesi) ve "dis" (söylem belirteci) için sözlükte var olan ilk tür. İstenen tür
  sözlükte yoksa YEDEK_TURLER denenir (Cambridge modalları "v" yazar: can v -> yardımcı fiil).
- Çoğuldan köke yalnızca PDF iki biçimi birlikte verdiyse bağlanır (foot/feet); "shorts" short'a
  ("kısa film") bağlanmaz.
Sözlükte olmayanlar cambridge-a1-sozlukte-yok.txt'ye yazılır. Bölümler harf harf (## A).
"""
import os
import re
import sqlite3
import sys

import pymupdf

sys.path.insert(0, os.path.dirname(__file__))
from cambridge_listesi import amerikan  # noqa: E402  (aynı İngiliz -> Amerikan yazım kuralı)

LISTELER = {  # kod: (ad, alfabetik listenin PDF sayfaları, 0'dan)
    "pre-a1-starters": ("Pre A1 Starters", range(9, 13)),
    "a1-movers": ("A1 Movers", range(18, 21)),
}
TURLER = {"n": ["noun"], "v": ["verb"], "adj": ["adjective"], "adv": ["adverb"], "prep": ["preposition"],
          "conj": ["conjunction"], "c": ["conjunction"], "det": ["determiner"], "pron": ["pronoun"],
          "excl": ["exclamation"], "poss": [],
          "int": ["pronoun", "determiner", "adverb", "exclamation"],
          "dis": ["exclamation", "adverb", "adjective"]}
ATLANAN_TURLER = {"phrase", "title"}
YEDEK_TURLER = {"verb": ["modal_verb", "phrasal_verb"], "exclamation": ["adjective", "adverb", "phrasal_verb"],
                "pronoun": ["adverb", "determiner"], "determiner": ["pronoun", "adjective"],
                "adjective": ["determiner"]}
# PDF'te türü yanlış yazılmış maddeler.
TUR_DUZELT = {"carefully": ["adverb"]}
_E = r"(?:n|v|adj|adv|prep|conj|c|det|pron|excl|poss|int|dis|phrase|title)"
ETIKET = re.compile(rf"\s((?:{_E}(?:\s*[+&]\s*|\s+))*{_E})\s*$")
GURULTU = re.compile(r"^(\(No words at this level\)|Grammatical key|adj|adv|conj|det|dis|excl|int|n|pl|"
                     r"poss|prep|pron|s|v|adjective|adverb|conjunction|determiner|discourse marker|"
                     r"exclamation|interrogative|noun|plural|possessive|preposition|pronoun|singular|"
                     r"verb|[A-Z]|\d+)$")
BASLIKLAR = ("The following", "Candidates", "Letters &", "Pre A1 Starters Digital", "A1 Movers Digital",
             "vocabulary list")


def temizle(satir):
    """Türden sonraki açıklamalar: 'fruit n (uncountable)', 'in prep of place + time', 'take off i.e. … v'."""
    satir = re.sub(r"\s+of (place|time)( \+ (place|time))?\s*$", "", satir)
    satir = re.sub(r"\s+i\.e\..*?(?=\s\S+$)", "", satir)
    m = re.search(r"\s\([^()]*\)\s*$", satir)
    if m and ETIKET.search(" " + satir[:m.start()]):
        satir = satir[:m.start()]
    return satir.strip()


def satirlar(pdf, sayfalar):
    """Madde satırları; iki satıra bölünmüş parantezler ve alt satıra düşen tür birleştirilir."""
    d = pymupdf.open(pdf)
    biriken, bekleyen = "", ""
    for i in sayfalar:
        for ham in d[i].get_text().splitlines():
            ham = ham.replace("\ufeff", "").replace("\xa0", " ").strip()
            if not ham:
                continue
            biriken = f"{biriken} {ham}" if biriken else ham
            if biriken.count("(") > biriken.count(")"):
                continue
            satir, biriken = biriken, ""
            if bekleyen and re.fullmatch(r"(n|v|adj|adv|prep|det|pron)", satir):
                yield temizle(f"{bekleyen} {satir}")       # "parking lot (UK car park)" + "n"
                bekleyen = ""
                continue
            if bekleyen:
                yield temizle(bekleyen)
                bekleyen = ""
            if "(" in satir and not ETIKET.search(" " + temizle(satir)):
                bekleyen = satir
                continue
            yield temizle(satir)
    if bekleyen:
        yield temizle(bekleyen)


def madde_coz(satir):
    """'apartment (UK flat) n' -> ('apartment (UK flat)', ['noun']); kalıp/unvan -> (bas, None)."""
    m = ETIKET.search(" " + satir)
    if not m:
        return None
    bas = (" " + satir)[:m.start()].strip()
    etiketler = re.split(r"\s*[+&]\s*|\s+", m.group(1))
    if any(e in ATLANAN_TURLER for e in etiketler):
        return bas, None
    if etiketler[:1] == ["poss"]:                     # "your poss adj" -> belirleyici
        return bas, ["determiner"]
    turler = []
    for e in etiketler:
        turler += [t for t in TURLER[e] if t not in turler]
    return bas, TUR_DUZELT.get(bas.lower(), turler)


def yazimlar(bas):
    """'colour (US color)' -> ['color']; 'Mum/mum (US Mom/mom)' -> ['Mom', 'mom']; 'foot/feet' -> ['foot', 'feet']."""
    us = re.search(r"\(US ([^()]*)\)", bas)
    if us:
        bas = us.group(1)
    while re.search(r"\([^()]*\)", bas):              # iç içe: candy (UK sweet(s))
        bas = re.sub(r"\([^()]*\)", "", bas)
    bas = bas.replace("’", "'").strip(" !?")
    return [re.sub(r"\s+", " ", v).strip(" !?") for v in re.split(r"[/,]", bas) if v.strip()]


def main(pdf, hedef):
    db = sqlite3.connect("file:db.sqlite3?mode=ro", uri=True)
    kayitlar = list(db.execute("select text, pos from words_word where isBaseWord or visibility='public'"))
    var = {(t.lower(), p) for t, p in kayitlar}
    yazim_of = {}
    for t, _ in kayitlar:
        yazim_of.setdefault(t.lower(), t)
    metinler = set(yazim_of)
    kokler = {}
    for yuzey, t, p in db.execute("select f.surface, w.text, w.pos from words_wordform f join words_word w on w.id = f.word_id"):
        kokler.setdefault(yuzey.lower(), set()).add((t.lower(), p))
    eksik_bolumleri = {}
    for kod, (ad, sayfalar) in LISTELER.items():
        cikti, eksik, harf, gorulen = [], [], None, set()
        for satir in satirlar(pdf, sayfalar):
            if GURULTU.match(satir) or satir.startswith(BASLIKLAR):
                continue
            cozum = madde_coz(satir)
            if cozum is None:
                eksik.append(f"{satir}\t# okunamadı")
                continue
            bas, turler = cozum
            if turler is None:
                if not re.search(r"\btitle$", satir):
                    eksik.append(f"{bas}\t# kalıp (phrase)")
                continue
            bulunan, varyantlar = [], yazimlar(bas)
            if turler == ["noun"] and all(v[:1].isupper() for v in varyantlar) and \
                    not any(v in yazim_of.values() for v in varyantlar):
                continue                                    # kişi adı: Adam, Max, Pat (max, pat değil)
            for v in varyantlar:
                k = v.lower()
                if k not in metinler:
                    k = amerikan(k, metinler) or k
                if k in metinler:
                    bulunan.append(k)
                elif k in kokler and len(varyantlar) > 1:   # foot/feet, mouse/mice; tek başına "shorts" short'a bağlanmaz
                    bulunan += [kok for kok, p in kokler[k] if p in turler]
            yazilan = False
            for k in dict.fromkeys(bulunan):
                adaylar = turler
                if " int" in f" {satir} " or " dis" in f" {satir} ":
                    adaylar = [t for t in turler if (k, t) in var][:1]   # soru kelimesi: ilk var olan tür
                if not any((k, t) in var for t in adaylar):
                    adaylar = [y for t in turler for y in YEDEK_TURLER.get(t, []) if (k, y) in var][:1]
                for t in adaylar:
                    if t == "verb" and " " in k and (k, "phrasal_verb") in var:
                        t = "phrasal_verb"                  # get up v -> phrasal verb
                    if (k, t) not in var:
                        continue
                    yazilan = True
                    if (k, t) in gorulen:
                        continue
                    gorulen.add((k, t))
                    ilk = yazim_of[k][0].upper()
                    if ilk != harf:
                        harf = ilk
                        cikti.append(f"## {harf}")
                    cikti.append(f"{yazim_of[k]}:{t}")
            if not yazilan:
                eksik.append(f"{bas} ({', '.join(turler)})" + ("; sözlükte başka türde" if bulunan else ""))
        with open(os.path.join(hedef, f"cambridge-{kod}.txt"), "w") as f:
            f.write(f"# Cambridge {ad} Digital Wordlist (2024) · alfabetik liste, ## = harf.\n")
            f.write("# Kişi adları, unvanlar, kalıplar (phrase), sayılar ve konu listeleri alınmadı. "
                    "Betik: araclar/cambridge_a1_listesi.py\n")
            f.write("\n".join(cikti) + "\n")
        eksik_bolumleri[ad] = eksik
        print(kod, sum(1 for s in cikti if not s.startswith("#")), "satır; sözlükte yok:", len(eksik))
    with open(os.path.join(hedef, "cambridge-a1-sozlukte-yok.txt"), "w") as f:
        f.write("# Cambridge Pre A1 Starters / A1 Movers listelerinde olup sözlükte bulunmayanlar (rapor 18.38).\n")
        for ad, eksik in eksik_bolumleri.items():
            f.write(f"\n# {ad}\n" + "\n".join(eksik) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
