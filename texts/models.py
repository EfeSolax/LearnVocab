"""
Yazma bölümü (ürün raporu 9).

  Text           -> serbest yazma: kullanıcının metni ve Gemini'nin geri bildirimi
  YazmaAyari     -> kullanıcının yazma tercihi (şimdilik yalnızca sertlik)
  Diyalog        -> "Diyalogda doğru kelime" havuzu (D6). Önceden üretilir,
                    denetlenir ve `diyalog_yukle` komutuyla yüklenir; canlı
                    üretilmez.
  DiyalogCevabi  -> kullanıcının bir diyaloğa verdiği cevap
"""

from django.db import models

from users.models import User
from words.models import Meaning, Register, Sentiment, Word


class YaziDurumu(models.TextChoices):
    # Gemini henüz cevap vermedi (kota, yoğunluk). Metin kaybolmaz; listede
    # sarı etiketle görünür ve `yazilari_yeniden_dene` komutu yeniden dener.
    BEKLIYOR = "bekliyor", "Henüz değerlendirilmedi"
    TAMAM = "tamam", "Değerlendirildi"
    # Model metni değerlendirilebilir bulmadı (İngilizce değil, anlamsız…).
    UYGUN_DEGIL = "uygun_degil", "Değerlendirilemedi"
    # Eski sistemin (10 kriter, 100 puan) kayıtları. Silinmez, olduğu gibi
    # "eski değerlendirme" diye gösterilir.
    ESKI = "eski", "Eski değerlendirme"


class Sertlik(models.TextChoices):
    """Geri bildirimin sertliği (rapor 9.1). Yalnızca hata listesini etkiler."""
    NAZIK = "nazik", "Nazik"
    NORMAL = "normal", "Normal"
    TITIZ = "titiz", "Titiz"


class Text(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name = "texts",
    )

    content = models.TextField()
    # Değerlendirmenin düz metin hâli (dışa aktarma için). Eski kayıtlarda
    # modelin uzun cevabı burada duruyor.
    response = models.TextField(blank=True)
    # ESKİ: 100 üzerinden puan ve 10 kriterin puanları. Yeni metinlerde 0 / "".
    score = models.IntegerField(default = 0)
    createdAt = models.DateTimeField(auto_now_add=True)
    # "Kullanmayı dene" diye önerilen kelimeler (eski kayıtlarda: son 7 günde
    # listeye eklenenler).
    words = models.ManyToManyField(Word, related_name="practiced_words_in_text")
    scores = models.CharField(max_length=40, default = "")

    # --- Yeni değerlendirme (rapor 9.1) ---
    durum = models.CharField(max_length=12, choices=YaziDurumu.choices,
                             default=YaziDurumu.BEKLIYOR, db_index=True)
    sertlik = models.CharField(max_length=8, choices=Sertlik.choices,
                               default=Sertlik.NORMAL)
    konu = models.CharField(max_length=200, blank=True, default="")
    # 5 üzerinden, yarım adımlı (1–5).
    puan = models.FloatField(blank=True, null=True)
    # {"iyi": [{alinti, aciklama}], "hatalar": [{alinti, dogrusu, neden}],
    #  "kullanilan_kelimeler": [...]} — doğrulanmış hâli (bkz. degerlendirme.py)
    geri_bildirim = models.JSONField(default=dict, blank=True)
    deneme_sayisi = models.PositiveSmallIntegerField(default=0)
    son_deneme = models.DateTimeField(blank=True, null=True)
    degerlendirildi = models.DateTimeField(blank=True, null=True)
    # Kullanıcı sildi. Satır hemen gitmiyor: "Geri al" çalışsın ve silip yeniden
    # yazarak günlük sınır aşılamasın diye. `yazilari_yeniden_dene` komutu
    # bir günden eski silinmişleri kalıcı olarak temizler.
    silindi = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return f"{self.owner.username} - {self.createdAt.strftime('%Y-%m-%d')}"

    @property
    def eski_mi(self):
        return self.durum == YaziDurumu.ESKI

    @property
    def bekliyor_mu(self):
        return self.durum == YaziDurumu.BEKLIYOR


class YazmaAyari(models.Model):
    """
    Kullanıcının yazma tercihi. Ayarlar sayfası henüz tasarlanmadığı için
    (rapor 16) seçim yazma formunda yapılıyor ve burada hatırlanıyor.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="yazma_ayari")
    sertlik = models.CharField(max_length=8, choices=Sertlik.choices, default=Sertlik.NORMAL)

    def __str__(self):
        return f"{self.user.username}: {self.sertlik}"

    @classmethod
    def sertlik_of(cls, user):
        ayar = cls.objects.filter(user=user).only("sertlik").first()
        return ayar.sertlik if ayar else Sertlik.NORMAL


class Diyalog(models.Model):
    """
    4–6 satırlık kısa diyalog, tek boşluk ("___"). Biçim: texts/diyalog_bicimi.md
    """
    BOSLUK = "___"

    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="diyaloglar")
    meaning = models.ForeignKey(Meaning, on_delete=models.SET_NULL, blank=True, null=True,
                                related_name="diyaloglar")
    # [{"kisi": "A", "metin": "..."}, ...] — tam olarak bir satırda "___" var.
    satirlar = models.JSONField()
    # Boşluğa gelen yazım (çekimli olabilir: "postponed").
    cevap = models.CharField(max_length=120)
    # Boşluğun altındaki Türkçe ipucu ("ertelemek").
    ipucu = models.CharField(max_length=200)
    # Cevaptan sonra gösterilen register/duygu tonu notu (Türkçe, isteğe bağlı).
    not_metni = models.CharField(max_length=400, blank=True, default="")
    register = models.CharField(max_length=12, choices=Register.choices, default=Register.NEUTRAL)
    sentiment = models.CharField(max_length=12, choices=Sentiment.choices, default=Sentiment.NEUTRAL)
    cefr = models.CharField(max_length=15, blank=True, default="")
    # Yalnızca denetlenmiş diyaloglar kullanıcıya gösterilir.
    denetlendi = models.BooleanField(default=False)
    kaynak = models.CharField(max_length=120, blank=True, default="")
    # Yeniden yüklemede aynı diyalog iki kez eklenmesin (kelime + satırlar özeti).
    anahtar = models.CharField(max_length=64, unique=True)
    olusturuldu = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "diyalog"
        verbose_name_plural = "diyaloglar"

    def __str__(self):
        return f"{self.word.text}: {self.cevap}"


class DiyalogCevabi(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="diyalog_cevaplari")
    diyalog = models.ForeignKey(Diyalog, on_delete=models.CASCADE, related_name="cevaplar")
    girdi = models.CharField(max_length=120)
    # dogru / neredeyse / yanlis
    sonuc = models.CharField(max_length=10)
    olusturuldu = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "olusturuldu"])]

    def __str__(self):
        return f"{self.user.username} - {self.diyalog_id}: {self.sonuc}"
