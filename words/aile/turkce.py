"""
Türkçe yazım denetimi — modelin yazdığı Türkçe karşılıklarda OLMAYAN kelime var mı?

2. doldurma denemesinde veritabanına "kirlık" (kirlilik), "teşeksiz",
"varolmama" gibi Türkçede olmayan kelimeler girdi. Bunları yakalamanın
kodla ölçülebilir yolu bir Türkçe sözlük. İngilizce tarafta wordfreq ne işi
görüyorsa Türkçe tarafta bu modül onu görüyor.

NEDEN HUNSPELL
--------------
Türkçe eklemeli bir dil: "kirletilmiş", "öngörülemezlik", "evlat edinilmiş"
düz bir kelime listesinde olmaz. Kelime listesi (wordfreq'in Türkçesi dahil)
"kirletmek"i bile tanımıyor. Hunspell sözlüğü kök + ek kurallarıyla çalıştığı
için çekimli ve türemiş biçimleri de tanıyor.

  sözlük : LibreOffice'in tr_TR sözlüğü (MPL), ~38 MB
  motor  : spylls (saf Python hunspell; derleme gerektirmiyor)

KURULUM
-------
    pip install spylls
    python manage.py turkce_sozluk_kur

Sözlük words/aile/sozluk/ klasörüne iner (git'e girmez, .gitignore'da).
Kurulu değilse denetim sessizce ATLANMAZ: aile_doldur başlarken yazar.

Yüklemesi ~8 saniye sürüyor; süreç başına bir kez yükleniyor.
"""

import re
from pathlib import Path

KLASOR = Path(__file__).with_name("sozluk")
AD = "tr_TR"
ADRES = "https://raw.githubusercontent.com/LibreOffice/dictionaries/master/tr_TR/"

KELIME = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşüÂâÎîÛû]+")
SAPKASIZ = str.maketrans("âîûÂÎÛ", "aiuAIU")

# Hunspell'in YANLIŞLIKLA tanıdığı hatalı yazımlar. Buradakiler sözlükte
# olsa bile bilinmeyen sayılır. ÖRNEK: "kirlendirmek" (DOĞRU: kirletmek).
YASAKLI = {"kirlendirmek", "kirlendir", "kirlendirme"}

_sozluk = None
_denendi = False
_hata = ""


def turkce_kucuk(metin):
    """Türkçe küçük harf: İ -> i, I -> ı (Python'un lower()'ı I'yı i yapar)."""
    return (metin or "").replace("İ", "i").replace("I", "ı").lower()


def kurulu_mu():
    return (KLASOR / f"{AD}.dic").exists() and (KLASOR / f"{AD}.aff").exists()


def durum():
    """(hazır mı, açıklama) — komutlar başlarken ekrana yazıyor."""
    try:
        import spylls  # noqa: F401
    except ImportError:
        return False, "spylls kurulu değil (pip install spylls)"
    if not kurulu_mu():
        return False, "sözlük yok (python manage.py turkce_sozluk_kur)"
    return True, "hunspell tr_TR"


def _yukle():
    global _sozluk, _denendi, _hata
    if not _denendi:
        _denendi = True
        hazir, aciklama = durum()
        if not hazir:
            _hata = aciklama
            return None
        try:
            from spylls.hunspell import Dictionary
            _sozluk = Dictionary.from_files(str(KLASOR / AD))
        except Exception as hata:   # bozuk dosya vb.
            _hata = f"sözlük yüklenemedi: {hata}"
            _sozluk = None
    return _sozluk


def hazir_mi():
    return _yukle() is not None


def bilinmeyenler(metin):
    """
    Metindeki, sözlüğün tanımadığı kelimeler (sırayla, tekrarsız).
    Sözlük yoksa boş liste döner — çağıran taraf hazir_mi() ile bakmalı.
    """
    sozluk = _yukle()
    if sozluk is None:
        return []
    sonuc = []
    for kelime in KELIME.findall(metin or ""):
        if len(kelime) < 2:
            continue
        kucuk = turkce_kucuk(kelime)
        if kucuk in sonuc:
            continue
        # Önce küçük harfle; tanınmazsa yazıldığı gibi (özel isimler); o da
        # olmazsa şapkasız (hâkim -> hakim: sözlük şapkalı yazımı tanımıyor,
        # ikisi de doğru kabul ediliyor).
        sapkasiz = kucuk.translate(SAPKASIZ)
        if any(kucuk.startswith(y) for y in YASAKLI):
            sonuc.append(kucuk)
            continue
        if sozluk.lookup(kucuk) or sozluk.lookup(kelime) or sozluk.lookup(sapkasiz):
            continue
        if _birlesik_mi(sozluk, kucuk):
            continue
        sonuc.append(kucuk)
    return sonuc


def _birlesik_mi(sozluk, kelime):
    """
    Bitişik yazılmış birleşik kelime mi? (köpekbalığı = köpek + balığı,
    ayçiçeği, hanımeli). Sözlük birçoğunu tanımıyor; iki parçası da gerçek
    kelimeyse kabul (25 Eylül: shark "köpekbalığı" yüzünden reddedilmişti).
    """
    # İki parça da en az 4 harf: kısa parçalar ("teş" + "eksiz") sözlükte
    # bir şekilde bulunuyor ve uydurma kelimeyi kabul ettiriyordu.
    # İkinci parça en az 5 harf: "varol" + "mama" gibi rastlantılar elenir.
    for i in range(4, len(kelime) - 4):
        bas, son = kelime[:i], kelime[i:]
        if sozluk.lookup(bas) and sozluk.lookup(son):
            return True
    return False
