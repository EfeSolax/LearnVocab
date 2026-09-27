from django.urls import path

from . import views

urlpatterns = [
    # Çalışma akışı
    path("study/", views.studyHome, name="study_home"),
    path("study/start/", views.studyStart, name="study_start"),
    path("study/<int:session_id>/", views.studyRun, name="study_run"),
    path("study/<int:session_id>/finish/", views.studyFinish, name="study_finish"),

    # İlerleme ve analiz
    path("progress/", views.studyProgress, name="study_progress"),
    path("analysis/", views.wordAnalysis, name="word_analysis"),

    # Eski adreslerin karşılığı — şablonlarda ve yer imlerinde
    # kalmış bağlantılar kırılmasın diye çalışma sayfasına yönlendiriyor.
    path("attempt-quiz/", views.legacyRedirect, name="attempt_quiz"),
    path("quiz-review/", views.studyProgress, name="quiz_review"),
]
