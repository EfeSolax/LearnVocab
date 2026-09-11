from django.contrib import admin
from .models import Word

# Register your models here.

@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = (
        'englishWord', 
        'meaningTr', 
        'owner', 
        'isVerb', 
        'wordLevel',
        'createdAt', 
        'visibility',
        'explanation',
        'note',
        'prefix',
        'v2Form',
        'v3Form',
        'exampleSentence1',
        'createdAt',
        'isBaseWord',
        'saved_users',
    )
    list_filter = ('isVerb', 'visibility', 'createdAt', 'owner','wordLevel','isBaseWord',)
    search_fields = ('englishWord', 'meaningTr') + tuple(
        f'exampleSentence{i}' for i in range(1, 11)
    )
    ordering = ('-createdAt',)
    readonly_fields = ('createdAt',)
    
    fieldsets = (
        (None, {
            'fields': ('englishWord', 'meaningTr', 'explanation', 'note', 'prefix', 'isVerb','wordLevel','isBaseWord',)
        }),
        ('Verb Forms', {
            'fields': ('v2Form', 'v3Form')
        }),
        ('Example Sentences', {
            'fields': ('exampleSentence1', 'exampleSentence2', 'exampleSentence3', 'exampleSentence4', 'exampleSentence5', 'exampleSentence6', 'exampleSentence7', 'exampleSentence8', 'exampleSentence9', 'exampleSentence10')
        }),
        ('Synonyms / Antonyms / Collocations', {
            'fields': ('synonyms', 'antonyms', 'collocations')
        }),
        ('Meta', {
            'fields': ('owner', 'visibility', 'createdAt','saved_users')
        }),
    )

    readonly_fields = ('createdAt','saved_users')  # read-only olarak gösterebilirsin

    # saved_by kullanıcılarını gösterecek fonksiyon
    def saved_users(self, obj):
        return ", ".join([user.username for user in obj.saved_by.all()])
    saved_users.short_description = "Saved By"