"""
Arayüz dili (rapor 18.22).

- Diller settings.LANGUAGES'tan gelir (YAYIN_DILLERI). Türkçe öneksiz, diğerleri
  /en/…, /de/… önekli. Dili ADRES belirler; tarayıcı diline göre yönlendirme YOK.
- Dil düğmesi (base/_dilDugmesi.html) POST ile `dil_degistir`'e gelir: aynı sayfanın
  o dildeki adresine gidilir, seçim çerezde (cihaz) ve girişliyse hesapta saklanır.
- Girişte hesapta kayıtlı dil varsa girişten sonraki adres o dile çevrilir
  (`hesap_dili_ile_yonlendir`; Google ile girişte LearnVocab.diller.HesapAdaptoru).
- Tarayıcı dili yayındaki başka bir dilse ve kullanıcı henüz seçim yapmadıysa
  sayfanın üstünde küçük bir öneri görünür (`dil_onerisi`); yönlendirme yapılmaz.
"""

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import translate_url
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST


def yayindaki_diller():
    return [kod for kod, _ in settings.LANGUAGES]


def _guvenli(request, adres):
    if adres and url_has_allowed_host_and_scheme(adres, allowed_hosts={request.get_host()},
                                                 require_https=request.is_secure()):
        return adres
    return "/"


def _cerez_yaz(cevap, kod):
    cevap.set_cookie(settings.LANGUAGE_COOKIE_NAME, kod, max_age=365 * 24 * 3600,
                     samesite="Lax", secure=settings.SESSION_COOKIE_SECURE)


def hesap_dili(user):
    if not getattr(user, "is_authenticated", False):
        return ""
    from usersettings.models import UserSettings
    kod = UserSettings.objects.filter(user=user).values_list("arayuz_dili", flat=True).first() or ""
    return kod if kod in yayindaki_diller() else ""


def hesap_dili_ile_yonlendir(user, adres):
    """Girişten sonraki yönlendirme: hesap dili varsa adres o dile çevrilir, çerez de yazılır."""
    kod = hesap_dili(user)
    cevap = HttpResponseRedirect(translate_url(adres, kod) if kod else adres)
    if kod:
        _cerez_yaz(cevap, kod)
    return cevap


def kullanici_dilinde(user):
    """İstek dışında (bildirim, e-posta, arka plan işi) metinler kullanıcının hesap dilinde çevrilsin."""
    return translation.override(hesap_dili(user) or settings.LANGUAGE_CODE)


@require_POST
def dil_degistir(request):
    kod = request.POST.get("dil", "")
    sonraki = _guvenli(request, request.POST.get("next", ""))
    if kod not in yayindaki_diller():
        return HttpResponseRedirect(sonraki)
    cevap = HttpResponseRedirect(translate_url(sonraki, kod))
    _cerez_yaz(cevap, kod)
    if request.user.is_authenticated:
        from usersettings.models import UserSettings
        UserSettings.objects.update_or_create(user=request.user, defaults={"arayuz_dili": kod})
    return cevap


def _tarayici_dili(request):
    """Accept-Language'daki ilk desteklenen dil (Türkçe dahil); yoksa ''."""
    for parca in request.META.get("HTTP_ACCEPT_LANGUAGE", "").split(","):
        kod = parca.split(";")[0].strip().lower()[:2]
        if kod in yayindaki_diller():
            return kod
    return ""


def diller(request):
    """Context processor: dil düğmesi ve öneri için."""
    kodlar = yayindaki_diller()
    if len(kodlar) < 2:
        return {}
    simdiki = translation.get_language() or settings.LANGUAGE_CODE
    adres = request.get_full_path()
    secenekler = [{"kod": k, "ad": settings.DIL_ADLARI[k], "secili": k == simdiki} for k in kodlar]
    baglam = {"dil_secenekleri": secenekler, "dil_simdiki": simdiki, "dil_sonraki": adres}

    # Öneri: kullanıcı hiç seçim yapmamışsa ve tarayıcısı başka bir yayındaki dili istiyorsa.
    tarayici = _tarayici_dili(request)
    if (tarayici and tarayici != simdiki and settings.LANGUAGE_COOKIE_NAME not in request.COOKIES
            and request.method == "GET"):
        with translation.override(tarayici):
            baglam["dil_onerisi"] = {
                "kod": tarayici,
                # Türkçe kaynak metin "bu dilde" anlamında yazıldı; her dilin çevirisi kendi adını söyler.
                "metin": translation.gettext("Bu sayfanın Türkçesi de var."),
                "dugme": translation.gettext("Türkçeye geç"),
                "kapat": translation.gettext("Kapat"),
            }
    return baglam


from allauth.account.adapter import DefaultAccountAdapter  # noqa: E402


class HesapAdaptoru(DefaultAccountAdapter):
    """Google ile girişte de hesap dili geçerli olsun (settings.ACCOUNT_ADAPTER)."""

    def get_login_redirect_url(self, request):
        adres = super().get_login_redirect_url(request)
        kod = hesap_dili(request.user)
        return translate_url(adres, kod) if kod else adres
