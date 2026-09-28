import json
import logging
import re
import threading
from datetime import datetime

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from LearnVocab import pagination, progress

from . import ai_import
from .models import (
    CEFR_LEVELS, PartOfSpeech, UserMeaning, UserWordLink, UserWordNote, Word, WordFamily,
)

logger = logging.getLogger(__name__)
from .addWeeks.addWeeks import allWordsAddDelete


# ---------------------------------------------------------------------------
# Görünürlük (visibility) yardımcıları
# ---------------------------------------------------------------------------

def visible_words_qs(user):
    """
    Bir kullanıcının görüntülemeye yetkili olduğu kelimelerin queryset'ini döner.
    - Anonim kullanıcı: sadece base (kur) kelimeleri ve public kelimeler.
    - Giriş yapmış kullanıcı: yukarıdakilere ek olarak kendi kelimeleri ve
      kendi listesine eklediği kelimeler.

    NOT: "friends" görünürlüğü kaldırıldı — arkadaşlık özelliği kapalı.
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
    if word.saved_by.filter(id=user.id).exists():
        return True
    return False


# ---------------------------------------------------------------------------
# Kelime listesi yönetimi
# ---------------------------------------------------------------------------

def _redirect_with_anchor(word_id, request):
    """
    Düğmeye basılan sayfaya geri dön (kelime detayı, Kelimelerim...).

    Eskiden her zaman Tüm Kelimeler'e dönüyordu; o sayfa arayüzden
    kaldırıldı (ürün raporu, Bölüm 17). Tüm Kelimeler düğmeleri fetch ile
    çalıştığı için buraya zaten düşmüyor. Geldiği adres bilinmiyorsa ya da
    başka bir siteyse Kelimelerim'e dönülür.
    """
    geldigi = request.META.get("HTTP_REFERER")
    if geldigi and url_has_allowed_host_and_scheme(
            geldigi, allowed_hosts={request.get_host()},
            require_https=request.is_secure()):
        return redirect(geldigi)
    return redirect("profile_words")


@login_required
def add_to_my_list(request, word_id):
    word = get_object_or_404(Word, id=word_id)

    # Yetkisi olmadığı bir kelimeyi listesine eklemesini engelle
    if not can_view_word(word, request.user):
        messages.error(request, "Bu kelimeyi listenize ekleme yetkiniz yok.")
        return redirect("profile_words")

    bag, olusturuldu = UserWordLink.objects.get_or_create(user=request.user, word=word)
    if olusturuldu and request.method == "POST":
        _geri_yukle(bag, request.POST.get("geri"))
    if _ajax_mi(request):   # kelime kartı / Tüm Kelimeler: sayfa yenilenmeden düğme değişir
        return JsonResponse({"ok": True, "kayitli": True,
                             "html": _dugme_html(request, word.id, True, request.GET.get("boyut", "k"))})
    return _redirect_with_anchor(word.id, request)


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
        return JsonResponse({"ok": True, "kayitli": False, "geri": geri,
                             "html": _dugme_html(request, word.id, False, request.GET.get("boyut", "k"))})
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
    "english": ["text__icontains"],
    "meaning": ["meanings__meaning_tr__icontains"],
    "explanation": ["meanings__definition__icontains"],
    "author": ["owner__username__icontains"],
    "all": [
        "text__icontains",
        "meanings__meaning_tr__icontains",
        "meanings__definition__icontains",
        "owner__username__icontains",
        "cefr__icontains",
        "v2Form__icontains",
        "v3Form__icontains",
    ],
}

_DEFAULT_QUERY_FIELDS = [
    "text__icontains",
    "meanings__meaning_tr__icontains",
    "meanings__definition__icontains",
    "owner__username__icontains",
]


# "Tüm Kelimeler" sayfasında sayfa başına gösterilecek adet seçenekleri
ALL_WORDS_PER_PAGE_OPTIONS = (25, 50, 100, 200)
ALL_WORDS_DEFAULT_PER_PAGE = 50


def _q_from_fields(query, fields):
    """Verilen field listesi için OR'lanmış bir Q objesi üretir."""
    q = Q()
    for f in fields:
        q |= Q(**{f: query})
    return q


# ---------------------------------------------------------------------------
# Arama parametreleri (25 Eylül: filtre paneli, çoklu seçim)
# ---------------------------------------------------------------------------

# "Nerede aransın" onay kutuları -> alanlar
ARAMA_ALANLARI = {
    "kelime": ("Kelime", ["text__icontains", "v2Form__icontains", "v3Form__icontains"]),
    "anlam": ("Türkçe anlam", ["meanings__meaning_tr__icontains"]),
    "aciklama": ("İngilizce açıklama", ["meanings__definition__icontains"]),
    "yazar": ("Ekleyen kullanıcı", ["owner__username__icontains"]),
}
VARSAYILAN_ALANLAR = ("kelime", "anlam")
KAYNAKLAR = {"sozluk": "Sözlük kelimeleri", "kullanici": "Kullanıcı kelimeleri"}
ICERIKLER = {"kelime": "Kelimeler", "ifade": "İfadeler"}

