from django.db import models
from users.models import User

# Create your models here.

class Word(models.Model):
    # Kelimeyi ekleyen kullanıcı
    owner = models.ForeignKey(User,
        blank=True,
        null = True,
        on_delete=models.CASCADE,
        related_name = "words",
    )

    # Final bir görünürlük listesi (seçenekler)
    VISIBILITY_CHOICES = [
        ('public', 'Herkese Açık'),
        ('friends', 'Arkadaşlara Açık'),
        ('private', 'Gizli'),
    ]

    # Ön Ekler (seçenekler)
    PREFIX_CHOICES = [
        ("dis","dis-"),
        ("un","un-"),
        ("im","im-"),
        ("in","in-"),
        ("ir","ir-"),
        ("il","il-")
    ]

    # Kelimenin ingilizcesi
    englishWord = models.CharField(max_length=100)
    explanation = models.CharField(max_length = 300, blank=True, null=True)
    note = models.CharField(max_length = 500, blank = True, null = True)
    prefix = models.CharField(max_length = 10, choices = PREFIX_CHOICES, blank = True, null = True)
    isVerb = models.BooleanField(default = False)
    meaningTr = models.CharField(max_length=200) 
    v2Form = models.CharField(max_length=100, blank = True, null = True)
    v3Form = models.CharField(max_length=100, blank = True, null = True)
    exampleSentence1 = models.CharField(max_length=400)
    exampleSentence2 = models.CharField(max_length=400, blank = True, null = True)
    exampleSentence3 = models.CharField(max_length=400, blank = True, null = True)
    visibility = models.CharField(max_length=10, choices = VISIBILITY_CHOICES, default = "private")###########
    createdAt = models.DateTimeField(auto_now_add=True)

    wordLevel = models.CharField(
        max_length=15,
        choices=[
            ('Belirtilmemiş','Belirtilmemiş'),
            ('101', '101'),
            ('201', '201'),
            ('301', '301'),
            ('401', '401'),
            ('501', '501'),
        ],
        default='Belirtilmemiş'
    )

    # Bu kelime herkesin görebileceği bir kur seviyesi kelimesi mi yoksa biri mi eklemiş.
    isBaseWord = models.BooleanField(default = False)

    # Kimler bu kelimeyi listesine eklemiş.
    saved_by = models.ManyToManyField(
        User, 
        related_name="saved_words", 
        blank=True,
        through='UserWordLink',
    )

    # Bir kelime objesi str'e nasıl dönüşecek:
    def __str__(self):
        return f"{self.englishWord}"


class UserWordLink(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wordLinks")
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="userLinks")

    dateAdded = models.DateTimeField(auto_now_add=True)

    correctCount = models.IntegerField(default=0)
    wrongCount = models.IntegerField(default=0)

    class Meta:
        # Bir kullanıcı bir kelimeyi listesine sadece bir kez ekleyebilmeli
        unique_together = ('user', 'word')

    def __str__(self):
        return f"{self.user.username} <-> {self.word.englishWord} (D:{self.correctCount} / Y:{self.wrongCount})"
    
    @property
    def totalAttempts(self):
        return self.correctCount + self.wrongCount
    
    # Belki yanlış oranını almak için bir 'property'
    # Not: totalAttempts = 0 ise hata vermemesi için kontrol
    @property
    def wrongRatio(self):
        total = self.totalAttempts
        if total == 0:
            return 0 # Henüz sorulmamış, 0 kabul edelim
        return (self.wrongCount / total) * 100 # Yüzdelik
    
    