"""
Önceden açılmış hesapla ele geçirme (8 Ekim): saldırgan kurbanın e-postasıyla şifreli
hesap açar; kurban sonra "Google ile giriş" yapar. Kayıt formumuz e-postayı
doğrulanmış saymadığı için allauth hesabın şifresini siler; şifre değişince
saldırganın açık oturumu da düşer. Bu test o zinciri korur.
"""
from allauth.account.models import EmailAddress
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

User = get_user_model()
SIFRE = "Saldirgan123"


GOOGLE = {"google": {**settings.SOCIALACCOUNT_PROVIDERS["google"],
                     "APP": {"client_id": "test", "secret": "test", "key": ""}}}


@override_settings(SOCIALACCOUNT_PROVIDERS=GOOGLE)
class OncedenAcilmisHesapTests(TestCase):
    def setUp(self):
        self.client.post(reverse("register"), {
            "first_name": "S", "last_name": "A", "username": "saldirgan",
            "email": "kurban@example.com", "password": SIFRE, "aydinlatma": "1"})
        self.user = User.objects.get(username="saldirgan")
        self.assertTrue(self.client.login(username="saldirgan", password=SIFRE))

    def _google_ile_giris(self):
        istek = RequestFactory().get("/accounts/google/login/callback/")
        SessionMiddleware(lambda r: None).process_request(istek)
        istek.session.save()
        istek.user = AnonymousUser()
        setattr(istek, "_messages", FallbackStorage(istek))
        from allauth.socialaccount.adapter import get_adapter
        saglayici = get_adapter().get_provider(istek, provider="google")
        giris = SocialLogin(
            provider=saglayici,
            account=SocialAccount(provider="google", uid="kurban-google-id",
                                  extra_data={"email": "kurban@example.com"}),
            email_addresses=[EmailAddress(email="kurban@example.com", verified=True, primary=True)])
        giris.user = User(email="kurban@example.com")
        from allauth.core import context
        with context.request_context(istek):
            complete_social_login(istek, giris)

    def test_kurbanin_google_girisi_saldirganin_sifresini_ve_oturumunu_dusurur(self):
        self._google_ile_giris()
        self.user.refresh_from_db()
        self.assertFalse(self.user.has_usable_password())
        self.assertTrue(SocialAccount.objects.filter(user=self.user, provider="google").exists())
        # Saldırganın açık oturumu geçersiz (şifre özeti değişti), şifresi de çalışmaz.
        self.assertFalse(self.client.get("/").wsgi_request.user.is_authenticated)
        self.assertFalse(self.client.login(username="saldirgan", password=SIFRE))
