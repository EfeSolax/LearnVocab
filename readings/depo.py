"""
Kullanıcı metinlerinin diskteki deposu (rapor 18.24, 18.32).

Sunucudaki MySQL veritabanı en çok 1 GB; disk ise limitsiz. "Kendi
metinlerim"in gövdesi bu yüzden veritabanına değil, zlib ile sıkıştırılmış
dosya olarak diske yazılır (düz İngilizce metin 3–4 kat küçülür).
Veritabanında yalnızca başlık, dosya adı ve bilgiler durur (UserText.dosya).

Depo `settings.OZEL_DEPO` altındadır ve WEB'DEN SUNULMAZ (media/ değil):
bu metinler yalnızca sahibine özeldir.

    ad = depo.yeni_ad(owner_id)      -> "okumalar/12/3f9c….txt.z"
    depo.yaz(ad, metin)
    depo.oku(ad)                     -> metin ("" : dosya yoksa)
    depo.sil(ad)
"""

import uuid
import zlib
from pathlib import Path

from django.conf import settings

KLASOR = "okumalar"


def _yol(ad):
    kok = Path(settings.OZEL_DEPO).resolve()
    yol = (kok / ad).resolve()
    if kok not in yol.parents:                 # "../" ile depodan çıkılamasın
        raise ValueError("Depo dışında bir yol.")
    return yol


def yeni_ad(owner_id):
    return f"{KLASOR}/{owner_id}/{uuid.uuid4().hex}.txt.z"


def yaz(ad, metin):
    yol = _yol(ad)
    yol.parent.mkdir(parents=True, exist_ok=True)
    gecici = yol.with_suffix(".yaziliyor")
    gecici.write_bytes(zlib.compress((metin or "").encode("utf-8"), 9))
    gecici.replace(yol)                        # yarım dosya kalmasın


def oku(ad):
    try:
        return zlib.decompress(_yol(ad).read_bytes()).decode("utf-8")
    except (FileNotFoundError, ValueError, zlib.error):
        return ""


def sil(ad):
    if not ad:
        return
    try:
        _yol(ad).unlink()
    except (FileNotFoundError, ValueError):
        pass
