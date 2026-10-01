"""
Kelime şablon süzgeçleri.

    {% load kelime %}
    {{ word.pos|tur_etiketi }}   -> isim, fiil, sıfat, zarf…
    {{ word.text|kelime_adresi }} -> /sozluk/bank/

Rapor 12.1: gramer (tür) etiketleri YALNIZCA Sözlük kartında gösterilir;
L&P kartlarında ve egzersizlerde kullanılmaz.
"""

from django import template

from words.kart import tur_etiketi as _tur_etiketi

register = template.Library()


@register.filter
def tur_etiketi(pos):
    return _tur_etiketi(pos)


@register.filter
def kelime_adresi(metin):
    """{{ k.text|kelime_adresi }} -> /sozluk/give-up/ (kalıcı kelime sayfası, rapor 18.15)"""
    from words.adres import kelime_adresi as _adres
    return _adres(metin)


@register.simple_tag
def telaffuz_adresi(metin, aksan):
    """
    Üretilmiş telaffuz dosyasının adresi (rapor 18.4); dosya yoksa "".
    {% telaffuz_adresi kart.text "us" as ses_us %}
    """
    import os

    from django.conf import settings

    from words.telaffuz import KLASOR, dosya_adi

    ad = dosya_adi(metin, aksan)
    if not ad or not os.path.exists(os.path.join(settings.MEDIA_ROOT, KLASOR, ad)):
        return ""
    return f"{settings.MEDIA_URL}{KLASOR}/{ad}"


@register.filter
def isaretle(cumle, kelime):
    """
    Örnek cümlede kelimeyi sarı kalemle işaretler (defter teması, rapor 18.12):
    {{ anlam.ornek|isaretle:kart.text }} -> "I visit the <mark class="lv-vurgu">bank</mark>."
    Kelimenin eklerle uzamış hâli de işaretlenir (banks, banking); düzensiz
    biçimler (went) işaretlenmez. Metin önce kaçışlanır, sonra işaretlenir.
    """
    import re

    from django.utils.html import escape
    from django.utils.safestring import mark_safe

    metin = escape(cumle or "")
    if not kelime:
        return mark_safe(metin)
    desen = re.compile(r"\b(" + re.escape(escape(kelime)) + r"[a-z]*)\b", re.IGNORECASE)
    return mark_safe(desen.sub(r'<mark class="lv-vurgu">\1</mark>', metin))
