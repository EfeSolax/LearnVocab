from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.cache import cache
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from users.models import User

# Kullanıcıya çıktı vermek için mesajlar import edelim.
from django.contrib import messages

from LearnVocab.authgate import GIRIS_NEDENLERI, giris_adresi, giris_notu, guvenli_sonraki
import random

# Burada hazırladığımız user modelini import ediyoruz.
from .models import User
from usersettings.models import UserSettings
from django.contrib.auth.decorators import login_required

# Şifre sıfırlama akışı için sabitler
PASSWORD_RESET_CODE_TTL_SECONDS = 10 * 60   # kod 10 dakika geçerli
PASSWORD_RESET_RESEND_SECONDS = 60          # aynı kişiye en fazla 60 sn'de bir mail
PASSWORD_RESET_MAX_ATTEMPTS = 5             # en fazla 5 yanlış kod denemesi


def _clear_password_reset_session(request):
    """Şifre sıfırlama akışına ait tüm session anahtarlarını temizler."""
    for key in (
        "verification_code",
        "verification_code_expires_at",
        "verification_attempts",
        "username",
        "mail_code_verification",
    ):
        request.session.pop(key, None)

"""

Django'da request çeşitleri 3 tanedir:

GET  => sayfa görüntüleme için veri isteyen request'tir.
POST => sayfaya form göndermek için veri gönderen request'tir.
PUT, DELETE, PATCH => Daha çok API ve güncelleme işlemlerinde kullanılan request'tir.

"""


# Kayıt olma işlemi için register fonksiyonu çalıştırılacak.
def register(request):
    """Kullanıcı kayıt görünümü."""

    # POST değilse formu göster
    if request.method != "POST":
        return render(request, "pages/users/register.html")

    # POST verilerini güvenli al (None gelirse "" varsayalım)
    name      = (request.POST.get("first_name") or "").strip()
    surname   = (request.POST.get("last_name") or "").strip()
    username  = (request.POST.get("username") or "").strip()
    email     = (request.POST.get("email") or "").strip().lower()
    level     = request.POST.get("level")
    password1 = request.POST.get("password1") or ""
    password2 = request.POST.get("password2") or ""

    # --- Validasyon ---
    if not username:
        messages.error(request, "Kullanıcı adı boş olamaz.")
        return redirect("register")

    if not email:
        messages.error(request, "E-posta boş olamaz.")
        return redirect("register")

    if password1 != password2:
        messages.error(request, "Şifreler uyuşmuyor!")
        return redirect("register")

    pwd_check = checkThePassword(password1)
    if pwd_check != "correct":
        messages.error(request, pwd_check)
        return redirect("register")

    if User.objects.filter(username__iexact=username).exists():
        messages.error(request, "Bu kullanıcı adı alınmış.")
        return redirect("register")

    if User.objects.filter(email__iexact=email).exists():
        messages.error(request, "Bu e-posta adresi ile daha önce kayıt yapılmış.")
        return redirect("register")

    if not level:
        messages.error(request, "Lütfen seviye (kur) seçiniz.")
        return redirect("register")

    try:
        level_int = int(level)
        if level_int not in (1, 101, 201, 301, 401, 501):
            raise ValueError
    except (TypeError, ValueError):
        messages.error(request, "Geçersiz seviye seçimi.")
        return redirect("register")

    # --- Kayıt ---
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password1,
        first_name=name,
        last_name=surname,
    )
    user.level = level_int
    user.save()

    UserSettings.objects.create(user=user)

    messages.success(request, "Başarılı bir şekilde kaydınız yapıldı. Artık giriş yapabilirsiniz!")
    return redirect("login")
def checkThePassword(s):
    if (len(s) < 8):
        return "Şifre en az 8 karakterli olmalıdır."
    
    digits = "0123456789"
    lowerCase = "abcçdefgğhıijklmnoöprsştuüvyzxwq"

    containsDigits = False
    containsLowerCase = False
    containsUpperCase = False

    for i in s:
        if (i in digits):
            containsDigits = True
        elif (i in lowerCase):
            containsLowerCase = True
        elif (i in lowerCase.upper()):
            containsUpperCase = True
    
    if (not containsDigits):
        return "Şifre en az bir tane rakam içermelidir."
    
    if (not containsLowerCase):
        return "Şifre en az bir tane küçük harf içermelidir."
    
    if (not containsUpperCase):
        return "Şifre en az bir tane büyük harf içermelidir."
    
    return "correct"

