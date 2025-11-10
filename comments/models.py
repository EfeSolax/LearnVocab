# Django importları
from django.db import models

# Gerekli model importları
from users.models import User

# Comment Modeli
class Comment(models.Model):
    # Yorumun sahibi olan kullanıcı, ondelete CASCADE (otomatik silinir)
    owner = models.ForeignKey(
        User,
        related_name = "comments",
        on_delete=models.CASCADE,
    )

    # Yorumun içeriği ve ne zaman oluşturulduğu (tarihi otomatik alıyor)
    content = models.CharField(max_length=500)
    createdAt = models.DateTimeField(auto_now_add=True)

    # Hangi kullanıcılar tarafından beğenildi veya beğenilmedi M2M fieldları
    liked_by = models.ManyToManyField(
        User,
        symmetrical= False, 
        blank = True, 
        related_name="users_liked"
    )

    disliked_by = models.ManyToManyField(
        User, 
        symmetrical=False, 
        blank = True, 
        related_name="users_disliked"
    )

    # Yorumun str'e dönüştürme kısmı. Kullanıcı adı ve yorumun ilk 20 karakteri 
    def __str__(self):
        return f"{self.owner.username} - {self.content[:20]}"
    