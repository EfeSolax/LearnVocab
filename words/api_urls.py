"""
Sözlük ve Listem uçları (JSON ya da HTML parçası). LearnVocab/urls.py:
path("api/", include(...)). /api/ robots.txt ile taramaya kapalıdır.
"""

from django.urls import path

from . import sozluk_views as v
from . import views

urlpatterns = [
    path("sozluk/oneri/", v.sozluk_oneri, name="sozluk_oneri"),
    path("sozluk/kart/<int:word_id>/", v.kart_parcasi, name="sozluk_kart"),
    path("gunun-kelimesi/cevap/", v.gunun_kelimesi_cevap, name="gunun_kelimesi_cevap"),
    path("listem/oneri/", v.listem_oneri, name="listem_oneri"),
    path("listem/cikar/", v.listem_toplu_cikar, name="listem_toplu_cikar"),
    path("listem/geri-al/", v.listem_geri_yukle, name="listem_geri_yukle"),
    path("listem/ekle/<int:word_id>/", views.add_to_my_list, name="add_to_my_list"),
    path("listem/cikar/<int:word_id>/", views.remove_from_my_list, name="remove_from_my_list"),
    path("listem/ifade-ekle/<int:expression_id>/", views.add_expression_to_my_list,
         name="add_expression_to_my_list"),
    path("listem/ifade-cikar/<int:expression_id>/", views.remove_expression_from_my_list,
         name="remove_expression_from_my_list"),
]
