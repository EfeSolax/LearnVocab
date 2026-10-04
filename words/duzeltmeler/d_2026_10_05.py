# -*- coding: utf-8 -*-
"""
5 Ekim — genişletme partisi 0'ın (200 tohum, 310 yeni kelime; rapor 18.35)
Claude denetimi. Yeni eklenen 342 anlamın hepsi okundu.

- Milliyet, dil ve bayram adları İngilizcede büyük harfle (1 Ekim kuralı):
  Dutch, German, Swiss, Easter, Catholicism. Türkçe karşılıklardaki özel
  adlar da büyük harfle (Hollandalı, Almanca, İsviçreli, Paskalya, İncil…).
- Zayıf ya da yanlış karşılıklar düzeltildi (chancellor "devlet başkanı"
  değil; furtherance "ileri sürme" değil …).
- Silinenler: fin'in argo "beş dolar" anlamı; welsh (fiil, "borçtan kaçmak":
  etnik aşağılama kökenli); replicant (bilimkurgu terimi, öğrenciye yük).
- Öğrenciye uygun olmayan iki örnek cümle (uyuşturucu, alkol) değiştirildi.

Çalıştırma:  python manage.py shell -c "from words.duzeltmeler import d_2026_10_05 as d; d.uygula()"
Tekrar çalıştırmak güvenli.
"""
from django.db import transaction

from words.models import ExampleSentence, Meaning, Word

BUYUK_HARFLI = ("Dutch", "German", "Swiss", "Easter", "Catholicism")

# (kelime, tür, eski karşılık) -> yeni karşılık
KARSILIK = {
    ("dutch", "adjective", "hollanda'ya ait, hollandalı"): "Hollanda'ya ait, Hollandalı",
    ("dutch", "noun", "hollandaca, felemenkçe"): "Hollandaca, Felemenkçe",
    ("german", "adjective", "alman"): "Alman, Almanya'ya ait",
    ("german", "noun", "alman"): "Alman (kişi)",
    ("german", "noun", "almanca"): "Almanca",
    ("swiss", "adjective", "isviçreli, isviçre"): "İsviçre'ye ait, İsviçreli",
    ("swiss", "noun", "isviçreli, isviçre vatandaşı"): "İsviçreli",
    ("easter", "noun", "paskalya, hristiyanların kutladığı bahar bayramı"): "Paskalya",
    ("catholic", "adjective", "katolik, Katolik Kilisesine ait"): "Katolik, Katolik Kilisesi'ne ait",
    ("catholicism", "noun", "katoliklik, katolik din"): "Katoliklik",
    ("mercury", "noun", "merkür, gezegen"): "Merkür (gezegen)",
    ("mercury", "noun", "cıva, metal"): "cıva",
    ("gospel", "noun", "incil"): "İncil",
    ("anime", "noun", "japon animasyonu, çizgi film"): "anime, Japon çizgi filmi",
    ("chancellor", "noun", "başbakan, devlet başkanı"): "başbakan (Almanya, Avusturya)",
    ("furtherance", "noun", "ileri sürme, destekleme, ilerletme"): "ilerletme, destekleme",
    ("axiom", "noun", "kabul edilen ilke"): "aksiyom, belit",
    ("ought", "verb", "gerekmek, zorunda olmak, -meli/-malı"): "-meli, -malı (tavsiye, görev)",
    ("whereas", "conjunction", "öte yandan, iken"): "oysa, -iken",
    ("posting", "noun", "gönderme, ilan"): "gönderi, ilan",
    ("compact", "adjective", "küçük, sıkışık, dar"): "küçük ve derli toplu, kompakt",
    ("aerosol", "noun", "havada asılı ince damlacıklar, sprey"): "aerosol, sprey",
    ("exponential", "adjective", "üst üste artan, katlanarak artan"): "üstel, katlanarak artan",
    ("incumbent", "adjective", "zorunlu"): "(birine) düşen, görevi olan",
}

# (kelime, eski cümlenin başı) -> yeni cümle
CUMLE = {
    ("marijuana", "Many students experiment with marijuana"):
        "Some countries allow doctors to prescribe marijuana for chronic pain.",
    ("undiluted", "She served the cocktail with undiluted vodka"):
        "The label warns that the cleaning liquid should never be used undiluted.",
}


def uygula():
    with transaction.atomic():
        for (kelime, tur, eski), yeni in KARSILIK.items():
            Meaning.objects.filter(word__text__iexact=kelime, word__pos=tur, meaning_tr=eski) \
                .update(meaning_tr=yeni)
        for yazim in BUYUK_HARFLI:
            for w in Word.objects.filter(text__iexact=yazim).exclude(text=yazim):
                w.text = yazim
                w.save(update_fields=["text"])
        for (kelime, bas), yeni in CUMLE.items():
            ExampleSentence.objects.filter(meaning__word__text__iexact=kelime, text__startswith=bas) \
                .update(text=yeni)
        Meaning.objects.filter(word__text="fin", meaning_tr="beş dolar").delete()
        Word.objects.filter(text="welsh", pos="verb").delete()
        Word.objects.filter(text="replicant").delete()