# Eski tek seçimli combobox değerleri (eski bağlantılar bozulmasın)
_ESKI_FILTRE = {"english": ("alan", "kelime"), "meaning": ("alan", "anlam"),
                "explanation": ("alan", "aciklama"), "author": ("alan", "yazar"),
                "only_METU": ("kaynak", "sozluk"), "only_User": ("kaynak", "kullanici")}


def _liste(request, ad, gecerli):
    return [v for v in request.GET.getlist(ad) if v in gecerli and v != "all"]


def arama_parametreleri(request):
    """GET'ten arama durumu. Boş liste = hepsi."""
    alanlar = _liste(request, "alan", ARAMA_ALANLARI)
    kaynaklar = _liste(request, "kaynak", KAYNAKLAR)
    eski = _ESKI_FILTRE.get(request.GET.get("filter_by") or "")
    if eski:
        (alanlar if eski[0] == "alan" else kaynaklar).append(eski[1])
    turler = _liste(request, "pos", dict(PartOfSpeech.choices))
    seviyeler = _liste(request, "level", CEFR_LEVELS)
    if set(kaynaklar) == set(KAYNAKLAR):
        kaynaklar = []
    icerik = _liste(request, "icerik", ICERIKLER) or list(ICERIKLER)
    q = (request.GET.get("q") or "").strip()
    return {
        "q": q,
        "alanlar": alanlar or list(VARSAYILAN_ALANLAR),
        "alan_ozel": bool(alanlar) and set(alanlar) != set(VARSAYILAN_ALANLAR),
        "turler": turler,
        "seviyeler": seviyeler,
        "kaynaklar": kaynaklar,
        "icerik": icerik,
        "kelime_goster": "kelime" in icerik,
        "ifade_goster": "ifade" in icerik,
    }


def _filtreli_kelimeler(user, p):
    words = visible_words_qs(user)
    if p["kaynaklar"] == ["sozluk"]:
        words = words.filter(isBaseWord=True)
    elif p["kaynaklar"] == ["kullanici"]:
        words = (words.filter(Q(owner=user) | Q(saved_by=user)).filter(isBaseWord=False)
                 if user.is_authenticated else words.none())
    if p["q"]:
        alanlar = [f for a in p["alanlar"] for f in ARAMA_ALANLARI[a][1]]
        words = words.filter(_q_from_fields(p["q"], alanlar))
    if p["seviyeler"]:
        words = words.filter(cefr__in=p["seviyeler"])
    if p["turler"]:
        words = words.filter(pos__in=p["turler"])
    return words


def _anlam_metni(kelimeler):
    """Bir ya da birkaç kaydın (anger isim + fiil) anlamları tek satırda."""
    return "; ".join(m.meaning_tr for w in kelimeler for m in w.meanings.all()
                     if m.meaning_tr)


def _kayitli_idler(user, kelimeler):
    if not user.is_authenticated or not kelimeler:
        return set()
    return set(UserWordLink.objects.filter(user=user, word_id__in=[w.id for w in kelimeler])
               .values_list("word_id", flat=True))


def _kelime_satirlari(kelimeler, saved_ids):
    return [{"w": w, "anlam": _anlam_metni([w]), "kayitli": w.id in saved_ids}
            for w in kelimeler]


# ---------------------------------------------------------------------------
# "Bunu mu demek istediniz?" — sonuç çıkmayan aramalar için öneriler
# ---------------------------------------------------------------------------

def _kucuk(metin):
    """Türkçe küçük harf: I -> ı, İ -> i."""
    return (metin or "").replace("I", "ı").replace("İ", "i").lower()


def _oneri_sozlugu():
    """
    (kelime metinleri, Türkçe anlam sözcüğü -> kelime metinleri). Kelime ya da
    anlam sayısı değişince önbellek kendiliğinden yenilenir.
    """
    from django.core.cache import cache
    from .models import Meaning
    anahtar = f"oneri-sozlugu-{Word.objects.count()}-{Meaning.objects.count()}"
    sozluk = cache.get(anahtar)
    if sozluk is None:
        herkese_acik = Q(word__isBaseWord=True) | Q(word__visibility="public")
        metinler = sorted({t.lower() for t in Word.objects
                           .filter(Q(isBaseWord=True) | Q(visibility="public"))
                           .values_list("text", flat=True)})
        anlamlar = {}
        for anlam, metin in Meaning.objects.filter(herkese_acik).values_list(
                "meaning_tr", "word__text"):
            for sozcuk in re.findall(r"\w{3,}", _kucuk(anlam)):
                anlamlar.setdefault(sozcuk, set()).add(metin.lower())
        sozluk = (metinler, {k: sorted(v) for k, v in anlamlar.items()})
        cache.set(anahtar, sozluk, 3600)
    return sozluk


