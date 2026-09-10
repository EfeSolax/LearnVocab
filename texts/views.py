import re

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from texts.models import Text
from words.models import UserWordLink
from .send_gemini import send_message_to_gemini


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------

# Gemini cevabının son satırı [p1, p2, ..., p10] formatında olmalı
# Bu kadar puan ve aşağıdaki dağılımı bekliyoruz.
EXPECTED_SCORE_COUNT = 10
DAILY_TEXT_INTERVAL = timedelta(days=1)
RECENT_LINKS_WINDOW = timedelta(days=7)

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


def _can_write_new_text(user):
    """Bir kullanıcı son 24 saat içinde yeni metin yazmış mı?"""
    last = Text.objects.filter(owner=user).order_by("-createdAt").first()
    if last is None:
        return True
    return (timezone.now() - last.createdAt) >= DAILY_TEXT_INTERVAL


# ---------------------------------------------------------------------------
# View'lar
# ---------------------------------------------------------------------------

@login_required
def newTextPage(request):
    if not _can_write_new_text(request.user):
        return redirect("profile_texts")

    links = _recent_links_for(request.user)
    return render(request, "pages/texts/newText.html", {"links": links})


@login_required
def createText(request):
    if request.method != "POST":
        return redirect("profile_texts")

    # Günde bir kez sınırını burada da uygulayalım (yarış koşullarına karşı)
    if not _can_write_new_text(request.user):
        messages.error(request, "Yeni bir metin yazmak için son metninizden bu yana 1 gün geçmesi gerekiyor.")
        return redirect("profile_texts")

    user_text = (request.POST.get("user_text") or "").strip()
    if not user_text:
        messages.error(request, "Lütfen değerlendirilebilecek İngilizce bir metin yazınız.")
        return redirect("profile_texts")

    links = list(_recent_links_for(request.user))
    words = [link.word for link in links]
    word_strings = [w.englishWord for w in words]

    # Gemini'ye gönder
    try:
        response = send_message_to_gemini(user_text, word_strings)
    except Exception as e:
        # send_gemini.py içinde yakalayamadığı bir hata olursa sayfa 500 vermesin
        print(f"[texts.createText] Gemini exception: {e}")
        messages.error(request, "Şu anda metin değerlendirme servisi cevap vermiyor. Lütfen biraz sonra tekrar deneyin.")
        return redirect("profile_texts")

    if not response or response == "Bu metin değerlendirilmedi.":
        messages.error(request, "Lütfen değerlendirilebilecek İngilizce bir metin yazınız.")
        return redirect("profile_texts")

    points, cleaned_response = _parse_gemini_scores(response)
    if points is None:
        print("[texts.createText] Gemini cevabı beklenen formatta değil:")
        print(response)
        messages.error(
            request,
            "Gemini şu anda başarılı bir şekilde metninizi değerlendiremedi. "
            "Lütfen birkaç dakika sonra tekrar deneyiniz."
        )
        return redirect("profile_texts")

    text = Text.objects.create(
        owner=request.user,
        content=user_text,
        score=sum(points),
        scores=str(points),
        response=cleaned_response,
    )
    if words:
        text.words.add(*words)

    return redirect("review_text", text_id=text.id)


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

    if (timezone.now() - text.createdAt) < DAILY_TEXT_INTERVAL:
        messages.error(request, "Oluşturulduktan sonra 1 gün geçmemiş metinler silinemez.")
        return redirect("profile_texts")

    text.delete()
    messages.success(request, "Metniniz başarılı bir şekilde silindi.")
    return redirect("profile_texts")


@login_required
def aboutGradingPage(request):
    return render(request, "pages/texts/aboutGrading.html")
