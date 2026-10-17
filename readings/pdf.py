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

from django.utils.translation import gettext as _

from .temizlik import anahtar, paragraflari_temizle

# Sınırlar: sunucuyu yormasın, okuma ekranı da makul kalsın.
# Rapor 18.24: PDF başına en çok 400 sayfa ve 50 MB.
EN_BUYUK_BOYUT = 50 * 1024 * 1024        # 50 MB
EN_BUYUK_BOYUT_MB = EN_BUYUK_BOYUT // (1024 * 1024)
EN_COK_SAYFA = 400
EN_COK_KARAKTER = 1_500_000               # ~400 sayfalık kitap; fazlası kesilir

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
            raise PdfOkunamadi(_("PDF okuyucu şu an kullanılamıyor. Metni kopyalayıp "
                                 "yapıştırmayı dener misin?")) from hata


def _paragraf(blok):
    """Bir metin bloğunu tek paragrafa çevirir: satır sonu tireleri birleşir."""
    blok = re.sub(r"([A-Za-z])-\s*\n\s*([a-z])", r"\1\2", blok)
    blok = re.sub(r"\s*\n\s*", " ", blok)
    return re.sub(r"[ \t ]+", " ", blok).strip()


def _sayfa_numarasi_mi(p):
    return bool(re.fullmatch(r"[\d\s\-–—/.|]+|page \d+( of \d+)?", p, re.IGNORECASE))


# Sayfanın başındaki ve sonundaki kaç blok üst/alt bilgi sayılabilir.
UC_BLOK = 2
# En az bu kadar sayfanın başında/sonunda geçen blok üst/alt bilgidir.
UST_ALT_SAYFA_ESIGI = 3
# Üst/alt bilgi kısa olur; uzun bir paragraf (aynı cümle birkaç kez geçse de) atılmaz.
UST_ALT_EN_COK_KELIME = 15


def _ust_alt_bilgisiz(bloklar):
    """
    Her sayfanın başında ya da sonunda tekrar eden blokları (kitap adı, yazar,
    "Free eBooks at …") atar: sayılar atılmış hâli en az 3 ayrı sayfanın
    ucunda geçiyorsa. Sayfa numarası farkı ("12 ANIMAL FARM") önemsizdir.
    """
    sayfalar = {}
    for p, no, uc in bloklar:
        a = anahtar(p)
        if uc and a and len(p.split()) <= UST_ALT_EN_COK_KELIME:
            sayfalar.setdefault(a, set()).add(no)
    tekrar = {a for a, s in sayfalar.items() if len(s) >= UST_ALT_SAYFA_ESIGI}
    return [p for p, no, uc in bloklar
            if not (uc and len(p.split()) <= UST_ALT_EN_COK_KELIME and anahtar(p) in tekrar)]


def pdf_metni(veri):
    """
    PDF baytlarından okunabilir metin. Döner: (metin, bilgi)
      metin: paragraflar boş satırla ayrılmış
      bilgi: {"sayfa", "baslik", "kesildi"}
    Okunamazsa PdfOkunamadi (mesajı kullanıcıya gösterilebilir).
    """
    if len(veri) > EN_BUYUK_BOYUT:
        raise PdfOkunamadi(_("Bu PDF çok büyük. En çok %(mb)s MB'lık dosyaları okuyabiliyoruz.") % {
            "mb": EN_BUYUK_BOYUT_MB})
    if not veri.startswith(b"%PDF"):
        raise PdfOkunamadi(_("Bu dosyayı PDF olarak açamadık. Başka bir dosya dener misin?"))

    pymupdf = _pymupdf()
    try:
        belge = pymupdf.open(stream=veri, filetype="pdf")
    except Exception as hata:
        raise PdfOkunamadi(_("Bu dosyayı PDF olarak açamadık. Başka bir dosya dener misin?")) from hata

    try:
        if belge.needs_pass:
            raise PdfOkunamadi(_("Bu PDF şifreli. Şifresiz bir kopyasını yükleyebilirsin."))
        if belge.page_count > EN_COK_SAYFA:
            raise PdfOkunamadi(_("Bu PDF %(sayfa)s sayfa. En çok %(en_cok)s sayfalık dosyaları "
                                 "okuyabiliyoruz; istersen bir bölümünü kopyalayıp "
                                 "yapıştırabilirsin.") % {"sayfa": belge.page_count, "en_cok": EN_COK_SAYFA})
        baslik = ((belge.metadata or {}).get("title") or "").strip()

        bloklar = []                     # (paragraf, sayfa no, sayfanın başında/sonunda mı)
        for no, sayfa in enumerate(belge):
            sayfanin = []
            for blok in sayfa.get_text("blocks", sort=True):
                if len(blok) > 6 and blok[6] != 0:      # görsel bloğu
                    continue
                p = _paragraf(blok[4])
                if not p or _sayfa_numarasi_mi(p):
                    continue
                sayfanin.append(p)
            for i, p in enumerate(sayfanin):
                bloklar.append((p, no, i < UC_BLOK or i >= len(sayfanin) - UC_BLOK))
        sayfa_sayisi = belge.page_count
    finally:
        belge.close()

    paragraflar = paragraflari_temizle(_ust_alt_bilgisiz(bloklar))
    toplam_harf = sum(len(re.findall(r"[A-Za-z]", p)) for p in paragraflar)
    if toplam_harf < TARAMA_ESIGI:
        raise PdfOkunamadi(TARANMIS_MESAJI)

    metin = "\n\n".join(paragraflar)
    kesildi = len(metin) > EN_COK_KARAKTER
    if kesildi:
        metin = metin[:EN_COK_KARAKTER].rsplit("\n\n", 1)[0]
    return metin, {"sayfa": sayfa_sayisi, "baslik": baslik[:200], "kesildi": kesildi}
