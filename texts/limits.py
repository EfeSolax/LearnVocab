"""
Yazma sınırları — TEK KAYNAK (rapor 9.1 "Sınırlar").

1) Kullanıcı başına GÜNLÜK değerlendirme sınırı

       settings.TEXT_DAILY_LIMIT   (.env: TEXT_DAILY_LIMIT, varsayılan 3, 0 = sınırsız)

   Bugün (yerel saatle) gönderilen metinler sayılır. Henüz değerlendirilemeyen
   ve silinen metinler de sayılır: ilki sonradan yine Gemini'ye gidecek,
   ikincisi silip yeniden yazarak sınır aşılmasın diye (silme yumuşak, bkz.
   Text.silindi). Arka plandaki yeniden denemeler hak harcamaz.

   Eskiden sınır "iki metin arasında 1440 dakika" idi
   (TEXT_SUBMISSION_INTERVAL_MINUTES); artık kullanılmıyor.

2) Yoğunluk: site genelinde dakikalık çağrı sınırı

       settings.YAZMA_DAKIKADA_EN_COK   (varsayılan 4)

   Gemini'nin ücretsiz katmanı model başına dakikada ~5 istek kabul ediyor.
   Son 60 saniyede bu kadar değerlendirme istendiyse yenisi hiç gönderilmez;
   metin kaydedilir ve kullanıcıya "Biraz sonra tekrar dene" denir. Sayaç
   süreçler arasında paylaşılan cache'te (bkz. settings.CACHES).
"""

import time
from datetime import datetime, time as dtime

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

VARSAYILAN_GUNLUK = 3
VARSAYILAN_DAKIKALIK = 4
_CAGRI_ANAHTARI = "yazma:gemini-cagrilari"


def _tam_sayi(ad, varsayilan):
    try:
        return max(0, int(getattr(settings, ad, varsayilan)))
    except (TypeError, ValueError):
        return varsayilan


def gunluk_limit():
    """Günlük sınır; 0 ise sınır yok."""
    return _tam_sayi("TEXT_DAILY_LIMIT", VARSAYILAN_GUNLUK)


def _bugunun_basi():
    bugun = timezone.localdate()
    bas = datetime.combine(bugun, dtime.min)
    return timezone.make_aware(bas) if settings.USE_TZ else bas


def bugun_gonderilen(user):
    from texts.models import Text, YaziDurumu

    return (Text.objects
            .filter(owner=user, createdAt__gte=_bugunun_basi())
            .exclude(durum=YaziDurumu.ESKI)
            .count())


def kalan_hak(user):
    """Bugün kalan değerlendirme hakkı; sınır yoksa None."""
    sinir = gunluk_limit()
    if not sinir:
        return None
    return max(0, sinir - bugun_gonderilen(user))


def yazabilir_mi(user):
    kalan = kalan_hak(user)
    return kalan is None or kalan > 0


def sinir_mesaji():
    return "Bugünkü yazma hakkın doldu. Yarın yeni bir metinle devam edebilirsin."


# ---------------------------------------------------------------------------
# Yoğunluk
# ---------------------------------------------------------------------------

def dakikalik_sinir():
    return _tam_sayi("YAZMA_DAKIKADA_EN_COK", VARSAYILAN_DAKIKALIK)


def _son_cagrilar(simdi):
    return [t for t in (cache.get(_CAGRI_ANAHTARI) or []) if simdi - t < 60]


def yogun_mu():
    """Son 60 saniyede sınır kadar değerlendirme istendi mi?"""
    sinir = dakikalik_sinir()
    return bool(sinir) and len(_son_cagrilar(time.time())) >= sinir


def cagri_hakki_al():
    """
    Yoğun değilse bir çağrı hakkı ayırır ve True döner; yoğunsa False.
    (Süreçler arası tam kilit değil; ücretsiz katmanın sınırını aşmamak için yeterli.)
    """
    sinir = dakikalik_sinir()
    if not sinir:
        return True
    simdi = time.time()
    cagrilar = _son_cagrilar(simdi)
    if len(cagrilar) >= sinir:
        return False
    cagrilar.append(simdi)
    cache.set(_CAGRI_ANAHTARI, cagrilar, 120)
    return True


def yogunluk_sifirla():
    """Testler için."""
    cache.delete(_CAGRI_ANAHTARI)
