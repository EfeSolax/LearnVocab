"""
Learn & Pass görünümleri (ürün raporu 6.1, misafir kuralları 2.3).

Akış (rapor 18.1):
  1) Kart yalnızca kelimeyi gösterir (tür etiketi yok, rapor 12.1).
  2) Sağa kaydır = biliyorum, sola = bilmiyorum.
  3) Anlam açılır. "Biliyorum" dediyse "Düşündüğün bu muydu?": ikinci
     kaydırma sağa = "Evet, eminim" (known), sola = "Hayır, yanılmışım"
     (misjudged). "Bilmiyorum" dediyse yalnızca anlam ve "Devam etmek için
     kaydır" (unknown).
  4) Karar İKİNCİ adımda kesinleşir ve anında sunucuya yazılır
     (learnPassVerdict); oturum yarıda kalsa da kayıp yok.

Kurallar:
  - Tekrar kuralı learnpass/tekrar.py (rapor 18.2); her karar seriye de
    sayılır (seri/hesap.py, rapor 18.9).
  - Bilinmeyenler listeye kendiliğinden EKLENMEZ. Oturum sonunda sorulur
    (learnPassBilinmeyenler). Sorulmadan kalanlar WordEncounter.listeye_sorulacak
    işaretiyle bekler ve açılış ekranında "Geçen sefer bilmediğin N kelime"
    kartı olarak çıkar.
  - Girişsiz ziyaretçi yalnızca kaydırır: kartlar sayfayla birlikte gelir,
    hiçbir istek atılmaz. Seviye seçimi yok: %60 B1 · %20 B2 · %20 C1 (18.3).

Oturum türleri (adresteki `mode`):
  karma -> "Hemen Başla": ~%70 tekrar / ~%30 yeni kelime
  mine  -> yalnızca tekrar adayları    new -> yalnızca yeni kelimeler
Her kart hangi havuzdan geldiğini (`kaynak`: mine/new) taşır ve karar o
havuzun adıyla kaydedilir.
"""

import json
import random
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from words.models import UserWordLink, Word

from seri import hesap as seri_hesap

from . import selection, tekrar
from .models import EncounterLog, WordEncounter


KARMA = "karma"
MODES = {
    KARMA: "Bugünün çalışması",
    WordEncounter.MODE_MINE: "Kendi Kelimelerim",
    WordEncounter.MODE_NEW: "Yeni Kelimeler",
}
KAYNAKLAR = (WordEncounter.MODE_MINE, WordEncounter.MODE_NEW)

# Bir oturumdaki kart sayısı. Oturum sonunda "bilmediklerini ekleyelim mi?"
# sorusu gelir; kullanıcı istediği an "Bitir" diyebilir.
OTURUM_KART_SAYISI = 20

# Anlam balonunda en çok kaç Türkçe anlam gösterileceği.
EN_COK_ANLAM = 3

# Geri al için saklanan adım sayısı. Oturumu şişirmemek için sınırlı.
HISTORY_LIMIT = 20


# ----------------------------------------------------------------------
# Kart verisi
# ----------------------------------------------------------------------

def encounter_payload(word, user):
    """Kelimenin kullanıcıdaki güncel tekrar bilgisi (kartta gösterilmez)."""
    kayit = WordEncounter.objects.filter(user=user, word=word).first()
    if kayit is None:
        return {"times_seen": 0, "basamak": 0, "miss_count": 0}
    return {"times_seen": kayit.times_seen, "basamak": kayit.basamak,
            "miss_count": kayit.miss_count}


def card_payload(word, user=None, kaynak=None):
    """
    Bir kelimeyi karta basılacak hâle getirir.

    Bilerek YOK: tür (isim/fiil…) ve seviye. Kartta yalnızca kelime görünür
    (rapor 6.1, 12.1); anlamlar ve örnek yalnızca kaydırınca açılır.
    """
    # list(...)[:n]: önceden getirilmişse (prefetch) yeni sorgu açılmasın.
    anlamlar = list(word.meanings.all())[:EN_COK_ANLAM]
    ornekler = []
    if anlamlar:
        ornekler = [o.text for o in anlamlar[0].examples.all()]
    kart = {
        "id": word.id,
        "word": word.text,
        "meanings": [a.meaning_tr for a in anlamlar],
        # Aynı kelime tekrar geldiğinde farklı bir cümleyle görülsün.
        "example": random.choice(ornekler) if ornekler else "",
        "kaynak": kaynak or WordEncounter.MODE_NEW,
    }
    if user is not None and user.is_authenticated:
        kart["encounter"] = encounter_payload(word, user)
        # Listedeki kelime oturum sonunda "listene ekleyelim mi?" diye sorulmaz.
        kart["listede"] = (kaynak == WordEncounter.MODE_MINE
                           or UserWordLink.objects.filter(user=user, word=word).exists())
    return kart


