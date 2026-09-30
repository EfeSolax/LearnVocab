"""
robots.txt ve sitemap.xml (rapor 18.15). Adresler settings.SITE_ADRESI'nden
üretilir (her zaman https://www…), istekteki adresten değil.

Sitemap'e yalnızca DİZİNE AÇIK sayfalar girer:
  - sabit sayfalar (ana sayfa, sözlük, seviye testi, okumalar, hakkında)
  - göz atma sayfalarının ilk sayfaları (/sozluk/seviye/b1/, /sozluk/harf/a/)
  - açılmış kelime ve ifade sayfaları (Word.dizinde / Expression.dizinde)
  - yayındaki hazır listeler ve kütüphane metinleri
50.000 adres sınırının çok altındayız (en çok ~14 bin); tek dosya yeter.
"""

from xml.sax.saxutils import escape

from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

from LearnVocab.seo import tam_adres


@require_GET
@cache_control(public=True, max_age=3600)
def robots_txt(request):
    satirlar = [
        "User-agent: *",
        # Yönetim ve JSON uçları taranmasın. Hesap, çalışmalar ve yazma
        # sayfaları burada KAPATILMAZ: onlar `noindex` taşır ve arama motoru
        # bunu ancak sayfayı açabilirse görür (LearnVocab/seo.py).
        "Disallow: /admin/",
        "Disallow: /api/",
        "Disallow: /*/api/",
        "",
        f"Sitemap: {tam_adres(reverse('sitemap_xml'))}",
        "",
    ]
    return HttpResponse("\n".join(satirlar), content_type="text/plain; charset=utf-8")


def sitemap_yollari():
    """Dizine açık bütün sayfaların yolları: [(yol, son değişiklik ya da None)]."""
    from readings.models import ReadingText
    from words import gozat
    from words.models import Expression, HazirListe, Word

    yollar = [(reverse(ad), None) for ad in ("index", "sozluk", "seviye_testi", "readings", "about")]
    yollar += [(reverse("sozluk_seviye", args=[s.lower()]), None) for s in gozat.dolu_seviyeler()]
    yollar += [(reverse("sozluk_harf", args=[h]), None) for h in gozat.dolu_harfler()]

    sluglar = set(Word.objects.filter(dizinde=True).exclude(slug="").values_list("slug", flat=True))
    sluglar |= set(Expression.objects.filter(dizinde=True, visibility="public")
                   .exclude(slug="").values_list("slug", flat=True))
    yollar += [(reverse("sozluk_kelime", args=[s]), None) for s in sorted(sluglar)]

    yollar += [(reverse("hazir_liste", args=[s]), None)
               for s in HazirListe.objects.filter(yayinda=True).values_list("slug", flat=True)]
    yollar += [(reverse("readings_library_text", args=[slug]), degisti)
               for slug, degisti in ReadingText.objects.exclude(slug__isnull=True)
               .values_list("slug", "updatedAt")]
    return yollar


@require_GET
@cache_control(public=True, max_age=3600)
def sitemap_xml(request):
    parcalar = ['<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n']
    for yol, degisti in sitemap_yollari():
        son = f"<lastmod>{degisti.date().isoformat()}</lastmod>" if degisti else ""
        parcalar.append(f"<url><loc>{escape(tam_adres(yol))}</loc>{son}</url>\n")
    parcalar.append("</urlset>\n")
    return HttpResponse("".join(parcalar), content_type="application/xml; charset=utf-8")
