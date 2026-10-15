"""Haiku + Sonnet + pilot taramalarının işaretlediği anlamları birleştirip doğrulama girdisi üretir.

Kullanım (proje kökünden): python3 araclar/dogrulama_hazirla.py
Çıktı: veri/kalite_olcumu/dogrulama/girdi/dNNN.txt (50'şer kayıt; girdi satırı + || BULGU: ...)
"""
from pathlib import Path

K = Path("veri/kalite_olcumu")
KAYNAK = {"S": K / "sonnet-deneme", "H": K / "haiku-tarama/cikti", "P": K / "haiku-tarama/pilot-high"}
HEDEF = K / "dogrulama/girdi"

bulgu = {}
for ad, klasor in KAYNAK.items():
    for p in sorted(klasor.glob("b*.tsv")):
        for s in p.read_text(encoding="utf-8").splitlines():
            f = s.split("\t")
            if len(f) > 1 and f[1].strip() in ("1", "2"):
                bulgu.setdefault(f[0].strip(), []).append(f"{ad}:{f[1].strip()} {' '.join(x.strip() for x in f[2:4])}".strip())

satirlar = []
for p in sorted((K / "haiku-tarama/girdi").glob("b*.txt")):
    for s in p.read_text(encoding="utf-8").splitlines():
        kimlik = s.split("|")[0].strip()
        if kimlik in bulgu:
            satirlar.append(f"{s.strip()} || BULGU: {'; '.join(bulgu[kimlik])}")

for i in range(0, len(satirlar), 50):
    (HEDEF / f"d{i // 50 + 1:03d}.txt").write_text("\n".join(satirlar[i:i + 50]) + "\n", encoding="utf-8")
print(f"{len(satirlar)} kayıt, {(len(satirlar) + 49) // 50} dosya")
