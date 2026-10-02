"""
Seviye testi (ürün raporu 7). Adresler: seviye/urls.py (/seviye-testi/…)

    /seviye-testi/                giriş: Başla · Seviyemi kendim seçeyim
    /seviye-testi/basla/          (POST) 1. ekranı hazırlar
    /seviye-testi/ekran/<n>/      1. kısım: 40 kelime, yalnızca bildiklerine dokunur
    /seviye-testi/okuma/          2. kısım: en çok 3 özet sorusu (rapor 18.27)
    /seviye-testi/sonuc/          son testin sonucu + ilk liste ("Geri al")
    /seviye-testi/geri-al/        (POST) ilk listeye eklenenleri çıkarır
    /seviye-testi/sec/            "Seviyemi kendim seçeyim"

Davet (18.27): kullanıcı testi yapana ya da seviyesini seçene kadar her
sayfada küçük bir davet çıkar (seviye/baglam.py); L&P ve egzersiz
oturumlarında çıkmaz. Testin ara durumu oturumda (session) tutulur; yarıda
bırakılan test hiçbir şey yazmaz. Kural: seviye/tahmin.py.
"""

import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_POST

from LearnVocab.authgate import login_gate
from users.seviye import kullanici_seviyesi, seviyesi_belli_mi
from words.models import UserWordLink, Word

from . import okuma, secim, tahmin
from .models import Ekran, OkumaSorusu, SeviyeTestiSonucu

OTURUM_ANAHTARI = "seviye_testi"

SECILEBILIR_SEVIYELER = (
    ("A1", gettext_lazy("Yeni başlıyorum")),
    ("A2", "Temel kelimeleri biliyorum"),
    ("B1", gettext_lazy("Günlük konuları anlıyorum")),
    ("B2", "Akademik metinleri takip edebiliyorum"),
    ("C1", gettext_lazy("İleri düzeydeyim")),
    ("C2", gettext_lazy("Neredeyse anadil düzeyindeyim")),
)

# Sonuç ekranındaki kısa, cesaretlendirici açıklama.
SEVIYE_NOTLARI = {
    "A1": gettext_lazy("Harika bir başlangıç noktası. En sık kullanılan kelimelerle başlayıp hızla ilerleyeceksin."),
    "A2": gettext_lazy("Temelin sağlam. Günlük hayatın kelimelerini oturtup bir üst basamağa geçmeye hazırsın."),
    "B1": gettext_lazy("Günlük konularda rahatsın. Şimdi okumaları ve yazmayı güçlendirecek kelimelerin zamanı."),
    "B2": gettext_lazy("Güçlü bir kelime bilgin var. Akademik ve daha ince anlamlı kelimelerle devam edebilirsin."),
    "C1": gettext_lazy("Çok iyi! İleri düzey kelimelerle kelime hazneni daha da zenginleştirebilirsin."),
    "C2": gettext_lazy("Harika! Çok ileri bir düzeydesin; nadir ve incelikli kelimelerle devam edebilirsin."),
}


def davet_gosterilsin_mi(request):
    """Seviye testi daveti: testi yapmamış ve seviyesini seçmemiş girişli kullanıcı."""
    return request.user.is_authenticated and not seviyesi_belli_mi(request.user)


def _durum(request):
    return request.session.get(OTURUM_ANAHTARI)


def _kaydet(request, durum):
    request.session[OTURUM_ANAHTARI] = durum
    request.session.modified = True


def _ekran_hazirla(durum, ekran):
    """Ekranın kelimelerini seçip duruma yazar; havuz boşsa False."""
    kelimeler = secim.ekran_kelimeleri(ekran, random.Random())
    if not kelimeler:
        return False
    durum["gosterilen"][str(ekran)] = kelimeler
    return True


# ----------------------------------------------------------------------
# Giriş, başla
# ----------------------------------------------------------------------

@login_gate(gettext_lazy("Seviye testi"), gettext_lazy("Seviyeni kaydedip ilk listeni hazırlayabilmek için bir hesaba ihtiyacın var."))
def giris(request):
    return render(request, "pages/seviye/giris.html", {
        "active_page": "Seviye testi",
        "son_sonuc": SeviyeTestiSonucu.objects.filter(user=request.user).first(),
        "seviye_belli": seviyesi_belli_mi(request.user),
        "okuma_var": okuma.havuz_var_mi(),
    })


