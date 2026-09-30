"""
Yazma bölümü (ürün raporu 9): Yazma ana sayfası (Yazılarım), serbest yazma,
değerlendirme görünümü ve "Diyalogda doğru kelime".

Girişsiz ziyaretçi için bölüm kapalı: sayfalar @login_gate ile "önce giriş
yap" ekranını gösterir (rapor 2.3); veri değiştiren uçlar @login_required.
"""

import logging
import random
import re
import threading
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from LearnVocab import progress
from LearnVocab.authgate import login_gate
from texts import degerlendirme as dg
from texts import diyalog as dy
from texts import limits
from texts.konular import konu_basligi, konular_listesi
from texts.models import (
    Diyalog, DiyalogCevabi, Sertlik, Text, YaziDurumu, YazmaAyari,
)
from words.models import UserWordLink

logger = logging.getLogger(__name__)

GIRIS_ACIKLAMASI = "Yazdıkların hesabına kaydedildiği için giriş yapman gerekiyor."

# Metin sınırları (karakter). Görev 3–8 cümle; cümle sayısı tarayıcıda
# yol gösterici olarak sayılıyor, sunucu yalnızca uç değerleri reddediyor.
EN_AZ_KARAKTER = 20
EN_COK_KARAKTER = 1500

ONERI_SAYISI = 5
YAKIN_ZAMAN = timedelta(days=7)

SERTLIK_ACIKLAMALARI = (
    (Sertlik.NAZIK, "Nazik", "Yalnızca anlamı bozan hatalar, en çok 3."),
    (Sertlik.NORMAL, "Normal", "Dilbilgisi ve kelime hataları, en çok 6."),
    (Sertlik.TITIZ, "Titiz", "Noktalama, büyük harf ve resmiyet de dahil."),
)

SONUC_MESAJLARI = {
    dg.TAMAM: (messages.SUCCESS, "Metnin değerlendirildi."),
    dg.UYGUN_DEGIL: (messages.WARNING,
                     "Bu metni değerlendiremedik. İngilizce, birkaç cümlelik bir metin yazdığından emin ol."),
    dg.KOTA: (messages.WARNING,
              "Değerlendirme servisinin kotası şu an dolu. Metnin kaydedildi; "
              "biraz sonra kendimiz yeniden deneyeceğiz."),
    dg.SERVIS: (messages.WARNING,
                "Değerlendirme servisi şu an cevap veremedi. Metnin kaydedildi; "
                "biraz sonra kendimiz yeniden deneyeceğiz."),
    dg.YOGUN: (messages.WARNING,
               "Şu an çok yoğunuz. Metnin kaydedildi; biraz sonra tekrar dene "
               "ya da değerlendirmeyi bize bırak."),
    dg.YAPILANDIRMA: (messages.WARNING,
                      "Değerlendirme servisine şu an ulaşılamıyor. Metnin kaydedildi; "
                      "sorun giderilince değerlendireceğiz."),
    dg.BOZUK: (messages.WARNING,
               "Değerlendirme bu sefer düzgün gelmedi. Metnin kaydedildi; "
               "biraz sonra yeniden deneyeceğiz."),
}


def _mesaj_ekle(request, sonuc):
    seviye, metin = SONUC_MESAJLARI.get(sonuc, SONUC_MESAJLARI[dg.BOZUK])
    messages.add_message(request, seviye, metin)


def _yazilar(user):
    return Text.objects.filter(owner=user, silindi__isnull=True)


# ---------------------------------------------------------------------------
# Yazma ana sayfası
# ---------------------------------------------------------------------------

def yazmaSayfasi(request):
    # Misafir (rapor 18.3): serbest yazma yok, yalnızca diyalog egzersizi ve
    # tek bir giriş daveti.
    if not request.user.is_authenticated:
        return render(request, "pages/texts/yazma.html", {"misafir": True})

    yazilar = list(_yazilar(request.user).order_by("-createdAt"))
    for yazi in yazilar:
        yazi.puan_yazisi = dg.puan_yazisi(yazi.puan)

    silinen = None
    silindi_id = request.GET.get("silindi")
    if silindi_id and silindi_id.isdigit():
        silinen = Text.objects.filter(owner=request.user, pk=silindi_id,
                                      silindi__isnull=False).values_list("pk", flat=True).first()

    return render(request, "pages/texts/yazma.html", {
        "yazilar": yazilar,
        "yazabilir": limits.yazabilir_mi(request.user),
        "kalan_hak": limits.kalan_hak(request.user),
        "gunluk_limit": limits.gunluk_limit(),
        "sinir_mesaji": limits.sinir_mesaji(),
        "silinen": silinen,
    })