def next_card(user, mode, haric=()):
    """Sıradaki kart ya da havuz bittiyse None."""
    if mode == KARMA:
        word, kaynak = selection.pick_mixed(user, haric=haric)
    else:
        word, kaynak = selection.pick_word(user, mode, haric=haric), mode
    return card_payload(word, user, kaynak) if word else None


# ----------------------------------------------------------------------
# Oturum durumu (sayaçlar + geri al geçmişi + bu turda gösterilenler)
# Yalnızca girişli kullanıcı için; misafir için oturuma hiçbir şey yazılmaz.
# ----------------------------------------------------------------------

def _stats_key(mode):
    return f"learnpass_stats_{mode}"


def _history_key(mode):
    return f"learnpass_history_{mode}"


def _shown_key(mode):
    return f"learnpass_shown_{mode}"


def _bos_sayac():
    return {"seen": 0, "known": 0, "unknown": 0}


def read_stats(session, mode):
    return session.get(_stats_key(mode)) or _bos_sayac()


def write_stats(session, mode, stats):
    session[_stats_key(mode)] = stats
    session.modified = True


def reset_run(session, mode):
    session[_stats_key(mode)] = _bos_sayac()
    session[_history_key(mode)] = []
    session[_shown_key(mode)] = []
    session.modified = True


def _gosterilenler(session, mode):
    return session.get(_shown_key(mode)) or []


def _gosterildi(session, mode, kart):
    """Bu turda gösterilen kart bir daha gelmesin (tur sonunda liste sıfırlanır)."""
    if kart is None:
        return
    liste = _gosterilenler(session, mode)
    liste.append(kart["id"])
    session[_shown_key(mode)] = liste[-(OTURUM_KART_SAYISI * 3):]
    session.modified = True


# ----------------------------------------------------------------------
# Sayfalar
# ----------------------------------------------------------------------

def acilis_verisi(user):
    """Açılış ekranı için girişli kullanıcının sayıları (tek yerde)."""
    bugun = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    bekleyen_tekrar = tekrar.bekleyen_tekrar_sayisi(user)
    oran = selection.yeni_orani(user, bekleyen_tekrar)
    bekleyenler = list(selection.bekleyen_bilinmeyenler(user).order_by("text")
                       .values("id", "text"))
    return {
        "liste_sayisi": UserWordLink.objects.filter(user=user).count(),
        "bugun_gorulen": EncounterLog.objects.filter(
            user=user, kind=EncounterLog.VERDICT, created_at__gte=bugun).count(),
        "bekleyen_tekrar": bekleyen_tekrar,
        "yeni_yuzde": round(oran * 100),
        "tekrar_yuzde": 100 - round(oran * 100),
        "oran_azaldi": oran < selection.kullanici_yeni_orani(user),
        "gecen_sefer": bekleyenler,
        "seri": seri_hesap.durum(user),
    }


def learnPassPage(request):
    """
    Learn & Pass açılış ekranı: istatistik şeridi, slogan, "Hemen Başla",
    oran notu, "Neden işe yarar". Girişsiz de açık (rapor 2.3).
    """
    context = {
        "active_page": "Learn & Pass",
        "exercise_tab": "learn",
    }
    if request.user.is_authenticated:
        # Seviye, L&P ve egzersiz cevaplarından kendiliğinden düzelir (rapor 18.27).
        from seviye.duzeltme import seviyeyi_sessizce_duzelt
        seviyeyi_sessizce_duzelt(request.user)
        context.update(acilis_verisi(request.user))
    return render(request, "pages/learnpass/modePicker.html", context)


def learnPassRun(request, mode):
    """
    Kart ekranı.

    Girişli: ilk kart sunucudan gelir, sonrakiler her kaydırmanın cevabıyla.
    Misafir: bütün tur (OTURUM_KART_SAYISI kart) sayfayla birlikte gelir;
    tarayıcı hiçbir istek atmaz, hiçbir şey kaydedilmez.
    """
    if mode not in MODES:
        return redirect("learn_pass_page")

    context = {
        "active_page": "Learn & Pass",
        "exercise_tab": "learn",
        "mode": mode,
        "mode_label": MODES[mode],
        "oturum_kart_sayisi": OTURUM_KART_SAYISI,
    }

    if not request.user.is_authenticated:
        if mode == WordEncounter.MODE_MINE:  # misafirin listesi yok
            return redirect("learn_pass_run", mode=KARMA)
        kelimeler = tekrar.misafir_kelimeleri(OTURUM_KART_SAYISI)
        context.update({
            "misafir": True,
            "kartlar": [card_payload(k) for k in kelimeler],
        })
        return render(request, "pages/learnpass/learnPass.html", context)

    reset_run(request.session, mode)
    ilk = next_card(request.user, mode)
    _gosterildi(request.session, mode, ilk)
    context.update({
        "misafir": False,
        "kartlar": [ilk] if ilk else [],
        "seri": seri_hesap.bugun(request.user),   # alevli çubuk (rapor 18.9)
    })
    return render(request, "pages/learnpass/learnPass.html", context)


