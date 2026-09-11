from django.contrib import admin

from .models import WordEncounter


@admin.register(WordEncounter)
class WordEncounterAdmin(admin.ModelAdmin):
    list_display = ("user", "word", "last_verdict", "times_seen", "misjudged_count",
                    "is_learned", "last_seen_at")
    list_filter = ("last_verdict", "last_mode", "is_learned")
    search_fields = ("user__username", "word__englishWord")
    autocomplete_fields = ()