# ---------------------------------------------------------------------------
# Serbest yazma
# ---------------------------------------------------------------------------

def kullanmayi_dene(user, adet=ONERI_SAYISI):
    """
    Listeden 3–5 "kullanmayı dene" kelimesi: önce son 7 günde eklenenler,
    yetmezse listenin geri kalanından rastgele.
    """
    linkler = UserWordLink.objects.filter(user=user)
    yakin = list(linkler.filter(dateAdded__gte=timezone.now() - YAKIN_ZAMAN)
                 .order_by("-dateAdded").values_list("word_id", flat=True)[:30])
    secilen = random.sample(yakin, min(adet, len(yakin)))
    if len(secilen) < adet:
        secilen += list(linkler.exclude(word_id__in=yakin).order_by("?")
                        .values_list("word_id", flat=True)[:adet - len(secilen)])

    from words.models import Word
    kelimeler = {w.id: w for w in Word.objects.filter(id__in=secilen).prefetch_related("meanings")}
    sonuc = []
    for wid in secilen:
        kelime = kelimeler.get(wid)
        if kelime is None:
            continue
        anlamlar = sorted(kelime.meanings.all(), key=lambda m: (m.sort_order, m.id))
        kelime.ilk_anlam = anlamlar[0].meaning_tr if anlamlar else ""
        sonuc.append(kelime)
    return sonuc


@login_gate("Yazılar", GIRIS_ACIKLAMASI)
def newTextPage(request):
    yazabilir = limits.yazabilir_mi(request.user)
    return render(request, "pages/texts/newText.html", {
        "yazabilir": yazabilir,
        "sinir_mesaji": limits.sinir_mesaji(),
        "kalan_hak": limits.kalan_hak(request.user),
        "oneriler": kullanmayi_dene(request.user) if yazabilir else [],
        "konular": konular_listesi(),
        "sertlik": YazmaAyari.sertlik_of(request.user),
        "sertlikler": SERTLIK_ACIKLAMALARI,
        "en_az": EN_AZ_KARAKTER,
        "en_cok": EN_COK_KARAKTER,
    })


def _girdiyi_dogrula(request):
    """(metin, hata_mesajı) — hata yoksa ikinci eleman None."""
    metin = (request.POST.get("user_text") or "").strip()
    metin = re.sub(r"\r\n?", "\n", metin)
    if len(metin) < EN_AZ_KARAKTER:
        return metin, "Birkaç cümlelik İngilizce bir metin yaz (3–8 cümle)."
    if len(metin) > EN_COK_KARAKTER:
        return metin, f"Metin biraz uzun oldu. {EN_COK_KARAKTER} karakteri geçmesin (3–8 cümle yeter)."
    return metin, None


def _yazi_olustur(request, metin):
    sertlik = dg.sertlik_gecerli(request.POST.get("sertlik"))
    YazmaAyari.objects.update_or_create(user=request.user, defaults={"sertlik": sertlik})

    yazi = Text.objects.create(
        owner=request.user,
        content=metin,
        durum=YaziDurumu.BEKLIYOR,
        sertlik=sertlik,
        konu=konu_basligi(request.POST.get("konu")),
    )
    istenen = [int(i) for i in request.POST.getlist("kelimeler") if str(i).isdigit()]
    if istenen:
        gecerli = list(UserWordLink.objects.filter(user=request.user, word_id__in=istenen)
                       .values_list("word_id", flat=True)[:ONERI_SAYISI])
        if gecerli:
            yazi.words.add(*gecerli)
    return yazi


def _seriye_say(user, yazi):
    """
    Metin gönderildiği an seriye sayılır, ama yalnızca geçerliyse (rapor 18.9,
    texts/gecerlilik.py). Döner: kullanıcıya gösterilecek not ya da "".
    """
    from seri import hesap as seri_hesap

    from .gecerlilik import seriye_sayilir_mi
    sayilir, neden = seriye_sayilir_mi(user, yazi.content, haric_id=yazi.pk)
    if sayilir:
        seri_hesap.say(user, seri_hesap.METIN)
        return ""
    return neden


