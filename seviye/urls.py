"""Seviye testi adresleri (rapor 7). LearnVocab/urls.py: path("seviye-testi/", include(...))."""

from django.urls import path

from . import views as v

urlpatterns = [
    path("", v.giris, name="seviye_testi"),
    path("basla/", v.basla, name="seviye_basla"),
    path("ekran/<int:ekran>/", v.ekran, name="seviye_ekran"),
    path("okuma/", v.okuma_sayfasi, name="seviye_okuma"),
    path("sonuc/", v.sonuc, name="seviye_sonuc"),
    path("geri-al/", v.geri_al, name="seviye_geri_al"),
    path("sec/", v.sec, name="seviye_sec"),
]
