"""
Öğren-Geç'te sıradaki kelimeyi seçme mantığı.

İki mod var ve ikisi tamamen farklı havuzlardan besleniyor:

  mine -> kullanıcının kendi listesi. Amaç ZORLANDIĞINI ORTAYA ÇIKARMAK.
  new  -> kullanıcının listesinde OLMAYAN temel kelimeler. Amaç keşif.

SIRALAMA — "EN ÇOK YANILDIĞINDAN EN AZ YANILDIĞINA"
---------------------------------------------------
Kendi kelimeleri modunda kartlar artık rastgele ya da "en uzun süredir
görülmeyen" sırasıyla gelmiyor; ZORLANMA PUANINA göre, en zorlanılandan
en az zorlanılana doğru geliyor.

Sebebi Öğren-Geç'in ne işe yaradığıyla ilgili. Bu bölüm bir alıştırma
değil, bir ölçüm: "kullanıcı bu kelimeyi bildiğini düşünüyor mu?"
sorusunu soruyor. Bu soruyu iyi bildiği kelimelerde sormanın bilgi
değeri düşük — cevabı zaten biliyoruz. Değerli olan, zorlandığı
kelimelerde sormak: orada cevap tahmin edilemez ve çoğu zaman
şaşırtıcıdır ("biliyorum" deyip yanılmak).

ZORLANMA PUANI ÜÇ KAYNAKTAN GELİYOR
-----------------------------------
Tek bir kaynak yetmiyor çünkü üçü farklı şeyleri ölçüyor:

  Öğren-Geç       kullanıcı kendini nasıl değerlendiriyor (miss_ratio)
  Çalışma         gerçekte kaç kez unuttu (ReviewItem.lapses)
  Eski sayaçlar   quizlerde yanlış oranı (UserWordLink.wrongRatio)

En ağır olan birincisi değil ikincisi de değil — kullanıcının kendi
BEYANI. "Bu kadar gördüm ve hâlâ öğrenemedim" diyen bir kelime her
şeyin önüne geçiyor, çünkü bu bilgi başka hiçbir yerden gelmiyor.

HİÇ VERİSİ OLMAYAN KELİMELER
----------------------------
Puanı ORTA (0.5) alıyorlar. Sıfır verilseydi hiç dokunulmamış kelimeler
listenin en sonuna düşer ve kullanıcı onlarla hiç karşılaşmazdı; yüksek
verilseydi bu sefer gerçekten zorlandıkları geri plana düşerdi. Ortada
durmaları şunu sağlıyor: önce zorlandıkları, sonra hiç bakmadıkları,
en sonda iyi bildikleri.
"""

import random

from django.db.models import Q

from words.models import UserWordLink, Word

from .models import Declaration, WordEncounter


# Seviye seçilme ağırlıkları ("new" modu). Toplamı 100 olmak zorunda değil.
LEVEL_WEIGHTS = (
    ("B2", 40),
    ("B1", 25),
    ("C1", 25),
    ("A1", 5),
    ("A2", 5),
)

# Zorlanma puanının bileşen ağırlıkları.
AGIRLIK_BEYAN = 10.0        # "hâlâ öğrenemedim" — her şeyin önünde
AGIRLIK_OGREN_GEC = 3.0     # kullanıcının kendi değerlendirmesi
AGIRLIK_UNUTMA = 1.5        # Çalışma'da kaç kez unuttu
AGIRLIK_ESKI_ORAN = 1.0     # quiz sayaçlarındaki yanlış oranı

# Hiç verisi olmayan kelimenin puanı.
NOTR_PUAN = 0.5

# Unutma sayısının doyduğu nokta: 3 kez unutmakla 9 kez unutmak arasında
# sıralama açısından anlamlı fark yok, ikisi de "bu kelime sorunlu".
UNUTMA_DOYUM = 3


def _weighted_levels(rng=None):
    """Seviyeleri ağırlıklarına göre rastgele sıraya dizer."""
    rng = rng or random
    kalan = list(LEVEL_WEIGHTS)
    sira = []
    while kalan:
        toplam = sum(agirlik for _, agirlik in kalan)
        nokta = rng.uniform(0, toplam)
        birikim = 0
        for i, (seviye, agirlik) in enumerate(kalan):
            birikim += agirlik
            if nokta <= birikim:
                sira.append(seviye)
                kalan.pop(i)
                break
        else:  # kayan nokta artığı: sonuncuyu al
            sira.append(kalan[-1][0])
            kalan.pop()
    return sira


def _seen_word_ids(user):
    return WordEncounter.objects.filter(user=user).values_list("word_id", flat=True)


def _learned_word_ids(user):
    return WordEncounter.objects.filter(user=user, is_learned=True).values_list("word_id", flat=True)


def own_words_qs(user):
    """Kullanıcının listesindeki, 'öğrenildi' işareti olmayan kelimeler."""
    return (
        Word.objects.filter(Q(owner=user) | Q(saved_by=user))
        .exclude(id__in=_learned_word_ids(user))
        .distinct()
    )


def new_words_qs(user, level=None):
    """
    Kullanıcının listesinde olmayan ve daha önce Öğren-Geç'te görmediği
    temel kelimeler. Kişisel/gizli kelimeler buraya hiç girmiyor.
    """
    qs = (
        Word.objects.filter(isBaseWord=True)
        .exclude(owner=user)
        .exclude(saved_by=user)
        .exclude(id__in=_seen_word_ids(user))
    )
    if level:
        qs = qs.filter(cefr=level)
    return qs.distinct()


# ----------------------------------------------------------------------
# Zorlanma puanı
# ----------------------------------------------------------------------

