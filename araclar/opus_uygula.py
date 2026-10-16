"""Opus turunun DUZELT kararlarını veritabanına uygular.

Kullanım (proje kökünden):
  python3 araclar/opus_uygula.py --db ~/db-calisma.sqlite3            # kuru deneme: yalnızca rapor
  python3 araclar/opus_uygula.py --db ~/db-calisma.sqlite3 --uygula   # yazar

- Yalnızca geçerli (kontrol aracından geçen) çıktı dosyaları işlenir.
- Bir alan, veritabanındaki değeri girdi dosyasındaki eski değerle aynıysa değiştirilir; değilse atlanır ve raporlanır
  (başkası değiştirmiş demektir); değer zaten yeni hâliyse sessizce geçilir, bu yüzden araç tekrar çalıştırılabilir.
- Uygulanan her değişiklik geri alınabilsin diye veri/kalite_olcumu/opus/uygulanan.tsv dosyasına eklenir.
- EFE kararları veri/kalite_olcumu/opus/efe.tsv dosyasına yazılır.
"""
import argparse
import datetime
import sqlite3
import subprocess
import sys
from pathlib import Path

D = Path("veri/kalite_olcumu/opus")
SINIR = {"TR": 300, "EN": 600, "ORNEK": 400}
ALAN_ADI = {"TR": "TR: ", "EN": "EN: ", "ORNEK": "ÖRNEK: "}


def tek(s):
    return " ".join((s or "").split())


def eski_degerler(satir):
    parca = satir.split(" || ")[0].split(" | ")
    d = {}
    for p in parca:
        for alan, onek in ALAN_ADI.items():
            if p.startswith(onek):
                d[alan] = p[len(onek):]
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--uygula", action="store_true")
    a = ap.parse_args()

    subprocess.run([sys.executable, "araclar/dogrulama_kontrol.py", str(D)], check=True, stdout=subprocess.DEVNULL)
    eksik = set((D / "eksik.txt").read_text(encoding="utf-8").split())

    db = sqlite3.connect(Path(a.db).expanduser())
    uygulanan, atlanan, efe = [], [], []
    zaten = 0
    for p in sorted((D / "cikti").glob("*.tsv")):
        if p.stem in eksik:
            continue
        eski = {s.split(" | ")[0].strip(): eski_degerler(s)
                for s in (D / "girdi" / f"{p.stem}.txt").read_text(encoding="utf-8").splitlines() if s.strip()}
        for s in p.read_text(encoding="utf-8").splitlines():
            f = [x.strip() for x in s.split("\t")] + [""] * 5
            kimlik, karar, alan, yeni = f[:4]
            # Fazladan TAB konmuş satırlarda gerekçe sağa kayar: ilk boş olmayanı al
            gerekce = next((x for x in f[4:] if x), "")
            if karar == "EFE":
                efe.append((kimlik, gerekce, p.stem))
            if karar != "DUZELT":
                continue
            if len(yeni) > SINIR[alan]:
                atlanan.append((kimlik, alan, "çok uzun"))
                continue
            mid = int(kimlik)
            if alan == "ORNEK":
                r = db.execute("SELECT id, text FROM words_examplesentence WHERE meaning_id=? ORDER BY sort_order, id LIMIT 1", (mid,)).fetchone()
            else:
                sutun = "meaning_tr" if alan == "TR" else "definition"
                r = db.execute(f"SELECT id, {sutun} FROM words_meaning WHERE id=?", (mid,)).fetchone()
            if r is None:
                atlanan.append((kimlik, alan, "kayıt yok"))
                continue
            if tek(r[1]) == tek(yeni):
                zaten += 1
                continue
            if tek(r[1]) != tek(eski[kimlik].get(alan)):
                atlanan.append((kimlik, alan, "değer başka biçimde değişmiş"))
                continue
            if a.uygula:
                if alan == "ORNEK":
                    db.execute("UPDATE words_examplesentence SET text=? WHERE id=?", (yeni, r[0]))
                else:
                    db.execute(f"UPDATE words_meaning SET {sutun}=? WHERE id=?", (yeni, mid))
            uygulanan.append((kimlik, alan, tek(r[1]), yeni, gerekce))
    if a.uygula:
        db.commit()
        zaman = datetime.datetime.now().isoformat(timespec="seconds")
        with open(D / "uygulanan.tsv", "a", encoding="utf-8") as f:
            for u in uygulanan:
                f.write("\t".join((zaman,) + u) + "\n")
    (D / "efe.tsv").write_text("".join("\t".join(e) + "\n" for e in efe), encoding="utf-8")
    print(f"{'Uygulandı' if a.uygula else 'Kuru deneme — uygulanacak'}: {len(uygulanan)} · önceden uygulanmış: {zaten} · atlanan: {len(atlanan)} · EFE: {len(efe)}")
    for x in atlanan[:20]:
        print("  atlandı:", *x)


if __name__ == "__main__":
    main()
