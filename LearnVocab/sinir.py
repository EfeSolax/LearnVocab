"""
İstek sınırı (8 Ekim): herkese açık uçlar ve giriş / kayıt denemeleri.

Sayaçlar ayrı bir önbellekte tutulur (settings.CACHES["sinir"], dosya tabanlı:
Passenger'ın bütün süreçleri aynı sayacı görür; ana önbelleği doldurmaz). Sabit pencere: ilk istekte pencere açılır, süresi
dolunca sayaç sıfırlanır. Önbellek bozulursa istek geri çevrilmez.
"""
import time
import uuid

from django.core.cache import caches
from django.http import JsonResponse


def _onbellek():
    return caches["sinir"]


def istemci(request):
    """İsteği yapanın adresi. Paylaşımlı sunucuda proxy başlığı güvenilmez; REMOTE_ADDR."""
    return request.META.get("REMOTE_ADDR") or "bilinmiyor"


def say(anahtar, sure):
    """
    Penceredeki istek sayısını bir artırır ve yeni değeri döner.

    Kayıt (sayı, pencerenin bitişi) olarak tutulur. Django'nun incr()'i dosya
    önbelleğinde süreyi varsayılana (1 saat) sıfırlıyordu; burada her yazışta
    kalan süre verilir, pencere uzamaz.
    """
    anahtar = f"sinir:{anahtar}"
    try:
        simdi = time.time()
        kayit = _onbellek().get(anahtar)
        if not isinstance(kayit, tuple) or kayit[1] <= simdi:
            _onbellek().set(anahtar, (1, simdi + sure), sure)
            return 1
        sayi, bitis = kayit[0] + 1, kayit[1]
        _onbellek().set(anahtar, (sayi, bitis), max(1, int(bitis - simdi) + 1))
        return sayi
    except Exception:
        return 0


def asildi(anahtar, sinir, sure):
    """Bu istekle birlikte sınır aşıldıysa True."""
    return say(anahtar, sure) > sinir


def oku(anahtar):
    try:
        kayit = _onbellek().get(f"sinir:{anahtar}")
    except Exception:
        return 0
    if not isinstance(kayit, tuple) or kayit[1] <= time.time():
        return 0
    return kayit[0]


def sifirla(anahtar):
    try:
        _onbellek().delete(f"sinir:{anahtar}")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Aynı anda en çok N iş (ağır işler: PDF okuma, metin değerlendirme)
# ---------------------------------------------------------------------------
# Her iş kendi "yer"ini zaman damgasıyla yazar; süresi geçen yer sayılmaz.
# Süreç iş ortasında ölürse (Passenger) yeri en geç `sure` saniye sonra boşalır.

def _yerler(anahtar):
    simdi = time.time()
    return {k: t for k, t in (_onbellek().get(anahtar) or {}).items() if t > simdi}


def yer_al(ad, en_cok, sure):
    """Boş yer varsa ayırır ve yer kimliğini döner; yoksa None. Önbellek bozuksa iş geri çevrilmez."""
    anahtar = f"yer:{ad}"
    try:
        yerler = _yerler(anahtar)
        if len(yerler) >= en_cok:
            return None
        kimlik = uuid.uuid4().hex
        yerler[kimlik] = time.time() + sure
        _onbellek().set(anahtar, yerler, sure)
        return kimlik
    except Exception:
        return "bilinmiyor"


def yer_birak(ad, kimlik):
    anahtar = f"yer:{ad}"
    try:
        yerler = _yerler(anahtar)
        if yerler.pop(kimlik, None) is not None:
            _onbellek().set(anahtar, yerler, max([int(t - time.time()) + 1 for t in yerler.values()] or [1]))
    except Exception:
        pass


def cok_istek(mesaj="Çok fazla istek. Biraz sonra tekrar dene.", sure=60):
    cevap = JsonResponse({"hata": mesaj}, status=429, json_dumps_params={"ensure_ascii": False})
    cevap["Retry-After"] = str(sure)
    return cevap
