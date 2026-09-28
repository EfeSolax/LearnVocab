"""
Seviye testi ekran kelimelerinin seçimi (veri işi D8, rapor 7).

Kural (deterministik; aynı veritabanı + aynı wordfreq sürümü = aynı havuz):

  1. Aday: ortak sözlükteki (isBaseWord) isim/fiil/sıfat/zarf, tek sözcük,
     yalnızca küçük harf a–z ve en az 3 harf (özel ad, kısaltma, tireli
     yazım yok), en az bir örnek cümlesi var. UYDURMA KELİME YOK: her aday
     veritabanındaki bir Word.
  2. Kelimenin seviyesi = aynı yazımın bütün türleri arasındaki EN KOLAY
     seviye. Böylece "dog" (fiil, C1) zor ekrana düşmez; "light" yalnızca
     bir ekranda görünür.
  3. Hassas/müstehcen bir anlamı olan kelime alınmaz (rapor 12.2).
  4. wordfreq kuruluysa "yaygın ve tanınır" bandı (ZIPF_BANDI): çok nadir
     kelime tanınmaz; çok sık kelime (can, will, just) hiçbir şey ölçmez.
     Kurulu değilse bant atlanır (1–3 yine uygulanır).
  5. Bir seviyede bandı geçenler yazımın sha1 özetine göre sıralanır
     (keyfî ama sabit, sıklığa göre değil: yalnızca en sık kelimeleri almak
     zor ekranı kolaylaştırırdı) ve ilk HAVUZ_BOYU kadarı havuza girer.

Her testte ekran başına havuzdan rastgele 40 kelime; iki seviyeli ekranlarda
(A1–A2, B2–C1) iki seviyeden yarı yarıya.

`seviye_kelimeleri_sec` komutu bu seçimi SeviyeKelimesi tablosuna yazar
(--dry-run ile önce gözden geçirilir, --json ile dosyaya dökülür). Tablo
boşsa `ekran_kelimeleri` seçimi aynı kuralla anında yapar.
"""

import hashlib
import random
import re
from dataclasses import dataclass

from django.db.models import Exists, OuterRef

from words.models import ExampleSentence, Meaning, PartOfSpeech, Word

from .models import Ekran, SeviyeKelimesi

EKRAN_BOYU = 40

# Ekran -> kapsadığı seviyeler (rapor 7: A1–A2, B1–B1+, B2–C1). Veride
# "B1+" diye ayrı bir seviye yok; 2. ekran B1'dir.
EKRAN_SEVIYELERI = {
    Ekran.KOLAY: ("A1", "A2"),
    Ekran.ORTA: ("B1",),
    Ekran.ZOR: ("B2", "C1"),
}
SEVIYE_EKRANI = {s: ekran for ekran, seviyeler in EKRAN_SEVIYELERI.items() for s in seviyeler}

# Seviye başına havuz boyu: ekran başına 120 aday, testte 40'ı görünür.
HAVUZ_BOYU = {"A1": 60, "A2": 60, "B1": 120, "B2": 60, "C1": 60}

# wordfreq zipf bandı (alt, üst). 3 ≈ milyon sözcükte 1, 6 ≈ binde 1.
ZIPF_BANDI = {
    "A1": (4.0, 6.0),
    "A2": (4.0, 6.0),
    "B1": (3.5, 5.5),
    "B2": (3.0, 4.8),
    "C1": (3.0, 4.5),
}

TURLER = (PartOfSpeech.NOUN, PartOfSpeech.VERB, PartOfSpeech.ADJECTIVE, PartOfSpeech.ADVERB)
_YAZIM = re.compile(r"[a-z]{3,}")


@dataclass
class Aday:
    word_id: int
    text: str
    cefr: str
    ekran: int
    zipf: float | None = None


def zipf_olcer():
    """wordfreq kuruluysa text -> zipf fonksiyonu, değilse None."""
    try:
        from wordfreq import zipf_frequency
    except ImportError:
        return None
    return lambda text: zipf_frequency(text, "en")


