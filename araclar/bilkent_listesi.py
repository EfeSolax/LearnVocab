"""
Bilkent ELPP seviye kelime listelerini PDF'ten hazır liste dosyalarına çevirir (rapor 4.1, D7).

    .venv/bin/python araclar/bilkent_listesi.py ~/Downloads/2025-26-ELPP-LEVEL-WORDLISTS.pdf veri/hazir_listeler

1) PDF tablosu koordinatla okunur: seviye (ELM/PIN/INT/UPP/PFC), başlık kelimesi
   ve fiil / isim / sıfat / zarf sütunları. Eş dizim sütunu ALINMAZ (Bilkent'in
   kendi yazdığı içerik; yalnızca kelimeler alınır).
2) Başlık kelimesi tek bir sütunda yazıyorsa o tür verilir (sözlükte o tür varsa);
   yoksa tür boş kalır, hazir_liste_yukle en yaygın türü seçer.
3) "a/b" ikiye ayrılır; İngiliz yazımı ve kalıplar DUZELT ile sözlükteki karşılığa
   bağlanır. Sözlükte olmayanlar bilkent-sozlukte-yok.txt'ye yazılır.
Sonra her dosya `hazir_liste_yukle` ile yüklenir (önce --dry-run).
Sütun sınırları 2025-26 PDF'ine göre; yeni yılın PDF'inde kontrol edilmeli.
"""
import os
import re
import sqlite3
import sys
import pymupdf

SEVIYELER = ("ELM", "PIN", "INT", "UPP", "PFC")
ADLAR = {"ELM": "elementary", "PIN": "pre-intermediate", "INT": "intermediate",
         "UPP": "upper-intermediate", "PFC": "pre-faculty"}
# Sözlükteki karşılığı (İngiliz yazımı -> Amerikan, kalıp -> kelime). [] = sözlükte yok.
DUZELT = {
    "favourite": ["favorite"], "grey": ["gray:adjective"], "jewellery": ["jewelry"], "metre": ["meter:noun"],
    "neighbour": ["neighbor"], "apologise": ["apologize"], "catalogue": ["catalog:noun"], "cheque": ["check:noun"],
    "programme": ["program:noun"], "theatre": ["theater"], "traveller": ["traveler"], "civilisation": ["civilization"],
    "coloured": ["colored"], "favour": ["favor:noun"], "flavour": ["flavor"], "harbour": ["harbor:noun"],
    "organisation": ["organization"], "realise": ["realize"], "recognise": ["recognize"], "honour": ["honor:noun"],
    "humour": ["humor:noun"], "sceptical": ["skeptical"], "speciality": ["specialty"], "plough": ["plow:noun"],
    "drivers license": ["license:noun"], "envelop": ["envelope"], "make-up": ["makeup"], "outwards": ["outward"],
    "hopeless, hopeful": ["hopeless", "hopeful"], "fulfill function": ["fulfill"], "dose-dosage": ["dose:noun", "dosage"],
    "buyer and seller": ["buyer", "seller"], "male-female": ["male", "female"], "chemist's": ["chemist"],
    "book store": ["bookstore"], "software programmer": ["programmer"], "background info": ["background"],
    "be born": ["born"], "belong to": ["belong"], "appeal to": ["appeal:verb"],
}


def sutun(x):
    """2025-26 PDF'inde sütunların x aralıkları (pt)."""
    if 110 <= x < 140:
        return "verb"
    if 140 <= x < 218:
        return "noun"
    if 218 <= x < 260:
        return "adjective"
    if 260 <= x < 300:
        return "adverb"
    return None


def pdf_satirlari(yol):
    """Her tablo satırı: {"seviye", "bas", "turler": {tür: [biçimler]}}."""
    satirlar = []
    for sayfa in pymupdf.open(yol):
        ws = sayfa.get_text("words")
        kodlar = sorted([w for w in ws if w[0] < 62 and w[4] in SEVIYELER], key=lambda w: w[1])
        ortalar = [(k[1] + k[3]) / 2 for k in kodlar]
        for i, k in enumerate(kodlar):
            ust = (ortalar[i] + ortalar[i - 1]) / 2 if i else 0
            alt = (ortalar[i] + ortalar[i + 1]) / 2 if i + 1 < len(kodlar) else 1e9
            icinde = [w for w in ws if ust <= (w[1] + w[3]) / 2 < alt]
            bas = " ".join(w[4] for w in sorted(icinde, key=lambda w: (round(w[1]), w[0]))
                           if 62 <= w[0] < 110 and w[4] not in ("HEADWORD", "LEVEL"))
            turler = {}
            for w in icinde:
                if sutun(w[0]):
                    turler.setdefault(sutun(w[0]), []).append(w[4].lower().strip(",;"))
            satirlar.append({"seviye": k[4], "bas": bas, "turler": turler})
    return satirlar


def main(pdf, hedef):
    db = sqlite3.connect("file:db.sqlite3?mode=ro", uri=True)
    var = {(t.lower(), p) for t, p in db.execute("select text, pos from words_word")}
    metinler = {t for t, _ in var} | {f.lower() for (f,) in db.execute("select surface from words_wordform")}
    eksik = {k: [] for k in ADLAR}
    cikti = {k: [] for k in ADLAR}
    for x in pdf_satirlari(pdf):
        bas = re.sub(r"\(.*?\)", " ", x["bas"].strip()).replace("*", " ")
        bas = re.split(r"\s[–-]\s", bas)[0]
        for v in [p.strip(" ,.;").lower() for p in bas.split("/")]:
            v = re.sub(r"\s+", " ", v).replace("’", "'")
            if not v:
                continue
            if v in DUZELT:
                cikti[x["seviye"]].extend(DUZELT[v])
                continue
            if v not in metinler:
                eksik[x["seviye"]].append(v)
                continue
            turler = [t for t, kel in x["turler"].items()
                      if any(v == k.strip(" /") for k in kel) and (v, t) in var]
            cikti[x["seviye"]].append(f"{v}:{turler[0]}" if len(turler) == 1 else v)

    os.makedirs(hedef, exist_ok=True)
    for k, satirlar in cikti.items():
        with open(os.path.join(hedef, f"bilkent-{ADLAR[k]}.txt"), "w") as f:
            f.write(f"# Bilkent ELPP 2025-26 · {ADLAR[k]} ({k}) · başlık kelimeleri, PDF sırasıyla\n")
            f.write("\n".join(satirlar) + "\n")
        print(k, len(satirlar), "satır; sözlükte yok:", len(eksik[k]))
    with open(os.path.join(hedef, "bilkent-sozlukte-yok.txt"), "w") as f:
        f.write("# Bilkent ELPP 2025-26 listelerinde olup sözlükte bulunmayanlar (rapor 4.1, D7).\n")
        f.write("# Sözlüğe eklenince ilgili listeye de eklenir.\n")
        for k, v in eksik.items():
            f.write(f"\n# {ADLAR[k]} ({k})\n" + "\n".join(v) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