def oneriler(user, sorgu, en_cok=12):
    """
    Yazım hatasına dayanıklı öneriler: benzer yazılan kelimeler (difflib),
    sorguyu içeren kelimeler, sorgunun içinde geçen kelimeler ve Türkçe
    anlamı benzeyenler. Sıra bu önceliğe göre.
    """
    import difflib
    q = _kucuk(sorgu).strip()
    if len(q) < 2:
        return []
    metinler, anlamlar = _oneri_sozlugu()
    sira = []

    def ekle(liste):
        for m in liste:
            if m not in sira:
                sira.append(m)

    ekle(difflib.get_close_matches(q, metinler, n=8, cutoff=0.72))
    if len(q) >= 3:
        ekle([m for m in metinler if q in m][:8])
        ekle(sorted((m for m in metinler if len(m) >= 4 and m in q), key=len, reverse=True)[:4])
    for sozcuk in difflib.get_close_matches(q, list(anlamlar), n=4, cutoff=0.78):
        ekle(anlamlar[sozcuk][:4])
    sira = sira[:en_cok]
    if not sira:
        return []
    kelimeler = list(visible_words_qs(user).filter(text__in=sira).distinct()
                     .prefetch_related("meanings"))
    kelimeler.sort(key=lambda w: (sira.index(w.text.lower()), w.pos))
    return kelimeler


# ---------------------------------------------------------------------------
# İfadeler (bağlayıcılar ve kalıplar) — 25 Eylül
# ---------------------------------------------------------------------------

def visible_expressions_qs(user):
    from .models import Expression
    qs = Expression.objects.all()
    if user.is_authenticated:
        return qs.filter(Q(visibility="public") | Q(owner=user))
    return qs.filter(visibility="public")


_IFADE_ALANLARI = {"kelime": ["text__icontains"], "anlam": ["meaning_tr__icontains"],
                   "aciklama": ["definition__icontains"], "yazar": ["owner__username__icontains"]}


def _ifadeler(user, p):
    """Arama/süzgeçlere uyan ifadeler (tür ve kaynak süzgeçleri yalnızca kelimeler için)."""
    qs = visible_expressions_qs(user)
    if p["q"]:
        qs = qs.filter(_q_from_fields(p["q"], [f for a in p["alanlar"] for f in _IFADE_ALANLARI[a]]))
    if p["seviyeler"]:
        qs = qs.filter(cefr__in=p["seviyeler"])
    return qs.distinct()


def _kayitli_ifadeler(user, ifadeler):
    from .models import UserExpressionLink
    if not user.is_authenticated or not ifadeler:
        return set()
    return set(UserExpressionLink.objects.filter(user=user, expression__in=ifadeler)
               .values_list("expression_id", flat=True))


def _ifade_satirlari(ifadeler, kayitli):
    return [{"e": e, "kayitli": e.id in kayitli} for e in ifadeler]


def _ifade_gruplari(user, p):
    """Arama yokken: işlev başlıkları altında ifadeler (ek işlevde de görünür)."""
    from .models import ExpressionGroup
    ifadeler = list(_ifadeler(user, p).select_related("group").prefetch_related("extra_groups")
                    .order_by("sort_order", "text"))
    kayitli = _kayitli_ifadeler(user, ifadeler)
    gruba_gore = {}
    for e in ifadeler:
        for g in ([e.group] if e.group else []) + list(e.extra_groups.all()):
            gruba_gore.setdefault(g.id, []).append(e)
    bloklar = []
    for g in ExpressionGroup.objects.order_by("sort_order"):
        if gruba_gore.get(g.id):
            bloklar.append({"grup": g, "satirlar": _ifade_satirlari(gruba_gore[g.id], kayitli)})
    grupsuz = [e for e in ifadeler if not e.group]
    if grupsuz:
        bloklar.append({"grup": None, "satirlar": _ifade_satirlari(grupsuz, kayitli)})
    return bloklar, len(ifadeler)


