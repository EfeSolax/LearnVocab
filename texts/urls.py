from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from . import views

# Diğer app'lerin altındaki urls.py 'leri dahil edebilmesi için include'u dahil ediyoruz.

# Bunlar profile_pics kısmını görüntülemek için gerekli import'lar

urlpatterns = [
    path("texts/new-text/", views.newTextPage, name = "new_text_page"),
    path("texts/create-text/", views.createText, name = "create_text"),
    path("texts/reviews-text/<int:text_id>", views.reviewText, name = "review_text"),
    path("texts/remove-text/<int:text_id>", views.removeText, name = "remove_text"),
    path("texts/about-grading/", views.aboutGradingPage, name = "about_grading_page")
]
