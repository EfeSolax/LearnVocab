from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from . import views

urlpatterns = [
    path("profile/", views.showProfile, name = "user_profile"),
    path("profile/words/", views.showWordsView, name = "profile_words"),
    path("profile/myaccount/", views.showMyAccountView, name = "profile_myaccount"),
    path("profile/quizzes/", views.showQuizzesView, name = "profile_quizzes"),
    path("profile/texts/", views.showTextsView, name = "profile_texts"),
    path("profile/settings/", views.showSettingsView, name = "profile_settings"),

    # kelimelerle ilgili url'ler
    path("profile/words/delete-word/<int:id>", views.deleteWord, name = "delete_word"),
    path("profile/words/add-word/", views.addWord, name = "add_word"),
    path("profile/words/edit-word/<int:id>", views.editWord, name = "edit_word"),

    #profille ilgili url'ler
    path("profile/myaccount/save-mybio/", views.saveMyBio, name = "save_mybio"),

    #her bir kullanıcının hesabının gösterilmesi kısmı
    path("profile/show-user-profile/<int:user_id>", views.showUserProfile, name = "show_user_profile"),

    path("delete-all-words/", views.deleteAllWords, name = "delete_all_words"),
]