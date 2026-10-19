"""
Göz atma sayfaları (rapor 18.15): /sozluk/seviye/b1/, /sozluk/harf/a/

Arama kutusu olmadan da bütün kelimelere bağlantıyla ulaşılabilsin diye
(arama motoru kelime sayfalarını buradan bulur, kullanıcı seviyesindeki
kelimelere göz atar). SEO güvenlik kuralı 2: sayfalı, ve her satırda anlam
var ("carpet · isim · halı · B1"); yalnızca bağlantı listesi değil.

Çok seyrek kayıtlar (Zipf < 2,3) burada listelenmez.
"""

import string
import sys

from django.core.cache import cache
from django.db.models.functions import Substr

from .arama import ortak_sozluk
from .dizine_alma import EN_AZ_SIKLIK
from .models import CEFR_LEVELS, Word

SAYFA_BOYU = 100
HARFLER = tuple(string.ascii_lowercase)


def _temel():
    return Word.objects.filter(ortak_sozluk(), siklik__gte=EN_AZ_SIKLIK).exclude(slug="")


def seviye_kelimeleri(seviye):
    # Az kullanılanların seviyesi yok sayılır (Word.az_kullanilan); harfe göre göz atmada ve aramada durur
    return _temel().filter(cefr=seviye, az_kullanilan=False).order_by("text", "pos")


def harf_kelimeleri(harf):
    return _temel().filter(text__istartswith=harf).order_by("text", "pos")


# Sekmeler ve harfler her Sözlük/seviye sayfasında hesaplanır. order_by() şart: modelin varsayılan
# sıralaması (text, pos) DISTINCT'e karışınca MySQL 22 bin satırı ayıklıyordu (canlıda 0,25 sn x 2;
# 17 Ekim). Sonuç neredeyse hiç değişmez: bir saat önbellekte (testlerde değil: her test kendi verisini kurar).
_SURE = 0 if "test" in sys.argv else 3600
def dolu_seviyeler():
    def hesapla():
        return set(_temel().filter(az_kullanilan=False).order_by().values_list("cefr", flat=True).distinct())
    dolu = (hesapla() if not _SURE else cache.get_or_set("gozat:dolu_seviyeler", hesapla, _SURE))
    return [s for s in CEFR_LEVELS if s in dolu]


def dolu_harfler():
    def hesapla():
        return set(_temel().order_by().annotate(h=Substr("slug", 1, 1)).values_list("h", flat=True).distinct())
    dolu = (hesapla() if not _SURE else cache.get_or_set("gozat:dolu_harfler", hesapla, _SURE))
    return [h for h in HARFLER if h in dolu]
