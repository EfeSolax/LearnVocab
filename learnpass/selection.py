"""
Learn & Pass'te sıradaki kelimenin seçimi.

Kuralın kendisi learnpass/tekrar.py'de (rapor 18.2); bu modül yalnızca
oturum türüne göre havuzu seçer:

  karma -> ~%70 tekrar / ~%30 yeni (oran ayarlardan; tekrar birikirse yeni azalır)
  mine  -> yalnızca tekrar adayları        new -> yalnızca yeni kelimeler
  çalışma listesi seçildiyse (?liste=) -> bütün kartlar o listeden (pick_from_secim)
"""

import random

from django.utils import timezone

from words.models import Word

from . import tekrar
from .models import WordEncounter


def pick_word(user, mode, rng=None, haric=()):
    """Moda göre sıradaki kelime; havuz bittiyse None."""
    if mode == WordEncounter.MODE_MINE:
        return tekrar.siradaki_tekrar(user, rng=rng, haric=haric)
    return tekrar.yeni_kelime(user, rng=rng, haric=haric)


# ----------------------------------------------------------------------
# Çalışma listesi (Efe, 17 Ekim): "Şu kelimelerle tekrar yap" ekranında
# Listem yerine bir hazır liste (bölümüyle) seçilince turun bütün kartları
# o listeden gelir.
# ----------------------------------------------------------------------

def pick_from_secim(user, secim, rng=None, haric=()):
    """
    Çalışma listesinden sıradaki kelime: (kelime, kaynak) ya da (None, None).

    Sıra: hiç görmediği kelimeler (rastgele) -> tekrar zamanı gelenler ya da
    zorlandıkları (en eski görülen önce) -> geri kalanı (en eski görülen önce).
    Tur boyunca liste bitene kadar kart gelir; günlük yeni kelime sınırı
    burada uygulanmaz (kullanıcı listeyi kendisi seçti). Aile aralama burada da
    geçerli. kaynak: hiç görülmemişse "new", görülmüşse "mine".
    """
    rng = rng or random
    haric = list(haric)
    idler = list(secim.kelimeler().exclude(id__in=haric).values_list("id", flat=True)[:3000])
    if not idler:
        return None, None
    kayitlar = {e.word_id: e for e in WordEncounter.objects.filter(user=user, word_id__in=idler)}
    simdi = timezone.now()
    yeni = [i for i in idler if i not in kayitlar or kayitlar[i].times_seen == 0]
    rng.shuffle(yeni)

    def eski_once(i):
        son = kayitlar[i].last_seen_at
        return son.timestamp() if son else 0

    gorulen = [i for i in idler if i in kayitlar and kayitlar[i].times_seen > 0]
    aday = sorted((i for i in gorulen if tekrar.aday_mi(kayitlar[i], simdi)), key=eski_once)
    adaylar = set(aday)
    kalan = sorted((i for i in gorulen if i not in adaylar), key=eski_once)
    sira = tekrar.aileye_gore_sirala(yeni + aday + kalan, haric)
    kelime = Word.objects.filter(id=sira[0]).first()
    kaynak = WordEncounter.MODE_NEW if sira[0] not in kayitlar or kayitlar[sira[0]].times_seen == 0 \
        else WordEncounter.MODE_MINE
    return kelime, kaynak


def pick_secim_karma(user, secim, rng=None, haric=(), oran=None):
    """
    Çalışma listesi seçili turun sıradaki kartı: `oran` olasılıkla o listeden
    (pick_from_secim), kalanında Listem'in tekrar adaylarından. Biri boşsa
    öteki. oran verilmezse Ayarlar'daki yeni kelime oranı.
    """
    rng = rng or random
    if oran is None:
        oran = kullanici_yeni_orani(user)
    listeden = rng.random() < oran
    for kaynak in ((True, False) if listeden else (False, True)):
        if kaynak:
            kelime, tur = pick_from_secim(user, secim, rng=rng, haric=haric)
        else:
            kelime, tur = tekrar.siradaki_tekrar(user, rng=rng, haric=haric), WordEncounter.MODE_MINE
        if kelime is not None:
            return kelime, tur
    return None, None


# ----------------------------------------------------------------------
# Yeni / tekrar oranı (rapor 6.1, 18.2)
# ----------------------------------------------------------------------

VARSAYILAN_YENI_ORANI = 0.30   # ~%70 tekrar / %30 yeni
EN_AZ_YENI_ORANI = 0.10        # tekrar ne kadar birikirse biriksin keşif sürsün
# Bekleyen tekrar bu sayıyı aşınca yeni kelime oranı azalmaya başlar.
TEKRAR_BIRIKME_ESIGI = 40


def kullanici_yeni_orani(user):
    """
    Kullanıcının ayarladığı yeni kelime oranı (0-1).

    Ayarlar'daki kaydırma çubuğu (rapor 18.26): UserSettings.learnpass_yeni_orani,
    0–100 arası %10'luk adımlar. Ayar satırı yoksa (misafir) sabit varsayılan.
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
        bekleyen_tekrar = tekrar.bekleyen_tekrar_sayisi(user)
    if bekleyen_tekrar <= TEKRAR_BIRIKME_ESIGI:
        return temel
    azaltilmis = temel * TEKRAR_BIRIKME_ESIGI / bekleyen_tekrar
    return min(temel, max(EN_AZ_YENI_ORANI, azaltilmis))


def pick_mixed(user, rng=None, haric=(), oran=None):
    """
    Karma oturumun sıradaki kelimesi: (kelime, kaynak) ya da (None, None).
    `oran` olasılıkla yeni, kalanında tekrar. Seçilen havuz boşsa öteki
    denenir; biri bitti diye oturum bitmez.
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
    """Listem'deki "Zorlandıklarım" (rapor 18.2): son sonucu "bilemedi" olanlar."""
    return tekrar.zorlanilan_kelimeler(user)
