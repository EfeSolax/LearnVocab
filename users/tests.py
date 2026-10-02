"""
Kimlik doğrulama ve şifre işlemleri için regresyon testleri.

Kapsanan hatalar:
- Şifre değiştirirken mevcut şifre sorulmuyordu.
- Şifre değiştirdikten sonra kullanıcı sistemden atılıyordu (update_session_auth_hash yok).
- Mail ile şifre sıfırlamada şifreler uyuşmazsa akış kilitleniyordu.
- Doğrulama kodunun süresi ve deneme limiti yoktu.
- Giriş ekranı, kayıtlı kullanıcı adlarını ele veriyordu (user enumeration).
"""

from django.contrib.messages import get_messages
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from users.models import User

LOCMEM_MAIL = "django.core.mail.backends.locmem.EmailBackend"

OLD_PASSWORD = "EskiSifre123"
NEW_PASSWORD = "YeniSifre456"


def messages_of(response):
    return [str(m) for m in get_messages(response.wsgi_request)]


class ChangePasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="efe", email="efe@example.com", password=OLD_PASSWORD
        )
        self.client.login(username="efe", password=OLD_PASSWORD)
        self.url = reverse("change_password")

    def test_old_password_is_required(self):
        response = self.client.post(
            self.url, {"password1": NEW_PASSWORD, "password2": NEW_PASSWORD}
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD), "şifre değişmemeliydi")
        self.assertFalse(self.user.check_password(NEW_PASSWORD))
        self.assertRedirects(response, reverse("change_password_page"))

    def test_wrong_old_password_is_rejected(self):
        self.client.post(
            self.url,
            {
                "oldPassword": "TamamenBaska1",
                "password1": NEW_PASSWORD,
                "password2": NEW_PASSWORD,
            },
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD))

    def test_mismatched_passwords_are_rejected(self):
        self.client.post(
            self.url,
            {
                "oldPassword": OLD_PASSWORD,
                "password1": NEW_PASSWORD,
                "password2": NEW_PASSWORD + "x",
            },
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD))

    def test_new_password_cannot_equal_old_one(self):
        self.client.post(
            self.url,
            {
                "oldPassword": OLD_PASSWORD,
                "password1": OLD_PASSWORD,
                "password2": OLD_PASSWORD,
            },
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD))

    def test_successful_change_keeps_user_logged_in(self):
        self.client.post(
            self.url,
            {
                "oldPassword": OLD_PASSWORD,
                "password1": NEW_PASSWORD,
                "password2": NEW_PASSWORD,
            },
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))

        # update_session_auth_hash olmasaydı bu istek login'e yönlenirdi
        response = self.client.get(reverse("change_password_page"))
        self.assertEqual(response.status_code, 200)

    def test_get_request_does_not_change_anything(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("change_password_page"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD))


