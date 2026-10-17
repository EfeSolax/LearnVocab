import re

from django import forms
from django.contrib import admin
from django.db.models import Max
from django.urls import reverse
from django.utils.html import format_html

from words.models import CEFR_LEVELS

from .models import OkumaKonusu, ReadingProgress, ReadingText


@admin.register(OkumaKonusu)
class OkumaKonusuAdmin(admin.ModelAdmin):
    """Okuma kütüphanesinin konuları (Efe, 17 Ekim). Yeni konu buradan eklenir, sonra metinlere seçilir."""

    list_display = ("ad", "anahtar", "ad_en", "ad_de", "renk", "sira", "metin_sayisi")
    list_editable = ("sira",)
    prepopulated_fields = {"anahtar": ("ad",)}
    search_fields = ("ad", "anahtar")
    fields = ("ad", "anahtar", "ad_en", "ad_de", "renk", "sira")

    @admin.display(description="metin")
    def metin_sayisi(self, konu):
        return ReadingText.objects.filter(topic=konu.anahtar).count()

    def get_prepopulated_fields(self, request, obj=None):
        # Anahtar yalnızca yeni konuda addan doldurulur; kullanılan konuda salt okunur
        return {} if obj else self.prepopulated_fields

    def get_readonly_fields(self, request, obj=None):
        # Anahtar metinlerde kayıtlı: konu kullanılırken değişirse metinler konusuz kalır
        if obj and ReadingText.objects.filter(topic=obj.anahtar).exists():
            return ("anahtar",)
        return ()

    def has_delete_permission(self, request, obj=None):
        # Metni olan konu silinemez (metinler konusuz kalırdı); önce metinleri başka konuya taşı
        if obj and ReadingText.objects.filter(topic=obj.anahtar).exists():
            return False
        return super().has_delete_permission(request, obj)


class ReadingTextForm(forms.ModelForm):
    topic = forms.ChoiceField(label="Konu")
    cefr = forms.ChoiceField(label="Seviye", required=False,
                             choices=[("", "—")] + [(s, s) for s in CEFR_LEVELS])

    class Meta:
        model = ReadingText
        fields = ("number", "title", "topic", "cefr", "source", "body")
        widgets = {"body": forms.Textarea(attrs={"rows": 24, "cols": 100})}
        help_texts = {
            "number": "Metnin kalıcı sıra numarası (benzersiz). Yeni metinde en büyük numaranın bir fazlası önerilir.",
            "body": "Paragrafları BOŞ BİR SATIRLA ayır. Kelime sayısı ve adres (slug) kaydederken kendiliğinden hesaplanır.",
            "source": "Ör. \"Project Gutenberg\", \"Yapay zekâ ile üretildi\". Boş bırakılabilir.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["topic"].choices = [("", "— konu seç —")] + [
            (k.anahtar, k.ad) for k in OkumaKonusu.objects.all()]
        self.fields["topic"].help_text = format_html(
            'Listede yoksa önce <a href="{}" target="_blank">yeni bir konu ekle</a>, sonra bu sayfayı yenile.',
            reverse("admin:readings_okumakonusu_add"))
        if not self.instance.pk and not self.initial.get("number"):
            self.initial["number"] = (ReadingText.objects.aggregate(n=Max("number"))["n"] or 0) + 1

    def clean_body(self):
        # Tarayıcı satır sonunu "\r\n" gönderir; paragraflar "\n\n" ile bölündüğü için (paragraflara_bol)
        # normalleştirilmezse metin tek paragraf görünür. Satır sonu boşlukları ve fazla boş satırlar da atılır.
        satirlar = [s.rstrip() for s in self.cleaned_data["body"].replace("\r\n", "\n").replace("\r", "\n").split("\n")]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(satirlar)).strip()


@admin.register(ReadingText)
class ReadingTextAdmin(admin.ModelAdmin):
    form = ReadingTextForm
    list_display = ("number", "title", "konu", "cefr", "word_count", "adres")
    list_filter = ("topic", "cefr")
    search_fields = ("title", "body")
    ordering = ("number",)
    readonly_fields = ("word_count", "adres")

    def get_fields(self, request, obj=None):
        alanlar = ["number", "title", "topic", "cefr", "source", "body"]
        return alanlar + (["word_count", "adres"] if obj else [])

    @admin.display(description="konu", ordering="topic")
    def konu(self, metin):
        return metin.topic_label

    @admin.display(description="adres")
    def adres(self, metin):
        if not metin.slug:
            return "—"
        yol = reverse("readings_library_text", args=[metin.slug])
        return format_html('<a href="{}" target="_blank">{}</a>', yol, yol)

    def save_model(self, request, obj, form, change):
        # Kütüphane komutlarıyla aynı kural: boşluklara göre kelime sayısı
        obj.word_count = len(obj.body.split())
        super().save_model(request, obj, form, change)


@admin.register(ReadingProgress)
class ReadingProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "text", "read_at")
    list_filter = ("read_at",)
    search_fields = ("user__username", "text__title")
