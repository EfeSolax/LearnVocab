
from django.urls import path
from usersettings import views

# Diğer app'lerin altındaki urls.py 'leri dahil edebilmesi için include'u dahil ediyoruz.

# Bunlar profile_pics kısmını görüntülemek için gerekli import'lar


urlpatterns = [
    path("settings/save-settings/", views.saveSettings, name = "save_settings"),
    path("settings/remove-all-words/", views.removeAllWords, name = "remove_all_words"),
    path("settings/remove-all-comments/", views.removeAllComments, name = "remove_all_comments"),
    path("settings/delete-myaccount/", views.deleteMyAccount, name = "delete_myaccount"),

    path("settings/export-mywords/", views.exportMyWords, name = "export_mywords"),
    path("settings/export-mycomments/", views.exportMyComments, name = "export_mycomments"),
    path("settings/export-mytexts/", views.exportMyTexts, name = "export_mytexts"),
    path("settings/export-all/", views.exportAll, name = "export_all")
]