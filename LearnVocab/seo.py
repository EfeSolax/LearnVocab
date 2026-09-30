"""
Arama motorları için ortak kurallar (rapor 18.15). Temel ilke: SEO bizi
cezalandırmamalı; şüphede sayfa KAPALI kalır.

1) Dizine açık sayfalar bir BEYAZ LİSTEDİR (DIZINE_ACIK, url adlarıyla).
   Listede olmayan her şey (hesap, çalışmalar, yazma, API, hata sayfaları)
   `noindex` alır: SeoMiddleware başlık ekler (X-Robots-Tag), şablon da
   <meta name="robots"> basar.
   Beyaz listedeki bir görünüm de sayfayı kapatabilir: bağlama
   `noindex=True` koyar (ör. bulunamayan arama, henüz açılmamış kelime).

2) canonical her zaman SITE_ADRESI'nden (https://www.learnvocab.com.tr)
   üretilir, istekten değil. Sorgu parametreleri atılır; yalnızca `sayfa`
   (sayfalama) kalır. Görünüm `canonical_yol` vererek değiştirebilir.

3) hreflang yalnızca birden çok dil YAYINDAYSA basılır (settings.LANGUAGES).
   Çevirisi olmayan dil açılmaz: aynı Türkçe içerik /en/ altında da durursa
   kopya içerik olur.

Şablon: base/layout.html `seo` bağlamını kullanır.
"""

from django.conf import settings
from django.urls import translate_url
from django.utils.translation import get_language

# Arama motorlarına açık sayfalar (url adı). Buraya eklenen her sayfanın
# gerçek, özgün içeriği olmalı.
DIZINE_ACIK = frozenset({
    "index",
    "about",
    "sozluk",                 # arama sonucu (?q=) ve Listem görünümde kapatılır
    "sozluk_kelime",          # kelime açılmamışsa görünümde kapatılır
    "sozluk_seviye",
    "sozluk_harf",
    "hazir_liste",
    "seviye_testi",           # yalnızca giriş ekranı; testin adımları kapalı
    "readings",
    "readings_library_text",
})

# canonical adreste kalmasına izin verilen tek sorgu parametresi.
SAYFA_PARAMETRESI = "sayfa"


def tam_adres(yol):
    """'/sozluk/bank/' -> 'https://www.learnvocab.com.tr/sozluk/bank/'"""
    return settings.SITE_ADRESI.rstrip("/") + yol


def dizine_acik_mi(request):
    eslesme = getattr(request, "resolver_match", None)
    return bool(eslesme and eslesme.url_name in DIZINE_ACIK)


def _sayfa_eki(request):
    sayfa = request.GET.get(SAYFA_PARAMETRESI, "")
    return f"?{SAYFA_PARAMETRESI}={sayfa}" if sayfa.isdigit() and int(sayfa) > 1 else ""


def _diger_diller(request):
    """[(dil kodu, tam adres)] — tek dil yayındaysa boş."""
    diller = [kod for kod, _ in settings.LANGUAGES]
    if len(diller) < 2:
        return []
    ek = _sayfa_eki(request)
    satirlar = [(kod, tam_adres(translate_url(request.path, kod)) + ek) for kod in diller]
    varsayilan = tam_adres(translate_url(request.path, settings.LANGUAGE_CODE)) + ek
    return satirlar + [("x-default", varsayilan)]


def seo(request):
    """Context processor: her şablonda `seo` hazır olsun."""
    acik = dizine_acik_mi(request)
    return {"seo": {
        "dizine_acik": acik,
        "canonical": tam_adres(request.path) + _sayfa_eki(request),
        "diller": _diger_diller(request) if acik else [],
        "site_adresi": settings.SITE_ADRESI.rstrip("/"),
        "dil": get_language(),
    }}


class SeoMiddleware:
    """Beyaz listede olmayan ya da hata dönen her cevaba X-Robots-Tag: noindex."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cevap = self.get_response(request)
        if (not dizine_acik_mi(request) or cevap.status_code >= 400) \
                and not cevap.has_header("X-Robots-Tag"):
            cevap["X-Robots-Tag"] = "noindex"
        return cevap