@override_settings(EMAIL_BACKEND=LOCMEM_MAIL)
class PasswordResetFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        mail.outbox = []
        self.user = User.objects.create_user(
            username="efe", email="efe@example.com", password=OLD_PASSWORD
        )
        self.send_url = reverse("send_verification_code")
        self.verify_url = reverse("verify_code")
        self.change_url = reverse("change_password_with_mail")

    def _request_code(self):
        self.client.post(self.send_url, {"username": "efe"})
        return self.client.session.get("verification_code")

    def test_code_is_emailed_and_stored_with_expiry(self):
        code = self._request_code()
        self.assertIsNotNone(code)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(code), mail.outbox[0].body)
        self.assertIsNotNone(self.client.session.get("verification_code_expires_at"))

    def test_unknown_username_does_not_leak_and_sends_no_mail(self):
        response = self.client.post(self.send_url, {"username": "boyle-biri-yok"})
        self.assertEqual(len(mail.outbox), 0)
        self.assertIsNone(self.client.session.get("verification_code"))
        text = " ".join(messages_of(response))
        self.assertIn("kayıtlıysa", text)

    def test_same_message_for_known_and_unknown_username(self):
        known = " ".join(messages_of(self.client.post(self.send_url, {"username": "efe"})))
        other = self.client_class()
        unknown = " ".join(messages_of(other.post(self.send_url, {"username": "yok"})))
        self.assertEqual(known, unknown)

    def test_resend_is_throttled(self):
        self._request_code()
        mail.outbox = []
        self.client.post(self.send_url, {"username": "efe"})
        self.assertEqual(len(mail.outbox), 0, "art arda mail gönderilmemeli")

    def test_wrong_code_does_not_destroy_the_flow(self):
        code = self._request_code()
        self.client.post(self.verify_url, {"verification_code": "000000"})
        # Kod hâlâ geçerli olmalı; kullanıcı doğrusunu girebilmeli
        self.client.post(self.verify_url, {"verification_code": str(code)})
        self.assertTrue(self.client.session.get("mail_code_verification"))

    def test_too_many_attempts_ends_the_flow(self):
        self._request_code()
        for _ in range(6):
            self.client.post(self.verify_url, {"verification_code": "000000"})
        self.assertIsNone(self.client.session.get("verification_code"))

    def test_expired_code_is_rejected(self):
        code = self._request_code()
        session = self.client.session
        session["verification_code_expires_at"] = 0  # süresi çoktan doldu
        session.save()

        self.client.post(self.verify_url, {"verification_code": str(code)})
        self.assertIsNone(self.client.session.get("mail_code_verification"))

    def test_mismatched_passwords_do_not_lock_the_user_out(self):
        """
        Eski kodda doğrulama bayrakları en başta siliniyordu; şifreler uyuşmazsa
        kullanıcı bir daha devam edemiyordu.
        """
        code = self._request_code()
        self.client.post(self.verify_url, {"verification_code": str(code)})

        self.client.post(
            self.change_url, {"password1": NEW_PASSWORD, "password2": "BaskaSifre1"}
        )
        self.assertTrue(
            self.client.session.get("mail_code_verification"),
            "hatalı denemeden sonra da akış devam edebilmeli",
        )

        self.client.post(
            self.change_url, {"password1": NEW_PASSWORD, "password2": NEW_PASSWORD}
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))

    def test_cannot_change_password_without_verifying(self):
        self.client.post(
            self.change_url, {"password1": NEW_PASSWORD, "password2": NEW_PASSWORD}
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD))

    def test_session_is_cleared_after_success(self):
        code = self._request_code()
        self.client.post(self.verify_url, {"verification_code": str(code)})
        self.client.post(
            self.change_url, {"password1": NEW_PASSWORD, "password2": NEW_PASSWORD}
        )
        for key in ("verification_code", "mail_code_verification", "username"):
            self.assertIsNone(self.client.session.get(key))


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="efe", email="efe@example.com", password=OLD_PASSWORD
        )
        self.url = reverse("login")

    def test_successful_login(self):
        response = self.client.post(self.url, {"username": "efe", "password": OLD_PASSWORD})
        self.assertRedirects(response, reverse("index"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_unknown_user_and_wrong_password_give_the_same_message(self):
        wrong_password = messages_of(
            self.client.post(self.url, {"username": "efe", "password": "YanlisSifre1"})
        )
        other = self.client_class()
        unknown_user = messages_of(
            other.post(self.url, {"username": "hicyok", "password": "YanlisSifre1"})
        )
        self.assertEqual(wrong_password, unknown_user)
        self.assertNotIn("_auth_user_id", self.client.session)


class GoogleGirisTests(TestCase):
    """Google ile giriş (rapor 18.21): düğme, adresler ve ilk girişte ayar satırı."""

    def test_dugme_anahtar_varsa_giris_ve_kayit_sayfasinda(self):
        from django.test import override_settings
        with override_settings(GOOGLE_GIRIS_ACIK=True):
            for ad in ("login", "register"):
                html = self.client.get(reverse(ad)).content.decode()
                self.assertIn("data-google-giris", html)
                self.assertIn('action="/accounts/google/login/', html)
                self.assertIn('method="post"', html)
        with override_settings(GOOGLE_GIRIS_ACIK=False):
            self.assertNotIn("data-google-giris", self.client.get(reverse("login")).content.decode())

    def test_allauth_kendi_sayfalari_bizimkilere_yonlenir(self):
        self.assertRedirects(self.client.get("/accounts/login/"), reverse("login"), fetch_redirect_response=False)
        self.assertRedirects(self.client.get("/accounts/signup/"), reverse("register"), fetch_redirect_response=False)

    def test_google_ile_ilk_giriste_ayar_satiri(self):
        from allauth.account.signals import user_signed_up
        from django.test import RequestFactory
        from usersettings.models import UserSettings
        u = User.objects.create_user(username="googleci", email="g@example.com", password="Sifre1234")
        user_signed_up.send(sender=User, request=RequestFactory().get("/"), user=u)
        self.assertTrue(UserSettings.objects.filter(user=u).exists())
