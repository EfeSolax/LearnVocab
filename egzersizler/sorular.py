"""
Soru üreteçleri (ürün raporu 6.2).

Her soru düz bir sözlüktür; oturumda (EgzersizOturumu.sorular) JSON olarak
saklanır, böylece sayfa yenilense de aynı soru aynı şıklarla gelir:

    {
      "tip":        "anlam",               # TIPLER anahtarı
      "etiket":     "Anlamını seç",        # küçük gri soru tipi etiketi
      "soru":       "aim",                 # büyük soru metni
      "alt":        "",                    # isteğe bağlı küçük yardımcı satır
      "cumle":      False,                 # soru bir cümle mi (boşluklu)
      "secenekler": ["amaç, hedef", …],    # 4 şık
      "dogru":      2,                     # doğru şıkkın sırası
      "aciklama":   "aim — amaç, hedef",   # cevaptan sonraki TEK satır
      "bicimler":   [{"metin", "anlam"}],  # yalnızca kelime biçimi: yanlışta gösterilir
      "kelimeler":  [12],                  # cevabı kaydedilecek kelime id'leri
    }

Eşleştirmede şıklar yerine `sol` (kelimeler), `sag` (anlamlar, karışık) ve
`eslesme` (her sol öğenin sag'daki doğru sırası) bulunur.

İki kesin kural:
  - TEK DOĞRU: çeldirici, doğru cevapla aynı anlamı taşıyamaz. Türkçe
    anlamlar virgülle parçalanıp karşılaştırılır; birbirine bağlı (eş, zıt,
    basit, karıştırılan) kelimeler çeldirici olmaz.
  - TÜR ETİKETİ YOK (rapor 12.1): hiçbir soruda, şıkta ya da açıklamada
    isim/fiil/sıfat/zarf yazmaz, gramer kuralı anlatılmaz.
"""

import random
import re

from django.db.models import Count, Prefetch, Q

from words import inflect
from words.models import (
    Collocation, Meaning, PartOfSpeech, RelationType, UserWordLink, Word, WordForm, WordRelation,
)

from . import seviye as seviye_mod
from .models import BaglacCumlesi


# ----------------------------------------------------------------------
# Tipler
# ----------------------------------------------------------------------

TIP_ANLAM = "anlam"
TIP_ACIKLAMA = "aciklama"
TIP_ESLESTIRME = "eslestirme"
TIP_FIIL = "fiil"
TIP_BICIM = "bicim"
TIP_ILISKI = "iliski"
TIP_BAGLAC = "baglac"
TIP_ESDIZIM = "esdizim"

# Deneme Sınavı'nın tip seçiminde görünen sıra, adlar ve açılış ekranındaki
# minicik örnek (ne tür bir soru olduğu bir bakışta anlaşılsın; defter teması, rapor 18.12).
TIPLER = {
    TIP_ANLAM: {"ad": "Kelime ↔ anlam", "not": "Listenden, iki yönlü", "ornek": "reluctant → isteksiz"},
    TIP_ACIKLAMA: {"ad": "Kelime ↔ İngilizce açıklama", "not": "Listenden", "ornek": "unwilling to do sth → reluctant"},
    TIP_ESLESTIRME: {"ad": "Eşleştirme", "not": "Listenden, dört kelime bir arada", "ornek": "4 kelime ⇄ 4 anlam"},
    TIP_FIIL: {"ad": "2. ve 3. hâller", "not": "go · went · gone gibi, listeden bağımsız", "ornek": "go · ___ · gone"},
    TIP_BICIM: {"ad": "Hangi biçimi gelir?", "not": "Seviyendeki kelime aileleri", "ornek": "She sang ___. (happy / happily)"},
    TIP_ILISKI: {"ad": "Eş / zıt / daha basit", "not": "Listende olmayan kelimeler", "ornek": "big = large · hot ≠ cold"},
    TIP_BAGLAC: {"ad": "Bağlaç ve ifadeler", "not": "Seviyene göre cümleler", "ornek": "___, it was cheap. (However)"},
    TIP_ESDIZIM: {"ad": "Eş dizim", "not": "make, take, do, give, have", "ornek": "___ a decision → make"},
}

KARISIK = "karisik"
SECENEK_SAYISI = 4
BOSLUK = "_____"

# Bu tiplerin kaynağı kullanıcının listesi.
LISTE_TIPLERI = (TIP_ANLAM, TIP_ACIKLAMA, TIP_ESLESTIRME)


def _ortak():
    """Herkesin görebildiği kelimeler (kur ya da herkese açık)."""
    return Q(isBaseWord=True) | Q(visibility="public")


def _anlamli(qs):
    return qs.prefetch_related(Prefetch("meanings", queryset=Meaning.objects.order_by("sort_order", "id")))


# ----------------------------------------------------------------------
# Tek doğru güvencesi: Türkçe anlam parçaları
# ----------------------------------------------------------------------

def _kucuk(metin):
    return (metin or "").replace("I", "ı").replace("İ", "i").lower()


def tr_parcalar(metin):
    """"(bir şeyi) bitirmek, sona erdirmek" -> {"bitirmek", "sona erdirmek"}"""
    metin = re.sub(r"\([^)]*\)", " ", _kucuk(metin))
    parcalar = re.split(r"[,;/]|\bveya\b|\bya da\b", metin)
    return {re.sub(r"\s+", " ", p).strip(" .-!?'\"") for p in parcalar} - {""}


