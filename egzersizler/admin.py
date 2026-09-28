from django.contrib import admin

from .models import BaglacCumlesi, EgzersizCevabi, EgzersizOturumu, EsdizimCeldiricisi


@admin.register(EgzersizOturumu)
class EgzersizOturumuAdmin(admin.ModelAdmin):
    list_display = ("user", "tur", "tip", "durum", "sira", "olusturma")
    list_filter = ("tur", "durum")
    raw_id_fields = ("user", "kaynak")


@admin.register(EgzersizCevabi)
class EgzersizCevabiAdmin(admin.ModelAdmin):
    list_display = ("user", "word", "soru_tipi", "dogru", "tarih")
    list_filter = ("soru_tipi", "dogru")
    raw_id_fields = ("user", "word", "oturum")


@admin.register(BaglacCumlesi)
class BaglacCumlesiAdmin(admin.ModelAdmin):
    list_display = ("cumle", "dogru", "cefr", "denetlendi")
    list_filter = ("cefr", "denetlendi")
    search_fields = ("cumle", "dogru")
    raw_id_fields = ("ifade",)


@admin.register(EsdizimCeldiricisi)
class EsdizimCeldiricisiAdmin(admin.ModelAdmin):
    list_display = ("collocation", "celdirici", "gercekten_yanlis", "kaynak", "dogrulama_tarihi")
    list_filter = ("gercekten_yanlis", "celdirici")
    raw_id_fields = ("collocation",)
