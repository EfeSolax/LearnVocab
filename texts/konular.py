"""
Serbest yazma için konu önerileri (rapor 9.1).

Elle yazılmış, sabit, küçük bir liste. Yapay zekâyla üretilmez. Kısa (3–8
cümle) ve gündelik yazılabilecek konular; akademik türün konuları KONULAR_AKADEMIK'te.

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

# Akademik tür (Efe, 17 Ekim): tartışma/değerlendirme soruları; Forefront'un kendi
# örnek sorularına benzer (suç oranları, zorunlu İngilizce, sosyal medya, sahip olmak ve mutluluk).
KONULAR_AKADEMIK = (
    ("a-ingilizce", "Zorunlu İngilizce", "Should English be a compulsory subject in schools? Discuss with reasons."),
    ("a-sosyal-medya", "Sosyal medya ve ilişkiler", "To what extent has social media affected people's offline relationships?"),
    ("a-suc", "Suç oranları", "What are the most effective ways to address rising crime rates?"),
    ("a-uzaktan", "Uzaktan eğitim", "Discuss the advantages and disadvantages of online education for university students."),
    ("a-yapay-zeka", "Yapay zekâ ve öğrenme", "How might generative AI tools affect the way students learn?"),
    ("a-iklim", "İklim değişikliği", "What role can individuals play in reducing the effects of climate change?"),
    ("a-mutluluk", "Sahip olmak ve mutluluk", "Is there a relationship between owning more and being happier?"),
    ("a-sehir", "Hızlı şehirleşme", "Discuss the effects of rapid urbanization on the quality of life."),
    ("a-calisma", "Dört günlük çalışma haftası", "Should a four-day working week be introduced? Evaluate the arguments."),
    ("a-turizm", "Kitle turizmi", "Discuss the economic and environmental effects of mass tourism."),
    ("a-ceza", "Ceza mı, rehabilitasyon mu?", "Should prisons focus more on rehabilitation than on punishment?"),
    ("a-sinav", "Sınavlar ve başarı", "Do standardized exams measure students' abilities accurately?"),
)

_SOZLUK = {anahtar: (baslik, yonerge) for anahtar, baslik, yonerge in KONULAR + KONULAR_AKADEMIK}


def konu_basligi(anahtar):
    """Anahtarın başlığı; bilinmeyen anahtar için boş string (serbest yazma)."""
    konu = _SOZLUK.get((anahtar or "").strip())
    return konu[0] if konu else ""


def konu_yonergesi(baslik):
    """Kaydedilmiş başlığın İngilizce yönergesi (prompt'a eklenir)."""
    for _anahtar, b, yonerge in KONULAR + KONULAR_AKADEMIK:
        if b == baslik:
            return yonerge
    return ""


def konular_listesi(akademik=False):
    return [{"anahtar": a, "baslik": b, "yonerge": y} for a, b, y in (KONULAR_AKADEMIK if akademik else KONULAR)]
