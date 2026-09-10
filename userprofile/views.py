from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from words.models import Word, UserWordLink, WordList
from users.models import User
from texts.models import Text
from django.contrib import messages
from usersettings.models import UserSettings

from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Q
from quizzes.models import MultipleChoiceQuestion, WritingQuestion, MatchingQuestion
from words.addWeeks.addWeeks import wordsAddDelete, allWordsAddDelete

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
    """
    Kullanıcının "Kelimelerim" sayfası. Aşağıdaki ?list_id= sorgu parametresi
    bir liste ID'si verirse sadece o listeye ait kelimeleri gösterir.
    list_id=__all__ veya boş ise kullanıcının tüm kelimeleri gösterilir.
    """
    user = request.user

    # Kullanıcının ana havuzu: kendi eklediği + listesine kaydettiği kelimeler
    base_words = Word.objects.filter(
        Q(owner=user) | Q(saved_by=user)
    ).distinct()

    # ---- Liste filtresi ----
    user_lists = WordList.objects.filter(owner=user).prefetch_related("words")
    selected_list_id = request.GET.get("list_id", "").strip()
    selected_list = None
    if selected_list_id and selected_list_id != "__all__":
        try:
            selected_list = user_lists.get(id=int(selected_list_id))
        except (ValueError, WordList.DoesNotExist):
            selected_list = None

    if selected_list is not None:
        words = base_words.filter(in_user_lists=selected_list)
    else:
        words = base_words

    # ---- Arama ----
    search_query = request.GET.get('q', '').strip()
    if search_query:
        words = words.filter(
            Q(englishWord__icontains=search_query) |
            Q(meaningTr__icontains=search_query)
        )

    # Sıralama (deterministik) — pagination'ın doğru çalışması için zorunlu
    words = words.order_by("englishWord", "id")

    # ---- Sayfalama ----
    # Sayfa başına gösterilecek kelime sayısı (?per_page= query ile değiştirilebilir)
    try:
        per_page = int(request.GET.get("per_page", 30))
        if per_page not in (15, 30, 60, 120):
            per_page = 30
    except (TypeError, ValueError):
        per_page = 30

    paginator = Paginator(words, per_page)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    # 3-4 önceki/sonraki sayfa linklerini hesapla (ellipsis için)
    page_window = _build_page_window(page_obj.number, paginator.num_pages, side=3)

    # Listelerin sayım bilgisi (her liste için kaç kelime var)
    lists_with_counts = []
    for wl in user_lists:
        lists_with_counts.append({
            "id": wl.id,
            "name": wl.name,
            "color": wl.color,
            "count": wl.words.count(),
        })

    # Hangi listeye eklenebilir? (Aktif liste haricindekiler)
    movable_targets = [l for l in lists_with_counts if l["id"] != (selected_list.id if selected_list else None)]

    # Pagination linklerinde korunacak query parametreleri
    extra_params = []
    if search_query:
        extra_params.append(f"q={search_query}")
    if selected_list:
        extra_params.append(f"list_id={selected_list.id}")
    if per_page != 30:
        extra_params.append(f"per_page={per_page}")
    base_qs = "&".join(extra_params)

    context = {
        "active_page": "Kelimelerim",
        "words": page_obj.object_list,           # Geriye dönük uyumluluk
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "page_window": page_window,
        "per_page": per_page,
        "base_qs": base_qs,
        "search_query": search_query,
        "user_lists": lists_with_counts,
        "selected_list": selected_list,
        "selected_list_id": selected_list_id or "__all__",
        "total_word_count": base_words.count(),
        "movable_targets": movable_targets,
    }

    return render(request, "pages/profile/words.html", context)


