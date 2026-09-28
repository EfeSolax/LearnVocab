"""
Öğren-Geç görünümleri.

Akış bilerek iki adımlı (bkz. templates/pages/learnpass/learnPass.html):

  1) Kart yalnızca kelimeyi ve içinde geçtiği bir cümleyi gösterir.
  2) Kullanıcı "Biliyorum" / "Bilmiyorum" der — anlamı GÖRMEDEN karar verir.
  3) Anlam açılır. "Biliyorum" diyene tek bir soru sorulur:
     "Aklındaki bu muydu?" — hayır derse kelime 'bildiğini sanıyordu' olarak
     işaretlenir ve listeye eklenir.

Anlamı baştan göstermek sınıflandırmayı anlamsız kılardı (insan gördüğü
anlamı zaten bildiğini sanır); anlamı hiç göstermemek de öğrenmeyi
engellerdi. İki adım bu ikisinin arasını buluyor ve hızlı yolu
(bilmiyorum -> ekle -> sonraki) tek dokunuşta bırakıyor.
"""

import json
import random

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from LearnVocab.authgate import login_gate
from words.models import UserWordLink, Word

from . import selection
from .models import Declaration, EncounterLog, WordEncounter


GATE_LABEL = "Çalışmalar"
GATE_NOTE = "Learn & Pass'te yaptıklarının kaydedilmesi için giriş yapman gerekiyor."

MODES = {
    WordEncounter.MODE_MINE: "Kendi Kelimelerim",
    WordEncounter.MODE_NEW: "Yeni Kelimeler",
}

# Geri al için saklanan adım sayısı. Oturumu şişirmemek için sınırlı.
HISTORY_LIMIT = 20


# ----------------------------------------------------------------------
# Kart verisi
# ----------------------------------------------------------------------

def encounter_payload(word, user):
    """
    Kartın altına basılacak karşılaşma bilgisi.

    Kullanıcıya kaçıncı kez gördüğünü söylemek bir süs değil: beyanın
    kendisi ("bu kadar çok çıkmasına RAĞMEN hâlâ öğrenemedim") ancak
    sayıyı bilirse anlamlı. Sayı görünmeden sorulan soru, kullanıcının
    hafızasındaki belirsiz bir izlenime dayanır.
    """
    kayit = WordEncounter.objects.filter(user=user, word=word).first()
    if kayit is None:
        return {"times_seen": 0, "can_declare": False,
                "declaration": Declaration.NONE, "miss_count": 0}
    return {
        "times_seen": kayit.times_seen,
        "can_declare": kayit.can_declare,
        "declaration": kayit.declaration,
        "miss_count": kayit.miss_count,
    }


def card_payload(word, user):
    """Bir kelimeyi karta basılacak hâle getirir."""
    sentences = word.example_sentences
    # Kart açılmadan gösterilecek cümle rastgele seçiliyor: aynı kelime
    # tekrar geldiğinde farklı bir bağlamda görülsün.
    prompt_sentence = random.choice(sentences) if sentences else ""
    # Kart açıldığında 2 ek cümle yetiyor: daha fazlası kartı uzatıp
    # karar düğmelerini ekranın dışına itiyor. Tamamı kelime detayında.
    extra = [s for s in sentences if s != prompt_sentence][:2]

    return {
        "id": word.id,
        "word": word.text,
        "level": word.cefr or "",
        "prompt_sentence": prompt_sentence,
        "meaning": word.meaningTr,
        "explanation": word.explanation or "",
        "pos": word.get_pos_display(),
        "extra_sentences": extra,
        "is_verb": word.is_verb,
        "v2": word.v2Form or "",
        "v3": word.v3Form or "",
        "in_my_list": UserWordLink.objects.filter(user=user, word=word).exists(),
        "detail_url": f"/words/word-detail/{word.id}/",
        "encounter": encounter_payload(word, user),
    }


def next_card(user, mode):
    """Sıradaki kart ya da havuz bittiyse None."""
    word = selection.pick_word(user, mode)
    return card_payload(word, user) if word else None


# ----------------------------------------------------------------------
# Oturum durumu (sayaçlar + geri al geçmişi)
# ----------------------------------------------------------------------

def _stats_key(mode):
    return f"learnpass_stats_{mode}"


def _history_key(mode):
    return f"learnpass_history_{mode}"


def read_stats(session, mode):
    return session.get(_stats_key(mode)) or {"seen": 0, "added": 0, "misjudged": 0}


def write_stats(session, mode, stats):
    session[_stats_key(mode)] = stats
    session.modified = True