def _olay_isleyici(reporter):
    """Gemini olaylarını ilerleme çubuğuna çevirir."""
    def isle(ad, bilgi):
        model_sayisi = max(1, bilgi.get("model_count", 1))
        oran = 0.15 + 0.65 * (bilgi.get("model_index", 0) / model_sayisi)
        if ad == "attempt":
            if bilgi.get("model_index", 0) == 0 and bilgi.get("attempt", 1) == 1:
                reporter.set(oran, "Metnin okunuyor...")
            else:
                reporter.set(oran, "Servis yoğun, yeniden deneniyor...")
        elif ad == "success":
            reporter.set(0.9, "Geri bildirim hazırlanıyor...")
    return isle


def _degerlendirme_isi(job_id, yazi_id):
    """Arka plan iş parçacığı: metni değerlendirir, sonucu işe yazar."""
    from django.db import connection

    try:
        yazi = Text.objects.get(pk=yazi_id)
        reporter = progress.Reporter(job_id, 5, 97)
        sonuc = dg.degerlendir(yazi, on_event=_olay_isleyici(reporter))
        progress.finish(job_id, {"text_id": yazi.pk, "sonuc": sonuc}, "Hazır.")
    except Exception:
        logger.exception("Yazma değerlendirme işi beklenmedik şekilde hata verdi.")
        progress.finish(job_id, {"text_id": yazi_id, "sonuc": dg.BOZUK}, "Hazır.")
    finally:
        connection.close()


@login_required
@require_POST
def createText(request):
    """
    Metni kaydeder ve değerlendirir. Metin ÖNCE kaydedilir: Gemini cevap
    vermezse de kaybolmaz ("Henüz değerlendirilmedi").

    JavaScript ile (AJAX) çağrılınca değerlendirme arka plana alınır ve
    ilerleme çubuğu için bir iş kimliği döner; JavaScript yoksa senkron.
    """
    ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    def hata(mesaj, durum=400):
        if ajax:
            return JsonResponse({"error": mesaj}, status=durum)
        messages.error(request, mesaj)
        return redirect("new_text_page")

    if not limits.yazabilir_mi(request.user):
        return hata(limits.sinir_mesaji(), 429)

    metin, sorun = _girdiyi_dogrula(request)
    if sorun:
        return hata(sorun)

    yazi = _yazi_olustur(request, metin)
    seri_notu = _seriye_say(request.user, yazi)
    if seri_notu:   # sonuç sayfasında görünür (AJAX'ta da yönlendirmeden sonra)
        messages.info(request, seri_notu)

    if ajax:
        job_id = progress.create(request.user.id, message="Metnin gönderiliyor...")
        threading.Thread(target=_degerlendirme_isi, args=(job_id, yazi.pk), daemon=True).start()
        return JsonResponse({"job_id": job_id})

    _mesaj_ekle(request, dg.degerlendir(yazi))
    return redirect("review_text", text_id=yazi.pk)


@login_required
def createTextProgress(request, job_id):
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
    job = progress.read(job_id)
    if job is None or job.get("owner_id") != request.user.id:
        return JsonResponse({"error": "İş bulunamadı."}, status=404)
    if job.get("state") == progress.STATE_RUNNING:
        return JsonResponse({"error": "İş hâlâ sürüyor."}, status=409)

    sonuc = job.get("result") or {}
    progress.delete(job_id)
    yazi_id = sonuc.get("text_id")
    if not yazi_id:
        return JsonResponse({"redirect": reverse("profile_texts")})
    if sonuc.get("sonuc") != dg.TAMAM:
        _mesaj_ekle(request, sonuc.get("sonuc"))
    return JsonResponse({"redirect": reverse("review_text", args=[yazi_id])})


# ---------------------------------------------------------------------------
# Değerlendirme görünümü
# ---------------------------------------------------------------------------

@login_gate("Yazılar", GIRIS_ACIKLAMASI)
def reviewText(request, text_id):
    yazi = get_object_or_404(_yazilar(request.user), id=text_id)
    geri = yazi.geri_bildirim or {}
    hatalar = geri.get("hatalar") or []

    return render(request, "pages/texts/textReview.html", {
        "yazi": yazi,
        "puan_yazisi": dg.puan_yazisi(yazi.puan),
        "puan_etiketi": dg.puan_etiketi(yazi.puan),
        "iyi": geri.get("iyi") or [],
        "hatalar": hatalar,
        "kullanilanlar": geri.get("kullanilan_kelimeler") or [],
        "onerilenler": list(yazi.words.values_list("text", flat=True)),
        "parcalar": dg.metin_parcalari(yazi.content, hatalar) if yazi.durum == YaziDurumu.TAMAM else [],
        "sertlik_adi": Sertlik(yazi.sertlik).label if yazi.sertlik in Sertlik.values else "",
        "yogun": limits.yogun_mu(),
    })


