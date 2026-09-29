from django.contrib import admin

from .models import GunlukCalisma, SeriDurumu


@admin.register(SeriDurumu)
class SeriDurumuAdmin(admin.ModelAdmin):
    list_display = ("user", "mevcut", "en_uzun", "hak", "ardisik", "son_islenen_gun", "saat_dilimi")
    search_fields = ("user__username",)


@admin.register(GunlukCalisma)
class GunlukCalismaAdmin(admin.ModelAdmin):
    list_display = ("user", "gun", "lp", "egzersiz", "metin", "diyalog", "tamamlandi", "dondurulan")
    list_filter = ("tamamlandi", "dondurulan")
    search_fields = ("user__username",)
