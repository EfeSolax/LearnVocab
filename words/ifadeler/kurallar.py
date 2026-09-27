# -*- coding: utf-8 -*-
"""
Noktalama kuralları ve doğru/yanlış örnekler — ifadenin YAPISINA göre üretilir.

Noktalama kuralı anlamdan değil dilbilgisel görevden gelir: "but" ile
"however" aynı anlama gelir ama biri bağlaç, öteki bağlayıcı zarftır ve
virgülleri farklıdır. Her ifadenin ilk örnek cümlesi yapısının tipik
kalıbında yazıldı (bkz. veri.py); doğru/yanlış örnekler oradan türetilir.
veri.py'deki elle yazılmış "nokta" ve "yanlis" her zaman önceliklidir.
"""

import re

KURAL = {
    "cumle_zarfi": (
        "Cümle başında kullanılır ve ARDINDAN VİRGÜL gelir. İki tam cümleyi tek cümlede "
        "bağlayacaksa ÖNÜNE NOKTALI VİRGÜL, ARDINA VİRGÜL konur (…; however, …). Cümle "
        "ortasında iki virgül arasında da kullanılabilir. İki tam cümleyi yalnızca virgülle "
        "bağlayamaz."),
    "baglac": (
        "İki tam cümleyi bağlarken ÖNÜNE VİRGÜL konur, ardına konmaz. Kelimeleri ya da kısa "
        "öbekleri bağlarken virgül gerekmez. Resmî ve akademik yazıda cümle başında kullanmaktan "
        "kaçının."),
    "yan_cumle": (
        "Yan cümle BAŞTA ise sonuna VİRGÜL konur (Although …, …). Yan cümle SONDA ise genellikle "
        "virgül gerekmez (… although …). Yan cümle tek başına bir cümle olamaz; nokta ile ayrılmaz."),
    "edat": (
        "Ardından İSİM, zamir ya da fiilin -ING hali gelir; TAM BİR CÜMLE (özne + fiil) gelmez. "
        "Cümle başında kullanılırsa öbeğin sonuna virgül konur; cümle sonunda genellikle virgül "
        "gerekmez."),
    "cift": (
        "İki parçalı bir yapıdır; iki kısım aynı dilbilgisel yapıda olmalıdır (paralellik)."),
    "ifade": (
        "Özel bir noktalama kuralı yoktur. Cümle başında kullanılıp cümlenin geri kalanını "
        "nitelediğinde ardından virgül konması yaygındır."),
}

AKADEMIK = {
    "academic": "Akademik yazıda sık kullanılır.",
    "formal": "Resmî bir ifadedir; akademik yazıya uygundur.",
    "neutral": "Hem konuşmada hem yazıda kullanılır.",
    "informal": "Gündelik konuşma dilidir; akademik yazıda kaçının.",
}

KARSITLIK_IKILISI = {"although", "though", "even though"}


def _buyuk(s):
    return s[:1].upper() + s[1:]


def dogru_yanlis(ifade):
    """
    Döner: (doğru örnekler [metin], yanlış örnekler [(metin, neden)]).
    """
    metin, yapi = ifade["metin"], ifade["yapi"]
    ilk = ifade["ornekler"][0] if ifade["ornekler"] else ""
    dogru, yanlis = list(ifade["dogru"]), list(ifade["yanlis"])

    if yapi == "cumle_zarfi":
        # "Cümle. However, cümle."  ->  "Cümle; however, cümle."  /  "Cümle, however cümle."
        m = re.match(rf"^(.+?)\. ({re.escape(_buyuk(metin))}), (.+)$", ilk)
        if m:
            once, _, sonra = m.groups()
            dogru += [ilk, f"{once}; {metin}, {sonra}"]
            yanlis.append((f"{once}, {metin} {sonra}",
                           "İki tam cümle yalnızca virgülle bağlanamaz (comma splice). Nokta ya da "
                           "noktalı virgül kullanın ve ifadeden sonra virgül koyun."))
        elif ilk.startswith(_buyuk(metin) + ","):
            dogru.append(ilk)
            yanlis.append((ilk.replace(_buyuk(metin) + ",", _buyuk(metin), 1),
                           "Cümle başındaki bağlayıcı ifadeden sonra virgül konur."))
    elif yapi == "baglac":
        # "Cümle, but cümle."  ->  "Cümle but, cümle."
        m = re.match(rf"^(.+?), ({re.escape(metin)}) (.+)$", ilk)
        if m:
            once, _, sonra = m.groups()
            dogru.append(ilk)
            yanlis.append((f"{once} {metin}, {sonra}",
                           "Virgül bağlaçtan ÖNCE gelir, sonra değil."))
            if metin in ("but", "and", "so", "or"):
                yanlis.append((f"{once}. {_buyuk(metin)}, {sonra}",
                               "Akademik yazıda cümle bağlaçla başlatılmaz; bağlaçtan sonra da "
                               "virgül konmaz. Örn. “However,” / “Therefore,” kullanın."))
    elif yapi == "yan_cumle":
        # "Although cümle, cümle."  ->  "Although cümle. Cümle."
        if ilk.startswith(_buyuk(metin.split(" …")[0]) + " ") and ", " in ilk:
            yan, ana = ilk.split(", ", 1)
            dogru.append(ilk)
            if len(ifade["ornekler"]) > 1 and ", " not in ifade["ornekler"][1]:
                dogru.append(ifade["ornekler"][1])
            if not any("tek başına" in n for _, n in yanlis):
                yanlis.append((f"{yan}. {_buyuk(ana)}",
                               "Yan cümle tek başına cümle olamaz; nokta yerine virgül konur."))
            if metin in KARSITLIK_IKILISI:
                yanlis.append((f"{yan}, but {ana}",
                               f"“{metin}” ile “but” aynı cümlede birlikte kullanılmaz; "
                               "ikisinden biri yeter."))
    else:
        if ilk:
            dogru.append(ilk)

    # tekrarları at, sırayı koru
    goruldu, tekil = set(), []
    for d in dogru:
        if d not in goruldu:
            goruldu.add(d); tekil.append(d)
    return tekil, yanlis


def noktalama_notu(ifade):
    return ifade["nokta"] or KURAL.get(ifade["yapi"], "")


def akademik_notu(ifade):
    return ifade["akademik"] or AKADEMIK.get(ifade["uslup"], "")
