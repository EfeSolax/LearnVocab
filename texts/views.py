from django.shortcuts import render, redirect
from texts.models import Text
from users.models import User
from words.models import Word, UserWordLink
from django.contrib.auth.decorators import login_required
from .send_gemini import *

from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
# Create your views here.

@login_required
def newTextPage(request):
    
    texts = Text.objects.filter(owner = request.user).order_by("-createdAt")
    can_write_new_text = True

    if texts.exists():
        newestText = texts.first()

        now = timezone.now()
        time_passed = now - newestText.createdAt

        if time_passed < timedelta(days=1):
            can_write_new_text = False

    if not can_write_new_text:
        return redirect("profile_texts")

    start_date = timezone.now() - timedelta(days=7)
    
    links = UserWordLink.objects.filter(user = request.user)

    links = links.filter(dateAdded__gte=start_date)
    
    return render(request, "pages/texts/newText.html", {"links":links})   

@login_required
def createText(request):
    
    if request.method == "POST":
        user_text = request.POST.get("user_text")
        user_text = user_text.strip()

        start_date = timezone.now() - timedelta(days=7)

        links = UserWordLink.objects.filter(user = request.user)
        links = links.filter(dateAdded__gte=start_date)
        wordsList = list()

        words = list()
        for link in links:
            words.append(link.word)
        
        for link in links:
            wordsList.append(link.word.englishWord)

        response = send_message_to_gemini(user_text, wordsList)

        if response == "Bu metin değerlendirilmedi.":
            messages.error(request, "Lütfen değerlendirilebilecek İngilizce bir metin yazınız.")
            return redirect("profile_texts")


        if not (("[" in response.split("\n")[-1]) and ("]" in response.split("\n")[-1])):
            print("RESPONSE BAŞARILI BİR ŞEKİLDE ALINAMADI.")
            messages.error(request, "Gemini şu anda başarılı bir şekilde metninizi değerlendiremedi. Lütfen birkaç dakika sonra tekrar deneyiniz.")
            return redirect("profile_texts")

        points = response.split("\n")[-1]
        points = points[1:len(points)-1]
        points = points.split(",")
        
        lines = response.splitlines(True) 
        lines = lines[:-1]
        response = "".join(lines)

        points = [int(point) for point in points]
        totalScore = sum(points)

        text = Text.objects.create(
            owner = request.user,
            content = user_text,
            score = totalScore,
            scores = str(points),
            response = response
        )

        for word in words:
            text.words.add(word)

        return redirect("review_text", text_id = text.id)

    
    return redirect("profile_texts")

@login_required
def reviewText(request, text_id):
    
    text = Text.objects.filter(id = text_id).first()

    start_date = timezone.now() - timedelta(days=7)

    links = UserWordLink.objects.filter(user = request.user)
    links = links.filter(dateAdded__gte=start_date)

    scores = text.scores
    
    scores = scores.replace(" ","")
    scores = scores.replace("[","")
    scores = scores.replace("]","")
    scores = scores.split(",")
    scores = [int(point) for point in scores]

    point1 = scores[0]
    point2 = scores[1]
    point3 = scores[2]
    point4 = scores[3]
    point5 = scores[4]
    point6 = scores[5]
    point7 = scores[6]
    point8 = scores[7]
    point9 = scores[8]
    point10 = scores[9]

    # 5, 21, 8, 5, 4, 12, 3, 3, 5, 3
    
    context = {
        "text":text,
        "point1":point1,
        "point2":point2,
        "point3":point3,
        "point4":point4,
        "point5":point5,
        "point6":point6,
        "point7":point7,
        "point8":point8,
        "point9":point9,
        "point10":point10,
        "context_point":point1+point2+point3+point4+point5,
        "language_point":point6+point7+point8+point9+point10,
        "links":links,
    }

    return render(request, "pages/texts/textReview.html", context)

@login_required
def removeText(request, text_id):
    text = Text.objects.filter(id=text_id).first()

    # 2. Gerekli zaman kontrollerini yap
    now = timezone.now()
    time_passed = now - text.createdAt
    
    # 3. Kuralı uygula: 1 günden daha mı yeni?
    if time_passed < timedelta(days=1):
        # Durum 1: Metin 1 günden YENİ. SİLME.
        
        # Kullanıcıya neden silinmediğini bildirmek için bir mesaj ekle
        messages.error(request, 'Oluşturulduktan sonra 1 gün geçmemiş metinler silinemez.')
    
    else:
        text.delete()
        messages.success(request, "Metniniz başarılı bir şekilde silindi.")
    
    return redirect("profile_texts")

@login_required
def aboutGradingPage(request):
    
    return render(request, "pages/texts/aboutGrading.html")