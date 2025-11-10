# Django importları
from django.contrib import admin

# Gerekli modellerin importu
from comments.models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    # Görünecek alanlar
    list_display = ('owner', 'content_snippet', 'createdAt')

    # Neye göre aranabileceğini belirten alanlar
    search_fields = ('owner__username', 'content')

    # Filtreleme alanları
    list_filter = ('createdAt',)

    # Detaylı görünü bilgisi
    fieldsets = (
        # Genel yorum bilgisinde gösterilecek alanlar
        ('Yorum Bilgisi', {
            'fields': ('owner', 'content', 'createdAt')
        }),
        # Etkileşimler kısmında gösterilecek alanlar
        ('Etkileşimler (Likes/Dislikes)', {
            'fields': ('liked_by', 'disliked_by'),
            'classes': ('collapse',) 
        }),
    )

    # M2M alanları için detaylı görünüm
    filter_horizontal = ('liked_by', 'disliked_by')

    # Sadece okunabilir, değiştirilebilir değil
    readonly_fields = ('createdAt',)

    # Listeleme görünümünde yorumu kısaltacak bir görünüm (ilk 30 karakter)
    @admin.display(description='Yorum (Kısa)')
    def content_snippet(self, obj):
        return f"{obj.content[:30]}..."