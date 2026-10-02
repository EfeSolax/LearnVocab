"""
Google ile ilk girişte (rapor 18.21) açılan hesaba, kayıt formundaki gibi
ayar satırı eklenir (users/views.register da aynısını yapar).
"""

from allauth.account.signals import user_signed_up
from django.dispatch import receiver


@receiver(user_signed_up, dispatch_uid="lv-google-kayit-ayarlari")
def ayarlari_olustur(sender, request, user, **kwargs):
    from usersettings.models import UserSettings
    UserSettings.objects.get_or_create(user=user)
