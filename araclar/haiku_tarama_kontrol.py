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
    ap.add_argument("--duzelt", action="store_true", help="adı karışmış çıktı dosyalarını içeriğine göre doğru adına taşı")
    a = ap.parse_args()
    girdiler = sorted((KOK / "girdi").glob("b*.txt"))
    beklenenler = {g.stem: girdi_oku(g) for g in girdiler}
    kimlikten_grup = {frozenset(b): ad for ad, b in beklenenler.items()}
    eksik, bozuk, gecerli, yer_degisen, tasima = [], [], {}, [], []
    for c in sorted((KOK / "cikti").glob("b*.tsv")):
        sat = cikti_oku(c)
        idler = [x[0] for x in sat]
        # Dosya adına değil kimliklere bak: paralel ajanlar adları karıştırabiliyor.
        ad = kimlikten_grup.get(frozenset(idler))
        if ad is None or len(idler) != len(set(idler)) or idler != list(beklenenler[ad]):
            bozuk.append((c.stem, f"{len(idler)} satır, hiçbir girdi grubuyla birebir uyuşmuyor"))
            if a.bozuk_sil:
                c.unlink()
            continue
        if ad != c.stem:
            yer_degisen.append(f"{c.stem} → {ad}")
            tasima.append((c, ad))
        if ad in gecerli:
            bozuk.append((c.stem, f"{ad} grubunun yinelenen çıktısı"))
            continue
        gecerli[ad] = (beklenenler[ad], sat)
    eksik = [g.stem for g in girdiler if g.stem not in gecerli and not any(b[0] == g.stem for b in bozuk)]

    if a.duzelt and tasima:
        gecici = []
        for c, ad in tasima:          # önce geçici adlara, sonra doğru adlara (çakışma olmasın)
            t = c.with_name(f"_tasi_{ad}.tmp"); c.rename(t); gecici.append((t, ad))
        for t, ad in gecici:
            t.rename(KOK / "cikti" / f"{ad}.tsv")
        yer_degisen = [f"{x} (düzeltildi)" for x in yer_degisen]
    (KOK / "eksik.txt").write_text("\n".join(eksik) + ("\n" if eksik else ""), encoding="utf-8")

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
    if yer_degisen:
        d += ["", "## Dosya adı karışmış ama içerik geçerli (kimlikle eşleşti): " + ", ".join(yer_degisen[:10])]
    if eksik:
        d += ["", f"## Eksik ({len(eksik)}): " + ", ".join(eksik[:12]) + (" …" if len(eksik) > 12 else "")]
    (KOK / "durum.md").write_text("\n".join(d) + "\n", encoding="utf-8")
    print("\n".join(d))


if __name__ == "__main__":
    main()
