"""
Kural tabanlı veri denetimleri (rapor 18.6, 18.7 A aşaması).

daha_basit_nedeni(kaynak, hedef) -> silme nedeni ya da None
    Bir "daha basit" ilişkisi yalnızca iki koşul birden sağlanırsa kalır:
      1. hedefin seviyesi A1, A2 ya da B1,
      2. hedef kaynaktan KESİNLİKLE daha alt seviyede.
    Kaynak seviyesi ilişkinin bağlı olduğu anlamın CEFR'i (yoksa kelimenin),
    hedef seviyesi hedef kelimenin CEFR'i.

Komut: manage.py veri_tara (--dry-run)
"""

SEVIYE = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
EN_YUKSEK_BASIT = SEVIYE["B1"]


def daha_basit_nedeni(kaynak_cefr, hedef_cefr):
    kaynak, hedef = SEVIYE.get(kaynak_cefr), SEVIYE.get(hedef_cefr)
    if hedef is None:
        return "hedefin seviyesi yok"
    if hedef > EN_YUKSEK_BASIT:
        return "hedef B2 ya da üstü"
    if kaynak is None:
        return "kaynağın seviyesi yok"
    if hedef >= kaynak:
        return "hedef kaynaktan alt seviyede değil"
    return None


def daha_basit_silinecekler():
    """[(ilişki id, neden)] — silinecek "daha basit" ilişkileri."""
    from words.models import WordRelation
    iliskiler = (WordRelation.objects.filter(type="simpler")
                 .select_related("from_word", "to_word", "meaning")
                 .only("id", "from_word__cefr", "to_word__cefr", "meaning__cefr"))
    sonuc = []
    for r in iliskiler:
        kaynak = (r.meaning.cefr if r.meaning_id and r.meaning.cefr in SEVIYE else r.from_word.cefr)
        neden = daha_basit_nedeni(kaynak, r.to_word.cefr)
        if neden:
            sonuc.append((r.id, neden))
    return sonuc


def es_zit_catismalari():
    """Aynı anlamda aynı hedef hem eş hem zıt anlamlıysa: [(meaning_id, to_word_id)]."""
    from django.db.models import Count
    from words.models import WordRelation
    return list(WordRelation.objects.filter(meaning__isnull=False, type__in=("synonym", "antonym"))
                .values("meaning_id", "to_word_id").annotate(t=Count("type", distinct=True))
                .filter(t__gt=1).values_list("meaning_id", "to_word_id"))
