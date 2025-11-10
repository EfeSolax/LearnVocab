from django.shortcuts import render, get_object_or_404, redirect
from .models import Word,UserWordLink
from django.db import models
from users.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse 
from .addWeeks.addWeeks import add101Weeks, add201Weeks, add301Weeks, add401Weeks

# Create your views here.

@login_required
def add_to_my_list(request, word_id):
    word = get_object_or_404(Word, id=word_id)
    UserWordLink.objects.get_or_create(user=request.user, word=word)
    query_parameters = request.GET.urlencode()
    
    # 2. Ana 'all_words' URL'ini oluştur
    base_url = reverse('all_words')
    
    # 3. Parametreleri ve kelimeye özel bir çapa (#) ekleyerek tam URL'i oluştur
    # Bu, sayfanın tıkladığın kelimeye geri kaymasını sağlayacak
    redirect_url = f"{base_url}?{query_parameters}#word-{word.id}"
    
    return redirect(redirect_url)


@login_required
def remove_from_my_list(request, word_id):
    word = get_object_or_404(Word, id=word_id)

    UserWordLink.objects.filter(user=request.user, word=word).delete()
    query_parameters = request.GET.urlencode()
    
    # 2. Ana 'all_words' URL'ini oluştur
    base_url = reverse('all_words')
    
    # 3. Parametreleri ve kelimeye özel bir çapa (#) ekleyerek tam URL'i oluştur
    redirect_url = f"{base_url}?{query_parameters}#word-{word.id}"

    return redirect(redirect_url)


def allWords(request):
    
    user = request.user
    words = Word.objects.all().order_by('-createdAt')

    if not user.is_authenticated:
        words = words.filter(
            models.Q(isBaseWord=True) | 
            models.Q(visibility="public")
        )

    else:
        # Kullanıcı giriş yapmışsa owner veya saved_by filtreleme yapılabilir
        # Örnek: sadece kullanıcının eklediği veya herkese açık kelimeler
        words = words.filter(
            models.Q(isBaseWord=True) |
            models.Q(owner=user) |
            models.Q(saved_by=user) |
            models.Q(visibility="friends", owner__friends=request.user) |
            models.Q(visibility="public")
        )
        

    # Arama filtreleri
    query = request.GET.get('q')
    filter_by = request.GET.get('filter_by')
    level = request.GET.get('level')  # Kur seviyesi filtresi

    if query:
        if filter_by == 'all':
            words = words.filter(
                models.Q(englishWord__icontains=query) |
                models.Q(meaningTr__icontains=query) |
                models.Q(explanation__icontains=query) |
                models.Q(owner__username__icontains=query) |
                models.Q(wordLevel__icontains=query) |
                models.Q(v2Form__icontains=query) |
                models.Q(v3Form__icontains=query)
            )
        elif filter_by == 'english':
            words = words.filter(englishWord__icontains=query)
        elif filter_by == 'meaning':
            words = words.filter(meaningTr__icontains=query)
        elif filter_by == 'explanation':
            words = words.filter(explanation__icontains=query)
        elif filter_by == 'author':
            words = words.filter(owner__username__icontains=query)
        elif filter_by == 'only_METU':
            words = words.select_related('owner').order_by('-createdAt')
            words = words.filter(isBaseWord = True)
        elif filter_by == 'only_User':
            words = words.select_related('owner').order_by('-createdAt')
            words = words.filter(
                models.Q(owner=user) |
                models.Q(saved_by=user)
            )
            words = words.filter(isBaseWord = False)

        else:
            
            # Genel arama (tüm alanlarda)
            words = words.filter(
                models.Q(englishWord__icontains=query) |
                models.Q(meaningTr__icontains=query) |
                models.Q(explanation__icontains=query) |
                models.Q(owner__username__icontains=query)
            )
    else:
        if filter_by == 'only_METU':
            words = Word.objects.all().select_related('owner').order_by('-createdAt')
            words = words.filter(isBaseWord = True)
        elif filter_by == 'only_User':
            words = Word.objects.all().select_related('owner').order_by('-createdAt')
            words = words.filter(
                models.Q(owner=user) |
                models.Q(saved_by=user) |
                models.Q(visibility="friends", owner__friends=request.user) |
                models.Q(visibility="public")
            )
            words = words.filter(isBaseWord = False)
    
    # Kur seviyesi filtresi
    if level and level != "all":
        words = words.filter(wordLevel=level)

    words = words.distinct()

    return render(request, "pages/words/allWords.html", {"words": words})


