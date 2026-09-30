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

    # Kütüphane (rapor 8, veri işi D5) için: metnin seviyesi ve kaynağı
    # ("Project Gutenberg", "Yapay zekâ ile üretildi" …). İkisi de boş olabilir;
    # kitaptan gelen ilk 40 metinde yok.
    cefr = models.CharField(max_length=15, blank=True, default="", verbose_name="seviye")
    source = models.CharField(max_length=200, blank=True, default="", verbose_name="kaynak")

    # Kalıcı adres (rapor 18.15): /okumalar/<slug>/. Başlıktan üretilir;
    # aynı başlık ikinci kez gelirse sonuna numara eklenir. Bir kez verilince
    # başlık değişse de değişmez (dizine girmiş adres kaybolmasın).
    slug = models.SlugField(max_length=220, unique=True, blank=True, null=True, editable=False)

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("number",)
        indexes = [models.Index(fields=["topic", "number"])]

    def __str__(self):
        return f"{self.number} {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._slug_uret()
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = set(kwargs["update_fields"]) | {"slug"}
        super().save(*args, **kwargs)

    def _slug_uret(self):
        from django.utils.text import slugify
        kok = slugify(self.title)[:200] or f"metin-{self.number}"
        # "metinlerim" kendi metinlerimin adres öneki; başlıkla çakışmasın.
        if kok == "metinlerim" or ReadingText.objects.filter(slug=kok).exclude(pk=self.pk).exists():
            kok = f"{kok}-{self.number}"
        return kok

    @property
    def paragraphs(self):
        """Boş olmayan paragraflar, metindeki sırayla."""
        return paragraflara_bol(self.body)

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


def paragraflara_bol(metin):
    """Boş satırla ayrılmış paragraflar; boş olanlar atılır."""
    return [p.strip() for p in (metin or "").split("\n\n") if p.strip()]


class UserTextQuerySet(models.QuerySet):
    def gorunen(self):
        """Silinmemiş (çöpte olmayan) metinler."""
        return self.filter(deleted_at__isnull=True)


class UserText(models.Model):
    """
    "Kendi metinlerim" (rapor 8): kullanıcının yüklediği PDF'ten çıkarılan
    ya da yapıştırdığı metin. YALNIZCA SAHİBİ görür; telif riski olmaması
    bunun üstüne kurulu.

    PDF dosyasının kendisi saklanmıyor, yalnızca çıkarılan metin: dosyayı
    tutmak gizlilik açısından gereksiz bir yük olurdu.

    Metnin gövdesi VERİTABANINDA DEĞİL, diskte sıkıştırılmış dosyada durur
    (rapor 18.24; readings/depo.py). `body` bir özelliktir: okurken dosya
    açılır, atanınca kaydederken dosyaya yazılır. Satır silinince dosya da
    silinir (readings/sinyaller.py).

    Silme onaysız ve "Geri al"lı (rapor 12.7): önce `deleted_at` dolar
    (yumuşak silme), metin çöp kutusuna gider. Çöpteki metinler bir hafta
    sonra kalıcı olarak temizlenir (bkz. views._copu_bosalt).
    """

    SOURCE_PDF = "pdf"
    SOURCE_PASTE = "paste"
    SOURCE_CHOICES = [(SOURCE_PDF, "PDF"), (SOURCE_PASTE, "Yapıştırma")]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reading_texts")
    title = models.CharField(max_length=200)
    # Gövdenin depodaki dosya adı: "okumalar/<kullanıcı>/<rastgele>.txt.z"
    dosya = models.CharField(max_length=80, blank=True, default="", editable=False)
    source_kind = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    word_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = UserTextQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [models.Index(fields=["owner", "deleted_at", "created_at"])]

    def __str__(self):
        return f"{self.owner_id} · {self.title}"

    # --- gövde: diskteki sıkıştırılmış dosya -----------------------------
    _body = None
    _body_degisti = False

    @property
    def body(self):
        if self._body is None:
            from . import depo
            self._body = depo.oku(self.dosya) if self.dosya else ""
        return self._body

    @body.setter
    def body(self, metin):
        self._body = metin or ""
        self._body_degisti = True

    def save(self, *args, **kwargs):
        if self._body_degisti:
            from . import depo
            if not self.dosya:
                self.dosya = depo.yeni_ad(self.owner_id)
                if kwargs.get("update_fields") is not None:
                    kwargs["update_fields"] = set(kwargs["update_fields"]) | {"dosya"}
            depo.yaz(self.dosya, self._body)
            self._body_degisti = False
        super().save(*args, **kwargs)

    @property
    def paragraphs(self):
        return paragraflara_bol(self.body)

    @property
    def reading_minutes(self):
        return max(1, round(self.word_count / WORDS_PER_MINUTE))
