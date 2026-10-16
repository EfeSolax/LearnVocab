"""Gemini'nin ikinci değerlendirmesinden (gemini-t-duzeltme.tsv + gemini-114-sonrasi-duzeltme.tsv)
Claude ile ortak kabul edilen düzeltmeleri gemini-2-uygulanacak.tsv dosyasına yazar (Efe onayı, 17 Ekim 2026).

Kurallar:
- Veritabanındaki değer Gemini'nin gördüğünden farklıysa (Opus zaten düzeltmiş) atlanır.
- Reddedilenler: torpedo (torpido başka şey), sanction / patriarch / orchestrate / come on / go ahead
  (tek kayda başka anlam eklenmiş). emigrate'te "hicret etmek" çıkarılır.
- "(with ile) " gibi parçacık etiketi yalnızca anlam parçacıksız oluşmuyorsa kalır (TUT kümesi);
  diğerlerinde etiket atılır, karşılık iyileştirmesi korunur.
"""
import csv
import re
import sqlite3
from pathlib import Path

K = Path("veri/kalite_olcumu")
RED = {"torpedo", "sanction", "patriarch", "orchestrate", "come on", "go ahead"}
TUT = {"alight", "comport", "accord", "consort", "mill", "pine", "fixate", "abound"}
ETIKET = re.compile(r"^\([^()]* ile\) ")


def tek(s):
    return " ".join((s or "").split())


db = sqlite3.connect("file:db.sqlite3?mode=ro", uri=True)
satirlar, gorulen = [], set()
for ad, mk in (("gemini-t-duzeltme.tsv", "mevcut_deger"), ("gemini-114-sonrasi-duzeltme.tsv", "mevcut_veya_claude_degeri")):
    with open(K / ad, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            anahtar = (r["kimlik"], r["alan"])
            if r["alan"] not in ("TR", "EN") or r["kelime"] in RED or anahtar in gorulen:
                continue
            gorulen.add(anahtar)
            sutun = "meaning_tr" if r["alan"] == "TR" else "definition"
            simdi = db.execute(f"SELECT {sutun} FROM words_meaning WHERE id=?", (int(r["kimlik"]),)).fetchone()
            if not simdi or tek(simdi[0]) != tek(r[mk]):
                continue
            yeni = tek(r["gemini_duzeltmesi"])
            if r["alan"] == "TR":
                if r["kelime"] not in TUT and not ETIKET.match(tek(r[mk])):
                    yeni = ETIKET.sub("", yeni)
                if r["kelime"] == "emigrate":
                    yeni = yeni.replace(", hicret etmek", "")
            satirlar.append({"kimlik": r["kimlik"], "kelime": r["kelime"], "tur": r["tur"], "alan": r["alan"],
                             "mevcut_veya_claude_degeri": tek(r[mk]), "gemini_duzeltmesi": yeni, "neden": r["neden"]})
with open(K / "gemini-2-uygulanacak.tsv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(satirlar[0]), delimiter="\t")
    w.writeheader()
    w.writerows(satirlar)
print(len(satirlar), "satır")
