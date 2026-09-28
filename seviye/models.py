"""
Seviye testi (ürün raporu 7; veri D4 ve D8).

  SeviyeKelimesi     1. kısmın ekran kelimeleri (D8). `seviye_kelimeleri_sec`
                     komutu seçer ve yazar; her testte havuzdan rastgele 40.
                     Tablo boşsa seçim aynı kuralla anında yapılır (secim.py).
  OkumaSorusu        2. kısmın okuma havuzu (D4). Yapay zekâ üretimi gerektirdiği
                     için BOŞ başlar; `seviye_okuma_yukle` ile JSON'dan yüklenir.
                     Havuz eksikse 2. kısım atlanır.
  SeviyeTestiSonucu  Her bitirilen test: tahmin, ekranlardaki bilinen sayıları,
                     okuma sonucu ve ilk listeye eklenen kelimeler (Geri al için).
"""

from django.conf import settings
from django.db import models

from users.seviye import SEVIYE_SECENEKLERI
from words.models import Word


class Ekran(models.IntegerChoices):
    KOLAY = 1, "A1–A2"
    ORTA = 2, "B1–B1+"
    ZOR = 3, "B2–C1"


class SeviyeKelimesi(models.Model):
    ekran = models.PositiveSmallIntegerField(choices=Ekran.choices, db_index=True)
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="seviye_testi_satirlari")
    # Seçildiği andaki seviye (ekranın içindeki A1/A2 dengesi için).
    cefr = models.CharField(max_length=2)
    # wordfreq zipf sıklığı (kurulu değilse boş). Denetim için saklanır.
    zipf = models.FloatField(blank=True, null=True)
    sira = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "seviye testi kelimesi"
        verbose_name_plural = "seviye testi kelimeleri"
        unique_together = ("ekran", "word")
        ordering = ("ekran", "sira")

    def __str__(self):
        return f"{self.ekran}. ekran · {self.word.text} ({self.cefr})"


class OkumaZorlugu(models.IntegerChoices):
    KOLAY = 1, "Kolay"
    ORTA = 2, "Orta"
    ZOR = 3, "Zor"


class OkumaSorusu(models.Model):
    """Kısa metin (4–5 cümle) + "metni en iyi özetleyen cümle" sorusu (D4)."""

    zorluk = models.PositiveSmallIntegerField(choices=OkumaZorlugu.choices, db_index=True)
    cefr = models.CharField(max_length=2, blank=True, default="")
    metin = models.TextField()
    dogru = models.CharField(max_length=400)
    celdiriciler = models.JSONField(default=list)
    # Yalnızca denetlenmiş sorular teste girer (rapor 7: havuz denetlenir).
    denetlendi = models.BooleanField(default=False)
    kaynak = models.CharField(max_length=120, blank=True, default="")
    # Metnin sha1'i: aynı metin ikinci kez yüklenirse güncellenir.
    anahtar = models.CharField(max_length=64, unique=True)
    olusturuldu = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "okuma sorusu"
        verbose_name_plural = "okuma soruları"

    def __str__(self):
        return f"{self.get_zorluk_display()} · {self.metin[:60]}"


class SeviyeTestiSonucu(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="seviye_testleri")
    olusturuldu = models.DateTimeField(auto_now_add=True)
    tahmin = models.CharField(max_length=2, choices=SEVIYE_SECENEKLERI)
    # Yalnızca 1. kısımdan çıkan tahmin (okuma düzeltmesinden önce).
    kelime_tahmini = models.CharField(max_length=2, choices=SEVIYE_SECENEKLERI)
    # {"1": {"gosterilen": 40, "bilinen": 31}, "2": {...}} — gösterilmeyen ekran yok.
    ekranlar = models.JSONField(default=dict)
    # {"dogru": 2, "toplam": 3} ya da 2. kısım atlandıysa boş.
    okuma = models.JSONField(blank=True, null=True)
    # İlk listeye YENİ eklenen kelimeler (zaten listede olanlar yok): Geri al bunları çıkarır.
    eklenen = models.JSONField(default=list)
    geri_alindi = models.BooleanField(default=False)

    class Meta:
        verbose_name = "seviye testi sonucu"
        verbose_name_plural = "seviye testi sonuçları"
        ordering = ("-olusturuldu", "-id")

    def __str__(self):
        return f"{self.user} · {self.tahmin} · {self.olusturuldu:%Y-%m-%d}"
