"""
Anlam katmanı.

Kelime ≠ anlam: ton, üslup, alan, collocation, kalıp ve örnek cümleler
artık `Word`'e değil `Meaning`'e bağlı. Ayrıca seviye CEFR'e döndü,
deyimler (`Expression`), yanlış dostlar (`FalseFriend`) ve kullanıcının
kendi eklediği anlamlar (`UserMeaning`) eklendi.

DİKKAT: mevcut örnek cümleler siliniyor — hangi cümlenin hangi anlama ait
olduğu eski veriden çıkarılamıyor. `seed_words` ile yeniden üretilir.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

def kur_seviyesini_cefr_e_esle(apps, schema_editor):
    """
    101–501 (ODTÜ kuru) -> A1–C1 (CEFR).

    Seviye artık kurun kendisi değil, kelimenin zorluğu. Kur üyeliği
    kelimenin bir özelliği olmaktan çıkıp kelimeye takılan bir liste
    etiketine dönüşecek; bu eşleme yalnızca elde bir şey kalmasın diye var.
    """
    Word = apps.get_model("words", "Word")
    for kur, cefr in (("101", "A1"), ("201", "A2"), ("301", "B1"),
                      ("401", "B2"), ("501", "C1")):
        Word.objects.filter(wordLevel=kur).update(cefr=cefr)

def geri_esle(apps, schema_editor):
    Word = apps.get_model("words", "Word")
    for kur, cefr in (("101", "A1"), ("201", "A2"), ("301", "B1"),
                      ("401", "B2"), ("501", "C1")):
        Word.objects.filter(cefr=cefr).update(wordLevel=kur)

def cumleleri_temizle(apps, schema_editor):
    """
    Örnek cümleler kelimeden ANLAMA taşınıyor.

    Hangi cümlenin hangi anlama ait olduğunu eski veriden çıkarmanın bir
    yolu yok (`bank`ın beş cümlesi iki anlama karışık dağılmış durumda),
    o yüzden cümleler siliniyor ve seed/AI tarafından yeniden üretiliyor.
    """
    apps.get_model("words", "ExampleSentence").objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('words', '0015_word_family_core'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='word',
            name='cefr',
            field=models.CharField(choices=[('Belirtilmemiş', 'Belirtilmemiş'), ('A1', 'A1 — Başlangıç'), ('A2', 'A2 — Temel'), ('B1', 'B1 — Orta öncesi'), ('B2', 'B2 — Orta'), ('C1', 'C1 — Orta üstü'), ('C2', 'C2 — İleri')], default='Belirtilmemiş', max_length=15, verbose_name='seviye'),
        ),
        migrations.RunPython(kur_seviyesini_cefr_e_esle, geri_esle),
        migrations.RemoveField(
            model_name='word',
            name='wordLevel',
        ),
        migrations.RunPython(cumleleri_temizle, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='examplesentence',
            name='word',
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True)),
                ('slug', models.SlugField(max_length=80, unique=True)),
            ],
            options={
                'verbose_name_plural': 'categories',
                'ordering': ('name',),
            },
        ),
        migrations.AddField(
            model_name='examplesentence',
            name='meaning',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='examples', to='words.meaning'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='meaning',
            name='register',
            field=models.CharField(choices=[('neutral', 'nötr'), ('formal', 'resmî'), ('academic', 'akademik'), ('informal', 'gündelik'), ('slang', 'argo'), ('literary', 'edebî')], default='neutral', max_length=12, verbose_name='üslup'),
        ),
        migrations.AddField(
            model_name='meaning',
            name='sentiment',
            field=models.CharField(choices=[('neutral', 'nötr'), ('positive', 'olumlu'), ('negative', 'olumsuz')], default='neutral', max_length=12, verbose_name='ton'),
        ),
        migrations.AddField(
            model_name='word',
            name='frequency_rank',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='yaygınlık sırası'),
        ),
        migrations.AlterField(
            model_name='wordrelation',
            name='type',
            field=models.CharField(choices=[('synonym', 'eş anlamlı'), ('antonym', 'zıt anlamlı'), ('simpler', 'daha basit karşılığı'), ('confused_with', 'karıştırılan')], max_length=16),
        ),
        migrations.AddField(
            model_name='meaning',
            name='categories',
            field=models.ManyToManyField(blank=True, related_name='meanings', to='words.category', verbose_name='alanlar'),
        ),
        migrations.CreateModel(
            name='Expression',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=200, unique=True)),
                ('meaning_tr', models.CharField(max_length=300, verbose_name='anlamı')),
                ('definition', models.CharField(blank=True, max_length=600, null=True, verbose_name='açıklaması')),
                ('kind', models.CharField(choices=[('idiom', 'deyim'), ('fixed', 'kalıp ifade'), ('proverb', 'atasözü'), ('linker', 'bağlayıcı ifade'), ('other', 'diğer')], default='fixed', max_length=12, verbose_name='türü')),
                ('cefr', models.CharField(choices=[('Belirtilmemiş', 'Belirtilmemiş'), ('A1', 'A1 — Başlangıç'), ('A2', 'A2 — Temel'), ('B1', 'B1 — Orta öncesi'), ('B2', 'B2 — Orta'), ('C1', 'C1 — Orta üstü'), ('C2', 'C2 — İleri')], default='Belirtilmemiş', max_length=15, verbose_name='seviye')),
                ('sentiment', models.CharField(choices=[('neutral', 'nötr'), ('positive', 'olumlu'), ('negative', 'olumsuz')], default='neutral', max_length=12, verbose_name='ton')),
                ('register', models.CharField(choices=[('neutral', 'nötr'), ('formal', 'resmî'), ('academic', 'akademik'), ('informal', 'gündelik'), ('slang', 'argo'), ('literary', 'edebî')], default='neutral', max_length=12, verbose_name='üslup')),
                ('visibility', models.CharField(choices=[('public', 'Herkese Açık'), ('private', 'Gizli')], default='private', max_length=10)),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
                ('categories', models.ManyToManyField(blank=True, related_name='expressions', to='words.category')),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='expressions', to=settings.AUTH_USER_MODEL)),
                ('saved_by', models.ManyToManyField(blank=True, related_name='saved_expressions', to=settings.AUTH_USER_MODEL)),
                ('words', models.ManyToManyField(blank=True, related_name='expressions', to='words.word')),
            ],
            options={
                'ordering': ('text',),
            },
        ),
        migrations.CreateModel(
            name='ExpressionExample',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=400)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('expression', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='examples', to='words.expression')),
            ],
            options={
                'ordering': ('sort_order', 'id'),
            },
        ),
        migrations.CreateModel(
            name='UserMeaning',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meaning_tr', models.CharField(max_length=300, verbose_name='anlamı')),
                ('definition', models.CharField(blank=True, max_length=600, null=True, verbose_name='açıklaması')),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
                ('updatedAt', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='word_meanings', to=settings.AUTH_USER_MODEL)),
                ('word', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_meanings', to='words.word')),
            ],
            options={
                'ordering': ('createdAt', 'id'),
            },
        ),
        migrations.CreateModel(
            name='Collocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pattern', models.CharField(max_length=200, verbose_name='yapı')),
                ('kind', models.CharField(choices=[('verb_noun', 'fiil + isim'), ('adj_noun', 'sıfat + isim'), ('noun_noun', 'isim + isim'), ('adv_adj', 'zarf + sıfat'), ('adv_verb', 'zarf + fiil'), ('other', 'diğer')], default='other', max_length=16, verbose_name='türü')),
                ('meaning_tr', models.CharField(blank=True, max_length=200, null=True, verbose_name='Türkçesi')),
                ('example', models.CharField(blank=True, max_length=400, null=True, verbose_name='örnek cümle')),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('meaning', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collocations', to='words.meaning')),
            ],
            options={
                'ordering': ('sort_order', 'id'),
                'unique_together': {('meaning', 'pattern')},
            },
        ),
        migrations.CreateModel(
            name='FalseFriend',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('turkish_lookalike', models.CharField(max_length=100, verbose_name='benzediği Türkçe kelime')),
                ('assumed_meaning', models.CharField(blank=True, max_length=200, null=True, verbose_name='sanılan anlam')),
                ('correct_english', models.CharField(blank=True, max_length=200, null=True, verbose_name='o anlam için doğru kelime')),
                ('note', models.CharField(blank=True, max_length=400, null=True)),
                ('word', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='false_friends', to='words.word')),
            ],
            options={
                'ordering': ('turkish_lookalike',),
                'unique_together': {('word', 'turkish_lookalike')},
            },
        ),
        migrations.CreateModel(
            name='UsagePattern',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pattern', models.CharField(max_length=200, verbose_name='kalıp')),
                ('kind', models.CharField(choices=[('preposition', 'bağımlı edat'), ('verb_form', 'fiil kalıbı'), ('clause', 'yan cümle kalıbı'), ('structure', 'yapı'), ('other', 'diğer')], default='other', max_length=16, verbose_name='türü')),
                ('example', models.CharField(blank=True, max_length=400, null=True, verbose_name='örnek cümle')),
                ('note', models.CharField(blank=True, max_length=300, null=True, verbose_name='not')),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('meaning', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='patterns', to='words.meaning')),
            ],
            options={
                'ordering': ('sort_order', 'id'),
                'unique_together': {('meaning', 'pattern')},
            },
        ),
    ]