def _build_page_window(current, total, side=3):
    """
    Sayfa numarası listesi üretir; ellipsis (None) ile boşluk bırakır.
    Örn: current=10, total=20, side=3 → [1, None, 7,8,9,10,11,12,13, None, 20]
    """
    if total <= 1:
        return [1] if total == 1 else []

    start = max(2, current - side)
    end = min(total - 1, current + side)

    pages = [1]
    if start > 2:
        pages.append(None)  # ...
    for p in range(start, end + 1):
        pages.append(p)
    if end < total - 1:
        pages.append(None)  # ...
    if total > 1:
        pages.append(total)

    # Tekilleştir (1 veya total komşulukta tekrar etmesin)
    seen = set()
    cleaned = []
    for p in pages:
        if p is None:
            if cleaned and cleaned[-1] is None:
                continue
            cleaned.append(None)
        else:
            if p in seen:
                continue
            seen.add(p)
            cleaned.append(p)
    return cleaned


# =============================================================================
# Kullanıcı kelime listeleri (WordList) - klasör mantığı
# =============================================================================

def _user_words_qs(user):
    """Kullanıcının ana havuzundaki kelimeler (kendi + saved_by)."""
    return Word.objects.filter(Q(owner=user) | Q(saved_by=user)).distinct()


def _redirect_back_to_words(request, list_id=None):
    """POST sonrası kelimeler sayfasına dön; mümkünse aynı listeye."""
    base = redirect("profile_words").url
    params = []
    target = list_id if list_id is not None else request.POST.get("current_list_id", "")
    if target and target != "__all__":
        params.append(f"list_id={target}")
    q = request.POST.get("q", "")
    if q:
        from urllib.parse import quote
        params.append(f"q={quote(q)}")
    suffix = ("?" + "&".join(params)) if params else ""
    return redirect(f"{base}{suffix}")


VALID_COLORS = {c[0] for c in WordList.COLOR_CHOICES}


@login_required
@require_POST
def createWordList(request):
    name = (request.POST.get("name") or "").strip()
    color = (request.POST.get("color") or "indigo").strip()

    if not name:
        messages.error(request, "Liste adı boş olamaz.")
        return _redirect_back_to_words(request)
    if len(name) > 80:
        messages.error(request, "Liste adı en fazla 80 karakter olabilir.")
        return _redirect_back_to_words(request)
    if color not in VALID_COLORS:
        color = "indigo"

    if WordList.objects.filter(owner=request.user, name__iexact=name).exists():
        messages.error(request, f"\"{name}\" adında bir listeniz zaten var.")
        return _redirect_back_to_words(request)

    wl = WordList.objects.create(owner=request.user, name=name, color=color)
    messages.success(request, f"\"{wl.name}\" listesi oluşturuldu.")
    return _redirect_back_to_words(request, list_id=wl.id)


@login_required
@require_POST
def renameWordList(request, list_id):
    wl = get_object_or_404(WordList, id=list_id, owner=request.user)
    new_name = (request.POST.get("name") or "").strip()
    new_color = (request.POST.get("color") or wl.color).strip()

    if not new_name:
        messages.error(request, "Liste adı boş olamaz.")
        return _redirect_back_to_words(request, list_id=wl.id)

    if new_name != wl.name and WordList.objects.filter(owner=request.user, name__iexact=new_name).exists():
        messages.error(request, f"\"{new_name}\" adında bir listeniz zaten var.")
        return _redirect_back_to_words(request, list_id=wl.id)

    wl.name = new_name
    if new_color in VALID_COLORS:
        wl.color = new_color
    wl.save()
    messages.success(request, "Liste güncellendi.")
    return _redirect_back_to_words(request, list_id=wl.id)


@login_required
@require_POST
def deleteWordList(request, list_id):
    wl = get_object_or_404(WordList, id=list_id, owner=request.user)
    name = wl.name
    wl.delete()  # Liste siler ama kelimeler kalır (sadece M2M ilişkisi gider)
    messages.success(request, f"\"{name}\" listesi silindi. (Kelimeleriniz silinmedi.)")
    return _redirect_back_to_words(request)


def _parse_word_ids(request):
    raw = request.POST.getlist("word_ids")
    ids = []
    for v in raw:
        try:
            ids.append(int(v))
        except (TypeError, ValueError):
            continue
    return ids


