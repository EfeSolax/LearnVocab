"""
Listeye ekleme / listeden çıkarma uçları (kelime ve ifade).

Kelime kartı (base/_kelimeKartiJs.html), Listem ve okuma baloncuğu bu
uçlara fetch ile POST ediyor ve JSON cevap bekliyor. Sözlük sayfalarının
kendisi words/sozluk_views.py'de.

Eski "Tüm Kelimeler", kelime detayı, ifade detayı, toplu ekleme ve
yapay zekâ ile kelime ekleme sayfaları 29 Eylül'de kaldırıldı (rapor 18.13).
"""

import json
from datetime import datetime

from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Expression, UserExpressionLink, UserWordLink, Word


# ---------------------------------------------------------------------------
# Görünürlük
# ---------------------------------------------------------------------------

def visible_words_qs(user):
    """
    Bir kullanıcının görüntülemeye yetkili olduğu kelimeler.
    - Anonim kullanıcı: temel kelimeler ve herkese açık kelimeler.
    - Giriş yapmış kullanıcı: bunlara ek olarak kendi kelimeleri ve
      listesine eklediği kelimeler.
    """
    base_qs = Word.objects.select_related("owner")

    if not user.is_authenticated:
        return base_qs.filter(Q(isBaseWord=True) | Q(visibility="public"))

    return base_qs.filter(
        Q(isBaseWord=True)
        | Q(owner=user)
        | Q(saved_by=user)
        | Q(visibility="public")
    )


def can_view_word(word, user):
    """Tek bir Word objesi için görünürlük kontrolü."""
    if word.isBaseWord or word.visibility == "public":
        return True
    if not user.is_authenticated:
        return False
    if word.owner_id == user.id:
        return True
    return word.saved_by.filter(id=user.id).exists()


def visible_expressions_qs(user):
    qs = Expression.objects.all()
    if user.is_authenticated:
        return qs.filter(Q(visibility="public") | Q(owner=user))
    return qs.filter(visibility="public")


# ---------------------------------------------------------------------------
# Ortak
# ---------------------------------------------------------------------------

def _ajax_mi(request):
    return request.headers.get("X-Requested-With") == "fetch"


def _geri_don(request):
    """
    fetch dışında (JS kapalıyken) düğmeye basılan sayfaya dön. Geldiği adres
    bilinmiyorsa ya da başka bir siteyse Listem'e dönülür.
    """
    geldigi = request.META.get("HTTP_REFERER")
    if geldigi and url_has_allowed_host_and_scheme(
            geldigi, allowed_hosts={request.get_host()},
            require_https=request.is_secure()):
        return redirect(geldigi)
    return redirect(f"{reverse('sozluk')}?sekme=listem")


# ---------------------------------------------------------------------------
# Kelime listesi
# ---------------------------------------------------------------------------

@login_required
def add_to_my_list(request, word_id):
    word = get_object_or_404(Word, id=word_id)

    # Yetkisi olmadığı bir kelimeyi listesine eklemesini engelle
    if not can_view_word(word, request.user):
        if _ajax_mi(request):
            return JsonResponse({"ok": False}, status=403)
        return _geri_don(request)

    bag, olusturuldu = UserWordLink.objects.get_or_create(user=request.user, word=word)
    if olusturuldu and request.method == "POST":
        _geri_yukle(bag, request.POST.get("geri"))
    if _ajax_mi(request):
        return JsonResponse({"ok": True, "kayitli": True})
    return _geri_don(request)


def _geri_verisi(bag):
    """Listeden çıkarılan bağın "Geri al" ile geri konacak hâli."""
    return {"dateAdded": bag.dateAdded.isoformat(),
            "correctCount": bag.correctCount, "wrongCount": bag.wrongCount}


def _geri_yukle(bag, ham):
    """
    "Geri al" (rapor 12.7): kelime listeye eklenme tarihi ve çalışma
    sayaçlarıyla geri konur; yoksa "en son eklenen" sırası ve Zorlandıklarım
    bilgisi bozulurdu. Kullanıcı yalnızca kendi bağını değiştirebiliyor.
    """
    if not ham:
        return
    try:
        veri = json.loads(ham)
        alanlar = {
            "dateAdded": datetime.fromisoformat(veri["dateAdded"]),
            "correctCount": max(0, int(veri.get("correctCount", 0))),
            "wrongCount": max(0, int(veri.get("wrongCount", 0))),
        }
    except (ValueError, TypeError, KeyError):
        return
    if timezone.is_naive(alanlar["dateAdded"]):
        return
    if alanlar["dateAdded"] > bag.dateAdded:   # gelecekten tarih kabul edilmez
        alanlar["dateAdded"] = bag.dateAdded
    UserWordLink.objects.filter(pk=bag.pk).update(**alanlar)


@login_required
def remove_from_my_list(request, word_id):
    word = get_object_or_404(Word, id=word_id)
    bag = UserWordLink.objects.filter(user=request.user, word=word).first()
    geri = _geri_verisi(bag) if bag else None
    if bag:
        bag.delete()
    if _ajax_mi(request):
        return JsonResponse({"ok": True, "kayitli": False, "geri": geri})
    return _geri_don(request)


# ---------------------------------------------------------------------------
# İfade listesi (kelime listesinden ayrı; Günün İfadesi kartı kullanacak, rapor 18.8)
# ---------------------------------------------------------------------------

def _ifade_listesi(request, expression_id, ekle):
    ifade = get_object_or_404(visible_expressions_qs(request.user), id=expression_id)
    if ekle:
        UserExpressionLink.objects.get_or_create(user=request.user, expression=ifade)
    else:
        UserExpressionLink.objects.filter(user=request.user, expression=ifade).delete()
    if _ajax_mi(request):
        return JsonResponse({"ok": True, "kayitli": ekle})
    return _geri_don(request)


@login_required
def add_expression_to_my_list(request, expression_id):
    return _ifade_listesi(request, expression_id, True)


@login_required
def remove_expression_from_my_list(request, expression_id):
    return _ifade_listesi(request, expression_id, False)
