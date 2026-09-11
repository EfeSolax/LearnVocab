from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from . import views

# Diğer app'lerin altındaki urls.py 'leri dahil edebilmesi için include'u dahil ediyoruz.

# Bunlar profile_pics kısmını görüntülemek için gerekli import'lar

urlpatterns = [
    path("texts/new-text/", views.newTextPage, name = "new_text_page"),
    path("texts/create-text/", views.createText, name = "create_text"),
    path("texts/create-text/progress/<str:job_id>/", views.createTextProgress, name = "create_text_progress"),
    path("texts/create-text/finish/<str:job_id>/", views.createTextFinish, name = "create_text_finish"),
    path("texts/reviews-text/<int:text_id>", views.reviewText, name = "review_text"),
    path("texts/remove-text/<int:text_id>", views.removeText, name = "remove_text"),
    path("texts/about-grading/", views.aboutGradingPage, name = "about_grading_page")
]