def _sabit_sira(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _hassas_kelime_idleri(idler):
    """Hassas (müstehcen) anlamı olan kelimeler: veri hattının süzgeci."""
    from words.aile.anlam import hassas_mi   # ağır modül; yalnızca seçimde gerekli
    return {a.word_id for a in Meaning.objects.filter(word_id__in=idler)
            .only("word_id", "meaning_tr", "definition") if hassas_mi(a)}


def adaylar(zipf=None):
    """
    Bütün havuz, deterministik: [Aday, …] (ekran, seviye içinde sabit sırayla).
    zipf: text -> sıklık fonksiyonu (zipf_olcer()); None ise bant atlanır.
    """
    en_kolay = {}
    sira = {s: i for i, s in enumerate(("A1", "A2", "B1", "B2", "C1", "C2"))}
    for text, cefr in Word.objects.filter(isBaseWord=True, cefr__in=sira).values_list("text", "cefr"):
        eski = en_kolay.get(text)
        if eski is None or sira[cefr] < sira[eski]:
            en_kolay[text] = cefr

    ornekli = Exists(ExampleSentence.objects.filter(meaning__word=OuterRef("pk")))
    satirlar = (Word.objects.filter(isBaseWord=True, pos__in=TURLER, cefr__in=SEVIYE_EKRANI)
                .filter(ornekli).order_by("id").values_list("id", "text", "cefr"))

    secilen = {}   # text -> Aday (aynı yazımın ilk türü; id sırasıyla sabit)
    for wid, text, cefr in satirlar:
        if text in secilen or not _YAZIM.fullmatch(text) or en_kolay.get(text) != cefr:
            continue
        secilen[text] = Aday(wid, text, cefr, SEVIYE_EKRANI[cefr])

    hassas = _hassas_kelime_idleri([a.word_id for a in secilen.values()])
    seviyeye_gore = {s: [] for s in HAVUZ_BOYU}
    for aday in secilen.values():
        if aday.word_id in hassas:
            continue
        if zipf is not None:
            aday.zipf = round(zipf(aday.text), 2)
            alt, ust = ZIPF_BANDI[aday.cefr]
            if not (alt <= aday.zipf <= ust):
                continue
        seviyeye_gore[aday.cefr].append(aday)

    sonuc = []
    for seviye, liste in seviyeye_gore.items():
        liste.sort(key=lambda a: _sabit_sira(a.text))
        sonuc.extend(liste[:HAVUZ_BOYU[seviye]])
    sonuc.sort(key=lambda a: (a.ekran, sira[a.cefr], _sabit_sira(a.text)))
    return sonuc


def havuz(ekran):
    """Ekranın havuzu: {seviye: [word_id, …]}. Tablo boşsa anında seçilir."""
    satirlar = list(SeviyeKelimesi.objects.filter(ekran=ekran).values_list("cefr", "word_id"))
    if not satirlar:
        satirlar = [(a.cefr, a.word_id) for a in adaylar(zipf_olcer()) if a.ekran == ekran]
    sonuc = {}
    for cefr, wid in satirlar:
        sonuc.setdefault(cefr, []).append(wid)
    return sonuc


def ekran_kelimeleri(ekran, rng=None, adet=EKRAN_BOYU):
    """
    Bir testte gösterilecek kelimeler: [word_id, …] (en çok `adet`, karışık).
    İki seviyeli ekranda seviyelerden eşit pay; biri yetmezse diğerinden tamamlanır.
    """
    rng = rng or random.Random()
    gruplar = havuz(ekran)
    seviyeler = [s for s in EKRAN_SEVIYELERI[ekran] if gruplar.get(s)]
    if not seviyeler:
        return []
    secilen = []
    pay = adet // len(seviyeler)
    for seviye in seviyeler:
        liste = gruplar[seviye]
        secilen += rng.sample(liste, min(pay, len(liste)))
    alinan = set(secilen)
    kalan = [w for s in seviyeler for w in gruplar[s] if w not in alinan]
    secilen += rng.sample(kalan, min(adet - len(secilen), len(kalan)))
    rng.shuffle(secilen)
    return secilen
