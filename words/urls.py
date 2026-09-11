from django.urls import path
from . import views 


urlpatterns = [
    path("all-words/", views.allWords, name="all_words"),
    path("add-to-my-list/<int:word_id>/", views.add_to_my_list, name="add_to_my_list"),
    path("remove-from-my-list/<int:word_id>/", views.remove_from_my_list, name="remove_from_my_list"),
    path("add-selected-to-my-list/", views.addSelectedToMyList, name="add_selected_to_my_list"),
    path("word-detail/<int:id>/", views.word_detail, name="word_detail"),
    path("add-all-words/", views.addAllWords, name="add_all_words"),

    # Yapay zeka ile kelime ekleme
    path("ai-add/", views.aiAddWordsPage, name="ai_add_words_page"),
    path("ai-add/create/", views.aiAddWords, name="ai_add_words"),
    path("ai-add/progress/<str:job_id>/", views.aiAddWordsProgress, name="ai_add_words_progress"),
    path("ai-add/finish/<str:job_id>/", views.aiAddWordsFinish, name="ai_add_words_finish"),
]