def kelime_parcalari(word):
    """Kelimenin BÜTÜN anlamlarının Türkçe parçaları."""
    sonuc = set()
    for anlam in word.meanings.all():
        sonuc |= tr_parcalar(anlam.meaning_tr)
    return sonuc


def _ilk_anlam(word):
    for anlam in word.meanings.all():
        if (anlam.meaning_tr or "").strip():
            return anlam
    return None


def bagli_idler(word_ids):
    """Bu kelimelere herhangi bir bağla (eş, zıt, basit, karıştırılan) bağlı kelimeler."""
    ids = set(word_ids)
    sonuc = set()
    for a, b in WordRelation.objects.filter(
            Q(from_word_id__in=ids) | Q(to_word_id__in=ids)).values_list("from_word_id", "to_word_id"):
        sonuc.update((a, b))
    return sonuc - ids


def _aday_akisi(katmanlar, haric_idler, blok=40):
    """
    Çeldirici adayları: katman katman (aynı tür + seviye, aynı tür, herhangi)
    rastgele kelimeler. Her kelime bir kez gelir.
    """
    goruldu = set(haric_idler)
    for filtre in katmanlar:
        qs = _anlamli(Word.objects.filter(_ortak()).filter(**filtre)
                      .exclude(id__in=goruldu).order_by("?")[:blok])
        for w in qs:
            if w.id not in goruldu:
                goruldu.add(w.id)
                yield w


def _katmanlar(word):
    return [{"pos": word.pos, "cefr": word.cefr}, {"pos": word.pos}, {}]


def _sec(akis, uygun, adet=SECENEK_SAYISI - 1):
    secilen = []
    for aday in akis:
        if uygun(aday, secilen):
            secilen.append(aday)
            if len(secilen) == adet:
                break
    return secilen


def _maskele(metin, yuzeyler):
    """Metinde geçen kelimeyi (ve çekimlerini) boşlukla örter: açıklama cevabı ele vermesin."""
    for y in sorted({y for y in yuzeyler if y}, key=len, reverse=True):
        metin = re.sub(rf"(?<![A-Za-z]){re.escape(y)}(?![A-Za-z])", BOSLUK, metin, flags=re.I)
    return metin


def _yuzeyler(word):
    return {word.text.lower()} | {f.surface.lower() for f in word.forms.all()}


def _soru(tip, etiket, soru, dogru_metin, celdiriciler, aciklama, kelimeler, rng,
          alt="", cumle=False, bicimler=None):
    """Şıkları karıştırıp soru sözlüğünü kurar. bicimler şıklarla aynı sırada verilir."""
    secenekler = [dogru_metin] + list(celdiriciler)
    sira = list(range(len(secenekler)))
    rng.shuffle(sira)
    soru_s = {
        "tip": tip, "etiket": etiket, "soru": soru, "alt": alt, "cumle": cumle,
        "secenekler": [secenekler[i] for i in sira],
        "dogru": sira.index(0),
        "aciklama": aciklama,
        "kelimeler": list(kelimeler),
    }
    if bicimler is not None:
        soru_s["bicimler"] = [bicimler[i] for i in sira]
    return soru_s


def karistir(soru, rng=None):
    """Aynı soruyu şıkları yeniden karıştırılmış olarak döndürür (Yanlışları tekrar çöz)."""
    rng = rng or random
    yeni = dict(soru)
    if soru["tip"] == TIP_ESLESTIRME:
        sira = list(range(len(soru["sag"])))
        rng.shuffle(sira)                       # yeni sag[j] = eski sag[sira[j]]
        yeni["sag"] = [soru["sag"][i] for i in sira]
        yeni["eslesme"] = [sira.index(e) for e in soru["eslesme"]]
        return yeni
    sira = list(range(len(soru["secenekler"])))
    rng.shuffle(sira)
    yeni["secenekler"] = [soru["secenekler"][i] for i in sira]
    yeni["dogru"] = sira.index(soru["dogru"])
    if "bicimler" in soru:
        yeni["bicimler"] = [soru["bicimler"][i] for i in sira]
    return yeni


# ----------------------------------------------------------------------
# 1) Kelime ↔ anlam (liste)
# ----------------------------------------------------------------------

def anlam_sorusu(word, rng, yon=None):
    anlam = _ilk_anlam(word)
    if anlam is None:
        return None
    yon = yon or rng.choice(("en_tr", "tr_en"))
    hedef = kelime_parcalari(word)
    haric = {word.id} | bagli_idler([word.id])
    metin = word.text.lower()

    if yon == "en_tr":
        def uygun(aday, secilen):
            a = _ilk_anlam(aday)
            if a is None or aday.text.lower() == metin:
                return False
            p = tr_parcalar(a.meaning_tr)
            if not p or p & hedef:
                return False
            return all(not (p & tr_parcalar(_ilk_anlam(s).meaning_tr)) for s in secilen)

        secilen = _sec(_aday_akisi(_katmanlar(word), haric), uygun)
        if len(secilen) < SECENEK_SAYISI - 1:
            return None
        return _soru(TIP_ANLAM, "Anlamını seç", word.text, anlam.meaning_tr,
                     [_ilk_anlam(s).meaning_tr for s in secilen],
                     f"{word.text} — {anlam.meaning_tr}", [word.id], rng)

    istenen = tr_parcalar(anlam.meaning_tr)

    def uygun(aday, secilen):
        if aday.text.lower() == metin or any(s.text.lower() == aday.text.lower() for s in secilen):
            return False
        return _ilk_anlam(aday) is not None and not (kelime_parcalari(aday) & (istenen | hedef))

    secilen = _sec(_aday_akisi(_katmanlar(word), haric), uygun)
    if len(secilen) < SECENEK_SAYISI - 1:
        return None
    return _soru(TIP_ANLAM, "Kelimesini seç", anlam.meaning_tr, word.text,
                 [s.text for s in secilen], f"{anlam.meaning_tr} — {word.text}", [word.id], rng)