@login_required
@require_POST
def basla(request):
    durum = {"gosterilen": {}, "bilinen": {}, "okuma": None}
    if not _ekran_hazirla(durum, 1):
        messages.info(request, _("Seviye testi şu an hazır değil. Seviyeni kendin seçebilirsin."))
        return redirect("seviye_sec")
    _kaydet(request, durum)
    return redirect("seviye_ekran", ekran=1)


# ----------------------------------------------------------------------
# 1. kısım: kelime ekranları
# ----------------------------------------------------------------------

@login_required
def ekran(request, ekran):
    durum = _durum(request)
    if not durum or str(ekran) not in durum["gosterilen"]:
        return redirect("seviye_testi")
    gosterilen = durum["gosterilen"][str(ekran)]

    if request.method == "POST":
        secilen = set()
        for deger in request.POST.getlist("bilinen"):
            try:
                secilen.add(int(deger))
            except ValueError:
                continue
        # Yalnızca bu ekranda gösterilenler sayılır.
        durum["bilinen"][str(ekran)] = [w for w in gosterilen if w in secilen]
        # Geri dönülüp yeniden gönderilirse sonraki ekranlar baştan kurulur.
        for sonraki in range(ekran + 1, 4):
            durum["gosterilen"].pop(str(sonraki), None)
            durum["bilinen"].pop(str(sonraki), None)

        sonuc = {"gosterilen": len(gosterilen), "bilinen": len(durum["bilinen"][str(ekran)])}
        sonraki = tahmin.sonraki_ekran(ekran, sonuc)
        if sonraki and _ekran_hazirla(durum, sonraki):
            _kaydet(request, durum)
            return redirect("seviye_ekran", ekran=sonraki)

        ekranlar = _ekran_sonuclari(durum)
        sorular = okuma.sorulari_sec(tahmin.sorulacak_seviyeler(ekranlar), random.Random())
        if sorular:
            durum["okuma"] = sorular
            _kaydet(request, durum)
            return redirect("seviye_okuma")
        return _bitir(request, durum)

    sira = {wid: i for i, wid in enumerate(gosterilen)}
    kelimeler = sorted(Word.objects.filter(id__in=gosterilen).only("id", "text"),
                       key=lambda w: sira[w.id])
    bilinen = set(durum["bilinen"].get(str(ekran), []))
    return render(request, "pages/seviye/ekran.html", {
        "active_page": "Seviye testi",
        "ekran": ekran,
        "ekran_adi": Ekran(ekran).label,
        "kelimeler": kelimeler,
        "bilinen": bilinen,
    })


# ----------------------------------------------------------------------
# 2. kısım: okuma
# ----------------------------------------------------------------------

@login_required
def okuma_sayfasi(request):
    durum = _durum(request)
    if not durum or not durum.get("okuma"):
        return redirect("seviye_testi")
    sorular = durum["okuma"]

    if request.method == "POST":
        cevaplar = {str(s["id"]): request.POST.get(f"soru_{s['id']}", "") for s in sorular}
        durum["okuma_dogru"] = okuma.dogru_seviyeler(sorular, cevaplar)
        return _bitir(request, durum)

    metinler = dict(OkumaSorusu.objects.filter(id__in=[s["id"] for s in sorular])
                    .values_list("id", "metin"))
    return render(request, "pages/seviye/okuma.html", {
        "active_page": "Seviye testi",
        "sorular": [{"id": s["id"], "metin": metinler.get(s["id"], ""), "siklar": s["siklar"]}
                    for s in sorular if s["id"] in metinler],
    })


# ----------------------------------------------------------------------
# Bitiş ve sonuç
# ----------------------------------------------------------------------

def _ekran_sonuclari(durum):
    return {e: {"gosterilen": len(ids), "bilinen": len(durum["bilinen"].get(e, []))}
            for e, ids in durum["gosterilen"].items() if e in durum["bilinen"]}


