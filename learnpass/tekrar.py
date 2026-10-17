"""
Tekrar kuralı (rapor 18.2) — L&P ve egzersizler bu modülü ortak kullanır.

KAYIT (kaydet)
--------------
- Bilinen kelime 1 · 3 · 7 · 21 birim arayla yeniden aday olur; 21'den sonra
  21'de bir. Birim 1 gün (settings.TEKRAR_BIRIMI_SAAT, varsayılan 24): tek
  yerden değişir, veri taşıma gerekmez.
- Aralık, kelimenin çalışmada en son görülüp BİLİNDİĞİ andan sayılır.
- Bilemezse ("bilmiyorum", "yanılmışım", egzersizde yanlış) bütün ilerleme
  sıfırlanır; sayaçlar silinmez.
- Yeni kelimeye ilk seferde "eminim" denirse kelime takibe girmez (bilinen
  sayılır); listede değilse bir daha yalnızca aralığı dolunca ve listeye
  eklenirse gelir.
- Egzersizde doğru cevap basamağı yalnızca kelime adayken ilerletir
  (çoktan seçmeli soru kolay olduğu için).

SIRALAMA (tekrar_sirasi)
------------------------
Adaylar: takipteki ya da listedeki kelimelerden zorlananlar (son sonuç
başarısız) + aralığı dolmuş bilinenler + listede olup hiç görülmemişler.
  1. Listede olup hiç görülmemiş kelimeler EN ÖNCE (18.2 d).
  2. En son karşısına çıkma zamanı en eski olan önce (dakika hassasiyetinde).
  3. Zaman eşitse zorlanma oranı yüksek olan önce.
  4. Hâlâ eşitse rastgele.

AİLE ARALAMA (aileye_gore_sirala, aileleri_arala)
-------------------------------------------------
Aynı aileden (Word.family) kelimeler bir turda art arda gelmesin
(decide → decision gibi; biri ötekini ele verir). Sıradaki kart seçilirken
turda henüz ailesi görünmemiş aday öne alınır; hepsinin ailesi görünmüşse
ailesi en uzun süre önce görünen seçilir. Öncelik sırası bunun dışında
korunur. Misafir turu baştan hazırlandığı için aynı ailedekiler tur içinde
birbirinden olabildiğince uzağa dağıtılır.

YENİ KELİME (yeni_kelime)
-------------------------
Günde en çok 15. Kullanıcının seviyesi çevresinden, sıklık ağırlıklı (sık kelime daha sık çıkar, rapor 18.16/3).
Nadir türler (dog fiil…) yalnızca C1–C2 kullanıcılara gelir.
"""

import random
from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from words.models import DILBILGISI_TURLERI, UserWordLink, Word
from words.siklik import lp_agirligi

from .models import EncounterLog, WordEncounter

ARALIKLAR = (1, 3, 7, 21)
GUNLUK_YENI_SINIRI = 15

SEVIYELER = ("A1", "A2", "B1", "B2", "C1", "C2")
# Girişli kullanıcıda yeni kelimenin seviyesi: kendi seviyesi, bir üstü, bir altı.
SEVIYE_AGIRLIKLARI = ((0, 60), (1, 25), (-1, 15))
# Misafir ve seviyesi bilinmeyen: %60 B1 · %20 B2 · %20 C1 (rapor 18.3).
MISAFIR_DAGILIMI = (("B1", 60), ("B2", 20), ("C1", 20))
NADIR_TUR_SEVIYELERI = ("C1", "C2")


def birim():
    return timedelta(hours=getattr(settings, "TEKRAR_BIRIMI_SAAT", 24))


def aralik(basamak):
    """basamak >= 1 için bir sonraki tekrara kadar geçecek süre."""
    return ARALIKLAR[min(max(basamak, 1), len(ARALIKLAR)) - 1] * birim()


# ----------------------------------------------------------------------
# Kayıt
# ----------------------------------------------------------------------

def _ilerlet(enc, simdi):
    enc.basamak += 1
    enc.son_basarili = True
    enc.son_bilinen_at = simdi
    enc.sonraki_tekrar = simdi + aralik(enc.basamak)


def _sifirla(enc):
    enc.basamak = 0
    enc.son_basarili = False
    enc.son_bilinen_at = None
    enc.sonraki_tekrar = None
    enc.takipte = True


def aday_mi(enc, simdi=None):
    """Kelime şu an tekrar adayı mı? (zorlanıyor ya da aralığı doldu)"""
    if enc is None or enc.times_seen == 0:
        return True
    if not enc.son_basarili or enc.sonraki_tekrar is None:
        return True
    return enc.sonraki_tekrar <= (simdi or timezone.now())


