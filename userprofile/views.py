import re

from django.shortcuts import render,redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from LearnVocab.authgate import login_gate
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from words.models import (
    CEFR_CHOICES, CEFR_LEVELS, Meaning, PartOfSpeech, Register, Sentiment, UserWordLink,
    Word, WordList,
)
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
from quizzes.models import ReviewLog
from words.addWeeks.addWeeks import allWordsAddDelete

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
    "az": ("A - Z", ("text", "id")),
    "za": ("Z - A", ("-text", "-id")),
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
            Q(text__icontains=search_query) |
            Q(meanings__meaning_tr__icontains=search_query)
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
    # Aile, anlam ve örnek cümleler tek seferde: liste her satır için
    # ayrı sorgu atmasın.
    words = words.select_related("family").prefetch_related("meanings")

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
        # Kelime kartındaki ekle/çıkar düğmesi bu kümeye bakıyor. Burada
        # verilmezse kullanıcının kendi listesindeki kelimeler "listende yok"
        # gibi görünüyordu.
        "saved_ids": set(
            UserWordLink.objects.filter(user=user).values_list("word_id", flat=True)
        ),
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
# Boyut grafiğinin renkleri. Eskiden beş SORU TİPİ vardı (eşleştirme,
# çoktan seçmeli, yazma, eş/zıt, boşluk); artık ölçülen şey soru tipi
# değil ÖĞRENME BOYUTU — "hangi biçimde soruldu" değil "neyi biliyor".
# Bir öğrencinin çoktan seçmelide iyi, yazmada kötü olması bir bilgi
# değil; tanımada iyi, üretimde kötü olması bilgidir.
ASPECT_CHART_COLORS = {
    "recognize": "#7c3aed",
    "produce": "#f59e0b",
    "context": "#ec4899",
    "collocation": "#06b6d4",
    "pattern": "#10b981",
    "false_friend": "#ef4444",
    "confusable": "#8b5cf6",
    "nuance": "#14b8a6",
    "family": "#f97316",
    "form": "#64748b",
}


def aspect_chart_data(user):
    """
    Boyut boyut doğru/yanlış sayıları.

    Kaynak ReviewLog: her cevap orada duruyor, kart silinse bile.
    """
    from quizzes.aspects import Aspect

    ham = (ReviewLog.objects.filter(user=user)
           .values("aspect")
           .annotate(correct=Count("id", filter=Q(is_correct=True)),
                     wrong=Count("id", filter=Q(is_correct=False))))
    sozluk = {satir["aspect"]: satir for satir in ham}

    satirlar = []
    for kod in Aspect.values:
        veri = sozluk.get(kod, {})
        dogru = veri.get("correct") or 0
        yanlis = veri.get("wrong") or 0
        toplam = dogru + yanlis
        if not toplam:
            continue
        satirlar.append({
            "key": kod,
            "label": Aspect(kod).label,
            "color": ASPECT_CHART_COLORS.get(kod, "#64748b"),
            "correct": dogru,
            "wrong": yanlis,
            "total": toplam,
            "correct_pct": round(dogru * 100 / toplam) if toplam else 0,
            "wrong_pct": round(yanlis * 100 / toplam) if toplam else 0,
        })
    return satirlar


# Eski ad — şablonlar ve testler kırılmasın diye duruyor.
quiz_type_chart_data = aspect_chart_data


