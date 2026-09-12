"""
Kelime çekirdeğinin yeniden kurulması.

Eski `Word` her şeyi tek satıra tıkıştırıyordu (anlam, 10 cümle kolonu,
virgüllü eş/zıt anlamlılar). Yerine dört katman geliyor:
WordFamily -> Word -> Meaning / ExampleSentence / WordForm, artı kullanıcı
katmanı (UserWordNote, UserExampleSentence).

NOT: Bu migration mevcut kelime verisini SİLER. Bu bilinçli bir karar —
sözlük verisi listelerden ve AI ile yeniden üretilebilir durumda, oysa
eski satırları yeni yapıya dönüştürmek modele taviz verdirirdi.
Yeniden doldurmak için: `python manage.py seed_words`
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def eski_kelimeleri_sil(apps, schema_editor):
    """
    Yeni kolonlar zorunlu (family, text) olduğu için önce tabloyu
    boşaltıyoruz. Kelimeye bağlı kullanıcı kayıtları da CASCADE ile gider.
    """
    Word = apps.get_model("words", "Word")
    Word.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("words", "0014_word_examplesentence10_word_examplesentence4_and_more"),
    ]

    operations = [
        migrations.RunPython(eski_kelimeleri_sil, migrations.RunPython.noop),

        # --- Yeni çekirdek tablolar ---
        migrations.CreateModel(
            name="WordFamily",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("root", models.CharField(max_length=100, unique=True)),
                ("note", models.CharField(blank=True, max_length=500, null=True)),
                ("createdAt", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ("root",), "verbose_name_plural": "word families"},
        ),

        # --- Eski Word alanlarını kaldır ---
        migrations.RemoveField(model_name="word", name="englishWord"),
        migrations.RemoveField(model_name="word", name="explanation"),
        migrations.RemoveField(model_name="word", name="note"),
        migrations.RemoveField(model_name="word", name="prefix"),
        migrations.RemoveField(model_name="word", name="isVerb"),
        migrations.RemoveField(model_name="word", name="meaningTr"),
        migrations.RemoveField(model_name="word", name="synonyms"),
        migrations.RemoveField(model_name="word", name="antonyms"),
        migrations.RemoveField(model_name="word", name="collocations"),
        migrations.RemoveField(model_name="word", name="span"),
        *[
            migrations.RemoveField(model_name="word", name=f"exampleSentence{i}")
            for i in range(1, 11)
        ],

        # --- Yeni Word alanları ---
        migrations.AddField(
            model_name="word",
            name="text",
            field=models.CharField(default="", max_length=120),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="word",
            name="pos",
            field=models.CharField(
                choices=[("noun", "isim"), ("verb", "fiil"), ("adjective", "sıfat"),
                         ("adverb", "zarf"), ("phrasal_verb", "phrasal verb"),
                         ("preposition", "edat"), ("conjunction", "bağlaç")],
                default="noun", max_length=20, verbose_name="tür"),
        ),
        migrations.AddField(
            model_name="word",
            name="family",
            field=models.ForeignKey(default=None,
                                    on_delete=django.db.models.deletion.CASCADE,
                                    related_name="words", to="words.wordfamily"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="word",
            name="base_verb",
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="phrasal_verbs", to="words.word"),
        ),
        migrations.AlterField(
            model_name="word",
            name="v2Form",
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.AlterField(
            model_name="word",
            name="v3Form",
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.AlterField(
            model_name="word",
            name="visibility",
            field=models.CharField(choices=[("public", "Herkese Açık"), ("private", "Gizli")],
                                   default="private", max_length=10),
        ),
        migrations.AlterModelOptions(
            name="word", options={"ordering": ("text", "pos")},
        ),
        migrations.AlterUniqueTogether(name="word", unique_together={("text", "pos")}),
        migrations.AddIndex(
            model_name="word",
            index=models.Index(fields=["text"], name="words_word_text_c757ab_idx"),
        ),
        migrations.AddIndex(
            model_name="word",
            index=models.Index(fields=["family", "text"], name="words_word_family__1b1f79_idx"),
        ),

        # --- Anlam / cümle / biçim / bağ ---
        migrations.CreateModel(
            name="Meaning",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("meaning_tr", models.CharField(max_length=300, verbose_name="anlamı")),
                ("definition", models.CharField(blank=True, max_length=600, null=True,
                                                verbose_name="açıklaması")),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("word", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="meanings", to="words.word")),
            ],
            options={"ordering": ("sort_order", "id")},
        ),
        migrations.CreateModel(
            name="ExampleSentence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("text", models.CharField(max_length=400)),
                ("source", models.CharField(blank=True, max_length=120, null=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("word", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="examples", to="words.word")),
            ],
            options={"ordering": ("sort_order", "id")},
        ),
        migrations.CreateModel(
            name="WordForm",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("surface", models.CharField(db_index=True, max_length=120)),
                ("kind", models.CharField(
                    choices=[("plural", "çoğul"), ("third_person", "3. tekil (-s)"),
                             ("past", "2. hâl"), ("past_participle", "3. hâl"),
                             ("present_participle", "-ing hâli"),
                             ("comparative", "karşılaştırma (-er)"),
                             ("superlative", "en üstünlük (-est)"), ("other", "diğer")],
                    default="other", max_length=24)),
                ("word", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="forms", to="words.word")),
            ],
            options={"ordering": ("surface",), "unique_together": {("word", "surface")}},
        ),
        migrations.CreateModel(
            name="WordRelation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("type", models.CharField(
                    choices=[("synonym", "eş anlamlı"), ("antonym", "zıt anlamlı"),
                             ("simpler", "daha basit karşılığı")], max_length=12)),
                ("note", models.CharField(blank=True, max_length=200, null=True)),
                ("from_word", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                related_name="relations_from", to="words.word")),
                ("to_word", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name="relations_to", to="words.word")),
            ],
            options={"unique_together": {("from_word", "to_word", "type")}},
        ),

        # --- Kullanıcı katmanı ---
        migrations.CreateModel(
            name="UserWordNote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("note", models.TextField(max_length=800)),
                ("createdAt", models.DateTimeField(auto_now_add=True)),
                ("updatedAt", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="word_notes",
                                           to=settings.AUTH_USER_MODEL)),
                ("word", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="user_notes", to="words.word")),
            ],
            options={"unique_together": {("user", "word")}},
        ),
        migrations.CreateModel(
            name="UserExampleSentence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("sentence", models.CharField(max_length=400)),
                ("createdAt", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="word_examples",
                                           to=settings.AUTH_USER_MODEL)),
                ("word", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="user_examples", to="words.word")),
            ],
            options={"ordering": ("createdAt",)},
        ),

        migrations.AlterModelOptions(name="wordlist", options={"ordering": ("name",)}),
        migrations.AlterUniqueTogether(name="wordlist", unique_together={("owner", "name")}),
    ]