def word_detail(request, id):
    
    word = get_object_or_404(Word, id=id)

    counter = 0

    if word.visibility == "private" and word.owner != request.user:
        messages.error(request, "Bu kelimeyi görüntüleyemezsiniz.")
        return redirect("all_words")

    if request.user.is_authenticated:
        if not word.isBaseWord:
            counter += 1
        
        if word.owner != request.user:
            counter += 1

        if word.saved_by.contains(request.user):
            counter += 1

        if not (word.visibility == "friends" and word.owner.friends.contains(request.user)):
            counter += 1

        if word.visibility != "public":
            counter += 1

        if counter == 5:
            messages.error(request, "Bu kelimeyi görüntüleyemezsiniz.")
            return redirect("all_words")
    else:
        if not word.isBaseWord:
            counter += 1
        
        if word.visibility != "public":
            counter += 1

        if counter == 2:
            messages.error(request, "Bu kelimeyi görüntüleyemezsiniz.")
            return redirect("all_words")
        

    context = {
        'word':word,
        "exampleSentences":[word.exampleSentence1, word.exampleSentence2, word.exampleSentence3],
    }


    return render(request, 'pages/words/wordDetail.html', context)

@login_required
def addAllWords(request):
    if request.method == "POST":
        value = request.POST.get("bulk_word_list_name")
        
        if value == "101:all":
            words = Word.objects.filter(wordLevel = "101", isBaseWord = True)

            for word in words:
                if UserWordLink.objects.filter(user = request.user, word = word).exists():
                    continue
                UserWordLink.objects.create(user = request.user, word = word)
        elif value == "201:all":
            words = Word.objects.filter(wordLevel = "201", isBaseWord = True)
            for word in words:
                if UserWordLink.objects.filter(user = request.user, word = word).exists():
                    continue
                UserWordLink.objects.create(user = request.user, word = word)
        elif value == "301:all":
            words = Word.objects.filter(wordLevel = "301", isBaseWord = True)
            for word in words:
                if UserWordLink.objects.filter(user = request.user, word = word).exists():
                    continue
                UserWordLink.objects.create(user = request.user, word = word)
        elif value == "401:all":
            words = Word.objects.filter(wordLevel = "401", isBaseWord = True)
            for word in words:
                if UserWordLink.objects.filter(user = request.user, word = word).exists():
                    continue
                UserWordLink.objects.create(user = request.user, word = word)
        elif value == "501:all":
            words = Word.objects.filter(wordLevel = "501", isBaseWord = True)
            for word in words:
                if UserWordLink.objects.filter(user = request.user, word = word).exists():
                    continue
                UserWordLink.objects.create(user = request.user, word = word)

        elif value.startswith("101"):
            week_no = int(value[-1])
            add101Weeks(request.user, week_no)

        elif value.startswith("201"):
            week_no = int(value[-1])
            add201Weeks(request.user, week_no)

        elif value.startswith("301"):
            week_no = int(value[-1])
            add301Weeks(request.user, week_no)

        elif value.startswith("401"):
            week_no = int(value[-1])
            add401Weeks(request.user, week_no)

        messages.success(request, "Seçtiğiniz bütün kelimeler listenize eklendi.")

        return redirect ("all_words")

    return redirect("all_words")

