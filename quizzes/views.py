from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from random import choice, shuffle, sample

from words.models import UserWordLink, Word
# Düzeltilmiş Model Importları: Sadece ihtiyacımız olanlar
from .models import QuizType, QuizAttempt, MultipleChoiceQuestion, WritingQuestion, MatchingQuestion
from usersettings.models import UserSettings

# Düzeltilmiş Fonksiyon Importları: Sadece ihtiyacımız olanlar
from .question_generator import (
    generate_mc_question, 
    generate_writing_question, 
    generate_matching_question
)


# Create your views here.

@login_required
def attemptQuiz(request):
    
    # ... (Bu fonksiyonunuzda hiçbir hata yoktu, aynı kalabilir) ...
    if request.method == "POST":
        quizType = request.POST.get("quizType")
        totalQuestion = request.POST.get("totalQuestion")

        if not (quizType == "mixed" or quizType == "matching" or quizType == "multiple_choice" or quizType == "writing" or quizType == "random"):
            messages.error(request, "Hatalı bir quiz tipi seçildi.") 
            return redirect("attempt_quiz")
        
        if not (totalQuestion == "5" or totalQuestion == "10" or totalQuestion == "15"):
            messages.error(request, "Hatalı bir soru sayısı seçildi.")
            return redirect("attempt_quiz")
        
        totalQuestion = int(totalQuestion)
        
        choices = ["mixed","matching","multiple_choice","writing"]

        if quizType == "random":
            quizType = choice(choices)

        links = UserWordLink.objects.filter(user=request.user)

        if totalQuestion > len(links):
            messages.error(request, "Listenizde bu istediğiniz soru sayısında kelime yok.")
            return redirect("profile_quizzes")
        
        priority1 = list()
        priority2 = list()
        priority3 = list()

        for link in links:
            if link.totalAttempts <= 4:
                priority1.append(link)

            elif link.totalAttempts <= 10:
                if link.wrongRatio >= 0.65:
                    priority1.append(link)
                else:
                    priority2.append(link)

            else:
                if link.wrongRatio >= 0.65:
                    priority1.append(link)
                elif link.wrongRatio >= 0.3:
                    priority2.append(link)
                else:
                    priority3.append(link)

        priority1.sort(
            # 'key' bir tuple döndürüyor: (Gruplama Kriteri, Sıralama Kriteri)
            key=lambda link: (
                link.totalAttempts > 0,  # 1. Kriter (Gruplama)
                -link.wrongRatio         # 2. Kriter (Sıralama)
            )
        )

        priority2.sort(
            key=lambda link: link.wrongRatio if link.totalAttempts > 0 else 0,
            reverse=True
        )

        priority3.sort(
            key=lambda link: link.wrongRatio if link.totalAttempts > 0 else 0,
            reverse=True
        )

        links_to_ask = get_words_for_quiz(priority1, priority2, priority3, totalQuestion)
        shuffle(links_to_ask)

        if len(links_to_ask) != totalQuestion:
            messages.error(request, f"İstenen soru sayısında bir quiz oluşturulamadı. Mevcut kelime sayısı: {len(links_to_ask)}")
            return redirect("attempt_quiz")

        newQuiz = QuizAttempt.objects.create(
            owner = request.user,
            totalQuestion = len(links_to_ask), # Bu, "10 kelime" sayısını saklar (Doğru)
            quizType = quizType,
        )

        all_user_words = Word.objects.filter(userLinks__user=request.user).distinct()
        
        if quizType == "mixed":
            if totalQuestion == 5: # Örn: 3 ÇS, 2 Yazma
                mc_links = links_to_ask[:3]
                wq_links = links_to_ask[3:]
                mq_links_list = []
            elif totalQuestion == 10: # Örn: 1 Eşleştirme (5), 3 ÇS, 2 Yazma
                mq_links_list = [links_to_ask[:5]] 
                mc_links = links_to_ask[5:8]
                wq_links = links_to_ask[8:]
            else: # 15 Soru: 1 Eşleştirme (5), 6 ÇS, 4 Yazma
                mq_links_list = [links_to_ask[:5]]
                mc_links = links_to_ask[5:11]
                wq_links = links_to_ask[11:]

            for link in mc_links:
                generate_mc_question(link, newQuiz, all_user_words)
            for link in wq_links:
                generate_writing_question(link, newQuiz)
            for group in mq_links_list:
                generate_matching_question(group, newQuiz)

        elif quizType == "multiple_choice":
            for link in links_to_ask:
                generate_mc_question(link, newQuiz, all_user_words)

        elif quizType == "writing":
            for link in links_to_ask:
                generate_writing_question(link, newQuiz)

        elif quizType == "matching":
            group_size = 5
            for i in range(0, totalQuestion, group_size):
                link_group = links_to_ask[i : i + group_size]
                if len(link_group) == group_size:
                    generate_matching_question(link_group, newQuiz)
        
        return redirect('quiz_page', attempt_id=newQuiz.id, question_index=1)

    return render(request, "pages/quizzes/attemptQuiz.html")