# ----------------------------------------------------------------------
# 2) Kelime ↔ İngilizce açıklama (liste)
# ----------------------------------------------------------------------

def _tanimli_anlam(word):
    for anlam in word.meanings.all():
        if (anlam.definition or "").strip():
            return anlam
    return None


def aciklama_sorusu(word, rng, yon=None):
    anlam = _tanimli_anlam(word)
    if anlam is None:
        return None
    yon = yon or rng.choice(("tanim_kelime", "kelime_tanim"))
    hedef = kelime_parcalari(word)
    haric = {word.id} | bagli_idler([word.id])
    metin = word.text.lower()
    maske = _yuzeyler(word)
    tanim = _maskele(anlam.definition.strip(), maske)
    aciklama = f"{word.text} — {anlam.meaning_tr}"

    def uygun(aday, secilen):
        if aday.text.lower() == metin or any(s.text.lower() == aday.text.lower() for s in secilen):
            return False
        if yon == "kelime_tanim" and _tanimli_anlam(aday) is None:
            return False
        return _ilk_anlam(aday) is not None and not (kelime_parcalari(aday) & hedef)

    secilen = _sec(_aday_akisi(_katmanlar(word), haric), uygun)
    if len(secilen) < SECENEK_SAYISI - 1:
        return None
    if yon == "tanim_kelime":
        return _soru(TIP_ACIKLAMA, "Açıklamaya uyan kelimeyi seç", tanim, word.text,
                     [s.text for s in secilen], aciklama, [word.id], rng, cumle=True)
    return _soru(TIP_ACIKLAMA, "İngilizce açıklamasını seç", word.text, tanim,
                 [_maskele(_tanimli_anlam(s).definition.strip(), maske) for s in secilen],
                 aciklama, [word.id], rng)


# ----------------------------------------------------------------------
# 3) Eşleştirme (liste)
# ----------------------------------------------------------------------

def eslestirme_gruplari(kelimeler, adet):
    """Anlamları birbirine karışmayan 4'lü gruplar (en çok `adet` tane)."""
    gruplar, grup, parcalar = [], [], set()
    for w in kelimeler:
        a = _ilk_anlam(w)
        if a is None:
            continue
        p = kelime_parcalari(w)
        if p & parcalar or any(g.text.lower() == w.text.lower() for g in grup):
            continue
        grup.append(w)
        parcalar |= p
        if len(grup) == SECENEK_SAYISI:
            gruplar.append(grup)
            grup, parcalar = [], set()
            if len(gruplar) == adet:
                break
    return gruplar


def eslestirme_sorusu(grup, rng):
    sol = [w.text for w in grup]
    anlamlar = [_ilk_anlam(w).meaning_tr for w in grup]
    sira = list(range(len(grup)))
    rng.shuffle(sira)
    return {
        "tip": TIP_ESLESTIRME, "etiket": "Eşleştir",
        "soru": "Kelimeleri anlamlarıyla eşleştir", "alt": "", "cumle": False,
        "sol": sol,
        "sag": [anlamlar[i] for i in sira],
        "eslesme": [sira.index(i) for i in range(len(grup))],
        "aciklama": " · ".join(f"{t} — {a}" for t, a in zip(sol, anlamlar)),
        "kelimeler": [w.id for w in grup],
    }


# ----------------------------------------------------------------------
# 4) Fiilin 2./3. hâli (bütün düzensiz fiiller, listeden bağımsız)
# ----------------------------------------------------------------------

# Modal ve yardımcılar: "2./3. hâl" sorusuna uymaz.
FIIL_HARIC = {"can", "will", "shall", "may", "must", "be"}

