# -*- coding: utf-8 -*-
"""
30 Eylül — veri adımında (rapor 18.7 A aşaması) bulunan tek tek hatalar.
Çalıştırma:  python manage.py shell -c "from words.duzeltmeler import d_2026_09_30 as d; d.uygula()"
Tekrar çalıştırmak güvenli.
"""
from django.db import transaction

from words.models import Word, WordRelation


def uygula():
    with transaction.atomic():
        # despairing (umutsuz): hopeless hem eş hem zıt anlamlı yazılmış;
        # doğrusu eş anlamlı, zıt kaydı silinir.
        WordRelation.objects.filter(from_word__text="despairing", to_word__text="hopeless",
                                    type="antonym").delete()
        # papist: Katolikler için aşağılayıcı söz (rapor 12.2 hassas anlam)
        Word.objects.filter(text="papist").delete()