def allWords(request):
    """
    Tüm Kelimeler.

    İki görünüm:
      * Arama ya da filtre YOKSA: AİLE listesi (24 Eylül). Satır = aile; kök
        ve anlamı, açılınca diğer kelimeler.
      * Arama ya da filtre VARSA: kelimeler ailelerinden BAĞIMSIZ, tek tek
        (25 Eylül, Efe: "aramada kullanıcının aklını karıştırmayalım").
        Tam eşleşme önce, sonra "ile başlayan", sonra "içeren".
    Sonuç yoksa öneriler gösterilir ("Bu aradığınız sanırım bizde yok…").

    ?partial=1 (canlı arama, sayfalama): yalnızca sonuç bölümü döner.
    """
    user = request.user
    p = arama_parametreleri(request)
    words = _filtreli_kelimeler(user, p)
    if not p["kelime_goster"]:
        words = words.none()
    duz = bool(p["q"] or p["turler"] or p["seviyeler"] or p["kaynaklar"])

    per_page = pagination.resolve_per_page(request, ALL_WORDS_PER_PAGE_OPTIONS,
                                           ALL_WORDS_DEFAULT_PER_PAGE)
    context = {"duz": duz, "p": p, "geri_qs": request.GET.urlencode().replace("partial=1", "").strip("&")}

    if duz:
        from django.db.models import Case, IntegerField, Value, When
        sira = Case(
            When(text__iexact=p["q"], then=Value(0)),
            When(text__istartswith=p["q"], then=Value(1)),
            When(text__icontains=p["q"], then=Value(2)),
            default=Value(3), output_field=IntegerField(),
        ) if p["q"] else Value(0)
        words = (words.distinct().annotate(sira=sira)
                 .prefetch_related("meanings").order_by("sira", "text", "pos"))
        paginator = Paginator(words, per_page)
        page_obj = paginator.get_page(request.GET.get("page") or 1)
        kelimeler = list(page_obj.object_list)
        saved_ids = _kayitli_idler(user, kelimeler)
        context["satirlar"] = _kelime_satirlari(kelimeler, saved_ids)
        context["kelime_sayisi"] = paginator.count
        ifade_bulunan = 0
        if p["ifade_goster"] and (p["q"] or p["seviyeler"]) and page_obj.number == 1:
            ifadeler = list(_ifadeler(user, p).order_by("text"))
            if p["q"]:
                q = p["q"].lower()
                ifadeler.sort(key=lambda e: (e.text.lower() != q,
                                             not e.text.lower().startswith(q), e.text))
            context["ifade_satirlari"] = _ifade_satirlari(ifadeler, _kayitli_ifadeler(user, ifadeler))
            ifade_bulunan = len(ifadeler)
        if not paginator.count and not ifade_bulunan and p["q"]:
            oneri = oneriler(user, p["q"])
            context["oneriler"] = _kelime_satirlari(oneri, _kayitli_idler(user, oneri))
            # Filtreler yüzünden mi çıkmadı?
            if p["turler"] or p["seviyeler"] or p["kaynaklar"] or p["alan_ozel"]:
                genis = dict(p, turler=[], seviyeler=[], kaynaklar=[],
                             alanlar=list(ARAMA_ALANLARI))
                context["filtresiz_sayi"] = _filtreli_kelimeler(user, genis).distinct().count()
    else:
        aile_idleri = words.values_list("family_id", flat=True).distinct()
        aileler = WordFamily.objects.filter(id__in=aile_idleri).order_by("root")
        paginator = Paginator(aileler, per_page)
        page_obj = paginator.get_page(request.GET.get("page") or 1)
        # İfadeler konu konu, yalnızca ilk sayfada (aile sayfalarında tekrar etmesin)
        if p["ifade_goster"] and page_obj.number == 1:
            context["ifade_bloklari"], context["ifade_sayisi"] = _ifade_gruplari(user, p)
            context["ifade_acik"] = not p["kelime_goster"]
        uyeler = list(visible_words_qs(user)
                      .filter(family__in=list(page_obj.object_list))
                      .distinct().prefetch_related("meanings").order_by("text", "pos"))
        aileye_gore = {}
        for w in uyeler:
            aileye_gore.setdefault(w.family_id, []).append(w)
        saved_ids = _kayitli_idler(user, uyeler)
        satirlar = []
        for aile in page_obj.object_list:
            uye = aileye_gore.get(aile.id, [])
            if not uye:
                continue
            kokler = [w for w in uye if w.text == aile.root] or uye[:1]
            digerleri = [w for w in uye if w not in kokler]
            # Aynı yazılışın birden çok türü varsa (burning sıfat / isim) türü
            # küçük harfle göster; yoksa satırda başka ayrıntı yok.
            sayim = {}
            for w in digerleri:
                sayim[w.text] = sayim.get(w.text, 0) + 1
            satirlar.append({
                "aile": aile,
                "kok_metin": kokler[0].text,
                "kok_anlam": _anlam_metni(kokler),
                "kok_idleri": [w.id for w in kokler],
                "kok_kayitli": all(w.id in saved_ids for w in kokler),
                "uyeler": [dict(r, tur_goster=sayim[r["w"].text] > 1)
                           for r in _kelime_satirlari(digerleri, saved_ids)],
                "eklenmemis": sum(1 for w in uye if w.id not in saved_ids),
            })
        context["aileler"] = satirlar
        context["kelime_sayisi"] = words.distinct().count()

    context.update({
        "arama_alanlari": [(k, v[0]) for k, v in ARAMA_ALANLARI.items()],
        "kaynaklar": list(KAYNAKLAR.items()),
        "icerikler": list(ICERIKLER.items()),
        "cefr_levels": CEFR_LEVELS,
        "pos_choices": PartOfSpeech.choices,
        "current_query": p["q"],
    })
    params = [("q", p["q"])]
    if p["alan_ozel"]:
        params += [("alan", a) for a in p["alanlar"]]
    params += [("kaynak", k) for k in p["kaynaklar"]]
    if set(p["icerik"]) != set(ICERIKLER):
        params += [("icerik", i) for i in p["icerik"]]
    params += [("pos", t) for t in p["turler"]] + [("level", s) for s in p["seviyeler"]]
    context.update(pagination.pagination_context(
        page_obj, paginator, params=params, per_page=per_page,
        per_page_options=ALL_WORDS_PER_PAGE_OPTIONS,
        default_per_page=ALL_WORDS_DEFAULT_PER_PAGE,
    ))
    sablon = ("pages/words/_sonuclar.html" if request.GET.get("partial")
              else "pages/words/allWords.html")
    return render(request, sablon, context)


