from django.urls import path
from comments import views

urlpatterns = [
    # Temel yorumlar sayfasını döndüren url
    path("", views.showComments, name = "show_comments_page"),

    # Yorum silme, like atma, dislike atma fonksiyonları ve url'leri
    path("remove-comment/<int:id>", views.removeComment, name = "remove_comment"),
    path("like-comment/<int:id>", views.likeComment, name = "like_comment"),
    path("dislike-comment/<int:id>", views.dislikeComment, name = "dislike_comment"),
]