"""
Bütün kelime ve ifadelerin telaffuz seslerini üretir (rapor 18.4).

Projenin sanal ortamında DEĞİL, Kokoro'nun kurulu olduğu ayrı ortamda
çalışır (Efe'nin bilgisayarında ~/LearnVocab-ses-deneme/.venv):

    ~/LearnVocab-ses-deneme/.venv/bin/python araclar/telaffuz_uret.py \
        --model ~/LearnVocab-ses-deneme --paralel 4

- Kelimeleri db.sqlite3'ten SALT OKUNUR okur (Django gerekmez).
- US = af_heart (en-us), UK = bf_emma (en-gb); hız 0,9; MP3.
- media/telaffuz/ altına yazar. Var olan dosyayı atlar: yarıda kalırsa
  aynı komutla kaldığı yerden devam eder.
- Ücretsiz ve yerel: hiçbir servise istek atmaz.
"""

import argparse
import multiprocessing as mp
import os
import sqlite3
import sys
import time

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)
from words.telaffuz import KLASOR, dosya_adi  # noqa: E402

SESLER = {"us": ("af_heart", "en-us"), "uk": ("bf_emma", "en-gb")}
_model = None


def metinler(db):
    bag = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    kelimeler = [r[0] for r in bag.execute("select distinct lower(text) from words_word")]
    ifadeler = [r[0] for r in bag.execute("select distinct text from words_expression")]
    bag.close()
    gorulen, sonuc = {}, []
    for m in kelimeler + ifadeler:
        ad = dosya_adi(m, "us")
        if not ad:
            continue
        if ad in gorulen:          # aynı dosya adına düşen iki yazım: ilki kalır
            continue
        gorulen[ad] = m
        sonuc.append(m)
    return sonuc


def _baslat(model_klasoru, is_parcacigi):
    global _model
    import onnxruntime as ort
    from kokoro_onnx import Kokoro
    ayar = ort.SessionOptions()
    ayar.intra_op_num_threads = is_parcacigi
    oturum = ort.InferenceSession(os.path.join(model_klasoru, "kokoro-v1.0.onnx"), ayar)
    _model = Kokoro.from_session(oturum, os.path.join(model_klasoru, "voices-v1.0.bin"))


def _uret(is_):
    import soundfile as sf
    metin, aksan, hedef = is_
    ses, dil = SESLER[aksan]
    try:
        ornekler, hiz = _model.create(metin, voice=ses, speed=0.9, lang=dil)
        gecici = hedef + ".yaziliyor"
        sf.write(gecici, ornekler, hiz, format="MP3", compression_level=0.6,
                 bitrate_mode="VARIABLE")
        os.replace(gecici, hedef)   # yarım dosya kalmasın
        return None
    except Exception as hata:  # tek kelimenin hatası bütün işi durdurmasın
        return f"{metin} [{aksan}]: {hata}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True, help="kokoro-v1.0.onnx ve voices-v1.0.bin klasörü")
    p.add_argument("--db", default=os.path.join(KOK, "db.sqlite3"))
    p.add_argument("--cikti", default=os.path.join(KOK, "media", KLASOR))
    p.add_argument("--paralel", type=int, default=4)
    p.add_argument("--limit", type=int, default=0, help="deneme için ilk N metin")
    a = p.parse_args()

    os.makedirs(a.cikti, exist_ok=True)
    liste = metinler(a.db)
    if a.limit:
        liste = liste[:a.limit]
    isler = [(m, aks, os.path.join(a.cikti, dosya_adi(m, aks)))
             for m in liste for aks in SESLER
             if not os.path.exists(os.path.join(a.cikti, dosya_adi(m, aks)))]
    print(f"{len(liste)} metin, {len(isler)} dosya üretilecek ({a.paralel} işlem)", flush=True)

    bas, hatalar, bitti = time.time(), [], 0
    is_parcacigi = max(1, (os.cpu_count() or 4) // a.paralel)
    with mp.Pool(a.paralel, initializer=_baslat, initargs=(a.model, is_parcacigi)) as havuz:
        for sonuc in havuz.imap_unordered(_uret, isler, chunksize=8):
            bitti += 1
            if sonuc:
                hatalar.append(sonuc)
            if bitti % 500 == 0 or bitti == len(isler):
                gecen = time.time() - bas
                kalan = gecen / bitti * (len(isler) - bitti)
                print(f"{bitti}/{len(isler)} · {gecen/60:.0f} dk geçti · ~{kalan/60:.0f} dk kaldı · {len(hatalar)} hata", flush=True)
    for h in hatalar:
        print("HATA", h, flush=True)
    print(f"bitti: {bitti - len(hatalar)} dosya, {len(hatalar)} hata, {(time.time()-bas)/60:.0f} dk", flush=True)


if __name__ == "__main__":
    main()
