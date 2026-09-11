"""
Giriş gerektiren SAYFALAR için kapı.

django'nun @login_required'ı kullanıcıyı doğrudan giriş formuna fırlatıyor.
Mobilde alt sekme çubuğundaki beş bölüm herkese görünüyor; bunlardan birine
girişsiz dokunan kullanıcının aniden giriş formunda bulması kafa karıştırıcı.
Bunun yerine "bu sayfa için giriş yapmalısın" diyen, bağlantısı olan bir
ekran gösteriliyor ve menü yerinde kalıyor.

Yalnızca GET ile açılan sayfalar için. Form gönderen / veri değiştiren
görünümler @login_required kullanmaya devam ediyor.
"""

from functools import wraps

from django.shortcuts import render


def login_gate(area_label, description=None):
    """
    area_label: ekranda geçen bölüm adı ("Kelimelerim", "Egzersizler", ...)
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
            }, status=200)
        return wrapper
    return decorator
