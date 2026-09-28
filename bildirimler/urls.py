from django.urls import path

from . import views

# LearnVocab/urls.py bunları köke bağlıyor: service worker'ın kapsamı bütün
# site olsun diye /sw.js kökte duruyor.
urlpatterns = [
    path("manifest.webmanifest", views.manifest, name="pwa_manifest"),
    path("sw.js", views.service_worker, name="service_worker"),
    path("bildirimler/abone-ol/", views.abone_ol, name="bildirim_abone_ol"),
    path("bildirimler/abonelikten-cik/", views.abonelikten_cik, name="bildirim_abonelikten_cik"),
]
