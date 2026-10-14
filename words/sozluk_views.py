"""
Sözlük sayfası ve uçları (ürün raporu 4, 5 ve 18.15).
Adresler: words/sozluk_urls.py (sayfalar) ve words/api_urls.py (uçlar)

    /sozluk/                     Keşfet (boş hâl) | ?sekme=listem Listem
    /sozluk/?q=bank              arama: tam eşleşme /sozluk/bank/ adresine 301;
                                 diğer sonuçlar burada gösterilir (noindex)
    /sozluk/bank/                kelimenin KALICI sayfası: aynı arayüz, aynı kartlar
    /sozluk/seviye/b1/           seviyeye göre göz at (sayfalı)
    /sozluk/harf/a/              harfe göre göz at (sayfalı)
    /listeler/<slug>/            hazır liste sayfası
    /listeler/<slug>/calis/      "Bu listeyle çalış" / "Seviyeme dön" (POST)
    /api/sozluk/oneri/?q=        anlık öneri (JSON)
    /api/sozluk/kart/<id>/       tek kelime kartı (HTML parçası; çip ve Listem satırı yerinde açar)
    /api/listem/oneri/?q=        Listem'in anlık önerisi (JSON, yalnızca listedekiler)
    /api/listem/cikar/           toplu çıkar (POST JSON {"idler": [...]})
    /api/listem/geri-al/         toplu "Geri al" (POST JSON {"geri": [...]})

Arama mantığı words/arama.py'de, Listem mantığı words/listem.py'de,
hazır listeler words/hazir_liste.py'de. Buradaki görünümler ince.
"""

import json
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Case, Q, Value, When
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.cache import patch_cache_control
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST

from LearnVocab import sinir
from LearnVocab.seo import tam_adres

from . import arama, dizine_alma, gozat, gunun, hazir_liste, konular, listem
from usersettings.anlam import turkce_acik

from .adres import kelime_adresi, slug_yap
from .kart import kart_verisi
from .models import CEFR_LEVELS, Category, Expression, HazirListe, Word

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
      - ?q= varsa arama. Tam eşleşen kelime ya da ifade kendi kalıcı adresine
        301 ile gider (/sozluk/?q=aim -> /sozluk/aim/): aynı içerik tek
        adreste durur. Geri kalan sonuç sayfaları (Türkçe sorgu, çekimli hâl,
        öneri, bulunamadı) dizine girmez (rapor 18.15, SEO kuralı 3).
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
            sonuc = arama.ara(request.user, sorgu)
            slug = arama.tam_eslesme_slug(sonuc)
            if slug:
                return redirect("sozluk_kelime", slug=slug, permanent=True)
            baglam.update(_sonuc_baglami(request, sonuc))
            if not sonuc.bulundu:
                arama.bulunamayan_kaydet(sorgu, oneri_vardi=bool(sonuc.oneriler or sonuc.digerleri),
                                         istemci=sinir.istemci(request))
        else:
            baglam.update(_kesfet_baglami(request))
    # Arama sonucu ve Listem kişiye/sorguya özel: dizine girmez.
    baglam["noindex"] = bool(baglam["sorgu"]) or sekme == "listem"
    return render(request, "pages/sozluk.html", baglam)


def sozluk_kelime(request, slug):
    """
    Kelimenin kalıcı sayfası (rapor 18.15). Arayüz Sözlük sayfasının aynısı:
    üstte arama kutusu, altında o kelimenin kartları. Değişen yalnızca adres.
    """
    dogru = slug_yap(slug)
    if dogru and dogru != slug:                       # /sozluk/Bank/ -> /sozluk/bank/
        return redirect("sozluk_kelime", slug=dogru, permanent=True)

    baglam = {"active_page": "Sözlük", "sekme": "kesfet", "kartlar": []}
    sonuc = arama.kelime_sayfasi(request.user, slug)
    if sonuc is None:
        # Böyle bir kelime yok: benzerleri göster ama 404 dön (yumuşak 404 olmasın).
        sorgu = slug.replace("-", " ")
        sonuc = arama.ara(request.user, sorgu)
        baglam.update(_sonuc_baglami(request, sonuc), sorgu=sorgu, noindex=True)
        return render(request, "pages/sozluk.html", baglam, status=404)

    baglam.update(_sonuc_baglami(request, sonuc), sorgu=sonuc.sorgu, kelime_sayfasi=True)
    baglam["noindex"] = not dizine_alma.sayfa_acik_mi(sonuc.kelimeler, sonuc.ifadeler)
    baglam["sayfa_basligi"] = _("%(kelime)s ne demek? Türkçe anlamı ve cümle içinde kullanımı — LearnVocab Sözlük") % {
        "kelime": sonuc.sorgu}
    baglam["ekmek_kirintisi"] = _ekmek_kirintisi(sonuc)
    baglam["yapisal_veri"] = _yapisal_veri(sonuc, baglam["kartlar"], baglam["ekmek_kirintisi"])
    if baglam["kartlar"]:
        baglam.update(_madde_baglami(sonuc, baglam["kartlar"]))
    return render(request, "pages/sozluk.html", baglam)


