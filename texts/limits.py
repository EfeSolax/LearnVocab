"""
Metin yazma sıklığı kısıtı — TEK KAYNAK.

Kullanıcının ne sıklıkla yeni metin yazabileceği tek bir ayardan yönetilir:

    settings.TEXT_SUBMISSION_INTERVAL_MINUTES   (.env: TEXT_SUBMISSION_INTERVAL_MINUTES)

Örnekler:
    1440 -> günde bir metin (varsayılan)
       5 -> beş dakikada bir
       0 -> kısıt tamamen kapalı

Eskiden bu süre üç ayrı yerde `timedelta(days=1)` olarak yazılıydı
(texts/views.py'de iki kez, userprofile/views.py'de bir kez) ve kullanıcıya
gösterilen "1 gün" metinleri de sabitti. Süreyi değiştirmek için hepsini
bulmak gerekiyordu; artık tek satır yetiyor.
"""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from texts.models import Text

DEFAULT_INTERVAL_MINUTES = 1440  # 1 gün


def interval():
    """Ayarlardaki bekleme süresi. Kısıt kapalıysa sıfır uzunlukta timedelta."""
    minutes = getattr(settings, "TEXT_SUBMISSION_INTERVAL_MINUTES", DEFAULT_INTERVAL_MINUTES)
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        minutes = DEFAULT_INTERVAL_MINUTES
    return timedelta(minutes=max(0, minutes))


def is_enabled():
    """Kısıt açık mı?"""
    return interval() > timedelta(0)


def remaining_for(user):
    """
    Kullanıcının yeni metin yazabilmesi için kalan süre.

    Yazabiliyorsa None döner.
    """
    wait = interval()
    if not wait:
        return None

    last = Text.objects.filter(owner=user).order_by("-createdAt").first()
    if last is None:
        return None

    remaining = (last.createdAt + wait) - timezone.now()
    return remaining if remaining > timedelta(0) else None


def can_write_new_text(user):
    """Kullanıcı şu anda yeni metin yazabilir mi?"""
    return remaining_for(user) is None


def can_delete(text):
    """
    Metin silinebilir mi?

    Kısıtla bilerek aynı süreye bağlı: aksi hâlde kullanıcı metnini silip
    hemen yenisini yazarak sınırı atlayabilirdi. Kısıt kapalıyken silme de
    serbest.
    """
    wait = interval()
    if not wait:
        return True
    return (timezone.now() - text.createdAt) >= wait


def humanize(delta):
    """
    Bir süreyi Türkçe okunur hâle getirir: "1 gün", "2 saat 5 dakika", "3 dakika".

    Saniyeler yukarı yuvarlanır; "0 dakika kaldı" gibi bir çıktı olmaz.
    """
    if delta is None:
        return ""

    total_seconds = int(delta.total_seconds())
    if total_seconds <= 0:
        return "0 dakika"

    days, rest = divmod(total_seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes = -(-rest // 60)  # yukarı yuvarla

    if minutes == 60:
        hours += 1
        minutes = 0
    if hours == 24:
        days += 1
        hours = 0

    parts = []
    if days:
        parts.append(f"{days} gün")
    if hours:
        parts.append(f"{hours} saat")
    if minutes and not days:
        parts.append(f"{minutes} dakika")

    return " ".join(parts) or "1 dakika"


def interval_label():
    """Ayardaki sürenin okunur hâli; kısıt kapalıysa boş string."""
    return humanize(interval()) if is_enabled() else ""


def remaining_label(user):
    """Kullanıcı için kalan sürenin okunur hâli; yazabiliyorsa boş string."""
    return humanize(remaining_for(user))
