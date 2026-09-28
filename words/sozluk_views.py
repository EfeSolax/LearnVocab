"""
Sözlük sayfası ve uçları (ürün raporu 4 ve 5). Adresler: words/sozluk_urls.py

    /sozluk/                     Keşfet (boş hâl ya da ?q= arama) | ?sekme=listem Listem
    /sozluk/oneri/?q=            anlık öneri (JSON)
    /sozluk/kart/<id>/           tek kelime kartı (HTML parçası; çip ve Listem satırı yerinde açar)
    /sozluk/liste/<slug>/        hazır liste sayfası
    /sozluk/liste/<slug>/calis/  "Bu listeyle çalış" / "Seviyeme dön" (POST)
    /sozluk/listem/oneri/?q=     Listem'in anlık önerisi (JSON, yalnızca listedekiler)
    /sozluk/listem/cikar/        toplu çıkar (POST JSON {"idler": [...]})
    /sozluk/listem/geri-al/      toplu "Geri al" (POST JSON {"geri": [...]})

Arama mantığı words/arama.py'de, Listem mantığı words/listem.py'de,
hazır listeler words/hazir_liste.py'de. Buradaki görünümler ince.
"""

from urllib.parse import quote, urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.cache import patch_cache_control
from django.views.decorators.http import require_GET, require_POST

from . import arama, hazir_liste, listem
from .kart import kart_verisi
from .models import HazirListe

HAZIR_LISTE_SAYFA_BOYU = 40


def _ajax_mi(request):
    return request.headers.get("X-Requested-With") == "fetch"


# ----------------------------------------------------------------------
# Sözlük sayfası
# ----------------------------------------------------------------------

def sozluk(request):
    """
    Üstte Keşfet | Listem (Listem yalnızca girişliye, rapor 2.3).

    Keşfet:
      - ?q= yoksa boş hâl: Günün Kelimesi, Günün İfadesi, Hazır Listeler.
      - ?q= varsa arama (sunucuda çizilir; adres paylaşılabilir ve
        arama motorları görebilir: /sozluk/?q=aim).
    Listem: ?sekme=listem (+ ara, sira, zaman, zor, sayfa). ?parca=1 ile
    yalnızca satırlar döner ("Daha fazla göster").
    """
    sekme = request.GET.get("sekme")
    if sekme != "listem" or not request.user.is_authenticated:
        sekme = "kesfet"

    baglam = {"active_page": "Sözlük", "sekme": sekme, "sorgu": "", "kartlar": []}
    if sekme == "listem":
        baglam.update(_listem_baglami(request))
        if request.GET.get("parca"):
            return render(request, "pages/words/_listemSatirlari.html", baglam)
    else:
        sorgu = (request.GET.get("q") or "").strip()[:120]
        baglam["sorgu"] = sorgu
        if sorgu:
            baglam.update(_arama_baglami(request, sorgu))
        else:
            baglam.update(_kesfet_baglami(request))
    return render(request, "pages/sozluk.html", baglam)


def _arama_baglami(request, sorgu):
    sonuc = arama.ara(request.user, sorgu)
    kartlar = kart_verisi(sonuc.kelimeler, request.user)

    turkce_kartlar = []
    if sonuc.turkce:
        eslesen = dict(sonuc.turkce)
        turkce_kartlar = kart_verisi([wid for wid, _ in sonuc.turkce], request.user)
        for kart in turkce_kartlar:
            kart.eslesen = eslesen.get(kart.id, "")

    if not sonuc.bulundu:
        arama.bulunamayan_kaydet(sorgu, oneri_vardi=bool(sonuc.oneriler or sonuc.digerleri))

    return {
        "sonuc": sonuc,
        "kartlar": kartlar,
        "turkce_kartlar": turkce_kartlar,
        # Arama motoru için: bulunamayan sayfa dizine girmesin.
        "noindex": not sonuc.bulundu,
        "meta_aciklama": _meta_aciklama(sorgu, kartlar),
    }


def _meta_aciklama(sorgu, kartlar):
    if not kartlar:
        return ""
    anlamlar = []
    for kart in kartlar:
        for a in kart.anlamlar:
            if a.meaning_tr and a.meaning_tr not in anlamlar:
                anlamlar.append(a.meaning_tr)
    return f"{kartlar[0].text} ne demek? Türkçe anlamı: {', '.join(anlamlar[:4])}. " \
           f"Örnek cümleler, eş ve zıt anlamlılar LearnVocab Sözlük'te."


def _kesfet_baglami(request):
    user = request.user
    kelime = arama.gunun_kelimesi(user)
    return {
        "gunun_karti": kart_verisi([kelime], user)[0] if kelime else None,
        "gunun_ifadesi": arama.gunun_ifadesi(user),
        "hazir_listeler": list(hazir_liste.yayindaki_listeler()),
        "aktif_liste": hazir_liste.aktif_liste(user),
    }


