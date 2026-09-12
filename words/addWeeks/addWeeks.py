"""
Seviye bazlı toplu ekleme/silme.

Eskiden bu dosya ODTÜ kuruna (101–501) ve kur içi haftaya ("span") göre
filtreliyordu. Seviye artık CEFR; kur üyeliği ise kelimenin bir özelliği
değil, kelimeye takılacak bir liste etiketi — o katman gelince buraya
dönecek.
"""

from ..models import Word, UserWordLink


def allWordsAddDelete(user, delete, level):
    """CEFR seviyesindeki (A1..C2) bütün temel kelimeleri ekler ya da çıkarır."""
    words = Word.objects.filter(cefr=str(level), isBaseWord=True).order_by("id")

    for word in words:
        if delete:
            UserWordLink.objects.filter(user=user, word=word).delete()
        else:
            UserWordLink.objects.get_or_create(user=user, word=word)

    return words.count()
