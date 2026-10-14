"""
Cambridge A2 Key ve B1 Preliminary kelime listelerini PDF'ten hazır liste dosyalarına çevirir (rapor 4.1, D7).

    .venv/bin/python araclar/cambridge_listesi.py ~/Desktop/"Kelime Listeler/Cambridge A2.pdf" a2-key veri/hazir_listeler
    .venv/bin/python araclar/cambridge_listesi.py ~/Desktop/"Kelime Listeler/Cambridge B1.pdf" b1-preliminary veri/hazir_listeler

1) Alfabetik ana liste okunur ("Appendix 1" sayfasında durur). Madde satırı
   "kelime (tür)" biçimindedir; "•" ile başlayan örnekler ve devam satırları
   ALINMAZ (Cambridge'in yazdığı içerik; yalnızca kelimeler alınır).
2) Türler sözlüğün türlerine çevrilir; "act (n & v)" iki satır olur (act:noun, act:verb).
   Sözlükte o türü olmayan tür atlanır. det / pron / mv / exclam 11 Ekim'den beri
   belirleyici / zamir / yardımcı fiil / ünlem olarak eşlenir (rapor 18.36; "can (mv)"
   teneke kutuya değil yardımcı fiile bağlanır).
3) "a/b" ikiye ayrılır; İngiliz yazımı Amerikan karşılığına bağlanır (sözlük
   Amerikan yazımını tutar). Sözlükte olmayanlar cambridge-sozlukte-yok.txt'ye yazılır.
Bölümler harf harf (## A). Sonra her dosya `hazir_liste_yukle` ile yüklenir (önce --dry-run).
"""
import os
import re
import sqlite3
import sys

import pymupdf

TURLER = {"n": "noun", "n pl": "noun", "v": "verb", "adj": "adjective", "adv": "adverb",
          "prep": "preposition", "conj": "conjunction", "phr v": "phrasal_verb",
          # Dilbilgisi türleri (rapor 18.36, 11 Ekim'den beri sözlükte).
          "det": "determiner", "pron": "pronoun", "mv": "modal_verb", "exclam": "exclamation"}
# Sözlükte karşılığı olmayan ama Cambridge'in kullandığı türler (madde satırını tanımak için).
DIGER_TURLER = {"av", "prep phr", "number", "abbrev", "phr",
                "adj phr", "adv phr", "n phr", "conj phr", "det phr", "pron phr", "exclam phr"}
ADLAR = {"a2-key": "A2 Key", "b1-preliminary": "B1 Preliminary"}
# Kurala uymayan İngiliz yazımları ve kalıplar.
DUZELT = {"grey": "gray", "jewellery": "jewelry", "cheque": "check", "programme": "program",
          "practise": "practice", "moustache": "mustache", "pyjamas": "pajamas", "cosy": "cozy",
          "omelette": "omelet", "kilogramme": "kilogram", "tyre": "tire", "aeroplane": "airplane",
          "make-up": "makeup", "mum": "mom", "maths": "math", "storey": "story", "plough": "plow",
          "sceptical": "skeptical", "speciality": "specialty", "draught": "draft", "catalogue": "catalog",
          "dialogue": "dialog", "suprising": "surprising"}
# PDF'te türü yanlış yazılmış maddeler.
TUR_DUZELT = {"unfortunately": ["adverb"], "unhappy": ["adjective"], "solve": ["verb"], "unusual": ["adjective"]}


def tur_coz(metin):
    """'n & v' / 'adj, adv & prep' -> (['noun', 'verb'], tanındı mı)."""
    parcalar = [p.strip() for p in re.split(r",|&", metin.lower()) if p.strip()]
    if not parcalar or not all(p in TURLER or p in DIGER_TURLER for p in parcalar):
        return [], False
    return [TURLER[p] for p in parcalar if p in TURLER], True


def maddeler(yol):
    """PDF sırasıyla (baş kelime, [türler], yalnızca çoğul mu) üçlüleri."""
    cikti, ornekte, hemen = [], False, False
    for sayfa in pymupdf.open(yol):
        metin = sayfa.get_text()
        if re.search(r"^\s*Appendix 1\s*$", metin, re.M):
            break
        if not re.search(r"^Page \d+ of", metin, re.M) or sayfa.number < 3:
            continue
        for satir in metin.splitlines():
            satir = satir.strip()
            if satir == "•":
                ornekte = hemen = True
                continue
            if not satir or satir.startswith(("©", "Page ")) or re.fullmatch(r"[A-Z]", satir):
                continue
            if hemen:  # "•"den hemen sonraki satır her zaman örnektir: "a book about animals (prep)"
                hemen = False
                continue
            m = None
            for grup in re.finditer(r"\(([^()]*)\)", satir):
                turler, tanindi = tur_coz(grup.group(1))
                if tanindi:
                    m = (satir[:grup.start()], turler, "n pl" in grup.group(1).lower())
                    break
            bas = m and re.sub(r"\([^()]*\)", "", m[0]).strip()
            # Örnek cümlenin kendisi (ya da devamı) "(adv)" ile bitebilir: "I have about £3. (adv)".
            if not m or not bas or (ornekte and (bas[0].isupper() or bas.endswith(".")) and len(bas) > 5) \
                    or bas.startswith("•") or (bas.endswith(".") and len(bas) > 5):
                continue
            ornekte = False
            cikti.append((bas, m[1], m[2]))
    return cikti


