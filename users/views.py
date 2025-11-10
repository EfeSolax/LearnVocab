from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.conf import settings
from users.models import User

# Kullanıcıya çıktı vermek için mesajlar import edelim.
from django.contrib import messages
import random

# Burada hazırladığımız user modelini import ediyoruz.
from .models import User
from usersettings.models import UserSettings
from django.contrib.auth.decorators import login_required

"""

Django'da request çeşitleri 3 tanedir:

GET  => sayfa görüntüleme için veri isteyen request'tir.
POST => sayfaya form göndermek için veri gönderen request'tir.
PUT, DELETE, PATCH => Daha çok API ve güncelleme işlemlerinde kullanılan request'tir.

"""


# Kayıt olma işlemi için register fonksiyonu çalıştırılacak.
def register(request):
    
    # Kullanıcı form göndermiş ise
    if request.method == "POST":
        # Request ile gelen formu al.

        name = request.POST.get("first_name").strip()
        surname = request.POST.get("last_name").strip()
        username = request.POST.get("username").strip()
        email = request.POST.get("email").strip().lower()
        level = request.POST.get("level")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")        


        # Şifre eşleşmesi ve şifrenin en az 8 karakterde olması ve kullanıcı adının daha önce bulunmuyor
        # olmasının kontrollerini form.is_valid()'den önce yapıyoruz çünkü eğer bunu yapmazsak django
        # form.is_valid()'i false döndürüyor ve kullanıcıya form başarılı bir şekilde alınamadı hatası
        # veriliyor bunun önüne geçmek için if form.is_valid()'den önce bizim bu kontrolleri manuel olarak 
        # yapmamız gerekiyor.

        if (password1 != password2):
            messages.error(request, "Şifreler uyuşmuyor!")
            return redirect("register")
        
        if (len(password1) < 8):
            messages.error(request, "Şifreniz en az 8 karakter içermelidir!")
            return redirect("register")
        
        if User.objects.filter(username = username).exists():
            messages.error(request, "Bu kullanıcı adı alınmış.")
            return redirect("register")
        
        if (level == None):
            messages.error(request, "Lütfen seviye (kur) seçiniz.")
            return redirect("register")
                
        if (checkThePassword(password1) != "correct"):
            messages.error(request, checkThePassword(password1))
            return redirect("register")
        

        # Eğer form doğru ise kaydet başarı mesajı göster ve kullanıcıyı login sayfasına yönlendir.
          
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=name,
            last_name=surname
        )
        if hasattr(user, "level"):
            user.level = level
            user.save()
        
        usersettings = UserSettings.objects.create(
            user = user
        )
        usersettings.save()

        messages.success(request, "Başarılı bir şekilde kaydınız yapıldı. Artık giriş yapabilirsiniz!")
        #return redirect("login")
        return redirect("login")

    return render(request, "pages/users/register.html")

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
        username = request.POST.get("username").strip()
        password = request.POST.get("password")

        # Email ile giriş yapılacağı için önce username'i bulmamız gerekiyor
        from .models import User
        try:
            user_obj = User.objects.get(username = username)
        except User.DoesNotExist:
            messages.error(request, "Bu kullanıcı adına sahip bir hesap bulunamadı.")
            return redirect("login")

        # Kullanıcı doğrulama
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Hoş geldin, {username}!")
            return redirect("index")
        else:
            messages.error(request, "Kullanıcı adı veya şifre hatalı!")
            return redirect("login")
        
    

    return render(request, "pages/users/login.html")

def logout_user(request):
    
    logout(request)
    messages.success(request, "Başarıyla çıkış yaptınız.")
    return redirect("index")

@login_required
def changePasswordPage(request):
    return render(request, "pages/users/changePasswordWithoutMail.html")

@login_required
def changePassword(request):
    if request.method == "POST":
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Girdiğiniz şifreler uyuşmuyor.")
            return redirect("change_password_page")
        
        result = checkThePassword(password1)
        if result != "correct":
            messages.error(request, result)
            return redirect("change_password_page")
        
        current_user = request.user
        current_user.set_password(password1)
        current_user.save()
        messages.success(request, "Şifreniz başarılı bir şekilde değiştirildi.")
    
    return redirect("index")

def forgotPassword(request):
    return render(request, "pages/users/forgotPassword1.html")

def sendVerificationCode(request):
    
    if request.method == "POST":
        username = request.POST.get("username")
        user = User.objects.filter(username = username)

        if not user.exists():
            messages.error(request, "Bu kullanıcı adına sahip bir kullanıcı bulunamadı")
            return redirect("login")
        
        user = user.first()
        mail = user.email
        code = random.randint(100000,999999)

        subject = 'LearnVocab Şifre Sıfırlama'
        message = (
            f"Merhaba, {username}\n\n"
            f"İşte şifreni yenilemek için kodun: {code}\n\n "
            "Eğer bu şifre yenileme isteğini siz oluşturmadıysanız bu mail'i görmezden gelebilirsiniz."
        )
        
        # Gönderen e-posta (settings.py'den alınır)
        from_email = settings.DEFAULT_FROM_EMAIL 
        
        # Alıcı (Test için kendi e-postanızı yazın)
        # ÖNEMLİ: Burası bir liste olmalıdır!
        recipient_list = [mail]

        # 2. E-postayı Gönderin
        try:
            send_mail(
                subject,        # Konu
                message,        # Mesaj (düz metin)
                from_email,     # Gönderen
                recipient_list, # Alıcılar (liste olarak)
                fail_silently=False, # Hata olursa program dursun (bize söylesin)
            )
            
            messages.success(request, "E-posta başarıyla gönderildi!")
            
        except Exception as e:
            # Eğer settings.py'deki şifre yanlışsa veya bağlantı sorunu varsa:
            print(f"E-posta gönderilemedi: {e}")
            messages.error(request, f"E-posta gönderilirken bir hata oluştu.")

        request.session['verification_code'] = code
        request.session['username'] = username

    return render(request, "pages/users/mailVerification.html")

def verifyCode(request):
    
    if request.method == "POST":
        enteredCode = request.POST.get("verification_code")
        
        verificationCode = request.session.get("verification_code")
        
        if 'verification_code' in request.session:
            del request.session['verification_code']
        
        if str(verificationCode) == str(enteredCode):
            request.session["mail_code_verification"] = True
            messages.success(request, "Kodu doğru girdiniz. Artık yeni şifrenizi oluşturabilirsiniz.")
            return render(request, "pages/users/changePasswordWithMail.html")
        else:
            messages.error(request, "Yanlış kod girildi. Tekrar deneyiniz.")

    return redirect("login")

def changePasswordWithMail(request):
    
    if request.method == "POST":
        if request.session.get("mail_code_verification"):
            username = request.session.get("username")

            if 'mail_code_verification' in request.session:
                del request.session['mail_code_verification']

            if 'username' in request.session:
                del request.session['username']

            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")

            if password1 != password2:
                messages.error(request, "Girdiğiniz şifreler uyuşmuyor")
                return redirect("change_password_with_mail")
            
            result = checkThePassword(password1)
            if result != "correct":
                messages.error(request, result)
                return redirect("change_password_with_mail")
            
            user = User.objects.filter(username = username).first()
            user.set_password(password1)
            user.save()
            messages.success(request, "Şifreniz başarıyla değiştirildi. Artık giriş yapabilirsiniz!")

    return redirect("login")
        