# Egzersizler sekmesi (exercises_page) egzersizler uygulamasına taşındı.


# ----------------------------------------------------------------------
# JSON uçları (yalnızca girişli kullanıcı; misafir hiçbirini çağırmaz)
# ----------------------------------------------------------------------

def _run_from(payload):
    mode = payload.get("mode")
    return mode if mode in MODES else WordEncounter.MODE_NEW


def _body(request):
    try:
        return json.loads(request.body.decode() or "{}")
    except (ValueError, UnicodeDecodeError):
        return {}


# Geri al için saklanan WordEncounter alanları (datetime'lar ISO metin olarak).
_GERI_AL_ALANLARI = ("last_verdict", "last_mode", "times_seen", "unknown_count", "known_count",
                     "misjudged_count", "egz_dogru", "egz_yanlis", "basamak", "son_basarili",
                     "son_bilinen_at", "sonraki_tekrar", "takipte", "listeye_sorulacak",
                     "last_seen_at")
_ZAMAN_ALANLARI = {"son_bilinen_at", "sonraki_tekrar", "last_seen_at"}
KARARLAR = (WordEncounter.KNOWN, WordEncounter.UNKNOWN, WordEncounter.MISJUDGED)


def _anlik_goruntu(kayit):
    if kayit is None:
        return None
    veri = {}
    for alan in _GERI_AL_ALANLARI:
        deger = getattr(kayit, alan)
        veri[alan] = deger.isoformat() if isinstance(deger, datetime) else deger
    return veri


def _goruntuden(veri):
    return {alan: (datetime.fromisoformat(d) if alan in _ZAMAN_ALANLARI and d else d)
            for alan, d in veri.items()}