def _ajax_mi(request):
    return request.headers.get("X-Requested-With") == "fetch"


def _dugme_html(request, word_id, kayitli, boyut="k"):
    from django.template.loader import render_to_string
    return render_to_string("pages/words/_listeDugmesi.html",
                            {"wid": word_id, "kayitli": kayitli, "boyut": boyut,
                             "geri_qs": request.GET.urlencode()}, request=request)


def _ifade_dugme_html(request, expression_id, kayitli, boyut="b"):
    from django.template.loader import render_to_string
    return render_to_string("pages/words/_ifadeDugmesi.html",
                            {"eid": expression_id, "kayitli": kayitli, "boyut": boyut,
                             "geri_qs": request.GET.urlencode()}, request=request)


def _ifade_listesi(request, expression_id, ekle):
    from .models import UserExpressionLink
    ifade = get_object_or_404(visible_expressions_qs(request.user), id=expression_id)
    if ekle:
        UserExpressionLink.objects.get_or_create(user=request.user, expression=ifade)
    else:
        UserExpressionLink.objects.filter(user=request.user, expression=ifade).delete()
    if _ajax_mi(request):
        return JsonResponse({"ok": True, "kayitli": ekle,
                             "html": _ifade_dugme_html(request, ifade.id, ekle,
                                                       request.GET.get("boyut", "b"))})
    sonraki = request.GET.get("next")
    if sonraki == "detay":
        return redirect("expression_detail", id=ifade.id)
    geri = request.GET.copy()
    geri.pop("next", None)
    qs = geri.urlencode()
    return redirect(f"{reverse('all_words')}{'?' + qs if qs else ''}#expr-{ifade.id}")


@login_required
def add_expression_to_my_list(request, expression_id):
    """İfade listesi (kelime listesinden ayrı). fetch ile JSON, yoksa geri dönüş."""
    return _ifade_listesi(request, expression_id, True)


@login_required
def remove_expression_from_my_list(request, expression_id):
    return _ifade_listesi(request, expression_id, False)


def expression_detail(request, id):
    """
    İfade detayı: anlamı, işlevi ("yönü"), kalıbı, noktalama kuralı (doğru ve
    YANLIŞ örneklerle), akademik kullanım, örnek cümleler ve aynı işi yapan
    ifadeler (birinden ötekine atlayarak öğrenmek için).
    """
    from .models import ExampleKind
    ifade = get_object_or_404(
        visible_expressions_qs(request.user).select_related("group")
        .prefetch_related("extra_groups", "examples"), id=id)
    ornekler = list(ifade.examples.all())
    benzerler = list(ifade.similar.select_related("group")[:40])
    gruplar = ([ifade.group] if ifade.group else []) + list(ifade.extra_groups.all())
    return render(request, "pages/words/expressionDetail.html", {
        "ifade": ifade,
        "gruplar": gruplar,
        "ornekler": [o for o in ornekler if o.kind == ExampleKind.EXAMPLE],
        "dogrular": [o for o in ornekler if o.kind == ExampleKind.CORRECT],
        "yanlislar": [o for o in ornekler if o.kind == ExampleKind.WRONG],
        "benzerler": benzerler,
        "kayitli": bool(_kayitli_ifadeler(request.user, [ifade])),
    })


