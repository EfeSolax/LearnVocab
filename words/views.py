from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.urls import reverse

from .models import Word, UserWordLink
from .addWeeks.addWeeks import wordsAddDelete, allWordsAddDelete


# ---------------------------------------------------------------------------
# Görünürlük (visibility) yardımcıları
# ---------------------------------------------------------------------------

def visible_words_qs(user):
    """
    Bir kullanıcının görüntülemeye yetkili olduğu kelimelerin queryset'ini döner.
    - Anonim kullanıcı: sadece base (kur) kelimeleri ve public kelimeler.
    - Giriş yapmış kullanıcı: yukarıdakilere ek olarak kendi kelimeleri,
      kendi listesine eklediği kelimeler ve arkadaşlarının "friends" görünür kelimeleri.
    """
    base_qs = Word.objects.select_related("owner")

    if not user.is_authenticated:
        return base_qs.filter(Q(isBaseWord=True) | Q(visibility="public"))

    return base_qs.filter(
        Q(isBaseWord=True)
        | Q(owner=user)
        | Q(saved_by=user)
        | Q(visibility="public")
        | Q(visibility="friends", owner__friends=user)
    )


def can_view_word(word, user):
    """Tek bir Word objesi için görünürlük kontrolü."""
    if word.isBaseWord or word.visibility == "public":
        return True
    if not user.is_authenticated:
        return False
    if word.owner_id == user.id:
        return True
    if word.saved_by.filter(id=user.id).exists():
        return True
    if word.visibility == "friends" and word.owner and word.owner.friends.filter(id=user.id).exists():
        return True
    return False


# ---------------------------------------------------------------------------
# Kelime listesi yönetimi
# ---------------------------------------------------------------------------

def _redirect_with_anchor(word_id, request):
    """allWords sayfasına geri dön, kullanıcının kaldığı yere kaydır."""
    base_url = reverse("all_words")
    query_parameters = request.GET.urlencode()
    suffix = f"?{query_parameters}" if query_parameters else ""
    return redirect(f"{base_url}{suffix}#word-{word_id}")


@login_required
def add_to_my_list(request, word_id):
    word = get_object_or_404(Word, id=word_id)

    # Yetkisi olmadığı bir kelimeyi listesine eklemesini engelle
    if not can_view_word(word, request.user):
        messages.error(request, "Bu kelimeyi listenize ekleme yetkiniz yok.")
        return redirect("all_words")

    UserWordLink.objects.get_or_create(user=request.user, word=word)
    return _redirect_with_anchor(word.id, request)


@login_required
def remove_from_my_list(request, word_id):
    word = get_object_or_404(Word, id=word_id)
    UserWordLink.objects.filter(user=request.user, word=word).delete()
    return _redirect_with_anchor(word.id, request)


@login_required
def addSelectedToMyList(request):
    """
    "Tüm Kelimeler" sayfasında seçilen birden fazla kelimeyi tek seferde
    kullanıcının listesine ekler. Form 'word_ids' isimli birden fazla input
    gönderir (her checkbox).
    """
    if request.method != "POST":
        return redirect("all_words")

    raw_ids = request.POST.getlist("word_ids")
    if not raw_ids:
        messages.info(request, "Eklenecek bir kelime seçmediniz.")
        # Geri dönüşte mevcut filtre/sayfa parametrelerini koru
        return redirect(_back_to_all_words_url(request))

    # Sadece sayısal id'leri al
    ids = []
    for v in raw_ids:
        try:
            ids.append(int(v))
        except (TypeError, ValueError):
            continue

    if not ids:
        messages.error(request, "Geçersiz seçim.")
        return redirect(_back_to_all_words_url(request))

    # Sadece kullanıcının görme yetkisi olduğu kelimeleri al
    visible_qs = visible_words_qs(request.user).filter(id__in=ids).distinct()
    visible_ids = set(visible_qs.values_list("id", flat=True))

    if not visible_ids:
        messages.error(request, "Seçtiğiniz kelimelere erişim yetkiniz yok.")
        return redirect(_back_to_all_words_url(request))

    # Zaten listede olanları çıkar (raporlama için)
    existing_ids = set(
        UserWordLink.objects
        .filter(user=request.user, word_id__in=visible_ids)
        .values_list("word_id", flat=True)
    )
    new_ids = visible_ids - existing_ids

    # Toplu oluştur
    UserWordLink.objects.bulk_create(
        [UserWordLink(user=request.user, word_id=wid) for wid in new_ids],
        ignore_conflicts=True,
    )

    skipped_unauthorized = len(ids) - len(visible_ids)
    parts = []
    if new_ids:
        parts.append(f"{len(new_ids)} kelime listenize eklendi")
    if existing_ids:
        parts.append(f"{len(existing_ids)} kelime zaten listenizde olduğu için atlandı")
    if skipped_unauthorized:
        parts.append(f"{skipped_unauthorized} kelime erişim yetkiniz olmadığı için eklenmedi")

    if new_ids:
        messages.success(request, ". ".join(parts) + ".")
    else:
        messages.info(request, ". ".join(parts) + ".")

    return redirect(_back_to_all_words_url(request))


