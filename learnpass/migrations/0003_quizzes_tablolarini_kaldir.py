"""
quizzes uygulamasının tablolarını kaldırır.

quizzes uygulaması tamamen silindi (ürün raporu, Bölüm 14). Uygulama
INSTALLED_APPS'ten çıkınca kendi migration'ları artık çalışmıyor; bu yüzden
tablolar burada, ham SQL ile düşürülüyor. Her ifade IF EXISTS ile yazıldı:
hiç quizzes kurulmamış bir veritabanında (testler, yeni kurulum) hiçbir şey
yapmaz, yarım kalmış bir kurulumda da hata vermez.

Listede yalnızca bugün var olan üç tablo değil, eski sürümlerin tabloları da
var (0015_calisma_modeli onları zaten silmişti ama o migration'ın hiç
çalışmadığı bir ortam kalmışsa temizlensin). Sıra çocuktan ebeveyne:
önce M2M ara tabloları ve FK taşıyan tablolar, en son bağlanılan tablolar.

MySQL'de ek güvence olarak yabancı anahtar denetimi geçici olarak kapatılıyor.
SQLite'ta buna gerek yok: Django migration sırasında SQLite'ın FK
denetimini zaten kapatıyor.

Geri alınamaz: veriler geri gelmez. Geri yönü noop, yani migration geri
sarılabilir ama tabloları yeniden kurmaz.
"""

from django.db import migrations


# Çocuktan ebeveyne.
QUIZZES_TABLOLARI = (
    # Aralıklı tekrar sistemi (0015_calisma_modeli)
    "quizzes_reviewlog",        # -> reviewitem, studysession
    "quizzes_reviewitem",
    "quizzes_studysession",
    # Eski soru tabloları: önce M2M ara tabloları (words), sonra sorular
    "quizzes_matchingquestion_words",
    "quizzes_multiplechoicequestion_words",
    "quizzes_writingquestion_words",
    "quizzes_synonymantonymquestion_words",
    "quizzes_fillintheblankquestion_words",
    "quizzes_matchingquestion",
    "quizzes_multiplechoicequestion",
    "quizzes_writingquestion",
    "quizzes_synonymantonymquestion",
    "quizzes_fillintheblankquestion",
    "quizzes_quizquestion",
    "quizzes_quizattempt",
)


def tablolari_dusur(apps, schema_editor):
    baglanti = schema_editor.connection
    ad = baglanti.ops.quote_name
    mysql = baglanti.vendor == "mysql"

    with baglanti.cursor() as imlec:
        if mysql:
            imlec.execute("SET FOREIGN_KEY_CHECKS = 0")
        try:
            for tablo in QUIZZES_TABLOLARI:
                imlec.execute(f"DROP TABLE IF EXISTS {ad(tablo)}")
        finally:
            if mysql:
                imlec.execute("SET FOREIGN_KEY_CHECKS = 1")


class Migration(migrations.Migration):

    dependencies = [
        ("learnpass", "0002_encounterlog_wordencounter_declaration_and_more"),
    ]

    operations = [
        migrations.RunPython(tablolari_dusur, migrations.RunPython.noop),
    ]