def reset_run(session, mode):
    session[_stats_key(mode)] = {"seen": 0, "added": 0, "misjudged": 0}
    session[_history_key(mode)] = []
    session.modified = True


# ----------------------------------------------------------------------
# Sayfalar
# ----------------------------------------------------------------------

def learnPassPage(request):
    """
    Mod seçimi. Hangi havuzdan çalışacağına burada karar veriliyor.

    Çalışmalar bölümünün açılış sayfası; menüden herkes gelebilsin diye
    girişsiz de açılıyor (rapor 2.3). Girişsiz ziyaretçinin yalnızca
    kaydırdığı, hiçbir şeyin kaydedilmediği akış 6. adımda (L&P) yazılacak;
    o zamana kadar mod düğmeleri girişsizken giriş sayfasına yönlendiriyor
    (data-giris-gerekli), sayaçlar gösterilmiyor.
    """
    girisli = request.user.is_authenticated
    context = {
        "active_page": "Learn & Pass",
        "exercise_tab": "learn",
        "own_count": selection.own_words_qs(request.user).count() if girisli else None,
        "new_count": selection.new_words_qs(request.user).count() if girisli else None,
    }
    return render(request, "pages/learnpass/modePicker.html", context)


@login_gate(GATE_LABEL, GATE_NOTE)
def learnPassRun(request, mode):
    """Kart ekranı. İlk kart sunucudan geliyor, gerisi JSON ile."""
    if mode not in MODES:
        return redirect("learn_pass_page")

    reset_run(request.session, mode)

    context = {
        "active_page": "Learn & Pass",
        "exercise_tab": "learn",
        "mode": mode,
        "mode_label": MODES[mode],
        "first_card": next_card(request.user, mode),
        "remaining": selection.remaining_count(request.user, mode),
    }
    return render(request, "pages/learnpass/learnPass.html", context)


# Egzersizler sekmesi (exercises_page) egzersizler uygulamasına taşındı.


# ----------------------------------------------------------------------
# JSON uçları
# ----------------------------------------------------------------------

def _mode_from(request, payload):
    mode = payload.get("mode")
    return mode if mode in MODES else WordEncounter.MODE_NEW


def _body(request):
    try:
        return json.loads(request.body.decode() or "{}")
    except (ValueError, UnicodeDecodeError):
        return {}


