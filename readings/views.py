"""
Okumalar (rapor 8): tek işi odaklanıp okumak.

  /okumalar/                         ana sayfa: Kendi metinlerim + Kütüphane
  /okumalar/<metin-adi>/             kütüphane metni (misafire açık, dizine açık)
  /okumalar/metinlerim/<id>/         kendi metni (yalnızca sahibi; başkası 404)
  /okumalar/metinlerim/ekle/         PDF yükle ya da yapıştır (giriş gerekli)
  /okumalar/metinlerim/<id>/sil/     yumuşak silme ("Geri al"lı, onaysız)
  /okumalar/metinlerim/<id>/geri-al/ silmeyi geri alma

Okuma ekranında kelimeye dokununca anlam /api/kelime/ ucundan gelir (api.py).
"""

import re
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from LearnVocab.authgate import login_gate

from . import pdf as pdf_okuyucu
from .models import TOPICS, ReadingText, UserText


# Kullanıcı başına en çok kaç metin (çöptekiler hariç).
EN_COK_METIN = 100
# Yapıştırılan metin sınırları (PDF'in karakter sınırıyla aynı).
EN_AZ_KARAKTER = 20
EN_COK_KARAKTER = pdf_okuyucu.EN_COK_KARAKTER
# Silinen metin bu kadar süre çöpte kalır ("Geri al" için), sonra temizlenir.
COP_SURESI = timedelta(days=1)


def _ajax_mi(request):
    return request.headers.get("X-Requested-With") == "fetch"


def _copu_bosalt(user):
    """Kullanıcının bir günden eski silinmiş metinlerini kalıcı olarak siler."""
    UserText.objects.filter(owner=user, deleted_at__lt=timezone.now() - COP_SURESI).delete()


def okumalar(request):
    """Okumalar ana sayfası: Kendi metinlerim (girişli) + Kütüphane (herkese açık)."""
    konu = request.GET.get("konu") or ""
    kutuphane = ReadingText.objects.only("number", "slug", "title", "topic", "word_count", "cefr")
    konular = [{"anahtar": a, "ad": ad, "renk": renk} for a, ad, renk in TOPICS]
    if konu in {k["anahtar"] for k in konular}:
        kutuphane = kutuphane.filter(topic=konu)
    else:
        konu = ""

    metinlerim = []
    if request.user.is_authenticated:
        _copu_bosalt(request.user)
        metinlerim = list(UserText.objects.gorunen().filter(owner=request.user)
                          .only("id", "title", "source_kind", "word_count", "created_at"))

    kutuphane = list(kutuphane)
    return render(request, "pages/readings.html", {
        "active_page": "Okumalar",
        "kutuphane": kutuphane,
        "kutuphane_bos": not kutuphane and not konu,
        "konular": konular if (kutuphane or konu) else [],
        "secili_konu": konu,
        "metinlerim": metinlerim,
    })


def _metin_ozeti(metin, en_cok=155):
    """Arama sonucunda görünecek açıklama: metnin kendi ilk cümleleri."""
    ilk = (metin.paragraphs or [""])[0]
    return ilk if len(ilk) <= en_cok else ilk[:en_cok].rsplit(" ", 1)[0] + "…"


def kutuphane_metni(request, slug):
    metin = get_object_or_404(ReadingText, slug=slug)
    return render(request, "pages/readings/oku.html", {
        "active_page": "Okumalar",
        "meta_aciklama": _metin_ozeti(metin),
        "baslik": metin.title,
        "paragraflar": metin.paragraphs,
        "metin": metin,
        "kutuphane": True,
    })


@login_gate("Okumalar", "Kendi metinlerin yalnızca sana özel; görmek için giriş yapmalısın.")
def kendi_metnim(request, pk):
    # Başkasının metni ve çöpteki metin: 404 (varlığı bile belli olmasın).
    metin = get_object_or_404(UserText.objects.gorunen(), pk=pk, owner=request.user)
    return render(request, "pages/readings/oku.html", {
        "active_page": "Okumalar",
        "baslik": metin.title,
        "paragraflar": metin.paragraphs,
        "metin": metin,
        "kutuphane": False,
    })


# ---------------------------------------------------------------------------
# Metin ekleme
# ---------------------------------------------------------------------------

def _yapistirilani_duzenle(ham):
    """
    Yapıştırılan metni paragraflara ayırır. Web'den kopyalanan metinde
    paragraflar çoğu zaman tek satır sonuyla ayrılır; hiç boş satır yoksa
    her satır bir paragraf sayılır.
    """
    metin = (ham or "").replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    if "\n\n" not in metin.strip():
        metin = metin.replace("\n", "\n\n")
    paragraflar = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", metin)]
    return "\n\n".join(p for p in paragraflar if p)


