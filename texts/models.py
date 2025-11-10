from django.db import models
from users.models import User
from words.models import Word

# Create your models here.

class Text(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name = "texts",
    )

    content = models.TextField()
    response = models.TextField()
    score = models.IntegerField(default = 0)
    createdAt = models.DateTimeField(auto_now_add=True)
    words = models.ManyToManyField(Word, related_name="practiced_words_in_text")
    scores = models.CharField(max_length=40, default = "")

    def __str__(self):
        return f"{self.owner.username} - {self.createdAt.strftime('%Y-%m-%d')}"


