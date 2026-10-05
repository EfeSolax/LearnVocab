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


# ---------------------------------------------------------------------------
# Parti 1 (769 tohum, 1.254 yeni kelime). 1.407 anlamın hepsi okundu.
# Not: hat kelimenin sözlükte olup olmadığına büyük-küçük harfe duyarlı baktığı
# için büyük harfe çevrilen kelimelerin (Dutch…) küçük harfli kopyaları ve
# silinen kelimeler yeniden üretildi. kopyalari_sil() bunları temizler; silinen
# kelimeler ara deponun kararlar.json'ına "cikar" olarak da yazılır.

BUYUK_HARFLI_1 = ("Protestant", "Protestantism", "Thanksgiving")

KARSILIK_1 = {
    ("antarctic", "adjective", "antarktika'ya ait"): "Antarktika'ya ait",
    ("antarctic", "noun", "antarktika, güney kutbu bölgesi"): "Antarktika, Güney Kutbu bölgesi",
    ("atheism", "noun", "tanrıya inanmama"): "ateizm, tanrıtanımazlık",
    ("avatar", "noun", "sanaldaki temsilci, karakter"): "avatar, sanal karakter",
    ("bachelor", "noun", "evli olmayan erkek"): "bekâr erkek",
    ("curry", "noun", "baharatlı yemek"): "köri",
    ("ditch", "verb", "havuz kazmak, hendek açmak"): "hendek kazmak",
    ("handicap", "noun", "engel, sakatlık, özür"): "engel, engellilik",
    ("hash", "noun", "diyez, kare simgesi"): "kare işareti (#)",
    ("lynching", "noun", "kamu dışı infaz, linç"): "linç",
    ("manga", "noun", "japon çizgi romanı, manga"): "manga, Japon çizgi romanı",
    ("omega", "noun", "yunan alfabesinin son harfi, ω"): "omega (Yunan alfabesinin son harfi)",
    ("protestant", "adjective", "protestan, protestanlıkla ilgili"): "Protestan",
    ("protestant", "noun", "protestan, protestanlık mezhebine mensup kişi"): "Protestan (kişi)",
    ("protestantism", "noun", "protestanlık"): "Protestanlık",
    ("python", "noun", "programlama dili"): "Python (programlama dili)",
    ("rabbi", "noun", "din adamı, haham"): "haham",
    ("scotch", "noun", "iskoç viskisi"): "İskoç viskisi",
    ("unanimous", "adjective", "hemfikir"): "oybirliğiyle alınan, hemfikir",
    ("valentine", "noun", "sevgili, aşkı"): "sevgili",
    ("yen", "noun", "japon yeni"): "Japon yeni",
    ("whiskey", "noun", "viski, alkolik içki"): "viski",
}

# Silinen anlamlar: (kelime, Türkçe karşılık)
ANLAM_SIL_1 = [
    ("fuzz", "polis"), ("chick", "fıstık, hatun, kız"), ("pea", "küçük yuvarlak nesne"),
    ("puck", "yaramaz peri, muzip cin"), ("panama", "panama"),
    ("crab", "yan yan gitmek, yanlamasına hareket etmek"),
]

# Silinen kelimeler: (kelime, tür ya da None = bütün türler)
KELIME_SIL_1 = [
    ("million", None), ("millionth", None), ("nineteen", None), ("nineteenth", None),
    ("psycho", "adjective"), ("rapist", None), ("prostitute", "verb"), ("reps", None),
    ("non-profit", None), ("ruth", None), ("replicant", None), ("welsh", "verb"),
]


def kopyalari_sil():
    """Aynı türde büyük harfli kaydı olan küçük harfli kopyaları siler."""
    silinen = []
    for w in Word.objects.exclude(text=models_lower("text")):
        for kopya in Word.objects.filter(text=w.text.lower(), pos=w.pos):
            silinen.append((kopya.text, kopya.pos))
            kopya.delete()
    return silinen


def models_lower(alan):
    from django.db.models.functions import Lower
    return Lower(alan)


def uygula_1():
    with transaction.atomic():
        for (kelime, tur, eski), yeni in KARSILIK_1.items():
            Meaning.objects.filter(word__text__iexact=kelime, word__pos=tur, meaning_tr=eski) \
                .update(meaning_tr=yeni)
        for kelime, karsilik in ANLAM_SIL_1:
            Meaning.objects.filter(word__text__iexact=kelime, meaning_tr=karsilik).delete()
        for kelime, tur in KELIME_SIL_1:
            qs = Word.objects.filter(text__iexact=kelime)
            (qs.filter(pos=tur) if tur else qs).delete()
        silinen = kopyalari_sil()
        for yazim in BUYUK_HARFLI_1:
            for w in Word.objects.filter(text__iexact=yazim).exclude(text=yazim):
                w.text = yazim
                w.save(update_fields=["text"])
        # Önceki partinin karşılık düzeltmelerini yeniden üretilen kopyalara da uygula.
        uygula()
    return silinen


