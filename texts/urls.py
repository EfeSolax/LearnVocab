from django.urls import path

from . import views

# LearnVocab/urls.py bunları "yazma/" altına bağlıyor: /yazma/, /yazma/yaz/ …
# Menü `profile_texts`, `new_text_page`, `review_text` adlarına bağlı; adlar değişmemeli.

urlpatterns = [
    path("", views.yazmaSayfasi, name="profile_texts"),
    path("yaz/", views.newTextPage, name="new_text_page"),
    path("gonder/", views.createText, name="create_text"),
    path("gonder/ilerleme/<str:job_id>/", views.createTextProgress, name="create_text_progress"),
    path("gonder/bitis/<str:job_id>/", views.createTextFinish, name="create_text_finish"),
    path("<int:text_id>/", views.reviewText, name="review_text"),
    path("<int:text_id>/tekrar-dene/", views.retryText, name="retry_text"),
    path("<int:text_id>/sil/", views.removeText, name="remove_text"),
    path("<int:text_id>/geri-al/", views.restoreText, name="restore_text"),
    path("puanlama/", views.aboutGradingPage, name="about_grading_page"),
    path("diyalog/", views.diyalogSayfasi, name="diyalog_page"),
    path("diyalog/<int:diyalog_id>/cevap/", views.diyalogCevap, name="diyalog_cevap"),
]
