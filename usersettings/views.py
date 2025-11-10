from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import datetime

from users.models import User
from usersettings.models import UserSettings
from words.models import Word, UserWordLink
from comments.models import Comment
from texts.models import Text
from quizzes.models import *

from django.db.models import Q

# Create your views here.

@login_required
def saveSettings(request):
    if request.method == "POST":
        user = request.user

        dailyGoal = request.POST.get("dailyGoal")
        audio = request.POST.get("audio")
        dailyGoalMail = request.POST.get("dailyGoalsMail")
        featuresMail = request.POST.get("featuresMail")
        improvementsMail  = request.POST.get("improvementsMail")

        settings = UserSettings.objects.filter(user = user).first()

        #print(dailyGoal, audio, dailyGoalMail, featuresMail, improvementsMail, sep = "\n")

        if audio != None: settings.audio = True
        else: settings.audio = False

        if dailyGoalMail != None: settings.dailyGoalsMail = True
        else: settings.dailyGoalsMail = False

        if featuresMail != None: settings.featuresMail = True
        else: settings.featuresMail = False

        if improvementsMail != None: settings.improvementsMail = True
        else: settings.improvementsMail = False

        if dailyGoal == "5":
            settings.dailyGoal = 5
        elif dailyGoal == "10":
            settings.dailyGoal = 10
        elif dailyGoal == "15":
            settings.dailyGoal = 15
        elif dailyGoal == "20":
            settings.dailyGoal = 20
            
        settings.save()

        messages.success(request, "Ayarlarınız kaydedildi.")
        return redirect("profile_settings")

@login_required
def removeAllWords(request):
    user = request.user

    links = UserWordLink.objects.filter(user = user)
    links.delete()

    words = Word.objects.filter(owner = user)
    words.delete()

    messages.success(request, "Tüm kelimeleriniz listenizden başarıyla silindi.")
    return redirect("profile_settings")

@login_required
def removeAllComments(request):
    user = request.user

    comments = Comment.objects.filter(owner = user)
    comments.delete()

    messages.success(request, "Tüm yorumlarınız silindi.")
    return redirect("profile_settings")

@login_required
def deleteMyAccount(request):
    user = request.user

    current_one = User.objects.filter(username = user.username).first()
    current_one.delete()

    messages.success(request, "Hesabınız başarılı bir şekilde silindi.")
    return redirect("index")


@login_required
def exportMyWords(request):
    user = request.user
    
    word_ids_from_links = UserWordLink.objects.filter(user=user).values_list('word_id', flat=True)

    # Bu ID'lere sahip olan tüm Word objelerini getir
    words_from_links_qs = Word.objects.filter(id__in=word_ids_from_links)

    # --- Kaynak 2: 'words_in_list' (Diğer kelime listeniz) ---
    # Örnek olarak, bu listenin kullanıcının bizzat "sahibi olduğu" 
    # (kendi eklediği) kelimeler olduğunu varsayalım.
    # BU SORGUNUN SİZDE NE OLDUĞUNU BİLMİYORUM, SADECE BİR ÖRNEK:
    words_in_list = Word.objects.filter(owner=user)

    total_words = words_from_links_qs.union(words_in_list)

    # 2. Bir HttpResponse objesi oluşturun
    #    content_type='text/plain', tarayıcıya bunun bir metin dosyası olduğunu söyler.
    response = HttpResponse(content_type='text/plain; charset=utf-8')
    
    # 3. Content-Disposition, tarayıcıya bunu indirmesini söyler ve dosya adını belirler
    filename = f"learnvocab_kelimelerim_{user.username}.txt"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # 4. Dosyanın içeriğini oluşturun ve response'a yazın
    response.write(f"LearnVocab Kelime Dökümü\n")
    response.write(f"Kullanıcı: {user.username}\n")
    response.write(f"Tarih: {datetime.date.today().strftime('%d-%m-%Y')}\n")
    response.write("="*30 + "\n\n")
    
    if words_in_list.exists():
        response.write("Kelime Listeniz:\n\n")
        for word in total_words:
            response.write(f"Kelime: {word.englishWord}\n")
            response.write(f"Anlamı: {word.meaningTr}\n")
            response.write(f"Açıklama: {word.explanation}\n")
            response.write(f"Not: {word.note}\n")
            response.write(f"Seviye: {word.wordLevel}\n")
            response.write("--------------------\n")
    else:
        response.write("Dışa aktarılacak kelime bulunamadı.\n")

    return response


