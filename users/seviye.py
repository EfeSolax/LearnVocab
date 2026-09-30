"""
Kullanıcının seviyesi (CEFR) — TEK kaynak.

Seviyeyi okuyan her yer (günün kelimesi, egzersizler, seviye testi, Ana
Sayfa) bu modüldeki `kullanici_seviyesi(user)` fonksiyonunu kullanır:

  1) User.cefr doluysa (seviye testi ya da "Seviyemi kendim seçeyim") o.
  2) Yoksa (girişsiz ziyaretçi ya da seviyesi henüz belirlenmemiş) B1
     varsayılır (rapor 2.3).

Eski kayıt formundaki "kur" (User.level) 30 Eylül'de kaldırıldı (rapor 18.23).

Bu modül modellere bağlı değil: users/models.py seçenekleri buradan alır.
"""

# words.models.CEFR_LEVELS ile aynı sıra (yaygından nadire).
SEVIYELER = ("A1", "A2", "B1", "B2", "C1", "C2")
SEVIYE_SECENEKLERI = [(s, s) for s in SEVIYELER]

VARSAYILAN = "B1"


def kullanici_seviyesi(user):
    """Kullanıcının CEFR seviyesi: User.cefr, yoksa B1."""
    if user is None or not getattr(user, "is_authenticated", False):
        return VARSAYILAN
    deger = getattr(user, "cefr", "")
    return deger if deger in SEVIYELER else VARSAYILAN


def seviyesi_belli_mi(user):
    """Seviye testi ya da kendi seçimiyle belirlenmiş bir seviye var mı?"""
    return bool(user is not None and getattr(user, "is_authenticated", False)
                and getattr(user, "cefr", "") in SEVIYELER)
