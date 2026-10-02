from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from LearnVocab.authgate import login_gate
from users.models import User
from words.models import Word

# Eski Kelimelerim sayfası, kelime klasörleri (WordList), elle kelime ekleme/
# düzenleme ve toplu ekleme/silme 29 Eylül'de kaldırıldı (rapor 18.13).
# Kullanıcının listesi artık Sözlük › Listem'de (words/listem.py).

@login_gate(gettext_lazy("Hesap"))
def showProfile(request):
    """
    Hesap sayfası (rapor 18.26): sağ üstteki profil fotoğrafından açılır.
    Kimlik kartı, hesap bilgileri formu (buraya POST eder), parola ve
    Ayarlar bağlantısı. Ayarlar ayrı sayfada: usersettings.views.ayarlarSayfasi
    """
    if request.method == "POST":
        user = request.user
        user.email = request.POST.get("email") or user.email
        user.first_name = request.POST.get("first_name") or ""
        user.last_name = request.POST.get("last_name") or ""

        # Resim seçilmeden kaydedilirse eski resim silinmesin
        profile_pic_file = request.FILES.get("profile_pic")
        if profile_pic_file:
            user.profile_pic = profile_pic_file

        user.save()
        messages.success(request, _("Hesap bilgileriniz başarıyla güncellendi."))
        return redirect("user_profile")

    # Defterin künyesi (defter teması, rapor 18.12): yalnızca var olan sayılar; "öğrenilen kelime" yok (Bölüm 17).
    from seri import hesap as seri_hesap
    from users.seviye import kullanici_seviyesi
    from words.models import UserWordLink
    return render(request, "pages/profile/hesap.html", {
        "active_page": "Hesap",
        "liste_sayisi": UserWordLink.objects.filter(user=request.user).count(),
        "seri": seri_hesap.durum(request.user),
        "seviye": kullanici_seviyesi(request.user),
    })


# Arkadaşlık özelliği (friends) kapalı ama kodu duruyor; profil görüntüleme ona ait.
def showUserProfile(request, user_id):
    
    allUsers = User.objects.all()
    current_user = User.objects.filter(id = user_id).first()

    wordsAddedFromUser = Word.objects.filter(owner = current_user)
    wordsAddedByUser = Word.objects.filter(saved_by = current_user)
    friends = current_user.friends.all()

    context = {
        "allUsers":allUsers,
        "current_user":current_user,
        "wordsAddedFromUser":wordsAddedFromUser,
        "wordsAddedByUser":wordsAddedByUser,
        "friends":friends,
    }

    if (request.user.is_authenticated):
        return render(request, "pages/profile/showUserProfileWithAuthentication.html", context)
    else:
        return render(request, "pages/profile/showUserProfileWithoutAuthentication.html", context)
