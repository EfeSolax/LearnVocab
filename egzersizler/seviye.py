"""
Kullanıcının seviyesi (CEFR) ve komşu seviyeler.

Seviyenin kendisi tek kaynaktan okunur: users.seviye.kullanici_seviyesi
(User.cefr, yoksa B1).
"""

from users.seviye import VARSAYILAN, kullanici_seviyesi  # noqa: F401
from words.models import CEFR_LEVELS


def bir_ust(seviye):
    """B1 -> B2 … C2'nin üstü yine C2."""
    i = CEFR_LEVELS.index(seviye) if seviye in CEFR_LEVELS else CEFR_LEVELS.index(VARSAYILAN)
    return CEFR_LEVELS[min(i + 1, len(CEFR_LEVELS) - 1)]


def komsular(seviye):
    """Seviyeye yakınlık sırası: B1, A2, B2, A1, C1, C2 … (havuz yetmezse genişlemek için)."""
    i = CEFR_LEVELS.index(seviye) if seviye in CEFR_LEVELS else CEFR_LEVELS.index(VARSAYILAN)
    return sorted(CEFR_LEVELS, key=lambda s: (abs(CEFR_LEVELS.index(s) - i),
                                              CEFR_LEVELS.index(s) > i))
