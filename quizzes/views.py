from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from random import choice, shuffle, sample

from words.models import UserWordLink, Word, WordList
from .models import QuizType, QuizAttempt, MultipleChoiceQuestion, WritingQuestion, MatchingQuestion, SynonymAntonymQuestion
from usersettings.models import UserSettings

from .question_generator import (
    generate_mc_question,
    generate_writing_question,
    generate_matching_question,
    generate_synonym_antonym_question,
)


# Create your views here.

@login_required
def attemptQuiz(request):

    if request.method == "POST":
        quizType = request.POST.get("quizType")
        totalQuestion = request.POST.get("totalQuestion")

        if quizType not in ("mixed", "matching", "multiple_choice", "writing", "random", "synonym_antonym"):
            messages.error(request, "Hatalı bir quiz tipi seçildi.")
            return redirect("attempt_quiz")

        if totalQuestion not in ("5", "10", "15", "25", "40"):
            messages.error(request, "Hatalı bir soru sayısı seçildi.")
            return redirect("attempt_quiz")

        totalQuestion = int(totalQuestion)

        choices = ["mixed", "matching", "multiple_choice", "writing"]
        if quizType == "random":
            quizType = choice(choices)

        # Opsiyonel: kullanıcı belirli kelimeler seçtiyse sadece onlardan quiz hazırla
        selected_raw = request.POST.getlist("selected_word_ids")
        selected_ids = []
        for v in selected_raw:
            try:
                selected_ids.append(int(v))
            except (TypeError, ValueError):
                continue

        links = UserWordLink.objects.filter(user=request.user)
        if selected_ids:
            links = links.filter(word_id__in=selected_ids)

        # Eşleştirme tipi quiz 5'er gruplar halinde çalışır; uygun değilse uyar
        if quizType == "matching" and totalQuestion % 5 != 0:
            messages.error(request, "Eşleştirme quiz'i 5'in katları olan soru sayılarıyla çalışır (5, 10, 15, 25, 40).")
            return redirect("attempt_quiz")

        # Eş/Zıt anlamlı quiz: sadece synonyms veya antonyms dolu kelimelere kısıtla
        if quizType == "synonym_antonym":
            eligible_links = [
                lnk for lnk in links.select_related('word')
                if (lnk.word.synonyms and lnk.word.synonyms.strip())
                or (lnk.word.antonyms and lnk.word.antonyms.strip())
            ]
            if totalQuestion > len(eligible_links):
                messages.error(
                    request,
                    f"Eş/Zıt Anlamlı quiz için yeterli kelime yok. "
                    f"Listenizde eş veya zıt anlamlısı girilmiş {len(eligible_links)} kelime var, "
                    f"ancak {totalQuestion} soruluk bir quiz istendi. "
                    "Kelimelerinize eş/zıt anlamlı ekleyin ya da soru sayısını azaltın."
                )
                return redirect("attempt_quiz")
            # links'i eligible ile değiştir; normal kelime sayısı kontrolünü atla
            links = eligible_links

        elif totalQuestion > len(links):
            if selected_ids:
                messages.error(
                    request,
                    f"Seçtiğiniz {len(links)} kelime ile {totalQuestion} soruluk bir quiz oluşturulamaz. "
                    "Daha fazla kelime seçin ya da soru sayısını azaltın."
                )
            else:
                messages.error(request, "Listenizde bu istediğiniz soru sayısında kelime yok.")
            return redirect("attempt_quiz")

        priority1 = list()
        priority2 = list()
        priority3 = list()

        for link in links:
            if link.totalAttempts <= 2:
                priority1.append(link)

            elif link.totalAttempts <= 6:
                if link.wrongRatio >= 0.50:
                    priority1.append(link)
                else:
                    priority2.append(link)

            else:
                if link.wrongRatio >= 0.50:
                    priority1.append(link)
                elif link.wrongRatio >= 0.2:
                    priority2.append(link)
                else:
                    priority3.append(link)

        priority1.sort(key=lambda link: (link.totalAttempts, -link.wrongRatio))

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
                num_matching_words = 0
                mc_links = links_to_ask[:3]
                wq_links = links_to_ask[3:]
                mq_links_list = []
            elif totalQuestion == 10: # Örn: 1 Eşleştirme (5), 3 ÇS, 2 Yazma
                num_matching_words = 5
                mq_links_list = [links_to_ask[:5]] 
                mc_links = links_to_ask[5:8]
                wq_links = links_to_ask[8:]
            elif totalQuestion == 15: # 15 Soru: 1 Eşleştirme (5), 6 ÇS, 4 Yazma
                num_matching_words = 5
                mq_links_list = [links_to_ask[:5]]
                mc_links = links_to_ask[5:11]
                wq_links = links_to_ask[11:]
            elif totalQuestion == 25: # 25 Soru: 1 Eşleştirme (5), 6 ÇS, 4 Yazma
                num_matching_words = 10
                mq_links_list = [links_to_ask[0:5], links_to_ask[5:10]]
                mc_links = links_to_ask[10:18]
                wq_links = links_to_ask[18:]
            else:
                num_matching_words = 15
                mq_links_list = [links_to_ask[0:5], links_to_ask[5:10], links_to_ask[10:15]]
                mc_links = links_to_ask[15:28]
                wq_links = links_to_ask[28:]

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

        elif quizType == "synonym_antonym":
            for link in links_to_ask:
                generate_synonym_antonym_question(link, newQuiz, all_user_words)

        return redirect('quiz_page', attempt_id=newQuiz.id, question_index=1)

    # GET: Kullanıcının kelime listesini kaynak rozetleriyle hazırla
    user = request.user
    user_links = (
        UserWordLink.objects
        .filter(user=user)
        .select_related("word", "word__owner")
        .prefetch_related("word__in_user_lists")
        .order_by("word__englishWord")
    )
    friend_ids = set(user.friends.values_list("id", flat=True))

    # Kullanıcının özel kelime listeleri (klasörleri)
    user_lists = list(WordList.objects.filter(owner=user).order_by("name"))
    list_count_map = {wl.id: 0 for wl in user_lists}

    word_items = []
    counts = {"base": 0, "own": 0, "friend": 0, "saved": 0}
    for link in user_links:
        w = link.word
        if w.isBaseWord:
            source, source_label = "base", "ODTÜ"
        elif w.owner_id == user.id:
            source, source_label = "own", "Kendi"
        elif w.owner_id in friend_ids:
            source, source_label = "friend", "Arkadaş"
        else:
            source, source_label = "saved", "Eklenen"
        counts[source] += 1

        # Bu kelimenin hangi kullanıcı listelerinde olduğunu çıkar
        word_list_ids = [wl.id for wl in w.in_user_lists.all() if wl.owner_id == user.id]
        for lid in word_list_ids:
            if lid in list_count_map:
                list_count_map[lid] += 1

        word_items.append({
            "id": w.id,
            "english": w.englishWord,
            "meaning": w.meaningTr,
            "level": w.wordLevel or "—",
            "source": source,
            "source_label": source_label,
            # Veri olarak listele (template data-lists attribute olarak join'leyecek)
            "list_ids": word_list_ids,
            "lists_attr": ",".join(str(i) for i in word_list_ids),
        })

    # Template'in render edebileceği zenginleştirilmiş liste meta verisi
    user_lists_meta = [
        {
            "id": wl.id,
            "name": wl.name,
            "color": wl.color,
            "count": list_count_map.get(wl.id, 0),
        }
        for wl in user_lists
    ]

    context = {
        "word_items": word_items,
        "total_word_count": len(word_items),
        "counts": counts,
        "user_lists": user_lists_meta,
    }
    return render(request, "pages/quizzes/attemptQuiz.html", context)

def get_words_for_quiz(priority1, priority2, priority3, total_question):
    # ... (Bu fonksiyonunuzda da hiçbir hata yoktu, aynı kalabilir) ...
    links_to_ask = list()

    if total_question == 5:
        (k1, k2, k3) = (3, 1, 1)
    elif total_question == 10:
        (k1, k2, k3) = (7, 2, 1)
    elif total_question == 15:
        (k1, k2, k3) = (10, 3, 2)
    elif total_question == 25:
        (k1, k2, k3) = (17, 5, 3)
    else: # 40
        (k1, k2, k3) = (28, 8, 4)

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
    sa_q = list(attempt.synonymantonymquestion_questions.all())

    all_questions = sorted(mc_q + wq_q + mq_q + sa_q, key=lambda q: q.id)

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
            
            if question_type in ("MultipleChoiceQuestion", "SynonymAntonymQuestion"):
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
    sa_q = list(attempt.synonymantonymquestion_questions.all())

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

    for q in sa_q:
        q.template_name = 'SynonymAntonymQuestion'
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