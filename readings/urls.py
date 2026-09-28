from django.urls import path

from . import views


urlpatterns = [
    path("", views.okumalar, name="readings"),
    path("kutuphane/<int:number>/", views.kutuphane_metni, name="readings_library_text"),
    path("metinlerim/ekle/", views.metin_ekle, name="readings_add"),
    path("metinlerim/<int:pk>/", views.kendi_metnim, name="readings_user_text"),
    path("metinlerim/<int:pk>/sil/", views.metnim_sil, name="readings_user_text_delete"),
    path("metinlerim/<int:pk>/geri-al/", views.metnim_geri_al, name="readings_user_text_restore"),
]
