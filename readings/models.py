"""
Okuma metinleri.

Metinlerin kaynağı proje kökündeki reading-texts/ klasöründeki düz metin
dosyaları. Veritabanı bir kopya tutuyor; kaynak dosyalar değiştiğinde
`python manage.py import_readings` tekrar çalıştırılıp güncelleniyor.
Metnin kimliği kitaptaki sıra numarası (number) — dosya adı ya da başlık
değişse bile kayıt aynı kalıyor.
"""

from django.db import models

from users.models import User


# Konu anahtarı -> (görünen ad, renk sınıfı kökü)
# Renkler liste sayfasında konuları birbirinden ayırmak için.
TOPICS = (
    ("hukuk", "Hukuk", "indigo"),
    ("psikoloji", "Psikoloji", "violet"),
    ("sosyoloji", "Sosyoloji", "emerald"),
    ("antropoloji", "Antropoloji", "amber"),
    ("egitim", "Eğitim", "rose"),
)

TOPIC_CHOICES = [(anahtar, ad) for anahtar, ad, _ in TOPICS]
TOPIC_LABELS = {anahtar: ad for anahtar, ad, _ in TOPICS}
TOPIC_COLORS = {anahtar: renk for anahtar, _, renk in TOPICS}

# Ortalama okuma hızı (kelime/dakika). Yetişkin bir okur ana dilinde ~250,
# yabancı dilde belirgin biçimde daha yavaş okur; hazırlık seviyesi için
# 150 gerçekçi bir tahmin.
WORDS_PER_MINUTE = 150


class ReadingText(models.Model):
    """Tek bir okuma parçası."""

    # Kitaptaki sıra numarası. Kaydın kalıcı kimliği bu.
    number = models.PositiveIntegerField(unique=True)

    topic = models.CharField(max_length=20, choices=TOPIC_CHOICES)
    title = models.CharField(max_length=200)

    # Paragraflar boş satırla ayrılmış olarak tutuluyor; ayrı bir tablo
    # açmaya değecek bir ihtiyaç yok, sıraları da böyle korunuyor.
    body = models.TextField()

    word_count = models.PositiveIntegerField(default=0)

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("number",)
        indexes = [models.Index(fields=["topic", "number"])]

    def __str__(self):
        return f"{self.number} {self.title}"

    @property
    def paragraphs(self):
        """Boş olmayan paragraflar, metindeki sırayla."""
        return [p.strip() for p in self.body.split("\n\n") if p.strip()]

    @property
    def topic_label(self):
        return TOPIC_LABELS.get(self.topic, self.topic)

    @property
    def topic_color(self):
        return TOPIC_COLORS.get(self.topic, "slate")

    @property
    def reading_minutes(self):
        """Kaba okuma süresi; en az 1 dakika."""
        return max(1, round(self.word_count / WORDS_PER_MINUTE))


class ReadingProgress(models.Model):
    """
    Kullanıcının bir metni okuduğu bilgisi.

    Satırın varlığı "okundu" demek; okunmamış metinler için kayıt tutulmuyor.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reading_progress")
    text = models.ForeignKey(ReadingText, on_delete=models.CASCADE, related_name="progress")
    read_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "text")
        indexes = [models.Index(fields=["user", "read_at"])]

    def __str__(self):
        return f"{self.user.username} · {self.text}"