# Login olma işlemi için bu fonksiyon çalışacak
def login_user(request):
    
    # Eğer form gönderilmişse
    if request.method == "POST":
        # .get() None dönebilir; doğrudan .strip() çağırmak 500 hatasına yol açıyordu
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        # Kullanıcı doğrulama.
        # NOT: Burada önceden "bu kullanıcı adı var mı" diye ayrı bir sorgu yapılıyordu;
        # bu, kayıtlı kullanıcı adlarının tek tek denenerek tespit edilmesine
        # (user enumeration) izin veriyordu. Artık tek ve genel bir mesaj veriyoruz.
        user = authenticate(request, username=username, password=password)

        # Giriş gerektiren bir düğmeden gelindiyse (?next=) oraya dönülür.
        # Yalnızca bu sitenin adresleri kabul ediliyor (bkz. authgate).
        sonraki = guvenli_sonraki(request)

        if user is not None:
            login(request, user)
            messages.success(request, f"Hoş geldin, {username}!")
            return redirect(sonraki or "index")
        else:
            messages.error(request, "Kullanıcı adı veya şifre hatalı!")
            # Hatalı denemede ?next= ve açıklama kaybolmasın.
            return redirect(giris_adresi(sonraki, request.POST.get("neden")))

    return render(request, "pages/users/login.html", {
        "sonraki": guvenli_sonraki(request) or "",
        # Yalnızca bilinen açıklama anahtarları taşınır (bkz. authgate.GIRIS_NEDENLERI).
        "neden": request.GET.get("neden") if request.GET.get("neden") in GIRIS_NEDENLERI else "",
        "giris_notu": giris_notu(request),
    })

def logout_user(request):
    
    logout(request)
    messages.success(request, "Başarıyla çıkış yaptınız.")
    return redirect("index")

@login_required
def changePasswordPage(request):
    return render(request, "pages/users/changePasswordWithoutMail.html")

@login_required
def changePassword(request):
    if request.method != "POST":
        return redirect("change_password_page")

    oldPassword = request.POST.get("oldPassword") or ""
    password1 = request.POST.get("password1")
    password2 = request.POST.get("password2")

    # Mevcut şifre doğrulaması: oturumu ele geçiren biri şifreyi değiştirememeli
    if not request.user.check_password(oldPassword):
        messages.error(request, "Mevcut şifrenizi hatalı girdiniz.")
        return redirect("change_password_page")

    if password1 != password2:
        messages.error(request, "Girdiğiniz şifreler uyuşmuyor.")
        return redirect("change_password_page")

    if oldPassword == password1:
        messages.error(request, "Yeni şifreniz mevcut şifrenizle aynı olamaz.")
        return redirect("change_password_page")

    result = checkThePassword(password1)
    if result != "correct":
        messages.error(request, result)
        return redirect("change_password_page")

    current_user = request.user
    current_user.set_password(password1)
    current_user.save()

    # set_password sonrası session auth hash değişir; bu çağrı olmazsa
    # kullanıcı kendi şifresini değiştirdiği anda sistemden atılır.
    update_session_auth_hash(request, current_user)

    messages.success(request, "Şifreniz başarılı bir şekilde değiştirildi.")
    return redirect("index")

def forgotPassword(request):
    return render(request, "pages/users/forgotPassword1.html")

def sendVerificationCode(request):
    """
    Şifre sıfırlama kodu gönderir.

    Güvenlik notları:
    - Kullanıcı adının kayıtlı olup olmadığı ele verilmez (user enumeration).
    - Aynı hesaba art arda mail atılamaz (mail bombing koruması).
    - Üretilen kodun geçerlilik süresi vardır.
    """
    if request.method != "POST":
        return redirect("forgot_password")

    username = (request.POST.get("username") or "").strip()

    # Aynı oturumdan çok sık istek atılmasını engelle
    last_sent_at = request.session.get("verification_code_sent_at")
    now_ts = timezone.now().timestamp()
    if last_sent_at and (now_ts - float(last_sent_at)) < PASSWORD_RESET_RESEND_SECONDS:
        remaining = int(PASSWORD_RESET_RESEND_SECONDS - (now_ts - float(last_sent_at)))
        messages.error(
            request,
            f"Çok sık kod talep ettiniz. Lütfen {remaining} saniye sonra tekrar deneyin."
        )
        return render(request, "pages/users/mailVerification.html")

    user = User.objects.filter(username=username).first()

    # Aynı hesaba dakikada birden fazla mail gitmesin (oturumdan bağımsız koruma)
    throttle_key = f"pwreset:{username.lower()}"
    already_sent = cache.get(throttle_key) if username else None

    if user and not already_sent:
        code = random.randint(100000, 999999)

        subject = 'LearnVocab Şifre Sıfırlama'
        message = (
            f"Merhaba, {username}\n\n"
            f"İşte şifreni yenilemek için kodun: {code}\n\n"
            f"Bu kod {PASSWORD_RESET_CODE_TTL_SECONDS // 60} dakika boyunca geçerlidir.\n\n"
            "Eğer bu şifre yenileme isteğini siz oluşturmadıysanız bu mail'i görmezden gelebilirsiniz."
        )

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            # Kodu ve son kullanma zamanını sadece mail gerçekten gidince sakla
            request.session['verification_code'] = code
            request.session['verification_code_expires_at'] = now_ts + PASSWORD_RESET_CODE_TTL_SECONDS
            request.session['verification_attempts'] = 0
            request.session['username'] = username
            cache.set(throttle_key, True, PASSWORD_RESET_RESEND_SECONDS)
        except Exception as e:
            # Mail ayarları hatalıysa veya bağlantı sorunu varsa
            print(f"E-posta gönderilemedi: {e}")

    request.session['verification_code_sent_at'] = now_ts

    # Kullanıcı var da olsa yok da olsa AYNI mesaj verilir.
    messages.success(
        request,
        "Bu kullanıcı adı kayıtlıysa, hesaba tanımlı e-posta adresine bir doğrulama kodu gönderildi."
    )
    return render(request, "pages/users/mailVerification.html")


