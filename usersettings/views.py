from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import datetime

from users.models import User
from usersettings.models import UserSettings
from words.models import Word, UserWordLink
from comments.models import Comment
from texts.models import Text
from quizzes.models import ReviewItem, ReviewLog, StudySession

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

        # Geçerli seçenekler tek yerde (userprofile.views.DAILY_GOAL_OPTIONS);
        # burada yalnızca gelen değerin o kümede olup olmadığına bakılıyor.
        # NOT: Eskiden zincirde 0 için bir dal yoktu, yani kullanıcı "Yok"
        # seçtiğinde hedefi değişmiyor, eski değeri sessizce kalıyordu.
        from userprofile.views import DAILY_GOAL_OPTIONS

        gecerli_hedefler = {str(deger) for deger, _ in DAILY_GOAL_OPTIONS}
        if dailyGoal in gecerli_hedefler:
            settings.dailyGoal = int(dailyGoal)

        
        settings.save()

        messages.success(request, "Ayarlarınız kaydedildi.")
        return redirect("user_profile")

def _confirm_with_password(request):
    """
    Tehlikeli (geri dönüşsüz) işlemlerden önce kullanıcının parolasıyla
    onay almamızı sağlayan yardımcı. Sadece POST'larda çalışır ve
    formdan 'confirm_password' bekler. Onay başarısızsa False döner.
    """
    if request.method != "POST":
        messages.error(request, "Bu işlem yalnızca form üzerinden yapılabilir.")
        return False

    password = request.POST.get("confirm_password") or ""
    if not password:
        messages.error(request, "Lütfen onaylamak için parolanızı giriniz.")
        return False

    if not request.user.check_password(password):
        messages.error(request, "Parola hatalı. İşlem iptal edildi.")
        return False

    return True


@login_required
def removeAllWords(request):
    if not _confirm_with_password(request):
        return redirect("user_profile")

    user = request.user
    UserWordLink.objects.filter(user=user).delete()
    Word.objects.filter(owner=user).delete()

    messages.success(request, "Tüm kelimeleriniz listenizden başarıyla silindi.")
    return redirect("user_profile")


@login_required
def removeAllComments(request):
    if not _confirm_with_password(request):
        return redirect("user_profile")

    Comment.objects.filter(owner=request.user).delete()

    messages.success(request, "Tüm yorumlarınız silindi.")
    return redirect("user_profile")


@login_required
def deleteMyAccount(request):
    if not _confirm_with_password(request):
        return redirect("user_profile")

    # Doğru objeyi sil — request.user zaten doğru User objesidir
    request.user.delete()

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
            response.write(f"Kelime: {word.text}\n")
            response.write(f"Anlamı: {word.meaningTr}\n")
            response.write(f"Açıklama: {word.explanation}\n")
            response.write(f"Not: {word.note}\n")
            response.write(f"Eş Anlamlılar: {word.synonyms or '-'}\n")
            response.write(f"Zıt Anlamlılar: {word.antonyms or '-'}\n")
            response.write(f"Kullanım Kalıpları: {word.collocations or '-'}\n")
            for index, sentence in enumerate(word.example_sentences, start=1):
                response.write(f"Örnek Cümle {index}: {sentence}\n")
            response.write(f"Seviye: {word.cefr}\n")
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



# ----------------------------------------------------------------------
# Çalışma geçmişi dökümü
# ----------------------------------------------------------------------

def _write_study_history(write_line, user):
    """
    Kullanıcının çalışma geçmişini metin olarak yazar.

    Eski döküm SORU METİNLERİNİ yazıyordu (şıklar, verilen cevap, doğru
    şık). Yeni sistemde sorular kalıcı değil — her tekrarda yeniden
    üretiliyorlar — ve zaten kullanıcıya ait olan şey soru değil,
    ÖĞRENME GEÇMİŞİ: hangi kelimenin hangi boyutunu ne zaman bildi,
    bir sonraki tekrar ne zaman. Döküm bunu veriyor.
    """
    from quizzes.models import ReviewItem, ReviewLog, StudySession

    oturumlar = StudySession.objects.filter(user=user).order_by("-started_at")
    write_line(f"Toplam {oturumlar.count()} çalışma oturumu.\n")

    for i, oturum in enumerate(oturumlar[:200], 1):
        write_line(f"OTURUM #{i}  —  {oturum.started_at.strftime('%d-%m-%Y %H:%M')}")
        write_line(f"  Kapsam: {oturum.get_mode_display()}")
        write_line(f"  Süre: {oturum.formatted_duration}")
        write_line(f"  {oturum.answered_count} soru, {oturum.correct_count} doğru")

        kayitlar = oturum.logs.all().order_by("answered_at")
        for kayit in kayitlar:
            sonuc = "DOĞRU" if kayit.is_correct else "YANLIŞ"
            write_line(f"    {kayit.word_text:<20} {kayit.get_aspect_display():<20} "
                       f"{sonuc:<7} → {kayit.scheduled_days:.0f} gün sonra")
        write_line("")

    write_line("\n--- KART DURUMLARI ---\n")
    kartlar = (ReviewItem.objects.filter(user=user)
               .select_related("word").order_by("word__text", "aspect"))
    for kart in kartlar:
        kararlilik = "—" if kart.stability is None else f"{kart.stability:.1f} gün"
        sira = kart.due_at.strftime("%d-%m-%Y") if kart.due_at else "—"
        write_line(f"  {kart.word.text:<20} {kart.get_aspect_display():<20} "
                   f"kararlılık: {kararlilik:<10} sıradaki tekrar: {sira}")

    toplam_kayit = ReviewLog.objects.filter(user=user).count()
    write_line(f"\nToplam {toplam_kayit} cevap kaydı.")


@login_required
def exportMyQuizzes(request):
    """Çalışma geçmişi dökümü (eski adıyla 'quizlerim')."""
    user = request.user

    response = HttpResponse(content_type='application/octet-stream')
    filename = f"learnvocab_calismalarim_{user.username}.txt"
    response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'

    def write_line(text):
        response.write(text.encode('utf-8') + b"\n")

    write_line("LearnVocab Çalışma Dökümü")
    write_line(f"Kullanıcı: {user.username}")
    write_line(f"Tarih: {datetime.date.today().strftime('%d-%m-%Y')}")
    write_line("="*40 + "\n")

    _write_study_history(write_line, user)
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
            write_line(f"Kelime: {word.text}")
            write_line(f"Anlamı: {word.meaningTr}")
            write_line(f"Açıklama: {word.explanation or ''}") # None ise hata vermesin
            write_line(f"Not: {word.note or ''}")           # None ise hata vermesin
            write_line(f"Seviye: {word.cefr}")
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
    write_line(" BOLUM 5: CALISMA GECMISIM")
    write_line("="*50 + "\n")

    _write_study_history(write_line, user)

    return response

