from django.contrib import admin

from .models import Diyalog, DiyalogCevabi, Text, YazmaAyari


@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    list_display = ("owner", "durum", "puan", "score", "sertlik", "createdAt", "silindi")
    search_fields = ("owner__username", "content")
    list_filter = ("durum", "sertlik", "createdAt")
    fieldsets = (
        ("Genel", {"fields": ("owner", "createdAt", "durum", "sertlik", "konu", "silindi")}),
        ("Metin", {"fields": ("content",)}),
        ("Değerlendirme", {"fields": ("puan", "geri_bildirim", "response",
                                      "deneme_sayisi", "son_deneme", "degerlendirildi")}),
        ("Eski değerlendirme (100 puan)", {"fields": ("score", "scores"), "classes": ("collapse",)}),
        ("Kullanmayı dene kelimeleri", {"fields": ("words",)}),
    )
    filter_horizontal = ("words",)
    readonly_fields = ("createdAt",)

    # Metinler yalnızca kullanıcı tarafından yazılır.
    def has_add_permission(self, request):
        return False


@admin.register(YazmaAyari)
class YazmaAyariAdmin(admin.ModelAdmin):
    list_display = ("user", "sertlik")
    search_fields = ("user__username",)


@admin.register(Diyalog)
class DiyalogAdmin(admin.ModelAdmin):
    list_display = ("word", "cevap", "ipucu", "register", "cefr", "denetlendi", "kaynak")
    list_filter = ("denetlendi", "register", "sentiment", "cefr")
    search_fields = ("word__text", "cevap", "ipucu")
    raw_id_fields = ("word", "meaning")
    readonly_fields = ("anahtar", "olusturuldu")


@admin.register(DiyalogCevabi)
class DiyalogCevabiAdmin(admin.ModelAdmin):
    list_display = ("user", "diyalog", "girdi", "sonuc", "olusturuldu")
    list_filter = ("sonuc",)
    raw_id_fields = ("user", "diyalog")
