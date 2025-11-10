# users/urls.py

# path (yol) ekleyebilmek için path'i, ve mevcut users'ın altındaki view yani görünümleri ayarlamak için
# users/views.py'yi import ediyoruz. 
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

# Login ve logout'tan sonra _user getirdik çünkü django'nun login ve logout için varsayılan fonksiyonları
# var. Karışmasın diye ekledik. 

urlpatterns = [
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name = "login"),
    path('change-password-page/', views.changePasswordPage, name = "change_password_page"),
    path('change-password/', views.changePassword, name = "change_password"),
    path('forgot-password/', views.forgotPassword, name = "forgot_password"),
    path('send-verification-code/', views.sendVerificationCode, name = "send_verification_code"),
    path('verify-code/', views.verifyCode, name = "verify_code"),
    path('change-password-with-mail/', views.changePasswordWithMail, name = "change_password_with_mail"),
]