# ---------------------------------------------------------------------------
# Parti 2 (769 tohum, 1.112 yeni kelime). 1.234 anlamın hepsi okundu.

BUYUK_HARFLI_2 = ("Torah",)

KARSILIK_2 = {
    ("fraternal", "adjective", "çift yumurta"): "çift yumurta (ikizler için)",
    ("torah", "noun", "tevrat"): "Tevrat",
}

ANLAM_SIL_2 = [
    ("cougar", "genç erkeklerle çıkan olgun kadın"), ("posterior", "arka bölüm, arka kısmı, kalça bölgesi"),
    ("rad", "havalı, süper"), ("mule", "uyuşturucu kaçakçısı, kontraband taşıyıcısı"),
    ("vat", "katma değer vergisi"), ("kite", "karşılıksız çekle dolandırmak"),
    ("birch", "huşla dövmek"), ("gutter", "oluk içine yönlendirmek, akıtmak"),
    ("legate", "vasiyet etmek, miras bırakmak"), ("legate", "görevli olarak göndermek, temsilci olarak atamak"),
]

KELIME_SIL_2 = [
    ("eighteen", None), ("eighteenth", None), ("six", None), ("sixth", None), ("sixteen", None),
    ("sixteenth", None), ("sixfold", None), ("bong", None), ("busty", None), ("butch", None),
    ("adulterer", None), ("adulterous", None), ("autistic", "noun"), ("norm", "verb"), ("mashable", None),
    ("buster", None), ("annal", None), ("ulster", None), ("non-diabetic", None), ("non-narcotic", None),
    ("replicant", None),
]


def uygula_2():
    with transaction.atomic():
        for (kelime, tur, eski), yeni in KARSILIK_2.items():
            Meaning.objects.filter(word__text__iexact=kelime, word__pos=tur, meaning_tr=eski) \
                .update(meaning_tr=yeni)
        for kelime, karsilik in ANLAM_SIL_2:
            Meaning.objects.filter(word__text__iexact=kelime, meaning_tr=karsilik).delete()
        for kelime, tur in KELIME_SIL_2:
            qs = Word.objects.filter(text__iexact=kelime)
            (qs.filter(pos=tur) if tur else qs).delete()
        for yazim in BUYUK_HARFLI_2:
            for w in Word.objects.filter(text__iexact=yazim).exclude(text=yazim):
                w.text = yazim
                w.save(update_fields=["text"])
        silinen = kopyalari_sil()
        uygula_1()
    return silinen


# ---------------------------------------------------------------------------
# Parti 3 (769 tohum, 1.006 yeni kelime). 1.096 anlamın hepsi okundu.

BUYUK_HARFLI_3 = ("Satan", "Moorish")

KARSILIK_3 = {
    ("satan", "noun", "şeytan"): "Şeytan",
    ("moorish", "adjective", "Mağribi Müslümanlara ait"): "Mağribi, Mağriplilere ait",
    ("kosher", "adjective", "yahudi dinine uygun"): "koşer, Yahudi dinine uygun",
    ("quid", "noun", "ingiliz sterlini"): "İngiliz sterlini (gündelik dil)",
}

ANLAM_SIL_3 = [
    ("beater", "döven kimse, saldırgan"), ("domino", "kapüşonlu pelerin"), ("gage", "rehin, teminat, güvence"),
    ("kinky", "cinsel açıdan alışılmadık, fetişist"), ("moor", "mağribi"),
    ("slug", "kafaya dikmek, bir dikişte içmek"), ("snowflake", "aşırı alıngan kimse, çıtkırıldım kimse"),
    ("withholding", "esirgeyen, sakınan, ketum"),
]

KELIME_SIL_3 = [
    ("thirteen", None), ("thirteenth", None), ("fourteen", None), ("fourteenth", None),
    ("fifteen", None), ("fifteenth", None), ("seventeen", None), ("seventeenth", None),
    ("autistic", "noun"), ("norm", "verb"), ("replicant", None), ("airforce", None), ("brownie", None),
    ("circumcise", None), ("uncircumcised", None), ("semen", None), ("midget", None), ("wack", None),
]

CUMLE_3 = {
    ("estrogen", "Estrogen helps girls develop"):
        "Estrogen is one of the hormones that control growth in the human body.",
}


