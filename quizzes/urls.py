from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

urlpatterns = [
    # Yeni Quiz oluşturulurken bağlanacak link
    path("quizzes/attempt-quiz/", views.attemptQuiz, name = "attempt_quiz"),
    path("quizzes/quiz-page/", views.quizPage, name = "quiz_page"),

    path('quiz/<int:attempt_id>/<int:question_index>/', views.quizPage, name='quiz_page'),
    path('quiz/<int:attempt_id>/complete/', views.quizComplete, name='quiz_complete'),

    path("quizzes/quiz-review/", views.quizReviewList, name = "quiz_review"),
    path("quizzes/remove-quiz/<int:quiz_id>", views.removeQuiz, name = "remove_quiz")
]