def kaydet(user, word, sonuc, mode, simdi=None):
    """
    Bir L&P kararını ya da egzersiz cevabını kaydeder; güncel satırı döner.
    sonuc: known / unknown / misjudged (L&P) ya da dogru / yanlis (egzersiz).
    """
    simdi = simdi or timezone.now()
    enc, _ = WordEncounter.objects.get_or_create(
        user=user, word=word, defaults={"last_verdict": sonuc, "last_mode": mode})
    ilk_kez = enc.times_seen == 0
    basamak_once = enc.basamak
    uygundu = aday_mi(enc, simdi)

    enc.last_verdict = sonuc
    enc.last_mode = mode
    enc.times_seen += 1

    if sonuc == WordEncounter.KNOWN:
        enc.known_count += 1
        enc.listeye_sorulacak = False
        _ilerlet(enc, simdi)
        if ilk_kez and not UserWordLink.objects.filter(user=user, word=word).exists():
            enc.takipte = False   # yeni kelimeye ilk seferde "eminim": takibe girmez
    elif sonuc == WordEncounter.DOGRU:
        enc.egz_dogru += 1
        if uygundu:
            _ilerlet(enc, simdi)
    elif sonuc in (WordEncounter.UNKNOWN, WordEncounter.MISJUDGED, WordEncounter.YANLIS):
        if sonuc == WordEncounter.UNKNOWN:
            enc.unknown_count += 1
        elif sonuc == WordEncounter.MISJUDGED:
            enc.misjudged_count += 1
        else:
            enc.egz_yanlis += 1
        _sifirla(enc)
    else:
        raise ValueError(f"bilinmeyen sonuç: {sonuc}")

    enc.save()
    EncounterLog.objects.create(
        user=user, word=word, word_text=word.text, verdict=sonuc, mode=mode,
        seen_index=enc.times_seen, basamak_once=basamak_once,
    )
    return enc


# ----------------------------------------------------------------------
# Sıralama
# ----------------------------------------------------------------------