# Veride tek biçim yazılı ama başka biçimi de doğru kabul edilen fiiller.
# Doğru kabul edilen hiçbir biçim çeldirici olamaz (tek doğru kuralı).
EK_BICIMLER = {
    "get": {"v3": {"got"}}, "prove": {"v3": {"proved"}}, "disprove": {"v3": {"disproved"}},
    "beat": {"v3": {"beat"}}, "show": {"v3": {"showed"}}, "sew": {"v3": {"sewed"}},
    "sow": {"v3": {"sowed"}}, "swell": {"v3": {"swelled"}}, "strew": {"v3": {"strewed"}},
    "bear": {"v3": {"born"}}, "fit": {"v2": {"fitted"}, "v3": {"fit"}},
    "wet": {"v2": {"wet"}, "v3": {"wetted"}}, "wed": {"v2": {"wed"}, "v3": {"wedded"}},
    "light": {"v2": {"lighted"}, "v3": {"lighted"}}, "speed": {"v2": {"speeded"}, "v3": {"speeded"}},
    "dwell": {"v2": {"dwelled"}, "v3": {"dwelled"}}, "kneel": {"v2": {"kneeled"}, "v3": {"kneeled"}},
    "knit": {"v2": {"knitted"}, "v3": {"knitted"}}, "spit": {"v2": {"spit"}, "v3": {"spit"}},
    "shrink": {"v2": {"shrunk"}}, "sink": {"v2": {"sunk"}}, "spring": {"v2": {"sprung"}},
    "stink": {"v2": {"stunk"}}, "strive": {"v2": {"strived"}, "v3": {"strived"}},
    "weave": {"v2": {"weaved"}, "v3": {"weaved"}}, "shine": {"v2": {"shined"}, "v3": {"shined"}},
    "hang": {"v2": {"hanged"}, "v3": {"hanged"}}, "bust": {"v2": {"bust"}, "v3": {"busted"}},
    "blend": {"v3": {"blended"}}, "misspell": {"v2": {"misspelt"}, "v3": {"misspelled"}},
    "unlearn": {"v2": {"unlearnt"}, "v3": {"unlearned"}}, "heave": {"v2": {"hove"}, "v3": {"heaved"}},
    "shear": {"v3": {"sheared"}}, "shoe": {"v2": {"shod"}, "v3": {"shoed"}},
    "alight": {"v2": {"alit"}, "v3": {"alighted"}}, "bid": {"v2": {"bade"}, "v3": {"bidden"}},
    "quit": {"v2": {"quitted"}, "v3": {"quitted"}}, "tread": {"v3": {"trod"}},
    "lie": {"v2": {"lied"}, "v3": {"lied"}}, "slay": {"v2": {"slayed"}, "v3": {"slayed"}},
    "wind": {"v2": {"winded"}, "v3": {"winded"}}, "cleave": {"v2": {"clove", "cleaved"}, "v3": {"cloven", "cleaved"}},
    "beget": {"v2": {"begat"}}, "stride": {"v3": {"strode"}}, "awake": {"v2": {"awaked"}, "v3": {"awaked"}},
    "broadcast": {"v2": {"broadcasted"}, "v3": {"broadcasted"}},
    "forecast": {"v2": {"forecasted"}, "v3": {"forecasted"}},
    "input": {"v2": {"inputted"}, "v3": {"inputted"}}, "output": {"v2": {"outputted"}, "v3": {"outputted"}},
    "rid": {"v2": {"ridded"}, "v3": {"ridded"}}, "smite": {"v3": {"smit"}},
}


def _bicimler(metin):
    return [b.strip().lower() for b in re.split(r"[/,]|\bor\b", metin or "") if b.strip()]


def duzensiz_fiil_mi(word):
    return (word.pos == PartOfSpeech.VERB and " " not in word.text
            and word.text.lower() not in FIIL_HARIC and bool(word.v2Form)
            and inflect.duzensiz_fiil_mi(word.text, word.v2Form, word.v3Form))


def duzensiz_fiiller():
    """Sözlükteki bütün düzensiz fiiller (words.inflect.duzensiz_fiil_mi ile)."""
    qs = (Word.objects.filter(_ortak(), pos=PartOfSpeech.VERB)
          .exclude(text__contains=" ").exclude(v2Form__isnull=True).exclude(v2Form=""))
    return [w for w in qs if duzensiz_fiil_mi(w)]


def fiil_sorusu(word, rng, hangi=None):
    """
    "go" -> 2. hâli? Şıklar yalnızca GERÇEK biçimlerden: diğer hâl, yalın
    hâl, -ing ve -s (uydurma "goed" yok, rapor 12.3). Doğru kabul edilen
    hiçbir biçim çeldirici olmaz.

    cut/put/hit gibi üç hâli aynı fiiller de sorulur (rapor 18.28): onlarda
    gerçek çeldirici yalnızca -ing ve -s hâlidir, soru 3 şıkla gelir
    ("cutted" gibi uydurma biçim yine YOK).
    """
    kok = word.text.lower()
    cekim = inflect.cekimler(kok, "verb")
    c = cekim["cekim"]
    v2 = _bicimler(word.v2Form) or _bicimler(c["v2Form"])
    v3 = _bicimler(word.v3Form) or _bicimler(c["v3Form"])
    if not v2 or not v3:
        return None
    ek = EK_BICIMLER.get(kok, {})
    diger = {d.lower() for d in cekim["diger_yazimlar"]}
    kabul = {
        "v2": set(v2) | set(_bicimler(c["v2Form"])) | ek.get("v2", set()) | diger,
        "v3": set(v3) | set(_bicimler(c["v3Form"])) | ek.get("v3", set()) | diger,
    }
    goster = {"v2": v2[0], "v3": v3[0]}
    # Üç hâli aynı fiil (cut · cut · cut): 3 şık yeter.
    ayni_bicimli = goster["v2"] == goster["v3"] == kok
    gereken = 2 if ayni_bicimli else SECENEK_SAYISI - 1
    anlam = _ilk_anlam(word)
    sira = [hangi] if hangi else rng.sample(["v2", "v3"], 2)
    for h in sira:
        obur = "v3" if h == "v2" else "v2"
        dogru = goster[h]
        adaylar = [goster[obur]]
        diger_adaylar = [kok, c["ingForm"], c["sVersion"]]
        rng.shuffle(diger_adaylar)
        celdirici = []
        for a in adaylar + diger_adaylar:
            a = (a or "").strip().lower()
            if a and a != dogru and a not in kabul[h] and a not in celdirici:
                celdirici.append(a)
        if len(celdirici) < gereken:
            continue
        return _soru(
            TIP_FIIL, "2. hâlini seç" if h == "v2" else "3. hâlini seç", word.text, dogru,
            celdirici[:SECENEK_SAYISI - 1], f"{word.text} · {goster['v2']} · {goster['v3']}",
            [word.id], rng, alt=anlam.meaning_tr if anlam else "",
        )
    return None


# ----------------------------------------------------------------------
# 5) Kelime biçimi: "hangi biçimi gelir?" (seviyedeki aileler)
# ----------------------------------------------------------------------

