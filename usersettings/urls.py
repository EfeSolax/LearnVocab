from django.urls import path

from usersettings import views

# LearnVocab/urls.py: path("ayarlar/", include(...))
urlpatterns = [
    path("kaydet/", views.saveSettings, name="save_settings"),
    path("kelimelerimi-sil/", views.removeAllWords, name="remove_all_words"),
    path("yorumlarimi-sil/", views.removeAllComments, name="remove_all_comments"),
    path("hesabimi-sil/", views.deleteMyAccount, name="delete_myaccount"),
    path("disa-aktar/kelimeler/", views.exportMyWords, name="export_mywords"),
    path("disa-aktar/yorumlar/", views.exportMyComments, name="export_mycomments"),
    path("disa-aktar/metinler/", views.exportMyTexts, name="export_mytexts"),
    path("disa-aktar/hepsi/", views.exportAll, name="export_all"),
]
