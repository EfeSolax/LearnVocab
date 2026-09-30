"""Okumalar kancaları: metin satırı silinince diskteki gövde dosyası da silinir."""

from django.db.models.signals import post_delete
from django.dispatch import receiver

from . import depo
from .models import UserText


@receiver(post_delete, sender=UserText, dispatch_uid="okuma-dosyasini-sil")
def dosyayi_sil(sender, instance, **kwargs):
    depo.sil(instance.dosya)
