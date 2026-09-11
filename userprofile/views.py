from django.shortcuts import render,redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from LearnVocab.authgate import login_gate
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from words.models import Word, UserWordLink, WordList
from users.models import User
from texts.models import Text
from texts import limits as text_limits
from django.contrib import messages
from usersettings.models import UserSettings

from django.utils import timezone
from datetime import timedelta
from LearnVocab import pagination
from django.db.models import Sum, Count, Q, Max
from django.db.models.functions import Coalesce
from quizzes.models import (
    MultipleChoiceQuestion, WritingQuestion, MatchingQuestion,
    SynonymAntonymQuestion, FillInTheBlankQuestion,
)
from words.addWeeks.addWeeks import wordsAddDelete, allWordsAddDelete

# Create your views here.

# "Profilim" sayfasındaki günlük hedef seçenekleri.
# Değerler int: şablon `settings.dailyGoal == deger` karşılaştırmasını
# bunun üzerinden yapıyor.
DAILY_GOAL_OPTIONS = (
    (0, "Yok"),
    (5, "5"),
    (10, "10"),
    (15, "15"),
    (20, "20"),
)


#Ana profil sayfasının görünümü 
@login_gate("Profilim")
def showProfile(request):
    """
    "Profilim" sayfası.

    Eskiden üç ayrı sayfa vardı: profil özeti, "Hesap Bilgilerim" ve "Ayarlar".
    Üçü de aynı şeyin parçasıydı, kullanıcıyı sekmeler arasında gezdiriyordu;
    tek sayfada birleştirildi. Hesap bilgisi formu da buraya POST ediyor.
    """
    if request.method == "POST":
        user = request.user
        user.email = request.POST.get("email") or user.email
        user.first_name = request.POST.get("first_name") or ""
        user.last_name = request.POST.get("last_name") or ""

        # Resim seçilmeden kaydedilirse eski resim silinmesin
        profile_pic_file = request.FILES.get("profile_pic")
        if profile_pic_file:
            user.profile_pic = profile_pic_file

        user.save()
        messages.success(request, "Hesap bilgileriniz başarıyla güncellendi.")
        return redirect("user_profile")

    context = {
        "active_page": "Profilim",
        "settings": UserSettings.objects.filter(user=request.user).first(),
        "daily_goal_options": DAILY_GOAL_OPTIONS,
        "export_links": [
            {"url": reverse("export_all"), "label": "Tüm verilerim"},
            {"url": reverse("export_mywords"), "label": "Kelimelerim"},
            {"url": reverse("export_myquizzes"), "label": "Egzersizlerim"},
            {"url": reverse("export_mytexts"), "label": "Metinlerim"},
        ],
    }

    return render(request, "pages/profile/myprofile.html", context)

# Kelimelerim sayfasının sıralama seçenekleri.
# Anahtar -> (etikette görünen ad, order_by alanları)
# Sıralama alanlarının sonunda her zaman "id" var: aynı değere sahip kayıtlar
# sayfadan sayfaya yer değiştirmesin, yani sayfalama kararlı olsun.
WORD_SORT_OPTIONS = {
    "new": ("Önce en yeni", ("-added_at", "-id")),
    "old": ("Önce en eski", ("added_at", "id")),
    "az": ("A - Z", ("englishWord", "id")),
    "za": ("Z - A", ("-englishWord", "-id")),
}
DEFAULT_WORD_SORT = "new"

# Kelimelerim sayfasında sayfa başına adet seçenekleri
MY_WORDS_PER_PAGE_OPTIONS = (15, 30, 60, 120)
MY_WORDS_DEFAULT_PER_PAGE = 30