@login_required
@require_POST
def addWordsToList(request, list_id):
    """Verilen kelimeleri (kullanıcının görme yetkisi olanları) listeye ekler."""
    wl = get_object_or_404(WordList, id=list_id, owner=request.user)
    ids = _parse_word_ids(request)
    if not ids:
        messages.info(request, "Kelime seçmediniz.")
        return _redirect_back_to_words(request)

    # Sadece kullanıcının havuzundaki kelimeler
    valid_words = list(_user_words_qs(request.user).filter(id__in=ids))
    if not valid_words:
        messages.error(request, "Geçerli kelime bulunamadı.")
        return _redirect_back_to_words(request)

    existing = set(wl.words.filter(id__in=[w.id for w in valid_words]).values_list("id", flat=True))
    new_words = [w for w in valid_words if w.id not in existing]
    if new_words:
        wl.words.add(*new_words)

    if new_words:
        msg = f"{len(new_words)} kelime \"{wl.name}\" listesine eklendi."
        if existing:
            msg += f" {len(existing)} tanesi zaten listedeymiş."
        messages.success(request, msg)
    else:
        messages.info(request, f"Seçilen kelimeler zaten \"{wl.name}\" listesindeymiş.")
    return _redirect_back_to_words(request, list_id=wl.id)


@login_required
@require_POST
def removeWordsFromList(request, list_id):
    """Verilen kelimeleri listeden çıkarır (kelimeler ana listede kalır)."""
    wl = get_object_or_404(WordList, id=list_id, owner=request.user)
    ids = _parse_word_ids(request)
    if not ids:
        messages.info(request, "Kelime seçmediniz.")
        return _redirect_back_to_words(request, list_id=wl.id)

    removed = wl.words.filter(id__in=ids)
    count = removed.count()
    if count:
        wl.words.remove(*removed)
        messages.success(request, f"{count} kelime \"{wl.name}\" listesinden çıkarıldı.")
    else:
        messages.info(request, "Seçilen kelimeler bu listede değil.")
    return _redirect_back_to_words(request, list_id=wl.id)


@login_required
@require_POST
def moveWordsBetweenLists(request):
    """
    Kelimeleri bir listeden diğerine taşı veya kopyala.
    POST: from_list_id (opsiyonel, "__all__" veya boş ise sadece hedefe ekler),
          to_list_id (zorunlu),
          word_ids (çoklu),
          mode = "move" | "copy"  (varsayılan: copy)
    """
    to_list_id = request.POST.get("to_list_id")
    if not to_list_id:
        messages.error(request, "Hedef liste seçmediniz.")
        return _redirect_back_to_words(request)

    try:
        to_list = WordList.objects.get(id=int(to_list_id), owner=request.user)
    except (ValueError, WordList.DoesNotExist):
        messages.error(request, "Geçersiz hedef liste.")
        return _redirect_back_to_words(request)

    ids = _parse_word_ids(request)
    if not ids:
        messages.info(request, "Kelime seçmediniz.")
        return _redirect_back_to_words(request)

    valid_words = list(_user_words_qs(request.user).filter(id__in=ids))
    if not valid_words:
        messages.error(request, "Geçerli kelime bulunamadı.")
        return _redirect_back_to_words(request)

    mode = request.POST.get("mode", "copy")
    from_list_id = request.POST.get("from_list_id", "")

    # Hedefe ekle (yoksa)
    to_list.words.add(*valid_words)

    removed_count = 0
    if mode == "move" and from_list_id and from_list_id != "__all__":
        try:
            from_list = WordList.objects.get(id=int(from_list_id), owner=request.user)
            if from_list.id != to_list.id:
                from_list.words.remove(*valid_words)
                removed_count = len(valid_words)
        except (ValueError, WordList.DoesNotExist):
            pass

    if mode == "move" and removed_count:
        messages.success(request, f"{len(valid_words)} kelime \"{to_list.name}\" listesine taşındı.")
    else:
        messages.success(request, f"{len(valid_words)} kelime \"{to_list.name}\" listesine eklendi.")

    return _redirect_back_to_words(request, list_id=to_list.id)

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

        # Eş anlamlı ve zıt anlamlı kelimeler (birden fazla input, virgülle birleştirilir)
        synonyms_list = [s.strip() for s in request.POST.getlist('synonym') if s.strip()]
        antonyms_list = [a.strip() for a in request.POST.getlist('antonym') if a.strip()]
        synonyms = ', '.join(synonyms_list) if synonyms_list else None
        antonyms = ', '.join(antonyms_list) if antonyms_list else None

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
            wordLevel = level,               # Modelinizde 'level' alanı olmalı
            synonyms = synonyms,             # Eş anlamlılar (virgülle ayrılmış)
            antonyms = antonyms,             # Zıt anlamlılar (virgülle ayrılmış)
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
        word.wordLevel = request.POST.get('level')

        # Eş anlamlı ve zıt anlamlı kelimeler
        synonyms_list = [s.strip() for s in request.POST.getlist('synonym') if s.strip()]
        antonyms_list = [a.strip() for a in request.POST.getlist('antonym') if a.strip()]
        word.synonyms = ', '.join(synonyms_list) if synonyms_list else None
        word.antonyms = ', '.join(antonyms_list) if antonyms_list else None

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

        if not value:
            messages.error(request, "Lütfen bir liste seçin.")
            return redirect("profile_words")
        
        values = value.split(":")
        level = values[0]
        span = values[1]

        if span == "all":
            allWordsAddDelete(request.user, True, level)
        else:
            wordsAddDelete(request.user, True, level, span)
                
        messages.success(request, "Seçtiğiniz bütün kelimeler listenizden silindi.")
        return redirect("profile_words")
        
    messages.error(request, "Teknik bir hatadan dolayı bu işlem şu anda yapılamıyor.")
    return redirect("profile_words")
    
    
