"""
Seviye testi ekran kelimelerinin seçimi (veri işi D8, rapor 7, 18.27).

Ekranlar ve yuvalar (her testte havuzdan rastgele):
    1. ekran  A1 20 + A2 20
    2. ekran  B1 20 + B2 20
    3. ekran  C1 30 + C2 10
C2 yuvası: seviyesi resmî kaynakla doğrulanmış C2 kelimesi yetmediği sürece
(şu an Oxford'da C2 yok) EN ZOR C1 kelimeleriyle doldurulur: önce seviyesi
Oxford'la doğrulanmış C1'ler, sıklığı en düşükten başlayarak (Zipf >= 2,8;
daha altı tanınmaz teknik kelimeler), nadir tür olmayanlar.

Kural (deterministik; aynı veritabanı = aynı havuz):
  1. Aday: ortak sözlükteki (isBaseWord) isim/fiil/sıfat/zarf, tek sözcük,
     yalnızca küçük harf a–z ve en az 3 harf, en az bir örnek cümlesi var,
     nadir tür değil. UYDURMA KELİME YOK.
  2. Kelimenin seviyesi = aynı yazımın bütün türleri arasındaki EN KOLAY
     seviye (dog fiil C1 zor ekrana düşmez).
  3. Hassas/müstehcen anlamı olan kelime alınmaz (rapor 12.2).
  4. Seviyesi resmî kaynakla doğrulanmış (cefr_kaynak != learnvocab)
     kelimeler tercih edilir; yetmezse bizim etiketlerimizle tamamlanır.
  5. Sıklık bandı (Word.siklik, Zipf): çok nadir kelime tanınmaz, çok sık
     kelime hiçbir şey ölçmez.
  6. Bandı geçenler yazımın sha1 özetine göre sıralanır (keyfî ama sabit)
     ve ilk HAVUZ_BOYU kadarı havuza girer.

`seviye_kelimeleri_sec` komutu bu seçimi SeviyeKelimesi tablosuna yazar.
Tablo boşsa `ekran_kelimeleri` seçimi aynı kuralla anında yapar.
"""

import hashlib
import random
import re
from dataclasses import dataclass

from django.db.models import Exists, OuterRef

from words.models import ExampleSentence, Meaning, PartOfSpeech, Word

from .models import Ekran, SeviyeKelimesi

EKRAN_BOYU = 40

# Ekran -> yuvalar ve testte gösterilecek adet (rapor 18.27).
EKRAN_PAYLARI = {
    Ekran.KOLAY: {"A1": 20, "A2": 20},
    Ekran.ORTA: {"B1": 20, "B2": 20},
    Ekran.ZOR: {"C1": 30, "C2": 10},
}
EKRAN_SEVIYELERI = {e: tuple(p) for e, p in EKRAN_PAYLARI.items()}
SEVIYE_EKRANI = {s: ekran for ekran, seviyeler in EKRAN_SEVIYELERI.items() for s in seviyeler}

# Yuva başına havuz boyu: testte gösterilenin 3 katı.
HAVUZ_BOYU = {s: 3 * adet for p in EKRAN_PAYLARI.values() for s, adet in p.items()}

