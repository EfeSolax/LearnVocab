from django.urls import path
from . import views 


urlpatterns = [
    path("all-words/", views.allWords, name="all_words"),
    path("add-to-my-list/<int:word_id>/", views.add_to_my_list, name="add_to_my_list"),
    path("remove-from-my-list/<int:word_id>/", views.remove_from_my_list, name="remove_from_my_list"),
    path("add-selected-to-my-list/", views.addSelectedToMyList, name="add_selected_to_my_list"),
    path("word-detail/<int:id>/", views.word_detail, name="word_detail"),
    path("add-all-words/", views.addAllWords, name="add_all_words"),
]
