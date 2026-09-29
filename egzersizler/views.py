"""
Egzersizler görünümleri (ürün raporu 6.2).

Akış:
  açılış (exercises_page) -> basla (POST) -> oturum/<id> (soru)
      -> cevap (POST, JSON ya da form) -> ilerle (POST, "Devam")
      -> ... -> oturum/<id> bitiş ekranı
      -> tekrar (POST, "Yanlışları tekrar çöz") | basla (POST, "Yeni tur") | Bitir

Oturumun bütün durumu (sorular, cevaplar, sıra) veritabanında: sayfa
yenilense de kaldığı yerden devam eder. Cevap verilmiş ama "Devam"a
basılmamış soru yenilenirse sonuç ekranıyla geri gelir.

Girişsiz ziyaretçi: açılış ve oturum sayfaları login_gate ile açıklama
ekranı gösterir (rapor 2.3); POST uçları login_required.
"""

import json
import random
from functools import wraps

from django.contrib import messages
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.http import require_POST

from LearnVocab.authgate import giris_adresi, login_gate
from seri import hesap as seri_hesap
from words.models import UserWordLink

from . import sorular as S
from .kayit import cevaplari_kaydet
from .models import EgzersizOturumu


GATE_LABEL = "Egzersizler"
GATE_NOTE = "Egzersizler kendi listenle çalıştığı için giriş yapman gerekiyor."


