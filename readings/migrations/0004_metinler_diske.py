"""
Kullanıcı metinlerinin gövdesi veritabanından diske taşınır (rapor 18.24).
Sıra: dosya alanı eklenir -> var olan gövdeler sıkıştırılıp dosyaya yazılır
-> body sütunu silinir.
"""

from django.db import migrations, models


def govdeleri_diske_yaz(apps, schema_editor):
    from readings import depo
    UserText = apps.get_model("readings", "UserText")
    for metin in UserText.objects.all().iterator():
        metin.dosya = depo.yeni_ad(metin.owner_id)
        depo.yaz(metin.dosya, metin.body)
        metin.save(update_fields=["dosya"])


def govdeleri_geri_al(apps, schema_editor):
    from readings import depo
    UserText = apps.get_model("readings", "UserText")
    for metin in UserText.objects.exclude(dosya="").iterator():
        metin.body = depo.oku(metin.dosya)
        metin.save(update_fields=["body"])


class Migration(migrations.Migration):

    dependencies = [
        ('readings', '0003_adres_ve_dizin'),
    ]

    operations = [
        migrations.AddField(
            model_name='usertext',
            name='dosya',
            field=models.CharField(blank=True, default='', editable=False, max_length=80),
        ),
        migrations.RunPython(govdeleri_diske_yaz, govdeleri_geri_al),
        migrations.RemoveField(
            model_name='usertext',
            name='body',
        ),
    ]
