from django.db import models
from users.models import User

# Create your models here.

class Word(models.Model):
    # Kaç adet örnek cümle alanı olduğu. Alan sayısı değişirse SADECE burayı
    # güncellemek yeterli; property'ler ve formlar bu sabiti kullanıyor.
    EXAMPLE_SENTENCE_COUNT = 10

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
    # Örnek cümleler. Bir kelime tek bir cümleden öğrenilmez; aynı kelimeyi
    # farklı bağlamlarda görmek gerekiyor. Bu yüzden 10 cümleye kadar yer var.
    # Sadece ilki zorunlu, kalan 9'u isteğe bağlı.
    exampleSentence1 = models.CharField(max_length=400)
    exampleSentence2 = models.CharField(max_length=400, blank = True, null = True)
    exampleSentence3 = models.CharField(max_length=400, blank = True, null = True)
    exampleSentence4 = models.CharField(max_length=400, blank = True, null = True)
    exampleSentence5 = models.CharField(max_length=400, blank = True, null = True)
    exampleSentence6 = models.CharField(max_length=400, blank = True, null = True)
    exampleSentence7 = models.CharField(max_length=400, blank = True, null = True)
    exampleSentence8 = models.CharField(max_length=400, blank = True, null = True)
    exampleSentence9 = models.CharField(max_length=400, blank = True, null = True)
    exampleSentence10 = models.CharField(max_length=400, blank = True, null = True)
    visibility = models.CharField(max_length=10, choices = VISIBILITY_CHOICES, default = "private")###########

    # Eş anlamlı ve zıt anlamlı kelimeler (virgülle ayrılmış, isteğe bağlı)
    synonyms = models.CharField(max_length=500, blank=True, null=True)
    antonyms = models.CharField(max_length=500, blank=True, null=True)

    # Kelimenin doğal kullanım kalıpları (virgülle ayrılmış, isteğe bağlı)
    # Örn: "retain information, retain control, retain its shape"
    # Kelimeyi tek başına değil, birlikte kullanıldığı yapılarla öğrenmek için.
    collocations = models.CharField(max_length=500, blank=True, null=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    span = models.IntegerField(null=True, blank=True)

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

    @classmethod
    def example_sentence_field_names(cls):
        """Örnek cümle alanlarının adları: ['exampleSentence1', ...]."""
        return [f"exampleSentence{i}" for i in range(1, cls.EXAMPLE_SENTENCE_COUNT + 1)]

    @property
    def example_sentences(self):
        """
        Boş olmayan örnek cümleler, girildikleri sırayla.

        Alanlar zaten Word satırıyla birlikte yüklendiği için bu property
        ek sorgu yapmaz; sadece dolu olanları süzer.
        """
        sentences = []
        for field_name in self.example_sentence_field_names():
            sentence = getattr(self, field_name, None)
            if sentence and sentence.strip():
                sentences.append(sentence.strip())
        return sentences

    @property
    def has_extra_example_sentences(self):
        """1. cümlenin dışında dolu örnek cümle var mı? (Formda paneli açık başlatmak için)"""
        return len(self.example_sentences) > 1

    @property
    def collocations_list(self):
        """Virgülle ayrılmış collocation'ları temizlenmiş liste olarak döner."""
        if not self.collocations:
            return []
        return [c.strip() for c in self.collocations.split(',') if c.strip()]

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


class WordList(models.Model):
    """
    Kullanıcının kelime listesi (klasör). Her kullanıcı kendi WordList'lerini
    oluşturabilir ve bir Word birden fazla listede yer alabilir.
    Listede yer alan kelimelerin kullanıcının ana kelime listesinde
    (UserWordLink) da olması mantıklıdır; view tarafında bu garanti edilir.
    """
    COLOR_CHOICES = [
        ("indigo", "Indigo"),
        ("blue", "Mavi"),
        ("emerald", "Yeşil"),
        ("amber", "Sarı"),
        ("rose", "Kırmızı"),
        ("purple", "Mor"),
        ("teal", "Turkuaz"),
        ("slate", "Gri"),
    ]

    owner = models.ForeignKey(
        User,
        related_name="word_lists",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=80)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default="indigo")
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    words = models.ManyToManyField(
        Word,
        related_name="in_user_lists",
        blank=True,
    )

    class Meta:
        unique_together = ("owner", "name")
        ordering = ["createdAt"]

    def __str__(self):
        return f"{self.owner.username}/{self.name}"
