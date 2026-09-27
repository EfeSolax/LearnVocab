"""
Giriş gerektiren yerler için ortak kurallar (ürün raporu 2.3 ve 12.6).

Genel kural: giriş gerektiren düğmeler ve bölümler GİZLENMEZ. Girişsiz
ziyaretçi bunlara dokununca kısa bir açıklamayla giriş sayfasına
yönlendirilir; girişten sonra `?next=` ile geldiği sayfaya döner.

İki yol var, ikisi de aynı adresi (giris_adresi) ve aynı açıklamaları
(GIRIS_NEDENLERI) kullanıyor:

  1) DÜĞME / BAĞLANTI (tarayıcıda): öğeye `data-giris-gerekli="<neden>"`
     özniteliği konur — yalnızca girişsiz ziyaretçiye basılır, örneğin
         <button {% if not user.is_authenticated %}data-giris-gerekli="liste"{% endif %}>
     Ortak JS (base/_girisGerekli.html) tıklamayı yakalar ve
     /users/login/?next=<bu sayfa>&neden=liste adresine gider.

  2) SAYFA (sunucuda): @login_gate. Adres doğrudan açılırsa kullanıcı giriş
     formuna fırlatılmaz; "bu sayfa için giriş yapmalısın" ekranı ve menü
     yerinde kalır. Ekrandaki "Giriş Yap" bağlantısı da ?next= taşır.

Form gönderen / veri değiştiren görünümler @login_required kullanmaya devam
ediyor; login_user ?next= adresine güvenli biçimde döner.

`neden` serbest metin DEĞİL, aşağıdaki sözlüğün anahtarı: giriş sayfasına
adres çubuğundan keyfî yazı bastırılamasın.
"""

from functools import wraps
from urllib.parse import urlencode

from django.shortcuts import render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


# Giriş sayfasında "Önce giriş yapmalısın." cümlesinin altına yazılan kısa açıklama.
GIRIS_NEDENLERI = {
    "liste": "Kelimeleri listene ekleyebilmek için bir hesaba ihtiyacın var.",
    "egzersiz": "Egzersizler kendi listenle çalıştığı için giriş yapman gerekiyor.",
    "yazma": "Yazdıkların hesabına kaydedildiği için giriş yapman gerekiyor.",
    "pdf": "Kendi metinlerini yükleyebilmek için giriş yapman gerekiyor.",
    "calisma": "Çalışmanın kaydedilmesi için giriş yapman gerekiyor.",
}


def giris_adresi(sonraki=None, neden=None):
    """/users/login/?next=…&neden=… — boş parçalar eklenmez."""
    parametreler = {}
    if sonraki:
        parametreler["next"] = sonraki
    if neden in GIRIS_NEDENLERI:
        parametreler["neden"] = neden
    adres = reverse("login")
    return f"{adres}?{urlencode(parametreler)}" if parametreler else adres


def guvenli_sonraki(request):
    """
    Girişten sonra dönülecek adres (GET ya da POST'taki `next`).
    Başka bir siteye yönlendirme (open redirect) olmasın diye yalnızca bu
    sitenin adresleri kabul edilir; değilse None.
    """
    sonraki = request.POST.get("next") or request.GET.get("next")
    if sonraki and url_has_allowed_host_and_scheme(
            sonraki, allowed_hosts={request.get_host()},
            require_https=request.is_secure()):
        return sonraki
    return None


def giris_notu(request):
    """Giriş sayfasında gösterilecek açıklama: (başlık, ayrıntı) ya da None."""
    neden = request.GET.get("neden") or request.POST.get("neden")
    if neden in GIRIS_NEDENLERI:
        return {"baslik": "Önce giriş yapmalısın.", "ayrinti": GIRIS_NEDENLERI[neden]}
    if guvenli_sonraki(request):
        return {"baslik": "Önce giriş yapmalısın.", "ayrinti": ""}
    return None


def login_gate(area_label, description=None):
    """
    Giriş gerektiren SAYFALAR için kapı (yalnızca GET ile açılan sayfalar).

    area_label: ekranda geçen bölüm adı ("Yazma", "Egzersizler", ...)
    description: isteğe bağlı ek açıklama cümlesi
    """
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                return view(request, *args, **kwargs)
            return render(request, "pages/loginRequired.html", {
                "active_page": area_label,
                "gate_area": area_label,
                "gate_description": description,
                "gate_login_url": giris_adresi(request.get_full_path()),
            }, status=200)
        return wrapper
    return decorator