@login_gate("Egzersizler", "Egzersizler kendi kelimelerinden üretildiği için giriş yapman gerekiyor.")
def showQuizzesView(request):
    from django.conf import settings as django_settings

    if not getattr(django_settings, "QUIZZES_ENABLED", True):
        return render(request, "pages/quizzes/quizzesDisabled.html",
                      {"active_page": "Çalışma", "exercise_tab": "quizzes"})

    tipler = aspect_chart_data(request.user)

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
        wordEn = word.text
        word.delete()
        messages.success(request, f"{wordEn} kelimesi siteden başarıyla silindi.")
    
    elif word.owner != request.user and word.isBaseWord == False:
        wordEn = word.text
        UserWordLink.objects.filter(user=request.user, word=word).delete()

        messages.success(request, f"{wordEn} kelimesi listenizden başarıyla silindi.")

    elif word.isBaseWord == True:
        wordEn = word.text
        UserWordLink.objects.filter(user=request.user, word=word).delete()

        messages.success(request, f"{wordEn} kelimesi listenizden başarıyla silindi.")
    else:
        # Belki de kelimenin sahibi değiliz veya base word değil?
        # Bu duruma da bir mesaj eklemek iyi olabilir.
        messages.error(request, "Bu işlemi yapma yetkiniz yok.")

    return redirect("profile_words")

@login_required
def addWord(request):
    """
    Elle kelime ekleme.

    Yeni modelde bir kelime tek başına yaşamaz: mutlaka bir aileye girer.
    Kullanıcı aile kökü yazmazsa kelimenin kendisi kök olur (tek kişilik
    aile) — ileride aynı kökten başka bir türev geldiğinde yanına eklenir.
    """
    if request.method != "POST":
        return render(request, "pages/words/addWord.html", {
            "active_page": "Yeni Kelime",
            "pos_choices": PartOfSpeech.choices,
            "level_choices": CEFR_CHOICES,
            "sentiment_choices": Sentiment.choices,
            "register_choices": Register.choices,
            "sentence_range": range(1, Meaning.EXAMPLE_SENTENCE_COUNT + 1),
            "slots": _bos_yuvalar(),
        })

    sonuc = _kelime_kaydet(request, kelime=None)
    if sonuc is None:
        return render(request, "pages/words/addWord.html", {
            "active_page": "Yeni Kelime",
            "pos_choices": PartOfSpeech.choices,
            "level_choices": CEFR_CHOICES,
            "sentiment_choices": Sentiment.choices,
            "register_choices": Register.choices,
            "sentence_range": range(1, Meaning.EXAMPLE_SENTENCE_COUNT + 1),
            "slots": _bos_yuvalar(),
            "form": request.POST,
        })
    return redirect("word_detail", id=sonuc.id)


@login_required
def editWord(request, id):
    """
    Kelime düzenleme — yalnızca KENDİ eklediğin kelimeler için.

    Ortak sözlükteki bir kelimeyi listesine ekleyen kişi onu düzenleyemez:
    çekirdek herkesindir, bir kişinin değiştirmesi herkesin sayfasını
    değiştirir. O kullanıcının yapabileceği şey kendi katmanına yazmak —
    kendi anlamı, kendi notu. Kelime sayfasına o bölüme yönlendiriliyor.
    """
    word = get_object_or_404(
        Word.objects.select_related("family").prefetch_related("meanings__examples"),
        id=id,
    )

    if not word.is_editable_by(request.user):
        messages.info(
            request,
            "Bu kelime ortak sözlüğe ait, alanları değiştirilemez. "
            "Kendi anlamını ve notunu aşağıdan ekleyebilirsin — sadece sen görürsün.",
        )
        return redirect(reverse("word_detail", kwargs={"id": word.id}) + "#kisisel")

    if request.method == "POST":
        sonuc = _kelime_kaydet(request, kelime=word)
        if sonuc is not None:
            return redirect("word_detail", id=sonuc.id)

    anlamlar = list(
        word.meanings.prefetch_related("examples", "collocations", "patterns", "categories")
    )
    return render(request, "pages/words/editWord.html", {
        "active_page": "Kelimeyi Düzenle",
        "word": word,
        "meanings": anlamlar,
        "slots": _dolu_yuvalar(anlamlar),
        "false_friends": "\n".join(
            " / ".join(p for p in (y.turkish_lookalike, y.assumed_meaning, y.correct_english) if p)
            for y in word.false_friends.all()
        ),
        "pos_choices": PartOfSpeech.choices,
        "level_choices": CEFR_CHOICES,
        "sentiment_choices": Sentiment.choices,
        "register_choices": Register.choices,
        "sentence_range": range(1, Meaning.EXAMPLE_SENTENCE_COUNT + 1),
        "my_note": word.note_of(request.user),
        # Kelimeyi başkaları da listesine almışsa değişiklik onlarda da görünür;
        # kullanıcı bunu bilerek kaydetsin.
        "shared_with": word.saved_by_others_count(request.user),
    })


