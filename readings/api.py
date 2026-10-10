"""
Kelime sorgulama API'si (rapor 8 ve 11).

    GET /api/kelime/?q=decided
    GET /api/kelime/?q=gave&once=she&sonra=it+up      (phrasal için bağlam)

Cevap (JSON):

    {
      "q": "decided", "bulundu": true, "kok": "decide",
      "word_id": 12, "listede": false,
      "anlamlar": [{"tr": "karar vermek", "tanim": "…", "word_id": 12}],
      "digerleri": [{"kok": "decided", "word_id": 13, "listede": false, "anlamlar": […]}],
      "phrasal": {"kok": "give up", "word_id": 40, "listede": false, "anlamlar": […]} | null
    }

Okuma ekranındaki baloncuk ve Chrome eklentisi (chrome-eklentisi/, rapor 11) aynı
ucu kullanır. Cevapta "girisli" de var: eklenti "Listeme ekle" mi "Giriş yap" mı
göstereceğini buradan bilir.
Girişsiz de çalışır (listede hep false). "+" düğmesi mevcut
add_to_my_list ucuna gider; bu uç yalnızca OKUR.

Hız: sözlük kısmı kullanıcıdan bağımsız, sunucu önbelleğinde tutulur
(kelime_sorgu.sorgula). Üstüne yalnızca "listede" için tek sorgu eklenir.
Girişsiz cevaplar tarayıcıda da önbelleğe alınabilir.

CORS: eklentiye gerekmiyor. Eklenti istekleri arka plan betiğinden atıyor; siteye
erişim izni olduğu için Chrome CORS uygulamıyor ve oturum çerezini gönderiyor.
Başka bir kaynak gerekirse settings.KELIME_API_CORS_ORIGINS'e yazılır.

Eklentinin "Listeme ekle"si: POST/DELETE /api/eklenti/listem/<word_id>/ (eklenti_listem).
CSRF jetonu yerine isteğin kaynağına bakılır: Origin yalnızca bizim eklentimiz
(settings.EKLENTI_KAYNAKLARI) olabilir. Tarayıcı Origin'i sayfaların değiştirmesine
izin vermediği için başka bir site kullanıcının listesine kelime ekletemez.
"""

import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils.cache import patch_cache_control, patch_vary_headers
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from LearnVocab import sinir
from words.extract.function_words import islev_kelimesi_mi
from usersettings.anlam import turkce_acik
from words.models import UserWordLink

from .kelime_sorgu import sorgula, tum_word_idleri


# Girişsiz cevabın tarayıcıda kalma süresi (saniye).
MISAFIR_ONBELLEK = 60 * 60


def _listede_ekle(sonuc, user):
    """Sonucun kopyasına "listede" alanlarını ekler (tek sorgu)."""
    sonuc = dict(sonuc)
    listedekiler = set()
    idler = tum_word_idleri(sonuc)
    if user.is_authenticated and idler:
        listedekiler = set(UserWordLink.objects.filter(user=user, word_id__in=idler)
                           .values_list("word_id", flat=True))
    sonuc["listede"] = sonuc.get("word_id") in listedekiler
    sonuc["digerleri"] = [dict(m, listede=m["word_id"] in listedekiler)
                          for m in sonuc.get("digerleri", [])]
    if sonuc.get("phrasal"):
        sonuc["phrasal"] = dict(sonuc["phrasal"],
                                listede=sonuc["phrasal"]["word_id"] in listedekiler)
    if not turkce_acik(user):
        _turkceyi_kaldir(sonuc)
    return sonuc


def _turkceyi_kaldir(sonuc):
    """"Türkçe anlamlar" kapalı (rapor 18.22): anlam satırları İngilizce açıklama olur."""
    def degistir(madde):
        madde["anlamlar"] = [dict(a, tr=a.get("tanim") or a.get("tr", "")) for a in madde.get("anlamlar", [])]
    degistir(sonuc)
    for m in sonuc.get("digerleri", []):
        degistir(m)
    if sonuc.get("phrasal"):
        degistir(sonuc["phrasal"])