# Şıklar farklı türlerden seçilir (türler EKRANDA YAZMAZ): aynı türden iki
# aile üyesi aynı boşluğa uyabilir (action / activity), farklı türden
# olanlar uymaz. Dört şık için ailede dört ayrı tür gerekir.
BICIM_TURLERI = (PartOfSpeech.NOUN, PartOfSpeech.VERB, PartOfSpeech.ADJECTIVE, PartOfSpeech.ADVERB)


def dort_turlu_aileler():
    return (Word.objects.filter(_ortak(), pos__in=BICIM_TURLERI).exclude(text__contains=" ")
            .values("family_id").annotate(n=Count("pos", distinct=True))
            .filter(n__gte=len(BICIM_TURLERI)).values("family_id"))


def _kelime_gecen_cumle(word, rng):
    desen = re.compile(rf"(?<![A-Za-z-]){re.escape(word.text)}(?![A-Za-z-])", re.I)
    cumleler = [e.text for a in word.meanings.all() for e in a.examples.all() if desen.search(e.text)]
    if not cumleler:
        return None
    return desen.sub(BOSLUK, rng.choice(cumleler))


def bicim_sorusu(word, rng):
    if word.pos not in BICIM_TURLERI or " " in word.text:
        return None
    cumle = _kelime_gecen_cumle(word, rng)
    if not cumle:
        return None
    metin = word.text.lower()
    hedef_cekimler = _yuzeyler(word) | {y for y, _ in inflect.forms_for(word.text, word.pos,
                                                                        word.v2Form, word.v3Form)}
    uyeler = list(_anlamli(Word.objects.filter(_ortak(), family_id=word.family_id, pos__in=BICIM_TURLERI)
                           .exclude(id=word.id).exclude(text__contains=" ").order_by("?")))
    # Aynı yazımı hedefin türünde de kullanılan üye boşluğa uyabilir
    # ("pass" hem fiil hem isim; "The ___ was dark"): çeldirici olamaz.
    metinler = {u.text.lower() for u in uyeler}
    ayni_turde = ({t.lower() for t in Word.objects.filter(text__in=metinler, pos=word.pos)
                   .values_list("text", flat=True)}
                  | {t.lower() for t in WordForm.objects.filter(surface__in=metinler, word__pos=word.pos)
                     .values_list("surface", flat=True)})
    secilen = {}
    for u in uyeler:
        t = u.text.lower()
        if (u.pos == word.pos or u.pos in secilen or t in hedef_cekimler or t in ayni_turde
                or t == metin or any(s.text.lower() == t for s in secilen.values())
                or _ilk_anlam(u) is None):
            continue
        secilen[u.pos] = u
    if len(secilen) < SECENEK_SAYISI - 1:
        return None
    celdiriciler = list(secilen.values())[:SECENEK_SAYISI - 1]
    anlam = _ilk_anlam(word)
    bicimler = [{"metin": w.text, "anlam": _ilk_anlam(w).meaning_tr} for w in [word] + celdiriciler]
    return _soru(TIP_BICIM, "Boşluğa hangisi gelir?", cumle, word.text,
                 [w.text for w in celdiriciler], f"{word.text} — {anlam.meaning_tr}",
                 [word.id], rng, cumle=True, bicimler=bicimler)


# ----------------------------------------------------------------------
# 6) Eş / zıt / daha basit anlamlı (listede OLMAYAN kelimeler)
# ----------------------------------------------------------------------

ILISKI_ETIKETLERI = {
    RelationType.SYNONYM: ("Eş anlamlısını seç", "≈"),
    RelationType.ANTONYM: ("Zıt anlamlısını seç", "↔"),
    RelationType.SIMPLER: ("Daha basit karşılığını seç", "≈"),
}
# Soru ekranındaki damga: "es" yeşil =, "zit" kırmızı ≠, "basit" mavi ≈ (soru.html).
ILISKI_TURLERI = {
    RelationType.SYNONYM: "es",
    RelationType.ANTONYM: "zit",
    RelationType.SIMPLER: "basit",
}
UST_SEVIYE_ORANI = 0.2      # ~%20 bir üst seviye, ~%80 kendi seviyesi


def iliski_sorusu(bag, rng):
    """bag: anlama bağlı WordRelation (D1). Soru o anlamın Türkçesiyle birlikte sorulur."""
    kaynak, dogru, anlam = bag.from_word, bag.to_word, bag.meaning
    if anlam is None or bag.type not in ILISKI_ETIKETLERI or _ilk_anlam(dogru) is None:
        return None
    etiket, isaret = ILISKI_ETIKETLERI[bag.type]
    haric = {kaynak.id, dogru.id} | bagli_idler([kaynak.id])
    yasak = kelime_parcalari(dogru) | tr_parcalar(anlam.meaning_tr) | kelime_parcalari(kaynak)
    yasak_metin = {kaynak.text.lower(), dogru.text.lower()}

    def uygun(aday, secilen):
        t = aday.text.lower()
        if t in yasak_metin or any(s.text.lower() == t for s in secilen):
            return False
        return _ilk_anlam(aday) is not None and not (kelime_parcalari(aday) & yasak)

    akis = _aday_akisi(_katmanlar(dogru), haric | bagli_idler([dogru.id]))
    secilen = _sec(akis, uygun)
    if len(secilen) < SECENEK_SAYISI - 1:
        return None
    soru = _soru(TIP_ILISKI, etiket, kaynak.text, dogru.text, [s.text for s in secilen],
                 f"{kaynak.text} ({anlam.meaning_tr}) {isaret} {dogru.text}: {_ilk_anlam(dogru).meaning_tr}",
                 [kaynak.id], rng, alt=anlam.meaning_tr)
    # Ekranda büyük, renkli damga için (Efe, 2 Ekim: "eş mi zıt mı, hemen anlaşılsın").
    soru["iliski"] = ILISKI_TURLERI[bag.type]
    return soru


