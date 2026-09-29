"""
Seri (streak) kayıtları (rapor 18.9).

GunlukCalisma  kullanıcı + yerel gün başına bir satır: o gün yapılanların
               sayacı, gün tamamlandı mı, dondurma hakkıyla mı kurtarıldı.
SeriDurumu     kullanıcı başına bir satır: mevcut seri, en uzun seri,
               dondurma hakkı, ardışık gün sayacı ve saat dilimi.
Kural: seri/hesap.py
"""

from django.conf import settings
from django.db import models


class GunlukCalisma(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="gunluk_calismalar")
    gun = models.DateField()   # kullanıcının YEREL günü

    lp = models.PositiveIntegerField(default=0)          # kaydırılan L&P kartı
    egzersiz = models.PositiveIntegerField(default=0)    # cevaplanan egzersiz sorusu
    metin = models.PositiveIntegerField(default=0)       # geçerli metin (texts/gecerlilik.py)
    diyalog = models.PositiveIntegerField(default=0)     # cevaplanan diyalog

    tamamlandi = models.BooleanField(default=False)
    tamamlandi_at = models.DateTimeField(blank=True, null=True)
    # Gün kaçırıldı ama dondurma hakkıyla seri korundu (takvimde mavi).
    dondurulan = models.BooleanField(default=False)

    class Meta:
        verbose_name = "günlük çalışma"
        verbose_name_plural = "günlük çalışmalar"
        constraints = [models.UniqueConstraint(fields=["user", "gun"], name="gunluk_calisma_tek")]
        indexes = [models.Index(fields=["user", "gun"])]

    def __str__(self):
        return f"{self.user} · {self.gun} · {'✓' if self.tamamlandi else ('❄' if self.dondurulan else '·')}"


class SeriDurumu(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="seri_durumu")
    mevcut = models.PositiveIntegerField(default=0)
    en_uzun = models.PositiveIntegerField(default=0)
    # Dondurma hakkı: herkes 1 ile başlar, en çok 3 (rapor 18.9).
    hak = models.PositiveSmallIntegerField(default=1)
    # Ardışık tamamlanan gün sayacı: 5 olunca +1 hak ve sıfırlanır.
    ardisik = models.PositiveSmallIntegerField(default=0)
    # Kuralın en son işlendiği yerel gün (kaçırılan günler buradan sonra işlenir).
    son_islenen_gun = models.DateField(blank=True, null=True)
    # Kullanıcının saat dilimi (tarayıcıdan). Gün yerel 00.00'da biter.
    saat_dilimi = models.CharField(max_length=64, default="Europe/Istanbul")

    class Meta:
        verbose_name = "seri durumu"
        verbose_name_plural = "seri durumları"

    def __str__(self):
        return f"{self.user} · seri {self.mevcut} · hak {self.hak}"