#Profilde "Kelimelerim" görünümü
@login_gate("Kelimelerim", "Kendi kelime listelerini oluşturmak ve kelime eklemek için bir hesaba ihtiyacın var.")
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

    # ---- Sıralama ----
    # "Eklenme tarihi" kelimenin oluşturulma tarihi değil, KULLANICININ onu
    # listesine eklediği tarih (UserWordLink.dateAdded). Aynı kelime birden
    # çok kullanıcıda olabildiği için bu bilgi Word üzerinde durmuyor.
    # Kullanıcının kendi eklediği ama bağlantısı olmayan bir kelime kalırsa
    # kelimenin oluşturulma tarihine düşülüyor.
    words = words.annotate(
        added_at=Coalesce(
            Max("userLinks__dateAdded", filter=Q(userLinks__user=user)),
            "createdAt",
        )
    )

    sort_key = request.GET.get("sort", "").strip()
    if sort_key not in WORD_SORT_OPTIONS:
        sort_key = DEFAULT_WORD_SORT

    words = words.order_by(*WORD_SORT_OPTIONS[sort_key][1])

    # ---- Sayfalama ----
    per_page = pagination.resolve_per_page(
        request, MY_WORDS_PER_PAGE_OPTIONS, MY_WORDS_DEFAULT_PER_PAGE
    )
    paginator = Paginator(words, per_page)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)



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

    context = {
        "active_page": "Kelimelerim",
        "words": page_obj.object_list,           # Geriye dönük uyumluluk
        "search_query": search_query,
        "user_lists": lists_with_counts,
        "selected_list": selected_list,
        "selected_list_id": selected_list_id or "__all__",
        "total_word_count": base_words.count(),
        "movable_targets": movable_targets,
        "sort_key": sort_key,
        "sort_options": [
            {"key": key, "label": label} for key, (label, _fields) in WORD_SORT_OPTIONS.items()
        ],
    }

    # Sayfalama arayüzü "Tüm Kelimeler" sayfasıyla ortak (base/_pagination.html)
    context.update(pagination.pagination_context(
        page_obj, paginator,
        params=[
            ("q", search_query),
            ("list_id", selected_list.id if selected_list else ""),
            ("sort", sort_key if sort_key != DEFAULT_WORD_SORT else ""),
        ],
        per_page=per_page,
        per_page_options=MY_WORDS_PER_PAGE_OPTIONS,
        default_per_page=MY_WORDS_DEFAULT_PER_PAGE,
    ))

    return render(request, "pages/profile/words.html", context)


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
    """
    Eski "Hesap Bilgilerim" adresi. İçeriği artık Profilim sayfasında.

    GET yönlendiriyor; POST'u ise Profilim'in kendi işleyicisine devrediyor.
    Yönlendirme POST gövdesini taşımadığı için, bu adrese gönderilen bir
    hesap formu aksi hâlde hiçbir şey kaydetmeden "başarılı" görünürdü.
    """
    if request.method == "POST":
        return showProfile(request)
    return redirect("user_profile")


# Grafikteki soru tipleri ve renkleri — TEK kaynak.
# Şablon hem birleşik grafiği hem mobildeki tip başına grafikleri hem de
# alttaki oran listesini bu listeden üretiyor; yeni bir soru tipi eklenince
# üç yeri birden elle güncellemek gerekmiyor.
#
# Renkler beş ayrı ton: mor, turuncu, pembe, camgöbeği, yeşil. Hepsi hem açık
# hem karanlık zeminde okunuyor.
QUIZ_TYPE_CHART = (
    ("mq", "Eşleştirme", "#7c3aed"),
    ("mc", "Çoktan Seçmeli", "#f59e0b"),
    ("wq", "Yazma", "#ec4899"),
    ("sa", "Eş / Zıt Anlam", "#06b6d4"),
    ("fb", "Boşluk Doldurma", "#10b981"),
)


def _question_stats(model, user):
    """Tek tek soru kayıtlarından doğru/yanlış sayısı."""
    sonuc = model.objects.filter(
        attempt__owner=user, attempt__isCompleted=True
    ).aggregate(
        correct=Count("id", filter=Q(is_correct=True)),
        wrong=Count("id", filter=Q(is_correct=False)),
    )
    return sonuc.get("correct") or 0, sonuc.get("wrong") or 0


def quiz_type_chart_data(user):
    """
    Beş soru tipinin doğru/yanlış sayıları ve doğruluk oranları.

    Eşleştirme diğerlerinden farklı: tek soru içinde birden çok eşleşme var,
    bu yüzden sayılar kayıt sayısından değil correct_matches/wrong_matches
    toplamından geliyor.
    """
    matching = MatchingQuestion.objects.filter(
        attempt__owner=user, attempt__isCompleted=True
    ).aggregate(correct=Sum("correct_matches"), wrong=Sum("wrong_matches"))

    ham = {
        "mq": (matching.get("correct") or 0, matching.get("wrong") or 0),
        "mc": _question_stats(MultipleChoiceQuestion, user),
        "wq": _question_stats(WritingQuestion, user),
        "sa": _question_stats(SynonymAntonymQuestion, user),
        "fb": _question_stats(FillInTheBlankQuestion, user),
    }

    satirlar = []
    for anahtar, etiket, renk in QUIZ_TYPE_CHART:
        dogru, yanlis = ham[anahtar]
        toplam = dogru + yanlis
        satirlar.append({
            "key": anahtar,
            "label": etiket,
            "color": renk,
            "correct": dogru,
            "wrong": yanlis,
            "total": toplam,
            # Oran deneme sayısıyla birlikte anlamlı: ikisi de şablona gidiyor
            "correct_pct": round(dogru * 100 / toplam) if toplam else 0,
            "wrong_pct": round(yanlis * 100 / toplam) if toplam else 0,
        })
    return satirlar


