"""Doğrulama aşaması kontrolü: eksik/bozuk dosyaları ve karar dağılımını gösterir.

Kullanım (proje kökünden): python3 araclar/dogrulama_kontrol.py [klasör]
Klasör varsayılanı veri/kalite_olcumu/dogrulama; Opus turu için veri/kalite_olcumu/opus.
Çıktı: özet + <klasör>/eksik.txt (girdi dosya adlarının sırasıyla)
"""
from collections import Counter
import sys
from pathlib import Path

D = Path(sys.argv[1] if len(sys.argv) > 1 else "veri/kalite_olcumu/dogrulama")
KARARLAR = {"DUZELT", "BIRAK", "EFE"}
ALANLAR = {"TR", "EN", "ORNEK"}


def gecerli(ad):
    cikti = D / "cikti" / f"{ad}.tsv"
    if not cikti.exists():
        return False
    beklenen = [s.split("|")[0].strip() for s in (D / "girdi" / f"{ad}.txt").read_text(encoding="utf-8").splitlines() if s.strip()]
    gorulen = []
    for s in cikti.read_text(encoding="utf-8").splitlines():
        if not s.strip():
            continue
        f = s.split("\t")
        if len(f) < 2 or f[1].strip() not in KARARLAR:
            return False
        if f[1].strip() == "DUZELT" and (len(f) < 4 or f[2].strip() not in ALANLAR or not f[3].strip()):
            return False
        if not gorulen or gorulen[-1] != f[0].strip():
            gorulen.append(f[0].strip())
    return gorulen == beklenen


# Sıra: o (işaretli) → y (hiç taranmamış) → t (temiz); dogrulama klasöründe yalnız d
dosyalar = sorted((p.stem for p in (D / "girdi").glob("*.txt")), key=lambda a: ("doyt".index(a[0]), a))
eksik = [d for d in dosyalar if not gecerli(d)]
bozuk = [d for d in eksik if (D / "cikti" / f"{d}.tsv").exists()]
(D / "eksik.txt").write_text("".join(d + "\n" for d in eksik), encoding="utf-8")

karar, alan = Counter(), Counter()
for d in dosyalar:
    if d in eksik:
        continue
    goruldu = set()
    for s in (D / "cikti" / f"{d}.tsv").read_text(encoding="utf-8").splitlines():
        f = s.split("\t")
        if len(f) > 1:
            if f[0] not in goruldu:
                karar[f[1].strip()] += 1
                goruldu.add(f[0])
            if f[1].strip() == "DUZELT":
                alan[f[2].strip()] += 1
print(f"Doğrulama: {len(dosyalar) - len(eksik)}/{len(dosyalar)} dosya geçerli · kararlar: {dict(karar)} · düzeltilen alanlar: {dict(alan)}")
print(f"Eksik: {len(eksik)} · bozuk: {len(bozuk)} {' '.join(bozuk)}")
