"""
reading-texts/ altındaki düz metin dosyalarını ayrıştırır.

Dosya biçimi (beş dosyada da aynı):

    25 SIBLINGS
    <boş satır>
    <paragraf, tek satır>
    <boş satır>
    <paragraf, tek satır>

Başlık satırı "<numara> <BÜYÜK HARFLİ BAŞLIK>" kalıbında. Konu adı dosya
adından geliyor: "1-10 Hukuk.txt" ve "13-22-Psikoloji.txt" gibi iki farklı
yazım da destekleniyor (biri boşluklu, diğeri tireli).
"""

import os
import re
import unicodedata


# "25 SIBLINGS", "41 WHO'S A GERMAN, THEN?" -> numara + başlık
BASLIK = re.compile(r"^(\d+)\s+([^a-zçğıöşü]+)$")

# "1-10 Hukuk", "13-22-Psikoloji" -> konu adı
DOSYA_ADI = re.compile(r"^\d+\s*-\s*\d+[\s\-_]*(.+)$")


def topic_key(ad):
    """
    "Eğitim" -> "egitim". Konu anahtarı Türkçe karakter içermesin ki URL'de
    ve veritabanında sorun çıkarmasın.
    """
    eslem = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    sade = ad.strip().translate(eslem)
    sade = unicodedata.normalize("NFKD", sade).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sade.lower()).strip("-")


def topic_from_filename(yol):
    """Dosya adından konu adını çıkarır; çıkaramazsa dosya adını döner."""
    taban = os.path.splitext(os.path.basename(yol))[0]
    eslesme = DOSYA_ADI.match(taban)
    return (eslesme.group(1) if eslesme else taban).strip()


def parse_text_file(icerik):
    """
    Bir dosyanın içeriğini metin sözlüklerine çevirir.

    Başlıktan önce gelen satırlar (sohbetten kalma açıklama cümleleri gibi)
    sessizce atlanıyor.
    """
    metinler = []
    simdiki = None

    for satir in icerik.splitlines():
        satir = satir.strip()
        if not satir:
            continue

        eslesme = BASLIK.match(satir)
        # Başlık satırı: harf içeriyor ve küçük harf içermiyor.
        if eslesme and any(k.isalpha() for k in eslesme.group(2)):
            simdiki = {
                "number": int(eslesme.group(1)),
                "title": eslesme.group(2).strip(),
                "paragraphs": [],
            }
            metinler.append(simdiki)
        elif simdiki is not None:
            simdiki["paragraphs"].append(satir)

    # Paragrafı olmayan başlık kaydı anlamsız
    return [m for m in metinler if m["paragraphs"]]


def parse_directory(klasor):
    """
    Klasördeki tüm .txt dosyalarını ayrıştırır ve metin listesini döner.
    Her metne dosya adından gelen konu bilgisi eklenir.
    """
    sonuc = []
    for dosya in sorted(os.listdir(klasor)):
        if not dosya.lower().endswith(".txt"):
            continue

        yol = os.path.join(klasor, dosya)
        with open(yol, encoding="utf-8") as f:
            icerik = f.read()

        konu_adi = topic_from_filename(yol)
        for metin in parse_text_file(icerik):
            metin["topic"] = topic_key(konu_adi)
            metin["topic_label"] = konu_adi
            metin["source_file"] = dosya
            sonuc.append(metin)

    return sonuc
