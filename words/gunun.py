"""
Günün kelimesi ve günün ifadesi (rapor 18.8). Ana Sayfa'da ve Sözlük ›
Keşfet'in boş hâlinde aynı kartlar durur (base/_gununKelimesi.html,
base/_gununIfadesi.html); 12.00 bildirimi de kelimeyi buradan alır.

GÜNÜN KELİMESİ
  - Kullanıcının seviyesinde (misafire B1).
  - Giriş yapmış kullanıcı onu henüz GÖRMEMİŞ olmalı: listesinde değil,
    L&P'de ya da egzersizde karşısına çıkmamış.
  - Verisi zengin: en az 2 örnek cümle ve bir eş dizim; dört ana türden tek
    sözcük; nadir tür değil; çok seyrek değil.
  - Sıklık ağırlığıyla seçilir (L&P'deki ağırlık: words.siklik.lp_agirligi).
  - Önce Google'a açık ve seviyesi resmî kaynakla doğrulanmış kelimeler;
    o seviyede böylesi yoksa koşullar sırayla gevşer (KADEMELER).
  - Misafire o gün HERKESE AYNI kelime (tarihten hesaplanır, saklanmaz).
    Giriş yapmış kullanıcıya kişiye özel kelime; gün boyunca değişmesin
    diye GununKelimesi tablosuna yazılır. Gün, kullanıcının yerel günüdür.
  - "Biliyordum" / "Bilmiyordum" L&P verisine yazılır (learnpass.tekrar.kaydet,
    yeni kelime olarak): bilinmeyen tekrar takibine girer.
  - Kullanıcı kelimeyi listesine ekler ya da "Biliyordum" derse kart o gün
    kapanır: "Bugünün kelimesi tamam ✓, yarın yenisi gelecek."

GÜNÜN İFADESİ
  - Herkese aynı ifade: AZ BİLİNEN ifadelerden (Expression.bilinirlik),
    sırası bir kez karıştırılmış döngüyle. N ifade varsa N günde başa döner.
  - Bilme kaydı tutulmaz; yalnızca "Listeme ekle". Eklenince kart kapanır.
"""

import random

from django.core.cache import cache
from django.db.models import Count, Exists, OuterRef
from django.utils import timezone

from users.seviye import VARSAYILAN, kullanici_seviyesi

from .arama import CEFR_SIRASI, ifade_hazirla, ortak_sozluk
from .dizine_alma import EN_AZ_SIKLIK
from .kart import kart_verisi
from .models import (
    CEFR_LEVELS, Collocation, Expression, GununKelimesi, PartOfSpeech, UserExpressionLink,
    UserWordLink, Word,
)
from .siklik import lp_agirligi

TURLER = (PartOfSpeech.NOUN, PartOfSpeech.VERB, PartOfSpeech.ADJECTIVE, PartOfSpeech.ADVERB)
RESMI_KAYNAKLAR = ("oxford", "cambridge")
EN_AZ_ORNEK = 2

BILIYORDUM, BILMIYORDUM = "known", "unknown"

# Koşullar sırayla gevşer: ilk dolu kademe kullanılır.
KADEMELER = (
    {"dizinde": True, "cefr_kaynak__in": RESMI_KAYNAKLAR},
    {"dizinde": True},
    {"cefr_kaynak__in": RESMI_KAYNAKLAR},
    {},
)

# İfade döngüsünün karıştırma tohumu: sıra bir kez belirlenir, değişmez.
_IFADE_TOHUMU = 20260930


# ----------------------------------------------------------------------
# Günün kelimesi
# ----------------------------------------------------------------------

def _uygun(seviye):
    eslesim = Collocation.objects.filter(meaning__word=OuterRef("pk"))
    return (Word.objects.filter(ortak_sozluk(), cefr=seviye, pos__in=TURLER, nadir_tur=False,
                                siklik__gte=EN_AZ_SIKLIK)
            .exclude(text__contains=" ")
            .annotate(_ornek=Count("meanings__examples", distinct=True))
            .filter(_ornek__gte=EN_AZ_ORNEK).filter(Exists(eslesim)))


def _yakin_seviyeler(seviye):
    """B1 -> B1, B2, A2, C1 …: seviyede hiç aday yoksa komşusuna kayılır."""
    i = CEFR_SIRASI.get(seviye, CEFR_SIRASI[VARSAYILAN])
    return sorted(CEFR_LEVELS, key=lambda s: (abs(CEFR_SIRASI[s] - i), -CEFR_SIRASI[s]))


def _adaylar(seviye, haric=()):
    """[(id, sıklık)] — ilk dolu kademeden; görülmüş kelimeler (haric) çıkarılır."""
    for s in _yakin_seviyeler(seviye)[:3]:
        temel = _uygun(s)
        for kosul in KADEMELER:
            satirlar = [(wid, z) for wid, z in temel.filter(**kosul).order_by("id")
                        .values_list("id", "siklik") if wid not in haric]
            if satirlar:
                return satirlar
    return []


def _agirlikli_sec(satirlar, rng):
    return rng.choices([wid for wid, _ in satirlar],
                       weights=[lp_agirligi(z) for _, z in satirlar], k=1)[0]


def misafir_kelimesi(gun=None, seviye=VARSAYILAN):
    """O gün herkese aynı kelime (Word ya da None). Günde bir kez hesaplanır."""
    gun = gun or timezone.localdate()
    anahtar = f"gunun-kelimesi:{gun.isoformat()}:{seviye}"
    wid = cache.get(anahtar)
    kelime = Word.objects.filter(pk=wid).first() if wid else None
    if kelime is None:          # önbellekte yok ya da kelime o arada silinmiş
        satirlar = _adaylar(seviye)
        if not satirlar:
            return None
        wid = _agirlikli_sec(satirlar, random.Random(anahtar))
        cache.set(anahtar, wid, 26 * 3600)
        kelime = Word.objects.filter(pk=wid).first()
    return kelime


