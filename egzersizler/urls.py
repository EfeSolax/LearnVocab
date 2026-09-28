from django.urls import path

from . import views

urlpatterns = [
    # Ad "exercises_page" kalıyor: menü (navigation.py) ve Çalışmalar
    # sekmeleri (base/_exerciseTabs.html) bu ada bağlı.
    path("", views.exercises_page, name="exercises_page"),
    path("basla/", views.basla, name="egzersiz_basla"),
    path("<int:pk>/", views.oturum, name="egzersiz_oturum"),
    path("<int:pk>/cevap/", views.cevap, name="egzersiz_cevap"),
    path("<int:pk>/ilerle/", views.ilerle, name="egzersiz_ilerle"),
    path("<int:pk>/tekrar/", views.tekrar, name="egzersiz_tekrar"),
]
