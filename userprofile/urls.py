from django.urls import path

from . import views

# LearnVocab/urls.py: path("profil/", include(...))
urlpatterns = [
    path("", views.showProfile, name="user_profile"),
    path("<int:user_id>/", views.showUserProfile, name="show_user_profile"),
]