# Form iki anlam yuvası gösteriyor. Üçüncüsü gerekirse tek yer burası.
MEANING_SLOTS = (1, 2)


def _bos_yuvalar():
    """Yeni kelime formu için boş anlam yuvaları."""
    return [{"index": i, "meaning": None, "sentences": [],
             "collocations": "", "patterns": "", "categories": ""}
            for i in MEANING_SLOTS]


def _dolu_yuvalar(anlamlar):
    """
    Düzenleme formu için yuvaları mevcut anlamlarla doldurur.

    Çok satırlı alanlar "yapı / açıklama" biçiminde düzleştiriliyor: form
    tarafında her collocation için ayrı input açmak yerine tek bir metin
    kutusu var, ayrıştırmayı `_satirlari_coz` yapıyor.
    """
    yuvalar = []
    for i in MEANING_SLOTS:
        anlam = anlamlar[i - 1] if len(anlamlar) >= i else None
        if anlam is None:
            yuvalar.append({"index": i, "meaning": None, "sentences": [],
                            "collocations": "", "patterns": "", "categories": ""})
            continue
        yuvalar.append({
            "index": i,
            "meaning": anlam,
            "sentences": [c.text for c in anlam.examples.all()],
            "collocations": "\n".join(
                " / ".join(p for p in (c.pattern, c.meaning_tr) if p)
                for c in anlam.collocations.all()
            ),
            "patterns": "\n".join(
                " / ".join(p for p in (k.pattern, k.note) if p)
                for k in anlam.patterns.all()
            ),
            "categories": ", ".join(k.name for k in anlam.categories.all()),
        })
    return yuvalar


def _secim(deger, secenekler, varsayilan):
    """Formdan gelen değer geçerli bir seçenek değilse varsayılana düşer."""
    deger = (deger or "").strip()
    return deger if deger in secenekler.values else varsayilan


def _kategori_coz(ham_metin):
    """Virgülle ayrılmış alan adlarını Category kayıtlarına çevirir."""
    from django.utils.text import slugify
    from words.models import Category

    kategoriler = []
    for ad in [p.strip() for p in (ham_metin or "").split(",") if p.strip()]:
        slug = (slugify(ad) or ad.lower())[:80]
        kategori, _ = Category.objects.get_or_create(slug=slug,
                                                     defaults={"name": ad[:80]})
        kategoriler.append(kategori)
    return kategoriler


# Alan ayırıcısı: iki yanı da BOŞLUKLU slash.
#
# Düz "/" olamaz, çünkü yapının kendisinde slash geçebiliyor:
# "sympathetic to/towards sb", "harmful to sb/sth". Bitişik slash yapının
# parçası, boşluklu slash ayırıcı — bu ayrım olmasa o kalıplar ikiye bölünürdü.
# "|" de tercih edilmedi: telefon klavyesinde kolay bulunmuyor.
ALAN_AYIRICI = re.compile(r"\s+/\s+")


