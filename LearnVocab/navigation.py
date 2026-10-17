"""
Uygulamanın ana menüsü — TEK kaynak.

Hem üstteki çubuk (masaüstü) hem de mobildeki alt sekme çubuğu bu listeden
besleniyor. Bir bölümün adını, adresini veya ikonunu değiştirmek için
yalnızca burayı düzenlemek yeterli.

Menü (ürün raporu 2.1): Sözlük · Çalışmalar · Ana Sayfa · Okumalar · Yazılar
Ana Sayfa ortada. "Hakkında" menüde yok (yardım bağlantısı Ana Sayfa'da),
Ayarlar sağ üstteki dişli simgesinde.

Her bölüm:
  key           -> şablonların ikon seçmek için kullandığı anahtar
  label         -> menüde görünen ad
  url_name      -> hedef sayfa
  matches       -> bu bölüm "aktif" sayılırken eşleşecek url adları
  giris_gerekli -> girişsiz ziyaretçi dokununca giriş sayfasına yönlendirilir
                   (değer: authgate.GIRIS_NEDENLERI anahtarı). Bölüm yine de
                   menüde görünür (rapor 2.3: giriş gerektiren düğmeler
                   gizlenmez).
"""

from django.urls import reverse
from django.utils.translation import gettext_lazy as _


NAV_SECTIONS = (
    {
        "key": "sozluk",
        "label": _("Sözlük"),
        "url_name": "sozluk",
        "matches": ("sozluk",),
    },
    {
        "key": "calismalar",
        "label": _("Çalışmalar"),
        # Bölüm Learn & Pass ile açılıyor; Egzersizler sekmesine oradaki
        # şeritten geçiliyor (bkz. base/_exerciseTabs.html).
        "url_name": "learn_pass_page",
        "matches": ("learn_pass_page", "learn_pass_run", "exercises_page",
                    "egzersiz_oturum"),
    },
    {
        "key": "home",
        "label": _("Ana Sayfa"),
        "url_name": "index",
        "matches": ("index",),
    },
    {
        "key": "readings",
        "label": _("Okumalar"),
        "url_name": "readings",
        "matches": ("readings", "readings_library_text", "readings_user_text", "readings_add"),
    },
    {
        # Eski "Metinler" / "Yazma" bölümü. Türkçe adı "Yazılar", İngilizcesi "Writings"
        # (Efe, 30 Eylül). url adları ve uygulama adı (texts) değişmedi.
        "key": "yazma",
        "label": _("Yazılar"),
        "url_name": "profile_texts",
        "matches": ("profile_texts", "new_text_page", "review_text", "about_grading_page",
                    "diyalog_page"),
        # Misafire açık (rapor 18.3): giriş daveti (diyalog açıksa diyalog egzersizi de).
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

    return [{
        "key": section["key"],
        "label": section["label"],
        "url": reverse(section["url_name"]),
        "is_active": section["key"] == active,
        # Yalnızca girişsizken dolu: şablon data-giris-gerekli özniteliğini
        # buna göre basıyor.
        "giris_gerekli": "" if authenticated else section.get("giris_gerekli", ""),
    } for section in NAV_SECTIONS]


def navigation(request):
    """Context processor: her şablonda nav_sections / nav_section hazır olsun."""
    return {
        "nav_sections": build_sections(request),
        "nav_section": current_section_key(request),
    }
