from django import template

from bildirimler import ayar

register = template.Library()


@register.simple_tag
def bildirim_genel_anahtar():
    """VAPID genel anahtarı; bildirimler kapalıysa boş dize."""
    return ayar.genel_anahtar() if ayar.acik() else ""