@login_required
def exportMyComments(request):
    user = request.user
    
    comments = Comment.objects.filter(owner = user)

    # content_type doğru
    response = HttpResponse(content_type='application/octet-stream')

    # Content-Disposition doğru
    filename = f"learnvocab_yorumlarım_{user.username}.txt"
    response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'

    # DÜZELTME: Tüm 'response.write'ları .encode() ile byte'a çevirin
    
    def write_line(text):
        response.write(text.encode('utf-8') + b"\n")

    # 4. Dosyanın içeriğini oluşturun
    write_line(f"LearnVocab Yorum Dökümü")
    write_line(f"Kullanıcı: {user.username}")
    write_line(f"Tarih: {datetime.date.today().strftime('%d-%m-%Y')}")
    write_line("="*30 + "\n")
    
    if comments.exists():
        write_line("Yorumlarınız:\n")
        for comment in comments:
            write_line(f"Yorum: {comment.content}")
            write_line(f"Eklenme Tarihi: {comment.createdAt.strftime('%d-%m-%Y')}")
            write_line(f"Like Sayısı: {comment.liked_by.count()}")
            write_line(f"Dislike Sayısı: {comment.disliked_by.count()}")
            write_line("--------------------")
    else:
        write_line("Dışa aktarılacak yorum bulunamadı.")

    return response


@login_required
def exportMyTexts(request):
    user = request.user
    
    texts = Text.objects.filter(owner = user)

    # content_type doğru
    response = HttpResponse(content_type='application/octet-stream')

    # Content-Disposition doğru
    filename = f"learnvocab_metinlerim_{user.username}.txt"
    response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'

    # DÜZELTME: Tüm 'response.write'ları .encode() ile byte'a çevirin
    
    def write_line(text):
        response.write(text.encode('utf-8') + b"\n")

    # 4. Dosyanın içeriğini oluşturun
    write_line(f"LearnVocab Metin Dökümü")
    write_line(f"Kullanıcı: {user.username}")
    write_line(f"Tarih: {datetime.date.today().strftime('%d-%m-%Y')}")
    write_line("="*30 + "\n")
    
    if texts.exists():
        write_line("Yorumlarınız:\n")
        for text in texts:
            write_line(f"Metniniz: {text.content}")
            write_line(f"Eklenme Tarihi: {text.createdAt.strftime('%d-%m-%Y')}")
            write_line(f"Puanınız: {text.score}")
            write_line(f"Kriter Puanları: {text.scores}")
            write_line(f"Gemini Pro Cevap: {text.response}")
            write_line("--------------------")
    else:
        write_line("Dışa aktarılacak yorum bulunamadı.")

    return response


