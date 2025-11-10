from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from words.models import Word,UserWordLink
from users.models import User
from texts.models import Text
from django.contrib import messages
from usersettings.models import UserSettings

from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Q
from quizzes.models import MultipleChoiceQuestion, WritingQuestion, MatchingQuestion
from words.addWeeks.addWeeks import add101Weeks, add201Weeks, add301Weeks, add401Weeks

# Create your views here.

#Ana profil sayfasının görünümü 
@login_required
def showProfile(request):
    
    wordsAddedFromUser = Word.objects.filter(owner = request.user)
    wordsAddedByUser = Word.objects.filter(saved_by = request.user)
    friends = request.user.friends.all()
    allUsers = User.objects.all()

    context = {
        "active_page":"Hesap Bilgilerim",
        "wordsAddedFromUser":wordsAddedFromUser,
        "wordsAddedByUser":wordsAddedByUser,
        "friends":friends,
        "allUsers":allUsers,
    }

    return render(request, "pages/profile.html",context)

#Profilde "Kelimelerim" görünümü
@login_required
def showWordsView(request):
    
    #Kullanıcıya ait olan ve wordList'ine eklediği kelimeleri görüntüle
    words = Word.objects.filter(
        Q(owner=request.user) | 
        Q(saved_by=request.user)
    ).distinct()

    search_query = request.GET.get('q', '') # 'q' parametresini al, yoksa boş string ata

    if search_query:
        words = words.filter(
            Q(englishWord__icontains=search_query) |
            Q(meaningTr__icontains=search_query)
        )

    allUsers = User.objects.all()

    context = {
        "active_page":"Kelimelerim",
        "words":words,
        "allUsers":allUsers,
    }

    #Hangi sayfanın aktif olduğunu gönderiyoruz.
    return render(request, "pages/profile/words.html", context)

@login_required
def showMyAccountView(request):
    
    
    # 1. Form gönderilmişse (POST İsteği)
    if request.method == 'POST':
        # 2. Formdaki metin verilerini al
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # 3. Formdaki DOSYA verisini al (Modeldeki ad: 'profile_pic')
        #    HTML'deki input'un name'i 'profile_pic' olmalı
        profile_pic_file = request.FILES.get('profile_pic')
        
        # 4. Giriş yapmış kullanıcıyı al ve güncelle
        user = request.user
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        
        # 5. EĞER yeni bir resim yüklendiyse, onu modele ata
        #    Bu kontrol, kullanıcının resim seçmeden kaydete basması 
        #    durumunda eski resminin silinmesini engeller.
        if profile_pic_file:
            user.profile_pic = profile_pic_file
            
        user.save()
        
        # 6. Başarı mesajı (Opsiyonel ama güzeldir)
        messages.success(request, 'Hesap bilgileriniz başarıyla güncellendi.')
        
        # 7. Sayfayı yenilemek yerine, aynı sayfaya yönlendir (PRG Deseni)
        return redirect('profile_myaccount') 
        
    # 8. Sayfa normal yüklendiyse (GET İsteği)
    #    Sidebar'ınız için gereken context verilerini burada hesaplayın
    #    (Bu kod sizin views.py dosyanızdan alınmıştır)
    wordsAddedFromUser = Word.objects.filter(owner = request.user)
    wordsAddedByUser = Word.objects.filter(saved_by = request.user)
    friends = User.objects.filter(friends = request.user)
    
    allUsers = User.objects.all()

    context = {
        "active_page":"Hesap Bilgilerim",
        "wordsAddedFromUser":wordsAddedFromUser,
        "wordsAddedByUser":wordsAddedByUser,
        "friends":friends,
        "allUsers":allUsers,
    }
    
    return render(request, "pages/profile/myaccount.html", context)

@login_required
def showQuizzesView(request):
    

    mc_stats = MultipleChoiceQuestion.objects.filter(
        attempt__owner=request.user, 
        attempt__isCompleted=True
    ).aggregate(
        correct=Count('id', filter=Q(is_correct=True)),
        wrong=Count('id', filter=Q(is_correct=False))
    )

    # 2. Yazma (WQ) İstatistikleri
    wq_stats = WritingQuestion.objects.filter(
        attempt__owner=request.user, 
        attempt__isCompleted=True
    ).aggregate(
        correct=Count('id', filter=Q(is_correct=True)),
        wrong=Count('id', filter=Q(is_correct=False))
    )

    # 3. Eşleştirme (MQ) İstatistikleri
    mq_stats = MatchingQuestion.objects.filter(
        attempt__owner=request.user, 
        attempt__isCompleted=True
    ).aggregate(
        correct=Sum('correct_matches'),
        wrong=Sum('wrong_matches')
    )

    allUsers = User.objects.all()

    context = {
        "active_page":"Quizlerim",
        'mq_correct': mq_stats.get('correct') or 0,
        'mq_wrong': mq_stats.get('wrong') or 0,
        
        # Çoktan Seçmeli (Renk 2)
        'mc_correct': mc_stats.get('correct') or 0,
        'mc_wrong': mc_stats.get('wrong') or 0,
        
        # Yazma (Renk 3)
        'wq_correct': wq_stats.get('correct') or 0,
        'wq_wrong': wq_stats.get('wrong') or 0,

        "allUsers":allUsers,
    }

    #Hangi sayfanın aktif olduğunu gönderiyoruz.
    return render(request, "pages/profile/quizzes.html", context)

