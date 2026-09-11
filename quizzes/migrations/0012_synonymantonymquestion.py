from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0011_matchingquestion_correct_matches_and_more'),
        ('words', '0012_word_synonyms_antonyms'),
    ]

    operations = [
        # QuizType alanına 'synonym_antonym' seçeneği eklendi (CharField olduğu için migration gerekmez,
        # ama tutarlılık açısından burada belirtiyoruz)
        migrations.AlterField(
            model_name='quizattempt',
            name='quizType',
            field=models.CharField(
                choices=[
                    ('matching', 'Eşleştirme'),
                    ('multiple_choice', 'Çoktan Seçmeli'),
                    ('writing', 'Yazma'),
                    ('mixed', 'Karma'),
                    ('random', 'Rastgele'),
                    ('synonym_antonym', 'Eş/Zıt Anlamlı'),
                ],
                default='mixed',
                max_length=20,
            ),
        ),
        # SynonymAntonymQuestion tablosu oluşturuluyor
        migrations.CreateModel(
            name='SynonymAntonymQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_answer', models.CharField(blank=True, max_length=250, null=True)),
                ('is_correct', models.BooleanField(default=False)),
                ('time_taken', models.FloatField(blank=True, help_text='Süreyi saniye cinsinden saklar', null=True)),
                ('question_text', models.CharField(max_length=400)),
                ('options_data', models.TextField(max_length=500)),
                ('correct_option', models.CharField(max_length=1)),
                ('attempt', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='synonymantonymquestion_questions',
                    to='quizzes.quizattempt',
                )),
                ('words', models.ManyToManyField(
                    related_name='synonymantonymquestion_quiz_questions',
                    to='words.word',
                )),
            ],
            options={
                'ordering': ['id'],
                'abstract': False,
            },
        ),
    ]
