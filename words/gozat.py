"""
Göz atma sayfaları (rapor 18.15): /sozluk/seviye/b1/, /sozluk/harf/a/

Arama kutusu olmadan da bütün kelimelere bağlantıyla ulaşılabilsin diye
(arama motoru kelime sayfalarını buradan bulur, kullanıcı seviyesindeki
kelimelere göz atar). SEO güvenlik kuralı 2: sayfalı, ve her satırda anlam
var ("carpet · isim · halı · B1"); yalnızca bağlantı listesi değil.

Çok seyrek kayıtlar (Zipf < 2,3) burada listelenmez.
"""

import string

from .arama import ortak_sozluk
from .dizine_alma import EN_AZ_SIKLIK
from .models import CEFR_LEVELS, Word

SAYFA_BOYU = 100
HARFLER = tuple(string.ascii_lowercase)


def _temel():
    return Word.objects.filter(ortak_sozluk(), siklik__gte=EN_AZ_SIKLIK).exclude(slug="")


def seviye_kelimeleri(seviye):
    return _temel().filter(cefr=seviye).order_by("text", "pos")


def harf_kelimeleri(harf):
    return _temel().filter(text__istartswith=harf).order_by("text", "pos")


def dolu_seviyeler():
    dolu = set(_temel().values_list("cefr", flat=True).distinct())
    return [s for s in CEFR_LEVELS if s in dolu]


def dolu_harfler():
    dolu = {(slug or " ")[0] for slug in _temel().values_list("slug", flat=True).distinct()}
    return [h for h in HARFLER if h in dolu]
