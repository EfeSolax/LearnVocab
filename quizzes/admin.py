"""
Çalışma kayıtlarının yönetim paneli.

Buradaki asıl iş hata ayıklamak: bir kart neden bugün soruldu, bir
kelime neden hiç gelmiyor. O yüzden listelerde kararlılık, zorluk ve
sıra günü doğrudan görünüyor.
"""

from django.contrib import admin

from .models import ReviewItem, ReviewLog, StudySession


@admin.register(ReviewItem)
class ReviewItemAdmin(admin.ModelAdmin):
    list_display = ("user", "word", "aspect", "state", "kararlilik",
                    "zorluk", "due_at", "reps", "lapses")
    list_filter = ("aspect", "state", "user")
    search_fields = ("word__text", "user__username")
    autocomplete_fields = ()
    readonly_fields = ("created_at",)
    list_select_related = ("user", "word")

    @admin.display(description="kararlılık (gün)", ordering="stability")
    def kararlilik(self, obj):
        return "—" if obj.stability is None else f"{obj.stability:.1f}"

    @admin.display(description="zorluk", ordering="difficulty")
    def zorluk(self, obj):
        return "—" if obj.difficulty is None else f"{obj.difficulty:.1f}"


@admin.register(ReviewLog)
class ReviewLogAdmin(admin.ModelAdmin):
    list_display = ("answered_at", "user", "word_text", "aspect", "format",
                    "is_correct", "grade", "seconds", "scheduled_days")
    list_filter = ("aspect", "format", "is_correct", "was_confident_error")
    search_fields = ("word_text", "user__username")
    date_hierarchy = "answered_at"
    list_select_related = ("user",)


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ("started_at", "user", "mode", "answered_count",
                    "correct_count", "planned_count", "finished_at")
    list_filter = ("mode",)
    search_fields = ("user__username",)
    date_hierarchy = "started_at"
    list_select_related = ("user",)
