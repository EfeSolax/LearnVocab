from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import ExpressionWrapper, F, FloatField, Sum
from django.db.models.functions import Cast, NullIf
from django.http import JsonResponse
from django.contrib import messages
from random import choice, shuffle, sample

from LearnVocab import pagination
from LearnVocab.authgate import login_gate

from words.models import UserWordLink, Word, WordList
from .models import QuizType, QuizAttempt, MultipleChoiceQuestion, WritingQuestion, MatchingQuestion, SynonymAntonymQuestion
from usersettings.models import UserSettings

from .question_generator import (
    generate_mc_question,
    generate_writing_question,
    generate_matching_question,
    generate_synonym_antonym_question,
    generate_fill_blank_question,
    can_generate_blank,
)


# Create your views here.

# wrongRatio bir YÜZDE döndürür (0-100). Eşikler de yüzde cinsindendir.
WRONG_RATIO_HIGH = 50   # %50 ve üzeri yanlış -> en yüksek öncelik
WRONG_RATIO_MID = 20    # %20 ve üzeri yanlış -> orta öncelik


def encounter_signals(user):
    """
    Öğren-Geç'ten gelen iki sinyali kelime id'lerine göre döner.

    misjudged: kullanıcının "biliyorum" deyip anlamı görünce yanıldığını
               kabul ettiği kelimeler. Bunlar kendi başına ASLA çalışmayacağı
               kelimelerdir (bildiğini sanıyor), o yüzden quizde öne alınıyor.
    learned:   Öğren-Geç'te doğrulayarak bildiği kelimeler. Listeden
               silinmiyor, sadece en sona düşüyor.
    """
    from learnpass.models import WordEncounter

    kayitlar = WordEncounter.objects.filter(user=user).values_list(
        "word_id", "misjudged_count", "is_learned"
    )
    misjudged, learned = set(), set()
    for word_id, misjudged_count, is_learned in kayitlar:
        if misjudged_count:
            misjudged.add(word_id)
        elif is_learned:
            learned.add(word_id)
    return misjudged, learned


def classify_links_by_priority(links, misjudged_ids=None, learned_ids=None):
    """
    Kullanıcının kelime bağlantılarını (UserWordLink) üç öncelik grubuna ayırır
    ve her grubu kendi içinde sıralar.

    - priority1: yeni kelimeler (<=2 deneme), yanlış oranı yüksek olanlar ve
                 Öğren-Geç'te "bildiğini sanıyordum" çıkanlar
    - priority2: orta düzeyde zorlananlar
    - priority3: iyi bilinen kelimeler ve Öğren-Geç'te "öğrenildi" işaretliler

    misjudged_ids / learned_ids verilmezse fonksiyon yalnızca quiz
    istatistiklerine bakar (eski davranış).

    NOT: Bu fonksiyon eskiden attemptQuiz içinde satır arasındaydı ve
    yüzdelik wrongRatio değeri 0.50 / 0.2 gibi ondalık eşiklerle
    karşılaştırıldığı için neredeyse her kelime priority1'e düşüyordu.
    """
    priority1, priority2, priority3 = [], [], []
    misjudged_ids = misjudged_ids or set()
    learned_ids = learned_ids or set()

    for link in links:
        # Öğren-Geç sinyalleri quiz istatistiklerinin önüne geçiyor:
        # "bildiğini sanıyordu" bilgisi, birkaç doğru cevaptan daha değerli.
        if link.word_id in misjudged_ids:
            priority1.append(link)

        elif link.word_id in learned_ids:
            priority3.append(link)

        elif link.totalAttempts <= 2:
            priority1.append(link)

        elif link.totalAttempts <= 6:
            if link.wrongRatio >= WRONG_RATIO_HIGH:
                priority1.append(link)
            else:
                priority2.append(link)

        else:
            if link.wrongRatio >= WRONG_RATIO_HIGH:
                priority1.append(link)
            elif link.wrongRatio >= WRONG_RATIO_MID:
                priority2.append(link)
            else:
                priority3.append(link)

    # En az denenmiş ve en çok yanlış yapılan kelimeler önce sorulsun
    priority1.sort(key=lambda link: (link.totalAttempts, -link.wrongRatio))
    priority2.sort(key=lambda link: link.wrongRatio, reverse=True)
    priority3.sort(key=lambda link: link.wrongRatio, reverse=True)

    return priority1, priority2, priority3



