# /usersettings/management/commands/send_daily_reminders.py

import datetime
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from usersettings.models import UserSettings # Modelinizin olduğu yer (users.models'da da olabilir)
from django.conf import settings
from django.utils import timezone

class Command(BaseCommand):
    help = 'Günlük pratik hatırlatması ("dailyGoalsMail=True") isteyen kullanıcılara e-posta gönderir.'

    def handle(self, *args, **options):

        # Sunucunuzun saat ayarı farklıysa diye UTC'ye göre değil, 
        # mevcut güne göre (naive time) kontrol etmek daha güvenli olabilir
        # VEYA kullanıcının son girişine bakabiliriz.

        # En basit yöntem: dailyGoalsMail=True olan herkesi al.
        users_settings = UserSettings.objects.filter(dailyGoalsMail=True).select_related('user')

        if not users_settings.exists():
            # Bu bir hata değil, o gün kimse mail istememiş olabilir.
            self.stdout.write(self.style.SUCCESS('E-posta gönderilecek aktif kullanıcı bulunamadı. Görev tamamlandı.'))
            return

        self.stdout.write(f'Gönderilecek {users_settings.count()} günlük hatırlatma e-postası bulundu...')

        # E-posta göndermek için bir liste oluşturalım
        sent_count = 0
        failed_count = 0

        for setting in users_settings:
            user = setting.user

            # Kullanıcının e-postası yoksa veya geçerli değilse atla
            if not user.email:
                failed_count += 1
                continue

            subject = f"LearnVocab Günlük Hatırlatman, {user.username}!"
            message = (
                f"Merhaba {user.username},\n\n"
                f"Günün kelimelerini öğrenme zamanı!\n\n"
                f"Pratik yapmak için: {settings.SITE_ADRESI}/calismalar/\n"
                f"\n\n"
                f"Bu e-postaları almak istemiyorsan, profilindeki 'Ayarlar' sayfasından bildirimleri kapatabilirsin.\n\n"
                f"İyi öğrenmeler!"
            )

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL, # 'settings.py'den
                    [user.email], # Alıcı
                    fail_silently=False, # Hata olursa program dursun (loglarda görmek için)
                )
                self.stdout.write(self.style.SUCCESS(f"'{user.username}' kullanıcısına e-posta başarıyla gönderildi."))
                sent_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"'{user.username}' kullanıcısına e-posta gönderilirken HATA: {e}"))
                failed_count += 1

        self.stdout.write(self.style.SUCCESS(f'\nGörev Tamamlandı: {sent_count} e-posta gönderildi, {failed_count} hata alındı.'))