@login_required
@require_POST
def retryText(request, text_id):
    """"Şimdi tekrar dene": bekleyen bir metni hemen değerlendirmeyi dener."""
    yazi = get_object_or_404(_yazilar(request.user), id=text_id)
    if yazi.durum == YaziDurumu.BEKLIYOR:
        _mesaj_ekle(request, dg.degerlendir(yazi))
    return redirect("review_text", text_id=yazi.pk)


@login_required
@require_POST
def removeText(request, text_id):
    """Onay penceresi yok: silinir, listede "Geri al" bildirimi çıkar (rapor 12.7)."""
    yazi = get_object_or_404(_yazilar(request.user), id=text_id)
    yazi.silindi = timezone.now()
    yazi.save(update_fields=["silindi"])
    ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if ajax:
        return JsonResponse({"ok": True})
    return redirect(f"{reverse('profile_texts')}?silindi={yazi.pk}")


@login_required
@require_POST
def restoreText(request, text_id):
    yazi = get_object_or_404(Text, owner=request.user, id=text_id)
    yazi.silindi = None
    yazi.save(update_fields=["silindi"])
    return JsonResponse({"ok": True, "adres": reverse("review_text", args=[yazi.pk])})


@login_gate("Yazılar", GIRIS_ACIKLAMASI)
def aboutGradingPage(request):
    return render(request, "pages/texts/aboutGrading.html", {
        "sertlikler": SERTLIK_ACIKLAMALARI,
        "gunluk_limit": limits.gunluk_limit(),
    })


# ---------------------------------------------------------------------------
# Diyalogda doğru kelime
# ---------------------------------------------------------------------------

def diyalogSayfasi(request):
    """
    Girişli kullanıcıda hedef kelime listeden gelir. Misafire de açıktır
    (rapor 18.3): diyalog havuzdan %60 B1 · %20 B2 · %20 C1 dağılımıyla
    seçilir, cevabı kaydedilmez.
    """
    misafir = not request.user.is_authenticated
    havuz_bos = dy.havuz_bos_mu()
    haric = request.GET.get("onceki")
    haric = int(haric) if haric and haric.isdigit() else None
    diyalog = None
    if misafir:
        liste_bos = False
        if not havuz_bos:
            diyalog = dy.misafir_siradaki(haric=haric) or dy.misafir_siradaki()
    else:
        liste_bos = not UserWordLink.objects.filter(user=request.user).exists()
        if not liste_bos and not havuz_bos:
            diyalog = dy.siradaki(request.user, haric=haric)
            if diyalog is None and haric:
                # Tek diyalog varsa "Sonraki" aynısını getirebilir.
                diyalog = dy.siradaki(request.user)

    return render(request, "pages/texts/diyalog.html", {
        "misafir": misafir,
        "liste_bos": liste_bos,
        "havuz_bos": havuz_bos,
        "diyalog": diyalog,
        "satirlar": dy.satirlari_hazirla(diyalog) if diyalog else [],
        "ilk_harf": diyalog.cevap.strip()[:1] if diyalog else "",
    })


@require_POST
def diyalogCevap(request, diyalog_id):
    """Cevabı değerlendirir. Misafirin cevabı kaydedilmez ve seriye sayılmaz (rapor 18.3)."""
    diyalog = get_object_or_404(Diyalog.objects.select_related("word"), pk=diyalog_id, denetlendi=True)
    girdi = (request.POST.get("cevap") or "")[:120]
    sonuc = dy.cevabi_degerlendir(diyalog, girdi)
    seri = None
    if sonuc.durum != dy.BOS and request.user.is_authenticated:
        DiyalogCevabi.objects.create(user=request.user, diyalog=diyalog,
                                     girdi=girdi.strip(), sonuc=sonuc.durum)
        # Cevaplanan diyalog, doğru ya da yanlış, seriye sayılır (rapor 18.9).
        from seri import hesap as seri_hesap
        seri = seri_hesap.say(request.user, seri_hesap.DIYALOG)
    veri = sonuc.sozluk()
    if seri is not None:
        veri["seri"] = seri
    veri["not"] = dy.register_notu(diyalog) if sonuc.durum != dy.BOS else ""
    return JsonResponse(veri)