@login_gate("Egzersizler", "Egzersizler kendi kelimelerinden üretildiği için giriş yapman gerekiyor.")
def showQuizzesView(request):
    tipler = quiz_type_chart_data(request.user)

    context = {
        "active_page": "Egzersizler",
        "quiz_types": tipler,
        "has_quiz_data": any(tip["total"] for tip in tipler),
        "allUsers": User.objects.all(),
    }

    return render(request, "pages/profile/quizzes.html", context)


@login_gate("Metinler", "Yazdığın metinler hesabına kaydedildiği için giriş yapman gerekiyor.")
def showTextsView(request):
    
    texts = Text.objects.filter(owner = request.user).order_by("-createdAt")

    # Kısıt ve kalan süre tek kaynaktan geliyor (bkz. texts/limits.py).
    # Eskiden burada timedelta(days=1) tekrar yazılıydı ve kalan süre
    # "saat:dakika:saniye" varsayımıyla elle biçimlendiriliyordu; süre bir günü
    # aştığında ("1 day, 3:00:00") bu biçimlendirme bozuluyordu.
    can_write_new_text = text_limits.can_write_new_text(request.user)
    remaining_time = text_limits.remaining_label(request.user) or None

    allUsers = User.objects.all()

    context = {
        "mytexts":texts,
        "isWriteable":can_write_new_text,
        "remaining_time":remaining_time,
        "allUsers":allUsers,
        # Bilgilendirme kutusundaki süre metni de ayardan gelsin
        "text_interval_label": text_limits.interval_label(),
    }

    return render(request, "pages/profile/texts.html", context)

@login_required
def showSettingsView(request):
    """Eski "Ayarlar" adresi. İçeriği artık Profilim sayfasında."""
    return redirect("user_profile")


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
        
        # 10 örnek cümle alanı; boş gelenler None olarak kaydedilir.
        sentences = {}
        for i in range(1, Word.EXAMPLE_SENTENCE_COUNT + 1):
            value = (request.POST.get(f'sentence_{i}') or '').strip()
            sentences[f'exampleSentence{i}'] = value or None

        visibility = request.POST.get('visibility')
        level = request.POST.get('level')

        # Eş anlamlı ve zıt anlamlı kelimeler (birden fazla input, virgülle birleştirilir)
        synonyms_list = [s.strip() for s in request.POST.getlist('synonym') if s.strip()]
        antonyms_list = [a.strip() for a in request.POST.getlist('antonym') if a.strip()]
        collocations_list = [c.strip() for c in request.POST.getlist('collocation') if c.strip()]
        synonyms = ', '.join(synonyms_list) if synonyms_list else None
        antonyms = ', '.join(antonyms_list) if antonyms_list else None
        collocations = ', '.join(collocations_list) if collocations_list else None

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
            **sentences,                     # exampleSentence1..10 (Form-name: sentence_1..10)
            visibility = visibility,         # Model: visibility, Form-name: visibility
            wordLevel = level,               # Modelinizde 'level' alanı olmalı
            synonyms = synonyms,             # Eş anlamlılar (virgülle ayrılmış)
            antonyms = antonyms,             # Zıt anlamlılar (virgülle ayrılmış)
            collocations = collocations,     # Kullanım kalıpları (virgülle ayrılmış)
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

        for i in range(1, Word.EXAMPLE_SENTENCE_COUNT + 1):
            value = (request.POST.get(f'sentence_{i}') or '').strip()
            setattr(word, f'exampleSentence{i}', value or None)
        word.visibility = request.POST.get('visibility')
        word.wordLevel = request.POST.get('level')

        # Eş anlamlı ve zıt anlamlı kelimeler
        synonyms_list = [s.strip() for s in request.POST.getlist('synonym') if s.strip()]
        antonyms_list = [a.strip() for a in request.POST.getlist('antonym') if a.strip()]
        collocations_list = [c.strip() for c in request.POST.getlist('collocation') if c.strip()]
        word.synonyms = ', '.join(synonyms_list) if synonyms_list else None
        word.antonyms = ', '.join(antonyms_list) if antonyms_list else None
        word.collocations = ', '.join(collocations_list) if collocations_list else None

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
