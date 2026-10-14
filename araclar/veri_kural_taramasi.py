"""Sözlük verisi için ücretsiz kural taraması (salt okunur; LLM yok).

Kullanım:
    python3 araclar/veri_kural_taramasi.py            # db.sqlite3'ü okur
    python3 araclar/veri_kural_taramasi.py --db yol    # başka veritabanı

Çıktı: veri/kalite_olcumu/kural-taramasi/<kural>.tsv + ozet.md
Her satır: anlam_kimligi, kelime, tür, cefr, kaynak, TR, neden.
Kurallar şüpheli kayıt bulur, düzeltme yapmaz; çıkanları Claude/Efe gözden geçirir.
Altın etiket (14 Ekim kör ölçüm) kontrolü: --altin ile hangi kuralın hangi
bilinen hatayı yakaladığı ozet.md'ye yazılır.
"""
import argparse
import collections
import os
import re
import sqlite3

CIKTI = "veri/kalite_olcumu/kural-taramasi"

# 14 Ekim kör ölçümünde bulunan anlam kimlikleri (veri/kalite_olcumu/2026-10-14-sonuc.md)
ALTIN = {
    23938: "bathe H", 7386: "moderate H", 7544: "deterministic H", 24894: "uptown H",
    7597: "sickened H", 12432: "dummy H(sıra)",
    21684: "fluff Z", 7144: "doom Z", 13201: "gagged Z(içerik)", 18548: "sum Z",
    19992: "team Z", 19779: "compressibility Z", 16987: "branded Z",
    13538: "excavator Z", 6195: "pat Z", 7569: "dip S(seviye)",
}

SIRA = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
# Yalnızca zarf parçacıkları: aim to / belong to / beg for geçerli fiil+edat kalıplarıdır.
PARCACIK = {"up", "out", "off", "down", "away", "over", "back", "around", "apart", "along", "together", "forward"}
HASSAS_TR = re.compile(
    r"cinsel (oyuncak|organ|ilişki|birleşme|haz|uyarı|iste[kğ]|arzu|çekici)|seks|erotik|porno|"
    r"mastürbasyon|prezervatif|kondom|genital|müstehcen|edepsiz söz|küfür|striptiz|azgın|şehvet", re.I)
HASSAS_EN = re.compile(
    r"sex toy|sexual (intercourse|act|pleasure|organ|stimulation|desire|arousal)|\bsex\b|"
    r"erotic|pornograph|masturbat|genital|obscene|vulgar|sexually aroused|\bstrip ?tease", re.I)
SIDDET = re.compile(
    r"\b(kidnap\w*|murder\w*|rape[ds]?|raping|molest\w*|suicid\w*|tortur\w*|terroris\w*|massacre\w*|"
    r"slaughter\w*|stabb\w*|strangl\w*|hostage\w*|assault\w*)\b", re.I)
SABLON_ORNEK = re.compile(
    r"\b(textbook explains|teacher explained|in simple terms|for beginners|the teacher said|"
    r"the manager said|the professor explained|the book describes)\b", re.I)
# Bilinen kötü Türkçe karşılıklar (altın etiketten tohumlanmış; yeni bulundukça eklenir).
SUPHELI_TR = {
    "ortacı": "yerleşik değil, 'ılımlı'", "duş almak": "bathe/banyo ile karışır",
    "lanetlemek": "doom/curse karışıklığı olabilir", "kazıcı": "ekskavatör/iş makinesi",
    "hafif tokat": "pat = okşama", "havalı": "argo/yanıltıcı", "bitap": "arkaik",
}
OZEL_YAZIM = re.compile(r"[qwx]", re.I)


def ana_fiil_parcalari(tr):
    """'(biri) soğumak, sevmez olmak' → ['soğumak', 'sevmez olmak']."""
    t = re.sub(r"\([^)]*\)", "", tr)
    return [p.strip() for p in t.split(",") if p.strip()]