def uygula_3():
    with transaction.atomic():
        for (kelime, tur, eski), yeni in KARSILIK_3.items():
            Meaning.objects.filter(word__text__iexact=kelime, word__pos=tur, meaning_tr=eski) \
                .update(meaning_tr=yeni)
        for kelime, karsilik in ANLAM_SIL_3:
            Meaning.objects.filter(word__text__iexact=kelime, meaning_tr=karsilik).delete()
        for kelime, tur in KELIME_SIL_3:
            qs = Word.objects.filter(text__iexact=kelime)
            (qs.filter(pos=tur) if tur else qs).delete()
        for (kelime, bas), yeni in CUMLE_3.items():
            ExampleSentence.objects.filter(meaning__word__text__iexact=kelime, text__startswith=bas) \
                .update(text=yeni)
        for yazim in BUYUK_HARFLI_3:
            for w in Word.objects.filter(text__iexact=yazim).exclude(text=yazim):
                w.text = yazim
                w.save(update_fields=["text"])
        silinen = kopyalari_sil()
        uygula_2()
    return silinen


# ---------------------------------------------------------------------------
# Parti 4 (766 tohum, 916 yeni kelime). 998 anlamın hepsi okundu.

BUYUK_HARFLI_4 = ("Passover",)

KARSILIK_4 = {
    ("passover", "noun", "hamursuz bayramı, yahudi kutsal bayramı"): "Hamursuz Bayramı (Yahudi bayramı)",
    ("halal", "adjective", "islami kurallara uygun, helal"): "helal, İslami kurallara uygun",
    ("crofting", "noun", "iskoçya'da küçük çiftlikçilik"): "küçük çiftlikçilik (İskoçya)",
    ("greyhound", "noun", "tazı, ingiliz tazısı"): "tazı, İngiliz tazısı",
    ("laird", "noun", "soylu toprak sahibi, iskoç derebeyi"): "soylu toprak sahibi (İskoçya)",
    ("theta", "noun", "yunan alfabesinin sekizinci harfi"): "theta (Yunan alfabesinin sekizinci harfi)",
    ("yak", "noun", "yak, tibet öküzü"): "yak, Tibet öküzü",
    ("vendetta", "noun", "kan davası, intikal eden düşmanlık"): "kan davası, uzun süren düşmanlık",
    ("chaste", "adjective", "namuslu, cinsel açıdan temiz"): "iffetli, namuslu",
    ("chastity", "noun", "iffet, namus, cinsel perhiz"): "iffet, namus",
}

ANLAM_SIL_4 = [
    ("bombshell", "çok çekici, göz alıcı kadın"), ("mow", "yok etmek, sürükleyerek öldürmek"),
    ("nominal", "adıl, isim soylu sözcük, ad öbeği"), ("solicitation", "azmettirme, suça teşvik, fuhşa teşvik"),
    ("swag", "kibirli bir şekilde yürümek, kendinden emin adımlarla dolaşmak"), ("thrashing", "vurma, dövme"),
]

KELIME_SIL_4 = [
    ("anorexic", "noun"), ("brain", "verb"), ("merchandising", "verb"), ("re-choreograph", None),
    ("non-nomadic", None),
]

CUMLE_4 = {
    ("contraceptive", "Many teenagers rely on a contraceptive pill"):
        "The doctor explained the different contraceptive methods during the health class.",
    ("mutilate", "The police found a man who had mutilated"):
        "Vandals mutilated the statue in the park last night.",
}


def uygula_4():
    with transaction.atomic():
        for (kelime, tur, eski), yeni in KARSILIK_4.items():
            Meaning.objects.filter(word__text__iexact=kelime, word__pos=tur, meaning_tr=eski) \
                .update(meaning_tr=yeni)
        for kelime, karsilik in ANLAM_SIL_4:
            Meaning.objects.filter(word__text__iexact=kelime, meaning_tr=karsilik).delete()
        for kelime, tur in KELIME_SIL_4:
            qs = Word.objects.filter(text__iexact=kelime)
            (qs.filter(pos=tur) if tur else qs).delete()
        for (kelime, bas), yeni in CUMLE_4.items():
            ExampleSentence.objects.filter(meaning__word__text__iexact=kelime, text__startswith=bas) \
                .update(text=yeni)
        for yazim in BUYUK_HARFLI_4:
            for w in Word.objects.filter(text__iexact=yazim).exclude(text=yazim):
                w.text = yazim
                w.save(update_fields=["text"])
        silinen = kopyalari_sil()
        uygula_3()
    return silinen