def amerikan(v, metinler):
    """İngiliz yazımını sözlükteki Amerikan karşılığına çevirir; yoksa None."""
    if v in DUZELT:
        return DUZELT[v]
    for eski, yeni in (("our", "or"), ("tre", "ter"), ("ise", "ize"), ("isation", "ization"),
                       ("ising", "izing"), ("ised", "ized"), ("ence", "ense"), ("lled", "led"),
                       ("lling", "ling"), ("ller", "ler"), ("llous", "lous"), ("ogue", "og")):
        if eski in v:
            aday = v.replace(eski, yeni)
            if aday in metinler:
                return aday
    return None


def main(pdf, kod, hedef):
    db = sqlite3.connect("file:db.sqlite3?mode=ro", uri=True)
    var = {(t.lower(), p) for t, p in db.execute("select text, pos from words_word where isBaseWord or visibility='public'")}
    metinler = {t for t, _ in var}
    # Çekimli biçim -> kök (glasses -> glass); yalnızca kökün türü Cambridge'in türüyle aynıysa kullanılır.
    kokler = {}
    for yuzey, t, p in db.execute("select f.surface, w.text, w.pos from words_wordform f join words_word w on w.id = f.word_id"):
        kokler.setdefault(yuzey.lower(), set()).add((t.lower(), p))
    satirlar, eksik, harf = [], [], None
    for bas, turler, cogul in maddeler(pdf):
        bas = bas.replace("’", "'").strip(" !?")
        turler = TUR_DUZELT.get(bas.lower(), turler)
        varyantlar = [p.strip() for p in bas.split("/") if p.strip()]
        varyantlar = [re.sub(r"\((\w+)\)", r"\1", v) if v.endswith(")") else re.sub(r"\(\w+\)", "", v)
                      for v in varyantlar]  # program(me) -> programme -> program
        bulunan = []
        for v in varyantlar:
            v = re.sub(r"\s+", " ", v).strip()
            k = v.lower()
            if k not in metinler:
                k = amerikan(k, metinler) or k
            if k in metinler:
                bulunan.append((v if v.lower() == k else k, k))
            elif k in kokler and not cogul:  # "shorts (n pl)" short'un "kısa film" anlamına bağlanmasın
                bulunan += [(kok, kok) for kok, p in kokler[k] if p in turler]
        if not bulunan or not turler:
            eksik.append(bas + (f" ({', '.join(turler)})" if turler else ""))
            continue
        yazilan = False
        for yazim, k in dict.fromkeys(bulunan):
            for t in turler:
                if t == "verb" and " " in k and (k, "phrasal_verb") in var:
                    t = "phrasal_verb"  # Cambridge çok kelimeli fiillere bazen "v" yazıyor: come back (v)
                if (k, t) in var:
                    ilk = yazim[0].upper()
                    if ilk != harf and ilk.isalpha():
                        harf = ilk
                        satirlar.append(f"## {harf}")
                    satirlar.append(f"{yazim}:{t}")
                    yazilan = True
        if not yazilan:
            eksik.append(f"{bas} ({', '.join(turler)}; sözlükte başka türde)")

    os.makedirs(hedef, exist_ok=True)
    with open(os.path.join(hedef, f"cambridge-{kod}.txt"), "w") as f:
        f.write(f"# Cambridge {ADLAR[kod]} Vocabulary List (August 2025) · alfabetik ana liste, ## = harf.\n")
        f.write("# Örnekler ve ekler (sayılar, günler, ülkeler; konu listeleri) alınmadı. Betik: araclar/cambridge_listesi.py\n")
        f.write("\n".join(satirlar) + "\n")
    yok = os.path.join(hedef, "cambridge-sozlukte-yok.txt")
    onceki = open(yok).read().split("\n# ") if os.path.exists(yok) else []
    bolumler = {b.split("\n", 1)[0].lstrip("# ").strip(): b for b in onceki[1:]}
    bolumler[ADLAR[kod]] = f"{ADLAR[kod]}\n" + "\n".join(eksik) + "\n"
    with open(yok, "w") as f:
        f.write("# Cambridge A2 Key / B1 Preliminary listelerinde olup sözlükte bulunmayanlar (rapor 18.36, 18.38).\n")
        for ad in ADLAR.values():
            if ad in bolumler:
                f.write("\n# " + bolumler[ad].rstrip("\n") + "\n")
    print(kod, sum(1 for s in satirlar if not s.startswith("#")), "satır; sözlükte yok:", len(eksik))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