# Misafir ana sayfasındaki defter tablosu (rapor 18.12): katlanan sütunla
# kendini sınama. O gün herkese aynı 5 kelime; günün kelimesiyle aynı ölçüt.
DEFTER_KOTASI = (("B1", 2), ("B2", 3))


def defter_kelimeleri(gun=None):
    """O gün herkese aynı kelimeler (list[Word], en çok 5); günün kelimesi hariç."""
    gun = gun or timezone.localdate()
    anahtar = f"defter-kelimeleri:{gun.isoformat()}"
    idler = cache.get(anahtar)
    if idler is None:
        gunun = misafir_kelimesi(gun)
        secilen = [gunun.pk] if gunun else []
        rng = random.Random(anahtar)
        for seviye, adet in DEFTER_KOTASI:
            satirlar = _adaylar(seviye, haric=set(secilen))
            for _ in range(adet):
                if not satirlar:
                    break
                wid = _agirlikli_sec(satirlar, rng)
                secilen.append(wid)
                satirlar = [(w, z) for w, z in satirlar if w != wid]
        idler = secilen[1:] if gunun else secilen
        cache.set(anahtar, idler, 26 * 3600)
    sira = {wid: i for i, wid in enumerate(idler)}
    return sorted(Word.objects.filter(pk__in=idler), key=lambda w: sira[w.pk])


def _gorulenler(user):
    from learnpass.models import WordEncounter
    gorulen = set(WordEncounter.objects.filter(user=user).values_list("word_id", flat=True))
    gorulen |= set(UserWordLink.objects.filter(user=user).values_list("word_id", flat=True))
    gorulen |= set(GununKelimesi.objects.filter(user=user).values_list("word_id", flat=True))
    return gorulen


def kullanici_kaydi(user, rng=None):
    """Kullanıcının bugünkü GununKelimesi satırı (yoksa seçilir ve yazılır); aday yoksa None."""
    from seri.zaman import yerel_gun
    gun = yerel_gun(user)
    kayit = GununKelimesi.objects.filter(user=user, gun=gun).select_related("word").first()
    if kayit:
        return kayit
    satirlar = _adaylar(kullanici_seviyesi(user), haric=_gorulenler(user))
    if not satirlar:
        return None
    wid = _agirlikli_sec(satirlar, rng or random.Random())
    kayit, _ = GununKelimesi.objects.get_or_create(user=user, gun=gun, defaults={"word_id": wid})
    return kayit


def gunun_kelimesi(user):
    """Yalnızca kelime (bildirim için): Word ya da None."""
    if user is None or not user.is_authenticated:
        return misafir_kelimesi()
    kayit = kullanici_kaydi(user)
    return kayit.word if kayit else None


def kelime_durumu(user):
    """
    Kart için: {"kart", "tamam", "cevap"} ya da None (aday yok).
      tamam: kart kapalı ("Bugünün kelimesi tamam ✓").
      cevap: "" | "known" | "unknown" — düğmeler yalnızca "" iken görünür.
    """
    if user is None or not user.is_authenticated:
        kelime = misafir_kelimesi()
        return {"kart": kart_verisi([kelime], user)[0], "tamam": False, "cevap": ""} if kelime else None
    kayit = kullanici_kaydi(user)
    if kayit is None:
        return None
    kart = kart_verisi([kayit.word], user)[0]
    return {"kart": kart, "cevap": kayit.cevap,
            "tamam": kayit.cevap == BILIYORDUM or kart.listede}


def cevapla(user, cevap):
    """
    "Biliyordum" / "Bilmiyordum". L&P verisine YENİ kelime olarak yazılır;
    bir kez cevaplanır. Döner: güncel kelime_durumu ya da None (geçersiz).
    """
    if cevap not in (BILIYORDUM, BILMIYORDUM):
        return None
    kayit = kullanici_kaydi(user)
    if kayit is None:
        return None
    if not kayit.cevap:
        from learnpass import tekrar
        from learnpass.models import WordEncounter
        tekrar.kaydet(user, kayit.word, cevap, WordEncounter.MODE_NEW)
        kayit.cevap = cevap
        kayit.save(update_fields=["cevap"])
    return kelime_durumu(user)


# ----------------------------------------------------------------------
# Günün ifadesi
# ----------------------------------------------------------------------

def _ifade_dongusu():
    """Az bilinen ifadelerin kimlikleri, bir kez karıştırılmış sırada."""
    idler = list(Expression.objects.filter(visibility="public", bilinirlik="az")
                 .exclude(meaning_tr="").order_by("id").values_list("id", flat=True))
    random.Random(_IFADE_TOHUMU).shuffle(idler)
    return idler


def gunun_ifadesi(gun=None):
    """Herkese aynı ifade (Expression, ilk_ornek ile) ya da None."""
    gun = gun or timezone.localdate()
    idler = _ifade_dongusu()
    if not idler:
        return None
    ifade = (Expression.objects.filter(pk=idler[gun.toordinal() % len(idler)])
             .prefetch_related("examples").first())
    return ifade_hazirla(ifade) if ifade else None


def ifade_durumu(user):
    """Kart için: {"ifade", "tamam"} ya da None. tamam: kullanıcı listesine eklemiş."""
    ifade = gunun_ifadesi()
    if ifade is None:
        return None
    tamam = bool(user is not None and user.is_authenticated and
                 UserExpressionLink.objects.filter(user=user, expression=ifade).exists())
    return {"ifade": ifade, "tamam": tamam}
