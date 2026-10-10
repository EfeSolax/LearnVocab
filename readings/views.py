"""
Okumalar (rapor 8): tek işi odaklanıp okumak.

  /okumalar/                         ana sayfa: Kendi metinlerim + Kütüphane
  /okumalar/<metin-adi>/             kütüphane metni (misafire açık, dizine açık)
  /okumalar/metinlerim/<id>/         kendi metni (yalnızca sahibi; başkası 404)
  /okumalar/metinlerim/ekle/         PDF yükle ya da yapıştır (giriş gerekli)
  /okumalar/metinlerim/<id>/sil/     çöp kutusuna atar ("Geri al"lı, onaysız)
  /okumalar/metinlerim/<id>/geri-al/ çöpten geri alır
  /okumalar/metinlerim/<id>/kalici-sil/  çöpteki metni kalıcı olarak siler

Sınırlar (rapor 18.24): kullanıcı başına 100 metin, bunların en çok 15'i PDF;
PDF başına 400 sayfa ve 50 MB. Çöpteki metinler sınıra sayılmaz ve 1 hafta
sonra kendiliğinden silinir. Gövdeler diskte durur (readings/depo.py).
Uzun metinler bölüm bölüm gösterilir (?bolum=2).

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
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_POST

from LearnVocab import sinir
from LearnVocab.authgate import login_gate

from . import pdf as pdf_okuyucu
from .models import TOPICS, ReadingText, UserText


# Kullanıcı başına en çok kaç metin ve bunların en çok kaçı PDF (çöptekiler hariç).
EN_COK_METIN = 100
EN_COK_PDF = 15

# Ağır iş sınırı (rapor 18.37): PDF isteğin içinde okunur (en çok 400 sayfa,
# birkaç saniye). Aynı anda en çok ESZAMANLI_PDF dosya okunur; kullanıcı başına
# saatte PDF_SAATTE yükleme. Süreç okurken ölürse yer PDF_EN_UZUN sn sonra boşalır.
ESZAMANLI_PDF = 2
PDF_SAATTE = 20
PDF_EN_UZUN = 60
# Yapıştırılan metin sınırları.
EN_AZ_KARAKTER = 20
EN_COK_KARAKTER = 150_000
# Silinen metin bu kadar süre çöp kutusunda kalır, sonra kalıcı olarak silinir.
COP_SURESI = timedelta(days=7)
# Okuma ekranında bir bölümün yaklaşık uzunluğu (kelime). 400 sayfalık bir
# kitap tek seferde yüklenmez; bölüm paragraf sınırında biter.
BOLUM_KELIME = 1500


def _ajax_mi(request):
    return request.headers.get("X-Requested-With") == "fetch"


def _copu_bosalt(user):
    """Kullanıcının çöpte bir haftayı dolduran metinlerini kalıcı olarak siler."""
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

    metinlerim, cop = [], []
    if request.user.is_authenticated:
        _copu_bosalt(request.user)
        metinlerim = list(UserText.objects.gorunen().filter(owner=request.user)
                          .only("id", "title", "source_kind", "word_count", "created_at"))
        cop = list(UserText.objects.filter(owner=request.user, deleted_at__isnull=False)
                   .order_by("-deleted_at")
                   .only("id", "title", "source_kind", "word_count", "deleted_at"))
        simdi = timezone.now()
        for m in cop:
            m.kalan_gun = max(1, (m.deleted_at + COP_SURESI - simdi).days + 1)

    kutuphane = list(kutuphane)
    return render(request, "pages/readings.html", {
        "active_page": "Okumalar",
        "kutuphane": kutuphane,
        "kutuphane_bos": not kutuphane and not konu,
        "konular": konular if (kutuphane or konu) else [],
        "secili_konu": konu,
        "metinlerim": metinlerim,
        "cop": cop,
        "cop_gun": COP_SURESI.days,
    })


def bolumle(paragraflar, hedef=BOLUM_KELIME):
    """Paragrafları yaklaşık `hedef` kelimelik bölümlere ayırır: [[p, p…], …]."""
    bolumler, simdiki, sayi = [], [], 0
    for p in paragraflar:
        simdiki.append(p)
        sayi += len(p.split())
        if sayi >= hedef:
            bolumler.append(simdiki)
            simdiki, sayi = [], 0
    if simdiki:
        bolumler.append(simdiki)
    return bolumler or [[]]


def _bolum_baglami(request, paragraflar):
    """Okuma ekranı için: o bölümün paragrafları ve önceki/sonraki bölüm."""
    bolumler = bolumle(paragraflar)
    try:
        no = int(request.GET.get("bolum") or 1)
    except ValueError:
        no = 1
    no = min(max(no, 1), len(bolumler))
    return {
        "paragraflar": bolumler[no - 1],
        "bolum": no,
        "bolum_sayisi": len(bolumler),
        "onceki_bolum": no - 1 if no > 1 else None,
        "sonraki_bolum": no + 1 if no < len(bolumler) else None,
    }


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
        "metin": metin,
        "kutuphane": True,
        # Okuma sonu (defter teması, rapor 18.12): kütüphanedeki sıradaki metin, sonda başa döner.
        "siradaki": (ReadingText.objects.filter(number__gt=metin.number).order_by("number").first()
                     or ReadingText.objects.exclude(pk=metin.pk).order_by("number").first()),
        **_bolum_baglami(request, metin.paragraphs),
    })


@login_gate(gettext_lazy("Okumalar"), gettext_lazy("Kendi metinlerin yalnızca sana özel; görmek için giriş yapmalısın."))
def kendi_metnim(request, pk):
    # Başkasının metni ve çöpteki metin: 404 (varlığı bile belli olmasın).
    metin = get_object_or_404(UserText.objects.gorunen(), pk=pk, owner=request.user)
    return render(request, "pages/readings/oku.html", {
        "active_page": "Okumalar",
        "baslik": metin.title,
        "metin": metin,
        "kutuphane": False,
        **_bolum_baglami(request, metin.paragraphs),
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


@login_gate(gettext_lazy("Okumalar"), gettext_lazy("Kendi metinlerini yükleyebilmek için giriş yapman gerekiyor."))
def metin_ekle(request):
    tur = request.POST.get("tur") or request.GET.get("tur") or "pdf"
    if tur not in ("pdf", "yapistir"):
        tur = "pdf"
    hata, baslik, yapistirilan = None, "", ""
    if request.method != "POST":
        # Telefonda "Paylaş → LearnVocab" ile gelen uzun metin (LearnVocab/paylas.py).
        from LearnVocab.paylas import OTURUM_ANAHTARI
        yapistirilan = request.session.pop(OTURUM_ANAHTARI, "")
        if yapistirilan:
            tur = "yapistir"

    if request.method == "POST":
        baslik = (request.POST.get("baslik") or "").strip()[:200]
        yapistirilan = request.POST.get("metin") or ""

        mevcut = UserText.objects.gorunen().filter(owner=request.user)
        if mevcut.count() >= EN_COK_METIN:
            hata = _("En çok %(n)s metin saklayabiliyorsun. Yenisini eklemek için "
                     "eskilerden birini silebilirsin.") % {"n": EN_COK_METIN}
        elif tur == "pdf" and mevcut.filter(source_kind=UserText.SOURCE_PDF).count() >= EN_COK_PDF:
            hata = _("En çok %(n)s PDF saklayabiliyorsun. Yenisini eklemek için eski "
                     "PDF'lerden birini silebilir ya da metni yapıştırabilirsin.") % {"n": EN_COK_PDF}
        elif tur == "pdf":
            dosya = request.FILES.get("dosya")
            if not dosya:
                hata = _("Bir PDF dosyası seçer misin?")
            elif dosya.size > pdf_okuyucu.EN_BUYUK_BOYUT:
                hata = _("Bu PDF çok büyük. En çok %(mb)s MB'lık dosyaları okuyabiliyoruz.") % {
                    "mb": pdf_okuyucu.EN_BUYUK_BOYUT_MB}
            elif sinir.asildi(f"pdf:{request.user.pk}", PDF_SAATTE, 3600):
                hata = _("Bir saatte en çok %(n)s PDF yükleyebilirsin. Biraz sonra tekrar dener misin?") % {
                    "n": PDF_SAATTE}
            elif (yer := sinir.yer_al("pdf", ESZAMANLI_PDF, PDF_EN_UZUN)) is None:
                hata = _("Şu an çok yoğunuz. Birkaç saniye sonra yeniden dener misin?")
            else:
                try:
                    # Dosya yalnızca bellekte okunur, saklanmaz.
                    metin, bilgi = pdf_okuyucu.pdf_metni(dosya.read())
                except pdf_okuyucu.PdfOkunamadi as e:
                    hata = str(e)
                finally:
                    sinir.yer_birak("pdf", yer)
                if not hata:
                    ad = re.sub(r"\.pdf$", "", dosya.name or "", flags=re.IGNORECASE)
                    kayit = UserText.objects.create(
                        owner=request.user, source_kind=UserText.SOURCE_PDF, body=metin,
                        title=baslik or bilgi["baslik"] or ad[:200] or _varsayilan_baslik(metin),
                        word_count=len(metin.split()))
                    if bilgi["kesildi"]:
                        messages.info(request, _("PDF çok uzun olduğu için yalnızca ilk kısmını aldık."))
                    return redirect("readings_user_text", pk=kayit.pk)
        else:
            metin = _yapistirilani_duzenle(yapistirilan)
            if len(re.findall(r"[A-Za-z]", metin)) < EN_AZ_KARAKTER:
                hata = _("Okumak için biraz daha uzun bir metin yapıştırır mısın?")
            elif len(metin) > EN_COK_KARAKTER:
                hata = _("Bu metin çok uzun (en çok %(n)s karakter). Bir bölümünü yapıştırabilirsin.") % {
                    "n": f"{EN_COK_KARAKTER:,}".replace(",", ".")}
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
        "en_buyuk_mb": pdf_okuyucu.EN_BUYUK_BOYUT_MB,
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


@login_required
@require_POST
def metnim_kalici_sil(request, pk):
    """Çöp kutusundaki metni kalıcı olarak siler (geri alınamaz; dosyası da silinir)."""
    metin = get_object_or_404(UserText, pk=pk, owner=request.user, deleted_at__isnull=False)
    baslik = metin.title
    metin.delete()
    if _ajax_mi(request):
        return JsonResponse({"ok": True})
    messages.info(request, _("“%(baslik)s” kalıcı olarak silindi.") % {"baslik": baslik})
    return redirect("readings")
