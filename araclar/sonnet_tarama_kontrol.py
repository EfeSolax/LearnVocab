"""Sonnet taraması kontrolü: girdi kimlikleriyle eşleşmeyen ya da eksik grupları listeler.

Kullanım (proje kökünden): python3 araclar/sonnet_tarama_kontrol.py
Çıktı: özet + veri/kalite_olcumu/sonnet-deneme/eksik.txt (önce hiç taranmamış gruplar, sonra Haiku'nun taradıkları).
"""
from pathlib import Path

GIRDI = Path("veri/kalite_olcumu/haiku-tarama/girdi")
CIKTI = Path("veri/kalite_olcumu/sonnet-deneme")
HAIKU = Path("veri/kalite_olcumu/haiku-tarama/cikti")


def kimlikler(yol, ayrac):
    return [s.split(ayrac)[0].strip() for s in yol.read_text(encoding="utf-8").splitlines() if s.strip()]


def gecerli(grup):
    cikti = CIKTI / f"{grup}.tsv"
    if not cikti.exists():
        return False
    satirlar = [s.split("\t") for s in cikti.read_text(encoding="utf-8").splitlines() if s.strip()]
    if [s[0].strip() for s in satirlar] != kimlikler(GIRDI / f"{grup}.txt", "|"):
        return False
    return all(len(s) > 1 and s[1].strip() in ("0", "1", "2") for s in satirlar)


gruplar = sorted(p.stem for p in GIRDI.glob("b*.txt"))
eksik = [g for g in gruplar if not gecerli(g)]
bozuk = [g for g in eksik if (CIKTI / f"{g}.tsv").exists()]
# Önce Haiku'nun da taramadığı gruplar, sonra Haiku'nun taradıkları
eksik.sort(key=lambda g: ((HAIKU / f"{g}.tsv").exists(), g))
(CIKTI / "eksik.txt").write_text("".join(g + "\n" for g in eksik), encoding="utf-8")

isaretli = puan2 = 0
for g in gruplar:
    if g not in eksik:
        for s in (CIKTI / f"{g}.tsv").read_text(encoding="utf-8").splitlines():
            p = s.split("\t")[1].strip() if "\t" in s else "0"
            isaretli += p in ("1", "2")
            puan2 += p == "2"
print(f"Sonnet taraması: {len(gruplar) - len(eksik)}/{len(gruplar)} grup geçerli · işaretli {isaretli} (puan 2: {puan2})")
print(f"Eksik: {len(eksik)} · bozuk (dosya var ama geçersiz): {len(bozuk)} {' '.join(bozuk)}")