@login_required
def attemptQuiz(request):

    if request.method == "POST":
        quizType = request.POST.get("quizType")
        totalQuestion = request.POST.get("totalQuestion")

        if quizType not in ("mixed", "matching", "multiple_choice", "writing", "random", "synonym_antonym", "fill_blank"):
            messages.error(request, "Hatalı bir quiz tipi seçildi.")
            return redirect("attempt_quiz")

        if totalQuestion not in ("5", "10", "15", "25", "40"):
            messages.error(request, "Hatalı bir soru sayısı seçildi.")
            return redirect("attempt_quiz")

        totalQuestion = int(totalQuestion)

        choices = ["mixed", "matching", "multiple_choice", "writing", "fill_blank"]
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

        elif quizType == "fill_blank":
            # Boşluk doldurma: sadece örnek cümlesinde (ya da collocation'ında)
            # kelimenin bir biçimi bulunabilen kelimeler sorulabilir.
            eligible_links = [
                lnk for lnk in links.select_related('word')
                if can_generate_blank(lnk.word)
            ]
            if totalQuestion > len(eligible_links):
                messages.error(
                    request,
                    f"Boşluk doldurma quiz'i için yeterli kelime yok. "
                    f"Listenizde örnek cümlesinden boşluk üretilebilen {len(eligible_links)} kelime var, "
                    f"ancak {totalQuestion} soruluk bir quiz istendi. "
                    "Kelimelerinize örnek cümle ekleyin ya da soru sayısını azaltın."
                )
                return redirect("attempt_quiz")
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

        misjudged_ids, learned_ids = encounter_signals(request.user)
        priority1, priority2, priority3 = classify_links_by_priority(
            links, misjudged_ids=misjudged_ids, learned_ids=learned_ids
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

            # Üretim gerektiren soruların yarısını boşluk doldurmaya ayır.
            # (Yazma ve boşluk doldurma aynı beceriyi farklı biçimde yokluyor:
            # biri tanımdan kelime, diğeri bağlamdan kelime.)
            split_at = len(wq_links) // 2
            fb_links = wq_links[:split_at]
            wq_links = wq_links[split_at:]

            for link in mc_links:
                generate_mc_question(link, newQuiz, all_user_words)
            for link in wq_links:
                generate_writing_question(link, newQuiz)
            for link in fb_links:
                # Boşluk üretilemeyen kelime için çoktan seçmeliye düş;
                # böylece toplam soru sayısı bozulmaz.
                if not generate_fill_blank_question(link, newQuiz):
                    generate_mc_question(link, newQuiz, all_user_words)
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

        elif quizType == "fill_blank":
            created = 0
            for link in links_to_ask:
                if generate_fill_blank_question(link, newQuiz):
                    created += 1

            # Ön filtreye rağmen bir soru üretilemediyse toplamı gerçeğe çek
            if created != newQuiz.totalQuestion:
                newQuiz.totalQuestion = created
                newQuiz.save(update_fields=["totalQuestion"])

            if created == 0:
                messages.error(request, "Boşluk doldurma sorusu üretilemedi.")
                newQuiz.delete()
                return redirect("attempt_quiz")

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

    # 1. Bu attempt'e ait tüm soruları (tiplerinden bağımsız) sıralı olarak al.
    # Soru tiplerinin listesi QUESTION_RELATED_NAMES'te tek yerde duruyor.
    all_questions = attempt.all_questions()

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
            elif question_type in ("WritingQuestion", "FillInTheBlankQuestion"):
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
        
    # --- Soru listesi (template_name ve combined_items artık model property'si) ---
    all_questions = attempt.all_questions()

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


# ======================================================================
# Bilgi Analizi
# ======================================================================

ANALYSIS_PER_PAGE_OPTIONS = (25, 50, 100, 200)
ANALYSIS_DEFAULT_PER_PAGE = 50

# Doğruluk oranını renge çeviren aralık: 0 = kırmızı, ortası sarı, 130 = yeşil.
# Şablon bu sayıyı hsl() içinde kullanıyor, böylece renk basamaklı değil
# sürekli oluyor (%61 ile %62 birbirinden bir tık farklı).
HUE_MAX = 130


def analysis_rows(page_object_list):
    """
    Sayfadaki bağlantıları satıra çevirir.

    Satırda bilinçli olarak yalnızca üç şey var: kelimenin kendisi, kaç kez
    çalışıldığı ve doğruluk oranı. Deneme sayısı olmadan oran yanıltıcı olurdu
    (2 denemede %50 ile 40 denemede %50 aynı şey değil).
    """
    rows = []
    for link in page_object_list:
        accuracy = link.accuracy or 0.0
        rows.append({
            "word": link.word,
            "attempts": link.attempts,
            "accuracy": round(accuracy),
            "hue": round(accuracy * HUE_MAX / 100),
        })
    return rows


@login_gate("Analiz", "Analiz senin kendi çalışma geçmişini gösterdiği için giriş yapman gerekiyor.")
def wordAnalysis(request):
    """
    Hangi kelimeyi iyi bildiğini, hangisinde takıldığını gösteren liste.

    Sıralama en çok yanlış yapılandan en çok doğru yapılana doğru. Aynı orana
    sahip kelimelerde çok denenmiş olan öne alınıyor: 20 denemede %50, 2
    denemede %50'den daha güvenilir bir "bunu bilmiyorsun" sinyali.

    Havuz yalnızca kullanıcının KENDİ listesindeki kelimeler. Hiç çalışılmamış
    kelimeler listeye girmiyor — doğruluk ekseninde yerleri yok — ama sayıları
    en altta tek satır olarak belirtiliyor.
    """
    user = request.user

    links = (
        UserWordLink.objects.filter(user=user)
        .select_related("word")
        .annotate(attempts=F("correctCount") + F("wrongCount"))
        .filter(attempts__gt=0)
        .annotate(
            accuracy=ExpressionWrapper(
                Cast(F("correctCount"), FloatField()) * 100.0
                / NullIf(F("correctCount") + F("wrongCount"), 0),
                output_field=FloatField(),
            )
        )
        .order_by("accuracy", "-attempts", "word__englishWord")
    )

    per_page = pagination.resolve_per_page(
        request, ANALYSIS_PER_PAGE_OPTIONS, ANALYSIS_DEFAULT_PER_PAGE
    )
    paginator = Paginator(links, per_page)
    page_obj = paginator.get_page(request.GET.get("page") or 1)

    # Özet: oranın tek başına anlatmadığını anlatan üç sayı
    toplamlar = UserWordLink.objects.filter(user=user).aggregate(
        dogru=Sum("correctCount"), yanlis=Sum("wrongCount")
    )
    dogru = toplamlar["dogru"] or 0
    yanlis = toplamlar["yanlis"] or 0
    toplam_deneme = dogru + yanlis

    context = {
        "active_page": "Analiz",
        "exercise_tab": "analysis",
        "rows": analysis_rows(page_obj.object_list),
        "studied_count": paginator.count,
        "untouched_count": UserWordLink.objects.filter(
            user=user, correctCount=0, wrongCount=0
        ).count(),
        "total_attempts": toplam_deneme,
        "overall_accuracy": round(dogru * 100 / toplam_deneme) if toplam_deneme else 0,
    }
    context.update(pagination.pagination_context(
        page_obj, paginator,
        params=[],
        per_page=per_page,
        per_page_options=ANALYSIS_PER_PAGE_OPTIONS,
        default_per_page=ANALYSIS_DEFAULT_PER_PAGE,
    ))

    return render(request, "pages/quizzes/wordAnalysis.html", context)