def iliski_sorulari(user, seviye, rng, adet, haric_kaynaklar=()):
    liste = UserWordLink.objects.filter(user=user).values("word_id")
    ust = seviye_mod.bir_ust(seviye)
    sorular, kullanilan = [], set(haric_kaynaklar)
    ust_adet = sum(1 for _ in range(adet) if rng.random() < UST_SEVIYE_ORANI)
    plan = [(ust, ust_adet), (seviye, adet - ust_adet)]
    # Bir seviyede yetmezse kalan komşu seviyelerden tamamlanır.
    for s in seviye_mod.komsular(seviye):
        plan.append((s, adet))
    for sev, hedef in plan:
        if len(sorular) >= adet:
            break
        hedef = min(hedef, adet - len(sorular))
        if hedef <= 0:
            continue
        uretilen = 0
        baglar = (WordRelation.objects
                  .filter(meaning__isnull=False, type__in=list(ILISKI_ETIKETLERI),
                          from_word__cefr=sev)
                  .filter(Q(from_word__isBaseWord=True) | Q(from_word__visibility="public"))
                  .filter(Q(to_word__isBaseWord=True) | Q(to_word__visibility="public"))
                  .exclude(from_word_id__in=liste)
                  .select_related("from_word", "to_word", "meaning")
                  .prefetch_related("from_word__meanings", "to_word__meanings")
                  .order_by("?")[:hedef * 4])
        for bag in baglar:
            if uretilen >= hedef:
                break
            if bag.from_word_id in kullanilan:
                continue
            soru = iliski_sorusu(bag, rng)
            if soru:
                kullanilan.add(bag.from_word_id)
                sorular.append(soru)
                uretilen += 1
    return sorular


# ----------------------------------------------------------------------
# 7) Bağlaç / ifade (D2 havuzu)
# ----------------------------------------------------------------------

def baglac_havuzu():
    return BaglacCumlesi.objects.filter(denetlendi=True)


def baglac_sorusu(kayit, rng):
    dogru = kayit.dogru.strip()
    celdiriciler = []
    for c in kayit.celdiriciler or []:
        c = str(c).strip()
        if c and c.lower() != dogru.lower() and c.lower() not in {x.lower() for x in celdiriciler}:
            celdiriciler.append(c)
    if len(celdiriciler) < SECENEK_SAYISI - 1 or BaglacCumlesi.BOSLUK not in kayit.cumle:
        return None
    rng.shuffle(celdiriciler)
    kelimeler = []
    return _soru(TIP_BAGLAC, "Boşluğa hangisi gelir?",
                 kayit.cumle.replace(BaglacCumlesi.BOSLUK, BOSLUK, 1), dogru,
                 celdiriciler[:SECENEK_SAYISI - 1], kayit.aciklama or f"Doğrusu: {dogru}",
                 kelimeler, rng, cumle=True)


def baglac_sorulari(seviye, rng, adet):
    sorular = []
    for sev in seviye_mod.komsular(seviye):
        for kayit in baglac_havuzu().filter(cefr=sev).order_by("?")[:adet * 2]:
            if len(sorular) >= adet:
                return sorular
            soru = baglac_sorusu(kayit, rng)
            if soru:
                sorular.append(soru)
    return sorular


# ----------------------------------------------------------------------
# 8) Eş dizim — v1'de yalnızca hafif fiiller (D3 ile doğrulanmış çeldiriciler)
# ----------------------------------------------------------------------

HAFIF_FIILLER = ("make", "take", "do", "give", "have")


def hafif_fiilli_esdizimler():
    """Hafif fiille başlayan eş dizimler (make a decision, take a breath …)."""
    kosul = Q()
    for f in HAFIF_FIILLER:
        kosul |= Q(pattern__istartswith=f + " ")
    return Collocation.objects.filter(kosul)


def esdizim_havuzu():
    """En az 3 DOĞRULANMIŞ çeldiricisi olan hafif fiilli eş dizimler."""
    return (hafif_fiilli_esdizimler()
            .annotate(dogrulanmis=Count("celdiriciler", filter=Q(celdiriciler__gercekten_yanlis=True)))
            .filter(dogrulanmis__gte=SECENEK_SAYISI - 1))


def esdizim_sorusu(esdizim, rng):
    fiil, _, kalan = esdizim.pattern.strip().partition(" ")
    fiil = fiil.lower()
    if fiil not in HAFIF_FIILLER or not kalan:
        return None
    celdiriciler = sorted({c.celdirici.strip().lower() for c in esdizim.celdiriciler.all()
                           if c.gercekten_yanlis is True} - {fiil, ""})
    if len(celdiriciler) < SECENEK_SAYISI - 1:
        return None
    rng.shuffle(celdiriciler)
    turkce = esdizim.meaning_tr or esdizim.meaning.meaning_tr
    return _soru(TIP_ESDIZIM, "Boşluğa hangisi gelir?", f"{BOSLUK} {kalan}", fiil,
                 celdiriciler[:SECENEK_SAYISI - 1], f"{esdizim.pattern} — {turkce}",
                 [esdizim.meaning.word_id], rng, alt=turkce)


