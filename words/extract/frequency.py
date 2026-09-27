"""
İngilizce sıklık verisi.

İKİ KAYNAK, BİRİ ZORUNLU DEĞİL
------------------------------
1. `wordfreq` paketi (varsa): 800 binden fazla kelime için sürekli bir
   sıklık değeri (Zipf ölçeği) veriyor. Eşik ayarlanabilir oluyor ve
   "bu kelime gerçek bir İngilizce kelime mi" sorusunun cevabı da
   buradan geliyor.
2. `top_english.txt` (her zaman var): en sık 5000 kelime, wordfreq'ten
   BİR KEZ üretilip dosyaya sabitlendi.

İkincisi neden var: bu komutun çalışması için bir paketin kurulu olması
şart olmamalı. Canlı sunucuda ya da başka bir makinede `pip install`
yapamadan da kelime süzülebilmeli. wordfreq kuruluysa daha iyi sonuç
veriyor, değilse liste yetiyor.

ZIPF ÖLÇEĞİ NEDİR
-----------------
Logaritmik: 7 = "the" gibi en sık kelimeler, 5 = günlük yaygın kelime,
3 = eğitimli bir okurun bildiği kelime, 2 = nadir, 1 ve altı = teknik
terim / özel isim / yazım hatası.

  the             7.73
  make            6.08
  analysis        4.91
  ubiquitous      3.42
  notwithstanding 3.48
  mitochondrion   1.92

Hazırlık öğrencisi için hedef bant kabaca 2.5 – 4.5: altı fazla teknik,
üstü zaten biliniyor.
"""

from pathlib import Path

VERI_DOSYASI = Path(__file__).with_name("top_english.txt")

# Bu değerin altındaki kelimeler "aşırı teknik / özel isim / hatalı yazım"
# sayılıp eleniyor. 1.8, mitochondrion'ın (1.92) hemen altında duruyor —
# yani gerçek ama çok teknik kelimeler sınırda kalıyor, uydurma diziler
# eleniyor.
VARSAYILAN_MIN_ZIPF = 1.8

# Bunun ÜSTÜNDEKİ kelimeler "zaten biliniyor" sayılıp eleniyor.
# Varsayılan olarak kapalı (None): eleme işi --top-skip ile sıra üzerinden
# yapılıyor, çünkü sıra hazırlık öğrencisinin sezgisine daha yakın.
VARSAYILAN_MAX_ZIPF = None


_wordfreq = None
_denendi = False


def _wf():
    """wordfreq varsa döner, yoksa None. Bir kez denenir."""
    global _wordfreq, _denendi
    if not _denendi:
        _denendi = True
        try:
            import wordfreq
            _wordfreq = wordfreq
        except ImportError:
            _wordfreq = None
    return _wordfreq


_sabit_liste = None


def sabit_liste():
    """top_english.txt içeriği, sıklık sırasına göre."""
    global _sabit_liste
    if _sabit_liste is None:
        satirlar = []
        if VERI_DOSYASI.exists():
            for satir in VERI_DOSYASI.read_text(encoding="utf-8").splitlines():
                satir = satir.strip()
                if satir and not satir.startswith("#"):
                    satirlar.append(satir)
        _sabit_liste = satirlar
    return _sabit_liste


def zipf(kelime: str) -> float:
    """
    Kelimenin Zipf sıklığı. wordfreq yoksa sabit listeden yaklaşık üretilir.

    Yaklaşık üretim kabaca doğru: listede ne kadar öndeyse o kadar sık.
    Listede hiç yoksa 0 dönüyor — yani "bilinmeyen kelime".
    """
    wf = _wf()
    if wf is not None:
        return wf.zipf_frequency(kelime.lower(), "en")

    liste = sabit_liste()
    try:
        sira = liste.index(kelime.lower())
    except ValueError:
        return 0.0
    # 1. sıra ≈ 7.7, 5000. sıra ≈ 3.4 — kabaca logaritmik bir eşleme.
    import math
    return max(7.7 - 1.25 * math.log10(sira + 1), 0.0)


def gecerli_kelime(kelime: str) -> bool:
    """
    Bu bir İngilizce kelime mi?

    Lemmatizer'ın "bu kök gerçek mi" kontrolü buradan geçiyor. Sıfırdan
    büyük bir sıklığı olan her dizi gerçek kabul ediliyor; wordfreq'in
    sözlüğü 800 binden fazla kelime içeriyor ve türemişleri de kapsıyor.

    wordfreq yoksa sabit liste 5000 kelimeyle sınırlı kalıyor ve
    lemmatizer belirgin biçimde zayıflıyor — komut çalışırken bunu
    ekrana yazıyor.
    """
    kelime = kelime.lower()
    if len(kelime) < 2:
        return False
    wf = _wf()
    if wf is not None:
        return wf.zipf_frequency(kelime, "en") > 0
    return kelime in set(sabit_liste())


def wordfreq_var_mi() -> bool:
    return _wf() is not None


def en_sik(n: int, lemma_fonksiyonu=None) -> set:
    """
    En sık n kelime — KÖK hâlleriyle.

    Ham liste çekimli biçimleri de içeriyor ("creating", "homes", "grew"
    ilk 2000'in içinde). Kök hâline indirilmeden sayılırsa "ilk 2000"
    aslında 1300 civarında farklı kelime demek oluyor ve eşik kullanıcının
    beklediğinden dar kalıyor.

    lemma_fonksiyonu verilirse liste köke indirilerek sayılıyor; böylece
    "ilk 2000" gerçekten 2000 ayrı kelime anlamına geliyor.
    """
    liste = sabit_liste()
    if lemma_fonksiyonu is None:
        return set(liste[:n])

    kokler = []
    gorulen = set()
    for kelime in liste:
        kok = lemma_fonksiyonu(kelime) or kelime
        if kok not in gorulen:
            gorulen.add(kok)
            kokler.append(kok)
        if len(kokler) >= n:
            break
    return set(kokler)
