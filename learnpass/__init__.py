"""
Learn & Pass.

Başka bölümlerin kullanması için kısa yol (Listem > "Zorlandıklarım"):

    import learnpass
    learnpass.zorlanilanlar(user)   # -> Word queryset

Uygulama yüklenirken modellere dokunmamak için içe aktarma fonksiyonun içinde.
"""


def zorlanilanlar(user):
    """Kullanıcının L&P'de "bilmiyorum" dediği kelimeler (bkz. selection.zorlanilan_kelimeler)."""
    from .selection import zorlanilan_kelimeler

    return zorlanilan_kelimeler(user)