def _sira_anahtari(enc, rng):
    """(hiç görülmemiş mi, son görülme dakikası, -zorlanma, rastgele)"""
    if enc is None:
        return (0, 0, 0.0, rng.random())
    dakika = int(enc.last_seen_at.timestamp() // 60) if enc.last_seen_at else 0
    return (1, dakika, -enc.zorlanma_orani, rng.random())


def _takip_kayitlari(user):
    liste = UserWordLink.objects.filter(user=user).values("word_id")
    return WordEncounter.objects.filter(user=user).filter(Q(takipte=True) | Q(word_id__in=liste))


def _uygun_q(simdi):
    return Q(son_basarili=False) | Q(sonraki_tekrar__isnull=True) | Q(sonraki_tekrar__lte=simdi)


# ----------------------------------------------------------------------
# Aile aralama
# ----------------------------------------------------------------------

# Sıradaki kart için bakılan aday sayısı (öncelik sırasının başı yeter).
ARALAMA_ADAY_SINIRI = 200


def _aileler(idler):
    return dict(Word.objects.filter(id__in=list(idler)).values_list("id", "family_id"))


def aile_mesafeleri(gosterilenler):
    """
    Turda görünen aileler -> kaç kart önce görüldüğü (1 = bir önceki kart).
    gosterilenler: turda gösterilen kelime id'leri, eskiden yeniye.
    """
    gosterilenler = list(gosterilenler)
    aile = _aileler(gosterilenler)
    mesafe = {}
    for i, wid in enumerate(reversed(gosterilenler), start=1):
        fid = aile.get(wid)
        if fid is not None and fid not in mesafe:
            mesafe[fid] = i
    return mesafe


def aileye_gore_sirala(idler, gosterilenler):
    """
    Öncelik sırasını bozmadan, ailesi turda henüz görünmemiş adayları öne,
    ailesi yakın zamanda görünenleri arkaya alır.
    """
    idler = list(idler)
    gosterilenler = list(gosterilenler)
    if not idler or not gosterilenler:
        return idler
    mesafe = aile_mesafeleri(gosterilenler)
    bas = idler[:ARALAMA_ADAY_SINIRI]
    aile = _aileler(bas)

    def anahtar(wid):
        fid = aile.get(wid)
        return (1, -mesafe[fid]) if fid in mesafe else (0, 0)

    return sorted(bas, key=anahtar) + idler[ARALAMA_ADAY_SINIRI:]


def aileleri_arala(idler, aile=None):
    """
    Baştan hazırlanan bir turu (misafir) aynı ailedekiler birbirinden
    olabildiğince uzak düşecek biçimde yeniden dizer. Kalabalık aile önce
    yerleşir: üyeleri boş yerlere eşit aralıkla dağıtılır; tek kişilik
    aileler kalan yerleri özgün sırayla doldurur.
    aile: {id: aile id} (verilmezse veritabanından okunur).
    """
    idler = list(idler)
    if aile is None:
        aile = _aileler(idler)
    gruplar = {}
    for wid in idler:
        gruplar.setdefault(aile.get(wid, ("tek", wid)), []).append(wid)
    bos = list(range(len(idler)))
    sira = [None] * len(idler)
    for grup in sorted(gruplar.values(), key=len, reverse=True):
        if len(grup) == 1:
            break
        yerler = [bos[j * len(bos) // len(grup)] for j in range(len(grup))]
        for yer, wid in zip(yerler, grup):
            sira[yer] = wid
        bos = [y for y in bos if y not in yerler]
    tekler = iter([w for w in idler if len(gruplar[aile.get(w, ("tek", w))]) == 1])
    for yer in bos:
        sira[yer] = next(tekler)
    return sira


def tekrar_sirasi(user, simdi=None, rng=None, haric=()):
    """Şu an tekrar adayı olan kelimelerin id'leri, öncelik sırasıyla."""
    simdi = simdi or timezone.now()
    rng = rng or random
    haric = set(haric)
    kayitlar = list(_takip_kayitlari(user).filter(_uygun_q(simdi)).exclude(word_id__in=haric)
                    .only("word_id", "last_seen_at", "times_seen", "unknown_count",
                          "misjudged_count", "egz_yanlis"))
    gorulen = WordEncounter.objects.filter(user=user).values("word_id")
    hic_gorulmemis = (UserWordLink.objects.filter(user=user).exclude(word_id__in=gorulen)
                      .exclude(word_id__in=haric).values_list("word_id", flat=True))
    adaylar = [(_sira_anahtari(k, rng), k.word_id) for k in kayitlar]
    adaylar += [(_sira_anahtari(None, rng), wid) for wid in hic_gorulmemis]
    adaylar.sort()
    return [wid for _, wid in adaylar]


def bekleyen_tekrar_sayisi(user, simdi=None):
    simdi = simdi or timezone.now()
    gorulen = WordEncounter.objects.filter(user=user).values("word_id")
    return (_takip_kayitlari(user).filter(_uygun_q(simdi)).count()
            + UserWordLink.objects.filter(user=user).exclude(word_id__in=gorulen).count())


def siradaki_tekrar(user, rng=None, haric=()):
    """haric: turda gösterilenler, eskiden yeniye (aile aralaması buna bakar)."""
    sira = aileye_gore_sirala(tekrar_sirasi(user, rng=rng, haric=haric), haric)
    return Word.objects.filter(id=sira[0]).first() if sira else None


def liste_sirasi(user, rng=None):
    """
    Egzersizler için kullanıcının bütün listesi, öncelik sırasıyla: önce
    adaylar (tekrar_sirasi), sonra aralığı henüz dolmamışlar en eski
    görülenden başlayarak.
    """
    rng = rng or random
    simdi = timezone.now()
    once = tekrar_sirasi(user, simdi=simdi, rng=rng)
    kalan = (WordEncounter.objects.filter(user=user, word__userLinks__user=user)
             .exclude(word_id__in=once).order_by("last_seen_at").values_list("word_id", flat=True))
    onde = set(once)
    return once + [w for w in kalan if w not in onde]


# ----------------------------------------------------------------------
# Yeni kelime
# ----------------------------------------------------------------------

def bugun_yeni_sayisi(user):
    from seri.zaman import yerel_gun_basi
    return EncounterLog.objects.filter(
        user=user, mode=WordEncounter.MODE_NEW, seen_index=1,
        created_at__gte=yerel_gun_basi(user)).count()


def _agirlikli_orneklem(adaylar, adet, rng):
    """adaylar: [(id, sıklık)] -> ağırlığa göre, tekrarsız `adet` id (Efraimidis–Spirakis)."""
    anahtarli = [(rng.random() ** (1.0 / lp_agirligi(s)), wid) for wid, s in adaylar]
    anahtarli.sort(reverse=True)
    return [wid for _, wid in anahtarli[:adet]]


def _seviye_sirasi(user, rng):
    """Yeni kelime için seviyeleri ağırlıklarına göre rastgele sıraya dizer."""
    from users.seviye import kullanici_seviyesi, seviyesi_belli_mi
    if user is not None and seviyesi_belli_mi(user):
        i = SEVIYELER.index(kullanici_seviyesi(user))
        agirliklar = [(SEVIYELER[i + f], a) for f, a in SEVIYE_AGIRLIKLARI
                      if 0 <= i + f < len(SEVIYELER)]
    else:
        agirliklar = list(MISAFIR_DAGILIMI)
    sira = []
    while agirliklar:
        seviye = rng.choices([s for s, _ in agirliklar], [a for _, a in agirliklar])[0]
        sira.append(seviye)
        agirliklar = [(s, a) for s, a in agirliklar if s != seviye]
    return sira + [s for s in SEVIYELER if s not in sira]


def _yeni_havuz(user, seviye=None):
    from users.seviye import kullanici_seviyesi
    qs = Word.objects.filter(isBaseWord=True).exclude(pos__in=DILBILGISI_TURLERI)
    if seviye:
        qs = qs.filter(cefr=seviye)
    if user is not None and user.is_authenticated:
        qs = (qs.exclude(saved_by=user).exclude(owner=user)
              .exclude(id__in=WordEncounter.objects.filter(user=user).values("word_id")))
        if kullanici_seviyesi(user) not in NADIR_TUR_SEVIYELERI:
            qs = qs.exclude(nadir_tur=True)
    else:
        qs = qs.exclude(nadir_tur=True)
    return qs


def _aileden_uzak(adaylar, mesafe):
    """
    [(id, sıklık, aile)] -> [(id, sıklık)]: ailesi turda görünmemişler;
    hiçbiri kalmıyorsa ailesi en uzun süre önce görünenler.
    """
    if not adaylar:
        return []
    en_uzak = max(mesafe.get(fid, float("inf")) for _, _, fid in adaylar)
    return [(wid, s) for wid, s, fid in adaylar if mesafe.get(fid, float("inf")) == en_uzak]


def yeni_kelime(user, rng=None, haric=()):
    """
    Sıradaki yeni kelime ya da None (günlük sınır doldu / havuz bitti).
    haric: turda gösterilenler, eskiden yeniye; ailesi turda görünmüş
    kelimeler mümkünse seçilmez (aile aralama).
    """
    rng = rng or random
    if bugun_yeni_sayisi(user) >= GUNLUK_YENI_SINIRI:
        return None
    haric = list(haric)
    mesafe = aile_mesafeleri(haric)

    for seviye in _seviye_sirasi(user, rng):
        adaylar = _aileden_uzak(list(_yeni_havuz(user, seviye).exclude(id__in=haric)
                                     .values_list("id", "siklik", "family_id")), mesafe)
        if adaylar:
            return Word.objects.filter(id=_agirlikli_orneklem(adaylar, 1, rng)[0]).first()
    return None


# Misafir havuzu herkes için aynı: her açılışta binlerce satırı yeniden çekmek
# yerine (id, sıklık) listesi bir saat önbellekte durur. Örnekleme yine her
# istekte yapılır, yani misafire her seferinde farklı kartlar gelir.
MISAFIR_HAVUZ_SURESI = 3600


def _misafir_havuzu(seviye):
    from django.core.cache import cache
    return cache.get_or_set(
        f"lp-misafir-havuz:{seviye or 'hepsi'}",
        lambda: list(_yeni_havuz(None, seviye).values_list("id", "siklik")
                     if seviye else _yeni_havuz(None).values_list("id", "siklik")),
        MISAFIR_HAVUZ_SURESI)


def misafir_kelimeleri(adet, rng=None):
    """Misafir turu: %60 B1 · %20 B2 · %20 C1, sıklık ağırlıklı, nadir tür yok (rapor 18.3)."""
    rng = rng or random
    toplam = sum(a for _, a in MISAFIR_DAGILIMI)
    paylar = [(s, round(adet * a / toplam)) for s, a in MISAFIR_DAGILIMI]
    paylar[0] = (paylar[0][0], adet - sum(p for _, p in paylar[1:]))
    secilen = []
    for seviye, pay in paylar:
        secilen += _agirlikli_orneklem(_misafir_havuzu(seviye), pay, rng)
    if len(secilen) < adet:   # bir seviye boşsa diğerleriyle tamamla
        alinan = set(secilen)
        adaylar = [a for a in _misafir_havuzu(None) if a[0] not in alinan]
        secilen += _agirlikli_orneklem(adaylar, adet - len(secilen), rng)
    rng.shuffle(secilen)
    kelimeler = {k.id: k for k in Word.objects.filter(id__in=secilen)
                 .prefetch_related("meanings__examples")}
    secilen = aileleri_arala(secilen, {i: k.family_id for i, k in kelimeler.items()})
    return [kelimeler[i] for i in secilen if i in kelimeler]


# ----------------------------------------------------------------------
# Başka bölümlerin kullandığı sorgular
# ----------------------------------------------------------------------

def zorlanilan_kelimeler(user):
    """Son sonucu "bilemedi" olan kelimeler — Listem'deki "Zorlandıklarım" (18.2)."""
    return Word.objects.filter(id__in=WordEncounter.objects.filter(
        user=user, son_basarili=False, times_seen__gt=0).values("word_id"))