def _back_to_all_words_url(request):
    """
    POST sonrası all_words sayfasına dönerken hangi sayfa/filtre parametrelerinde
    olduğumuzu korumak için. Form içinde gizli alanlar olarak gönderilir.
    """
    base_url = reverse("all_words")
    keep_keys = ("q", "filter_by", "level", "page")
    qs_parts = []
    for key in keep_keys:
        val = request.POST.get(key)
        if val:
            qs_parts.append(f"{key}={val}")
    suffix = ("?" + "&".join(qs_parts)) if qs_parts else ""
    return f"{base_url}{suffix}"


# ---------------------------------------------------------------------------
# Tüm kelimeler sayfası
# ---------------------------------------------------------------------------

# Hangi alanın hangi filtreye karşılık geldiğinin haritası.
# Karmaşık if/elif yığınını ortadan kaldırır.
_FIELD_FILTERS = {
    "english": ["englishWord__icontains"],
    "meaning": ["meaningTr__icontains"],
    "explanation": ["explanation__icontains"],
    "author": ["owner__username__icontains"],
    "all": [
        "englishWord__icontains",
        "meaningTr__icontains",
        "explanation__icontains",
        "owner__username__icontains",
        "wordLevel__icontains",
        "v2Form__icontains",
        "v3Form__icontains",
    ],
}

_DEFAULT_QUERY_FIELDS = [
    "englishWord__icontains",
    "meaningTr__icontains",
    "explanation__icontains",
    "owner__username__icontains",
]


def _q_from_fields(query, fields):
    """Verilen field listesi için OR'lanmış bir Q objesi üretir."""
    q = Q()
    for f in fields:
        q |= Q(**{f: query})
    return q


def allWords(request):
    user = request.user

    # 1) Kullanıcının görme yetkisi olan kelimeler
    words = visible_words_qs(user)

    # 2) Filtreleri uygula
    query = (request.GET.get("q") or "").strip()
    filter_by = request.GET.get("filter_by")
    level = request.GET.get("level")

    if filter_by == "only_METU":
        words = words.filter(isBaseWord=True)
    elif filter_by == "only_User":
        # Kullanıcı kendi eklediklerini ve listesine kaydettiklerini görür.
        if user.is_authenticated:
            words = words.filter(
                Q(owner=user) | Q(saved_by=user)
            ).filter(isBaseWord=False)
        else:
            words = words.none()

    if query:
        fields = _FIELD_FILTERS.get(filter_by, _DEFAULT_QUERY_FIELDS)
        words = words.filter(_q_from_fields(query, fields))

    if level and level != "all":
        words = words.filter(wordLevel=level)

    # 3) Sıralama + tekilleştirme + N+1 önleme
    words = words.distinct().order_by("id")

    # 4) Pagination (her sayfada 50 kelime)
    paginator = Paginator(words, 50)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    # Kullanıcının listesinde hangi kelimeler var? (Sadece bu sayfada görünenler)
    saved_ids = set()
    if user.is_authenticated:
        page_word_ids = [w.id for w in page_obj.object_list]
        if page_word_ids:
            saved_ids = set(
                UserWordLink.objects
                .filter(user=user, word_id__in=page_word_ids)
                .values_list("word_id", flat=True)
            )

    context = {
        "words": page_obj.object_list,  # Geriye dönük uyumluluk: template hala "words" bekliyor
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "current_query": query,
        "current_filter": filter_by or "",
        "current_level": level or "all",
        "saved_ids": saved_ids,
    }
    return render(request, "pages/words/allWords.html", context)


# ---------------------------------------------------------------------------
# Kelime detay
# ---------------------------------------------------------------------------

def word_detail(request, id):
    word = get_object_or_404(Word.objects.select_related("owner"), id=id)

    if not can_view_word(word, request.user):
        messages.error(request, "Bu kelimeyi görüntüleyemezsiniz.")
        return redirect("all_words")

    # Boş örnek cümleleri (None / "" ) atlayarak template'e gönder
    example_sentences = [
        s for s in (word.exampleSentence1, word.exampleSentence2, word.exampleSentence3)
        if s
    ]

    context = {
        "word": word,
        "exampleSentences": example_sentences,
    }
    return render(request, "pages/words/wordDetail.html", context)


# ---------------------------------------------------------------------------
# Toplu kelime ekleme (kur seviyelerine göre)
# ---------------------------------------------------------------------------

@login_required
def addAllWords(request):
    if request.method != "POST":
        messages.error(request, "Geçersiz istek.")
        return redirect("profile_words")

    value = request.POST.get("bulk_word_list_name")
    if not value or ":" not in value:
        messages.error(request, "Lütfen bir liste seçin.")
        return redirect("profile_words")

    try:
        level, span = value.split(":", 1)
    except ValueError:
        messages.error(request, "Liste formatı hatalı.")
        return redirect("profile_words")

    try:
        if span == "all":
            allWordsAddDelete(request.user, False, level)
        else:
            wordsAddDelete(request.user, False, level, span)
    except Exception as e:
        # Loader'lardan beklenmeyen bir hata gelirse kullanıcıya makul bir mesaj göster.
        messages.error(request, f"Kelimeler eklenirken bir hata oluştu: {e}")
        return redirect("profile_words")

    messages.success(request, "Seçtiğiniz bütün kelimeler listenize eklendi.")
    return redirect("profile_words")
