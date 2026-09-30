from django.db import models

# Django'nun hazır AbstractUser modelini import edelim.
from django.contrib.auth.models import AbstractUser

from .seviye import SEVIYE_SECENEKLERI


# Create your models here.

class User(AbstractUser):
    # CEFR seviyesi (rapor 7): seviye testi ya da "Seviyemi kendim seçeyim"
    # yazar. Boşsa seviye henüz belirlenmemiş demek; okurken her zaman
    # users.seviye.kullanici_seviyesi(user) kullanılır (eski kur, varsayılan B1).
    cefr = models.CharField(max_length=2, choices=SEVIYE_SECENEKLERI, blank=True, default="",
                            verbose_name="CEFR seviyesi")

    profile_pic = models.ImageField(
        upload_to='profile_pics/',  # Yüklenecekleri klasör
        null=True,                  # Veritabanında boş olabilir
        blank=True,                 # Formlarda boş bırakılabilir
        default='profile_pics/default.png' # Opsiyonel: Varsayılan bir resim atar
    )

    # Kullanıcının biyografisi
    bio = models.CharField(max_length=500, blank = True, null = True)

    friends = models.ManyToManyField(
        "self", #bu objenin kendisi ile arkadaşlık ilişkisi kurulacak.
        symmetrical=True, #b a'nın arkadaşı diye a b'nin arkadaşı olmak zorunda değil (simetrik değil)
        blank=True, #her kullanıcının bir arkadaşı olmak zorunda değil
        ## DİKKAT! related_name kısmı objenin kendisi ile aynı isimde olmamalıymış.
    )

    incomingRequests = models.ManyToManyField(
        "self", #bu objenin kendisi ile arkadaşlık ilişkisi kurulacak.
        symmetrical=False, # ""
        blank=True, # ""
        
    )

    def __str__(self):
        return self.username
