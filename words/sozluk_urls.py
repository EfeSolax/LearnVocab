"""
Sözlük adresleri (ürün raporu 4 ve 5). LearnVocab/urls.py: path("sozluk/", include(...)).
Görünümler: words/sozluk_views.py
"""

from django.urls import path

from . import sozluk_views as v

urlpatterns = [
    # Paylaşılabilir arama adresi: /sozluk/?q=aim
    path("", v.sozluk, name="sozluk"),
    path("oneri/", v.sozluk_oneri, name="sozluk_oneri"),
    path("kart/<int:word_id>/", v.kart_parcasi, name="sozluk_kart"),
    path("liste/<slug:slug>/", v.hazir_liste_sayfasi, name="hazir_liste"),
    path("liste/<slug:slug>/calis/", v.hazir_liste_calis, name="hazir_liste_calis"),
    path("listem/oneri/", v.listem_oneri, name="listem_oneri"),
    path("listem/cikar/", v.listem_toplu_cikar, name="listem_toplu_cikar"),
    path("listem/geri-al/", v.listem_geri_yukle, name="listem_geri_yukle"),
]
