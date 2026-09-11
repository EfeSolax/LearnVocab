import logging
import re
import threading

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from LearnVocab import progress

from texts.models import Text
from texts import limits
from words.models import UserWordLink
from .send_gemini import (
    send_message_to_gemini,
    RATE_LIMIT_RESPONSE,
    UNAVAILABLE_RESPONSE,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------

# Gemini cevabının son satırı [p1, p2, ..., p10] formatında olmalı
# Bu kadar puan ve aşağıdaki dağılımı bekliyoruz.
EXPECTED_SCORE_COUNT = 10
RECENT_LINKS_WINDOW = timedelta(days=7)

# NOT: Metin yazma sıklığı kısıtı artık burada değil, texts/limits.py'de ve
# tek bir ayardan (TEXT_SUBMISSION_INTERVAL_MINUTES) yönetiliyor.

# Son satırdaki puanları yakalayan regex (boşluklu/boşluksuz çalışır)
SCORE_LINE_RE = re.compile(r"\[\s*(\d+(?:\s*,\s*\d+)*)\s*\]\s*$")


def _parse_gemini_scores(response_text):
    """
    Gemini cevabının son satırından puanları çıkarır.
    Başarılıysa (puan_listesi, ana_metin) döner; başarısızsa (None, response).
    """
    if not response_text:
        return None, response_text

    lines = response_text.splitlines()
    if not lines:
        return None, response_text

    last_line = lines[-1].strip()
    m = SCORE_LINE_RE.search(last_line)
    if not m:
        return None, response_text

    try:
        points = [int(x.strip()) for x in m.group(1).split(",")]
    except ValueError:
        return None, response_text

    if len(points) != EXPECTED_SCORE_COUNT:
        return None, response_text

    main_text = "\n".join(lines[:-1]).rstrip() + "\n"
    return points, main_text


def _recent_links_for(user):
    """Son 7 gün içinde listeye eklenen kelime bağlantıları."""
    start_date = timezone.now() - RECENT_LINKS_WINDOW
    return (
        UserWordLink.objects
        .filter(user=user, dateAdded__gte=start_date)
        .select_related("word")
    )


def _limit_message(user):
    """Kısıta takılan kullanıcıya gösterilecek mesaj."""
    return (
        f"Yeni bir metin yazabilmek için {limits.remaining_label(user)} beklemeniz gerekiyor."
    )


# ---------------------------------------------------------------------------
# View'lar
# ---------------------------------------------------------------------------

@login_required
def newTextPage(request):
    if not limits.can_write_new_text(request.user):
        messages.error(request, _limit_message(request.user))
        return redirect("profile_texts")

    links = _recent_links_for(request.user)
    return render(request, "pages/texts/newText.html", {"links": links})


# Değerlendirme sonucunun neden başarısız olduğunu anlatan mesajlar
EVALUATION_ERROR_MESSAGES = {
    "rate_limit": (
        "Metin değerlendirme servisinin kotası şu an dolu. "
        "Lütfen daha sonra tekrar deneyin. Metniniz kaydedilmedi, hakkınız harcanmadı."
    ),
    "unavailable": (
        "Değerlendirme servisi şu anda yoğun ve cevap veremedi. "
        "Birkaç dakika sonra tekrar deneyebilirsiniz; hakkınız harcanmadı."
    ),
    "unreachable": (
        "Metin değerlendirme servisine şu anda ulaşılamıyor. "
        "Sorun devam ederse lütfen bize bildirin."
    ),
    "refused": "Lütfen değerlendirilebilecek İngilizce bir metin yazınız.",
    "malformed": (
        "Gemini şu anda başarılı bir şekilde metninizi değerlendiremedi. "
        "Lütfen birkaç dakika sonra tekrar deneyiniz."
    ),
}


def _evaluation_event_handler(reporter):
    """Gemini olaylarını ilerleme çubuğuna çevirir."""
    if reporter is None:
        return None

    def handle(name, info):
        model_count = max(1, info.get("model_count", 1))
        model_index = info.get("model_index", 0)
        ratio = 0.15 + 0.65 * (model_index / model_count)

        if name == "attempt":
            if model_index == 0 and info.get("attempt", 1) == 1:
                reporter.set(ratio, "Metniniz değerlendirmeye gönderiliyor...")
            else:
                reporter.set(ratio, f"Yedek model deneniyor ({info.get('model')})...")
        elif name == "error":
            if info.get("kind") == "transient":
                reporter.message("Servis yoğun, birazdan yeniden denenecek...")
            elif info.get("kind") == "rate_limit":
                reporter.message("İstek kotası doldu...")
        elif name == "success":
            reporter.set(0.9, "Değerlendirme alındı, puanlar okunuyor...")

    return handle


def _evaluate_text(user, user_text, reporter=None):
    """
    Metni değerlendirtir ve kaydeder.

    Dönüş: (Text nesnesi, hata_kodu). Biri her zaman None olur.
    Hem normal istekte hem arka plan iş parçacığında kullanılıyor.
    """
    links = list(_recent_links_for(user))
    words = [link.word for link in links]
    word_strings = [w.englishWord for w in words]

    try:
        response = send_message_to_gemini(
            user_text, word_strings, on_event=_evaluation_event_handler(reporter)
        )
    except Exception:
        logger.exception("Gemini çağrısı beklenmedik şekilde hata verdi.")
        return None, "unreachable"

    if response == RATE_LIMIT_RESPONSE:
        return None, "rate_limit"
    if response == UNAVAILABLE_RESPONSE:
        return None, "unavailable"
    if not response:
        return None, "unreachable"
    if response == "Bu metin değerlendirilmedi.":
        return None, "refused"

    if reporter:
        reporter.set(0.95, "Puanlar hesaplanıyor...")

    points, cleaned_response = _parse_gemini_scores(response)
    if points is None:
        logger.warning("Gemini cevabı beklenen formatta değil:\n%s", response)
        return None, "malformed"

    text = Text.objects.create(
        owner=user,
        content=user_text,
        score=sum(points),
        scores=str(points),
        response=cleaned_response,
    )
    if words:
        text.words.add(*words)

    return text, None


def _run_text_evaluation(job_id, user_id, user_text):
    """Arka planda çalışan değerlendirme işi."""
    from django.contrib.auth import get_user_model
    from django.db import connection

    try:
        user = get_user_model().objects.get(pk=user_id)
        reporter = progress.Reporter(job_id, 5, 97)

        text, error = _evaluate_text(user, user_text, reporter=reporter)

        if error:
            progress.fail(job_id, EVALUATION_ERROR_MESSAGES.get(
                error, EVALUATION_ERROR_MESSAGES["malformed"]))
            return

        progress.finish(job_id, {"text_id": text.id}, "Değerlendirme hazır.")
    except Exception:
        logger.exception("Metin değerlendirme işi beklenmedik şekilde hata verdi.")
        progress.fail(job_id, EVALUATION_ERROR_MESSAGES["malformed"])
    finally:
        connection.close()


@login_required
@require_POST
def createText(request):
    """
    Metni değerlendirir.

    JavaScript ile (AJAX) çağrıldığında iş arka plana alınır ve ilerleme
    çubuğu için bir iş kimliği döner. JavaScript yoksa aynı iş senkron yapılır.
    """
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if not limits.can_write_new_text(request.user):
        message = _limit_message(request.user)
        if is_ajax:
            return JsonResponse({"error": message}, status=429)
        messages.error(request, message)
        return redirect("profile_texts")

    user_text = (request.POST.get("user_text") or "").strip()
    if not user_text:
        message = "Lütfen değerlendirilebilecek İngilizce bir metin yazınız."
        if is_ajax:
            return JsonResponse({"error": message}, status=400)
        messages.error(request, message)
        return redirect("profile_texts")

    if is_ajax:
        job_id = progress.create(request.user.id, message="Metniniz hazırlanıyor...")
        threading.Thread(
            target=_run_text_evaluation,
            args=(job_id, request.user.id, user_text),
            daemon=True,
        ).start()
        return JsonResponse({"job_id": job_id})

    text, error = _evaluate_text(request.user, user_text)

    if error:
        messages.error(request, EVALUATION_ERROR_MESSAGES.get(
            error, EVALUATION_ERROR_MESSAGES["malformed"]))
        return redirect("profile_texts")

    return redirect("review_text", text_id=text.id)


@login_required
def createTextProgress(request, job_id):
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
def createTextFinish(request, job_id):
    """İş bittiğinde sonucu mesaja çevirir ve nereye gidileceğini söyler."""
    job = progress.read(job_id)

    if job is None or job.get("owner_id") != request.user.id:
        return JsonResponse({"error": "İş bulunamadı."}, status=404)

    if job.get("state") == progress.STATE_RUNNING:
        return JsonResponse({"error": "İş hâlâ sürüyor."}, status=409)

    if job.get("state") == progress.STATE_FAILED:
        messages.error(request, job.get("message") or EVALUATION_ERROR_MESSAGES["malformed"])
        progress.delete(job_id)
        return JsonResponse({"redirect": reverse("profile_texts")})

    result = job.get("result") or {}
    progress.delete(job_id)

    text_id = result.get("text_id")
    target = reverse("review_text", args=[text_id]) if text_id else reverse("profile_texts")
    return JsonResponse({"redirect": target})


@login_required
def reviewText(request, text_id):
    # Kullanıcı sadece kendi metnini görüntüleyebilsin
    text = get_object_or_404(Text, id=text_id, owner=request.user)

    links = _recent_links_for(request.user)

    # scores alanı "[5, 21, 8, ...]" stringi olarak kaydedilmiş.
    raw_scores = (text.scores or "").strip()
    cleaned = raw_scores.replace("[", "").replace("]", "").replace(" ", "")
    parts = [p for p in cleaned.split(",") if p]

    try:
        scores = [int(p) for p in parts]
    except ValueError:
        scores = []

    # Beklenen 10 puanı doldur (eksikse 0, fazlaysa kırp)
    if len(scores) < EXPECTED_SCORE_COUNT:
        scores += [0] * (EXPECTED_SCORE_COUNT - len(scores))
    elif len(scores) > EXPECTED_SCORE_COUNT:
        scores = scores[:EXPECTED_SCORE_COUNT]

    # Template hala point1..point10 bekliyor; geriye dönük uyum için doldur
    point_context = {f"point{i+1}": scores[i] for i in range(EXPECTED_SCORE_COUNT)}

    context = {
        "text": text,
        **point_context,
        "context_point": sum(scores[0:5]),
        "language_point": sum(scores[5:10]),
        "links": links,
    }
    return render(request, "pages/texts/textReview.html", context)


@login_required
def removeText(request, text_id):
    # Sadece kendi metnini silebilsin
    text = get_object_or_404(Text, id=text_id, owner=request.user)

    # Silme kısıtı bilerek aynı süreye bağlı: aksi hâlde kullanıcı metnini
    # silip hemen yenisini yazarak sınırı atlayabilirdi.
    if not limits.can_delete(text):
        messages.error(
            request,
            f"Oluşturulduktan sonra {limits.interval_label()} geçmemiş metinler silinemez."
        )
        return redirect("profile_texts")

    text.delete()
    messages.success(request, "Metniniz başarılı bir şekilde silindi.")
    return redirect("profile_texts")


@login_required
def aboutGradingPage(request):
    return render(request, "pages/texts/aboutGrading.html")
