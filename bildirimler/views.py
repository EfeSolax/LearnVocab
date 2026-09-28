"""
PWA dosyaları (manifest, service worker) ve push abonelik uçları (rapor 10).
"""

import json

from django.contrib.staticfiles import finders
from django.http import Http404, HttpResponse, JsonResponse
from django.templatetags.static import static
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_safe, require_POST

from . import ayar
from .models import PushAboneligi

# Tema rengi: sitenin ana indigo tonu (Tailwind indigo-600).
TEMA_RENGI = "#4f46e5"
ARKA_PLAN = "#ffffff"


@require_safe
@cache_control(max_age=3600)
def manifest(request):
    veri = {
        "name": "LearnVocab",
        "short_name": "LearnVocab",
        "description": "İngilizce kelime öğrenme: sözlük, Learn & Pass, okuma ve yazma.",
        "lang": "tr",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "theme_color": TEMA_RENGI,
        "background_color": ARKA_PLAN,
        "icons": [
            {"src": static("pwa/ikon-192.png"), "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": static("pwa/ikon-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": static("pwa/ikon-maskable-512.png"), "sizes": "512x512", "type": "image/png",
             "purpose": "maskable"},
        ],
    }
    return HttpResponse(json.dumps(veri, ensure_ascii=False),
                        content_type="application/manifest+json; charset=utf-8")


_SW_ONBELLEK = None


def _sw_kaynagi():
    global _SW_ONBELLEK
    if _SW_ONBELLEK is None:
        yol = finders.find("pwa/sw.js")
        if not yol:
            raise Http404("sw.js bulunamadı")
        with open(yol, encoding="utf-8") as f:
            _SW_ONBELLEK = f.read()
    return _SW_ONBELLEK


@require_safe
def service_worker(request):
    """
    Service worker kökten (/sw.js) sunuluyor: kapsamı bütün site olsun diye.
    Tarayıcı her gezintide güncellemeyi kontrol edebilsin diye önbelleğe
    alınmıyor (eski sürüm takılı kalmasın).
    """
    yanit = HttpResponse(_sw_kaynagi(), content_type="application/javascript; charset=utf-8")
    yanit["Service-Worker-Allowed"] = "/"
    yanit["Cache-Control"] = "no-cache"
    return yanit


# ---------------------------------------------------------------- Abonelik

def _govde(request):
    try:
        veri = json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        return None
    return veri if isinstance(veri, dict) else None


def _gecerli_anahtar(deger, en_cok):
    return (isinstance(deger, str) and 0 < len(deger) <= en_cok
            and all(c.isalnum() or c in "-_=" for c in deger))


def _on_kontrol(request):
    if not ayar.acik():
        raise Http404
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth"}, status=403)
    return None


@require_POST
def abone_ol(request):
    hata = _on_kontrol(request)
    if hata:
        return hata
    veri = _govde(request)
    if veri is None:
        return JsonResponse({"error": "json"}, status=400)

    endpoint = veri.get("endpoint")
    anahtarlar = veri.get("keys") if isinstance(veri.get("keys"), dict) else {}
    p256dh, auth = anahtarlar.get("p256dh"), anahtarlar.get("auth")
    if not (isinstance(endpoint, str) and endpoint.startswith("https://")
            and len(endpoint) <= 500 and " " not in endpoint):
        return JsonResponse({"error": "endpoint"}, status=400)
    if not (_gecerli_anahtar(p256dh, 200) and _gecerli_anahtar(auth, 100)):
        return JsonResponse({"error": "keys"}, status=400)

    _, yeni = PushAboneligi.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            "user": request.user,
            "p256dh": p256dh,
            "auth": auth,
            "tarayici": request.META.get("HTTP_USER_AGENT", "")[:200],
        },
    )
    return JsonResponse({"ok": True, "yeni": yeni})


@require_POST
def abonelikten_cik(request):
    hata = _on_kontrol(request)
    if hata:
        return hata
    veri = _govde(request)
    if veri is None:
        return JsonResponse({"error": "json"}, status=400)
    endpoint = veri.get("endpoint")
    abonelikler = PushAboneligi.objects.filter(user=request.user)
    if endpoint:
        abonelikler = abonelikler.filter(endpoint=endpoint)
    elif not veri.get("hepsi"):
        return JsonResponse({"error": "endpoint"}, status=400)
    silinen, _ = abonelikler.delete()
    return JsonResponse({"ok": True, "silinen": silinen})