def _listem_baglami(request):
    d = listem.durum(request.GET)
    satirlar, toplam, devam = listem.satirlar(request.user, d)
    adres = reverse("sozluk")

    def url(**degisen):
        return f"{adres}?{urlencode(d.parametreler(sayfa=1, **degisen))}"

    baglam = {
        "d": d,
        "satirlar": satirlar,
        "toplam": toplam,
        "devam_adresi": (f"{adres}?{urlencode(d.parametreler(sayfa=d.sayfa + 1, parca=1))}"
                         if devam else ""),
    }
    if not request.GET.get("parca"):
        baglam.update({
            "filtre_satirlari": [
                ("Sırala", [(ad, url(sira=kod), d.sira == kod) for kod, ad in listem.SIRALAR.items()]),
                ("Zaman", [(ad, url(zaman=kod), d.zaman == kod) for kod, ad in listem.ZAMANLAR.items()]),
            ],
            "zor_adresi": url(zor="" if d.zor else "1"),
            "temizle_adresi": url(sira="yeni", zaman="tumu", zor="", ara=""),
            "tum_idler": listem.tum_kelime_idleri(request.user, d),
            # "Listen boş." yalnızca liste gerçekten boşsa; süzgeç boş
            # çıkardıysa başka metin gösterilir.
            "liste_bos": not toplam and not request.user.wordLinks.exists(),
        })
    return baglam


# ----------------------------------------------------------------------
# Anlık öneri ve kart parçası
# ----------------------------------------------------------------------

@require_GET
def sozluk_oneri(request):
    """{"oneriler": [{"metin", "anlam", "cefr", "adres"}]} — kullanıcıdan bağımsız, önbelleklenebilir."""
    sorgu = (request.GET.get("q") or "")[:60]
    satirlar = arama.otomatik_oneri(sorgu)
    adres = reverse("sozluk")
    for s in satirlar:
        s["adres"] = f"{adres}?q={quote(s['metin'])}"
    cevap = JsonResponse({"oneriler": satirlar})
    patch_cache_control(cevap, public=True, max_age=300)
    return cevap


@require_GET
def kart_parcasi(request, word_id):
    """
    Tek kelimenin kartı (HTML parçası): kart çipleri, "Diğer sonuçlar"
    satırları ve Listem satırları kartı yerinde açmak için kullanır.
    ?kapat=olay: kartın ⌃ düğmesi kartı küçültmek yerine "kart-kapat"
    olayı gönderir (Listem satırı kendi hâline döner).
    """
    kelime = arama.gorunur_kelimeler(request.user).filter(id=word_id).first()
    if kelime is None:
        raise Http404
    kart = kart_verisi([kelime], request.user)[0]
    return render(request, "pages/words/_kartParcasi.html", {
        "kart": kart, "kapat_olay": request.GET.get("kapat") == "olay",
    })


# ----------------------------------------------------------------------
# Listem uçları
# ----------------------------------------------------------------------

@login_required
@require_GET
def listem_oneri(request):
    sorgu = (request.GET.get("q") or "")[:60]
    adres = reverse("sozluk")
    satirlar = listem.oneri(request.user, sorgu)
    for s in satirlar:
        s["adres"] = f"{adres}?{urlencode({'sekme': 'listem', 'ara': s['metin']})}"
    return JsonResponse({"oneriler": satirlar})


@login_required
@require_POST
def listem_toplu_cikar(request):
    veri = listem.json_govdesi(request)
    geri = listem.toplu_cikar(request.user, veri.get("idler"))
    return JsonResponse({"ok": True, "sayi": len(geri), "geri": geri})


@login_required
@require_POST
def listem_geri_yukle(request):
    veri = listem.json_govdesi(request)
    sayi = listem.toplu_geri_yukle(request.user, veri.get("geri"))
    return JsonResponse({"ok": True, "sayi": sayi})


# ----------------------------------------------------------------------
# Hazır listeler
# ----------------------------------------------------------------------

def hazir_liste_sayfasi(request, slug):
    """Liste sayfası: kelimeler kapalı kartlar; "Bu listeyle çalış". Toplu ekleme YOK."""
    liste = get_object_or_404(HazirListe, slug=slug, yayinda=True)
    uyeler = liste.uyelikler.order_by("sira", "id").values_list("word_id", flat=True)
    sayfa = Paginator(uyeler, HAZIR_LISTE_SAYFA_BOYU).get_page(request.GET.get("sayfa") or 1)
    kartlar = kart_verisi(list(sayfa.object_list), request.user)
    baglam = {
        "active_page": "Sözlük",
        "liste": liste,
        "kartlar": kartlar,
        "sayfa": sayfa,
        "calisiliyor": hazir_liste.aktif_liste(request.user) == liste,
    }
    if request.GET.get("parca"):
        return render(request, "pages/words/_hazirListeKartlari.html", baglam)
    return render(request, "pages/words/hazirListe.html", baglam)


@login_required
@require_POST
def hazir_liste_calis(request, slug):
    """islem=birak -> seviyeye dön; yoksa bu listeyle çalış."""
    liste = get_object_or_404(HazirListe, slug=slug, yayinda=True)
    if request.POST.get("islem") == "birak":
        hazir_liste.seviyeye_don(request.user)
        mesaj = "Learn & Pass yeni kelimeleri yine seviyene göre seçecek."
    else:
        hazir_liste.listeyle_calis(request.user, liste)
        mesaj = f"Learn & Pass artık yeni kelimeleri “{liste.ad}” listesinden getirecek."
    if _ajax_mi(request):
        return JsonResponse({"ok": True, "mesaj": mesaj,
                             "calisiliyor": request.POST.get("islem") != "birak"})
    messages.success(request, mesaj)
    return redirect("hazir_liste", slug=liste.slug)

