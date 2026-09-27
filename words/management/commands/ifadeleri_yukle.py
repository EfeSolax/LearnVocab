# -*- coding: utf-8 -*-
"""
Bağlayıcı ifadeleri ve kalıpları veritabanına yükler (words/ifadeler/veri.py).

    python manage.py ifadeleri_yukle            # yükle / güncelle
    python manage.py ifadeleri_yukle --dry-run  # yalnızca say

Tekrar çalıştırmak güvenli: ifade metnine göre günceller, kopya açmaz.
Aynı ifade iki işlev grubunda geçiyorsa ("while": zaman + karşıtlık) TEK
kayıt olur: ilk grup ana işlev, öteki ek işlev; anlamlar ve örnekler
birleştirilir.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from words.ifadeler import kurallar
from words.ifadeler.veri import EK_YANLIS, GRUPLAR, IFADELER
from words.models import (ExampleKind, Expression, ExpressionExample, ExpressionGroup,
                          ExpressionKind)

BAGLAYICI = {"baglac", "yan_cumle", "cumle_zarfi", "edat", "cift"}


def _tekil(liste):
    goruldu, sonuc = set(), []
    for x in liste:
        anahtar = x if isinstance(x, str) else x[0]
        if anahtar not in goruldu:
            goruldu.add(anahtar)
            sonuc.append(x)
    return sonuc


def birlestir():
    """metin -> birleşik kayıt (gruplar sıralı)."""
    kayitlar = {}
    for grup, liste in IFADELER.items():
        for sira, ifade in enumerate(liste):
            dogru, yanlis = kurallar.dogru_yanlis(ifade)
            k = kayitlar.get(ifade["metin"])
            if k is None:
                kayitlar[ifade["metin"]] = {
                    "ana": ifade, "gruplar": [grup], "sira": sira,
                    "tr": [ifade["tr"]], "ornekler": list(ifade["ornekler"]),
                    "dogru": dogru, "yanlis": yanlis + EK_YANLIS.get(ifade["metin"], []),
                    "kaliplar": [ifade["kalip"]],
                }
            else:
                k["gruplar"].append(grup)
                k["tr"].append(ifade["tr"])
                k["ornekler"] += ifade["ornekler"]
                k["dogru"] += dogru
                k["yanlis"] += yanlis
                k["kaliplar"].append(ifade["kalip"])
    return kayitlar


class Command(BaseCommand):
    help = "Bağlayıcı ifadeleri (veri.py) yükler / günceller."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **s):
        kayitlar = birlestir()
        if s["dry_run"]:
            self.stdout.write(f"{len(GRUPLAR)} işlev grubu · {len(kayitlar)} ifade (yazılmadı)")
            return
        with transaction.atomic():
            gruplar = {}
            for sira, (slug, ad, baslik, aciklama) in enumerate(GRUPLAR):
                gruplar[slug], _ = ExpressionGroup.objects.update_or_create(
                    slug=slug, defaults={"name": ad, "heading": baslik,
                                         "description": aciklama, "sort_order": sira})
            yeni = 0
            for metin, k in kayitlar.items():
                ana = k["ana"]
                tr = "; ".join(_tekil(k["tr"]))[:300]
                ifade, olustu = Expression.objects.update_or_create(
                    text=metin,
                    defaults={
                        "meaning_tr": tr,
                        "definition": ana["en"] or None,
                        "kind": ExpressionKind.LINKER if ana["yapi"] in BAGLAYICI
                        else ExpressionKind.FIXED,
                        "cefr": ana["seviye"],
                        "register": ana["uslup"],
                        "group": gruplar[k["gruplar"][0]],
                        "structure": ana["yapi"],
                        "pattern": " / ".join(_tekil(k["kaliplar"]))[:120],
                        "punctuation_note": kurallar.noktalama_notu(ana),
                        "academic_note": kurallar.akademik_notu(ana)[:300],
                        "sort_order": k["sira"],
                        "visibility": "public",
                        "owner": None,
                    },
                )
                yeni += olustu
                ifade.extra_groups.set([gruplar[g] for g in k["gruplar"][1:]])
                ifade.examples.all().delete()
                satirlar = []
                for i, c in enumerate(_tekil(k["ornekler"])):
                    satirlar.append(ExpressionExample(expression=ifade, text=c,
                                                      kind=ExampleKind.EXAMPLE, sort_order=i))
                for i, c in enumerate(_tekil(k["dogru"])):
                    satirlar.append(ExpressionExample(expression=ifade, text=c,
                                                      kind=ExampleKind.CORRECT, sort_order=100 + i))
                for i, (c, neden) in enumerate(_tekil(k["yanlis"])):
                    satirlar.append(ExpressionExample(expression=ifade, text=c, note=neden[:300],
                                                      kind=ExampleKind.WRONG, sort_order=200 + i))
                ExpressionExample.objects.bulk_create(satirlar)
        self.stdout.write(self.style.SUCCESS(
            f"{len(GRUPLAR)} işlev grubu · {len(kayitlar)} ifade ({yeni} yeni, "
            f"{len(kayitlar) - yeni} güncellendi)"))
