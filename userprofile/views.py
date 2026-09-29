from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages

from LearnVocab.authgate import login_gate
from users.models import User
from usersettings.models import UserSettings
from words.models import Word

# Eski Kelimelerim sayfası, kelime klasörleri (WordList), elle kelime ekleme/
# düzenleme ve toplu ekleme/silme 29 Eylül'de kaldırıldı (rapor 18.13).
# Kullanıcının listesi artık Sözlük › Listem'de (words/listem.py).

# "Profilim" sayfasındaki günlük hedef seçenekleri.
# Değerler int: şablon `settings.dailyGoal == deger` karşılaştırmasını
# bunun üzerinden yapıyor.
DAILY_GOAL_OPTIONS = (
    (0, "Yok"),
    (5, "5"),
    (10, "10"),
    (15, "15"),
    (20, "20"),
)


#Ana profil sayfasının görünümü 
@login_gate("Profilim")
def showProfile(request):
    """
    "Profilim" sayfası.

    Eskiden üç ayrı sayfa vardı: profil özeti, "Hesap Bilgilerim" ve "Ayarlar".
    Üçü de aynı şeyin parçasıydı, kullanıcıyı sekmeler arasında gezdiriyordu;
    tek sayfada birleştirildi. Hesap bilgisi formu da buraya POST ediyor.
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
        messages.success(request, "Hesap bilgileriniz başarıyla güncellendi.")
        return redirect("user_profile")

    context = {
        "active_page": "Profilim",
        "settings": UserSettings.objects.filter(user=request.user).first(),
        "daily_goal_options": DAILY_GOAL_OPTIONS,
        "export_links": [
            {"url": reverse("export_all"), "label": "Tüm verilerim"},
            {"url": reverse("export_mywords"), "label": "Kelimelerim"},
            {"url": reverse("export_mytexts"), "label": "Metinlerim"},
        ],
    }

    return render(request, "pages/profile/myprofile.html", context)


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