@login_required
def exportMyQuizzes(request):
    user = request.user
    
    # 1. Yanıtı ve dosya ayarlarını hazırla
    response = HttpResponse(content_type='application/octet-stream')
    filename = f"learnvocab_quizlerim_{user.username}.txt"
    response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'

    # 2. String'leri byte'a çevirerek yazan yardımcı fonksiyon
    def write_line(text):
        response.write(text.encode('utf-8') + b"\n")

    # 3. Dosya Başlığını Yaz
    write_line(f"LearnVocab Quiz Dökümü")
    write_line(f"Kullanıcı: {user.username}")
    write_line(f"Tarih: {datetime.date.today().strftime('%d-%m-%Y')}")
    write_line("="*40 + "\n")

    # 4. Kullanıcının tüm quiz denemelerini al (en yeniden en eskiye)
    attempts = QuizAttempt.objects.filter(owner=user).order_by('-createdAt')

    if not attempts.exists():
        write_line("Dışa aktarılacak tamamlanmış quiz bulunamadı.")
        return response

    write_line(f"Toplam {attempts.count()} quiz denemesi bulundu:\n")
    write_line("="*40 + "\n")

    # 5. Her bir quiz denemesini (Attempt) döngüye al
    for i, attempt in enumerate(attempts, 1):
        write_line(f"QUIZ #{i}")
        write_line(f"Tarih: {attempt.createdAt.strftime('%d-%m-%Y %H:%M')}")
        write_line(f"Türü: {attempt.get_quizType_display()}")
        write_line(f"Durum: {'Tamamlandı' if attempt.isCompleted else 'Tamamlanmadı'}")
        write_line(f"Toplam Süre: {attempt.formatted_total_time}")
        write_line(f"SKOR: {attempt.totalCorrect} DOĞRU / {attempt.totalWrong} YANLIŞ / {attempt.totalEmpty()} BOŞ")
        write_line("\n  --- Sorular ---")

        # 6. BU KISIM ÖNEMLİ: 3 FARKLI TİPTEKİ TÜM SORULARI TOPLA
        all_questions = []
        
        # Eşleştirme sorularının 'words' alanını veritabanından önceden çekiyoruz
        # Bu, 'left_column_items' gibi özelliklerin düzgün çalışmasını sağlar
        mc_qs = attempt.multiplechoicequestion_questions.all()
        wq_qs = attempt.writingquestion_questions.all()
        mq_qs = attempt.matchingquestion_questions.all().prefetch_related('words') 

        all_questions.extend(mc_qs)
        all_questions.extend(wq_qs)
        all_questions.extend(mq_qs)
        
        # Soruları, quiz'deki orijinal sıralarına (ID'ye) göre sırala
        all_questions.sort(key=lambda q: q.id)

        if not all_questions:
            write_line("  Bu quiz'e ait soru bulunamadı.\n")
            continue

        # 7. Her bir soruyu tipiyle birlikte yazdır
        for q_num, q in enumerate(all_questions, 1):
            write_line(f"\n  Soru {q_num}:")
            
            # Python'un 'isinstance' fonksiyonu ile sorunun tipini kontrol et
            if isinstance(q, MultipleChoiceQuestion):
                write_line(f"    Tipi: Çoktan Seçmeli")
                write_line(f"    Soru: {q.question_text}")
                options_str = ", ".join([f"{opt[0]}: {opt[1]}" for opt in q.options_as_list])
                write_line(f"    Seçenekler: {options_str}")
                write_line(f"    Verilen Cevap: {q.user_answer or 'Boş'}")
                write_line(f"    Doğru Cevap: {q.correct_option}")
                write_line(f"    Durum: {'Doğru' if q.is_correct else 'Yanlış'}")

            elif isinstance(q, WritingQuestion):
                write_line(f"    Tipi: Yazma")
                write_line(f"    Soru: {q.question_text}")
                write_line(f"    Verilen Cevap: {q.user_answer or 'Boş'}")
                write_line(f"    Doğru Cevap: {q.correct_answer}")
                write_line(f"    Durum: {'Doğru' if q.is_correct else 'Yanlış'}")

            elif isinstance(q, MatchingQuestion):
                write_line(f"    Tipi: Eşleştirme")
                write_line(f"    Soru: {q.question_text}")
                write_line(f"    Sonuç: {q.correct_matches} doğru, {q.wrong_matches} yanlış eşleşme.")

            # Ortak alanlar
            write_line(f"    Süre: {q.time_taken or 0:.1f} sn")

        write_line("\n" + "-"*40 + "\n") # Bir sonraki quiz'e geçmeden önce ayraç

    return response