# Sıklık bandı (alt, üst), Zipf. 3 ≈ milyon sözcükte 1, 6 ≈ binde 1.
ZIPF_BANDI = {
    "A1": (4.0, 6.0),
    "A2": (4.0, 6.0),
    "B1": (3.5, 5.5),
    "B2": (3.0, 4.8),
    "C1": (3.0, 4.5),
    "C2": (2.3, 4.0),
}
# C2 yedeği olan "en zor C1"ler için sıklık tabanı. Google'a açıklık sınırı
# 2,3 ama o bantta "concentrator, interfacial" gibi tanınmaz teknik kelimeler
# var; ileri düzey ama tanınabilir kelimeler için 2,8.
EN_DUSUK_SIKLIK = 2.8

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
    Bütün havuz, deterministik: [Aday, …] (ekran, yuva içinde sabit sırayla).
    zipf: eski imza için; sıklık artık Word.siklik alanından okunur
    (manage.py siklik_hesapla). Alan boşsa bant atlanır.
    """
    sira = {s: i for i, s in enumerate(("A1", "A2", "B1", "B2", "C1", "C2"))}
    en_kolay = {}
    for text, cefr in Word.objects.filter(isBaseWord=True, cefr__in=sira).values_list("text", "cefr"):
        eski = en_kolay.get(text)
        if eski is None or sira[cefr] < sira[eski]:
            en_kolay[text] = cefr

    ornekli = Exists(ExampleSentence.objects.filter(meaning__word=OuterRef("pk")))
    satirlar = (Word.objects.filter(isBaseWord=True, pos__in=TURLER, cefr__in=sira, nadir_tur=False)
                .filter(ornekli).order_by("id")
                .values_list("id", "text", "cefr", "siklik", "cefr_kaynak"))

    secilen = {}   # text -> (Aday, resmi_mi)
    for wid, text, cefr, siklik, kaynak in satirlar:
        if text in secilen or not _YAZIM.fullmatch(text) or en_kolay.get(text) != cefr:
            continue
        aday = Aday(wid, text, cefr, SEVIYE_EKRANI[cefr], round(siklik, 2) if siklik is not None else None)
        secilen[text] = (aday, kaynak != "learnvocab")

    hassas = _hassas_kelime_idleri([a.word_id for a, _ in secilen.values()])
    temiz = [(a, resmi) for a, resmi in secilen.values() if a.word_id not in hassas]

    def bantta(aday, seviye):
        if aday.zipf is None:
            return True
        alt, ust = ZIPF_BANDI[seviye]
        return alt <= aday.zipf <= ust

    def sec(liste, adet):
        """Önce resmî kaynaklılar, sonra bizimkiler; her grupta sabit sıra."""
        liste.sort(key=lambda x: (not x[1], _sabit_sira(x[0].text)))
        return [a for a, _ in liste[:adet]]

    # C2 yuvası ÖNCE: resmî C2 yetmiyorsa en zor C1'ler (önce Oxford'lu,
    # sıklığı en düşükten; >= EN_DUSUK_SIKLIK). C1 havuzu kalanlardan seçilir.
    c2 = [(a, r) for a, r in temiz if a.cefr == "C2" and r and bantta(a, "C2")]
    c2_secilen = sec(c2, HAVUZ_BOYU["C2"])
    if len(c2_secilen) < HAVUZ_BOYU["C2"]:
        zor_c1 = sorted(((a, r) for a, r in temiz if a.cefr == "C1"
                         and a.zipf is not None and a.zipf >= EN_DUSUK_SIKLIK),
                        key=lambda x: (not x[1], x[0].zipf, _sabit_sira(x[0].text)))
        for a, _ in zor_c1[:HAVUZ_BOYU["C2"] - len(c2_secilen)]:
            c2_secilen.append(Aday(a.word_id, a.text, "C2", Ekran.ZOR, a.zipf))
    alinan = {a.word_id for a in c2_secilen}

    sonuc = []
    for seviye in ("A1", "A2", "B1", "B2", "C1"):
        uygun = [(a, r) for a, r in temiz if a.cefr == seviye and a.word_id not in alinan
                 and bantta(a, seviye)]
        sonuc.extend(sec(uygun, HAVUZ_BOYU[seviye]))
    sonuc.extend(c2_secilen)

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
    Yuvalardan EKRAN_PAYLARI kadar; bir yuva yetmezse diğerinden tamamlanır.
    """
    rng = rng or random.Random()
    gruplar = havuz(ekran)
    paylar = EKRAN_PAYLARI[ekran]
    if not any(gruplar.get(s) for s in paylar):
        return []
    toplam = sum(paylar.values())
    if adet != toplam:   # daha az/çok isteniyorsa paylar orantılı
        paylar = {s: round(p * adet / toplam) for s, p in paylar.items()}
    secilen = []
    for seviye, pay in paylar.items():
        liste = gruplar.get(seviye, [])
        secilen += rng.sample(liste, min(pay, len(liste)))
    alinan = set(secilen)
    kalan = [w for s in paylar for w in gruplar.get(s, []) if w not in alinan]
    secilen += rng.sample(kalan, max(0, min(adet - len(secilen), len(kalan))))
    rng.shuffle(secilen)
    return secilen
