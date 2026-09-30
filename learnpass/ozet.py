"""
Ayrıntılı karşılaşma kayıtlarının özetlenmesi (rapor 18.32).

EncounterLog her cevap için bir satır yazar; 1 GB'lık MySQL sınırı yüzünden
bu satırlar 90 gün tutulur. Daha eskileri (gün, mod, basamak, karar)
başına tek sayıya indirilip (KarsilasmaOzeti) silinir. Özet kişisizdir.

90 günlük pencere seviyenin kendiliğinden düzelmesiyle (seviye/duzeltme.py)
aynıdır; tekrar kuralı zaten WordEncounter'daki güncel durumla çalışır.

    ozetle()                 -> {"ozetlenen": n, "gun": k}
    manage.py karsilasma_ozetle [--dry-run]   (cron: günde bir, gece)
"""

from datetime import timedelta

from django.db import transaction
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import EncounterLog, KarsilasmaOzeti

SAKLAMA_GUN = 90


def sinir(simdi=None):
    """Bu andan eski kayıtlar özetlenir."""
    return (simdi or timezone.now()) - timedelta(days=SAKLAMA_GUN)


def eski_kayitlar(simdi=None):
    return EncounterLog.objects.filter(created_at__lt=sinir(simdi))


@transaction.atomic
def ozetle(simdi=None, dry_run=False):
    eski = eski_kayitlar(simdi)
    gruplar = list(eski.annotate(gun=TruncDate("created_at"))
                   .values("gun", "mode", "basamak_once", "verdict")
                   .annotate(n=Count("id")).order_by())
    toplam = sum(g["n"] for g in gruplar)
    if dry_run or not gruplar:
        return {"ozetlenen": toplam, "gun": len({g["gun"] for g in gruplar})}
    for g in gruplar:
        ozet, _ = KarsilasmaOzeti.objects.select_for_update().get_or_create(
            gun=g["gun"], mode=g["mode"] or "", basamak_once=g["basamak_once"],
            verdict=g["verdict"] or "")
        ozet.sayi += g["n"]
        ozet.save(update_fields=["sayi"])
    silinen, _ = eski.delete()
    return {"ozetlenen": silinen, "gun": len({g["gun"] for g in gruplar})}
