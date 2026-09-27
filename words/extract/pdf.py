"""
PDF'ten düz metin (extract_words için).

Ham PDF metni doğrudan tokenlenirse kelime listesi kirleniyor:
  - satır sonunda bölünen kelimeler:   "environ-\\nment" -> "environ", "ment"
  - her sayfada tekrar eden başlık/alt bilgi (dergi adı, yazar, "Page 3")
  - sayfa numaraları
  - kaynakça: yazar soyadları, dergi adları, "et al." — öğrenciye kelime değil
Bu modül bunları temizliyor. Taranmış (görüntü) PDF'lerde metin katmanı
yoktur; onlar OCR ister ve rapora "taranmış" diye düşer, sessizce boş
geçilmez.

Kütüphane: PyMuPDF (pip install pymupdf). Kurulu değilse açık bir hata verir.
"""

import re
from collections import Counter
from pathlib import Path

# Sayfa başına bundan az harf varsa sayfa büyük olasılıkla görüntü (tarama).
TARAMA_ESIGI = 80
# Bir satır sayfaların en az bu oranında tekrar ediyorsa başlık/alt bilgidir.
TEKRAR_ORANI = 0.5
KAYNAKCA_BASLIKLARI = re.compile(
    r"^\s*(\d+\.?\s*)?(references|bibliography|works cited|literature cited|"
    r"reference list|sources)\s*$", re.IGNORECASE)


class PdfHatasi(Exception):
    pass


def _pymupdf():
    try:
        import pymupdf
        return pymupdf
    except ImportError:
        try:
            import fitz as pymupdf  # eski paket adı
            return pymupdf
        except ImportError as hata:
            raise PdfHatasi("PDF okumak için PyMuPDF gerekli: pip install pymupdf") from hata


def _normal_satir(satir):
    """Başlık karşılaştırması için: rakamlar atılır ("Page 3" == "Page 4")."""
    return re.sub(r"\d+", "#", satir.strip().lower())


def _tire_birlestir(metin):
    """
    "environ-\\nment" -> "environment". Ama "well-\\nknown" gibi gerçek tireli
    kelimeler korunur: birleşik hâl sözlükte yoksa tire kalır.
    """
    try:
        from wordfreq import zipf_frequency
    except ImportError:          # pragma: no cover
        zipf_frequency = None

    def birlestir(m):
        sol, sag = m.group(1), m.group(2)
        birlesik = sol + sag
        if zipf_frequency is None:
            return birlesik
        if zipf_frequency(birlesik.lower(), "en") >= zipf_frequency(f"{sol}-{sag}".lower(), "en"):
            return birlesik
        return f"{sol}-{sag}"

    return re.sub(r"([A-Za-z]+)-\s*\n\s*([a-z]+)", birlestir, metin)


LIGATURLER = ("fi", "fl", "ff", "ffi", "ffl")
# Belgede bundan az onarım varsa belge sağlam sayılır, onarım uygulanmaz.
LIGATUR_EN_AZ = 60   # ART C105: 23 sahte onarım ("CC BY-NC-ND" -> find)


def _sozlukte(kelime):
    from words import inflect
    return any(inflect.tur_sozlukte(kelime, t) is True
               for t in ("noun", "verb", "adjective", "adverb"))


