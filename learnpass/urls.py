from django.urls import path

from . import views

urlpatterns = [
    path("learn/", views.learnPassPage, name="learn_pass_page"),
    # JSON uçları mod adresinden ÖNCE: "verdict" bir mod adı sanılmasın
    path("learn/api/verdict/", views.learnPassVerdict, name="learn_pass_verdict"),
    path("learn/api/undo/", views.learnPassUndo, name="learn_pass_undo"),
    path("learn/api/declare/", views.learnPassDeclare, name="learn_pass_declare"),
    path("learn/api/bilinmeyenler/", views.learnPassBilinmeyenler, name="learn_pass_bilinmeyenler"),
    path("learn/<str:mode>/", views.learnPassRun, name="learn_pass_run"),
    # Egzersizler sekmesi (exercises_page) egzersizler uygulamasında: /egzersizler/
]