def verifyCode(request):
    """Kullanıcının girdiği doğrulama kodunu kontrol eder."""
    if request.method != "POST":
        return redirect("login")

    enteredCode = (request.POST.get("verification_code") or "").strip()
    verificationCode = request.session.get("verification_code")
    expires_at = request.session.get("verification_code_expires_at")

    # Kod hiç üretilmemişse ya da süresi dolmuşsa akışı bitir
    if not verificationCode or not expires_at or timezone.now().timestamp() > float(expires_at):
        _clear_password_reset_session(request)
        messages.error(request, "Doğrulama kodunuzun süresi doldu. Lütfen yeniden kod talep edin.")
        return redirect("forgot_password")

    # Deneme sayısını sınırla (kaba kuvvet denemesine karşı)
    attempts = int(request.session.get("verification_attempts", 0)) + 1
    request.session["verification_attempts"] = attempts

    if attempts > PASSWORD_RESET_MAX_ATTEMPTS:
        _clear_password_reset_session(request)
        messages.error(request, "Çok fazla hatalı deneme yaptınız. Lütfen yeniden kod talep edin.")
        return redirect("forgot_password")

    if str(verificationCode) == str(enteredCode):
        # Kod tek kullanımlıktır; doğrulandıktan sonra silinir
        request.session.pop("verification_code", None)
        request.session.pop("verification_code_expires_at", None)
        request.session.pop("verification_attempts", None)
        request.session["mail_code_verification"] = True
        messages.success(request, "Kodu doğru girdiniz. Artık yeni şifrenizi oluşturabilirsiniz.")
        return render(request, "pages/users/changePasswordWithMail.html")

    kalan = PASSWORD_RESET_MAX_ATTEMPTS - attempts
    messages.error(request, f"Yanlış kod girildi. Kalan deneme hakkınız: {kalan}")
    return render(request, "pages/users/mailVerification.html")


def changePasswordWithMail(request):
    """
    Mail ile doğrulama yapmış kullanıcının yeni şifresini kaydeder.

    ÖNEMLİ: Doğrulama bayrakları, şifre kontrolleri BAŞARILI olduktan sonra silinir.
    (Eskiden en başta siliniyordu; şifreler uyuşmadığında kullanıcı akışın
    ortasında kalıyor ve bir daha devam edemiyordu.)
    """
    if request.method != "POST":
        return redirect("login")

    if not request.session.get("mail_code_verification"):
        messages.error(request, "Önce e-posta ile doğrulama yapmalısınız.")
        return redirect("forgot_password")

    password1 = request.POST.get("password1")
    password2 = request.POST.get("password2")

    if password1 != password2:
        messages.error(request, "Girdiğiniz şifreler uyuşmuyor.")
        return render(request, "pages/users/changePasswordWithMail.html")

    result = checkThePassword(password1)
    if result != "correct":
        messages.error(request, result)
        return render(request, "pages/users/changePasswordWithMail.html")

    username = request.session.get("username")
    user = User.objects.filter(username=username).first()

    if not user:
        _clear_password_reset_session(request)
        messages.error(request, "İşlem tamamlanamadı. Lütfen yeniden kod talep edin.")
        return redirect("forgot_password")

    user.set_password(password1)
    user.save()

    # Akış başarıyla bittiği için tüm doğrulama bilgilerini temizle
    _clear_password_reset_session(request)

    messages.success(request, "Şifreniz başarıyla değiştirildi. Artık giriş yapabilirsiniz!")
    return redirect("login")