def esdizim_sorulari(user, seviye, rng, adet):
    """Önce listedeki kelimelerin eş dizimleri, yetmezse seviyeden, o da yetmezse hepsinden."""
    havuz = (esdizim_havuzu().select_related("meaning", "meaning__word")
             .prefetch_related("celdiriciler"))
    liste = UserWordLink.objects.filter(user=user).values("word_id")
    katmanlar = [havuz.filter(meaning__word_id__in=liste), havuz.filter(meaning__word__cefr=seviye), havuz]
    sorular, kullanilan = [], set()
    for qs in katmanlar:
        for e in qs.order_by("?")[:adet * 2]:
            if len(sorular) >= adet:
                return sorular
            if e.id in kullanilan:
                continue
            soru = esdizim_sorusu(e, rng)
            if soru:
                kullanilan.add(e.id)
                sorular.append(soru)
    return sorular


# ----------------------------------------------------------------------
# Tur kurma
# ----------------------------------------------------------------------

HIZLI_SORU_SAYISI = 10
SORU_SAYILARI = (5, 10, 15, 20)
VARSAYILAN_SORU_SAYISI = 10


def varsayilan_soru_sayisi(user):
    """Deneme Sınavı'nın açılışta seçili gelen soru sayısı: Ayarlar'dan (rapor 18.26)."""
    try:
        sayi = user.mysettings.egzersiz_soru_sayisi
    except Exception:   # ayar satırı olmayan eski kullanıcılar
        return VARSAYILAN_SORU_SAYISI
    return sayi if sayi in SORU_SAYILARI else VARSAYILAN_SORU_SAYISI


def liste_kelimeleri(user):
    """
    Kullanıcının listesi, tekrar kuralının öncelik sırasıyla (rapor 18.2):
    önce hiç görülmemişler, sonra en uzun süredir görülmeyenler, sonra en
    çok zorlanılanlar (learnpass/tekrar.py). L&P ile aynı sıra.
    """
    from learnpass.tekrar import liste_sirasi
    sira = liste_sirasi(user)
    kelimeler = {w.id: w for w in _anlamli(Word.objects.filter(id__in=sira)).prefetch_related("forms")}
    return [kelimeler[i] for i in sira if i in kelimeler]


def tip_durumlari(user):
    """
    Deneme Sınavı'nın tip seçimi için her tipin durumu:
    [{"anahtar", "ad", "not", "aktif", "pasif_notu"}]
    Veri yoksa tip pasif görünür ve karışık turda atlanır.
    """
    liste_sayisi = UserWordLink.objects.filter(user=user).count()
    tanimli = (UserWordLink.objects.filter(user=user, word__meanings__definition__gt="")
               .values("word_id").distinct().count())
    pasif = {
        TIP_ANLAM: None if liste_sayisi >= 1 else "Listene kelime ekleyince açılır",
        TIP_ACIKLAMA: None if tanimli >= 1 else "Listene kelime ekleyince açılır",
        TIP_ESLESTIRME: None if liste_sayisi >= SECENEK_SAYISI else "Listende en az 4 kelime olunca açılır",
        TIP_FIIL: None, TIP_BICIM: None, TIP_ILISKI: None,
        TIP_BAGLAC: None if baglac_havuzu().exists() else "Yakında",
        TIP_ESDIZIM: None if esdizim_havuzu().exists() else "Yakında",
    }
    return [{"anahtar": k, "ad": v["ad"], "not": v["not"], "ornek": v["ornek"], "aktif": pasif[k] is None,
             "pasif_notu": pasif[k] or ""} for k, v in TIPLER.items()]


def _liste_sorulari(tip, kelimeler, rng, adet, haric=()):
    """haric: bu turda başka tipte zaten sorulmuş kelimeler; önce sorulmamışlar gelir."""
    kelimeler = list(kelimeler)   # öncelik sırasında (liste_kelimeleri)
    kelimeler.sort(key=lambda w: w.id in haric)
    if tip == TIP_ESLESTIRME:
        return [eslestirme_sorusu(g, rng) for g in eslestirme_gruplari(kelimeler, adet)]
    uret = anlam_sorusu if tip == TIP_ANLAM else aciklama_sorusu
    sorular = []
    for w in kelimeler:
        if len(sorular) >= adet:
            break
        soru = uret(w, rng)
        if soru:
            sorular.append(soru)
    return sorular


def tip_sorulari(tip, user, seviye, rng, adet, haric=()):
    """Bir tipten en çok `adet` soru. Veri yetmezse daha az (hiç yoksa boş liste)."""
    if adet <= 0:
        return []
    if tip in LISTE_TIPLERI:
        return _liste_sorulari(tip, liste_kelimeleri(user), rng, adet, haric)
    if tip == TIP_FIIL:
        fiiller = duzensiz_fiiller()
        rng.shuffle(fiiller)
        sorular = []
        for w in fiiller:
            if len(sorular) >= adet:
                break
            soru = fiil_sorusu(w, rng)
            if soru:
                sorular.append(soru)
        return sorular
    if tip == TIP_BICIM:
        sorular, kullanilan = [], set()
        for sev in seviye_mod.komsular(seviye):
            anlamlar = Meaning.objects.order_by("sort_order", "id").prefetch_related("examples")
            adaylar = (Word.objects.filter(_ortak(), cefr=sev, pos__in=BICIM_TURLERI,
                                           family_id__in=dort_turlu_aileler())
                       .exclude(text__contains=" ")
                       .prefetch_related(Prefetch("meanings", queryset=anlamlar), "forms")
                       .order_by("?")[:adet * 4])
            for w in adaylar:
                if len(sorular) >= adet:
                    return sorular
                if w.family_id in kullanilan:
                    continue
                soru = bicim_sorusu(w, rng)
                if soru:
                    kullanilan.add(w.family_id)
                    sorular.append(soru)
        return sorular
    if tip == TIP_ILISKI:
        return iliski_sorulari(user, seviye, rng, adet)
    if tip == TIP_BAGLAC:
        return baglac_sorulari(seviye, rng, adet)
    if tip == TIP_ESDIZIM:
        return esdizim_sorulari(user, seviye, rng, adet)
    return []


