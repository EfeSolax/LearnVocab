"""
LearnVocab - Ana URL yapılandırması.

Her uygulama (users, words, learnpass, ...) kendi urls.py dosyasında URL'lerini
tanımlar; bu dosya yalnızca onları include eder.
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.urls import include, path

from LearnVocab.anasayfa import ana_sayfa
from readings import api as readings_api
from words import views as word_views


def showAbout(request):
    return render(request, "pages/about.html")


urlpatterns = [
    path("admin/", admin.site.urls),
    # Ana Sayfa (rapor 3): LearnVocab/anasayfa.py
    path("", ana_sayfa, name="index"),
    path("about/", showAbout, name="about"),
    # Okumalar (rapor 8) ve kelime sorgulama API'si (okuma baloncuğu, Chrome eklentisi)
    path("readings/", include("readings.urls")),
    path("api/kelime/", readings_api.kelime, name="kelime_api"),
    # Sözlük (rapor 4). Adres paylaşılabilir: /sozluk/?q=aim
    path("sozluk/", include("words.sozluk_urls")),
    path("users/", include("users.urls")),
    path("words/", include("words.urls")),
    # Arkadaşlık özelliği şu an KAPALI.
    # Uygulamanın kendisi (friends/views.py, friends/urls.py, templates/pages/friends.html)
    # ve kullanıcı modelindeki friends / incomingRequests alanları duruyor;
    # yalnızca dışarıya açılan yol kapatıldı. Geri açmak için bu satırı yorumdan
    # çıkarmak ve navbar'daki bağlantıyı geri koymak yeterli.
    # path("friends/", include("friends.urls")),
    path("profile/", include("userprofile.urls")),
    path("exercises/", include("learnpass.urls")),
    # Egzersizler (rapor 6.2): Hızlı ve Tempolu Egzersiz
    path("egzersizler/", include("egzersizler.urls")),
    # Yorumlar özelliği şu an KAPALI (arkadaşlık gibi).
    # comments uygulaması, view'ları, şablonu ve Comment modeli duruyor;
    # veriler yalnızca admin panelinden görülebiliyor. Geri açmak için bu
    # satırı yorumdan çıkarmak ve navbar'a bağlantıyı geri koymak yeterli.
    # path("comments/", include("comments.urls")),
    path("texts/", include("texts.urls")),
    path("settings/", include("usersettings.urls")),
    # Seviye testi (rapor 7)
    path("seviye/", include("seviye.urls")),
    # Bildirimler ve PWA (rapor 10): /manifest.webmanifest, /sw.js, /bildirimler/...
    path("", include("bildirimler.urls")),
]

# Geliştirme ortamında media dosyalarını Django'nun servis etmesi için
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