@require_POST
def learnPassVerdict(request):
    """
    Bir kararı kaydeder ve sıradaki kartı döner.

    Listeye ekleme kuralı: kullanıcı kelimeyi bilmiyorsa ya da bildiğini
    sanıp yanıldıysa kelime listesine giriyor. "Gerçekten biliyorum"
    dediğinde eklenmiyor; zaten listesindeyse 'öğrenildi' işaretleniyor
    (silinmiyor — bkz. WordEncounter.record).
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth"}, status=403)

    payload = _body(request)
    mode = _mode_from(request, payload)
    verdict = payload.get("verdict")

    if verdict not in dict(WordEncounter.VERDICT_CHOICES):
        return JsonResponse({"error": "verdict"}, status=400)

    word = get_object_or_404(Word, id=payload.get("word_id") or 0)

    # --- Geri al için önceki hâli sakla ---
    onceki = WordEncounter.objects.filter(user=request.user, word=word).first()
    gecmis_kaydi = {
        "word_id": word.id,
        "encounter": None if onceki is None else {
            "last_verdict": onceki.last_verdict,
            "last_mode": onceki.last_mode,
            "times_seen": onceki.times_seen,
            "unknown_count": onceki.unknown_count,
            "known_count": onceki.known_count,
            "misjudged_count": onceki.misjudged_count,
            "is_learned": onceki.is_learned,
            "declaration": onceki.declaration,
        },
        "added_to_list": False,
    }

    WordEncounter.record(request.user, word, verdict, mode)

    # --- Listeye ekleme ---
    if verdict in (WordEncounter.UNKNOWN, WordEncounter.MISJUDGED):
        _, olusturuldu = UserWordLink.objects.get_or_create(user=request.user, word=word)
        gecmis_kaydi["added_to_list"] = olusturuldu

    # --- Sayaçlar ---
    stats = read_stats(request.session, mode)
    stats["seen"] += 1
    if gecmis_kaydi["added_to_list"]:
        stats["added"] += 1
    if verdict == WordEncounter.MISJUDGED:
        stats["misjudged"] += 1
    write_stats(request.session, mode, stats)

    gecmis = request.session.get(_history_key(mode)) or []
    gecmis.append(gecmis_kaydi)
    request.session[_history_key(mode)] = gecmis[-HISTORY_LIMIT:]
    request.session.modified = True

    return JsonResponse({
        "stats": stats,
        # Cevaplanan kelimenin GÜNCEL durumu. Beyan şeridinin çıkıp
        # çıkmayacağına bu karar veriyor; eşiğin (BEYAN_ESIGI) tarayıcıda
        # tekrar yazılmaması için sunucu hesaplayıp gönderiyor.
        "answered": encounter_payload(word, request.user),
        "card": next_card(request.user, mode),
        "remaining": selection.remaining_count(request.user, mode),
    })


@require_POST
def learnPassUndo(request):
    """
    Son kararı geri alır: kaydı eski hâline döndürür, o adımda listeye
    eklenmiş kelimeyi listeden çıkarır ve kartı tekrar gösterir.
    Hızlı dokunulan bir ekranda yanlış tuşa basmak kaçınılmaz.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth"}, status=403)

    mode = _mode_from(request, _body(request))
    gecmis = request.session.get(_history_key(mode)) or []
    if not gecmis:
        return JsonResponse({"error": "empty"}, status=400)

    kayit = gecmis.pop()
    request.session[_history_key(mode)] = gecmis
    request.session.modified = True

    word = Word.objects.filter(id=kayit["word_id"]).first()
    if word is None:
        return JsonResponse({"error": "missing"}, status=404)

    onceki = kayit["encounter"]
    if onceki is None:
        WordEncounter.objects.filter(user=request.user, word=word).delete()
    else:
        WordEncounter.objects.filter(user=request.user, word=word).update(**onceki)

    # Günlükteki son karşılaşma kaydı da geri alınıyor. Yanlış tuşa
    # basılarak oluşmuş bir kayıt, ileride "kullanıcı bu kelimeyi kaçıncı
    # karşılaşmada öğrendi" sorusunun cevabını bozar.
    son_kayit = (EncounterLog.objects
                 .filter(user=request.user, word=word, kind=EncounterLog.VERDICT)
                 .order_by("-created_at", "-id").first())
    if son_kayit is not None:
        son_kayit.delete()

    if kayit["added_to_list"]:
        UserWordLink.objects.filter(user=request.user, word=word).delete()

    stats = read_stats(request.session, mode)
    stats["seen"] = max(0, stats["seen"] - 1)
    if kayit["added_to_list"]:
        stats["added"] = max(0, stats["added"] - 1)
    if onceki is not None and onceki.get("last_verdict") == WordEncounter.MISJUDGED:
        pass  # önceki hâli zaten geri yüklendi
    write_stats(request.session, mode, stats)

    return JsonResponse({
        "stats": stats,
        "card": card_payload(word, request.user),
        "remaining": selection.remaining_count(request.user, mode),
    })


@require_POST
def learnPassDeclare(request):
    """
    Kullanıcının "artık öğrendim" / "hâlâ öğrenemedim" beyanını kaydeder.

    Bu uç Öğren-Geç'in asıl ürününü topluyor. Karar (biliyorum/bilmiyorum)
    tek bir ana ait; beyan ise kullanıcının o kelimeyle kurduğu İLİŞKİ
    hakkında ve tekrar sayısını da hesaba katıyor.

    Beyan yalnızca kelime yeterince görüldükten sonra kabul ediliyor
    (BEYAN_ESIGI): "bu kadar çok çıkmasına rağmen" ifadesi, birinci
    karşılaşmada bir şey anlatmaz.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth"}, status=403)

    payload = _body(request)
    beyan = payload.get("declaration")
    if beyan not in (Declaration.MASTERED, Declaration.STUCK):
        return JsonResponse({"error": "declaration"}, status=400)

    word = get_object_or_404(Word, id=payload.get("word_id") or 0)
    kayit = WordEncounter.objects.filter(user=request.user, word=word).first()

    if kayit is None or not kayit.can_declare:
        return JsonResponse({"error": "too_early"}, status=400)

    kayit.declare(beyan)

    # "Hâlâ öğrenemedim" denen kelime listede olmalı: kullanıcı onunla
    # uğraşmaya devam edecek. "Öğrendim" denen kelime listeden
    # ÇIKARILMIYOR — yalnızca Öğren-Geç havuzundan düşüyor.
    if beyan == Declaration.STUCK:
        UserWordLink.objects.get_or_create(user=request.user, word=word)

    mode = _mode_from(request, payload)
    return JsonResponse({
        "ok": True,
        "declaration": beyan,
        "remaining": selection.remaining_count(request.user, mode),
    })
