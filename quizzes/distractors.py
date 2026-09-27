"""
Çeldirici üretimi.

ÇELDİRİCİ, SORUNUN KENDİSİNDEN ÖNEMLİDİR
----------------------------------------
Çoktan seçmeli bir soruda öğrencinin ne öğrendiğini belirleyen şey soru
kökü değil, yanlış şıklardır. `abundant` sorulurken şıklar "bol",
"masa", "koşmak", "mavi" ise soru hiçbir şey ölçmez: öğrenci kelimeyi
bilmeden de eleyerek bulur ve bulduğu için bildiğini sanır. Aynı soru
"bol / yeterli / aşırı / kıt" şıklarıyla sorulduğunda gerçekten ayrım
yapmak zorunda kalır.

Bu yüzden çeldirici seçimi üç kademeli:

  1. TUZAK ÇELDİRİCİ — kelimenin kendi karıştırılan çifti ya da yanlış
     dostu. Elde varsa en değerlisi budur: öğrencinin gerçekten yaptığı
     hatayı şık olarak koyar. `principle` sorulurken `principal`in
     anlamını şık yapmak, o ayrımı öğreten tek şeydir.
  2. YAKIN ÇELDİRİCİ — aynı alandan (psikoloji, ekonomi) ya da aynı
     türden ve aynı seviyeden kelimeler. Konu yakınlığı elemeyi zorlaştırır.
  3. UZAK ÇELDİRİCİ — havuz yetmezse rastgele. Sayı tutsun diye var,
     öğretici değeri düşük.

ÖRTÜŞEN ŞIK KONTROLÜ
--------------------
Yakın çeldirici seçmenin riski: iki şıkkın da doğru olması. "ders, konu"
sorulurken "konu, ders" şıkkını koyarsak soru bozulur ve öğrenci haklı
olarak yanlış yapar. Zenginleştirme hattında aynı problem için yazılmış
örtüşme kontrolünün (ortak kelime oranı) bir kopyası burada da var.
"""

import random
import re

from django.db.models import Q

from words.models import (
    CEFR_LEVELS, Meaning, RelationType, Word, WordRelation,
)


# Örtüşme sayılan ortak kelime oranı.
ORTUSME_ESIGI = 0.5

# Türkçe anlamlarda örtüşmeyi yapay olarak düşüren dolgu kelimeler.
DOLGU = {"ve", "bir", "ile", "veya", "da", "de", "olan", "olarak", "gibi",
         "için", "çok", "daha", "en", "bu", "şu", "o"}


def _kelimeler(metin: str) -> set:
    parcalar = {p for p in re.split(r"[^\wçğıöşüÇĞİÖŞÜ]+", (metin or "").lower()) if p}
    return parcalar - DOLGU


def ortusuyor_mu(a: str, b: str) -> bool:
    """İki anlam birbirinin yerine geçecek kadar örtüşüyor mu?"""
    ka, kb = _kelimeler(a), _kelimeler(b)
    if not ka or not kb:
        return False
    ortak = ka & kb
    return len(ortak) / min(len(ka), len(kb)) >= ORTUSME_ESIGI


def _farklilar(adaylar, dogru_metin, alan_adi, gereken):
    """
    Adaylardan, doğru cevapla ve birbiriyle örtüşmeyenleri seçer.

    Örtüşme kontrolü yalnızca doğru cevaba karşı değil, seçilen
    çeldiricilerin kendi aralarında da yapılıyor: iki eş anlamlı çeldirici
    soruyu bozmaz ama şık sayısını fiilen üçe düşürür.
    """
    secilen, metinler = [], [dogru_metin]
    for aday in adaylar:
        metin = getattr(aday, alan_adi, None) if not isinstance(aday, str) else aday
        if not metin:
            continue
        if any(ortusuyor_mu(metin, onceki) for onceki in metinler):
            continue
        secilen.append(aday)
        metinler.append(metin)
        if len(secilen) >= gereken:
            break
    return secilen


