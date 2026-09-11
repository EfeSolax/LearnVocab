"""
Uygulamanın ana menüsü — TEK kaynak.

Hem üstteki navbar hem de mobildeki alt sekme çubuğu bu listeden besleniyor.
Bir bölümün adını, adresini veya ikonunu değiştirmek için yalnızca burayı
düzenlemek yeterli; iki ayrı şablonu elle eşit tutmaya çalışmak gerekmiyor.

Her bölüm:
  key          -> şablonların ikon seçmek için kullandığı anahtar
  label        -> menüde görünen ad
  url_name     -> giriş yapmış kullanıcı için hedef
  public_url   -> giriş yapmamış kullanıcı için hedef (yoksa url_name kullanılır)
  matches      -> bu bölüm "aktif" sayılırken eşleşecek url adları

"Kelimeler" bölümü iki sayfayı (Kelimelerim / Tüm Kelimeler) kapsıyor:
giriş yapmış kullanıcı Kelimelerim'e, yapmamış olan Tüm Kelimeler'e düşüyor;
iki sayfanın tepesindeki seçici ile aralarında geçiliyor (bkz. _wordsTabs.html).
"""

from django.urls import reverse


NAV_SECTIONS = (
    {
        "key": "words",
        "label": "Kelimeler",
        "url_name": "profile_words",
        "public_url": "all_words",
        "matches": (
            "profile_words", "all_words", "word_detail",
            "add_word", "edit_word", "ai_add_words_page",
        ),
    },
    {
        "key": "readings",
        "label": "Okumalar",
        "url_name": "readings",
        "public_url": "readings",
        "matches": ("readings",),
    },
    {
        "key": "about",
        "label": "Hakkında",
        "url_name": "about",
        "public_url": "about",
        "matches": ("about",),
    },
    {
        "key": "quizzes",
        "label": "Egzersizler",
        # Bölümün varsayılan sayfası Öğren-Geç; Quizler'e oradaki şeritten
        # geçiliyor (Kelimeler bölümündeki Kelimelerim/Tüm Kelimeler gibi).
        "url_name": "learn_pass_page",
        "public_url": "learn_pass_page",
        "matches": (
            "learn_pass_page", "learn_pass_run",
            "profile_quizzes", "attempt_quiz", "quiz_page",
            "quiz_complete", "quiz_review", "word_analysis",
        ),
    },
    {
        "key": "texts",
        "label": "Metinler",
        "url_name": "profile_texts",
        "public_url": "profile_texts",
        "matches": (
            "profile_texts", "new_text_page", "review_text", "about_grading_page",
        ),
    },
)


def current_section_key(request):
    """İstenen sayfa hangi menü bölümüne ait? Hiçbiri ise None."""
    match = getattr(request, "resolver_match", None)
    url_name = getattr(match, "url_name", None)
    if not url_name:
        return None
    for section in NAV_SECTIONS:
        if url_name in section["matches"]:
            return section["key"]
    return None


def build_sections(request):
    """Şablonların doğrudan gezebileceği hâle getirilmiş menü listesi."""
    authenticated = bool(getattr(request, "user", None) and request.user.is_authenticated)
    active = current_section_key(request)

    sections = []
    for section in NAV_SECTIONS:
        name = section["url_name"] if authenticated else section.get("public_url") or section["url_name"]
        sections.append({
            "key": section["key"],
            "label": section["label"],
            "url": reverse(name),
            "is_active": section["key"] == active,
        })
    return sections


def navigation(request):
    """Context processor: her şablonda nav_sections / nav_section hazır olsun."""
    return {
        "nav_sections": build_sections(request),
        "nav_section": current_section_key(request),
    }