def get_words_for_quiz(priority1, priority2, priority3, total_question):
    # ... (Bu fonksiyonunuzda da hiçbir hata yoktu, aynı kalabilir) ...
    links_to_ask = list()

    if total_question == 5:
        (k1, k2, k3) = (3, 1, 1)
    elif total_question == 10:
        (k1, k2, k3) = (7, 2, 1)
    else: # 15
        (k1, k2, k3) = (10, 3, 2)

    actual_count_p1 = min(k1, len(priority1))
    actual_links_p1 = priority1[:actual_count_p1]
    links_to_ask.extend(actual_links_p1)
    
    quota_transfer_to_p2 = k1 - actual_count_p1
    k2_new = k2 + quota_transfer_to_p2
    actual_count_p2 = min(k2_new, len(priority2))
    actual_links_p2 = priority2[:actual_count_p2]
    links_to_ask.extend(actual_links_p2)

    quota_transfer_to_p3 = k2_new - actual_count_p2
    k3_new = k3 + quota_transfer_to_p3
    actual_count_p3 = min(k3_new, len(priority3))
    actual_links_p3 = priority3[:actual_count_p3]
    links_to_ask.extend(actual_links_p3)
    
    current_count = len(links_to_ask)

    if current_count < total_question:
        remaining_needed = total_question - current_count
        remaining_p1 = priority1[actual_count_p1:]
        remaining_p2 = priority2[actual_count_p2:]
        remaining_p3 = priority3[actual_count_p3:]
        
        backfill_pool = remaining_p1 + remaining_p2 + remaining_p3
        links_to_ask.extend(backfill_pool[:remaining_needed])

    shuffle(links_to_ask)
    
    return links_to_ask

@login_required
def quizPage(request, attempt_id, question_index):
    
    """
    Quiz'in gerçekleştiği, soruları tek tek gösteren ve cevapları kontrol eden view.
    """
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, owner=request.user)
    userset = UserSettings.objects.filter(user = request.user)
    audio = None

    if userset.exists():
        audio = userset.first().audio

    # 1. Bu attempt'e ait tüm soruları (tiplerinden bağımsız) alıp sıralamamız gerek
    # NOT: Bu sorguların çalışması için Modellerin import edilmesi gerekmez,
    # çünkü 'related_name'leri (örn: "multiplechoicequestion_questions") kullanıyoruz.
    mc_q = list(attempt.multiplechoicequestion_questions.all())
    wq_q = list(attempt.writingquestion_questions.all())
    mq_q = list(attempt.matchingquestion_questions.all())
    
    all_questions = sorted(mc_q + wq_q + mq_q, key=lambda q: q.id)
    
    try:
        current_question = all_questions[question_index - 1]
    except IndexError:
        return redirect('quiz_complete', attempt_id=attempt.id)
    
    question_type = current_question.__class__.__name__ 
    total_questions = len(all_questions)
    next_question_index = question_index + 1
    is_last_question = (question_index == total_questions)

    # 4. Cevabı Kontrol Etme (POST)
    if request.method == "POST":
        user_input = request.POST.get("answer") 

        time_taken_str = request.POST.get("time_taken") # JS'ten gelen veriyi al
        
        try:
            time_taken = float(time_taken_str)
        except (ValueError, TypeError):
            time_taken = None
        
        # Bu kod, bir önceki adımdaki 'models.py' değişikliğini (time_taken parametresi)
        # yaptığınızı varsayar.
        current_question.check_answer(user_input, time_taken=time_taken)
        
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            correct_answer_value = ""
            
            if question_type == "MultipleChoiceQuestion":
                correct_answer_value = current_question.correct_option 
            elif question_type == "WritingQuestion":
                correct_answer_value = current_question.correct_answer 
            
            return JsonResponse({
                'is_correct': current_question.is_correct,
                'correct_answer': correct_answer_value
            })
            
        context = {
            'attempt': attempt, 
            'question': current_question,
            'attempt_id': attempt_id,
            'question_index': question_index,
            'total_questions': total_questions,
            'is_last_question': is_last_question,
            'next_question_index': next_question_index,
            'question_type': question_type,
            'answer_checked': True, 
            'is_correct': current_question.is_correct, 
            "audio":audio,
        }
        return render(request, "pages/quizzes/quizPage.html", context)


    # 5. Soruyu Gösterme (GET)
    context = {
        'attempt': attempt, 
        'question': current_question,
        'attempt_id': attempt_id,
        'question_index': question_index,
        'total_questions': total_questions,
        'is_last_question': is_last_question,
        'next_question_index': next_question_index,
        'question_type': question_type,
        'answer_checked': False, 
        "audio":audio,
    }
    
    return render(request, "pages/quizzes/quizPage.html", context)

