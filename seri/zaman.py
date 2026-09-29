"""Kullanıcının yerel saati (rapor 18.9: gün yerel 00.00'da biter)."""

from datetime import datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.utils import timezone


def saat_dilimi(user):
    ad = None
    if user is not None and getattr(user, "is_authenticated", False):
        from .models import SeriDurumu
        ad = SeriDurumu.objects.filter(user=user).values_list("saat_dilimi", flat=True).first()
    try:
        return ZoneInfo(ad or settings.TIME_ZONE)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo(settings.TIME_ZONE)


def gecerli_saat_dilimi_mi(ad):
    try:
        ZoneInfo(ad)
        return True
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        return False


def yerel_simdi(user, simdi=None):
    return (simdi or timezone.now()).astimezone(saat_dilimi(user))


def yerel_gun(user, simdi=None):
    return yerel_simdi(user, simdi).date()


def yerel_gun_basi(user, simdi=None):
    """Kullanıcının bugününün başlangıcı (aware datetime)."""
    yerel = yerel_simdi(user, simdi)
    return datetime.combine(yerel.date(), time.min, tzinfo=yerel.tzinfo)
