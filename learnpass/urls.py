"""
Çalışmalar (rapor 6). LearnVocab/urls.py: path("calismalar/", include(...)).
Egzersizler "calismalar/egzersizler/" altında (egzersizler/urls.py).
JSON uçları api_urlpatterns: /api/learn-pass/…
"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.learnPassPage, name="learn_pass_page"),
    path("learn-pass/sec/", views.learnPassSec, name="learn_pass_sec"),
    path("learn-pass/<str:mode>/", views.learnPassRun, name="learn_pass_run"),
]

api_urlpatterns = [
    path("verdict/", views.learnPassVerdict, name="learn_pass_verdict"),
    path("undo/", views.learnPassUndo, name="learn_pass_undo"),
    path("bilinmeyenler/", views.learnPassBilinmeyenler, name="learn_pass_bilinmeyenler"),
    path("liste/", views.learnPassListe, name="learn_pass_liste"),
]
