from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import datetime

from users.models import User
from usersettings.models import UserSettings
from words.models import Word, UserWordLink
from comments.models import Comment
from texts import degerlendirme
from texts.models import Sertlik, Text, YaziDurumu, YazmaAyari
from django.urls import reverse
from egzersizler.sorular import SORU_SAYILARI
from LearnVocab.authgate import login_gate

from django.db.models import Q

TEMA_SECENEKLERI = (("sistem", "Sistem"), ("light", "Açık"), ("dark", "Koyu"))


@login_gate("Ayarlar")
def ayarlarSayfasi(request):
    """
    Ayarlar sayfası (rapor 18.26). Hesap sayfasından gelinir.
    Tema cihazda saklanır (tarayıcı); diğerleri save_settings'e POST eder.
    """
    ayarlar, _ = UserSettings.objects.get_or_create(user=request.user)
    return render(request, "pages/profile/ayarlar.html", {
        "active_page": "Ayarlar",
        "settings": ayarlar,
        "tekrar_orani": 100 - ayarlar.learnpass_yeni_orani,
        "tema_secenekleri": TEMA_SECENEKLERI,
        "sertlik": YazmaAyari.sertlik_of(request.user),
        "sertlik_secenekleri": Sertlik.choices,
        "soru_sayilari": SORU_SAYILARI,
        "export_links": [
            {"url": reverse("export_all"), "label": "Tüm verilerim"},
            {"url": reverse("export_mywords"), "label": "Kelimelerim"},
            {"url": reverse("export_mytexts"), "label": "Metinlerim"},
        ],
    })


@login_required
def saveSettings(request):
    if request.method == "POST":
        user = request.user

        audio = request.POST.get("audio")
        dailyGoalMail = request.POST.get("dailyGoalsMail")
        featuresMail = request.POST.get("featuresMail")
        improvementsMail  = request.POST.get("improvementsMail")

        settings, _ = UserSettings.objects.get_or_create(user=user)

        # Yeni kelime oranı: 0–100, %10'luk adımlar. Geçersiz değer yok sayılır.
        oran = request.POST.get("learnpass_yeni_orani")
        if oran is not None and oran.isdigit() and int(oran) in range(0, 101, 10):
            settings.learnpass_yeni_orani = int(oran)

        sayi = request.POST.get("egzersiz_soru_sayisi")
        if sayi is not None and sayi.isdigit() and int(sayi) in SORU_SAYILARI:
            settings.egzersiz_soru_sayisi = int(sayi)

        sertlik = request.POST.get("sertlik")
        if sertlik in Sertlik.values:
            YazmaAyari.objects.update_or_create(user=user, defaults={"sertlik": sertlik})

        #print(dailyGoal, audio, dailyGoalMail, featuresMail, improvementsMail, sep = "\n")

        if audio != None: settings.audio = True
        else: settings.audio = False

        if dailyGoalMail != None: settings.dailyGoalsMail = True
        else: settings.dailyGoalsMail = False

        if featuresMail != None: settings.featuresMail = True
        else: settings.featuresMail = False

        if improvementsMail != None: settings.improvementsMail = True
        else: settings.improvementsMail = False

        settings.save()

        messages.success(request, "Ayarların kaydedildi.")
        return redirect("settings_page")

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
        return redirect("settings_page")

    user = request.user
    UserWordLink.objects.filter(user=user).delete()
    Word.objects.filter(owner=user).delete()

    messages.success(request, "Tüm kelimeleriniz listenizden başarıyla silindi.")
    return redirect("settings_page")


@login_required
def removeAllComments(request):
    if not _confirm_with_password(request):
        return redirect("settings_page")

    Comment.objects.filter(owner=request.user).delete()

    messages.success(request, "Tüm yorumlarınız silindi.")
    return redirect("settings_page")


@login_required
def deleteMyAccount(request):
    if not _confirm_with_password(request):
        return redirect("settings_page")

    # Doğru objeyi sil — request.user zaten doğru User objesidir
    request.user.delete()

    messages.success(request, "Hesabınız başarılı bir şekilde silindi.")
    return redirect("index")


def _virgullu(parcalar):
    """Kelime ilişkilerini ve kalıpları dökümde tek satırda yazar."""
    return ", ".join(p for p in parcalar if p)


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

    # union() varsayılan sıralamayla SQLite'ta çöküyor; tek sorgu yeterli.
    total_words = Word.objects.filter(Q(id__in=word_ids_from_links) | Q(owner=user)).distinct()

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
    
    if total_words.exists():
        response.write("Kelime Listeniz:\n\n")
        for word in total_words:
            response.write(f"Kelime: {word.text}\n")
            response.write(f"Anlamı: {word.meaningTr}\n")
            response.write(f"Açıklama: {word.explanation}\n")
            response.write(f"Eş Anlamlılar: {_virgullu(r.to_word.text for r in word.synonyms) or '-'}\n")
            response.write(f"Zıt Anlamlılar: {_virgullu(r.to_word.text for r in word.antonyms) or '-'}\n")
            response.write(f"Kullanım Kalıpları: {_virgullu(c.pattern for c in word.collocations) or '-'}\n")
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
    # union() varsayılan sıralamayla SQLite'ta çöküyor; tek sorgu yeterli.
    total_words = Word.objects.filter(Q(id__in=word_ids_from_links) | Q(owner=user)).distinct()

    if total_words.exists():
        write_line(f"Toplam {total_words.count()} kelime bulundu:\n")
        for word in total_words:
            write_line(f"Kelime: {word.text}")
            write_line(f"Anlamı: {word.meaningTr}")
            write_line(f"Açıklama: {word.explanation or ''}") # None ise hata vermesin
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

