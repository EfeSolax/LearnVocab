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

ZORLANMA PUANI İKİ KAYNAKTAN GELİYOR
------------------------------------
Tek bir kaynak yetmiyor çünkü ikisi farklı şeyleri ölçüyor:

  Öğren-Geç       kullanıcı kendini nasıl değerlendiriyor (miss_ratio)
  Eski sayaçlar   eski egzersizlerdeki yanlış oranı (UserWordLink.wrongRatio)

(Eski "Çalışma" bölümünün unutma sayaçları da bir kaynaktı; o bölüm
quizzes uygulamasıyla birlikte kaldırıldı.)

En ağır olan ikisi de değil — kullanıcının kendi BEYANI. "Bu kadar gördüm ve hâlâ öğrenemedim" diyen bir kelime her
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
AGIRLIK_ESKI_ORAN = 1.0     # eski egzersiz sayaçlarındaki yanlış oranı

# Hiç verisi olmayan kelimenin puanı.
NOTR_PUAN = 0.5


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

    İki kaynak tek geçişte toplanıyor; kelime başına sorgu açılmıyor
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

    # 2. Eski egzersiz sayaçları
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


def pick_own_word(user, rng=None, haric=()):
    """
    Kendi listesinden sıradaki kelime — en çok zorlanılandan başlayarak.

    Eski davranış: hiç görülmemişler mutlak öncelikli, sonra en uzun
    süredir görülmeyenler. O sıralama Öğren-Geç'i bir "liste gezme"
    aracına çeviriyordu; artık bölüm zorlanmayı ortaya çıkarmak için var.
    """
    rng = rng or random
    adaylar = list(own_words_qs(user).exclude(id__in=list(haric)).only("id"))
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


def pick_new_word(user, rng=None, haric=()):
    """
    Sıradaki yeni kelime.

    Kullanıcı Sözlük'te bir hazır liste için "Bu listeyle çalış" dediyse
    kelimeler o listeden gelir (bkz. yeni_kelime_havuzu); demediyse ya da
    listede görmediği kelime kalmadıysa kur havuzundan, ağırlıklı kur
    sırasına göre.

    Burada zorlanma sıralaması YOK ve olamaz: kullanıcı bu kelimeleri
    hiç görmedi, zorlandığına dair veri yok. Bu mod keşif için.
    """
    rng = rng or random
    haric = list(haric)

    liste_havuzu = yeni_kelime_havuzu(user)
    if liste_havuzu is not None:
        kelime = _random_from(liste_havuzu.exclude(id__in=haric), rng)
        if kelime is not None:
            return kelime

    for kur in _weighted_levels(rng):
        kelime = _random_from(new_words_qs(user, level=kur).exclude(id__in=haric), rng)
        if kelime is not None:
            return kelime
    return _random_from(new_words_qs(user).exclude(id__in=haric), rng)


def pick_word(user, mode, rng=None, haric=()):
    """Moda göre sıradaki kelime; havuz bittiyse None."""
    if mode == WordEncounter.MODE_MINE:
        return pick_own_word(user, rng, haric)
    return pick_new_word(user, rng, haric)


def remaining_count(user, mode):
    """Modda gösterilecek kaç kelime kaldığı (bitiş ekranı için)."""
    if mode == WordEncounter.MODE_MINE:
        return own_words_qs(user).count()
    return new_words_qs(user).count()


def stuck_word_ids(user):
    """
    Kullanıcının "hâlâ öğrenemedim" dediği kelimeler.

    Egzersizler (yeniden yazılacak) sıralamada kullanabilsin diye duruyor.
    """
    return set(
        WordEncounter.objects
        .filter(user=user, declaration=Declaration.STUCK)
        .values_list("word_id", flat=True)
    )


# ----------------------------------------------------------------------
# Yeni kelime kaynağı: hazır liste bağlantı noktası (rapor 4.1)
# ----------------------------------------------------------------------