@login_required
@require_POST
def add_family_to_my_list(request, family_id):
    """
    Tüm Kelimeler'deki aile düğmeleri.
      kapsam=hepsi : ailenin bütün görünür kelimeleri ("Tüm aileyi listeme ekle")
      kapsam=kok   : yalnızca kök satırı (alarm isim + fiil gibi birden çok kayıt)
      islem=cikar  : ekleme yerine listeden çıkar (kök düğmesi)
    fetch ile çağrılırsa JSON döner, sayfa yenilenmez.
    """
    aile = get_object_or_404(WordFamily, id=family_id)
    kelimeler = visible_words_qs(request.user).filter(family=aile).distinct()
    kapsam = request.POST.get("kapsam")
    if kapsam == "kok":
        kokler = kelimeler.filter(text=aile.root)
        kelimeler = kokler if kokler.exists() else kelimeler.order_by("text")[:1]
    ids = list(kelimeler.values_list("id", flat=True))

    if request.POST.get("islem") == "cikar":
        UserWordLink.objects.filter(user=request.user, word_id__in=ids).delete()
        yeni, kayitli = [], False
    else:
        mevcut = set(UserWordLink.objects.filter(user=request.user, word_id__in=ids)
                     .values_list("word_id", flat=True))
        yeni = [i for i in ids if i not in mevcut]
        UserWordLink.objects.bulk_create(
            [UserWordLink(user=request.user, word_id=i) for i in yeni], ignore_conflicts=True)
        kayitli = True

    if _ajax_mi(request):
        from django.template.loader import render_to_string
        mesaj = ""
        if kapsam == "hepsi":
            mesaj = (f"{aile.root} ailesinden {len(yeni)} kelime listene eklendi." if yeni
                     else f"{aile.root} ailesinin bütün kelimeleri zaten listende.")
        return JsonResponse({
            "ok": True, "idler": ids, "mesaj": mesaj,
            "dugmeler": {i: _dugme_html(request, i, kayitli) for i in ids},
            "kok_html": render_to_string("pages/words/_kokDugmesi.html",
                                         {"aile_id": aile.id, "kayitli": kayitli,
                                          "geri_qs": request.POST.get("geri", "")},
                                         request=request),
        })
    if kapsam == "hepsi":
        if yeni:
            messages.success(request, f"{aile.root} ailesinden {len(yeni)} kelime listene eklendi.")
        else:
            messages.info(request, f"{aile.root} ailesinin bütün kelimeleri zaten listende.")
    geri = request.POST.get("geri") or ""
    return redirect(f"{reverse('all_words')}{'?' + geri if geri else ''}#family-{aile.id}")


# ---------------------------------------------------------------------------
# Kelime detay
# ---------------------------------------------------------------------------

def _kisisel_kayit(request, word):
    """
    Aile sayfasındaki kullanıcı formlarını işler.

    `form` alanı hangi formun gönderildiğini söylüyor; hepsi aynı adrese
    POST ettiği için ayırt etmenin başka yolu yok.
    """
    hangi = request.POST.get("form") or "note"

    if hangi == "meaning":
        # Kullanıcı aradığı anlamı bulamadıysa kendi anlamını ekliyor.
        # Bu anlam yalnızca ona görünür; çekirdek sözlük değişmez.
        anlam = (request.POST.get("meaning_tr") or "").strip()
        if anlam:
            UserMeaning.objects.create(
                user=request.user, word=word, meaning_tr=anlam[:300],
                definition=(request.POST.get("definition") or "").strip()[:600] or None,
            )
            messages.success(request, "Kendi anlamın eklendi.")
        else:
            messages.error(request, "Anlam boş olamaz.")

    elif hangi == "meaning_delete":
        silinen, _ = UserMeaning.objects.filter(
            user=request.user, word=word, id=request.POST.get("meaning_id") or 0,
        ).delete()
        if silinen:
            messages.info(request, "Anlamın silindi.")

    else:
        metin = (request.POST.get("note") or "").strip()
        if metin:
            UserWordNote.objects.update_or_create(
                user=request.user, word=word, defaults={"note": metin},
            )
            messages.success(request, "Notun kaydedildi.")
        else:
            UserWordNote.objects.filter(user=request.user, word=word).delete()
            messages.info(request, "Notun silindi.")

    return redirect("word_detail", id=word.id)


def word_detail(request, id):
    """
    Kelime sayfası. Tek kelimeyi değil, AİLESİNİ gösterir: seçili kelime
    açık, ailedeki diğer türevler altında listelenir.
    """
    word = get_object_or_404(
        Word.objects.select_related("owner", "family")
        .prefetch_related(
            "meanings__examples", "meanings__collocations", "meanings__patterns",
            "meanings__categories", "forms", "false_friends", "expressions",
        ),
        id=id,
    )

    if not can_view_word(word, request.user):
        messages.error(request, "Bu kelimeyi görüntüleyemezsiniz.")
        return redirect("index")

    # Sayfada iki form var: kişisel not ve kişisel anlam. İkisi de kullanıcı
    # katmanına yazar, çekirdeğe dokunmaz.
    if request.method == "POST" and request.user.is_authenticated:
        return _kisisel_kayit(request, word)

    aile_uyeleri = (
        word.family.words.exclude(id=word.id)
        .prefetch_related("meanings")
        .order_by("text", "pos")
    )

    context = {
        "word": word,
        "family": word.family,
        "family_members": aile_uyeleri,
        # Anlamlar artık kendi cümlelerini, collocation'larını, kalıplarını,
        # tonunu ve alanını taşıyor; şablon her anlamı kendi bloğu olarak basıyor.
        "meanings": word.meanings.all(),
        "synonyms": word.synonyms,
        "antonyms": word.antonyms,
        "simpler_words": word.simpler_words,
        "confusables": word.confusables,
        "false_friends": word.false_friends.all(),
        "expressions": word.expressions.all(),
        "forms": word.forms.exclude(surface=word.text),
        "my_note": word.note_of(request.user),
        "my_meanings": word.meanings_of(request.user),
        "can_edit": word.is_editable_by(request.user),
        "in_my_list": (
            request.user.is_authenticated
            and UserWordLink.objects.filter(user=request.user, word=word).exists()
        ),
    }
    return render(request, "pages/words/wordDetail.html", context)


