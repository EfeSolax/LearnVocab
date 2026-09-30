"""
Kelime sayfalarının kalıcı adresi (rapor 18.15): /sozluk/bank/, /sozluk/give-up/

Aynı yazımın bütün türleri (bank isim, bank fiil) TEK sayfadadır; adres
yalnızca yazımdan üretilir. Biçim: küçük harf, ASCII, sözcükler tireyle.

    slug_yap("give up")           -> "give-up"
    slug_yap("o'clock")           -> "o-clock"
    slug_yap("either … or")       -> "either-or"
    kelime_adresi("give up")      -> "/sozluk/give-up/"

Word.slug ve Expression.slug kaydederken bu fonksiyonla doldurulur; sayfa
görünümü (words.sozluk_views.sozluk_kelime) kelimeyi slug'dan bulur.
"""

import re

from django.urls import reverse

_TIRE_OLACAK = re.compile(r"[^a-z0-9]+")


def slug_yap(metin):
    # Türkçe klavye tuzağı: "İ"/"ı" İngilizce kelimede "i" demektir.
    metin = (metin or "").replace("İ", "i").replace("ı", "i").lower()
    return _TIRE_OLACAK.sub("-", metin).strip("-")


def kelime_adresi(metin):
    """Kelimenin ya da ifadenin sayfası; slug çıkmıyorsa (boş, yalnızca işaret) Sözlük."""
    slug = slug_yap(metin)
    return reverse("sozluk_kelime", args=[slug]) if slug else reverse("sozluk")
