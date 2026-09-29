"""
Telaffuz ses dosyaları (rapor 18.4).

Sesler bir kez, Efe'nin bilgisayarında açık kaynak Kokoro modeliyle
üretilir (araclar/telaffuz_uret.py) ve MEDIA_ROOT/telaffuz/ altına MP3
olarak yazılır: US = af_heart, UK = bf_emma. Dosya yoksa kart tarayıcının
kendi sesine döner (base/_kelimeKartiJs.html).

Bu modül Django'ya bağımlı DEĞİL: üretim betiği ayrı bir sanal ortamda
(Kokoro'nun olduğu) çalışıyor ve dosya adını buradan alıyor. Site ile
betik aynı adı üretmek zorunda.
"""

import re

KLASOR = "telaffuz"
AKSANLAR = {"us": "en-US", "uk": "en-GB"}


def dosya_adi(metin, aksan):
    """
    'Give up' + 'us' -> 'give-up_us.mp3'. Küçük harf; harf ve rakam dışındaki
    her şey tek tireye iner. Boş kalırsa None.
    """
    kok = re.sub(r"[^a-z0-9]+", "-", (metin or "").strip().lower()).strip("-")
    if not kok or aksan not in AKSANLAR:
        return None
    return f"{kok}_{aksan}.mp3"
