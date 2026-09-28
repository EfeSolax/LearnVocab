"""
Egzersizler (ürün raporu 6.2): Hızlı Egzersiz ve Tempolu Egzersiz.

Başka uygulamaların kullanacağı tek kapı:

    import egzersizler
    egzersizler.zorlanilanlar(user)          # Word queryset
    egzersizler.zorlanilan_kelime_idleri(user)

Listem'in "Zorlandıklarım" filtresi (rapor 5) egzersizde yanlış yapılan
kelimeleri buradan okur. Ayrıntı: egzersizler/kayit.py.
"""


def zorlanilanlar(user, gun=None):
    """Kullanıcının egzersizde en az bir kez yanlış yaptığı kelimeler (Word queryset)."""
    from .kayit import zorlanilanlar as _z
    return _z(user, gun=gun)


def zorlanilan_kelime_idleri(user, gun=None):
    """zorlanilanlar() ile aynı, yalnızca kelime id'leri (alt sorgu olarak kullanılabilir)."""
    from .kayit import zorlanilan_kelime_idleri as _z
    return _z(user, gun=gun)
