"""
Web Push abonelikleri ve gönderim kayıtları (rapor 10).
"""

from django.conf import settings
from django.db import models


class PushAboneligi(models.Model):
    """
    Bir tarayıcının (cihazın) push aboneliği. Bir kullanıcının birden çok
    cihazı olabilir. `endpoint` tarayıcıya özgüdür: aynı cihazda başka bir
    hesapla abone olunursa abonelik o hesaba geçer.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="push_abonelikleri")
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=100)
    tarayici = models.CharField(max_length=200, blank=True, default="")
    olusturuldu = models.DateTimeField(auto_now_add=True)
    # Son başarılı gönderim. Hiç gönderilmediyse boş.
    son_basari = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "push aboneliği"
        verbose_name_plural = "push abonelikleri"

    def __str__(self):
        return f"{self.user} · {self.endpoint[:60]}"

    def bilgi(self):
        """pywebpush'un beklediği biçim."""
        return {"endpoint": self.endpoint, "keys": {"p256dh": self.p256dh, "auth": self.auth}}


class GunlukHatirlatma(models.Model):
    """
    Günlük L&P hatırlatmasının gönderildiği gün. Kullanıcı başına günde tek
    kayıt: komut aynı gün birden çok kez çalışsa bile ikinci bildirim gitmez.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="gunluk_hatirlatmalar")
    gun = models.DateField()
    gonderilen = models.PositiveSmallIntegerField(default=0)  # başarılı cihaz sayısı
    olusturuldu = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "günlük hatırlatma"
        verbose_name_plural = "günlük hatırlatmalar"
        constraints = [
            models.UniqueConstraint(fields=["user", "gun"], name="gunluk_hatirlatma_tek"),
        ]

    def __str__(self):
        return f"{self.user} · {self.gun}"