def _madde_baglami(sonuc, kartlar):
    """
    Kelime sayfasının defter maddesi için ek veri (rapor 18.12; örnek
    ozetler/tasarim-ornekleri/defter/kelime.html). Üç küçük sorgu:
      aile    -> aynı ailedeki kelimeler, her birinin ilk Türkçe anlamıyla (ağaç çizimi)
      komsular -> sözlükte alfabetik olarak hemen önceki ve sonraki dizine açık kelimeler
      sayfa_no -> maddenin "sayfa numarası": dizine açık kelimeler içindeki alfabetik sırası
    Komşular yalnızca Google'a açık kelimelerdir (rapor 18.15): kapalı sayfaya bağlantı verilmez.
    """
    from .models import Meaning, Word

    aile, gorulen = [], {k.id for k in kartlar}
    for kart in kartlar:
        for uye in kart.aile:
            if uye.pk not in gorulen:
                gorulen.add(uye.pk)
                aile.append(uye)
    aile = aile[:6]
    ilk_anlam = {}
    for wid, tr in (Meaning.objects.filter(word__in=aile).order_by("word_id", "sort_order", "id")
                    .values_list("word_id", "meaning_tr")):
        ilk_anlam.setdefault(wid, tr)
    aile_satirlari = [{"text": u.text, "anlam": ilk_anlam.get(u.pk, "")} for u in aile]

    acik = Word.objects.filter(dizinde=True).exclude(text__contains=" ")
    oncekiler = list(acik.filter(text__lt=sonuc.sorgu).order_by("-text")
                     .values_list("text", flat=True).distinct()[:4])[::-1]
    sonrakiler = list(acik.filter(text__gt=sonuc.sorgu).order_by("text")
                      .values_list("text", flat=True).distinct()[:4])
    return {
        "aile_satirlari": aile_satirlari,
        "komsular": (oncekiler, sonrakiler),
        "sayfa_no": acik.filter(text__lt=sonuc.sorgu).values("text").distinct().count() + 1,
    }


def _ekmek_kirintisi(sonuc):
    """[(ad, yol)] — sayfada görünen satır: Sözlük › B1 kelimeleri › bank"""
    adimlar = [(_("Sözlük"), reverse("sozluk"))]
    seviye = next((k.cefr for k in sonuc.kelimeler if k.cefr in CEFR_LEVELS), "")
    if seviye:
        adimlar.append((_("%(seviye)s kelimeleri") % {"seviye": seviye}, reverse("sozluk_seviye", args=[seviye.lower()])))
    adimlar.append((sonuc.sorgu, kelime_adresi(sonuc.sorgu)))
    return adimlar


def _yapisal_veri(sonuc, kartlar, ekmek_kirintisi):
    """
    JSON-LD (schema.org DefinedTerm + BreadcrumbList). Yalnızca sayfada
    GÖRÜNEN içeriği anlatır (rapor 18.15, SEO kuralı 5).
    """
    adres = tam_adres(kelime_adresi(sonuc.sorgu))
    terim = {
        "@context": "https://schema.org",
        "@type": "DefinedTerm",
        "name": sonuc.sorgu,
        "description": ", ".join(_turkce_anlamlar(sonuc, kartlar)),
        "inLanguage": "en",
        "url": adres,
        "inDefinedTermSet": {
            "@type": "DefinedTermSet",
            "name": _("LearnVocab Sözlük"),
            "url": tam_adres(reverse("sozluk")),
        },
    }
    kirinti = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": ad, "item": tam_adres(yol)}
            for i, (ad, yol) in enumerate(ekmek_kirintisi, start=1)
        ],
    }
    # "</script>" metnin içinde geçemesin.
    return [json.dumps(v, ensure_ascii=False).replace("<", "\\u003c") for v in (terim, kirinti)]


