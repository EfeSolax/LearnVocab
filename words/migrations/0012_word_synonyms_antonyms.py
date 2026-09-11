from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('words', '0011_wordlist'),
    ]

    operations = [
        migrations.AddField(
            model_name='word',
            name='synonyms',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='word',
            name='antonyms',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
