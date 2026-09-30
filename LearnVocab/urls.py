"""
LearnVocab - Ana URL yapılandırması (adres şeması: rapor 18.15).

Her uygulama kendi urls.py dosyasında adreslerini tanımlar; bu dosya onları
bağlar. Adresler küçük harf, ASCII ve Türkçedir; sonda "/" olur.

İki grup var:
  1) Dil öneki ALMAYANLAR: admin, robots.txt, sitemap.xml, PWA dosyaları ve
     eski adreslerin 301 yönlendirmeleri.
  2) Dil öneki ALANLAR (i18n_patterns): bütün sayfalar ve /api/. Türkçe
     öneksizdir (/sozluk/bank/); başka bir dil yayına alınınca aynı sayfa
     /en/sozluk/bank/ adresinde de açılır (settings.LANGUAGES, rapor 18.22).

Arama motoru kuralları (hangi sayfa dizine açık, canonical): LearnVocab/seo.py
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path

from bildirimler.urls import kok_urlpatterns as pwa_urlpatterns
from learnpass.urls import api_urlpatterns as learnpass_api
from LearnVocab import eski_adresler, seo_views
from LearnVocab.anasayfa import ana_sayfa
from readings import api as readings_api
from words.sozluk_urls import liste_urlpatterns


def showAbout(request):
    return render(request, "pages/about.html")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("robots.txt", seo_views.robots_txt, name="robots_txt"),
    path("sitemap.xml", seo_views.sitemap_xml, name="sitemap_xml"),
    # PWA (rapor 10): /manifest.webmanifest, /sw.js
    *pwa_urlpatterns,
]

# /api/…: JSON ve HTML parçası dönen uçlar. robots.txt ile taramaya kapalı.
api_urlpatterns = [
    # Kelime sorgulama (okuma baloncuğu, Chrome eklentisi)
    path("kelime/", readings_api.kelime, name="kelime_api"),
    path("", include("words.api_urls")),
    path("learn-pass/", include(learnpass_api)),
    path("seri/", include("seri.urls")),
    path("bildirimler/", include("bildirimler.urls")),
]

urlpatterns += i18n_patterns(
    # Ana Sayfa (rapor 3)
    path("", ana_sayfa, name="index"),
    path("hakkinda/", showAbout, name="about"),
    # Sözlük (rapor 4): /sozluk/, /sozluk/bank/, /sozluk/seviye/b1/, /sozluk/harf/a/
    path("sozluk/", include("words.sozluk_urls")),
    path("listeler/", include(liste_urlpatterns)),
    # Çalışmalar (rapor 6): Learn & Pass ve Egzersizler
    path("calismalar/", include("learnpass.urls")),
    path("calismalar/egzersizler/", include("egzersizler.urls")),
    # Okumalar (rapor 8) ve Yazma (rapor 9)
    path("okumalar/", include("readings.urls")),
    path("yazma/", include("texts.urls")),
    # Seviye testi (rapor 7)
    path("seviye-testi/", include("seviye.urls")),
    # Hesap: /giris/, /kayit/, /cikis/, /sifremi-unuttum/, /profil/, /ayarlar/
    path("", include("users.urls")),
    path("profil/", include("userprofile.urls")),
    path("ayarlar/", include("usersettings.urls")),
    path("api/", include(api_urlpatterns)),
    # Arkadaşlık ve yorumlar KAPALI (uygulamaları, modelleri ve şablonları
    # duruyor; yalnızca dışarıya açılan yol yok). Geri açmak için:
    # path("arkadaslar/", include("friends.urls")),
    # path("yorumlar/", include("comments.urls")),
    prefix_default_language=False,
)

# Eski adresler (v1.0 ve geliştirme sırasındaki İngilizce adresler) yeni
# adreslere 301 ile yönlenir; Google'da dizine girmiş sayfalar kaybolmaz.
urlpatterns += eski_adresler.urlpatterns

# Geliştirme ortamında media dosyalarını Django'nun servis etmesi için
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
