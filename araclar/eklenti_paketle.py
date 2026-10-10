"""
Chrome eklentisini hazırlar (rapor 11, chrome-eklentisi/).

    .venv/bin/python araclar/eklenti_paketle.py --yerel
        tmp/eklenti-yerel/ klasörünü kurar: eklenti yerel sunucuya
        (http://localhost:8765) bağlanır. Chrome'da "Paketlenmemiş öğe yükle"
        ile bu klasör seçilir. Kaynak dosyalar değişmez.

    .venv/bin/python araclar/eklenti_paketle.py
        Web Store'a yüklenecek zip'i yapar: tmp/learnvocab-eklenti-<sürüm>.zip
        (canlı siteye bağlanır; README girmez).
"""

import argparse
import json
import shutil
import zipfile
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
KAYNAK = KOK / "chrome-eklentisi"
TMP = KOK / "tmp"
CANLI = "https://www.learnvocab.com.tr"
YEREL = "http://localhost:8765"
DISARIDA = {"README.md"}


def dosyalar():
    for yol in sorted(KAYNAK.rglob("*")):
        goreli = yol.relative_to(KAYNAK)
        if yol.is_file() and goreli.name not in DISARIDA and not goreli.name.startswith("."):
            yield yol, goreli


def yerel():
    hedef = TMP / "eklenti-yerel"
    if hedef.exists():
        shutil.rmtree(hedef)
    for yol, goreli in dosyalar():
        (hedef / goreli).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(yol, hedef / goreli)

    arkaplan = hedef / "arkaplan.js"
    metin = arkaplan.read_text()
    assert f'const SITE = "{CANLI}";' in metin, "arkaplan.js'de SITE satırı bulunamadı"
    arkaplan.write_text(metin.replace(f'const SITE = "{CANLI}";', f'const SITE = "{YEREL}";'))

    manifest = json.loads((hedef / "manifest.json").read_text())
    manifest["host_permissions"].append(f"{YEREL}/*")
    manifest["name"] = "LearnVocab (yerel)"
    (hedef / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"Hazır: {hedef}")


def paket():
    surum = json.loads((KAYNAK / "manifest.json").read_text())["version"]
    TMP.mkdir(exist_ok=True)
    hedef = TMP / f"learnvocab-eklenti-{surum}.zip"
    with zipfile.ZipFile(hedef, "w", zipfile.ZIP_DEFLATED) as z:
        for yol, goreli in dosyalar():
            z.write(yol, goreli.as_posix())
    print(f"Hazır: {hedef}")


if __name__ == "__main__":
    ayrac = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayrac.add_argument("--yerel", action="store_true", help="yerel deneme kopyası (localhost:8765)")
    if ayrac.parse_args().yerel:
        yerel()
    else:
        paket()
