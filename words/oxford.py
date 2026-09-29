"""
Oxford 3000/5000 "by CEFR level" listelerini okur (rapor 18.16/8).

PDF'ler projeye konmaz (pdfler/ git'e girmiyor); veritabanına yalnızca
seviye ve kaynağı ("oxford") yazılır. Komut: manage.py oxford_cefr_yukle
"""

import re

SEVIYELER = {"A1", "A2", "B1", "B2", "C1", "C2"}
SEVIYE_SIRASI = {s: i for i, s in enumerate(["A1", "A2", "B1", "B2", "C1", "C2"], 1)}

# Oxford kısaltması -> Word.pos. Bizde karşılığı olmayanlar (det., pron.,
# exclam., modal v., number…) atlanır.
TURLER = {"n.": "noun", "v.": "verb", "adj.": "adjective", "adv.": "adverb",
          "prep.": "preposition", "conj.": "conjunction"}
_TUR_KALIBI = re.compile(
    r"(auxiliary v\.|modal v\.|indefinite article|definite article|infinitive marker|"
    r"ordinal number|number|exclam\.|det\.|pron\.|conj\.|prep\.|adj\.|adv\.|n\.|v\.)")
_SATIR = re.compile(r"^(?P<kelime>[A-Za-z][A-Za-z' .\-]*?)(?:\s*\([^)]*\))?\s+(?P<turler>(?:"
                    + _TUR_KALIBI.pattern + r")(?:\s*[,/]\s*" + _TUR_KALIBI.pattern + r")*)\s*$")


def satirlari_coz(metin):
    """
    PDF metni -> {(kelime, pos): seviye}. Aynı (kelime, tür) birden çok
    seviyede geçerse (bank (money) A1, bank (river) B1) en düşüğü alınır.
    """
    sonuc, seviye = {}, None
    for ham in metin.splitlines():
        satir = ham.strip()
        if satir in SEVIYELER:
            seviye = satir
            continue
        if not seviye:
            continue
        m = _SATIR.match(satir)
        if not m:
            continue
        kelime = m.group("kelime").strip()
        # "a, an" gibi virgüllü başlıklar ve sayılar atlanır
        if "," in kelime or any(ch.isdigit() for ch in kelime):
            continue
        for kisaltma in _TUR_KALIBI.findall(m.group("turler")):
            pos = TURLER.get(kisaltma)
            if not pos:
                continue
            anahtar = (kelime.lower(), pos)
            if anahtar not in sonuc or SEVIYE_SIRASI[seviye] < SEVIYE_SIRASI[sonuc[anahtar]]:
                sonuc[anahtar] = seviye
    return sonuc


def pdf_metni(yol):
    import pymupdf
    with pymupdf.open(yol) as belge:
        return "\n".join(sayfa.get_text() for sayfa in belge)