# ----------------------------------------------------------------------
# Tuzak çeldiriciler
# ----------------------------------------------------------------------

def trap_meanings(word, exclude_meaning_ids=()):
    """
    Kelimenin karıştırıldığı ve yanlış dost olduğu anlamlar.

    İkisi de öğrencinin GERÇEKTEN yaptığı hatayı temsil ettiği için en
    değerli çeldiricilerdir; şıkların başına konuyorlar.
    """
    sonuc = []

    baglar = (WordRelation.objects
              .filter(from_word=word, type=RelationType.CONFUSED_WITH)
              .select_related("to_word"))
    for bag in baglar:
        anlam = bag.to_word.meanings.exclude(id__in=exclude_meaning_ids).first()
        if anlam:
            sonuc.append(anlam)

    return sonuc


def trap_texts(word):
    """
    Yanlış dost kayıtlarından gelen "sanılan anlam" metinleri.

    Bunlar bir Meaning satırı değil, düz metin: `sympathetic` için
    "sempatik". Çoktan seçmelide şık olarak kullanılıyorlar çünkü
    öğrencinin kafasındaki yanlış cevap tam olarak budur.
    """
    metinler = []
    for yanlis_dost in word.false_friends.all():
        if yanlis_dost.assumed_meaning:
            metinler.append(yanlis_dost.assumed_meaning)
    return metinler


# ----------------------------------------------------------------------
# Anlam çeldiricileri (Türkçe şıklar)
# ----------------------------------------------------------------------

def meaning_distractors(meaning, count=3, rng=None):
    """
    Bir anlam sorusu için Türkçe çeldirici anlamlar.

    Dönen şey Meaning nesneleri ya da düz metinler olabilir; çağıran
    taraf `meaning_tr` alanına değil, `distractor_text()` yardımcısına
    bakmalı.
    """
    rng = rng or random
    word = meaning.word
    haric = {meaning.id}

    adaylar = []

    # 1. Tuzaklar
    adaylar.extend(trap_meanings(word, exclude_meaning_ids=haric))
    adaylar.extend(trap_texts(word))

    # 2. Aynı alandan — ama ÖNCE aynı türden.
    #
    # Tür filtresi olmadan şu çıkıyordu: "account (isim)" sorulurken
    # şıklardan biri "talep etmek" oluyordu. Bir isim sorusunda mastar
    # hâlindeki bir şık kendini ele verir; öğrenci kelimeyi bilmeden
    # eler ve soru ölçmeyi bırakır. Çeldirici ancak DOĞRU CEVAP KADAR
    # akla yatkın olduğunda çeldiricidir.
    alan_idleri = list(meaning.categories.values_list("id", flat=True))
    if alan_idleri:
        yakin = list(Meaning.objects
                     .filter(categories__id__in=alan_idleri, word__pos=word.pos)
                     .exclude(id__in=haric).exclude(word_id=word.id)
                     .select_related("word").distinct()[:40])
        rng.shuffle(yakin)
        adaylar.extend(yakin)

        farkli_tur = list(Meaning.objects
                          .filter(categories__id__in=alan_idleri)
                          .exclude(word__pos=word.pos)
                          .exclude(id__in=haric).exclude(word_id=word.id)
                          .select_related("word").distinct()[:20])
        rng.shuffle(farkli_tur)
        adaylar.extend(farkli_tur)

    # 3. Aynı tür + aynı seviye
    ayni = (Meaning.objects
            .filter(word__pos=word.pos, word__cefr=word.cefr)
            .exclude(id__in=haric)
            .exclude(word_id=word.id)
            .select_related("word")[:60])
    ayni = list(ayni)
    rng.shuffle(ayni)
    adaylar.extend(ayni)

    # 4. Havuz yetmezse herhangi bir anlam — yine aynı tür öncelikli
    if len(adaylar) < count * 3:
        genel = list(Meaning.objects
                     .filter(word__pos=word.pos)
                     .exclude(id__in=haric).exclude(word_id=word.id)
                     .select_related("word")[:120])
        rng.shuffle(genel)
        adaylar.extend(genel)
    if len(adaylar) < count * 2:
        genel = list(Meaning.objects
                     .exclude(id__in=haric)
                     .exclude(word_id=word.id)
                     .select_related("word")[:120])
        rng.shuffle(genel)
        adaylar.extend(genel)

    return _farklilar(adaylar, meaning.meaning_tr, "meaning_tr", count)


