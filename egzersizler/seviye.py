"""
Kullanıcının seviyesi (CEFR).

Seviye testi uygulama planının 10. adımında gelecek. O zamana kadar:

  1) Kullanıcı nesnesinde CEFR değeri taşıyan bir `seviye` / `cefr` alanı
     varsa (seviye testi eklendiğinde) o kullanılır.
  2) Yoksa eski kayıt formundaki kur (User.level: 101…501) CEFR'e çevrilir.
     Eşleme Ana Sayfa'nın eski "401/501 -> B2/C1" kuralıyla aynı çizgide.
  3) Hiçbiri yoksa (level=1, "belirtilmemiş") B1 varsayılır (rapor 2.3).
"""

from words.models import CEFR_LEVELS

VARSAYILAN = "B1"

KUR_CEFR = {101: "A1", 201: "A2", 301: "B1", 401: "B2", 501: "C1"}


def kullanici_seviyesi(user):
    for alan in ("seviye", "cefr"):
        deger = getattr(user, alan, None)
        if isinstance(deger, str) and deger in CEFR_LEVELS:
            return deger
    kur = getattr(user, "level", None)
    return KUR_CEFR.get(kur, VARSAYILAN)


def bir_ust(seviye):
    """B1 -> B2 … C2'nin üstü yine C2."""
    i = CEFR_LEVELS.index(seviye) if seviye in CEFR_LEVELS else CEFR_LEVELS.index(VARSAYILAN)
    return CEFR_LEVELS[min(i + 1, len(CEFR_LEVELS) - 1)]


def komsular(seviye):
    """Seviyeye yakınlık sırası: B1, A2, B2, A1, C1, C2 … (havuz yetmezse genişlemek için)."""
    i = CEFR_LEVELS.index(seviye) if seviye in CEFR_LEVELS else CEFR_LEVELS.index(VARSAYILAN)
    return sorted(CEFR_LEVELS, key=lambda s: (abs(CEFR_LEVELS.index(s) - i),
                                              CEFR_LEVELS.index(s) > i))
