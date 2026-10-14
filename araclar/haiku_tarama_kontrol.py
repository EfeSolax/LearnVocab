"""Haiku taramasının çıktılarını doğrular, birleştirir ve özetler (salt okunur; veritabanına dokunmaz).

    python3 araclar/haiku_tarama_kontrol.py            # durum + birleştirme
    python3 araclar/haiku_tarama_kontrol.py --bozuk-sil # bozuk çıktı dosyalarını sil (yeniden üretilsin)

Girdi : veri/kalite_olcumu/haiku-tarama/girdi/bNNNN.txt   (100 satır: kimlik | kelime | ...)
Çıktı : veri/kalite_olcumu/haiku-tarama/cikti/bNNNN.tsv   (Haiku yazar: kimlik<TAB>puan<TAB>tür<TAB>neden)
Üretir: sonuc.tsv (geçerli tüm satırlar), isaretlenen.tsv (puan >= 1, girdi satırıyla birlikte), durum.md
"""
import argparse
import collections
import re
from pathlib import Path

KOK = Path("veri/kalite_olcumu/haiku-tarama")


def girdi_oku(yol):
    satirlar = {}
    for s in yol.read_text(encoding="utf-8").splitlines():
        if s.strip():
            satirlar[int(s.split("|", 1)[0])] = s
    return satirlar


def cikti_oku(yol):
    """Satırları ayrıştırır; kod bloğu çitlerini ve başlıkları yok sayar. [(kimlik, puan, tür, neden)]"""
    sonuc = []
    for s in yol.read_text(encoding="utf-8").splitlines():
        s = s.strip().strip("`")
        m = re.match(r"^(\d+)\s*[\t ]\s*([012])(?:\s*[\t ]\s*([AB])?\s*[\t ]?\s*(.*))?$", s)
        if m:
            sonuc.append((int(m.group(1)), int(m.group(2)), m.group(3) or "", (m.group(4) or "").strip()))
    return sonuc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bozuk-sil", action="store_true")
    a = ap.parse_args()
    girdiler = sorted((KOK / "girdi").glob("b*.txt"))
    eksik, bozuk, gecerli = [], [], {}
    for g in girdiler:
        ad = g.stem
        c = KOK / "cikti" / f"{ad}.tsv"
        if not c.exists():
            eksik.append(ad)
            continue
        beklenen = girdi_oku(g)
        sat = cikti_oku(c)
        idler = [x[0] for x in sat]
        if idler != list(beklenen):
            bozuk.append((ad, f"{len(idler)} satır (beklenen {len(beklenen)}), kimlikler uyuşmuyor" if set(idler) != set(beklenen) else "sıra farklı"))
            if a.bozuk_sil:
                c.unlink()
            continue
        gecerli[ad] = (beklenen, sat)

    toplam = collections.Counter(); batch_oran = {}
    sonuc_satirlari, isaretli = [], []
    for ad, (beklenen, sat) in gecerli.items():
        n1 = sum(1 for x in sat if x[1] >= 1)
        batch_oran[ad] = n1 / len(sat)
        for mid, puan, tur, neden in sat:
            toplam[puan] += 1
            sonuc_satirlari.append(f"{mid}\t{puan}\t{tur}\t{neden}")
            if puan >= 1:
                isaretli.append(f"{puan}\t{tur}\t{neden}\t{beklenen[mid]}")
    (KOK / "sonuc.tsv").write_text("kimlik\tpuan\ttür\tneden\n" + "\n".join(sonuc_satirlari) + "\n", encoding="utf-8")
    isaretli.sort(key=lambda s: -int(s[0]))
    (KOK / "isaretlenen.tsv").write_text("puan\ttür\tneden\tgirdi_satiri\n" + "\n".join(isaretli) + "\n", encoding="utf-8")

    supheli = sorted(ad for ad, o in batch_oran.items() if o < 0.03 or o > 0.6)
    n = sum(toplam.values())
    d = [f"# Haiku taraması durumu", "",
         f"- Girdi dosyası: {len(girdiler)} · tamamlanan (geçerli): **{len(gecerli)}** · eksik: {len(eksik)} · bozuk: {len(bozuk)}",
         f"- Taranan anlam: **{n}** · puan 0: {toplam[0]} · puan 1: {toplam[1]} · puan 2: {toplam[2]}",
         f"- İşaretlenen (≥1): **{toplam[1] + toplam[2]}** ({100 * (toplam[1] + toplam[2]) / max(n, 1):.1f}%) — kalibrasyonda beklenen ~%25"]
    if bozuk:
        d += ["", "## Bozuk çıktılar (yeniden çalıştırılmalı; `--bozuk-sil` siler)"] + [f"- {ad}: {neden}" for ad, neden in bozuk[:40]]
    if supheli:
        d += ["", "## Şüpheli grup (işaretleme oranı <%3 ya da >%60: model tembellik/aşırı işaretleme yapmış olabilir)"] + [f"- {ad}: %{100 * batch_oran[ad]:.0f}" for ad in supheli[:40]]
    if eksik:
        d += ["", f"## Eksik ({len(eksik)}): " + ", ".join(eksik[:12]) + (" …" if len(eksik) > 12 else "")]
    (KOK / "durum.md").write_text("\n".join(d) + "\n", encoding="utf-8")
    print("\n".join(d))


if __name__ == "__main__":
    main()
