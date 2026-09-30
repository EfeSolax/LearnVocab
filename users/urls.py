"""Hesap adresleri (rapor 18.15). LearnVocab/urls.py bunları köke bağlar."""

from django.urls import path

from . import views

urlpatterns = [
    path("giris/", views.login_user, name="login"),
    path("kayit/", views.register, name="register"),
    path("cikis/", views.logout_user, name="logout"),
    path("sifre-degistir/", views.changePasswordPage, name="change_password_page"),
    path("sifre-degistir/kaydet/", views.changePassword, name="change_password"),
    path("sifremi-unuttum/", views.forgotPassword, name="forgot_password"),
    path("sifremi-unuttum/kod-gonder/", views.sendVerificationCode, name="send_verification_code"),
    path("sifremi-unuttum/dogrula/", views.verifyCode, name="verify_code"),
    path("sifremi-unuttum/yeni-sifre/", views.changePasswordWithMail,
         name="change_password_with_mail"),
]
