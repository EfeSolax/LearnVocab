"""
İstek sınırı (8 Ekim): herkese açık uçlar ve giriş / kayıt denemeleri.

Sayaçlar ayrı bir önbellekte tutulur (settings.CACHES["sinir"], dosya tabanlı:
Passenger'ın bütün süreçleri aynı sayacı görür; ana önbelleği doldurmaz). Sabit pencere: ilk istekte pencere açılır, süresi
dolunca sayaç sıfırlanır. Önbellek bozulursa istek geri çevrilmez.
"""
from django.core.cache import caches
from django.http import JsonResponse


def _onbellek():
    return caches["sinir"]


def istemci(request):
    """İsteği yapanın adresi. Paylaşımlı sunucuda proxy başlığı güvenilmez; REMOTE_ADDR."""
    return request.META.get("REMOTE_ADDR") or "bilinmiyor"


def say(anahtar, sure):
    """Penceredeki istek sayısını bir artırır ve yeni değeri döner."""
    anahtar = f"sinir:{anahtar}"
    try:
        if _onbellek().add(anahtar, 1, sure):
            return 1
        return _onbellek().incr(anahtar)
    except ValueError:            # anahtar arada süresi dolup silindi
        _onbellek().set(anahtar, 1, sure)
        return 1
    except Exception:
        return 0


def asildi(anahtar, sinir, sure):
    """Bu istekle birlikte sınır aşıldıysa True."""
    return say(anahtar, sure) > sinir


def oku(anahtar):
    try:
        return _onbellek().get(f"sinir:{anahtar}", 0)
    except Exception:
        return 0


def sifirla(anahtar):
    try:
        _onbellek().delete(f"sinir:{anahtar}")
    except Exception:
        pass


def cok_istek(mesaj="Çok fazla istek. Biraz sonra tekrar dene.", sure=60):
    cevap = JsonResponse({"hata": mesaj}, status=429, json_dumps_params={"ensure_ascii": False})
    cevap["Retry-After"] = str(sure)
    return cevap