# ---------------------------------------------------------------------------
# Toplu kelime ekleme (CEFR seviyesine göre)
# ---------------------------------------------------------------------------

@login_required
def addAllWords(request):
    if request.method != "POST":
        messages.error(request, "Geçersiz istek.")
        return redirect("profile_words")

    level = (request.POST.get("bulk_level") or "").strip()
    if level not in CEFR_LEVELS:
        messages.error(request, "Lütfen bir seviye seçin.")
        return redirect("profile_words")

    try:
        allWordsAddDelete(request.user, False, level)
    except Exception as e:
        # Loader'lardan beklenmeyen bir hata gelirse kullanıcıya makul bir mesaj göster.
        messages.error(request, f"Kelimeler eklenirken bir hata oluştu: {e}")
        return redirect("profile_words")

    messages.success(request, "Seçtiğiniz bütün kelimeler listenize eklendi.")
    return redirect("profile_words")


# ---------------------------------------------------------------------------
# Yapay zeka ile kelime ekleme
# ---------------------------------------------------------------------------

AI_IMPORT_ERROR_MESSAGES = {
    "rate_limit": (
        "Yapay zeka servisinin istek kotası doldu. Lütfen bir dakika bekleyip "
        "tekrar deneyin ya da daha az kelimeyle deneyin."
    ),
    "unavailable": (
        "Yapay zeka servisi şu anda yoğun ve cevap veremedi. "
        "Birkaç dakika sonra tekrar deneyebilirsiniz."
    ),
    "unconfigured": (
        "Yapay zeka servisine şu anda ulaşılamıyor. Sorun devam ederse lütfen bize bildirin."
    ),
    "failed": (
        "Kelimeler işlenirken beklenmedik bir sorun oluştu. Lütfen tekrar deneyin."
    ),
}


@login_required
def aiAddWordsPage(request):
    """Kullanıcının kelimelerini yazdığı sayfa."""
    return render(request, "pages/words/aiAddWords.html", {
        "max_words": settings.AI_WORD_IMPORT_MAX_WORDS,
        "sentence_count": ai_import.SENTENCE_COUNT,
    })


def _ai_import_messages(request, summary):
    """Özet sözlüğünü kullanıcı mesajlarına çevirir."""
    added = summary.get("added") or []

    if added:
        messages.success(
            request, f"{len(added)} kelime listenize eklendi: " + ", ".join(added)
        )
    else:
        messages.error(request, "Hiçbir kelime eklenemedi.")

    if summary.get("corrected"):
        messages.info(request, "Yazım düzeltmeleri: " + ", ".join(summary["corrected"]))

    if summary.get("duplicates"):
        messages.info(
            request,
            "Zaten listenizde olduğu için atlananlar: " + ", ".join(summary["duplicates"])
        )

    if summary.get("not_found"):
        messages.warning(
            request,
            "İngilizce'de bulunamadığı için atlananlar: " + ", ".join(summary["not_found"])
        )

    if summary.get("unusable"):
        messages.warning(
            request,
            "Yeterli bilgi üretilemediği için atlananlar: " + ", ".join(summary["unusable"])
        )

    if summary.get("error") and added:
        messages.warning(
            request,
            "Kelimelerin bir kısmı servis kaynaklı bir sorun nedeniyle işlenemedi. "
            "Eksik kalanları tekrar gönderebilirsiniz."
        )


def _ai_import_error_message(error, detail=""):
    message = AI_IMPORT_ERROR_MESSAGES.get(error, AI_IMPORT_ERROR_MESSAGES["failed"])
    return f"{message} ({detail})" if detail else message


