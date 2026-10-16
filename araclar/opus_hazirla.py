"""Opus düzeltme turu için girdi dosyalarını üretir (veritabanını yalnızca okur).

Kullanım (proje kökünden): python3 araclar/opus_hazirla.py
Çıktı: veri/kalite_olcumu/opus/girdi/
  o001…  işaretlenen anlamlar (Haiku+Sonnet bulguları ve Sonnet'in önerisiyle), 50'şer
  y001…  hiç taranmamış anlamlar, 100'er
  t001…  taranmış ama işaretlenmemiş anlamlar, 100'er
"""
import sqlite3
from pathlib import Path

K = Path("veri/kalite_olcumu")
HEDEF = K / "opus/girdi"
HEDEF.mkdir(parents=True, exist_ok=True)


def tek_satir(s):
    return " ".join((s or "").split())


db = sqlite3.connect("file:db.sqlite3?mode=ro", uri=True)
anlamlar = {}
sira = {}
for mid, wid, tr, en, cefr, kelime, tur, wcefr in db.execute(
        "SELECT m.id, m.word_id, m.meaning_tr, m.definition, m.cefr, w.text, w.pos, w.cefr "
        "FROM words_meaning m JOIN words_word w ON w.id = m.word_id "
        "WHERE w.owner_id IS NULL ORDER BY w.text, w.pos, m.sort_order, m.id"):
    sira.setdefault(wid, []).append(mid)
    bos = ("", None, "Belirtilmemiş")
    anlamlar[mid] = (wid, kelime, tur, (cefr if cefr not in bos else wcefr if wcefr not in bos else ""), tr, en)
ornek = {}
for mid, metin in db.execute("SELECT meaning_id, text FROM words_examplesentence ORDER BY meaning_id, sort_order, id"):
    ornek.setdefault(mid, metin)


def satir(mid):
    wid, kelime, tur, cefr, tr, en = anlamlar[mid]
    s = sira[wid]
    return (f"{mid} | {kelime} | {tur} | {cefr} | #{s.index(mid) + 1}/{len(s)} | TR: {tek_satir(tr)} | "
            f"EN: {tek_satir(en)} | ÖRNEK: {tek_satir(ornek.get(mid))}")


# Sonnet doğrulamasının önerileri
oneri = {}
for p in sorted((K / "dogrulama/cikti").glob("d*.tsv")):
    for s in p.read_text(encoding="utf-8").splitlines():
        f = s.split("\t")
        if len(f) > 1:
            parca = f[1] if f[1] != "DUZELT" else f"{f[2]}={f[3]}"
            oneri.setdefault(f[0].strip(), []).append(parca)

isaretli, taranan = [], set()
for p in sorted((K / "dogrulama/girdi").glob("d*.txt")):
    for s in p.read_text(encoding="utf-8").splitlines():
        mid = int(s.split("|")[0])
        if mid in anlamlar:
            bulgu = s.split("|| BULGU:")[1].strip()
            isaretli.append(f"{satir(mid)} || BULGU: {bulgu} || SONNET ÖNERİSİ: {' ;; '.join(oneri.get(str(mid), []))}")
for p in sorted((K / "haiku-tarama/girdi").glob("b*.txt")):
    for s in p.read_text(encoding="utf-8").splitlines():
        taranan.add(int(s.split("|")[0]))
isaretli_id = {int(s.split("|")[0]) for s in isaretli}
hic = [satir(m) for m in anlamlar if m not in taranan]
temiz = [satir(m) for m in anlamlar if m in taranan and m not in isaretli_id]


def yaz(onek, satirlar, boy):
    for i in range(0, len(satirlar), boy):
        (HEDEF / f"{onek}{i // boy + 1:03d}.txt").write_text("\n".join(satirlar[i:i + boy]) + "\n", encoding="utf-8")


yaz("o", isaretli, 50)
yaz("y", hic, 100)
yaz("t", temiz, 100)
print(f"işaretli {len(isaretli)} · hiç taranmamış {len(hic)} · temiz {len(temiz)}")
