from django.db import models
from users.models import User
from django.utils import timezone

# Create your models here.

class BroadcastEmail(models.Model):
    EMAIL_TYPE_CHOICES = (
        ('features', 'Yeni Özellikler'),
        ('improvements', 'Geliştirmeler ve İpuçları'),
    )
    STATUS_CHOICES = (
        ('draft', 'Taslak'),
        ('sent', 'Gönderildi'),
    )

    subject = models.CharField(max_length=255, verbose_name="E-posta Konusu")
    body = models.TextField(verbose_name="E-posta İçeriği")
    email_type = models.CharField(
        max_length=20, 
        choices=EMAIL_TYPE_CHOICES, 
        verbose_name="Kime Gönderilecek?"
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='draft', 
        verbose_name="Durum"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Gönderilme Tarihi")

    class Meta:
        verbose_name = "Toplu E-Posta"
        verbose_name_plural = "Toplu E-Postalar"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_email_type_display()}] {self.subject}"


class UserSettings(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,    
        related_name="mysettings",
    )

    # Mail kısmı:
    featuresMail = models.BooleanField(default = True)
    improvementsMail = models.BooleanField(default = True)
    dailyGoalsMail = models.BooleanField(default = True)

    # Günlük hedef (dailyGoal) 30 Eylül'de kaldırıldı: seri sabit kurallarla
    # çalışır (rapor 18.9, 18.23).

    audio = models.BooleanField(default = True)

    # Diğer eklenecek seçenekler
    # Tüm verilerimi dışa aktar
    # Tüm kelimelerimi dışa aktar
    # Tüm metinlerimi dışa aktar
    # Tüm yorumlarımı dışa aktar

    # Tüm like'larımı kaldır
    # Tüm dislike'larımı kaldır
    # Tüm yorumlarımı kaldır
    # Tüm metinlerimi kaldı (bug'a dikkat)
    # Siteye eklediğim tüm kelimeleri kaldır
    # Listeme dahil ettiğim tüm kelimeleri kaldır
    # Listemdeki TÜM kelimeleri kaldır

    # Hesabımı sil