def yaz(ad, satirlar, baslik="anlam_id\tkelime\ttür\tcefr\tkaynak\tTR\tneden"):
    os.makedirs(CIKTI, exist_ok=True)
    with open(f"{CIKTI}/{ad}.tsv", "w", encoding="utf-8") as f:
        f.write(baslik + "\n")
        for s in satirlar:
            f.write("\t".join(str(x) for x in s) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="db.sqlite3")
    ap.add_argument("--altin", action="store_true", help="altın etiket yakalama tablosunu özete yaz")
    a = ap.parse_args()
    c = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)

    kelimeler = {}
    for r in c.execute("select id,text,pos,cefr,cefr_kaynak,siklik,nadir_tur,family_id from words_word where owner_id is null"):
        kelimeler[r[0]] = dict(text=r[1], pos=r[2], cefr=r[3], kaynak=r[4], zipf=r[5], nadir=r[6], aile=r[7])
    formlar = collections.defaultdict(set)
    for wid, s in c.execute("select word_id, lower(surface) from words_wordform"):
        formlar[wid].add(s)
    phrasal = {w["text"].lower() for w in kelimeler.values() if w["pos"] == "phrasal_verb"}
    anlamlar = {}
    kelime_anlamlari = collections.defaultdict(list)
    for r in c.execute("select id,word_id,meaning_tr,definition,sort_order,cefr from words_meaning order by word_id, sort_order"):
        if r[1] in kelimeler:
            anlamlar[r[0]] = dict(wid=r[1], tr=r[2] or "", tanim=r[3] or "", sira=r[4], cefr=r[5])
            kelime_anlamlari[r[1]].append(r[0])
    ornekler = collections.defaultdict(list)
    for mid, t in c.execute("select meaning_id, text from words_examplesentence order by meaning_id, sort_order"):
        ornekler[mid].append(t)

    def satir(mid, neden):
        m = anlamlar[mid]; w = kelimeler[m["wid"]]
        return (mid, w["text"], w["pos"], w["cefr"], w["kaynak"], m["tr"], neden)

    bulgu = collections.defaultdict(list)  # kural -> satırlar

    # R1 seviye: bizim etiketimiz, sıklıkla çelişen (kelime düzeyinde)
    sev = []
    for wid, w in kelimeler.items():
        if w["kaynak"] != "learnvocab" or w["zipf"] is None or w["nadir"]:
            continue
        sr = SIRA.get(w["cefr"], 0)
        neden = None
        if sr in (2, 3, 4) and w["zipf"] < 3.0:
            neden = f"{w['cefr']} ama Zipf {w['zipf']:.2f} (<3,0): seyrek"
        elif sr in (1, 2) and w["zipf"] < 3.5:
            neden = f"{w['cefr']} ama Zipf {w['zipf']:.2f} (<3,5)"
        elif sr >= 5 and w["zipf"] > 4.4:
            neden = f"{w['cefr']} ama Zipf {w['zipf']:.2f} (>4,4): çok sık"
        if neden:
            ids = kelime_anlamlari.get(wid)
            if ids:
                bulgu["r01_seviye"].append(satir(ids[0], neden))

    # R2 yalnızca parçacıklı fiil
    for mid, m in anlamlar.items():
        w = kelimeler[m["wid"]]
        if w["pos"] != "verb" or not ornekler.get(mid):
            continue
        if re.match(r"\([a-z/]+ ile\)", m["tr"]):
            continue  # 14 Ekim: parçacık etiketi yazılmış, bilinçli (d_2026_10_14b)
        formlar_w = formlar.get(m["wid"], set()) | {w["text"].lower()}
        bulundu, parcacikli, hangi = 0, 0, collections.Counter()
        for ex in ornekler[mid]:
            tok = re.findall(r"[a-z']+", ex.lower())
            for i, t in enumerate(tok):
                if t in formlar_w:
                    bulundu += 1
                    if i + 1 < len(tok) and tok[i + 1] in PARCACIK:
                        parcacikli += 1; hangi[tok[i + 1]] += 1
                    break
        if bulundu and parcacikli == bulundu:
            p = hangi.most_common(1)[0][0]
            guclu = f"{w['text'].lower()} {p}" in phrasal
            bulgu["r02_yalniz_parcacikli_fiil"].append(satir(
                mid, f"tüm örnekler '{w['text']} {p}'" + (" (phrasal verb kaydı var: tekrar)" if guclu else "")))

    # R3 tür uyumsuzluğu: Türkçe karşılığın türü
    for mid, m in anlamlar.items():
        w = kelimeler[m["wid"]]
        parcalar = ana_fiil_parcalari(m["tr"])
        if not parcalar:
            continue
        fiil_biter = [bool(re.search(r"(mak|mek)$", p)) for p in parcalar]
        # İsim kolu kaldırıldı: ekmek, parmak, basamak, yemek gibi geçerli isimler yanlış alarm veriyordu.
        if w["pos"] == "verb" and not any(fiil_biter) and not re.search(r"-(ma|me)", m["tr"]):
            bulgu["r03_tur_uyumsuzlugu"].append(satir(mid, "fiil ama hiçbir karşılık -mak/-mek ile bitmiyor"))

    # R4 karşılık biçimi
    for mid, m in anlamlar.items():
        w = kelimeler[m["wid"]]; tr = m["tr"]
        nedenler = []
        parcalar = ana_fiil_parcalari(tr)
        if OZEL_YAZIM.search(tr): nedenler.append("q/w/x harfi (yabancı sözcük?)")
        if len(tr) > 70: nedenler.append("karşılık çok uzun")
        if len(parcalar) > 5: nedenler.append(">5 karşılık")
        if len({p.lower() for p in parcalar}) < len(parcalar): nedenler.append("yinelenen karşılık")
        if re.search(r"\s{2,}|\(\s*\)|[.;]$", tr): nedenler.append("biçim bozuk (boşluk/parantez/nokta)")
        if tr and tr[0].isupper() and w["text"][0].islower() and w["pos"] != "phrasal_verb": nedenler.append("büyük harfle başlıyor")
        if nedenler:
            bulgu["r04_karsilik_bicimi"].append(satir(mid, "; ".join(nedenler)))

    # R5 tanım türü
    for mid, m in anlamlar.items():
        w = kelimeler[m["wid"]]; d = m["tanim"].strip().lower()
        if not d: continue
        nedenler = []
        if w["pos"] in ("noun", "adjective", "adverb") and d.startswith("to ") and not re.match(
                r"to (a|an|the|such|this|that|some|every|any|what|no|one|another|its|their|his|her|my|our|your|all|both|each|be)\b", d):
            nedenler.append("tanım 'to …' ama tür fiil değil")
        if w["pos"] in ("verb", "phrasal_verb") and not d.startswith(("to ", "(")): nedenler.append("fiil ama tanım 'to …' ile başlamıyor")
        if w["pos"] != "adjective" and d.startswith("relating to"): nedenler.append("'relating to' tanımı sıfat gibi")
        if w["pos"] != "adverb" and re.match(r"(in a|in an) .*(manner|way)\b", d): nedenler.append("zarf tanımı başka türde")
        if nedenler:
            bulgu["r05_tanim_turu"].append(satir(mid, "; ".join(nedenler)))

    # R6 örnek kalitesi
    sablon = collections.Counter()
    for mid, exs in ornekler.items():
        if mid not in anlamlar: continue
        for ex in exs[:1]:
            sablon[" ".join(ex.lower().split()[:3])] += 1
    kalabalik = {k for k, n in sablon.items() if n >= 40}
    for mid, exs in ornekler.items():
        if mid not in anlamlar or not exs: continue
        ex = exs[0]; nedenler = []
        if len(ex.split()) < 3: nedenler.append("örnek <3 kelime")
        if SABLON_ORNEK.search(ex): nedenler.append("kalıp örnek (textbook explains…)")
        if nedenler:
            bulgu["r06_ornek_kalitesi"].append(satir(mid, "; ".join(nedenler) + " :: " + ex[:80]))

    # R7 hassas / şiddet
    for mid, m in anlamlar.items():
        exs = " ".join(ornekler.get(mid, []))
        nedenler = []
        if HASSAS_TR.search(m["tr"]) or HASSAS_EN.search(m["tanim"]) or HASSAS_EN.search(exs): nedenler.append("hassas (müstehcen) kalıp")
        mm = SIDDET.search(exs)
        hw = kelimeler[m["wid"]]["text"].lower()
        if mm and mm.group(0).lower()[:5] != hw[:5]: nedenler.append(f"şiddet sözcüğü: {mm.group(0)}")
        if nedenler:
            bulgu["r07_hassas_siddet"].append(satir(mid, "; ".join(nedenler)))

    # R8 bilinen şüpheli Türkçe
    for mid, m in anlamlar.items():
        low = m["tr"].lower()
        for k, why in SUPHELI_TR.items():
            if k in low:
                bulgu["r08_supheli_turkce"].append(satir(mid, f"'{k}': {why}"))

    # R9 yinelenen anlam (aynı kelime, çakışan karşılıklar)
    for wid, ids in kelime_anlamlari.items():
        if len(ids) < 2: continue
        kumeler = {i: {p.lower() for p in ana_fiil_parcalari(anlamlar[i]["tr"])} for i in ids}
        for x in range(len(ids)):
            for y in range(x + 1, len(ids)):
                a_, b_ = kumeler[ids[x]], kumeler[ids[y]]
                if a_ and b_ and (a_ == b_ or len(a_ & b_) >= 2):
                    bulgu["r09_yinelenen_anlam"].append(satir(ids[y], f"#{anlamlar[ids[x]]['sira']+1} ile karşılıklar çakışıyor: {sorted(a_ & b_)}"))

    # R10 anlam sırası: 1. anlamın CEFR'i diğerlerinden 2+ seviye yüksek
    for wid, ids in kelime_anlamlari.items():
        if len(ids) < 2: continue
        sr = [SIRA.get(anlamlar[i]["cefr"], 0) for i in ids]
        rest = [x for x in sr[1:] if x]
        if sr[0] and rest and min(rest) + 1 < sr[0]:
            bulgu["r10_anlam_sirasi"].append(satir(ids[0], f"1. anlam {anlamlar[ids[0]]['cefr']}, sonrakiler daha kolay"))

    for kural, satirlar in sorted(bulgu.items()):
        yaz(kural, satirlar)

    ozet = ["# Kural taraması özeti", "", f"Veritabanı: `{a.db}`; {len(anlamlar)} anlam, {len(kelimeler)} kelime tarandı.", "",
            "| Kural | Bulgu | Not |", "|---|---|---|"]
    notlar = {
        "r01_seviye": "kelime düzeyinde; `learnvocab` etiketli, Zipf ile çelişen seviye",
        "r02_yalniz_parcacikli_fiil": "fiil anlamının tüm örnekleri 'X up/for…'",
        "r03_tur_uyumsuzlugu": "karşılığın -mak/-mek biçimi ile kelime türü uyuşmuyor",
        "r04_karsilik_bicimi": "q/w/x, yinelenen, çok uzun, boş parantez…",
        "r05_tanim_turu": "tanımın biçimi kelimenin türüne uymuyor",
        "r06_ornek_kalitesi": "çok kısa, şablon, 'textbook explains' örüntüsü",
        "r07_hassas_siddet": "mevcut hassas filtre + şiddet sözcükleri (örneklerde)",
        "r08_supheli_turkce": "altın etiketten tohumlanmış kötü karşılıklar listesi",
        "r09_yinelenen_anlam": "aynı kelimenin anlamları çakışıyor",
        "r10_anlam_sirasi": "1. anlam sonrakilerden 2+ CEFR yüksek (sıra şüphesi)",
    }
    for k in sorted(notlar):
        ozet.append(f"| `{k}` | {len(bulgu.get(k, []))} | {notlar[k]} |")
    tum = {s[0] for ss in bulgu.values() for s in ss}
    ozet += ["", f"Birleşik: **{len(tum)}** farklı anlam en az bir kural tarafından işaretlendi ({100*len(tum)/len(anlamlar):.1f}%).", ""]
    if a.altin:
        ozet += ["## Altın etiket (14 Ekim, 16 bulgu) hangi kuralla yakalandı", "", "| Kimlik | Kayıt | Yakalayan kurallar |", "|---|---|---|"]
        yakalanan = 0
        for mid, ad in ALTIN.items():
            wid = anlamlar.get(mid, {}).get("wid")
            ilk = kelime_anlamlari.get(wid, [None])[0]
            hangi = set()
            for k, ss in bulgu.items():
                for x in ss:
                    if x[0] == mid or (k == "r01_seviye" and x[0] == ilk):
                        hangi.add(k[:3])
            bagimsiz = hangi - {"r08", "r01"}
            yakalanan += bool(bagimsiz)
            ozet.append(f"| {mid} | {ad} | {', '.join(sorted(hangi)) or '—'} |")
        ozet += ["", f"Bağımsız yakalanan (r08 altından tohumlandığı, r01 çok geniş olduğu için ikisi sayılmaz): **{yakalanan}/{len(ALTIN)}**"]
    with open(f"{CIKTI}/ozet.md", "w", encoding="utf-8") as f:
        f.write("\n".join(ozet) + "\n")
    print("\n".join(ozet))


if __name__ == "__main__":
    main()