def hizli_sorular(user, rng=None):
    """
    Kısa Sınav (eski adıyla Hızlı Egzersiz): tam 10 soru (liste kısaysa listedeki kadar), yalnızca
    anlam, TR→EN ve EN→TR karışık, yalnızca kullanıcının listesinden.
    """
    rng = rng or random.Random()
    kelimeler = list(liste_kelimeleri(user))   # öncelik sırasında (rapor 18.2)
    yonler = ["en_tr", "tr_en"] * (HIZLI_SORU_SAYISI // 2)
    rng.shuffle(yonler)
    sorular = []
    for w in kelimeler:
        if len(sorular) >= HIZLI_SORU_SAYISI:
            break
        yon = yonler[len(sorular)]
        soru = anlam_sorusu(w, rng, yon=yon) or anlam_sorusu(w, rng, yon="tr_en" if yon == "en_tr" else "en_tr")
        if soru:
            sorular.append(soru)
    return sorular


def tempolu_sorular(user, tip, adet, rng=None):
    """
    Deneme Sınavı (eski adıyla Tempolu Egzersiz). tip: KARISIK ya da tek bir tip. Karışıkta pasif
    tipler (boş havuz, kısa liste) atlanır; bir tip yetmezse kalan soru
    diğerlerinden tamamlanır.
    """
    rng = rng or random.Random()
    seviye = seviye_mod.kullanici_seviyesi(user)
    aktifler = [d["anahtar"] for d in tip_durumlari(user) if d["aktif"]]
    if tip == KARISIK:
        tipler = aktifler
    else:
        tipler = [tip] if tip in aktifler else []
    if not tipler:
        return []

    sirali = list(tipler)
    rng.shuffle(sirali)
    pay = {t: 0 for t in tipler}
    for i in range(adet):
        pay[sirali[i % len(sirali)]] += 1

    sorular, eksik, kalanlar = [], 0, []
    for t in sirali:
        sorulan = {k for s in sorular for k in s.get("kelimeler") or ()}
        uretilen = tip_sorulari(t, user, seviye, rng, pay[t], haric=sorulan)
        sorular.extend(uretilen)
        eksik += pay[t] - len(uretilen)
        if len(uretilen) == pay[t]:
            kalanlar.append(t)
    # Yetmeyen tiplerin payı yetenlerden tamamlanır (aynı soru tekrar gelmesin).
    gorulen = {_soru_anahtari(s) for s in sorular}
    for t in kalanlar:
        if eksik <= 0:
            break
        for s in tip_sorulari(t, user, seviye, rng, eksik * 2):
            if eksik <= 0:
                break
            if _soru_anahtari(s) not in gorulen:
                gorulen.add(_soru_anahtari(s))
                sorular.append(s)
                eksik -= 1
    rng.shuffle(sorular)
    return sorular[:adet]


def _soru_anahtari(soru):
    return (soru["tip"], tuple(soru.get("kelimeler") or ()), soru["soru"])


# ----------------------------------------------------------------------
# Değerlendirme
# ----------------------------------------------------------------------

def degerlendir(soru, secim):
    """
    Cevabı değerlendirir. Döner: (dogru_mu, [(kelime_id | None, dogru_mu), …])
    ya da geçersiz secimde None.
    """
    kelimeler = soru.get("kelimeler") or []
    if soru["tip"] == TIP_ESLESTIRME:
        if (not isinstance(secim, list) or len(secim) != len(soru["eslesme"])
                or not all(isinstance(s, int) for s in secim)):
            return None
        tek_tek = [s == e for s, e in zip(secim, soru["eslesme"])]
        return all(tek_tek), list(zip(kelimeler, tek_tek))
    if not isinstance(secim, int) or not 0 <= secim < len(soru["secenekler"]):
        return None
    dogru_mu = secim == soru["dogru"]
    return dogru_mu, [(k, dogru_mu) for k in kelimeler] or [(None, dogru_mu)]


def istemci_sorusu(soru):
    """Tarayıcıya giden hâl: cevap verilmeden doğru şık ve açıklama gitmez."""
    return {k: v for k, v in soru.items()
            if k not in ("dogru", "eslesme", "aciklama", "bicimler", "kelimeler")}


def sonuc_verisi(soru, cevap):
    """Cevaptan sonra gösterilecek her şey."""
    veri = {"dogru_mu": cevap["dogru_mu"], "secim": cevap["secim"], "aciklama": soru["aciklama"]}
    if soru["tip"] == TIP_ESLESTIRME:
        veri["eslesme"] = soru["eslesme"]
    else:
        veri["dogru"] = soru["dogru"]
    # Kelime biçiminde YANLIŞ cevapta şıklardaki bütün biçimler anlamlarıyla.
    if soru["tip"] == TIP_BICIM and not cevap["dogru_mu"]:
        veri["bicimler"] = soru.get("bicimler", [])
    return veri


def dogru_cevap_metni(soru):
    if soru["tip"] == TIP_ESLESTIRME:
        return soru["aciklama"]
    return soru["secenekler"][soru["dogru"]]