def login_required(view):
    """
    POST uçları için: girişsiz istek Egzersizler'e dönecek şekilde giriş
    sayfasına ("egzersiz" açıklamasıyla) yönlendirilir.
    """
    @wraps(view)
    def sarici(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(giris_adresi(reverse("exercises_page"), "egzersiz"))
        return view(request, *args, **kwargs)
    return sarici


def _ses_acik(user):
    try:
        return bool(user.mysettings.audio)
    except Exception:  # ayar satırı olmayan eski kullanıcılar
        return True


def _yarim_oturum(user):
    return (EgzersizOturumu.objects
            .filter(user=user, durum=EgzersizOturumu.DURUM_DEVAM).order_by("-guncelleme").first())


@login_gate(GATE_LABEL, GATE_NOTE)
def exercises_page(request):
    """Açılış: iki büyük seçenek — Hızlı Egzersiz ve Tempolu Egzersiz."""
    liste_sayisi = UserWordLink.objects.filter(user=request.user).count()
    yarim = _yarim_oturum(request.user)
    context = {
        "active_page": "Egzersizler",
        "exercise_tab": "exercises",
        "liste_sayisi": liste_sayisi,
        "hizli_soru_sayisi": min(S.HIZLI_SORU_SAYISI, liste_sayisi),
        "hizli_tam": S.HIZLI_SORU_SAYISI,
        "tipler": S.tip_durumlari(request.user),
        "soru_sayilari": S.SORU_SAYILARI,
        "varsayilan_sayi": S.VARSAYILAN_SORU_SAYISI,
        "yarim": yarim if yarim and yarim.soru_sayisi else None,
    }
    return render(request, "pages/egzersizler/acilis.html", context)


def _yeni_oturum(user, tur, tip, sayi, sorular, kaynak=None):
    # Yarım kalan eski turlar "bırakıldı" sayılır: açılışta tek bir "devam et" olsun.
    EgzersizOturumu.objects.filter(user=user, durum=EgzersizOturumu.DURUM_DEVAM).update(
        durum=EgzersizOturumu.DURUM_BIRAKILDI)
    return EgzersizOturumu.objects.create(user=user, tur=tur, tip=tip, istenen=sayi,
                                          sorular=sorular, kaynak=kaynak)


@login_required
@require_POST
def basla(request):
    tur = request.POST.get("tur")
    user = request.user
    if tur == EgzersizOturumu.TUR_HIZLI:
        sorular = S.hizli_sorular(user)
        if not sorular:
            messages.info(request, "Hızlı Egzersiz listendeki kelimelerle çalışıyor. "
                                   "Sözlük'te + ile birkaç kelime ekle, hemen başlayalım.")
            return redirect("exercises_page")
        oturum = _yeni_oturum(user, tur, S.TIP_ANLAM, S.HIZLI_SORU_SAYISI, sorular)
        return redirect("egzersiz_oturum", pk=oturum.pk)

    if tur == EgzersizOturumu.TUR_TEMPOLU:
        tip = request.POST.get("tip") or S.KARISIK
        if tip != S.KARISIK and tip not in S.TIPLER:
            tip = S.KARISIK
        try:
            sayi = int(request.POST.get("sayi") or S.VARSAYILAN_SORU_SAYISI)
        except ValueError:
            sayi = S.VARSAYILAN_SORU_SAYISI
        if sayi not in S.SORU_SAYILARI:
            sayi = S.VARSAYILAN_SORU_SAYISI
        sorular = S.tempolu_sorular(user, tip, sayi)
        if not sorular:
            messages.info(request, "Bu tip için şu an soru hazırlayamadık. "
                                   "Başka bir tip ya da Karışık ile devam edebilirsin.")
            return redirect("exercises_page")
        oturum = _yeni_oturum(user, tur, tip, sayi, sorular)
        return redirect("egzersiz_oturum", pk=oturum.pk)

    return redirect("exercises_page")


def _oturum_al(request, pk):
    return get_object_or_404(EgzersizOturumu, pk=pk, user=request.user)


@login_gate(GATE_LABEL, GATE_NOTE)
def oturum(request, pk):
    o = _oturum_al(request, pk)
    if o.sira >= o.soru_sayisi:
        if not o.bitti_mi:
            o.durum = EgzersizOturumu.DURUM_BITTI
            o.save(update_fields=["durum", "guncelleme"])
        return _bitis(request, o)
    if o.durum == EgzersizOturumu.DURUM_BIRAKILDI:
        # Bırakılmış bir tur adresinden açılırsa yine devam edilebilsin.
        EgzersizOturumu.objects.filter(user=request.user, durum=EgzersizOturumu.DURUM_DEVAM).update(
            durum=EgzersizOturumu.DURUM_BIRAKILDI)
        o.durum = EgzersizOturumu.DURUM_DEVAM
        o.save(update_fields=["durum", "guncelleme"])

    soru = o.sorular[o.sira]
    sonuc = S.sonuc_verisi(soru, o.cevaplar[o.sira]) if o.cevaplandi_mi(o.sira) else None
    # Alevli çubuk (rapor 18.9): günün egzersiz sayısı 10'a ulaşınca yanar.
    # Alev, günün tamamlanacağı soru hizasında durur. "Yanlışları tekrar
    # çöz" turları seriye sayılmadığı için orada alev yalnızca durumu gösterir.
    seri = seri_hesap.bugun(request.user)
    kalan = max(0, seri["esik"] - seri["egzersiz"])
    tekrar_turu = o.kaynak_id is not None
    alev = {"esik": seri["esik"], "tamamlandi": seri["tamamlandi"],
            "yer": 100 if tekrar_turu else round(100 * (o.sira + kalan) / o.soru_sayisi, 1)}
    context = {
        "active_page": "Egzersizler",
        "exercise_tab": "exercises",
        "oturum": o,
        "soru": soru,
        "alev": alev,
        "sira_no": o.sira + 1,
        "ilerleme": round(100 * o.sira / o.soru_sayisi),
        "sonuc": sonuc,
        "config": {
            "cevapUrl": reverse("egzersiz_cevap", kwargs={"pk": o.pk}),
            "soru": S.istemci_sorusu(soru),
            "sonuc": sonuc,
            "ses": _ses_acik(request.user),
            "sesDogru": static("sounds/correct.mp3"),
            "sesYanlis": static("sounds/wrong.mp3"),
        },
    }
    return render(request, "pages/egzersizler/soru.html", context)


def _bitis(request, o):
    yanlislar = []
    for soru, cevap in zip(o.sorular, o.cevaplar):
        if cevap and not cevap.get("dogru_mu"):
            yanlislar.append({"soru": soru["soru"], "etiket": soru["etiket"],
                              "dogru": S.dogru_cevap_metni(soru), "cumle": soru.get("cumle")})
    liste_sayisi = None
    if o.tur == EgzersizOturumu.TUR_HIZLI and o.soru_sayisi < S.HIZLI_SORU_SAYISI:
        liste_sayisi = UserWordLink.objects.filter(user=request.user).count()
    oran = o.dogru_sayisi / o.soru_sayisi if o.soru_sayisi else 0
    if oran == 1:
        mesaj = "Hepsi doğru! Harika gidiyorsun."
    elif oran >= 0.7:
        mesaj = "Çok iyi! Yanlışlar da öğrenmenin parçası."
    elif oran >= 0.4:
        mesaj = "Güzel bir tur. Yanlışlarına bir kez daha bakmak iyi gelir."
    else:
        mesaj = "Her tur bir adım. Yanlışları tekrar çözünce fark edeceksin."
    context = {
        "active_page": "Egzersizler",
        "exercise_tab": "exercises",
        "oturum": o,
        "yanlislar": yanlislar,
        "mesaj": mesaj,
        "kisa_liste": liste_sayisi is not None,
    }
    return render(request, "pages/egzersizler/bitis.html", context)


def _secim_oku(request):
    if request.content_type == "application/json":
        try:
            veri = json.loads(request.body or b"{}")
        except ValueError:
            return None
        return veri.get("secim")
    ham = request.POST.get("secim")
    try:
        return int(ham)
    except (TypeError, ValueError):
        return None


def _json_istiyor(request):
    return request.content_type == "application/json" or "application/json" in request.headers.get("Accept", "")


@login_required
@require_POST
def cevap(request, pk):
    o = _oturum_al(request, pk)
    if o.durum != EgzersizOturumu.DURUM_DEVAM or o.sira >= o.soru_sayisi:
        return HttpResponseBadRequest("Bu tur bitti.")
    soru = o.sorular[o.sira]

    if not o.cevaplandi_mi(o.sira):
        degerlendirme = S.degerlendir(soru, _secim_oku(request))
        if degerlendirme is None:
            return HttpResponseBadRequest("Geçersiz cevap.")
        dogru_mu, sonuclar = degerlendirme
        cevaplar = list(o.cevaplar) + [None] * (o.sira + 1 - len(o.cevaplar))
        cevaplar[o.sira] = {"secim": _secim_oku(request), "dogru_mu": dogru_mu}
        o.cevaplar = cevaplar
        o.save(update_fields=["cevaplar", "guncelleme"])
        seri = cevaplari_kaydet(request.user, o, soru["tip"], sonuclar)
    else:
        seri = None
    # Aynı soruya ikinci cevap sayılmaz: kayıtlı sonuç döner.
    sonuc = S.sonuc_verisi(soru, o.cevaplar[o.sira])
    if seri is not None:
        sonuc = dict(sonuc, seri=seri)
    if _json_istiyor(request):
        return JsonResponse(sonuc)
    return redirect("egzersiz_oturum", pk=o.pk)


@login_required
@require_POST
def ilerle(request, pk):
    o = _oturum_al(request, pk)
    if o.durum == EgzersizOturumu.DURUM_DEVAM and o.cevaplandi_mi(o.sira):
        o.sira += 1
        if o.sira >= o.soru_sayisi:
            o.durum = EgzersizOturumu.DURUM_BITTI
        o.save(update_fields=["sira", "durum", "guncelleme"])
    return redirect("egzersiz_oturum", pk=o.pk)


@login_required
@require_POST
def tekrar(request, pk):
    """Yanlışları tekrar çöz: yalnızca yanlış yapılan sorular, şıklar yeniden karışık."""
    o = _oturum_al(request, pk)
    rng = random.Random()
    yanlislar = [S.karistir(s, rng) for s, c in zip(o.sorular, o.cevaplar)
                 if c and not c.get("dogru_mu")]
    if not yanlislar:
        return redirect("egzersiz_oturum", pk=o.pk)
    rng.shuffle(yanlislar)
    yeni = _yeni_oturum(request.user, o.tur, o.tip, o.istenen, yanlislar, kaynak=o)
    return redirect("egzersiz_oturum", pk=yeni.pk)