def _satirlari_coz(ham_metin, alan_sayisi, tekil_alan=0):
    """
    Çok satırlı alanı " / " ile bölünmüş demetlere çevirir.

        make a decision / karar vermek  ->  ["make a decision", "karar vermek"]
        harmful to sb/sth               ->  ["harmful to sb/sth", ""]

    Boş satırlar atılır; `tekil_alan` sütununda tekrar eden satırlar da atılır
    (ilgili tablolarda o sütun üzerinde tekillik kısıtı var, aksi hâlde kayıt
    bütün formu düşürürdü).
    """
    satirlar, gorulen = [], set()
    for satir in (ham_metin or "").splitlines():
        satir = satir.strip()
        if not satir:
            continue
        parcalar = [p.strip() for p in ALAN_AYIRICI.split(satir)]
        parcalar += [""] * (alan_sayisi - len(parcalar))
        parcalar = parcalar[:alan_sayisi]
        if not parcalar[tekil_alan]:
            continue
        anahtar = parcalar[tekil_alan].lower()
        if anahtar in gorulen:
            continue
        gorulen.add(anahtar)
        satirlar.append(parcalar)
    return satirlar


def _bag_kur(kelime, ham_metin, tur):
    """
    Virgülle ayrılmış kelime adlarını gerçek bağlara çevirir.

    Bağ iki KAYIT arasındadır; sözlükte olmayan bir kelimeye bağ kurulamaz.
    Bulunamayanlar sessizce atılmaz, çağırana döndürülür.
    """
    from words.models import WordRelation

    WordRelation.objects.filter(from_word=kelime, type=tur).delete()
    bulunamayan = []

    for ad in [p.strip() for p in (ham_metin or "").split(",") if p.strip()]:
        hedef = Word.objects.filter(text__iexact=ad).exclude(id=kelime.id).first()
        if hedef is None:
            bulunamayan.append(ad)
            continue
        WordRelation.objects.get_or_create(
            from_word=kelime, to_word=hedef, type=tur, defaults={"note": None},
        )
    return bulunamayan


def _anlam_yaz(kelime, request, index, sira):
    """
    Bir anlam yuvasını yazar: anlam + açıklama + ton + üslup + alanlar +
    cümleler + collocation'lar + kalıplar.

    Bunların hepsi anlama bağlı, kelimeye değil: `bank`ın "banka" anlamıyla
    "nehir kıyısı" anlamı aynı collocation'ı paylaşmaz.
    """
    from words.models import Collocation, ExampleSentence, UsagePattern

    metin = (request.POST.get(f"meaning_{index}") or "").strip()
    if not metin:
        return None

    anlam = Meaning.objects.create(
        word=kelime,
        meaning_tr=metin,
        definition=(request.POST.get(f"definition_{index}") or "").strip() or None,
        sentiment=_secim(request.POST.get(f"sentiment_{index}"), Sentiment, Sentiment.NEUTRAL),
        register=_secim(request.POST.get(f"register_{index}"), Register, Register.NEUTRAL),
        sort_order=sira,
    )

    anlam.categories.set(_kategori_coz(request.POST.get(f"categories_{index}")))

    cumleler = []
    for k in range(1, Meaning.EXAMPLE_SENTENCE_COUNT + 1):
        cumle = (request.POST.get(f"sentence_{index}_{k}") or "").strip()
        if cumle:
            cumleler.append(ExampleSentence(meaning=anlam, text=cumle,
                                            source="manual", sort_order=len(cumleler)))
    ExampleSentence.objects.bulk_create(cumleler)

    Collocation.objects.bulk_create([
        Collocation(meaning=anlam, pattern=yapi, meaning_tr=tr or None, sort_order=k)
        for k, (yapi, tr) in enumerate(
            _satirlari_coz(request.POST.get(f"collocations_{index}"), 2))
    ])

    UsagePattern.objects.bulk_create([
        UsagePattern(meaning=anlam, pattern=kalip, note=notu or None, sort_order=k)
        for k, (kalip, notu) in enumerate(
            _satirlari_coz(request.POST.get(f"patterns_{index}"), 2))
    ])

    return anlam


