from django.urls import path

from . import views

urlpatterns = [
    path("durum/", views.durum, name="seri_durum"),
    path("saat-dilimi/", views.saat_dilimi, name="seri_saat_dilimi"),
]
