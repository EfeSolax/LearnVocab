from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("profile/", views.showProfile, name="user_profile"),
    path("profile/words/", views.showWordsView, name="profile_words"),
    path("profile/myaccount/", views.showMyAccountView, name="profile_myaccount"),
    # Yazma sayfası texts uygulamasına taşındı (/texts/); eski adres oraya gider.
    path("profile/texts/", RedirectView.as_view(pattern_name="profile_texts", permanent=True)),
    path("profile/settings/", views.showSettingsView, name="profile_settings"),

    # kelimelerle ilgili url'ler
    path("profile/words/delete-word/<int:id>", views.deleteWord, name="delete_word"),
    path("profile/words/add-word/", views.addWord, name="add_word"),
    path("profile/words/edit-word/<int:id>", views.editWord, name="edit_word"),

    # profille ilgili url'ler
    path("profile/myaccount/save-mybio/", views.saveMyBio, name="save_mybio"),

    # her bir kullanıcının hesabının gösterilmesi kısmı
    path("profile/show-user-profile/<int:user_id>", views.showUserProfile, name="show_user_profile"),

    # toplu kelime işlemleri
    path("delete-all-words/", views.deleteAllWords, name="delete_all_words"),

    # YENİ: galeri tarzı manuel seçim ile toplu silme
    path("profile/words/delete-selected/", views.deleteSelectedWords, name="delete_selected_words"),

    # Kullanıcı kelime listeleri (klasörler)
    path("profile/words/lists/create/", views.createWordList, name="wordlist_create"),
    path("profile/words/lists/<int:list_id>/rename/", views.renameWordList, name="wordlist_rename"),
    path("profile/words/lists/<int:list_id>/delete/", views.deleteWordList, name="wordlist_delete"),
    path("profile/words/lists/<int:list_id>/add-words/", views.addWordsToList, name="wordlist_add_words"),
    path("profile/words/lists/<int:list_id>/remove-words/", views.removeWordsFromList, name="wordlist_remove_words"),
    path("profile/words/lists/move/", views.moveWordsBetweenLists, name="wordlist_move_words"),
]