def _sonuc_baglami(request, sonuc):
    kartlar = kart_verisi(sonuc.kelimeler, request.user)

    turkce_kartlar = []
    if sonuc.turkce:
        eslesen = dict(sonuc.turkce)
        turkce_kartlar = kart_verisi([wid for wid, _ in sonuc.turkce], request.user)
        for kart in turkce_kartlar:
            # "Türkçe anlamlar" kapalıysa eşleşen Türkçe anlam da gösterilmez (rapor 18.22).
            kart.eslesen = eslesen.get(kart.id, "") if turkce_acik(request.user) else ""

    return {
        "sonuc": sonuc,
        "kartlar": kartlar,
        "turkce_kartlar": turkce_kartlar,
        "meta_aciklama": _meta_aciklama(sonuc, kartlar),
    }


def _turkce_anlamlar(sonuc, kartlar):
    """Sayfadaki kartların Türkçe anlamları, sırayla ve tekrarsız."""
    anlamlar = [a.meaning_tr for kart in kartlar for a in kart.anlamlar]
    anlamlar += [ifade.meaning_tr for ifade in sonuc.ifadeler]
    return list(dict.fromkeys(a for a in anlamlar if a))


def _meta_aciklama(sonuc, kartlar):
    """Arama sonucunda görünen açıklama: sayfadaki Türkçe anlamlar ve ilk örnek cümle."""
    anlamlar = _turkce_anlamlar(sonuc, kartlar)
    if not anlamlar:
        return ""
    ornekler = [a.ornek for kart in kartlar for a in kart.anlamlar]
    ornekler += [ifade.ilk_ornek for ifade in sonuc.ifadeler]
    ornek = next((o for o in ornekler if o), "")
    metin = _("%(kelime)s ne demek? Türkçe anlamı: %(anlamlar)s.") % {"kelime": sonuc.sorgu, "anlamlar": ", ".join(anlamlar[:4])}
    if ornek:
        metin += " " + _("Örnek: “%(ornek)s”") % {"ornek": ornek}
    return metin


