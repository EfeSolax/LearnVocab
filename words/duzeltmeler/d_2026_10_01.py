# -*- coding: utf-8 -*-
"""
1 Ekim — büyük harf düzeltmesi (rapor 18.16 "Bulgu, büyük harf").

İngilizcede her zaman büyük harfle yazılan milliyet ve dil kelimeleri
veritabanında küçük harfle duruyordu. Okuma ekranının kelime sorgusu
(readings/kelime_sorgu.py) artık büyük-küçük harfe duyarsız olduğu için
yazımları düzeltmek güvenli: "Arabic"e dokunan kullanıcı yine kartı görür.

"oriental" (isim): insanlar için eskimiş ve rahatsız edici bir söz (rapor
12.2, hassas anlam); kişi anlamındaki isim kaydı silinir. Sıfat ("oriental
rug" gibi eşya/sanat kullanımı) kalır.

Çalıştırma:  python manage.py shell -c "from words.duzeltmeler import d_2026_10_01 as d; d.uygula()"
Tekrar çalıştırmak güvenli.
"""
from django.db import transaction

from words.models import Meaning, Word

BUYUK_HARFLI = ("Arab", "Arabian", "Arabic", "Caucasian", "Chinese", "Guinean")


def uygula():
    with transaction.atomic():
        for yazim in BUYUK_HARFLI:
            for w in Word.objects.filter(text__iexact=yazim).exclude(text=yazim):
                w.text = yazim
                w.save(update_fields=["text"])
        Meaning.objects.filter(word__text="Guinean", meaning_tr="gine'ye ait, gineli") \
            .update(meaning_tr="Gine'ye ait, Gineli")
        Meaning.objects.filter(word__text="Caucasian", meaning_tr="kafkas kökenli, beyaz tenli") \
            .update(meaning_tr="Kafkas kökenli, beyaz tenli")
        Word.objects.filter(text="oriental", pos="noun").delete()