def _ligatur_onar(metin):
    """
    Bazı PDF'lerde "fi/fl/ff" bitişik harfleri metin katmanında YOK: "first"
    -> "rst", "field" -> "eld" (24 Eylül, 17 PDF'lik deneme: "rst" 691 kez).
    Sözlükte olmayan bir parçaya eksik harfler eklenince çok daha yaygın,
    sözlükte olan bir kelime çıkıyorsa onarılır. Döner: (metin, onarım sayısı).
    """
    try:
        from wordfreq import zipf_frequency
    except ImportError:          # pragma: no cover
        return metin, 0
    esleme = {}
    for token in set(re.findall(r"[A-Za-z]{2,}", metin)):
        kucuk = token.lower()
        if token.isupper() or kucuk in esleme or _sozlukte(kucuk):   # ND, USA: kısaltma
            continue
        z = zipf_frequency(kucuk, "en")
        en_iyi, en_iyi_z = None, max(3.0, z + 1.5)
        for i in range(len(kucuk) + 1):
            for lig in LIGATURLER:
                aday = kucuk[:i] + lig + kucuk[i:]
                az = zipf_frequency(aday, "en")
                if az >= en_iyi_z and _sozlukte(aday):
                    en_iyi, en_iyi_z = aday, az
        if en_iyi:
            esleme[kucuk] = en_iyi
    if not esleme:
        return metin, 0
    sayi = 0

    def onar(m):
        nonlocal sayi
        k = m.group(0)
        aday = esleme.get(k.lower())
        if not aday or k.isupper():
            return k
        sayi += 1
        return aday.capitalize() if k[0].isupper() else aday

    yeni = re.sub(r"[A-Za-z]{2,}", onar, metin)
    return (yeni, sayi) if sayi >= LIGATUR_EN_AZ else (metin, 0)


def pdf_metni(yol):
    """
    Döner: (metin, bilgi). bilgi: sayfa, taranmis_sayfa, atilan_satir,
    kaynakca_kesildi (bool). Hiç metin yoksa PdfHatasi.
    """
    pymupdf = _pymupdf()
    try:
        belge = pymupdf.open(str(yol))
    except Exception as hata:
        raise PdfHatasi(f"PDF açılamadı: {hata}") from hata
    if belge.needs_pass:
        raise PdfHatasi("PDF şifreli")

    sayfalar = [sayfa.get_text("text", sort=True) for sayfa in belge]
    belge.close()
    taranmis = sum(1 for s in sayfalar if len(re.findall(r"[A-Za-z]", s)) < TARAMA_ESIGI)
    if not sayfalar or taranmis == len(sayfalar):
        raise PdfHatasi("PDF'te metin katmanı yok (taranmış görüntü); OCR gerekir")

    # Başlık / alt bilgi: sayfaların yarısından fazlasında geçen kısa satırlar
    sayac = Counter()
    for s in sayfalar:
        sayac.update({_normal_satir(x) for x in s.splitlines() if 0 < len(x.strip()) <= 80})
    esik = max(2, int(len(sayfalar) * TEKRAR_ORANI))
    tekrarlar = {x for x, n in sayac.items() if n >= esik} if len(sayfalar) >= 3 else set()

    satirlar, atilan = [], 0
    for s in sayfalar:
        for satir in s.splitlines():
            temiz = satir.strip()
            if not temiz:
                satirlar.append("")
                continue
            if re.fullmatch(r"[\d\s\-–—/.|]+|page \d+( of \d+)?", temiz, re.IGNORECASE) \
                    or _normal_satir(temiz) in tekrarlar:
                atilan += 1
                continue
            satirlar.append(temiz)
        satirlar.append("")

    # Kaynakça: belgenin son %40'ında bir "References" başlığı varsa oradan kes.
    kesildi = False
    sinir = int(len(satirlar) * 0.6)
    for i in range(len(satirlar) - 1, sinir - 1, -1):
        if KAYNAKCA_BASLIKLARI.match(satirlar[i]):
            satirlar, kesildi = satirlar[:i], True
            break

    metin = _tire_birlestir("\n".join(satirlar))
    metin, ligatur = _ligatur_onar(metin)
    metin = re.sub(r"\n{3,}", "\n\n", metin).strip()
    # Paragraf içi satır sonları boşluk olur: PDF satırı cümlenin ortasında
    # bölüyor; bölünmezse her satır başı "cümle başı" sanılıyor ve oradaki
    # özel isimler (Maria) kaçıyordu.
    metin = re.sub(r"(?<!\n)\n(?!\n)", " ", metin)
    return metin, {"sayfa": len(sayfalar), "taranmis_sayfa": taranmis,
                   "atilan_satir": atilan, "kaynakca_kesildi": kesildi,
                   "ligatur_onarimi": ligatur}


def pdf_mi(yol):
    return Path(yol).suffix.lower() == ".pdf"
