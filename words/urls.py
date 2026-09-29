from django.urls import path
from . import views


# Liste düğmelerinin uçları (kelime kartı, Listem, okuma baloncuğu).
# Sözlük sayfaları: words/sozluk_urls.py
urlpatterns = [
    path("add-to-my-list/<int:word_id>/", views.add_to_my_list, name="add_to_my_list"),
    path("remove-from-my-list/<int:word_id>/", views.remove_from_my_list, name="remove_from_my_list"),
    path("add-expression-to-my-list/<int:expression_id>/", views.add_expression_to_my_list,
         name="add_expression_to_my_list"),
    path("remove-expression-from-my-list/<int:expression_id>/",
         views.remove_expression_from_my_list, name="remove_expression_from_my_list"),
]