def _kesfet_baglami(request):
    user = request.user
    return {
        "gunun_kelimesi": gunun.kelime_durumu(user),
        "gunun_ifadesi": gunun.ifade_durumu(user),
        "hazir_listeler": list(hazir_liste.yayindaki_listeler()),
        # Konu kutucukları (rapor 18.39): arama kutusuyla günün kelimesi arasında
        "konular": konular.kesfet_konulari(),
        "konu_onde": konular.ONDE_GORUNEN,
        "aktif_liste": hazir_liste.aktif_liste(user),
        # Göz atma bağlantıları (rapor 18.15)
        "seviyeler": gozat.dolu_seviyeler(),
        "harfler": gozat.dolu_harfler(),
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
                (_("Sırala"), [(ad, url(sira=kod), d.sira == kod) for kod, ad in listem.SIRALAR.items()]),
                (_("Zaman"), [(ad, url(zaman=kod), d.zaman == kod) for kod, ad in listem.ZAMANLAR.items()]),
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
    turkcesiz = request.GET.get("tr") == "0"     # "Türkçe anlamlar" kapalı (rapor 18.22)
    for s in satirlar:
        s["adres"] = kelime_adresi(s["metin"])
        if turkcesiz:
            s["anlam"] = ""
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


@login_required
@require_POST
def gunun_kelimesi_cevap(request):
    """Günün kelimesinde "Biliyordum" / "Bilmiyordum" (rapor 18.8). POST: cevap=known|unknown"""
    durum = gunun.cevapla(request.user, request.POST.get("cevap"))
    if durum is None:
        return JsonResponse({"ok": False}, status=400)
    return JsonResponse({"ok": True, "cevap": durum["cevap"]})


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
# Göz atma sayfaları (rapor 18.15)
# ----------------------------------------------------------------------

def _gozat(request, kelimeler, baslik, aciklama, **ek):
    sayfa = Paginator(kelimeler.prefetch_related("meanings"), gozat.SAYFA_BOYU) \
        .get_page(request.GET.get("sayfa") or 1)
    if sayfa.number > 1:
        baslik = f"{baslik} (sayfa {sayfa.number})"
    return render(request, "pages/words/gozat.html", {
        "active_page": "Sözlük",
        "baslik": baslik,
        "meta_aciklama": aciklama,
        "sayfa": sayfa,
        "satirlar": [arama._satir(word=w) for w in sayfa.object_list],
        "seviyeler": gozat.dolu_seviyeler(),
        "harfler": gozat.dolu_harfler(),
        **ek,
    })


def sozluk_seviye(request, seviye):
    if seviye != seviye.lower():
        return redirect("sozluk_seviye", seviye=seviye.lower(), permanent=True)
    kod = seviye.upper()
    if kod not in CEFR_LEVELS:
        raise Http404
    return _gozat(request, gozat.seviye_kelimeleri(kod),
                  _("%(seviye)s seviyesi İngilizce kelimeler") % {"seviye": kod},
                  _("%(seviye)s seviyesindeki İngilizce kelimeler: Türkçe anlamları, örnek cümleleri "
                    "ve telaffuzlarıyla.") % {"seviye": kod},
                  secili_seviye=kod)


def sozluk_harf(request, harf):
    if harf != harf.lower():
        return redirect("sozluk_harf", harf=harf.lower(), permanent=True)
    if harf not in gozat.HARFLER:
        raise Http404
    return _gozat(request, gozat.harf_kelimeleri(harf),
                  _("%(harf)s harfiyle başlayan İngilizce kelimeler") % {"harf": harf.upper()},
                  _("%(harf)s harfiyle başlayan İngilizce kelimeler ve Türkçe anlamları.") % {"harf": harf.upper()},
                  secili_harf=harf)


# ----------------------------------------------------------------------
# Hazır listeler
# ----------------------------------------------------------------------

def hazir_listeler(request):
    """/listeler/ : ayrı bir sayfa yok; listeler Sözlük'ün Keşfet ekranında durur."""
    return redirect("sozluk")


def _liste_uyeleri(liste, ara, bolum=""):
    """
    Listenin kelime kimlikleri, liste sırasıyla. `ara` verilirse yalnızca o listedeki
    kelimeler: İngilizcesinde ya da Türkçe anlamında geçenler, baştan eşleşenler önce.
    """
    uyeler = liste.uyelikler.all()
    if bolum:
        uyeler = uyeler.filter(bolum=bolum)
    if ara:
        en, tr = arama.en_normal(ara), arama.tr_normal(ara)
        eslesen = (liste.uyelikler.filter(Q(word__text__icontains=en) | Q(word__meanings__meaning_tr__icontains=tr))
                   .values("id"))
        uyeler = (uyeler.filter(id__in=eslesen)
                  .annotate(bastan=Case(When(word__text__istartswith=en, then=Value(0)), default=Value(1)))
                  .order_by("bastan", "sira", "id"))
    else:
        uyeler = uyeler.order_by("sira", "id")
    return uyeler.values_list("word_id", "bolum")


def _kaynak_ailesi(liste, kartlar):
    """
    Kaynağın kendi ailesi varsa (More to Read II) kartta sözlüğün ailesi yerine o gösterilir.
    Sözlükte ayrı kelime olanlar kendi kartına bağlanır; çekimler (abandoned) düz yazı kalır.
    """
    aileler = dict(liste.uyelikler.filter(word_id__in=[k.id for k in kartlar])
                   .exclude(aile=[]).values_list("word_id", "aile"))
    if not aileler and not liste.uyelikler.exclude(aile=[]).exists():
        return
    metinler = {t.lower() for a in aileler.values() for t in a}
    kelime_idleri = {}
    for w in Word.objects.filter(arama.ortak_sozluk(), text__in=list(metinler)).order_by("id"):
        kelime_idleri.setdefault(w.text.lower(), w)
    for kart in kartlar:
        kart.aile = [kelime_idleri.get(t.lower()) or {"text": t, "id": None}
                     for t in aileler.get(kart.id, [])]


def hazir_liste_sayfasi(request, slug):
    """
    Liste sayfası: kelimeler kapalı kartlar; "Bu listeyle çalış". Toplu ekleme YOK.
    ?ara= yalnızca bu listede arar (Efe'nin isteği, 10 Ekim): sayfa yazdıkça
    ?ara=…&parca=1 ile kartları yeniler, Enter gerekmez.
    """
    liste = get_object_or_404(HazirListe, slug=slug, yayinda=True)
    ara = (request.GET.get("ara") or "").strip()[:80]
    # Bölümler (ODTÜ'de haftalar) listede ilk geçtikleri sırayla; ?bolum= yalnızca o bölüm.
    bolumler = list(dict.fromkeys(liste.uyelikler.exclude(bolum="").order_by("sira", "id")
                                  .values_list("bolum", flat=True)))
    bolum = request.GET.get("bolum") or ""
    if bolum not in bolumler:
        bolum = ""
    uyeler = _liste_uyeleri(liste, ara, bolum)
    sayfa = Paginator(uyeler, HAZIR_LISTE_SAYFA_BOYU).get_page(request.GET.get("sayfa") or 1)
    satirlar = list(sayfa.object_list)
    kartlar = kart_verisi([w for w, _ in satirlar], request.user)
    _kaynak_ailesi(liste, kartlar)
    # Bölüm başlığı (ODTÜ'de hafta) bölüm değişince bir kez; aramada başlık yok.
    # "Daha fazla göster" ile gelen parçada önceki sayfanın son bölümü tekrar yazılmaz.
    onceki = ""
    if not ara and sayfa.start_index() > 1:
        onceki = uyeler[sayfa.start_index() - 2][1]
    bolum_of = dict(satirlar)
    ogeler = []
    for kart in kartlar:
        kart_bolumu = bolum_of.get(kart.id, "")
        baslik = kart_bolumu if (kart_bolumu and kart_bolumu != onceki and not ara) else ""
        onceki = kart_bolumu
        ogeler.append((kart, baslik))
    baglam = {
        "active_page": "Sözlük",
        "liste": liste,
        "kartlar": kartlar,
        "ogeler": ogeler,
        "sayfa": sayfa,
        "ara": ara,
        "bolumler": bolumler,
        "secili_bolum": bolum,
        "toplam": liste.uyelikler.count(),
        "meta_aciklama": liste.yerel_aciklama,
        "calisiliyor": hazir_liste.aktif_liste(request.user) == liste,
    }
    if request.GET.get("parca"):
        cevap = render(request, "pages/words/_hazirListeKartlari.html", baglam)
        cevap["X-Sonuc-Sayisi"] = str(sayfa.paginator.count)
        return cevap
    return render(request, "pages/words/hazirListe.html", baglam)


def konu_sayfasi(request, slug):
    """
    Konu sayfası (rapor 18.39): o konuyla işaretlenmiş kelimeler, hazır liste sayfasındaki gibi
    alt alta kapalı kartlar (kolaydan zora); konunun ifadeleri en altta. "Daha fazla göster"
    ?sayfa=N&parca=1 ile gelir; "Bu listede ara" ?ara=…&parca=1 ile yazdıkça süzer.
    Google'a kapalı (seo.DIZINE_ACIK'ta değil).
    """
    kategori = get_object_or_404(Category, slug=slug)
    tumu = konular.konu_kelime_idleri(kategori, arama.ortak_sozluk())
    # "Bu listede ara" (hazır listedeki gibi): İngilizcede ya da Türkçe anlamda, baştan eşleşenler önce.
    ara = (request.GET.get("ara") or "").strip()[:80]
    idler = tumu
    if ara:
        en, tr = arama.en_normal(ara), arama.tr_normal(ara)
        eslesen = Word.objects.filter(id__in=tumu).filter(
            Q(text__icontains=en) | Q(meanings__meaning_tr__icontains=tr))
        bastan = set(eslesen.filter(text__istartswith=en).values_list("id", flat=True))
        eslesen = set(eslesen.values_list("id", flat=True))
        idler = [i for i in tumu if i in bastan] + [i for i in tumu if i in eslesen and i not in bastan]
    sayfa = Paginator(idler, HAZIR_LISTE_SAYFA_BOYU).get_page(request.GET.get("sayfa") or 1)
    kartlar = kart_verisi(list(sayfa.object_list), request.user)
    baglam = {
        "active_page": "Sözlük",
        "konu": konular.konu_bilgisi(kategori),
        "ogeler": [(k, "") for k in kartlar],
        "sayfa": sayfa,
        "ara": ara,
        "secili_bolum": "",
        "toplam": len(tumu),
    }
    if request.GET.get("parca"):
        cevap = render(request, "pages/words/_hazirListeKartlari.html", baglam)
        cevap["X-Sonuc-Sayisi"] = str(sayfa.paginator.count)
        return cevap
    if not sayfa.has_previous() and not ara:
        baglam["ifadeler"] = [arama.ifade_hazirla(e) for e in Expression.objects.filter(
            visibility="public", categories=kategori).prefetch_related("examples").order_by("text")]
    return render(request, "pages/words/konu.html", baglam)


@login_required
@require_POST
def hazir_liste_calis(request, slug):
    """islem=birak -> seviyeye dön; yoksa bu listeyle çalış."""
    liste = get_object_or_404(HazirListe, slug=slug, yayinda=True)
    if request.POST.get("islem") == "birak":
        hazir_liste.seviyeye_don(request.user)
        mesaj = _("Learn & Pass yeni kelimeleri yine seviyene göre seçecek.")
    else:
        hazir_liste.listeyle_calis(request.user, liste)
        mesaj = _("Learn & Pass artık yeni kelimeleri “%(liste)s” listesinden getirecek.") % {"liste": liste.yerel_ad}
    if _ajax_mi(request):
        return JsonResponse({"ok": True, "mesaj": mesaj,
                             "calisiliyor": request.POST.get("islem") != "birak"})
    messages.success(request, mesaj)
    return redirect("hazir_liste", slug=liste.slug)

