# Django importları
from django.contrib import admin

# Gerekli model importları
from quizzes.models import (
    QuizAttempt, 
    MultipleChoiceQuestion, 
    WritingQuestion, 
    MatchingQuestion
)

# Quizlerin sadece okunur olmasını sağlayan class (diğerleri extend ediyor)
class BaseQuizReadOnlyAdmin(admin.ModelAdmin):

    # Yeni quiz eklenemesin
    def has_add_permission(self, request):
        return False

    # Quizler silinemesin
    def has_delete_permission(self, request, obj=None):
        return True

    # Sadece okunur olsun
    def get_readonly_fields(self, request, obj=None):
        if obj: 
            # Modeldeki tüm field'ları al
            fields = [f.name for f in self.model._meta.fields]
            # Modeldeki tüm M2M field'ları al
            m2m_fields = [f.name for f in self.model._meta.many_to_many]
            return fields + m2m_fields
        return []
    
# Quiz Attempt'lerinin göründüğü model
@admin.register(QuizAttempt)
class QuizAttemptAdmin(BaseQuizReadOnlyAdmin):
    # Görünecek field'lar
    list_display = (
        'id',
        'owner',
        'get_quizType_display',
        'isCompleted',
        'totalQuestion',
        'totalCorrect',
        'totalWrong',
        'formatted_total_time',
        'createdAt',
    )

    # Arama filtrelerini göster
    list_filter = ('quizType', 'isCompleted', 'createdAt')

    # Arama yapılacak field
    search_fields = ('owner__username',)
    
    # 'get_quizType_display' için sıralama ve başlık ayarı
    @admin.display(description='Quiz Tipi', ordering='quizType')
    def get_quizType_display(self, obj):
        return obj.get_quizType_display()

# Çoktan seçmeli soruların görünüm modeli (extends BaseQuizReadOnlyAdmin)
@admin.register(MultipleChoiceQuestion)
class MultipleChoiceQuestionAdmin(BaseQuizReadOnlyAdmin):
    # Görünecek field'lar, arama filtrelerini göster, arama yapılacak fieldlar
    list_display = ('id', 'attempt', 'is_correct', 'user_answer', 'correct_option', 'time_taken')
    list_filter = ('is_correct', 'attempt__quizType')
    search_fields = ('attempt__owner__username', 'question_text')

# Yazma sorularının görünüm modeli (extends BaseQuizReadOnlyAdmin)
@admin.register(WritingQuestion)
class WritingQuestionAdmin(BaseQuizReadOnlyAdmin):
    # Görünecek field'lar, arama filtrelerini göster, arama yapılacak fieldlar
    list_display = ('id', 'attempt', 'is_correct', 'user_answer', 'correct_answer', 'time_taken')
    list_filter = ('is_correct', 'attempt__quizType')
    search_fields = ('attempt__owner__username', 'question_text', 'correct_answer')

# Eşleştirme sorularının görünüm modeli (extends BaseQuizReadOnlyAdmin)
@admin.register(MatchingQuestion)
class MatchingQuestionAdmin(BaseQuizReadOnlyAdmin):
    # Görünecek field'lar, arama filtrelerini göster, arama yapılacak fieldlar
    list_display = (
        'id', 
        'attempt', 
        'is_correct', 
        'correct_matches', 
        'wrong_matches', 
        'word_count', 
        'time_taken'
    )
    list_filter = ('is_correct', 'attempt__quizType')
    search_fields = ('attempt__owner__username',)

