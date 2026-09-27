"""
Kelime şablon süzgeçleri.

    {% load kelime %}
    {{ word.pos|tur_etiketi }}   -> isim, fiil, sıfat, zarf…

Rapor 12.1: gramer (tür) etiketleri YALNIZCA Sözlük kartında gösterilir;
L&P kartlarında ve egzersizlerde kullanılmaz.
"""

from django import template

from words.kart import tur_etiketi as _tur_etiketi

register = template.Library()


@register.filter
def tur_etiketi(pos):
    return _tur_etiketi(pos)
