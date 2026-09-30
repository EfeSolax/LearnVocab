"""
Kademeli dizine alma (rapor 18.15, SEO güvenlik kuralı 1).

Bir kelime sayfası arama motorlarına ancak AÇILINCA görünür (Word.dizinde);
açılmayan sayfa `noindex` kalır ve sitemap'e girmez. 16 bin sayfa tek günde
açılmaz; partiler hâlinde, en güvendiğimiz kelimelerden başlanır.

Açılabilmek için (uygun_kelimeler):
  - ortak sözlükte olmalı (kullanıcının özel kelimesi değil),
  - Türkçe anlamı, İngilizce açıklaması ve en az bir örnek cümlesi olmalı,
  - sıklığı EN_AZ_SIKLIK'ın üstünde olmalı (rapor 18.16/5: işe yaramaz
    kayıtlar Google'dan gizlenir).

Bir sayfada aynı yazımın bütün türleri durur (bank isim, bank fiil); türlerden
biri açıksa sayfa açıktır.

Komut: manage.py dizine_ac
"""

from django.db.models import Count, Exists, OuterRef

from .arama import cefr_sira_ifadesi, ortak_sozluk
from .models import ExampleSentence, Expression, Meaning, Word

# Zipf 2,3'ün altı: "handwrite", "pillared" gibi çok seyrek kayıtlar.
EN_AZ_SIKLIK = 2.3


def uygun_kelimeler():
    anlam = Meaning.objects.filter(word=OuterRef("pk")).exclude(meaning_tr="")
    aciklama = anlam.exclude(definition="").exclude(definition__isnull=True)
    ornek = ExampleSentence.objects.filter(meaning__word=OuterRef("pk"))
    return (Word.objects.filter(ortak_sozluk(), siklik__gte=EN_AZ_SIKLIK)
            .exclude(slug="")
            .filter(Exists(aciklama), Exists(ornek)))


def uygun_ifadeler():
    """İfade sayfası: Türkçe anlamı ve en az 2 örneği olanlar (rapor 18.8)."""
    return (Expression.objects.filter(visibility="public").exclude(slug="")
            .exclude(meaning_tr="").annotate(_ornek=Count("examples")).filter(_ornek__gte=2))


def siradaki_kelimeler(seviyeler=None, kaynak=None, en_az_siklik=None):
    """Henüz açılmamış uygun kelimeler: kolay seviye ve sık kelime önce."""
    q = uygun_kelimeler().filter(dizinde=False)
    if seviyeler:
        q = q.filter(cefr__in=seviyeler)
    if kaynak:
        q = q.filter(cefr_kaynak=kaynak)
    if en_az_siklik is not None:
        q = q.filter(siklik__gte=en_az_siklik)
    return q.annotate(_sira=cefr_sira_ifadesi()).order_by("_sira", "-siklik", "text", "pos")


def sayfa_acik_mi(kelimeler, ifadeler=()):
    """Kelime sayfası dizine açık mı? Türlerden ya da ifadelerden biri açıksa evet."""
    return any(k.dizinde for k in kelimeler) or any(i.dizinde for i in ifadeler)
