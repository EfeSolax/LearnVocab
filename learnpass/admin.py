from django.contrib import admin

from .models import WordEncounter


@admin.register(WordEncounter)
class WordEncounterAdmin(admin.ModelAdmin):
    list_display = ("user", "word", "last_verdict", "times_seen", "misjudged_count",
                    "basamak", "son_basarili", "sonraki_tekrar", "last_seen_at")
    list_filter = ("last_verdict", "last_mode", "son_basarili", "takipte")
    search_fields = ("user__username", "word__text")
    autocomplete_fields = ()
