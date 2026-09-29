"""
Learn & Pass'te sıradaki kelimenin seçimi.

Kuralın kendisi learnpass/tekrar.py'de (rapor 18.2); bu modül yalnızca
oturum türüne göre havuzu seçer:

  karma -> ~%70 tekrar / ~%30 yeni (oran ayarlardan; tekrar birikirse yeni azalır)
  mine  -> yalnızca tekrar adayları        new -> yalnızca yeni kelimeler
"""

import random

from words.models import Word

from . import tekrar
from .models import WordEncounter


def pick_word(user, mode, rng=None, haric=()):
    """Moda göre sıradaki kelime; havuz bittiyse None."""
    if mode == WordEncounter.MODE_MINE:
        return tekrar.siradaki_tekrar(user, rng=rng, haric=haric)
    return tekrar.yeni_kelime(user, rng=rng, haric=haric)


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
            .exclude(id__in=WordEncounter.objects.filter(user=user).values("word_id"))
            .distinct())


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