def distractor_text(aday) -> str:
    """Çeldirici nesnesinden gösterilecek metni çıkarır."""
    if isinstance(aday, str):
        return aday
    return getattr(aday, "meaning_tr", "") or ""


# ----------------------------------------------------------------------
# Kelime çeldiricileri (İngilizce şıklar)
# ----------------------------------------------------------------------

def word_distractors(word, count=3, rng=None, prefer_family=True):
    """
    Bir üretim sorusu için İngilizce çeldirici kelimeler.

    Aile üyeleri öncelikli: `analysis` sorulurken `analyse` ve
    `analytical` şık olarak konduğunda soru "kelimeyi biliyor musun"dan
    "hangi türevini kullanacağını biliyor musun"a dönüşür — ve asıl
    ölçülmesi gereken ikincisidir. Öğrenci kelimeyi tanır ama cümleye
    isim mi fiil mi gireceğini bilemez.
    """
    rng = rng or random
    secilen, gorulen = [], {word.text.lower()}

    def ekle(aday_kelime):
        metin = (aday_kelime.text or "").lower()
        if metin in gorulen:
            return
        gorulen.add(metin)
        secilen.append(aday_kelime)

    # 1. Karıştırılan çiftler — en iyi çeldirici
    baglar = (WordRelation.objects
              .filter(from_word=word, type=RelationType.CONFUSED_WITH)
              .select_related("to_word"))
    for bag in baglar:
        ekle(bag.to_word)

    # 2. Aile üyeleri
    if prefer_family and word.family_id:
        uyeler = list(word.family.words.exclude(id=word.id))
        rng.shuffle(uyeler)
        for uye in uyeler:
            ekle(uye)

    # 3. Aynı tür ve seviyeden kelimeler
    if len(secilen) < count:
        ayni = list(Word.objects
                    .filter(pos=word.pos, cefr=word.cefr)
                    .exclude(id=word.id)
                    .exclude(family_id=word.family_id)[:60])
        rng.shuffle(ayni)
        for aday in ayni:
            ekle(aday)
            if len(secilen) >= count * 2:
                break

    # 4. Havuz yetmezse aynı türden herhangi biri
    if len(secilen) < count:
        genel = list(Word.objects.filter(pos=word.pos)
                     .exclude(id=word.id)[:80])
        rng.shuffle(genel)
        for aday in genel:
            ekle(aday)
            if len(secilen) >= count * 2:
                break

    return secilen[:count]


def token_distractors(dogru_token, havuz, count=3, rng=None):
    """
    Edat / kısa kelime çeldiricileri.

    Kalıp sorularında şıklar edatlardır ve havuz sabittir; anlam
    yakınlığı aranamaz. Doğru olanın dışındakilerden rastgele seçiliyor.
    """
    rng = rng or random
    adaylar = [t for t in havuz if t.lower() != (dogru_token or "").lower()]
    rng.shuffle(adaylar)
    return adaylar[:count]


# Kalıp sorularında kullanılan edat havuzu. Sabit ve küçük bir küme
# olduğu için veritabanından üretmek yerine burada duruyor.
EDATLAR = ("on", "in", "at", "to", "for", "with", "from", "of", "about",
           "by", "into", "over", "under", "against", "between", "through",
           "upon", "towards", "without")

# Fiil kalıplarında kullanılan biçim havuzu.
FIIL_BICIMLERI = ("to do", "doing", "do", "to be done", "done", "that")