def yeni_kelime_havuzu(user):
    """
    "Bu listeyle çalış" seçilmişse yeni kelimelerin geleceği Word queryset'i,
    seçilmemişse None (o zaman kur havuzu kullanılır).

    Bağlantı noktası: Sözlük'ün hazır liste kodu `words.hazir_liste`
    modülünde `aktif_liste(user)` fonksiyonunu sağlar. Beklenen sözleşme:
      - seçili liste yoksa None,
      - varsa listenin kelimelerini veren bir Word queryset'i ya da
        `kelimeler` özniteliği/yöntemi Word queryset'i dönen bir nesne.
    Modül henüz yoksa (ImportError) ya da hiçbir şey seçilmemişse seviye
    tabanlı kaynağa düşülür. Dönen havuzdan kullanıcının listesindekiler,
    kendi (kişisel) kelimeleri ve L&P'de daha önce gördükleri çıkarılır.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return None
    try:
        from words.hazir_liste import aktif_liste
    except ImportError:
        return None

    secili = aktif_liste(user)
    if secili is None:
        return None
    kelimeler = secili
    if not hasattr(kelimeler, "filter"):
        kelimeler = getattr(secili, "kelimeler", None)
        if callable(kelimeler):
            kelimeler = kelimeler()
        if kelimeler is not None and hasattr(kelimeler, "all") and not hasattr(kelimeler, "exclude"):
            kelimeler = kelimeler.all()  # ilişki yöneticisi
    if kelimeler is None or not hasattr(kelimeler, "exclude"):
        return None
    return (kelimeler
            .exclude(owner=user)
            .exclude(saved_by=user)
            .exclude(id__in=_seen_word_ids(user))
            .distinct())


# ----------------------------------------------------------------------
# Yeni / tekrar oranı (rapor 6.1)
# ----------------------------------------------------------------------
#
# "Tekrar" şimdilik kullanıcının listesindeki, öğrenildi işareti olmayan
# kelimeler (own_words_qs, zorlanma sırasıyla). Ne zaman tekrar gelecekleri
# (tekrar algoritması) Bölüm 16'da Efe ile konuşulacak; burada yalnızca
# iki havuz arasındaki ORAN uygulanıyor.

VARSAYILAN_YENI_ORANI = 0.30   # ~%70 tekrar / %30 yeni
EN_AZ_YENI_ORANI = 0.10        # tekrar ne kadar birikirse biriksin keşif sürsün
# Bekleyen tekrar bu sayıyı aşınca yeni kelime oranı azalmaya başlar.
TEKRAR_BIRIKME_ESIGI = 40


def kullanici_yeni_orani(user):
    """
    Kullanıcının ayarladığı yeni kelime oranı (0-1).

    Ayarlar sayfası henüz tasarlanmadı (Bölüm 16); UserSettings'te oran
    alanı yok. Alan eklendiğinde (`learnpass_yeni_orani`, 0-1 ya da 0-100)
    buradan okunur; yoksa sabit varsayılan.
    """
    ayarlar = None
    try:
        ayarlar = user.mysettings
    except Exception:  # ayar satırı yok ya da misafir
        pass
    deger = getattr(ayarlar, "learnpass_yeni_orani", None)
    if deger is None:
        return VARSAYILAN_YENI_ORANI
    deger = float(deger)
    if deger > 1:
        deger /= 100.0
    return min(max(deger, 0.0), 1.0)


def yeni_orani(user, bekleyen_tekrar=None):
    """
    Bu oturumda kartların ne kadarı yeni kelime olsun (0-1).

    Tekrar birikirse (listede bekleyen kelime eşiği aşarsa) yeni oranı
    eşik/bekleyen ölçüsünde azalır, EN_AZ_YENI_ORANI'nin altına inmez
    (kullanıcı kendisi daha düşük seçtiyse onun seçimi geçerli).
    """
    temel = kullanici_yeni_orani(user)
    if bekleyen_tekrar is None:
        bekleyen_tekrar = own_words_qs(user).count()
    if bekleyen_tekrar <= TEKRAR_BIRIKME_ESIGI:
        return temel
    azaltilmis = temel * TEKRAR_BIRIKME_ESIGI / bekleyen_tekrar
    return min(temel, max(EN_AZ_YENI_ORANI, azaltilmis))


def pick_mixed(user, rng=None, haric=(), oran=None):
    """
    Karma oturumun sıradaki kelimesi: (kelime, kaynak) ya da (None, None).

    `oran` olasılıkla yeni, kalanında tekrar (kendi listesi) havuzundan.
    Seçilen havuz boşsa öteki denenir; biri bitti diye oturum bitmez.
    """
    rng = rng or random
    if oran is None:
        oran = yeni_orani(user)
    sira = [WordEncounter.MODE_NEW, WordEncounter.MODE_MINE]
    if rng.random() >= oran:
        sira.reverse()
    for kaynak in sira:
        kelime = pick_word(user, kaynak, rng, haric)
        if kelime is not None:
            return kelime, kaynak
    return None, None


# ----------------------------------------------------------------------
# Misafir (girişsiz) ziyaretçi (rapor 2.3)
# ----------------------------------------------------------------------

MISAFIR_SEVIYELERI = ("A1", "A2", "B1", "B2", "C1")
MISAFIR_VARSAYILAN_SEVIYE = "B1"


def misafir_kelimeleri(seviye, adet, rng=None):
    """
    Girişsiz ziyaretçi için seçilen seviyeden rastgele `adet` temel kelime.
    Hiçbir şey okunmaz ya da yazılmaz; seviye boşsa diğer seviyelerle
    tamamlanır.
    """
    rng = rng or random
    if seviye not in MISAFIR_SEVIYELERI:
        seviye = MISAFIR_VARSAYILAN_SEVIYE
    temel = Word.objects.filter(isBaseWord=True)
    idler = list(temel.filter(cefr=seviye).values_list("id", flat=True)[:3000])
    secilen = rng.sample(idler, min(adet, len(idler)))
    if len(secilen) < adet:
        kalan = list(temel.exclude(id__in=secilen).values_list("id", flat=True)[:3000])
        secilen += rng.sample(kalan, min(adet - len(secilen), len(kalan)))
    kelimeler = {k.id: k for k in Word.objects.filter(id__in=secilen)
                 .prefetch_related("meanings__examples")}
    return [kelimeler[i] for i in secilen if i in kelimeler]


# ----------------------------------------------------------------------
# Başka bölümlerin kullandığı sorgular
# ----------------------------------------------------------------------

def bekleyen_bilinmeyenler(user):
    """
    "Bilmiyorum" denmiş, listede olmayan ve henüz sorulmamış kelimeler:
    "Geçen sefer bilmediğin N kelime" kartının içeriği.
    """
    kayitlar = WordEncounter.objects.filter(user=user, listeye_sorulacak=True)
    return (Word.objects
            .filter(id__in=kayitlar.values("word_id"))
            .exclude(saved_by=user))


def zorlanilan_kelimeler(user):
    """
    Kullanıcının L&P'de "bilmiyorum" dediği (ya da bildiğini sanıp yanıldığı,
    ya da "hâlâ öğrenemedim" dediği) kelimeler — Listem'deki "Zorlandıklarım"
    filtresinin L&P yarısı (rapor 5). "Artık öğrendim" beyanı olanlar
    çıkarılır. Egzersiz yanlışları ayrıca eklenmeli
    (UserWordLink.wrongCount > 0).
    """
    kayitlar = (WordEncounter.objects.filter(user=user)
                .filter(Q(unknown_count__gt=0) | Q(misjudged_count__gt=0)
                        | Q(declaration=Declaration.STUCK))
                .exclude(declaration=Declaration.MASTERED))
    return Word.objects.filter(id__in=kayitlar.values("word_id"))
