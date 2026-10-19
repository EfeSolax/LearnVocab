"""
Zorlanan kelimeye 1 birim bekleme (20 Ekim, learnpass/tekrar.py): bundan önce "bilmiyorum"
denen kelimenin sonraki_tekrar'ı boş kalıyor ve hemen aday oluyordu. Mevcut kayıtlara son
görülmeden 1 birim sonrası yazılır (görülme zamanı yoksa şimdi).
"""
from datetime import timedelta

from django.conf import settings
from django.db import migrations
from django.db.models import F
from django.utils import timezone


def bekleme_yaz(apps, schema_editor):
    WordEncounter = apps.get_model("learnpass", "WordEncounter")
    birim = timedelta(hours=getattr(settings, "TEKRAR_BIRIMI_SAAT", 24))
    bos = WordEncounter.objects.filter(son_basarili=False, sonraki_tekrar__isnull=True, times_seen__gt=0)
    bos.filter(last_seen_at__isnull=False).update(sonraki_tekrar=F("last_seen_at") + birim)
    bos.filter(last_seen_at__isnull=True).update(sonraki_tekrar=timezone.now())


class Migration(migrations.Migration):
    dependencies = [("learnpass", "0006_karsilasma_ozeti")]
    operations = [migrations.RunPython(bekleme_yaz, migrations.RunPython.noop)]
