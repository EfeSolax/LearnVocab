"""
Eski adreslerden yeni adreslere kalıcı (301) yönlendirmeler (rapor 18.15).

İki kaynak var:
  - v1.0 (canlıdaki site): /words/…, /users/…, /profile/profile/…, /texts/…,
    /quizzes/…, /exercises/learn/…, /readings/, /about/
  - geliştirme sırasındaki ara adresler: /egzersizler/, /seviye/, /sozluk/liste/…

Yalnızca SAYFA adresleri yönlenir. POST ile çalışan eski uçlar (form
gönderme, silme) yönlenmez; 404 kalır.

v1.0'daki /words/word-detail/<id>/ kimlikleri yeni veritabanında geçerli
değil (kelimeler baştan üretildi); bu adresler Sözlük'e yönlenir.
"""

from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.urls import path, reverse


def _yonlendir(ad, *sabit, sorgu=""):
    """Adı verilen yeni sayfaya 301. Eski adresteki parametreler atılır."""
    def view(request, **kwargs):
        return HttpResponsePermanentRedirect(reverse(ad, args=sabit) + sorgu)
    return view


def _ayni_parcalarla(ad):
    """Eski adresteki parçalar (slug, mod) yeni adrese aynen taşınır."""
    def view(request, **kwargs):
        return HttpResponsePermanentRedirect(reverse(ad, kwargs=kwargs))
    return view


def _kutuphane_metni(request, number):
    from readings.models import ReadingText
    metin = get_object_or_404(ReadingText, number=number)
    return HttpResponsePermanentRedirect(reverse("readings_library_text", args=[metin.slug]))


urlpatterns = [
    # Sözlük
    path("words/all-words/", _yonlendir("sozluk")),
    path("words/word-detail/<int:id>/", _yonlendir("sozluk")),
    path("words/expression/<int:id>/", _yonlendir("sozluk")),
    path("sozluk/liste/<slug:slug>/", _ayni_parcalarla("hazir_liste")),
    path("profile/profile/words/", _yonlendir("sozluk", sorgu="?sekme=listem")),

    # Çalışmalar
    path("exercises/", _yonlendir("learn_pass_page")),
    path("exercises/learn/", _yonlendir("learn_pass_page")),
    path("exercises/learn/<str:mode>/", _ayni_parcalarla("learn_pass_run")),
    path("egzersizler/", _yonlendir("exercises_page")),
    path("quizzes/quizzes/quiz-page/", _yonlendir("exercises_page")),
    path("quizzes/quizzes/quiz-review/", _yonlendir("exercises_page")),
    path("profile/profile/quizzes/", _yonlendir("exercises_page")),

    # Okumalar
    path("readings/", _yonlendir("readings")),
    path("readings/kutuphane/<int:number>/", _kutuphane_metni),
    path("readings/metinlerim/ekle/", _yonlendir("readings_add")),
    path("readings/metinlerim/<int:pk>/", _ayni_parcalarla("readings_user_text")),

    # Yazma
    path("texts/", _yonlendir("profile_texts")),
    path("texts/yaz/", _yonlendir("new_text_page")),
    path("texts/puanlama/", _yonlendir("about_grading_page")),
    path("texts/diyalog/", _yonlendir("diyalog_page")),
    path("texts/<int:text_id>/", _ayni_parcalarla("review_text")),
    path("texts/texts/new-text/", _yonlendir("new_text_page")),
    path("texts/texts/about-grading/", _yonlendir("about_grading_page")),
    path("texts/texts/reviews-text/<int:text_id>", _ayni_parcalarla("review_text")),
    path("profile/profile/texts/", _yonlendir("profile_texts")),

    # Seviye testi
    path("seviye/", _yonlendir("seviye_testi")),

    # Hesap
    path("users/login/", _yonlendir("login")),
    path("users/register/", _yonlendir("register")),
    path("users/forgot-password/", _yonlendir("forgot_password")),
    path("users/change-password-page/", _yonlendir("change_password_page")),
    path("profile/profile/", _yonlendir("user_profile")),
    path("profile/profile/myaccount/", _yonlendir("user_profile")),
    path("profile/profile/settings/", _yonlendir("user_profile")),
    path("profile/profile/show-user-profile/<int:user_id>", _ayni_parcalarla("show_user_profile")),

    path("about/", _yonlendir("about")),
]
