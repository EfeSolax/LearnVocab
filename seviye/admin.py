from django.contrib import admin

from .models import OkumaSorusu, SeviyeKelimesi, SeviyeTestiSonucu


@admin.register(SeviyeKelimesi)
class SeviyeKelimesiAdmin(admin.ModelAdmin):
    list_display = ("word", "ekran", "cefr", "zipf", "sira")
    list_filter = ("ekran", "cefr")
    search_fields = ("word__text",)
    raw_id_fields = ("word",)


@admin.register(OkumaSorusu)
class OkumaSorusuAdmin(admin.ModelAdmin):
    list_display = ("__str__", "zorluk", "cefr", "denetlendi", "kaynak")
    list_filter = ("zorluk", "denetlendi")
    search_fields = ("metin", "dogru")


@admin.register(SeviyeTestiSonucu)
class SeviyeTestiSonucuAdmin(admin.ModelAdmin):
    list_display = ("user", "tahmin", "kelime_tahmini", "olusturuldu", "geri_alindi")
    list_filter = ("tahmin",)
    raw_id_fields = ("user",)
