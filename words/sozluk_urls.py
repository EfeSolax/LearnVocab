"""
Sözlük sayfaları (ürün raporu 4, 5 ve 18.15). Görünümler: words/sozluk_views.py
LearnVocab/urls.py: path("sozluk/", include(...)); hazır listeler "listeler/" altında.

    /sozluk/                   Keşfet | Listem (?sekme=listem); ?q= arama
    /sozluk/bank/              kelimenin kalıcı sayfası (bütün türleri)
    /sozluk/seviye/b1/         seviyeye göre göz at
    /sozluk/harf/a/            harfe göre göz at
    /sozluk/konu/hayvanlar/    konudaki kelimeler (rapor 18.39)

JSON / HTML parçası dönen uçlar words/api_urls.py'de (/api/ altında).
"""

from django.urls import path

from . import sozluk_views as v

urlpatterns = [
    path("", v.sozluk, name="sozluk"),
    path("seviye/<str:seviye>/", v.sozluk_seviye, name="sozluk_seviye"),
    path("harf/<str:harf>/", v.sozluk_harf, name="sozluk_harf"),
    path("konu/<slug:slug>/", v.konu_sayfasi, name="sozluk_konu"),
    # En sonda: tek parçalı her adres bir kelimedir.
    path("<slug:slug>/", v.sozluk_kelime, name="sozluk_kelime"),
]

liste_urlpatterns = [
    path("", v.hazir_listeler, name="hazir_listeler"),
    path("<slug:slug>/", v.hazir_liste_sayfasi, name="hazir_liste"),
    path("<slug:slug>/calis/", v.hazir_liste_calis, name="hazir_liste_calis"),
]
