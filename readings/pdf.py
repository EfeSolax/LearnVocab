"""
"Kendi metinlerim" için PDF'ten okunabilir metin (rapor 8).

words/extract/pdf.py kelime çıkarma hattı için yazıldı (dosya yolu alır,
kaynakçayı keser, bitişik harf onarımı için sıklık verisine bakar). Burada
ihtiyaç daha basit ve farklı: yüklenen dosyanın BAYTLARINDAN, okumaya
uygun paragraflar. Dosya diske yazılmaz, saklanmaz; yalnızca metin kalır.

v1'de OCR yok: metin katmanı olmayan (taranmış) PDF'lerde nazik bir hata
verilir.
"""

import re

# Sınırlar: sunucuyu yormasın, okuma ekranı da makul kalsın.
EN_BUYUK_BOYUT = 10 * 1024 * 1024        # 10 MB
EN_COK_SAYFA = 60
EN_COK_KARAKTER = 150_000                 # ~25 bin kelime; fazlası kesilir

# Bütün belgede bundan az harf varsa belge büyük olasılıkla görüntü (tarama).
TARAMA_ESIGI = 20

TARANMIS_MESAJI = "Bu PDF'te okunabilir metin bulamadık (taranmış olabilir)."


class PdfOkunamadi(Exception):
    """Kullanıcıya olduğu gibi gösterilebilecek, nazik bir mesaj taşır."""


def _pymupdf():
    try:
        import pymupdf
        return pymupdf
    except ImportError:                    # pragma: no cover
        try:
            import fitz as pymupdf         # eski paket adı
            return pymupdf
        except ImportError as hata:
            raise PdfOkunamadi("PDF okuyucu şu an kullanılamıyor. Metni kopyalayıp "
                               "yapıştırmayı dener misin?") from hata


def _paragraf(blok):
    """Bir metin bloğunu tek paragrafa çevirir: satır sonu tireleri birleşir."""
    blok = re.sub(r"([A-Za-z])-\s*\n\s*([a-z])", r"\1\2", blok)
    blok = re.sub(r"\s*\n\s*", " ", blok)
    return re.sub(r"[ \t ]+", " ", blok).strip()


def _sayfa_numarasi_mi(p):
    return bool(re.fullmatch(r"[\d\s\-–—/.|]+|page \d+( of \d+)?", p, re.IGNORECASE))


def pdf_metni(veri):
    """
    PDF baytlarından okunabilir metin. Döner: (metin, bilgi)
      metin: paragraflar boş satırla ayrılmış
      bilgi: {"sayfa", "baslik", "kesildi"}
    Okunamazsa PdfOkunamadi (mesajı kullanıcıya gösterilebilir).
    """
    if len(veri) > EN_BUYUK_BOYUT:
        raise PdfOkunamadi("Bu PDF çok büyük. En çok 10 MB'lık dosyaları okuyabiliyoruz.")
    if not veri.startswith(b"%PDF"):
        raise PdfOkunamadi("Bu dosyayı PDF olarak açamadık. Başka bir dosya dener misin?")

    pymupdf = _pymupdf()
    try:
        belge = pymupdf.open(stream=veri, filetype="pdf")
    except Exception as hata:
        raise PdfOkunamadi("Bu dosyayı PDF olarak açamadık. Başka bir dosya dener misin?") from hata

    try:
        if belge.needs_pass:
            raise PdfOkunamadi("Bu PDF şifreli. Şifresiz bir kopyasını yükleyebilirsin.")
        if belge.page_count > EN_COK_SAYFA:
            raise PdfOkunamadi(f"Bu PDF {belge.page_count} sayfa. En çok {EN_COK_SAYFA} "
                               "sayfalık dosyaları okuyabiliyoruz; istersen bir bölümünü "
                               "kopyalayıp yapıştırabilirsin.")
        baslik = ((belge.metadata or {}).get("title") or "").strip()

        paragraflar = []
        for sayfa in belge:
            for blok in sayfa.get_text("blocks", sort=True):
                if len(blok) > 6 and blok[6] != 0:      # görsel bloğu
                    continue
                p = _paragraf(blok[4])
                if not p or _sayfa_numarasi_mi(p):
                    continue
                paragraflar.append(p)
        sayfa_sayisi = belge.page_count
    finally:
        belge.close()

    toplam_harf = sum(len(re.findall(r"[A-Za-z]", p)) for p in paragraflar)
    if toplam_harf < TARAMA_ESIGI:
        raise PdfOkunamadi(TARANMIS_MESAJI)

    metin = "\n\n".join(paragraflar)
    kesildi = len(metin) > EN_COK_KARAKTER
    if kesildi:
        metin = metin[:EN_COK_KARAKTER].rsplit("\n\n", 1)[0]
    return metin, {"sayfa": sayfa_sayisi, "baslik": baslik[:200], "kesildi": kesildi}
