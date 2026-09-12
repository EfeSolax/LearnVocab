"""
Öğren-Geç'te sıradaki kelimeyi seçme mantığı.

İki mod var ve ikisi tamamen farklı havuzlardan besleniyor:

  mine -> kullanıcının kendi listesi. Amaç hızlı gözden geçirme.
  new  -> kullanıcının listesinde OLMAYAN temel kelimeler. Amaç keşif.

"new" modunda seviyeler eşit değil: hazırlık öğrencisinin asıl ihtiyacı
orta-üst seviyede olduğu için ağırlık B2'de. Dağılım LEVEL_WEIGHTS'te,
tek yerde.
"""

import random

from django.db.models import Q

from words.models import Word

from .models import WordEncounter


# Seviye seçilme ağırlıkları. Toplamı 100 olmak zorunda değil; oranlar önemli.
LEVEL_WEIGHTS = (
    ("B2", 40),
    ("B1", 25),
    ("C1", 25),
    ("A1", 5),
    ("A2", 5),
)


def _weighted_levels(rng=None):
    """
    Seviyeleri ağırlıklarına göre rastgele sıraya dizer.

    Tek bir seviye seçip "boşsa vazgeç" demek yerine bütün seviyeleri
    sıralıyoruz: seçilen seviyede gösterilecek kelime kalmadıysa sıradakine
    düşülüyor, yani havuz tükenene kadar kart gelmeye devam ediyor.
    """
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
    temel kelimeler. Kişisel/gizli kelimeler buraya hiç girmiyor: havuz
    yalnızca herkese açık temel kelimelerden oluşuyor.
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


def _random_from(qs, rng=None):
    """
    Queryset'ten rastgele bir kayıt. order_by("?") büyük tablolarda yavaş
    olduğu için önce id listesi alınıp aralarından seçiliyor.
    """
    ids = list(qs.values_list("id", flat=True)[:2000])
    if not ids:
        return None
    return Word.objects.filter(id=(rng or random).choice(ids)).first()


# Aynı kelimenin üst üste gelmemesi için rastgele seçim yapılan aday penceresi
OWN_CANDIDATE_WINDOW = 30


def pick_own_word(user, rng=None):
    """
    Kendi listesinden sıradaki kelime.

    Hiç görülmemiş kelimeler KESİN önceliklidir: bir tane bile varsa, daha
    önce görülmüş kelimeler hiç değerlendirmeye girmez. (Önceki sürümde iki
    grup tek bir listede sıralanıp ilk 30 aday arasından rastgele seçiliyordu;
    havuz küçükken bu, görülmüş bir kelimenin görülmemişin önüne geçmesine
    sebep oluyordu.)

    Görülmemiş kalmadıysa en uzun süredir görülmeyenlere düşülür. Her iki
    durumda da ilk OWN_CANDIDATE_WINDOW aday arasından rastgele seçiliyor ki
    aynı kelime arka arkaya gelmesin.
    """
    rng = rng or random
    gorulme = dict(
        WordEncounter.objects.filter(user=user).values_list("word_id", "last_seen_at")
    )
    adaylar = list(own_words_qs(user).only("id"))
    if not adaylar:
        return None

    gorulmemis = [w for w in adaylar if w.id not in gorulme]
    if gorulmemis:
        havuz = gorulmemis[:OWN_CANDIDATE_WINDOW]
    else:
        adaylar.sort(key=lambda w: gorulme[w.id])
        havuz = adaylar[:OWN_CANDIDATE_WINDOW]

    return Word.objects.filter(id=rng.choice(havuz).id).first()


def pick_new_word(user, rng=None):
    """Kur havuzundan, ağırlıklı kur sırasına göre sıradaki yeni kelime."""
    rng = rng or random
    for kur in _weighted_levels(rng):
        kelime = _random_from(new_words_qs(user, level=kur), rng)
        if kelime is not None:
            return kelime
    # Ağırlık tablosunda olmayan bir kur seviyesi kalmış olabilir
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