@login_required
def exportAll(request):
    user = request.user
    
    # 1. Yanıtı ve dosya ayarlarını hazırla
    response = HttpResponse(content_type='application/octet-stream')
    filename = f"learnvocab_TUM_VERILERIM_{user.username}.txt"
    response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'

    # 2. String'leri byte'a çevirerek yazan yardımcı fonksiyon
    def write_line(text):
        response.write(text.encode('utf-8') + b"\n")

    # 3. ANA BAŞLIK
    write_line(f"LearnVocab Tum Veri Dokumu")
    write_line(f"Kullanıcı: {user.username}")
    write_line(f"Tarih: {datetime.date.today().strftime('%d-%m-%Y %H:%M')}")

    # ==========================================================
    # BÖLÜM 1: KULLANICI AYARLARI (saveSettings'ten)
    # ==========================================================
    write_line("\n" + "="*50)
    write_line(" BOLUM 1: KULLANICI AYARLARI")
    write_line("="*50 + "\n")
    try:
        settings = UserSettings.objects.get(user=user)
        write_line(f"Günlük Hedef: {settings.dailyGoal}")
        write_line(f"Ses Ayarı (Audio): {'Açık' if settings.audio else 'Kapalı'}")
        write_line(f"Günlük Hedef Maili: {'İzin Verildi' if settings.dailyGoalsMail else 'İzin Verilmedi'}")
        write_line(f"Yeni Özellikler Maili: {'İzin Verildi' if settings.featuresMail else 'İzin Verilmedi'}")
        write_line(f"Geliştirmeler Maili: {'İzin Verildi' if settings.improvementsMail else 'İzin Verilmedi'}")
    except UserSettings.DoesNotExist:
        write_line("Kullanıcı ayar profili bulunamadı.")


    # ==========================================================
    # BÖLÜM 2: KELİMELER (exportMyWords'ten)
    # ==========================================================
    write_line("\n" + "="*50)
    write_line(" BOLUM 2: KELIMELERIM")
    write_line("="*50 + "\n")
    
    word_ids_from_links = UserWordLink.objects.filter(user=user).values_list('word_id', flat=True)
    words_from_links_qs = Word.objects.filter(id__in=word_ids_from_links)
    words_in_list = Word.objects.filter(owner=user)
    total_words = words_from_links_qs.union(words_in_list)

    if total_words.exists():
        write_line(f"Toplam {total_words.count()} kelime bulundu:\n")
        for word in total_words:
            write_line(f"Kelime: {word.englishWord}")
            write_line(f"Anlamı: {word.meaningTr}")
            write_line(f"Açıklama: {word.explanation or ''}") # None ise hata vermesin
            write_line(f"Not: {word.note or ''}")           # None ise hata vermesin
            write_line(f"Seviye: {word.wordLevel}")
            write_line("--------------------")
    else:
        write_line("Dışa aktarılacak kelime bulunamadı.")

    # ==========================================================
    # BÖLÜM 3: YORUMLAR (exportMyComments'ten)
    # ==========================================================
    write_line("\n" + "="*50)
    write_line(" BOLUM 3: YORUMLARIM")
    write_line("="*50 + "\n")
    
    comments = Comment.objects.filter(owner = user)
    if comments.exists():
        write_line(f"Toplam {comments.count()} yorum bulundu:\n")
        for comment in comments:
            write_line(f"Yorum: {comment.content}")
            write_line(f"Eklenme Tarihi: {comment.createdAt.strftime('%d-%m-%Y')}")
            write_line(f"Like Sayısı: {comment.liked_by.count()}")
            write_line(f"Dislike Sayısı: {comment.disliked_by.count()}")
            write_line("--------------------")
    else:
        write_line("Dışa aktarılacak yorum bulunamadı.")

    # ==========================================================
    # BÖLÜM 4: METİNLER (exportMyTexts'ten)
    # ==========================================================
    write_line("\n" + "="*50)
    write_line(" BOLUM 4: METINLERIM (WRITING ALANI)")
    write_line("="*50 + "\n")
    
    texts = Text.objects.filter(owner = user)
    if texts.exists():
        write_line(f"Toplam {texts.count()} metin bulundu:\n")
        for text in texts:
            write_line(f"Eklenme Tarihi: {text.createdAt.strftime('%d-%m-%Y')}")
            write_line(f"Puanınız: {text.score}")
            write_line("--- Sizin Metniniz ---")
            write_line(text.content)
            write_line("--- Gemini Değerlendirmesi ---")
            write_line(f"Kriter Puanları: {text.scores}")
            write_line(f"Açıklama: {text.response}")
            write_line("--------------------")
    else:
        write_line("Dışa aktarılacak metin bulunamadı.")

    # ==========================================================
    # BÖLÜM 5: QUIZLER (exportMyQuizzes'ten)
    # ==========================================================
    write_line("\n" + "="*50)
    write_line(" BOLUM 5: QUIZLERIM")
    write_line("="*50 + "\n")

    attempts = QuizAttempt.objects.filter(owner=user).order_by('-createdAt')

    if not attempts.exists():
        write_line("Dışa aktarılacak tamamlanmış quiz bulunamadı.")
    else:
        write_line(f"Toplam {attempts.count()} quiz denemesi bulundu:\n")
        
        # Her bir quiz denemesini (Attempt) döngüye al
        for i, attempt in enumerate(attempts, 1):
            write_line(f"QUIZ #{i}")
            write_line(f"Tarih: {attempt.createdAt.strftime('%d-%m-%Y %H:%M')}")
            write_line(f"Türü: {attempt.get_quizType_display()}")
            write_line(f"Durum: {'Tamamlandı' if attempt.isCompleted else 'Tamamlanmadı'}")
            write_line(f"Toplam Süre: {attempt.formatted_total_time}")
            write_line(f"SKOR: {attempt.totalCorrect} DOĞRU / {attempt.totalWrong} YANLIŞ / {attempt.totalEmpty()} BOŞ")
            write_line("\n  --- Sorular ---")

            all_questions = []
            mc_qs = attempt.multiplechoicequestion_questions.all()
            wq_qs = attempt.writingquestion_questions.all()
            mq_qs = attempt.matchingquestion_questions.all().prefetch_related('words') 

            all_questions.extend(mc_qs)
            all_questions.extend(wq_qs)
            all_questions.extend(mq_qs)
            all_questions.sort(key=lambda q: q.id)

            if not all_questions:
                write_line("  Bu quiz'e ait soru bulunamadı.\n")
                continue

            for q_num, q in enumerate(all_questions, 1):
                write_line(f"\n  Soru {q_num}:")
                
                if isinstance(q, MultipleChoiceQuestion):
                    write_line(f"    Tipi: Çoktan Seçmeli")
                    write_line(f"    Soru: {q.question_text}")
                    options_str = ", ".join([f"{opt[0]}: {opt[1]}" for opt in q.options_as_list])
                    write_line(f"    Seçenekler: {options_str}")
                    write_line(f"    Verilen Cevap: {q.user_answer or 'Boş'}")
                    write_line(f"    Doğru Cevap: {q.correct_option}")
                    write_line(f"    Durum: {'Doğru' if q.is_correct else 'Yanlış'}")

                elif isinstance(q, WritingQuestion):
                    write_line(f"    Tipi: Yazma")
                    write_line(f"    Soru: {q.question_text}")
                    write_line(f"    Verilen Cevap: {q.user_answer or 'Boş'}")
                    write_line(f"    Doğru Cevap: {q.correct_answer}")
                    write_line(f"    Durum: {'Doğru' if q.is_correct else 'Yanlış'}")

                elif isinstance(q, MatchingQuestion):
                    write_line(f"    Tipi: Eşleştirme")
                    write_line(f"    Soru: {q.question_text}")
                    write_line(f"    Sonuç: {q.correct_matches} doğru, {q.wrong_matches} yanlış eşleşme.")

                write_line(f"    Süre: {q.time_taken or 0:.1f} sn")

            write_line("\n" + "-"*40 + "\n")

    return response

