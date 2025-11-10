from django.db import models

# Django'nun hazır AbstractUser modelini import edelim.
from django.contrib.auth.models import AbstractUser


# Create your models here.

class User(AbstractUser):
    # Kullanıcının kurunu temsilen oluşturulan değişken.
    level = models.PositiveBigIntegerField(default = 1, verbose_name="level")

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
