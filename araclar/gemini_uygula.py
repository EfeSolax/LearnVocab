"""Gemini'nin Opus turuna yaptığı düzeltmeleri (veri/kalite_olcumu/gemini-duzeltme.tsv) veritabanına uygular.

Kullanım (proje kökünden):
  python3 araclar/gemini_uygula.py --db ~/db-calisma.sqlite3            # kuru deneme
  python3 araclar/gemini_uygula.py --db ~/db-calisma.sqlite3 --uygula   # yazar

- EFE satırları uygulanmaz (yalnızca efe.tsv gerekçelerini tamamlar).
- Efe'nin reddettiği kelimeler (17 Ekim 2026) atlanır: also, roc; croaker kararı bekliyor.
- Değer, dosyadaki "mevcut" değerle aynıysa değiştirilir; zaten yeni hâliyse geçilir; başka bir şeyse atlanır.
- Uygulananlar veri/kalite_olcumu/gemini-uygulanan.tsv dosyasına eklenir (geri alma için).
"""
import argparse
import csv
import datetime
import re
from pathlib import Path
import sqlite3

K = Path("veri/kalite_olcumu")
REDDEDILEN = {"also", "roc", "croaker"}
SINIR = {"TR": 300, "EN": 600, "ORNEK": 400}


def tek(s):
    return " ".join((s or "").split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--uygula", action="store_true")
    a = ap.parse_args()

    db = sqlite3.connect(Path(a.db).expanduser())
    uygulanan, atlanan, zaten = [], [], 0
    with open(K / "gemini-duzeltme.tsv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            alan = r["alan"]
            if alan not in SINIR or r["kelime"] in REDDEDILEN:
                continue
            mid = int(r["kimlik"])
            # Virgülden sonra boşluk eksikse ekle (ör. "nezaket,ölçülülük")
            yeni = re.sub(r",(?=\S)", ", ", tek(r["gemini_duzeltmesi"])) if alan == "TR" else tek(r["gemini_duzeltmesi"])
            if len(yeni) > SINIR[alan]:
                atlanan.append((r["kimlik"], r["kelime"], alan, "çok uzun"))
                continue
            if alan == "ORNEK":
                k = db.execute("SELECT id, text FROM words_examplesentence WHERE meaning_id=? ORDER BY sort_order, id LIMIT 1", (mid,)).fetchone()
            else:
                sutun = "meaning_tr" if alan == "TR" else "definition"
                k = db.execute(f"SELECT id, {sutun} FROM words_meaning WHERE id=?", (mid,)).fetchone()
            if k is None:
                atlanan.append((r["kimlik"], r["kelime"], alan, "kayıt yok"))
                continue
            if tek(k[1]) == yeni:
                zaten += 1
                continue
            if tek(k[1]) != tek(r["mevcut_veya_claude_degeri"]):
                atlanan.append((r["kimlik"], r["kelime"], alan, "değer başka biçimde değişmiş"))
                continue
            if a.uygula:
                if alan == "ORNEK":
                    db.execute("UPDATE words_examplesentence SET text=? WHERE id=?", (yeni, k[0]))
                else:
                    db.execute(f"UPDATE words_meaning SET {sutun}=? WHERE id=?", (yeni, mid))
            uygulanan.append((r["kimlik"], r["kelime"], alan, tek(k[1]), yeni))
    if a.uygula:
        db.commit()
        zaman = datetime.datetime.now().isoformat(timespec="seconds")
        with open(K / "gemini-uygulanan.tsv", "a", encoding="utf-8") as f:
            for u in uygulanan:
                f.write("\t".join((zaman,) + u) + "\n")
    print(f"{'Uygulandı' if a.uygula else 'Kuru deneme — uygulanacak'}: {len(uygulanan)} · önceden uygulanmış: {zaten} · atlanan: {len(atlanan)}")
    for x in atlanan:
        print("  atlandı:", *x)


if __name__ == "__main__":
    main()