def _kelime_kaydet(request, kelime=None):
    """
    Formdan gelen veriyi yeni modele yazar. Hata varsa mesaj bırakıp None döner.
    Ekleme ve düzenleme aynı kodu kullanıyor: alanlar birebir aynı.
    """
    from words.models import FalseFriend, UserWordNote, WordFamily
    from words import inflect

    metin = (request.POST.get("text") or "").strip()
    tur = (request.POST.get("pos") or "").strip()
    anlam1 = (request.POST.get("meaning_1") or "").strip()

    if not metin or not anlam1:
        messages.error(request, "Kelime ve en az bir anlam zorunlu.")
        return None
    if tur not in PartOfSpeech.values:
        messages.error(request, "Geçerli bir tür seçmelisin.")
        return None

    cakisan = Word.objects.filter(text__iexact=metin, pos=tur)
    if kelime is not None:
        cakisan = cakisan.exclude(id=kelime.id)
    if cakisan.exists():
        messages.error(request, f"“{metin}” zaten bu türde kayıtlı.")
        return None

    # --- Aile ---
    kok = (request.POST.get("family_root") or "").strip() or metin
    aile, _ = WordFamily.objects.get_or_create(root=kok.lower())

    alanlar = {
        "family": aile,
        "text": metin,
        "pos": tur,
        "cefr": request.POST.get("level") or "Belirtilmemiş",
        "visibility": request.POST.get("visibility") or "private",
        "v2Form": (request.POST.get("v2") or "").strip() or None,
        "v3Form": (request.POST.get("v3") or "").strip() or None,
    }

    if kelime is None:
        kelime = Word.objects.create(owner=request.user, isBaseWord=False, **alanlar)
    else:
        for ad, deger in alanlar.items():
            setattr(kelime, ad, deger)
        kelime.save()

    # --- Anlamlar (cümleler, collocation'lar ve kalıplar onlara bağlı) ---
    kelime.meanings.all().delete()
    sira = 0
    for index in MEANING_SLOTS:
        if _anlam_yaz(kelime, request, index, sira) is not None:
            sira += 1

    # --- Yanlış dostlar (kelimenin bütününe ait) ---
    kelime.false_friends.all().delete()
    FalseFriend.objects.bulk_create([
        FalseFriend(word=kelime, turkish_lookalike=benzer,
                    assumed_meaning=sanilan or None, correct_english=dogru or None)
        for benzer, sanilan, dogru in _satirlari_coz(request.POST.get("false_friends"), 3)
    ])

    # --- Çekim biçimleri ---
    inflect.rebuild_forms(kelime)

    # --- Bağlar ---
    bulunamayan = []
    bulunamayan += _bag_kur(kelime, request.POST.get("synonyms"), "synonym")
    bulunamayan += _bag_kur(kelime, request.POST.get("antonyms"), "antonym")
    bulunamayan += _bag_kur(kelime, request.POST.get("simpler"), "simpler")
    bulunamayan += _bag_kur(kelime, request.POST.get("confused_with"), "confused_with")

    # --- Kişisel not (çekirdeğe değil, kullanıcı katmanına) ---
    not_metni = (request.POST.get("note") or "").strip()
    if not_metni:
        UserWordNote.objects.update_or_create(
            user=request.user, word=kelime, defaults={"note": not_metni},
        )
    else:
        UserWordNote.objects.filter(user=request.user, word=kelime).delete()

    # Kendi eklediği kelime listesine de girsin
    UserWordLink.objects.get_or_create(user=request.user, word=kelime)

    messages.success(request, f"“{kelime.text}” kaydedildi.")
    if bulunamayan:
        messages.warning(request, "Sözlükte bulunmadığı için bağlanmayan kelimeler: "
                                  + ", ".join(bulunamayan))
    return kelime


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
        level = (request.POST.get("bulk_level") or "").strip()

        if level not in CEFR_LEVELS:
            messages.error(request, "Lütfen bir seviye seçin.")
            return redirect("profile_words")

        allWordsAddDelete(request.user, True, level)

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