@login_required
def showTextsView(request):
    
    texts = Text.objects.filter(owner = request.user).order_by("-createdAt")

    can_write_new_text = True
    remaining_time = None

    if texts.exists():
        newestText = texts.first()

        now = timezone.now()
        time_passed = now - newestText.createdAt

        if time_passed < timedelta(days=1):
            can_write_new_text = False
            remaining_time = timedelta(days=1) - time_passed

    
    if remaining_time != None:
        remaining_time = str(remaining_time).split(".")[0]

        remaining_time = remaining_time.split(":")
        hour = remaining_time[0]
        minute = remaining_time[1]
        second = remaining_time[2]

        remaining_time = f"{hour} saat {minute} dakika {second} saniye"

    allUsers = User.objects.all()

    context = {
        "mytexts":texts,
        "isWriteable":can_write_new_text,
        "remaining_time":remaining_time,
        "allUsers":allUsers,
    }

    return render(request, "pages/profile/texts.html", context)

@login_required
def showSettingsView(request):
    
    allUsers = User.objects.all()

    settings = UserSettings.objects.filter(user = request.user).first()

    context = {
        "active_page":"Ayarlar",
        "allUsers":allUsers,
        "settings":settings,
    }

    #Hangi sayfanın aktif olduğunu gönderiyoruz.
    return render(request, "pages/profile/settings.html", context)

@login_required
def deleteWord(request, id):
    word = Word.objects.filter(id = id).first()

    if word.owner == request.user:
        wordEn = word.englishWord
        word.delete()
        messages.success(request, f"{wordEn} kelimesi siteden başarıyla silindi.")
    
    elif word.owner != request.user and word.isBaseWord == False:
        wordEn = word.englishWord
        UserWordLink.objects.filter(user=request.user, word=word).delete()

        messages.success(request, f"{wordEn} kelimesi listenizden başarıyla silindi.")

    elif word.isBaseWord == True:
        wordEn = word.englishWord
        UserWordLink.objects.filter(user=request.user, word=word).delete()

        messages.success(request, f"{wordEn} kelimesi listenizden başarıyla silindi.")
    else:
        # Belki de kelimenin sahibi değiliz veya base word değil?
        # Bu duruma da bir mesaj eklemek iyi olabilir.
        messages.error(request, "Bu işlemi yapma yetkiniz yok.")

    return redirect("profile_words")

@login_required
def addWord(request):
    

    if request.method == 'POST':
        word_text = request.POST.get('word_text')
        translation_tr = request.POST.get('translation_tr')
        description = request.POST.get('description')
        notes = request.POST.get('notes')
        prefix = request.POST.get('prefix')
        
        # !! ÖNEMLİ: Checkbox'lar (is_verb) özeldir.
        # İşaretliyse 'on' değeri gelir, değilse HİÇ gelmez (None).
        is_verb = request.POST.get('is_verb') == 'on' # Bu, True/False döndürür

        v2_form = request.POST.get('v2_form')
        v3_form = request.POST.get('v3_form')
        
        sentence_1 = request.POST.get('sentence_1')
        sentence_2 = request.POST.get('sentence_2')
        sentence_3 = request.POST.get('sentence_3')
        
        visibility = request.POST.get('visibility')
        level = request.POST.get('level')

        new_word = Word(
            owner = request.user, # Kelimeyi o anki kullanıcıyla ilişkilendir
            
            # Formdan gelen alanlar (Modelinizdeki isimler = Formdaki 'name'ler)
            englishWord = word_text,         # Model: englishWord, Form-name: word_text
            meaningTr = translation_tr,      # Model: meaningTr, Form-name: translation_tr
            explanation = description,       # Model: explanation, Form-name: description
            note = notes,                    # Model: note, Form-name: notes
            prefix = prefix,                 # Model: prefix, Form-name: prefix
            isVerb = is_verb,                # Model: isVerb, Form-name: is_verb
            v2Form = v2_form,                # Model: v2Form, Form-name: v2_form
            v3Form = v3_form,                # Model: v3Form, Form-name: v3_form
            exampleSentence1 = sentence_1,   # Model: exampleSentence1, Form-name: sentence_1
            exampleSentence2 = sentence_2,   # Model: exampleSentence2, Form-name: sentence_2
            exampleSentence3 = sentence_3,   # Model: exampleSentence3, Form-name: sentence_3
            visibility = visibility,         # Model: visibility, Form-name: visibility
            wordLevel = level                # Modelinizde 'level' alanı olmalı
        )
        
        # 4. Veritabanına kaydet
        new_word.save()

        UserWordLink.objects.create(user=request.user, word=new_word)

        return redirect("profile_words")

    return render(request, "pages/words/addWord.html")