def _bulunamayani_kaydet(sonuc, request):
    """
    "Henüz sözlüğümüzde yok" aramaları kaydedilir (rapor 4.2 ve 8): hangi
    kelimelerin ekleneceğine bu kayıttan karar verilir.

    Kayıt Sözlük tarafının (words.arama.bulunamayan_kaydet ->
    words.models.BulunamayanArama, kaynak="okuma"). Yoksa ya da kaydetme bir
    sebeple başarısız olursa sessizce geçilir: okuma baloncuğu bu yüzden
    bozulmamalı. İşlev kelimeleri (the, of …) kaydedilmez: sözlüğe
    eklenecek şeyler değiller.
    """
    q = sonuc.get("q") or ""
    if sonuc.get("bulundu") or sonuc.get("phrasal") or len(q) < 2 or islev_kelimesi_mi(q):
        return
    try:
        from words.arama import bulunamayan_kaydet
    except ImportError:
        return
    try:
        bulunamayan_kaydet(q, kaynak="okuma", istemci=sinir.istemci(request))
    except Exception:          # kayıt yan iş; asla cevabı bozmasın
        logging.getLogger(__name__).exception("Bulunamayan arama kaydedilemedi: %s", q)


def _cors(response, request):
    """İzin verilen kaynaklara CORS başlığı (liste boşsa hiçbir şey yapmaz)."""
    izinli = getattr(settings, "KELIME_API_CORS_ORIGINS", ())
    kaynak = request.headers.get("Origin")
    if kaynak and kaynak in izinli:
        response["Access-Control-Allow-Origin"] = kaynak
        response["Access-Control-Allow-Credentials"] = "true"
        patch_vary_headers(response, ("Origin",))
    return response


# Girişsiz çalışan uç (okuma baloncuğu, Chrome eklentisi): adres başına dakikada.
# Günlük ya da saatlik sınır yok (Efe'nin kararı, 10 Ekim); bu yalnızca botlar için.
# Okul ve yurt ağlarında çok kişi aynı adresi paylaştığı için geniş tutuldu.
KELIME_SINIRI = 300


@require_GET
def kelime(request):
    if sinir.asildi(f"kelime:{sinir.istemci(request)}", KELIME_SINIRI, 60):
        return _cors(sinir.cok_istek(), request)
    sonuc = sorgula(request.GET.get("q", ""),
                    once=request.GET.get("once", ""),
                    sonra=request.GET.get("sonra", ""))
    _bulunamayani_kaydet(sonuc, request)
    sonuc = _listede_ekle(sonuc, request.user)
    sonuc["girisli"] = request.user.is_authenticated

    cevap = JsonResponse(sonuc, json_dumps_params={"ensure_ascii": False})
    if request.user.is_authenticated:
        # "listede" kişiye özel ve "+" ile değişiyor: tarayıcı saklamasın.
        patch_cache_control(cevap, private=True, max_age=0)
    else:
        patch_cache_control(cevap, public=True, max_age=MISAFIR_ONBELLEK)
    patch_vary_headers(cevap, ("Cookie",))
    return _cors(cevap, request)


# ---------------------------------------------------------------------------
# Chrome eklentisi: Listeme ekle / çıkar (rapor 11)
# ---------------------------------------------------------------------------

def eklentiden_mi(request):
    kaynak = request.headers.get("Origin") or ""
    return kaynak in getattr(settings, "EKLENTI_KAYNAKLARI", ())


@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def eklenti_listem(request, word_id):
    """
    Eklentinin "+" düğmesi. POST ekler, DELETE çıkarır. Asıl iş sitedeki uçlarda
    (words.views.add_to_my_list / remove_from_my_list), davranış aynı kalsın diye.
    """
    if not eklentiden_mi(request):
        return JsonResponse({"ok": False}, status=403)
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "giris": True}, status=401)

    from words import views as kelime_views
    request.META["HTTP_X_REQUESTED_WITH"] = "fetch"      # JSON cevap versinler
    request.__dict__.pop("headers", None)                 # request.headers önbellekli
    if request.method == "POST":
        return kelime_views.add_to_my_list(request, word_id)
    return kelime_views.remove_from_my_list(request, word_id)
