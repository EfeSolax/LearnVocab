"""
Çalışma görünümleri.

AKIŞ
----
    /quizzes/study/                 durum + "Çalışmaya başla"
    /quizzes/study/<id>/            tek soru  (GET)
                                    cevap + geri bildirim  (POST)
    /quizzes/study/<id>/finish/     oturum özeti
    /quizzes/progress/              ilerleme
    /quizzes/analysis/              kelime kelime analiz

Tek soru, tek ekran. Eski sistemde soru indeksi adresin içindeydi
(`/quiz/12/3/`) ve kullanıcı geri tuşuyla soruları gezebiliyordu —
hatırlama denemesinin tekrarlanabilir olması onu hatırlama denemesi
olmaktan çıkarır. Şimdi sıradaki soru sunucuda: adresin içinde soru
numarası yok, geri gitmek yeni bir soru getirmiyor.

GERİ BİLDİRİM AYNI SAYFADA
--------------------------
Cevap POST edilir, aynı şablon bu kez geri bildirim paneliyle basılır.
Sonraki soruya geçmek ayrı bir tıklama ister. Otomatik geçmemesinin
sebebi: düzeltmeyi okumaya vakit bırakmak. Öğrenmenin olduğu an orası.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import (
    Count, ExpressionWrapper, F, FloatField, Sum,
)
from django.db.models.functions import Cast, NullIf
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from LearnVocab import pagination
from LearnVocab.authgate import login_gate
from words.models import UserWordLink, WordList

from . import build, session as oturum
from .analysis import (  # noqa: F401 — eski içe aktarmalar için yeniden dışa veriliyor
    classify_links_by_priority, declaration_summary, declared_stuck,
    encounter_signals, recent_confident_errors, weak_items,
)
from .aspects import Aspect
from .models import (
    ItemState, ReviewItem, ReviewLog, SessionMode, StudySession,
)

ANALYSIS_PER_PAGE_OPTIONS = (25, 50, 100, 200)
ANALYSIS_DEFAULT_PER_PAGE = 50

GATE_NOTE = ("Çalışma senin kendi kelimelerinle ve kendi geçmişinle "
             "yürüdüğü için giriş yapman gerekiyor.")


# ----------------------------------------------------------------------
# Çalışma
# ----------------------------------------------------------------------

@login_gate("Çalışma", GATE_NOTE)
def studyHome(request):
    """
    Çalışma ana sayfası: bugün ne var, ne kadar birikmiş.

    Sayfada soru tipi seçeneği YOK. Bilinçli: kullanıcı hangi tipte
    çalışacağını seçtiğinde kendini iyi hissettiren tipi seçer.
    Seçilebilen tek şey oturumun KAPSAMI (hepsi / bir liste /
    zorlandıkların), çünkü bu bir kolaylık tercihi, zorluk tercihi değil.
    """
    user = request.user

    # Kelime eklenmiş ama kart açılmamışsa burada tamamlanıyor; böylece
    # sayfadaki sayılar gerçeği gösteriyor.
    build.ensure_all_entry_items(user)

    ozet = oturum.summary_for(user)

    # Yarım kalmış oturum varsa ona devam etmeyi öner.
    devam = (StudySession.objects
             .filter(user=user, finished_at=None)
             .exclude(queue=[])
             .first())

    return render(request, "pages/quizzes/studyHome.html", {
        "active_page": "Çalışma",
        "exercise_tab": "quizzes",
        "summary": ozet,
        "resume_session": devam,
        "word_lists": WordList.objects.filter(owner=user),
        "has_items": ozet["total_items"] > 0,
    })


@require_POST
@login_required
def studyStart(request):
    """Yeni oturum kurar ve ilk soruya götürür."""
    mod = request.POST.get("mode") or SessionMode.DUE
    if mod not in dict(SessionMode.choices):
        mod = SessionMode.DUE

    liste_id = request.POST.get("list_id") or None
    if liste_id:
        try:
            liste_id = int(liste_id)
        except (TypeError, ValueError):
            liste_id = None
        else:
            # Başkasının listesiyle oturum açılmasın.
            if not WordList.objects.filter(id=liste_id, owner=request.user).exists():
                liste_id = None

    calisma = oturum.start(request.user, mode=mod, list_id=liste_id)

    if not calisma.queue:
        calisma.finish()
        messages.info(request, "Şu an sırası gelen kart yok. Yarın görüşürüz.")
        return redirect("study_home")

    return redirect("study_run", session_id=calisma.id)


@login_required
def studyRun(request, session_id):
    """Tek soruluk ekran. GET soru verir, POST cevabı işler."""
    calisma = get_object_or_404(StudySession, id=session_id, user=request.user)

    if request.method == "POST":
        return _cevabi_isle(request, calisma)

    if calisma.is_finished or not calisma.queue:
        return redirect("study_finish", session_id=calisma.id)

    item, soru = oturum.next_question(calisma)
    if soru is None:
        return redirect("study_finish", session_id=calisma.id)

    return render(request, "pages/quizzes/studyRun.html", {
        "active_page": "Çalışma",
        "session": calisma,
        "item": item,
        "question": soru,
        "progress": _ilerleme(calisma),
    })


def _cevabi_isle(request, calisma):
    item_id = request.POST.get("item_id")
    item = ReviewItem.objects.filter(id=item_id, user=request.user).first()
    if item is None:
        return redirect("study_run", session_id=calisma.id)

    saniye = request.POST.get("seconds")
    try:
        saniye = float(saniye) if saniye else None
    except (TypeError, ValueError):
        saniye = None
    # Sekmeyi açık bırakıp dönen kullanıcı "çok yavaş" sayılmasın:
    # makul bir üst sınırın üstündeki süreler ölçülmemiş kabul ediliyor.
    if saniye is not None and (saniye <= 0 or saniye > 300):
        saniye = None

    sonuc = oturum.answer(
        calisma, item,
        user_input=request.POST.get("answer", ""),
        seconds=saniye,
        used_hint=request.POST.get("used_hint") == "1",
    )

    if not sonuc.get("ok"):
        return redirect("study_run", session_id=calisma.id)

    _kelime_sayaclarini_guncelle(request.user, item, sonuc["correct"])

    return render(request, "pages/quizzes/studyRun.html", {
        "active_page": "Çalışma",
        "session": calisma,
        "item": item,
        "question": sonuc["question"],
        "feedback": sonuc,
        "user_answer": _cevabi_goster(sonuc["question"], request.POST.get("answer", "")),
        "progress": _ilerleme(calisma),
    })


def _cevabi_goster(soru, ham_cevap):
    """
    Kullanıcının verdiği cevabı okunabilir hâle getirir.

    Çoktan seçmelide form "A" gönderiyor; geri bildirimde "Senin cevabın: A"
    yazmak hiçbir şey anlatmıyor — öğrenci bir soru önce neyi işaretlediğini
    şıkkın HARFİYLE hatırlamıyor, METNİYLE hatırlıyor. Yanlış cevabın ne
    olduğunu görmek düzeltmenin yarısı.
    """
    ham_cevap = (ham_cevap or "").strip()
    if not ham_cevap or soru.is_typed:
        return ham_cevap
    for secenek in soru.options:
        if secenek["key"] == ham_cevap.upper():
            return secenek["text"]
    return ham_cevap


def _kelime_sayaclarini_guncelle(user, item, dogru):
    """
    UserWordLink sayaçlarını da güncel tutar.

    Yeni sistem bu sayaçları KULLANMIYOR (zamanlama kart bazında ve
    kararlılık üzerinden yapılıyor). Yine de güncelleniyorlar çünkü
    analiz sayfası ve Öğren-Geç'in öncelik sıralaması onlara bakıyor;
    iki sistem aynı anda yaşarken birinin verisi donmuş olmamalı.
    """
    from django.db.models import F as _F

    baglar = UserWordLink.objects.filter(user=user, word_id=item.word_id)
    if dogru:
        baglar.update(correctCount=_F("correctCount") + 1)
    else:
        baglar.update(wrongCount=_F("wrongCount") + 1)


def _ilerleme(calisma):
    """Üstteki ilerleme çubuğu için yüzde."""
    plan = max(calisma.planned_count, 1)
    yapilan = min(calisma.answered_count, plan)
    return {
        "answered": calisma.answered_count,
        "planned": calisma.planned_count,
        "remaining": len(calisma.queue or []),
        "percent": round(100 * yapilan / plan),
    }


@login_required
def studyFinish(request, session_id):
    """
    Oturum özeti.

    Ekranda yüzde YOK — bilinçli. Yüzde bir sınav çıktısıdır ve yanlış
    şeyi ödüllendirir: yüzdesini yüksek tutmak isteyen öğrenci kolay
    kartları çalışır, zorlarından kaçar. Onun yerine gösterilen şey
    NE OLDUĞU: kaç kart ilerledi, hangileri takıldı, yarın kaç kart var.
    """
    calisma = get_object_or_404(StudySession, id=session_id, user=request.user)
    ozet = oturum.finish(calisma)

    yarin = timezone.now() + timezone.timedelta(days=1)
    yarinki = (ReviewItem.objects
               .filter(user=request.user, due_at__lte=yarin)
               .exclude(state=ItemState.NEW)
               .count())

    return render(request, "pages/quizzes/studyFinish.html", {
        "active_page": "Çalışma",
        "exercise_tab": "quizzes",
        "session": calisma,
        "missed_words": ozet["missed_words"],
        "tomorrow_count": yarinki,
        "summary": oturum.summary_for(request.user),
    })


def legacyRedirect(request):
    """Eski quiz adreslerinden çalışma sayfasına."""
    return redirect("study_home")


# ----------------------------------------------------------------------
# İlerleme
# ----------------------------------------------------------------------

@login_gate("İlerleme", GATE_NOTE)
def studyProgress(request):
    """
    İlerleme sayfası.

    Üç şey gösteriliyor ve üçü de bilinçli seçildi:

    1. KALICI BİLGİ — kartların hatırlanabilirlik toplamı. Çalışılmadığında
       DÜŞER. Sürekli artan bir sayaç (çalışılan kelime sayısı) öğrenciye
       yanlış bir güvenlik hissi verir; gerçekte bilgi eriyor.
    2. BOYUT DAĞILIMI — "tanıdığın 400 kelimenin 90'ını üretebiliyorsun".
       Tek bir "kelime sayısı" rakamı bu farkı gizler.
    3. SERİ — kaç gündür çalışıyor. Doğru cevap serisi değil, GÜN serisi:
       doğru cevabı ödüllendiren bir seri, öğrenciyi zor kart açmaktan
       caydırır.
    """
    user = request.user

    dagilim = build.aspect_breakdown(user)
    # Boyutlar merdiven sırasına göre gösteriliyor.
    sirali = [dagilim[a] for a in Aspect.values if a in dagilim]

    son_gunler = (ReviewLog.objects
                  .filter(user=user)
                  .order_by("-answered_at")[:200])

    return render(request, "pages/quizzes/studyProgress.html", {
        "active_page": "İlerleme",
        "exercise_tab": "quizzes",
        "summary": oturum.summary_for(user),
        "breakdown": sirali,
        "weak": weak_items(user, limit=15),
        "confident_errors": recent_confident_errors(user, limit=8),
        "declared_stuck": declared_stuck(user, limit=10),
        "declarations": declaration_summary(user),
        "recent_sessions": StudySession.objects.filter(user=user)[:10],
        "log_count": ReviewLog.objects.filter(user=user).count(),
        "recent_logs": son_gunler[:20],
    })


# ----------------------------------------------------------------------
# Analiz (eski sayfa, kelime bazında)
# ----------------------------------------------------------------------

HUE_MAX = 130


def analysis_rows(page_object_list):
    """
    Sayfadaki bağlantıları satıra çevirir.

    Satırda bilinçli olarak yalnızca üç şey var: kelimenin kendisi, kaç kez
    çalışıldığı ve doğruluk oranı. Deneme sayısı olmadan oran yanıltıcı olurdu
    (2 denemede %50 ile 40 denemede %50 aynı şey değil).
    """
    rows = []
    for link in page_object_list:
        accuracy = link.accuracy or 0.0
        rows.append({
            "word": link.word,
            "attempts": link.attempts,
            "accuracy": round(accuracy),
            "hue": round(accuracy * HUE_MAX / 100),
        })
    return rows


@login_gate("Analiz", "Analiz senin kendi çalışma geçmişini gösterdiği için giriş yapman gerekiyor.")
def wordAnalysis(request):
    """
    Hangi kelimeyi iyi bildiğini, hangisinde takıldığını gösteren liste.

    Sıralama en çok yanlış yapılandan en çok doğru yapılana doğru. Aynı orana
    sahip kelimelerde çok denenmiş olan öne alınıyor: 20 denemede %50, 2
    denemede %50'den daha güvenilir bir "bunu bilmiyorsun" sinyali.
    """
    user = request.user

    links = (
        UserWordLink.objects.filter(user=user)
        .select_related("word")
        .annotate(attempts=F("correctCount") + F("wrongCount"))
        .filter(attempts__gt=0)
        .annotate(
            accuracy=ExpressionWrapper(
                Cast(F("correctCount"), FloatField()) * 100.0
                / NullIf(F("correctCount") + F("wrongCount"), 0),
                output_field=FloatField(),
            )
        )
        .order_by("accuracy", "-attempts", "word__text")
    )

    per_page = pagination.resolve_per_page(
        request, ANALYSIS_PER_PAGE_OPTIONS, ANALYSIS_DEFAULT_PER_PAGE
    )
    paginator = Paginator(links, per_page)
    page_obj = paginator.get_page(request.GET.get("page") or 1)

    toplamlar = UserWordLink.objects.filter(user=user).aggregate(
        dogru=Sum("correctCount"), yanlis=Sum("wrongCount")
    )
    dogru = toplamlar["dogru"] or 0
    yanlis = toplamlar["yanlis"] or 0
    toplam_deneme = dogru + yanlis

    context = {
        "active_page": "Analiz",
        "exercise_tab": "analysis",
        "rows": analysis_rows(page_obj.object_list),
        "studied_count": paginator.count,
        "untouched_count": UserWordLink.objects.filter(
            user=user, correctCount=0, wrongCount=0
        ).count(),
        "total_attempts": toplam_deneme,
        "overall_accuracy": round(dogru * 100 / toplam_deneme) if toplam_deneme else 0,
    }
    context.update(pagination.pagination_context(
        page_obj, paginator,
        params=[],
        per_page=per_page,
        per_page_options=ANALYSIS_PER_PAGE_OPTIONS,
        default_per_page=ANALYSIS_DEFAULT_PER_PAGE,
    ))

    return render(request, "pages/quizzes/wordAnalysis.html", context)