@require_POST
def learnPassVerdict(request):
    """
    Kesinleşen kararı (18.1: ikinci kaydırma) ANINDA kaydeder ve sıradaki
    kartı döner. verdict: known ("Evet, eminim") / misjudged ("Hayır,
    yanılmışım") / unknown ("Bilmiyorum").

    Bilinmeyen kelime listeye EKLENMEZ (rapor 6.1): listede değilse
    `listeye_sorulacak` işaretlenir; oturum sonunda ya da bir sonraki
    girişte kullanıcıya sorulur.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth"}, status=403)

    payload = _body(request)
    run = _run_from(payload)
    kaynak = payload.get("kaynak")
    if kaynak not in KAYNAKLAR:
        kaynak = run if run in KAYNAKLAR else WordEncounter.MODE_NEW
    verdict = payload.get("verdict")
    if verdict not in KARARLAR:
        return JsonResponse({"error": "verdict"}, status=400)

    word = get_object_or_404(Word, id=payload.get("word_id") or 0)

    # --- Geri al için önceki hâli sakla ---
    onceki = WordEncounter.objects.filter(user=request.user, word=word).first()
    gecmis_kaydi = {"word_id": word.id, "verdict": verdict, "kaynak": kaynak,
                    "encounter": _anlik_goruntu(onceki)}

    kayit = tekrar.kaydet(request.user, word, verdict, kaynak)
    seri = seri_hesap.say(request.user, seri_hesap.LP)

    bilmiyor = verdict in (WordEncounter.UNKNOWN, WordEncounter.MISJUDGED)
    if bilmiyor and not kayit.listeye_sorulacak:
        if not UserWordLink.objects.filter(user=request.user, word=word).exists():
            kayit.listeye_sorulacak = True
            kayit.save(update_fields=["listeye_sorulacak"])

    # --- Sayaçlar ---
    stats = read_stats(request.session, run)
    stats["seen"] = stats.get("seen", 0) + 1
    anahtar = "unknown" if bilmiyor else "known"
    stats[anahtar] = stats.get(anahtar, 0) + 1
    write_stats(request.session, run, stats)

    gecmis = request.session.get(_history_key(run)) or []
    gecmis.append(gecmis_kaydi)
    request.session[_history_key(run)] = gecmis[-HISTORY_LIMIT:]
    request.session.modified = True

    kart = next_card(request.user, run, haric=_gosterilenler(request.session, run) + [word.id])
    _gosterildi(request.session, run, kart)

    return JsonResponse({
        "stats": stats,
        "answered": encounter_payload(word, request.user),
        "card": kart,
        "seri": seri,
    })


@require_POST
def learnPassUndo(request):
    """
    Son kaydı geri alır: kaydı eski hâline döndürür ve kartı tekrar
    gösterir. Hızlı kaydırılan bir ekranda yanlış yöne kaydırmak kaçınılmaz.
    Günün L&P sayacı da bir azalır (tamamlanmış gün geri alınmaz).
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth"}, status=403)

    run = _run_from(_body(request))
    gecmis = request.session.get(_history_key(run)) or []
    if not gecmis:
        return JsonResponse({"error": "empty"}, status=400)

    kayit = gecmis.pop()
    request.session[_history_key(run)] = gecmis
    request.session.modified = True

    word = Word.objects.filter(id=kayit["word_id"]).first()
    if word is None:
        return JsonResponse({"error": "missing"}, status=404)

    onceki = kayit["encounter"]
    if onceki is None:
        WordEncounter.objects.filter(user=request.user, word=word).delete()
    else:
        WordEncounter.objects.filter(user=request.user, word=word).update(**_goruntuden(onceki))

    # Günlükteki son kayıt da geri alınır: yanlış yöne kaydırılarak oluşmuş
    # bir kayıt basamak başına unutma ölçümünü bozar.
    son_kayit = (EncounterLog.objects
                 .filter(user=request.user, word=word, kind=EncounterLog.VERDICT)
                 .order_by("-created_at", "-id").first())
    if son_kayit is not None:
        son_kayit.delete()
    seri = seri_hesap.geri_al(request.user, seri_hesap.LP)

    stats = read_stats(request.session, run)
    stats["seen"] = max(0, stats.get("seen", 0) - 1)
    anahtar = ("unknown" if kayit.get("verdict") in (WordEncounter.UNKNOWN, WordEncounter.MISJUDGED)
               else "known")
    stats[anahtar] = max(0, stats.get(anahtar, 0) - 1)
    write_stats(request.session, run, stats)

    return JsonResponse({
        "stats": stats,
        "card": card_payload(word, request.user, kayit.get("kaynak")),
        "seri": seri,
    })


@require_POST
def learnPassBilinmeyenler(request):
    """
    "Bilmediğin N kelimeyi listene ekleyelim mi?" sorusunun cevabı.

    Gövde: {"islem": "ekle" | "gec" | "geri_al", "word_ids": [...],
            "eklenenler": [...] (yalnızca geri_al)}

      ekle     -> kelimeler listeye toplu eklenir, soru işareti kalkar.
      gec      -> "şimdilik hayır": işaret kalkar, bir daha sorulmaz.
      geri_al  -> ikisinin de "Geri al"ı: `eklenenler` listeden çıkar,
                  işaret geri konur.

    Yalnızca kullanıcının L&P'de karşılaştığı kelimeler kabul edilir;
    uç, keyfî kelimeleri listeye eklemenin arka kapısı olmasın.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth"}, status=403)

    payload = _body(request)
    islem = payload.get("islem")
    if islem not in ("ekle", "gec", "geri_al"):
        return JsonResponse({"error": "islem"}, status=400)

    def idler(anahtar):
        ham = payload.get(anahtar) or []
        if not isinstance(ham, list):
            return []
        return [int(i) for i in ham[:500] if str(i).isdigit()]

    kayitlar = WordEncounter.objects.filter(user=request.user, word_id__in=idler("word_ids"))
    gecerli = list(kayitlar.values_list("word_id", flat=True))

    if islem == "ekle":
        listede = set(UserWordLink.objects.filter(user=request.user, word_id__in=gecerli)
                      .values_list("word_id", flat=True))
        yeni = [i for i in gecerli if i not in listede]
        UserWordLink.objects.bulk_create(
            [UserWordLink(user=request.user, word_id=i) for i in yeni],
            ignore_conflicts=True,
        )
        kayitlar.update(listeye_sorulacak=False)
        return JsonResponse({"ok": True, "eklenenler": yeni, "sayi": len(yeni)})

    if islem == "gec":
        kayitlar.update(listeye_sorulacak=False)
        return JsonResponse({"ok": True})

    # geri_al
    geri = [i for i in idler("eklenenler") if i in set(gecerli)]
    UserWordLink.objects.filter(user=request.user, word_id__in=geri).delete()
    kayitlar.update(listeye_sorulacak=True)
    return JsonResponse({"ok": True})