@login_required
def quizComplete(request, attempt_id):
    
    """
    Quiz bittiğinde sonuçları gösteren sayfa.
    (TEMİZLENMİŞ VE DÜZELTİLMİŞ FONKSİYON)
    """
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, owner=request.user)
    
    # Henüz tamamlanmadıysa (ilk ziyaretse) skoru hesapla
    if not attempt.isCompleted:
        # Bu, 'models.py' dosyanızdaki DÜZELTİLMİŞ 'calculateScore' metodunu
        # çağırdığınızı varsayar (Puanlama hatası için)
        attempt.calculateScore() 
        
    # --- Soru listesini 'quizPage'deki gibi tekrar oluştur ---
    mc_q = list(attempt.multiplechoicequestion_questions.all())
    wq_q = list(attempt.writingquestion_questions.all())
    mq_q = list(attempt.matchingquestion_questions.all())
    
    all_questions = []
    
    for q in mc_q:
        q.template_name = 'MultipleChoiceQuestion'
        all_questions.append(q)
        
    for q in wq_q:
        q.template_name = 'WritingQuestion'
        all_questions.append(q)
        
    for q in mq_q:
        q.template_name = 'MatchingQuestion'

        q.combined_items = list(zip(
            q.left_column_items, 
            q.right_column_items_user_ordered,
            q.correct_column_items
        ))
        all_questions.append(q)
    
    # Hepsini ID'ye göre sırala (oluşturulma sırası)
    all_questions.sort(key=lambda q: q.id)
    
    context = {
        "attempt": attempt,
        "all_questions": all_questions
    }
        
    return render(request, "pages/quizzes/quizComplete.html", context)
    
@login_required
def quizReviewList(request):
    
    """
    Kullanıcının tamamladığı tüm geçmiş quiz'leri listeler.
    """
    # Sadece oturum açmış kullanıcıya ait VE tamamlanmış olanları al
    attempts = QuizAttempt.objects.filter(
        owner=request.user, 
        isCompleted=True
    ).order_by('-createdAt') # En yeniden eskiye doğru sırala

    context = {
        'attempts': attempts
    }
    
    return render(request, 'pages/quizzes/quizReviews.html', context)

@login_required
def removeQuiz(request, quiz_id):
    if request.method == "POST":
        # Silinmek istenen quiz'i bul, AMA sadece bu kullanıcıya aitse
        attempt = get_object_or_404(QuizAttempt, id=quiz_id, owner=request.user)
        
        # Quiz'i sil
        # (Modellerdeki 'on_delete=models.CASCADE' sayesinde 
        # bu quiz'e bağlı tüm sorular da otomatik silinecektir)
        attempt.delete()
        
        # Kullanıcıya başarı mesajı göster
        messages.success(request, "Quiz kaydı başarıyla silindi.")
        
        # Kullanıcıyı quiz listesine geri yönlendir
        return redirect('quiz_review')
    
    # Eğer birisi bu URL'e GET isteği ile (adres çubuğundan) gelirse,
    # hiçbir şey yapma ve listeye geri yönlendir.
    return redirect('quiz_revi')