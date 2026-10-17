"""
Konular (rapor 18.39): elle işaretlenmiş 34 konu (Category). Arayüz (Efe'nin isteği, 11 Ekim):

  - Sözlük › Keşfet: arama kutusuyla günün kelimesi arasında eliptik konu kutucukları
    (emoji + ad, her biri kendi renginde); ilk ONDE_GORUNEN tanesi görünür, "Daha fazla
    göster" hepsini aynı yerde açar (pages/words/_konular.html).
  - /sozluk/konu/<slug>/: o konudaki kelimeler, hazır liste sayfası gibi alt alta kapalı kartlar.
  - Kelime kartında anlamın konusu küçük bir kutucuk olarak görünür (words.kart).

Konunun Türkçe adı veritabanında (Category.name); emoji, renk ve İngilizce adı burada.
Sıra = Keşfet'teki sıra (en çok merak edilen gündelik konular önde).
"""

from django.db.models import Count
from django.utils.translation import get_language

ONDE_GORUNEN = 8

# slug: (emoji, zemin rengi, İngilizce ad)
KONULAR = {
    "hayvanlar": ("🐾", "#fde2c8", "Animals"),
    "yiyecek-icecek": ("🍎", "#fecaca", "Food and drink"),
    "duygular": ("😊", "#fef08a", "Feelings"),
    "aile-iliskiler": ("👨‍👩‍👧", "#fbcfe8", "Family and relationships"),
    "ev-esyalar": ("🏠", "#e7d8c9", "Home and furniture"),
    "giyim-moda": ("👕", "#ddd6fe", "Clothes and fashion"),
    "spor": ("⚽", "#bbf7d0", "Sports"),
    "seyahat": ("✈️", "#bae6fd", "Travel and holidays"),
    "kisilik-davranis": ("🙋", "#fed7aa", "Personality and behavior"),
    "gorus-tercih": ("👍", "#d9f99d", "Opinions and preferences"),
    "gorunus-beden": ("💪", "#fecdd3", "Appearance and body"),
    "yemek-yapma": ("🍳", "#fde68a", "Cooking"),
    "saglik": ("🩺", "#ccfbf1", "Health and illness"),
    "okul-egitim": ("🎓", "#c7d2fe", "School and education"),
    "is-meslekler": ("💼", "#e2e8f0", "Work and jobs"),
    "sanat-eglence": ("🎨", "#f5d0fe", "Arts and entertainment"),
    "bos-zaman": ("🎲", "#a7f3d0", "Free time and hobbies"),
    "ulasim": ("🚌", "#fef3c7", "Transport"),
    "sehir-yerler": ("🏙️", "#cbd5e1", "Town and places"),
    "alisveris-para": ("🛍️", "#fbcfe8", "Shopping and money"),
    "hava-durumu": ("☀️", "#fef9c3", "Weather"),
    "doga": ("🌳", "#bbf7d0", "Nature"),
    "zaman": ("⏰", "#e0e7ff", "Time"),
    "iletisim-medya": ("📰", "#e5e7eb", "Communication and media"),
    "teknoloji": ("💻", "#cffafe", "Technology and the internet"),
    "bilim-arastirma": ("🔬", "#dbeafe", "Science and research"),
    "ekonomi-is-dunyasi": ("📈", "#dcfce7", "Economy and business"),
    "hukuk-suc": ("⚖️", "#fee2e2", "Law and crime"),
    "siyaset-toplum": ("🏛️", "#ede9fe", "Politics and society"),
    "tarih": ("🏺", "#fde4cf", "History"),
    "psikoloji-zihin": ("🧠", "#fce7f3", "Psychology and the mind"),
    "cevre-iklim": ("🌍", "#d1fae5", "Environment and climate"),
    "neden-sonuc-degisim": ("🔄", "#e0f2fe", "Cause, effect and change"),
    "tartisma": ("💬", "#f3e8ff", "Argument and discussion"),
}
_SIRA = {slug: i for i, slug in enumerate(KONULAR)}
_VARSAYILAN = ("🏷️", "#e5e7eb", "")


def konu_bilgisi(kategori):
    """Category -> {slug, ad, emoji, renk} (ad arayüz diline göre; Türkçe değilse İngilizce)."""
    emoji, renk, ad_en = KONULAR.get(kategori.slug, _VARSAYILAN)
    turkce = (get_language() or "tr").startswith("tr")
    return {"slug": kategori.slug, "ad": kategori.name if turkce or not ad_en else ad_en,
            "emoji": emoji, "renk": renk}


def kesfet_konulari():
    """Keşfet'teki kutucuklar: kelimesi olan konular, KONULAR sırasıyla. Tek sorgu."""
    from .models import Category
    kategoriler = (Category.objects.annotate(n=Count("meanings", distinct=True) + Count("expressions", distinct=True))
                   .filter(n__gt=0))
    return [konu_bilgisi(k) for k in sorted(kategoriler, key=lambda k: (_SIRA.get(k.slug, 99), k.name))]


_SEVIYE = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}


def konu_kelime_idleri(kategori, ortak, seviyeler=False):
    """Konudaki kelimeler, zordan kolaya (C2 → A1, Efe 17 Ekim); aynı seviyede sık kullanılan önce,
    seviyesi olmayanlar en sonda.
    seviyeler=True: [(id, cefr), …] (konu sayfasının seviye süzgeci için)."""
    from .models import Word
    satirlar = (Word.objects.filter(ortak, meanings__categories=kategori)
                .values_list("id", "cefr", "siklik").distinct())
    sirali = sorted(set(satirlar), key=lambda s: (-_SEVIYE.get(s[1], 0), -(s[2] or 0), s[0]))
    return [(s[0], s[1]) for s in sirali] if seviyeler else [s[0] for s in sirali]
