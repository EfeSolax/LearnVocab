from django.contrib import admin

from .models import ReadingProgress, ReadingText


@admin.register(ReadingText)
class ReadingTextAdmin(admin.ModelAdmin):
    list_display = ("number", "title", "topic", "word_count")
    list_filter = ("topic",)
    search_fields = ("title", "body")
    ordering = ("number",)


@admin.register(ReadingProgress)
class ReadingProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "text", "read_at")
    list_filter = ("read_at",)
    search_fields = ("user__username", "text__title")
