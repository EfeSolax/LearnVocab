from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.cache import cache
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from users.models import User

# Kullanıcıya çıktı vermek için mesajlar import edelim.
from django.contrib import messages
from django.utils.translation import gettext as _

from LearnVocab import diller, sinir
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

# Giriş ve kayıt denemeleri (8 Ekim): şifre tahmini ve toplu hesap açma.
GIRIS_ADRES_SINIRI = 20       # bir adresten 15 dakikada en çok giriş denemesi
GIRIS_HESAP_SINIRI = 10       # bir kullanıcı adına 15 dakikada en çok HATALI deneme
GIRIS_SURE = 15 * 60
KAYIT_ADRES_SINIRI = 10       # bir adresten saatte en çok kayıt denemesi
KAYIT_SURE = 60 * 60


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


def register(request):
    """
    Kayıt (rapor 18.23): ad, soyad, e-posta, kullanıcı adı, şifre.

    Şifre TEK kez alınır ("göster / gizle" düğmesi formda). Eski "kur" seçimi
    yok: seviye, seviye testinden ya da "Seviyemi kendim seçeyim"den gelir.
    Hata olursa form yazılanlarla birlikte yeniden çizilir (şifre hariç).
    """
    if request.method != "POST":
        return render(request, "pages/users/register.html", {"degerler": {}})
    if sinir.asildi(f"kayit:{sinir.istemci(request)}", KAYIT_ADRES_SINIRI, KAYIT_SURE):
        messages.error(request, _("Çok fazla deneme yapıldı. Lütfen biraz sonra tekrar dene."))
        return render(request, "pages/users/register.html", {"degerler": {}}, status=429)

    degerler = {
        "first_name": (request.POST.get("first_name") or "").strip()[:150],
        "last_name": (request.POST.get("last_name") or "").strip()[:150],
        "username": (request.POST.get("username") or "").strip(),
        "email": (request.POST.get("email") or "").strip().lower(),
        "aydinlatma": bool(request.POST.get("aydinlatma")),
    }
    sifre = request.POST.get("password") or ""

    hata = None
    if not degerler["first_name"] or not degerler["last_name"]:
        hata = _("Adını ve soyadını yazar mısın?")
    elif not degerler["email"]:
        hata = _("E-posta boş olamaz.")
    elif not degerler["username"]:
        hata = _("Kullanıcı adı boş olamaz.")
    elif len(degerler["username"]) > 150:
        hata = _("Kullanıcı adı en çok 150 karakter olabilir.")
    elif not degerler["aydinlatma"]:
        hata = _("Hesap açmak için Aydınlatma Metni'ni okuduğunu onaylaman gerekiyor.")
    elif checkThePassword(sifre) != "correct":
        hata = checkThePassword(sifre)
    elif User.objects.filter(username__iexact=degerler["username"]).exists():
        hata = _("Bu kullanıcı adı alınmış.")
    elif User.objects.filter(email__iexact=degerler["email"]).exists():
        hata = _("Bu e-posta adresi ile daha önce kayıt yapılmış.")

    if hata:
        messages.error(request, hata)
        return render(request, "pages/users/register.html", {"degerler": degerler}, status=400)

    degerler.pop("aydinlatma")
    user = User.objects.create_user(password=sifre, aydinlatma_okundu=timezone.now(), **degerler)
    UserSettings.objects.create(user=user)

    messages.success(request, _("Başarılı bir şekilde kaydınız yapıldı. Artık giriş yapabilirsiniz!"))
    return redirect("login")


def checkThePassword(s):
    if (len(s) < 8):
        return _("Şifre en az 8 karakterli olmalıdır.")
    
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
        return _("Şifre en az bir tane rakam içermelidir.")
    
    if (not containsLowerCase):
        return _("Şifre en az bir tane küçük harf içermelidir.")
    
    if (not containsUpperCase):
        return _("Şifre en az bir tane büyük harf içermelidir.")
    
    return "correct"