def _run_ai_import(job_id, user_id, words):
    """
    Arka planda çalışan iş: zenginleştir, kaydet, sonucu iş kaydına yaz.

    Kendi veritabanı bağlantısını kullandığı için sonunda kapatılıyor; aksi
    hâlde her istekte bir bağlantı sızar.
    """
    from django.contrib.auth import get_user_model
    from django.db import connection

    try:
        user = get_user_model().objects.get(pk=user_id)

        reporter = progress.Reporter(job_id, 3, 92)
        outcome = ai_import.enrich_words(words, reporter=reporter)

        if outcome.is_total_failure:
            progress.fail(job_id, _ai_import_error_message(outcome.error, outcome.detail))
            return

        progress.update(job_id, percent=95, message="Kelimeler listenize ekleniyor...")
        summary = ai_import.save_enriched_words(user, outcome)

        eklenen = len(summary["added"])
        progress.finish(
            job_id, summary,
            f"{eklenen} kelime eklendi." if eklenen else "Hiçbir kelime eklenemedi."
        )
    except Exception:
        logger.exception("Kelime zenginleştirme işi beklenmedik şekilde hata verdi.")
        progress.fail(job_id, AI_IMPORT_ERROR_MESSAGES["failed"])
    finally:
        connection.close()


@login_required
@require_POST
def aiAddWords(request):
    """
    Kullanıcının yazdığı kelimeleri işler.

    Tarayıcı JavaScript ile (AJAX) çağırdığında iş arka plana alınır ve bir iş
    kimliği döner; ilerleme `ai_add_words_progress` ile sorulur. JavaScript
    çalışmıyorsa aynı iş istek içinde senkron yapılır; özellik yine çalışır,
    yalnızca ilerleme çubuğu olmaz.
    """
    words, was_truncated = ai_import.parse_input_words(request.POST.get("words"))
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if not words:
        if is_ajax:
            return JsonResponse({"error": "Lütfen en az bir kelime yazınız."}, status=400)
        messages.error(request, "Lütfen en az bir kelime yazınız.")
        return redirect("ai_add_words_page")

    truncation_warning = None
    if was_truncated:
        truncation_warning = (
            f"Tek seferde en fazla {settings.AI_WORD_IMPORT_MAX_WORDS} kelime "
            "işlenebiliyor; listenin ilk kısmı alındı."
        )

    # --- Arka plan (ilerleme çubuklu) akış ---
    if is_ajax:
        job_id = progress.create(
            request.user.id,
            message=f"{len(words)} kelime hazırlanıyor...",
        )
        threading.Thread(
            target=_run_ai_import,
            args=(job_id, request.user.id, words),
            daemon=True,
        ).start()

        return JsonResponse({
            "job_id": job_id,
            "word_count": len(words),
            "warning": truncation_warning,
        })

    # --- JavaScript yoksa: senkron akış ---
    if truncation_warning:
        messages.warning(request, truncation_warning)

    outcome = ai_import.enrich_words(words)

    if outcome.is_total_failure:
        messages.error(request, _ai_import_error_message(outcome.error, outcome.detail))
        return redirect("ai_add_words_page")

    summary = ai_import.save_enriched_words(request.user, outcome)
    _ai_import_messages(request, summary)

    return redirect("profile_words") if summary["added"] else redirect("ai_add_words_page")


@login_required
def aiAddWordsProgress(request, job_id):
    """Tarayıcının ilerlemeyi sorduğu uç."""
    job = progress.read(job_id)

    if job is None or job.get("owner_id") != request.user.id:
        return JsonResponse({"error": "İş bulunamadı."}, status=404)

    return JsonResponse({
        "state": job.get("state"),
        "percent": job.get("percent", 0),
        "message": job.get("message", ""),
    })


@login_required
@require_POST
def aiAddWordsFinish(request, job_id):
    """
    İş bittiğinde çağrılır: sonucu mesajlara çevirir, nereye gidileceğini söyler.

    Mesajlar bir isteğe bağlı olduğu için arka plan iş parçacığında
    üretilemiyor; özet iş kaydında taşınıp burada mesaja dönüştürülüyor.
    """
    job = progress.read(job_id)

    if job is None or job.get("owner_id") != request.user.id:
        return JsonResponse({"error": "İş bulunamadı."}, status=404)

    if job.get("state") == progress.STATE_RUNNING:
        return JsonResponse({"error": "İş hâlâ sürüyor."}, status=409)

    if job.get("state") == progress.STATE_FAILED:
        messages.error(request, job.get("message") or AI_IMPORT_ERROR_MESSAGES["failed"])
        progress.delete(job_id)
        return JsonResponse({"redirect": reverse("ai_add_words_page")})

    summary = job.get("result") or {}
    _ai_import_messages(request, summary)
    progress.delete(job_id)

    target = "profile_words" if summary.get("added") else "ai_add_words_page"
    return JsonResponse({"redirect": reverse(target)})


# ---------------------------------------------------------------------------
# Sözlük (ürün raporu 4 ve 5): words/sozluk_views.py, adresler words/sozluk_urls.py
# ---------------------------------------------------------------------------