@login_required
def editWord(request, id):
    word = get_object_or_404(Word, id = id)

    if word.isBaseWord:
        messages.error(request, "Bu kelime ODTÜ'nün kur kelimelerindendir ve sadece admin panelinden değiştirilebilir.")
        return redirect("profile_words")

    if request.method == 'POST':
        
        # 3. HTML formundaki 'name' özniteliklerine göre tüm verileri çek.
        word.englishWord = request.POST.get('word_text')
        word.meaningTr = request.POST.get('translation_tr')
        word.explanation = request.POST.get('description') # Model: explanation, Form: description
        word.note = request.POST.get('notes')
        word.prefix = request.POST.get('prefix')
        
        # Checkbox ('is_verb') kontrolü:
        # İşaretliyse 'on' değeri gelir, değilse HİÇ gelmez (None).
        is_verb_checked = request.POST.get('is_verb') == 'on'
        word.isVerb = is_verb_checked

        # Eğer "Fiil" olarak İŞARETLENMEMİŞSE, V2/V3 alanlarını temizle.
        if is_verb_checked:
            word.v2Form = request.POST.get('v2_form')
            word.v3Form = request.POST.get('v3_form')
        else:
            word.v2Form = None # veya modelinize göre ""
            word.v3Form = None # veya modelinize göre ""

        word.exampleSentence1 = request.POST.get('sentence_1')
        word.exampleSentence2 = request.POST.get('sentence_2')
        word.exampleSentence3 = request.POST.get('sentence_3')
        word.visibility = request.POST.get('visibility')
        word.wordLevel = request.POST.get('level') # Modelinizde 'level' alanı olduğunu varsayıyorum

        # 4. Değişiklikleri veritabanına kaydet.
        word.save()
        
        # 5. Kullanıcıyı kelime listesine geri yönlendir.
        return redirect('profile_words') # Kelime listenizin URL name'i

    # 3. Sayfa İLK YÜKLENDİ mi (GET isteği)?
    # Kullanıcı "Düzenle" butonuna tıkladı ve sayfa açılıyor.
    else:
        # İŞTE SİZİN İSTEDİĞİNİZ KISIM BURASI:
        # Template'e 'word' adında bir context değişkeni yolluyoruz.
        # Template'iniz bu 'word' nesnesini kullanarak 
        # value="{{ word.englishWord }}" gibi alanları dolduracak.
        context = {
            'word': word
        }

    return render(request, "pages/words/editWord.html",{"word":word})

@login_required
def saveMyBio(request):
    # Eğer form gönderilmişse (yani buton submitlenmişse)
    if request.method == 'POST':
        # Formdan gelen bio datasını al ve kaydet
        bio_data = request.POST.get('bio')
        request.user.bio = bio_data
        request.user.save()

        return redirect("user_profile")
    
    # Submitlenmemişse sadece sayfa görüntüleniyorsa sadece sayfayı döndür.
    else:
        return redirect("user_profile")

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
    
@login_required
def deleteAllWords(request):
    if request.method == "POST":
        value = request.POST.get("bulk_word_list_name")
        
        if value == "101:all":
            links = UserWordLink.objects.filter(user = request.user, word__wordLevel = "101")
            links.delete()
            
        elif value == "201:all":
            links = UserWordLink.objects.filter(user = request.user, word__wordLevel = "201")
            links.delete()

        elif value == "301:all":
            links = UserWordLink.objects.filter(user = request.user, word__wordLevel = "301")
            links.delete()

        elif value == "401:all":
            links = UserWordLink.objects.filter(user = request.user, word__wordLevel = "401")
            links.delete()

        elif value == "501:all":
            links = UserWordLink.objects.filter(user = request.user, word__wordLevel = "501")
            links.delete()

        elif value.startswith("101"):
            week_no = int(value[-1])
            add101Weeks(request.user, week_no, delete = True)

        elif value.startswith("201"):
            week_no = int(value[-1])
            add201Weeks(request.user, week_no, delete = True)

        elif value.startswith("301"):
            week_no = int(value[-1])
            add301Weeks(request.user, week_no, delete = True)

        elif value.startswith("401"):
            week_no = int(value[-1])
            add401Weeks(request.user, week_no, delete = True)

        messages.success(request, "Seçtiğiniz bütün kelimeler listenizden silindi.")

        return redirect ("profile_words")

    return redirect("profile_words")

