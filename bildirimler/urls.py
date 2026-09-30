from django.urls import path

from . import views

# Kökte durmak zorunda olanlar: service worker'ın kapsamı bütün site olsun
# diye /sw.js kökte. Dil öneki almazlar (LearnVocab/urls.py).
kok_urlpatterns = [
    path("manifest.webmanifest", views.manifest, name="pwa_manifest"),
    path("sw.js", views.service_worker, name="service_worker"),
]

# /api/bildirimler/…
urlpatterns = [
    path("abone-ol/", views.abone_ol, name="bildirim_abone_ol"),
    path("abonelikten-cik/", views.abonelikten_cik, name="bildirim_abonelikten_cik"),
]