@login_required
@require_POST
def deleteSelectedWords(request):
    """
    Galeri tarzı manuel seçim ile gelen kelimeleri toplu siler.
    Form içinde 'word_ids' adıyla birden fazla hidden input gönderilir.

    Silme mantığı tek tek silmeyle aynıdır:
      - Kullanıcı kelimenin sahibiyse  -> kelime tamamen silinir.
      - Kullanıcı sahibi değilse veya base word ise -> sadece UserWordLink silinir.
    """
    word_ids = request.POST.getlist("word_ids")

    if not word_ids:
        messages.error(request, "Silinecek kelime seçilmedi.")
        return redirect("profile_words")

    # ID'leri temizle ve int'e çevir (güvenlik için)
    try:
        word_ids = [int(wid) for wid in word_ids if str(wid).isdigit()]
    except (TypeError, ValueError):
        messages.error(request, "Geçersiz seçim.")
        return redirect("profile_words")

    if not word_ids:
        messages.error(request, "Geçersiz seçim.")
        return redirect("profile_words")

    # Kullanıcının erişebileceği (kendi eklediği veya kaydettiği) kelimeler
    accessible_words = Word.objects.filter(
        Q(owner=request.user) | Q(saved_by=request.user),
        id__in=word_ids,
    ).distinct()

    deleted_owned = 0   # tamamen silinen (sahibi olduğu) kelime sayısı
    removed_link = 0    # sadece listesinden çıkardığı kelime sayısı
    skipped = 0         # işlem yapılamayan kelime sayısı

    for word in accessible_words:
        if word.owner == request.user and word.isBaseWord == False:
            # Kullanıcının kendi eklediği kelime -> tamamen sil
            word.delete()
            deleted_owned += 1
        elif word.isBaseWord or word.owner != request.user:
            # Base word veya başkasının kelimesi -> sadece bağlantıyı kaldır
            UserWordLink.objects.filter(user=request.user, word=word).delete()
            removed_link += 1
        else:
            skipped += 1

    total_processed = deleted_owned + removed_link

    if total_processed == 0:
        messages.error(request, "Seçilen kelimeler üzerinde işlem yapılamadı.")
    else:
        parts = []
        if deleted_owned:
            parts.append(f"{deleted_owned} kelime tamamen silindi")
        if removed_link:
            parts.append(f"{removed_link} kelime listenizden çıkarıldı")
        message = "Toplu silme tamamlandı: " + ", ".join(parts) + "."
        if skipped:
            message += f" ({skipped} kelime üzerinde işlem yapılamadı.)"
        messages.success(request, message)

    return redirect("profile_words")
