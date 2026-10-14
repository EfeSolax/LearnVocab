# -*- coding: utf-8 -*-
"""
Denetimden geçmiş veriyi veritabanına yazan tek yer.

Modelin ürettiği hiçbir şey buraya doğrudan gelmez; önce `checks.denetle`den
geçer. Her kelime kendi transaction'ında yazılır: bir kelimenin bir parçası
patlarsa o kelime hiç yazılmamış olur, ama önceki kelimeler durur. Binlerce
kelimelik bir çalıştırmada tek bir bozuk kayıt yüzünden her şeyi kaybetmek
kabul edilemez.

Yazma HER ZAMAN toplayıcıdır (additive): var olan anlamlar silinmez, üstüne
eklenir. Aynı listeyi iki kez çalıştırmak veriyi bozmaz.
"""

import logging

from django.db import transaction

from words import inflect
from words.models import (
    Collocation, ExampleSentence, FalseFriend, Meaning,
    UsagePattern, Word, WordFamily, WordRelation,
)

logger = logging.getLogger(__name__)


@transaction.atomic
def yaz(kelime, kaynak="AI", aile=None):
    """
    Doğrulanmış bir `schema.Word`u veritabanına yazar.

    `aile` verilirse (context.aile_bul'un bulduğu) O KULLANILIR. Bu önemli:
    model `interpret` için "interpret" kökünü yazıyor ama veritabanında
    zaten `interpretation` ailesi var. Modelin dediğine bakıp yeni aile
    açmak, aynı ailenin iki parçaya bölünmesi demek — ve bu bölünme bir
    daha kendiliğinden kapanmaz.

    Döner: {"kelime": Word, "yeni_kelime": bool, "anlam": n, "cumle": n,
            "collocation": n, "kalip": n, "yanlis_dost": n, "bag": n,
            "bicim": n, "atlanan_bag": n}
    """
    sayac = dict(anlam=0, cumle=0, collocation=0, kalip=0,
                 yanlis_dost=0, bag=0, bicim=0, atlanan_bag=0)

    # --- Aile -----------------------------------------------------------
    if aile is None:
        aile, _ = WordFamily.objects.get_or_create(
            root=kelime.family_root.strip().lower()
        )

    # Aile kökü, ailenin EN YALIN üyesi olmalı. Türev tabandan önce geldiğinde
    # (metinlerden toplarken sık olur) aile "interpretation" adıyla kuruluyor;
    # sonradan "interpret" gelince kök ona taşınıyor. Aile sayfasında ve
    # sıralamada kök başta göründüğü için bu kozmetik değil.
    # Taşıma koşulu "daha kısa" DEĞİL, "gerçekten gövdesi": mevcut kök yeni
    # kökle BAŞLAMALI. Yalnızca uzunluğa bakmak `analysis` ailesinin kökünü
    # `analyst`e kaydırıyordu — kısa ama daha yalın değil.
    from words.enrich.checks import kok_gecerli_mi
    yeni_kok = kelime.text.strip().lower()
    if (yeni_kok != aile.root
            and len(yeni_kok) < len(aile.root)
            and aile.root.startswith(yeni_kok)):
        gecerli, _sebep = kok_gecerli_mi(yeni_kok, aile.root)
        if gecerli and not WordFamily.objects.filter(root=yeni_kok).exists():
            aile.root = yeni_kok
            aile.save(update_fields=["root"])

    # --- Kelime ---------------------------------------------------------
    kayit, yeni = Word.objects.get_or_create(
        text=kelime.text, pos=kelime.pos,
        defaults={
            "family": aile,
            "cefr": kelime.cefr,
            "v2Form": kelime.v2Form or None,
            "v3Form": kelime.v3Form or None,
            "isBaseWord": True,
            "visibility": "public",
        },
    )

    if not yeni:
        # Var olan kaydı EZME; yalnızca boş alanları tamamla.
        degisen = []
        if kayit.cefr in ("", "Belirtilmemiş") and kelime.cefr:
            kayit.cefr = kelime.cefr
            degisen.append("cefr")
        if not kayit.v2Form and kelime.v2Form:
            kayit.v2Form = kelime.v2Form
            degisen.append("v2Form")
        if not kayit.v3Form and kelime.v3Form:
            kayit.v3Form = kelime.v3Form
            degisen.append("v3Form")
        if degisen:
            kayit.save(update_fields=degisen)

    # --- Anlamlar --------------------------------------------------------
    sonraki_sira = kayit.meanings.count()

    for anlam in kelime.meanings:
        kayitli_anlam = Meaning.objects.create(
            word=kayit,
            meaning_tr=anlam.meaning_tr[:300],
            definition=(anlam.definition or "")[:600] or None,
            sentiment=anlam.sentiment,
            register=anlam.register,
            sort_order=sonraki_sira,
        )
        sonraki_sira += 1
        sayac["anlam"] += 1

        # Kategoriler (konular) 11 Ekim'den beri yalnızca elle işaretlenir (rapor 18.39).

        ExampleSentence.objects.bulk_create([
            ExampleSentence(meaning=kayitli_anlam, text=cumle[:400],
                            source=kaynak, sort_order=i)
            for i, cumle in enumerate(anlam.sentences)
        ])
        sayac["cumle"] += len(anlam.sentences)

        for i, coll in enumerate(anlam.collocations):
            _, olustu = Collocation.objects.get_or_create(
                meaning=kayitli_anlam, pattern=coll.pattern[:200],
                defaults={
                    "kind": coll.kind,
                    "meaning_tr": (coll.meaning_tr or "")[:200] or None,
                    "example": (coll.example or "")[:400] or None,
                    "sort_order": i,
                },
            )
            sayac["collocation"] += int(olustu)

        for i, kalip in enumerate(anlam.patterns):
            _, olustu = UsagePattern.objects.get_or_create(
                meaning=kayitli_anlam, pattern=kalip.pattern[:200],
                defaults={
                    "kind": kalip.kind,
                    "example": (kalip.example or "")[:400] or None,
                    "note": (kalip.note or "")[:300] or None,
                    "sort_order": i,
                },
            )
            sayac["kalip"] += int(olustu)

    # --- Yanlış dostlar ---------------------------------------------------
    for dost in kelime.false_friends:
        _, olustu = FalseFriend.objects.get_or_create(
            word=kayit, turkish_lookalike=dost.turkish_lookalike[:100],
            defaults={
                "assumed_meaning": (dost.assumed_meaning or "")[:200] or None,
                "correct_english": (dost.correct_english or "")[:200] or None,
                "note": (dost.note or "")[:400] or None,
            },
        )
        sayac["yanlis_dost"] += int(olustu)

    # --- Bağlar ------------------------------------------------------------
    # Hedef kelime henüz veritabanında yoksa bağ KURULMAZ. Uydurma bir hedef
    # kaydı açmak, sonradan gerçek kelime geldiğinde çift kayda yol açardı.
    for bag in kelime.relations:
        hedef = Word.objects.filter(text=bag.to_word, pos=bag.to_pos).first() \
             or Word.objects.filter(text=bag.to_word).first()
        if hedef is None or hedef.pk == kayit.pk:
            sayac["atlanan_bag"] += 1
            continue
        # get_or_create değil: D1'den sonra aynı bağ birden çok anlamda
        # (birden çok satırda) durabiliyor.
        olustu = not WordRelation.objects.filter(
            from_word=kayit, to_word=hedef, type=bag.type).exists()
        if olustu:
            WordRelation.objects.create(from_word=kayit, to_word=hedef, type=bag.type,
                                        note=(bag.note or "")[:200] or None)
        sayac["bag"] += int(olustu)

    # --- Çekim biçimleri ----------------------------------------------------
    inflect.rebuild_forms(kayit)
    sayac["bicim"] = kayit.forms.count()

    sayac["kelime"] = kayit
    sayac["yeni_kelime"] = yeni
    return sayac
