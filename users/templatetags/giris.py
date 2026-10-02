"""Google ile giriş açık mı (anahtarlar .env'de var mı)? Rapor 18.21."""

from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def google_giris_acik():
    return getattr(settings, "GOOGLE_GIRIS_ACIK", False)