def struggle_scores(user, word_ids=None):
    """
    {word_id: puan} — puan büyükse kullanıcı o kelimede daha çok zorlanıyor.

    Üç kaynak tek geçişte toplanıyor; kelime başına sorgu açılmıyor
    (havuz binlerce kelime olabilir).
    """
    puanlar = {}

    def ekle(word_id, miktar):
        puanlar[word_id] = puanlar.get(word_id, 0.0) + miktar

    # 1. Öğren-Geç'in kendi verisi + kullanıcının beyanı
    kayitlar = WordEncounter.objects.filter(user=user)
    if word_ids is not None:
        kayitlar = kayitlar.filter(word_id__in=word_ids)
    for kayit in kayitlar.only("word_id", "times_seen", "unknown_count",
                               "misjudged_count", "declaration"):
        ekle(kayit.word_id, AGIRLIK_OGREN_GEC * kayit.miss_ratio)
        if kayit.declaration == Declaration.STUCK:
            ekle(kayit.word_id, AGIRLIK_BEYAN)

    # 2. Çalışma'daki unutmalar
    try:
        from quizzes.models import ReviewItem

        kartlar = ReviewItem.objects.filter(user=user, lapses__gt=0)
        if word_ids is not None:
            kartlar = kartlar.filter(word_id__in=word_ids)
        # Aynı kelimenin birden çok kartı olabilir; en çok unutulan boyut
        # kelimenin puanını belirliyor (toplamak, çok kartlı kelimeleri
        # yapay olarak öne çıkarırdı).
        en_cok = {}
        for word_id, lapses in kartlar.values_list("word_id", "lapses"):
            en_cok[word_id] = max(en_cok.get(word_id, 0), lapses)
        for word_id, lapses in en_cok.items():
            ekle(word_id, AGIRLIK_UNUTMA * min(lapses / UNUTMA_DOYUM, 1.0))
    except Exception:  # pragma: no cover — quizzes yoksa Öğren-Geç yine çalışsın
        pass

    # 3. Eski quiz sayaçları
    baglar = UserWordLink.objects.filter(user=user)
    if word_ids is not None:
        baglar = baglar.filter(word_id__in=word_ids)
    for bag in baglar.only("word_id", "correctCount", "wrongCount"):
        if bag.totalAttempts:
            ekle(bag.word_id, AGIRLIK_ESKI_ORAN * (bag.wrongRatio / 100.0))

    return puanlar


# Puanı en yüksek kaç aday arasından rastgele seçileceği.
#
# Kesin sıra (hep en yüksek puanlıyı göstermek) kullanıcıyı aynı kelimeye
# kilitler: kart her açtığında aynı kelime gelir, karar verir, kelime yine
# en tepede kalır. Tepeden rastgele seçmek hem en zorlandıklarında kalmayı
# hem de tekrarı önlemeyi sağlıyor.
ADAY_PENCERESI = 12


def pick_own_word(user, rng=None):
    """
    Kendi listesinden sıradaki kelime — en çok zorlanılandan başlayarak.

    Eski davranış: hiç görülmemişler mutlak öncelikli, sonra en uzun
    süredir görülmeyenler. O sıralama Öğren-Geç'i bir "liste gezme"
    aracına çeviriyordu; artık bölüm zorlanmayı ortaya çıkarmak için var.
    """
    rng = rng or random
    adaylar = list(own_words_qs(user).only("id"))
    if not adaylar:
        return None

    puanlar = struggle_scores(user, [k.id for k in adaylar])
    # Hiç verisi olmayan kelime ortada durur (bkz. dosya başı).
    sirali = sorted(adaylar,
                    key=lambda k: puanlar.get(k.id, NOTR_PUAN),
                    reverse=True)
    havuz = sirali[:ADAY_PENCERESI]
    return Word.objects.filter(id=rng.choice(havuz).id).first()


def _random_from(qs, rng=None):
    """Queryset'ten rastgele bir kayıt."""
    ids = list(qs.values_list("id", flat=True)[:2000])
    if not ids:
        return None
    return Word.objects.filter(id=(rng or random).choice(ids)).first()


def pick_new_word(user, rng=None):
    """
    Kur havuzundan, ağırlıklı kur sırasına göre sıradaki yeni kelime.

    Burada zorlanma sıralaması YOK ve olamaz: kullanıcı bu kelimeleri
    hiç görmedi, zorlandığına dair veri yok. Bu mod keşif için.
    """
    rng = rng or random
    for kur in _weighted_levels(rng):
        kelime = _random_from(new_words_qs(user, level=kur), rng)
        if kelime is not None:
            return kelime
    return _random_from(new_words_qs(user), rng)


def pick_word(user, mode, rng=None):
    """Moda göre sıradaki kelime; havuz bittiyse None."""
    if mode == WordEncounter.MODE_MINE:
        return pick_own_word(user, rng)
    return pick_new_word(user, rng)


def remaining_count(user, mode):
    """Modda gösterilecek kaç kelime kaldığı (bitiş ekranı için)."""
    if mode == WordEncounter.MODE_MINE:
        return own_words_qs(user).count()
    return new_words_qs(user).count()


def stuck_word_ids(user):
    """
    Kullanıcının "hâlâ öğrenemedim" dediği kelimeler.

    Çalışma bölümü bunu sıralamada kullanıyor (quizzes/session.py):
    aynı gün sırası gelmiş kartlar arasında bunlar öne alınıyor.
    """
    return set(
        WordEncounter.objects
        .filter(user=user, declaration=Declaration.STUCK)
        .values_list("word_id", flat=True)
    )
