from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import datetime

from users.models import User
from usersettings.models import UserSettings
from words.models import Word, UserWordLink
from comments.models import Comment
from texts import degerlendirme
from texts.models import Text, YaziDurumu

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



def metin_disa_aktarma_satirlari(text):
    """
    Bir Yazma kaydının dışa aktarma satırları.

    Yeni kayıtlar (rapor 9.1): 5 üzerinden puan, durum, iki liste (iyi
    yapılanlar ve hatalar). Eski sistemin kayıtları (durum=eski) eskisi gibi:
    100 üzerinden puan, kriter puanları, modelin düz cevabı.
    """
    satirlar = [f"Eklenme Tarihi: {text.createdAt.strftime('%d-%m-%Y')}"]
    if text.konu:
        satirlar.append(f"Konu: {text.konu}")
    satirlar += ["--- Metniniz ---", text.content]

    if text.durum == YaziDurumu.ESKI:
        satirlar += [
            "--- Değerlendirme (eski sistem) ---",
            f"Puanınız: {text.score} / 100",
            f"Kriter Puanları: {text.scores}",
            f"Açıklama: {text.response}",
        ]
        return satirlar

    satirlar.append(f"Durum: {text.get_durum_display()}")
    if text.durum != YaziDurumu.TAMAM:
        return satirlar

    satirlar.append("--- Değerlendirme ---")
    if text.puan is not None:
        satirlar.append(f"Puanınız: {degerlendirme.puan_yazisi(text.puan)} / 5 "
                        f"({degerlendirme.puan_etiketi(text.puan)})")
    geri = text.geri_bildirim or {}
    iyiler = geri.get("iyi") or []
    hatalar = geri.get("hatalar") or []
    if iyiler:
        satirlar.append("İyi yapılanlar:")
        satirlar += [f"  + \"{m.get('alinti', '')}\": {m.get('aciklama', '')}" for m in iyiler]
    if hatalar:
        satirlar.append("Hatalar:")
        satirlar += [f"  - {m.get('alinti', '')} → {m.get('dogrusu', '')} · {m.get('neden', '')}"
                     for m in hatalar]
    else:
        satirlar.append("Hata bulunmadı.")
    return satirlar


def _disa_aktarilacak_metinler(user):
    """Kullanıcının sildiği (Geri al süresindeki) metinler dışa aktarılmaz."""
    return Text.objects.filter(owner=user, silindi__isnull=True).order_by("createdAt", "id")


@login_required
def exportMyTexts(request):
    user = request.user
    
    texts = _disa_aktarilacak_metinler(user)

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
        write_line("Metinleriniz:\n")
        for text in texts:
            for satir in metin_disa_aktarma_satirlari(text):
                write_line(satir)
            write_line("--------------------")
    else:
        write_line("Dışa aktarılacak metin bulunamadı.")

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
    
    texts = _disa_aktarilacak_metinler(user)
    if texts.exists():
        write_line(f"Toplam {texts.count()} metin bulundu:\n")
        for text in texts:
            for satir in metin_disa_aktarma_satirlari(text):
                write_line(satir)
            write_line("--------------------")
    else:
        write_line("Dışa aktarılacak metin bulunamadı.")

    return response