def _varsayilan_baslik(metin):
    kelimeler = metin.split()
    baslik = " ".join(kelimeler[:8])
    return (baslik + "…") if len(kelimeler) > 8 else baslik


@login_gate("Okumalar", "Kendi metinlerini yükleyebilmek için giriş yapman gerekiyor.")
def metin_ekle(request):
    tur = request.POST.get("tur") or request.GET.get("tur") or "pdf"
    if tur not in ("pdf", "yapistir"):
        tur = "pdf"
    hata, baslik, yapistirilan = None, "", ""

    if request.method == "POST":
        baslik = (request.POST.get("baslik") or "").strip()[:200]
        yapistirilan = request.POST.get("metin") or ""

        if UserText.objects.gorunen().filter(owner=request.user).count() >= EN_COK_METIN:
            hata = (f"En çok {EN_COK_METIN} metin saklayabiliyorsun. Yenisini eklemek için "
                    "eskilerden birini silebilirsin.")
        elif tur == "pdf":
            dosya = request.FILES.get("dosya")
            if not dosya:
                hata = "Bir PDF dosyası seçer misin?"
            elif dosya.size > pdf_okuyucu.EN_BUYUK_BOYUT:
                hata = "Bu PDF çok büyük. En çok 10 MB'lık dosyaları okuyabiliyoruz."
            else:
                try:
                    # Dosya yalnızca bellekte okunur, saklanmaz.
                    metin, bilgi = pdf_okuyucu.pdf_metni(dosya.read())
                except pdf_okuyucu.PdfOkunamadi as e:
                    hata = str(e)
                else:
                    ad = re.sub(r"\.pdf$", "", dosya.name or "", flags=re.IGNORECASE)
                    kayit = UserText.objects.create(
                        owner=request.user, source_kind=UserText.SOURCE_PDF, body=metin,
                        title=baslik or bilgi["baslik"] or ad[:200] or _varsayilan_baslik(metin),
                        word_count=len(metin.split()))
                    if bilgi["kesildi"]:
                        messages.info(request, "PDF çok uzun olduğu için yalnızca ilk kısmını aldık.")
                    return redirect("readings_user_text", pk=kayit.pk)
        else:
            metin = _yapistirilani_duzenle(yapistirilan)
            if len(re.findall(r"[A-Za-z]", metin)) < EN_AZ_KARAKTER:
                hata = "Okumak için biraz daha uzun bir metin yapıştırır mısın?"
            elif len(metin) > EN_COK_KARAKTER:
                hata = (f"Bu metin çok uzun (en çok {EN_COK_KARAKTER:,} karakter). "
                        "Bir bölümünü yapıştırabilirsin.").replace(",", ".")
            else:
                kayit = UserText.objects.create(
                    owner=request.user, source_kind=UserText.SOURCE_PASTE, body=metin,
                    title=baslik or _varsayilan_baslik(metin),
                    word_count=len(metin.split()))
                return redirect("readings_user_text", pk=kayit.pk)

    return render(request, "pages/readings/ekle.html", {
        "active_page": "Okumalar",
        "tur": tur,
        "hata": hata,
        "baslik": baslik,
        "yapistirilan": yapistirilan,
        "en_cok_sayfa": pdf_okuyucu.EN_COK_SAYFA,
    }, status=400 if hata else 200)


# ---------------------------------------------------------------------------
# Silme ve geri alma (rapor 12.7: onay yok, "Geri al" var)
# ---------------------------------------------------------------------------

@login_required
@require_POST
def metnim_sil(request, pk):
    metin = get_object_or_404(UserText.objects.gorunen(), pk=pk, owner=request.user)
    metin.deleted_at = timezone.now()
    metin.save(update_fields=["deleted_at"])
    geri_al = reverse("readings_user_text_restore", args=[metin.pk])
    if _ajax_mi(request):
        return JsonResponse({"ok": True, "geri_al_url": geri_al})
    messages.info(request, f"“{metin.title}” silindi.")
    return redirect("readings")


@login_required
@require_POST
def metnim_geri_al(request, pk):
    metin = get_object_or_404(UserText, pk=pk, owner=request.user, deleted_at__isnull=False)
    metin.deleted_at = None
    metin.save(update_fields=["deleted_at"])
    if _ajax_mi(request):
        return JsonResponse({"ok": True})
    return redirect("readings")
