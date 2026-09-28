"""
Serbest yazma için konu önerileri (rapor 9.1).

Elle yazılmış, sabit, küçük bir liste. Yapay zekâyla üretilmez. Kısa (3–8
cümle) ve gündelik yazılabilecek konular seçildi; akademik yazı beklenmez.

Her konu: (anahtar, Türkçe başlık, İngilizce yönlendirme). Anahtar formda
gönderilir, metne başlık kaydedilir. Yeni konu eklemek için listeye bir satır
eklemek yeter; anahtarlar değiştirilmemeli.
"""

KONULAR = (
    ("hafta-sonu", "Hafta sonum", "Write about what you did last weekend."),
    ("sabah", "Sabah rutinim", "Describe your usual morning, from waking up to leaving home."),
    ("sehir", "Yaşadığım şehir", "What do you like and dislike about the city you live in?"),
    ("yemek", "En sevdiğim yemek", "Describe your favourite meal and when you usually eat it."),
    ("tatil", "Unutamadığım bir yolculuk", "Tell a short story about a trip you remember well."),
    ("arkadas", "Bir arkadaşım", "Describe a close friend and why you get along."),
    ("okul", "Okulda bir gün", "Write about a typical day at school or university."),
    ("hedef", "Bu yılki hedefim", "What is one goal you have for this year, and how will you reach it?"),
    ("telefon", "Telefonsuz bir gün", "Could you spend a whole day without your phone? Why or why not?"),
    ("kitap-dizi", "Önerdiğim bir kitap ya da dizi", "Recommend a book, film or series to a friend."),
    ("hobi", "Hobim", "Describe a hobby you enjoy and how you started it."),
    ("hava", "Mevsimler", "Which season do you like most, and why?"),
    ("ev", "Hayalimdeki ev", "Describe the home you would like to live in one day."),
    ("zor-gun", "Zor bir gün", "Write about a difficult day and what you learned from it."),
    ("ogrenmek", "İngilizce öğrenmek", "What helps you most when you learn English?"),
    ("tavsiye", "Yeni gelen birine tavsiye", "Give advice to someone who is moving to your city."),
)

_SOZLUK = {anahtar: (baslik, yonerge) for anahtar, baslik, yonerge in KONULAR}


def konu_basligi(anahtar):
    """Anahtarın başlığı; bilinmeyen anahtar için boş string (serbest yazma)."""
    konu = _SOZLUK.get((anahtar or "").strip())
    return konu[0] if konu else ""


def konu_yonergesi(baslik):
    """Kaydedilmiş başlığın İngilizce yönergesi (prompt'a eklenir)."""
    for _anahtar, b, yonerge in KONULAR:
        if b == baslik:
            return yonerge
    return ""


def konular_listesi():
    return [{"anahtar": a, "baslik": b, "yonerge": y} for a, b, y in KONULAR]
