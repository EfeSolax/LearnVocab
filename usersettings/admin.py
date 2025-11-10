# /usersettings/admin.py

from django.contrib import admin
from .models import UserSettings
from .models import BroadcastEmail, UserSettings
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

@admin.register(BroadcastEmail)
class BroadcastEmailAdmin(admin.ModelAdmin):
    list_display = ('subject', 'email_type', 'status', 'sent_at', 'created_at')
    list_filter = ('email_type', 'status')
    actions = ['send_selected_broadcasts'] # Admin eylemi

    @admin.action(description='Seçili e-postaları ilgili kullanıcılara gönder')
    def send_selected_broadcasts(self, request, queryset):
        for broadcast in queryset.filter(status='draft'):

            if broadcast.email_type == 'features':
                settings_list = UserSettings.objects.filter(featuresMail=True)
            elif broadcast.email_type == 'improvements':
                settings_list = UserSettings.objects.filter(improvementsMail=True)

            recipients = list(settings_list.select_related('user').values_list('user__email', flat=True))

            if not recipients:
                self.message_user(request, f"'{broadcast.subject}' için e-posta listesi boş, gönderilmedi.", 'warning')
                continue

            try:
                send_mail(
                    broadcast.subject,
                    broadcast.body, 
                    settings.DEFAULT_FROM_EMAIL,
                    recipients, # Toplu gönderim
                    fail_silently=False,
                )

                broadcast.status = 'sent'
                broadcast.sent_at = timezone.now()
                broadcast.save()

                self.message_user(request, f"'{broadcast.subject}' e-postası {len(recipients)} kullanıcıya gönderildi.", 'success')
            except Exception as e:
                self.message_user(request, f"E-posta gönderirken hata: {e}", 'error')

# 1. UserSettings için bir Inline Admin sınıfı tanımlayın
# StackedInline, alanları alt alta güzel bir şekilde gösterir.
class UserSettingsInline(admin.StackedInline):
    model = UserSettings
    
    # Modelinizde OneToOneField varsa max_num=1'e gerek yoktur.
    # ForeignKey ise max_num = 1 kalmalı.
    max_num = 1 
    
    can_delete = False 
    verbose_name_plural = 'Kullanıcı Ayarları'
    
    fieldsets = (
        ('Öğrenme Ayarları', {
            'fields': ('dailyGoal', 'audio')
        }),
        ('E-posta Bildirimleri', {
            'classes': ('collapse',),
            'fields': ('featuresMail', 'improvementsMail', 'dailyGoalsMail'),
        }),
    )

# İsteğe bağlı: UserSettings modelini ayrıca görmek isterseniz
# @admin.register(UserSettings)
# class UserSettingsAdmin(admin.ModelAdmin):
#     list_display = ('user', 'dailyGoal', 'audio')
#     search_fields = ('user__username',)