def _bitir(request, durum):
    user = request.user
    ekranlar = _ekran_sonuclari(durum)
    kelime_seviyesi = tahmin.kelime_tahmini(ekranlar)

    # Sonuç: doğru cevaplanan en yüksek seviye (rapor 18.27). Doğru cevaplar
    # ve doğru sayısı kullanıcıya GÖSTERİLMEZ; yalnızca kayıtta durur.
    sorulan = [s["cefr"] for s in durum.get("okuma") or []]
    dogru = durum.get("okuma_dogru") or []
    seviye = tahmin.sonuc_seviyesi(kelime_seviyesi, sorulan, dogru)
    okuma_sonucu = {"sorulan": sorulan, "dogru": dogru} if sorulan else None

    gosterilen = {e: ids for e, ids in durum["gosterilen"].items() if e in durum["bilinen"]}
    ilk = tahmin.ilk_liste(seviye, gosterilen, durum["bilinen"])

    with transaction.atomic():
        zaten = set(UserWordLink.objects.filter(user=user, word_id__in=ilk)
                    .values_list("word_id", flat=True))
        yeni = [w for w in ilk if w not in zaten]
        UserWordLink.objects.bulk_create([UserWordLink(user=user, word_id=w) for w in yeni],
                                         ignore_conflicts=True)
        user.cefr = seviye
        user.save(update_fields=["cefr"])
        SeviyeTestiSonucu.objects.create(user=user, tahmin=seviye, kelime_tahmini=kelime_seviyesi,
                                         ekranlar=ekranlar, okuma=okuma_sonucu, eklenen=yeni)

    request.session.pop(OTURUM_ANAHTARI, None)
    return redirect("seviye_sonuc")


@login_required
def sonuc(request):
    son = SeviyeTestiSonucu.objects.filter(user=request.user).first()
    if son is None:
        return redirect("seviye_testi")
    ekranlar = [{"no": int(e), "ad": Ekran(int(e)).label, **v,
                 "yuzde": round(100 * tahmin.oran(v))}
                for e, v in sorted(son.ekranlar.items(), key=lambda x: int(x[0]))]
    eklenenler = list(Word.objects.filter(id__in=son.eklenen).order_by("text")
                      .values_list("text", flat=True)[:12]) if not son.geri_alindi else []
    return render(request, "pages/seviye/sonuc.html", {
        "active_page": "Seviye testi",
        "son": son,
        "not_metni": SEVIYE_NOTLARI.get(son.tahmin, ""),
        "ekranlar": ekranlar,
        "eklenen_sayisi": 0 if son.geri_alindi else len(son.eklenen),
        "eklenenler": eklenenler,
        "gecme_yuzdesi": round(100 * tahmin.GECME_ORANI),
    })


@login_required
@require_POST
def geri_al(request):
    """İlk listeye eklenenleri çıkarır (rapor 12.7: onay yerine Geri al)."""
    son = SeviyeTestiSonucu.objects.filter(user=request.user).first()
    cikarilan = 0
    if son is not None and not son.geri_alindi:
        cikarilan, _ayrinti = UserWordLink.objects.filter(user=request.user,
                                                   word_id__in=son.eklenen).delete()
        son.geri_alindi = True
        son.save(update_fields=["geri_alindi"])
    if request.headers.get("X-Requested-With") == "fetch":
        return JsonResponse({"ok": True, "cikarilan": cikarilan})
    messages.success(request, _("İlk listen geri alındı."))
    return redirect("seviye_sonuc")


# ----------------------------------------------------------------------
# Kaçış yolları
# ----------------------------------------------------------------------

@login_gate(gettext_lazy("Seviye testi"))
def sec(request):
    """Seviyemi kendim seçeyim (rapor 7)."""
    if request.method == "POST":
        seviye = request.POST.get("seviye")
        if seviye in dict(SECILEBILIR_SEVIYELER):
            request.user.cefr = seviye
            request.user.save(update_fields=["cefr"])
            messages.success(request, f"Seviyen {seviye} olarak kaydedildi. "
                                      "Seviyeni istediğin zaman Ayarlar'dan değiştirebilirsin.")
            return redirect("index")
        messages.error(request, _("Lütfen bir seviye seç."))
    return render(request, "pages/seviye/sec.html", {
        "active_page": _("Seviyemi seçeyim"),
        "secenekler": SECILEBILIR_SEVIYELER,
        "mevcut": kullanici_seviyesi(request.user) if seviyesi_belli_mi(request.user) else "",
    })
