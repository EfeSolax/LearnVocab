from django.contrib import admin

from .models import GunlukHatirlatma, PushAboneligi


@admin.register(PushAboneligi)
class PushAboneligiAdmin(admin.ModelAdmin):
    list_display = ("user", "tarayici", "olusturuldu", "son_basari")
    search_fields = ("user__username",)
    raw_id_fields = ("user",)


@admin.register(GunlukHatirlatma)
class GunlukHatirlatmaAdmin(admin.ModelAdmin):
    list_display = ("user", "gun", "gonderilen")
    list_filter = ("gun",)
    raw_id_fields = ("user",)