# Login olma işlemi için bu fonksiyon çalışacak
def login_user(request):
    
    # Eğer form gönderilmişse
    if request.method == "POST":
        # .get() None dönebilir; doğrudan .strip() çağırmak 500 hatasına yol açıyordu
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        # Giriş gerektiren bir düğmeden gelindiyse (?next=) oraya dönülür.
        # Yalnızca bu sitenin adresleri kabul ediliyor (bkz. authgate).
        sonraki = guvenli_sonraki(request)

        # Şifre tahminine karşı: adres başına toplam, hesap başına hatalı deneme sınırı.
        hesap_anahtari = f"giris-hesap:{username.lower()}"
        if (sinir.asildi(f"giris:{sinir.istemci(request)}", GIRIS_ADRES_SINIRI, GIRIS_SURE)
                or sinir.oku(hesap_anahtari) >= GIRIS_HESAP_SINIRI):
            messages.error(request, _("Çok fazla deneme yapıldı. Lütfen birkaç dakika sonra tekrar dene."))
            return redirect(giris_adresi(sonraki, request.POST.get("neden")))

        # Kullanıcı doğrulama.
        # NOT: Burada önceden "bu kullanıcı adı var mı" diye ayrı bir sorgu yapılıyordu;
        # bu, kayıtlı kullanıcı adlarının tek tek denenerek tespit edilmesine
        # (user enumeration) izin veriyordu. Artık tek ve genel bir mesaj veriyoruz.
        user = authenticate(request, username=username, password=password)

        if user is not None:
            sinir.sifirla(hesap_anahtari)
            login(request, user)
            messages.success(request, _("Hoş geldin, %(ad)s!") % {"ad": username})
            # Hesapta kayıtlı arayüz dili varsa girişten sonra o dilde devam edilir (rapor 18.22).
            return diller.hesap_dili_ile_yonlendir(user, sonraki or reverse("index"))
        else:
            sinir.say(hesap_anahtari, GIRIS_SURE)
            messages.error(request, _("Kullanıcı adı veya şifre hatalı!"))
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
    messages.success(request, _("Başarıyla çıkış yaptınız."))
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
        messages.error(request, _("Mevcut şifrenizi hatalı girdiniz."))
        return redirect("change_password_page")

    if password1 != password2:
        messages.error(request, _("Girdiğiniz şifreler uyuşmuyor."))
        return redirect("change_password_page")

    if oldPassword == password1:
        messages.error(request, _("Yeni şifreniz mevcut şifrenizle aynı olamaz."))
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

    messages.success(request, _("Şifreniz başarılı bir şekilde değiştirildi."))
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
            _("Çok sık kod talep ettiniz. Lütfen %(n)s saniye sonra tekrar deneyin.") % {"n": remaining}
        )
        return render(request, "pages/users/mailVerification.html")

    # Bir adres saatte en çok 10 kod istesin (oturum değiştirerek aşılamasın).
    if sinir.asildi(f"sifre-kodu:{sinir.istemci(request)}", 10, 3600):
        messages.error(request, _("Çok fazla deneme yapıldı. Lütfen biraz sonra tekrar dene."))
        return render(request, "pages/users/mailVerification.html", status=429)

    user = User.objects.filter(username=username).first()

    # Aynı hesaba dakikada birden fazla mail gitmesin (oturumdan bağımsız koruma)
    throttle_key = f"pwreset:{username.lower()}"
    already_sent = cache.get(throttle_key) if username else None

    if user and not already_sent:
        code = random.randint(100000, 999999)

        subject = _("LearnVocab Şifre Sıfırlama")
        message = (
            _("Merhaba, %(ad)s") % {"ad": username} + "\n\n"
            + _("İşte şifreni yenilemek için kodun: %(kod)s") % {"kod": code} + "\n\n"
            + _("Bu kod %(dk)s dakika boyunca geçerlidir.") % {"dk": PASSWORD_RESET_CODE_TTL_SECONDS // 60} + "\n\n"
            + _("Eğer bu şifre yenileme isteğini siz oluşturmadıysanız bu mail'i görmezden gelebilirsiniz.")
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
        _("Bu kullanıcı adı kayıtlıysa, hesaba tanımlı e-posta adresine bir doğrulama kodu gönderildi.")
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
        messages.error(request, _("Doğrulama kodunuzun süresi doldu. Lütfen yeniden kod talep edin."))
        return redirect("forgot_password")

    # Deneme sayısını sınırla (kaba kuvvet denemesine karşı)
    attempts = int(request.session.get("verification_attempts", 0)) + 1
    request.session["verification_attempts"] = attempts

    if attempts > PASSWORD_RESET_MAX_ATTEMPTS:
        _clear_password_reset_session(request)
        messages.error(request, _("Çok fazla hatalı deneme yaptınız. Lütfen yeniden kod talep edin."))
        return redirect("forgot_password")

    if str(verificationCode) == str(enteredCode):
        # Kod tek kullanımlıktır; doğrulandıktan sonra silinir
        request.session.pop("verification_code", None)
        request.session.pop("verification_code_expires_at", None)
        request.session.pop("verification_attempts", None)
        request.session["mail_code_verification"] = True
        messages.success(request, _("Kodu doğru girdiniz. Artık yeni şifrenizi oluşturabilirsiniz."))
        return render(request, "pages/users/changePasswordWithMail.html")

    kalan = PASSWORD_RESET_MAX_ATTEMPTS - attempts
    messages.error(request, _("Yanlış kod girildi. Kalan deneme hakkınız: %(n)s") % {"n": kalan})
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
        messages.error(request, _("Önce e-posta ile doğrulama yapmalısınız."))
        return redirect("forgot_password")

    password1 = request.POST.get("password1")
    password2 = request.POST.get("password2")

    if password1 != password2:
        messages.error(request, _("Girdiğiniz şifreler uyuşmuyor."))
        return render(request, "pages/users/changePasswordWithMail.html")

    result = checkThePassword(password1)
    if result != "correct":
        messages.error(request, result)
        return render(request, "pages/users/changePasswordWithMail.html")

    username = request.session.get("username")
    user = User.objects.filter(username=username).first()

    if not user:
        _clear_password_reset_session(request)
        messages.error(request, _("İşlem tamamlanamadı. Lütfen yeniden kod talep edin."))
        return redirect("forgot_password")

    user.set_password(password1)
    user.save()

    # Akış başarıyla bittiği için tüm doğrulama bilgilerini temizle
    _clear_password_reset_session(request)

    messages.success(request, _("Şifreniz başarıyla değiştirildi. Artık giriş yapabilirsiniz!"))
    return redirect("login")
