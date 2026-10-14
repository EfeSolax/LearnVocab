"""
3. AŞAMA — anlam doldurma: şema, denetim ve veritabanına yazma.

Birleşmiş ailelerin (ara-depo/aileler.json) her kelimesi için model
word_filling prompt'uyla anlamları üretir; burada denetlenir ve
veritabanına yazılır. Komut: manage.py aile_doldur.

Denetimin gövdesi eski hattın denetimi (words/enrich/checks.py ·
_anlami_denetle): Türkçe karşılık, mastar, cümle, eş dizim, kalıp
kontrolleri aynen kullanılıyor — o kurallar gerçek çıktıyla, beş ayrı
listede sınanarak oturdu, yeniden yazmak geri adım olurdu. Yeni olan:
şema (Efe'nin word_filling'deki alan adları), anlam başına CEFR, alanların
108'lik İngilizce liste olması ve yazıcının aile düzeyinde çalışması.

YENİ HATTA AİT KARARLAR
-----------------------
  - register: prompt "general" diyor, veritabanı "neutral" tutuyor; yazarken
    çevriliyor (general -> neutral).
  - cefr anlam başına (Meaning.cefr, migration 0017). Word.cefr = kelimenin
    EN KOLAY anlamının seviyesi (seçim ve çeldirici sorguları onu kullanıyor).
  - relations prompt'ta anlam başına; veritabanında da anlam başına
    (WordRelation.meaning, D1 — önceden kelime düzeyindeydi; eski satırlar
    iliskileri_anlama_bagla komutuyla bağlandı). Depodaki anlam cevabı
    veritabanındaki Meaning'e anlam_eslemesi ile eşleniyor (meaning_tr,
    sonra açıklama). Hedef kelime henüz veritabanında yoksa bağ kurulmuyor ama
    cevap depoda kalıyor; her çalıştırmanın sonunda depodaki BÜTÜN bağlar
    yeniden deneniyor (bag_tamamla). Liste büyüdükçe bağlar kendiliğinden
    tamamlanıyor.
  - Eş dizim ve kalıp TÜRÜ (verb_noun, preposition…) prompt'ta istenmiyor;
    kodla çıkarılıyor (esdizim_turu, kalip_turu). Çalışma sistemindeki
    soru üreticileri bu türlere bakıyor.
  - Anlam üst sınırı 3 (eski hat 2'ydi). Efe'nin prompt'u meet gibi üç
    anlamlı kelimeleri örnek veriyor; birbirinin tekrarı olan anlamlar
    yakın-anlam ve ortak-eş-dizim kontrolleriyle zaten atılıyor.
"""

import re
import unicodedata
import warnings
from typing import List, Literal

from django.db import transaction
from pydantic import BaseModel, Field

from words import inflect
from words.aile import turkce
from words.aile.schema import POS
from words.enrich import checks
from words.enrich.prompt import KATEGORILER

# `register` alanı BaseModel'in register metodunu gölgeliyor; alan adı
# prompt'la aynı kalsın diye uyarıyı susturuyoruz (enrich/schema.py'daki gibi).
warnings.filterwarnings("ignore", message='Field name "register"')
warnings.filterwarnings("ignore", message=".*non-serializable-default.*")
warnings.filterwarnings("ignore", message=".*is not JSON serializable.*")

# Kategoriler şemada KAPALI LİSTE (enum): model listede olmayan bir alan
# yazamaz. Önce (1. deneme) serbest metindi ve 185 anlamda 78 uydurma alan
# geldi (Psychology, Finance, Statistics…).
KATEGORI = Literal[tuple(KATEGORILER)]

EN_COK_ANLAM = 3
REGISTER_ESLEME = {"general": "neutral", "academic": "academic",
                   "formal": "formal", "slang": "slang"}
CEFR_SIRASI = ["A1", "A2", "B1", "B2", "C1", "C2"]


# ----------------------------------------------------------------------
# Şema — alan adları word_filling'deki gibi
# ----------------------------------------------------------------------

class Esdizim(BaseModel):
    collocation: str = Field(description="Somut kelimelerden eş dizim: 'make a decision'")
    meaning_tr: str
    example: str = Field(description="Eş dizimi GERÇEKTEN kullanan cümle")

    # Eski denetim (checks._anlami_denetle) alanı "pattern" adıyla okuyor.
    @property
    def pattern(self):
        return self.collocation

    @pattern.setter
    def pattern(self, deger):
        self.collocation = deger


class Kalip(BaseModel):
    pattern: str = Field(description="Yer tutuculu gramer kalıbı: 'depend on sth'")
    example: str
    note: str


class Bag(BaseModel):
    to_word: str
    type: Literal["simpler", "synonym", "antonym"]


class Anlam(BaseModel):
    meaning_tr: str
    definition: str
    sentiment: Literal["positive", "negative", "neutral"]
    register: Literal["general", "academic", "formal", "slang"]
    cefr: Literal["A1", "A2", "B1", "B2", "C1", "C2"]
    categories: List[KATEGORI]
    collocations: List[Esdizim]
    patterns: List[Kalip]
    sentences: List[str] = Field(description="TAM 5 cümle, kolaydan zora")
    relations: List[Bag]


class KelimeCevabi(BaseModel):
    found: bool
    skip_reason: str
    word: str
    type: POS
    meanings: List[Anlam]


# ----------------------------------------------------------------------
# Denetim
# ----------------------------------------------------------------------

def _t(metin):
    return checks.duzelt_tipografi((metin or "").strip())


def _tipografi(cevap):
    for anlam in cevap.meanings:
        anlam.meaning_tr = _t(anlam.meaning_tr)
        anlam.definition = _t(anlam.definition)
        anlam.sentences = [_t(c) for c in anlam.sentences]
        for e in anlam.collocations:
            e.collocation, e.meaning_tr, e.example = _t(e.collocation), _t(e.meaning_tr), _t(e.example)
        for k in anlam.patterns:
            k.pattern, k.example, k.note = _t(k.pattern), _t(k.example), _t(k.note)
        for b in anlam.relations:
            b.to_word = _t(b.to_word).lower()


_MIS = re.compile(r"m[ıiuü]ş$")
YENIDEN_SORULACAK = {"karsilik_tanim", "karsilik_uzun", "mastar_degil", "anlam_yok",
                     "turkce_tamlama", "karsilik_ingilizce", "cumlesiz_anlam",
                     "turkce_yazim"}


_PARANTEZ = re.compile(r"\s*[\(\[][^\)\]]*[\)\]]")


def parantezsiz(karsilik):
    """
    "oynamak (spor, oyun)" -> "oynamak". Prompt parantezi yasaklıyor ama
    model yine yazıyor: 5. ölçümde play (fiil) temel anlamı parantez yüzünden
    "mastar değil" diye silindi, setter "Ayarlayıcı (bir şeyi ayarlayan
    kişi)" ise geçti. Parantez içi açıklamadır, karşılık değil.
    """
    metin = _PARANTEZ.sub("", karsilik or "")
    metin = re.sub(r"\s+,", ",", re.sub(r"\s{2,}", " ", metin)).strip(" ,;")
    # Cümle başı büyük harf: "Ayarlayıcı" -> "ayarlayıcı" (Türkçe I/İ).
    parcalar = []
    for p in _parcalar(metin):
        ilk = {"I": "ı", "İ": "i"}.get(p[0], p[0].lower())
        # Başka büyük harf varsa özel ad olabilir ("İngiliz Seti", "AB"): dokunma.
        ozel = any(h.isupper() for h in p[1:])
        parcalar.append(p if ozel else ilk + p[1:])
    return ", ".join(parcalar)


# Hassas (müstehcen) anlamlar YAZILMAZ: site akademik İngilizce için (Efe,
# 24 Eylül; 10. ölçümde vibrator 2. anlam "cinsel oyuncak" geldi). Kelimenin
# kendisi değil yalnızca o ANLAM atılır. "sexual harassment = cinsel taciz"
# gibi akademik kullanımlar kalsın diye tek başına "cinsel" / "sexual" aranmaz.
_HASSAS_TR = re.compile(
    r"cinsel (oyuncak|organ|ilişki|birleşme|haz|uyarı|iste[kğ]|arzu|çekici)|seks|erotik|porno|"
    r"mastürbasyon|prezervatif|kondom|genital|müstehcen|edepsiz söz|küfür|striptiz|"
    r"azgın|şehvet", re.IGNORECASE)
_HASSAS_EN = re.compile(
    r"sex toy|sexual (intercourse|act|pleasure|organ|stimulation|desire|arousal)|\bsex\b|"
    r"erotic|pornograph|masturbat|genital|obscene|vulgar|sexually aroused|\bstrip ?tease|"
    r"removes (her |his |their )?cloth", re.IGNORECASE)


def hassas_mi(anlam):
    return bool(_HASSAS_TR.search(anlam.meaning_tr or "")
                or _HASSAS_EN.search(anlam.definition or ""))


def tanimsiz(karsilik):
    """
    Virgüllü karşılıkta "ve / veya / ya da / gibi" içeren (tanım gibi) parçayı
    atar; başka temiz parça yoksa DOKUNMAZ (karsilik_tanim denetimi yeniden
    sordurur). 10. ölçüm: eliminator "yok edici, eleyici, ortadan kaldıran
    şey veya kimse" ikinci denemede de geldi ve geçti.
    """
    parcalar = _parcalar(karsilik)
    temiz = [p for p in parcalar
             if not any(i in f" {p.lower()} " for i in checks.TANIM_ISARETLERI)]
    return ", ".join(temiz) if temiz and len(temiz) < len(parcalar) else karsilik


def _parcalar(karsilik):
    return [p.strip() for p in re.split(r"[,;]", karsilik or "") if p.strip()]


def _tekrarsiz(karsilik):
    """ "üretmek, üretmek" -> "üretmek" (aynı karşılık içinde tekrar). """
    gorulen, sonuc = set(), []
    for parca in _parcalar(karsilik):
        if parca.lower() not in gorulen:
            gorulen.add(parca.lower())
            sonuc.append(parca)
    return ", ".join(sonuc)


def katilim_mi(metin, tur, supheli=False):
    """
    -ed/-en sıfatı mı (ya da 1. aşamada şüpheli katılım işaretlenmiş mi)?
    Bunların Türkçe karşılığı "-mış" ile başlıyorsa anlam sadece fiilin
    anlamıdır (kirletilmiş, basitleştirilmiş, evlat edinilmiş).
    """
    # Sözlükte fiil çekimi olarak da geçmeli: unannounced ve unwritten
    # "-mış" ile çevrilse de bağımsız sıfatlar (unannounce diye fiil yok).
    if metin.lower() in KALICI_SIFATLAR:
        return False
    return supheli or (tur == "adjective" and metin.endswith(("ed", "en"))
                       and inflect.tur_sozlukte(metin, "verb") is True)


# Biçimce -ed/-en ama öğrenciye SIFAT olarak öğretilen kelimeler (25 Eylül:
# confused, satisfied, terrified, relieved "fiilin çekimi" diye elenmişti).
# Duygu ve durum sıfatları; sınavlarda "I feel confused" biçiminde çıkar.
KALICI_SIFATLAR = set("""
abandoned advanced alarmed amazed amused annoyed armed ashamed astonished balanced
beloved bent bewildered blessed bored broken civilized closed complicated concerned
confused contented convinced cracked crowded cursed dedicated delighted depressed deserted
detailed determined devoted disappointed disgusted disgraced distinguished distracted
distressed divorced drunken educated embarrassed employed enchanted engaged enraged
exhausted experienced fallen fascinated fixed forbidden frightened frozen frustrated
gifted grown haunted heated hidden horrified hurried inclined infuriated injured
inspired interested irritated isolated learned limited married mistaken mixed
motivated moved muted naked offended organized outraged overwhelmed panicked
pleased preoccupied puzzled qualified relaxed relieved renowned reserved retired
satisfied scared scattered secluded settled shaken shocked skilled sophisticated
spoiled startled stressed stunned surprised suspended swollen talented tangled terrified
thrilled tired torn troubled twisted unemployed unexpected unfinished unknown
unrelated upset used wasted wicked wounded worried wrecked
""".split())


def denetle(cevap, metin, tur, cekim=None, supheli_katilim=False):
    """
    Modelin KelimeCevabi'nı yerinde onarır. Döner: checks.Rapor
    (rapor.kabul False ise kelime yazılmaz).
    """
    rapor = checks.Rapor()
    _tipografi(cevap)

    if not cevap.found:
        sebep = (cevap.skip_reason or "sebep yok").strip()
        kod = "fiil_cekimi" if "çekim" in sebep.lower() or "cekim" in sebep.lower() else \
              "bulunamadi"
        rapor.ekle("hata", kod, f"Model kelimeyi reddetti: {sebep}")
        return rapor

    if checks._normalize(cevap.word) != checks._normalize(metin) or cevap.type != tur:
        rapor.ekle("uyari", "farkli_kelime",
                   f"İstenen {metin} ({tur}), dönen {cevap.word} ({cevap.type}); istenen yazıldı.")
    cevap.word, cevap.type = metin, tur

    cekim = cekim or inflect.cekimler(metin, tur)["cekim"]
    bicimler = checks._bicimler(metin, tur, cekim.get("v2Form") or None,
                                cekim.get("v3Form") or None)

    if len(cevap.meanings) > EN_COK_ANLAM:
        rapor.ekle("uyari", "fazla_anlam",
                   f"{len(cevap.meanings)} anlam döndü; ilk {EN_COK_ANLAM} alındı.")
        cevap.meanings = cevap.meanings[:EN_COK_ANLAM]

    # 25 Eylül: "symptoms = belirtiler", "implications = sonuçlar" ayrı kelime
    # olarak yazıldı. Çoğul isim, bütün karşılıkları -ler/-lar ise tekilin
    # çoğuludur (stairs = merdiven, glasses = gözlük kalır).
    if tur == "noun" and metin.endswith("s") and cevap.meanings and all(
            _parcalar(parantezsiz(m.meaning_tr)) and all(
                p.lower().endswith(("ler", "lar", "leri", "ları")) for p in _parcalar(parantezsiz(m.meaning_tr)))
            for m in cevap.meanings):
        rapor.ekle("hata", "cogul_cekimi",
                   f"'{metin}' tekilin çoğulu (bütün karşılıklar -ler/-lar); ayrı kelime değil.")
        return rapor

    katilim = katilim_mi(metin, tur, supheli_katilim)
    saglam, gorulen = [], set()
    for sira, anlam in enumerate(cevap.meanings, 1):
        etiket = f"anlam {sira}"
        temiz = parantezsiz(anlam.meaning_tr)
        if temiz != anlam.meaning_tr:
            rapor.ekle("uyari", "parantez_atildi",
                       f"{etiket}: '{anlam.meaning_tr}' -> '{temiz}'")
            anlam.meaning_tr = temiz
        anlam.meaning_tr = _tekrarsiz(anlam.meaning_tr)
        if hassas_mi(anlam):
            rapor.ekle("uyari", "hassas_anlam",
                       f"{etiket}: '{anlam.meaning_tr}' hassas (müstehcen) anlam; yazılmadı.")
            continue
        temiz = tanimsiz(anlam.meaning_tr)
        if temiz != anlam.meaning_tr:
            rapor.ekle("uyari", "tanim_parcasi_atildi",
                       f"{etiket}: '{anlam.meaning_tr}' -> '{temiz}'")
            anlam.meaning_tr = temiz
        parcalar = _parcalar(anlam.meaning_tr)

        # Türkçede olmayan kelime ("kirlık", "teşeksiz"): o karşılık ATILIR.
        # Başka sağlam karşılık kalmadıysa anlam da gider. Kod
        # "turkce_yazim" ikinci denemeyi tetikliyor.
        yanlislar = turkce.bilinmeyenler(anlam.meaning_tr)
        if yanlislar:
            parcalar = [p for p in parcalar if not turkce.bilinmeyenler(p)]
            rapor.ekle("uyari", "turkce_yazim",
                       f"{etiket}: Türkçede olmayan kelime ({', '.join(yanlislar)}) → "
                       f"'{anlam.meaning_tr}'; o karşılık atıldı.")
            if not parcalar:
                continue
            anlam.meaning_tr = ", ".join(parcalar)

        # 2. denemede "sebze, meyve gibi gıdalar" produce FİİLİNE anlam
        # olarak yazıldı; eski denetim bunu yalnızca uyarıyordu. Fiil
        # anlamında hiç mastar yoksa anlam başka bir türe ait: ATILIR.
        if tur in ("verb", "phrasal_verb") and parcalar and not any(
                p.lower().endswith(("mak", "mek")) for p in parcalar):
            rapor.ekle("uyari", "mastar_degil",
                       f"{etiket}: fiil anlamında mastar yok → '{anlam.meaning_tr}'; atıldı.")
            continue

        # Katılım sıfatının ana karşılığı "-mış" ise anlam fiilin kendisi:
        # polluted = kirletilmiş. Model found=false demeyi beceremedi
        # (2. denemede 12 şüpheli katılımın 0'ını reddetti); karar kodda.
        if katilim and parcalar and _MIS.search(parcalar[0].lower()):
            rapor.ekle("uyari", "fiil_anlami",
                       f"{etiket}: '{anlam.meaning_tr}' fiilin kendi anlamı "
                       f"(-mış); ayrı bir sıfat değil, atıldı.")
            continue

        if not checks._anlami_denetle(anlam, etiket, bicimler, KATEGORILER, rapor, tur, metin):
            continue
        anahtar = checks._normalize(anlam.meaning_tr)
        if anahtar in gorulen:
            rapor.ekle("uyari", "yinelenen_anlam", f"{etiket}: '{anlam.meaning_tr}' tekrar etti.")
            continue
        yakin = checks._yakin_anlam(anahtar, gorulen)
        if yakin:
            rapor.ekle("uyari", "yakin_anlam",
                       f"{etiket}: '{anlam.meaning_tr}' önceki anlamla örtüşüyor ('{yakin}'); atlandı.")
            continue
        ortak = checks._paylasilan_esdizim(anlam, saglam)
        if ortak:
            rapor.ekle("uyari", "ayni_baglam",
                       f"{etiket}: '{anlam.meaning_tr}' önceki anlamla aynı eş dizimi "
                       f"paylaşıyor ('{ortak}'); atlandı.")
            continue

        # Bağlar: boş, kendine, tekrar edenler atılır; Amerikan yazımı.
        baglar, gorulen_bag = [], set()
        for bag in anlam.relations:
            hedef = inflect.amerikan(bag.to_word.strip().lower())
            if not hedef or hedef == metin or (hedef, bag.type) in gorulen_bag:
                continue
            gorulen_bag.add((hedef, bag.type))
            bag.to_word = hedef
            baglar.append(bag)
        anlam.relations = baglar

        gorulen.add(anahtar)
        saglam.append(anlam)

    cevap.meanings = saglam
    if not saglam:
        if any(s.kod == "fiil_anlami" for s in rapor.sorunlar):
            rapor.ekle("hata", "fiil_cekimi",
                       "Bütün anlamlar fiilin kendi anlamı; kelime fiilin çekimi.")
        else:
            rapor.ekle("hata", "anlam_yok", "Hiç geçerli anlam kalmadı.")
    return rapor


def yeniden_sorulmali(rapor):
    """Türkçe ya da anlam sorunu olan cevap uyarıyla bir kez daha sorulur."""
    return [s for s in rapor.sorunlar if s.kod in YENIDEN_SORULACAK]


def puan(rapor, cevap):
    """İki cevaptan iyisini seçmek için: önce kabul, sonra az sorun, çok anlam."""
    return (rapor.kabul, -len(yeniden_sorulmali(rapor)), len(cevap.meanings))


# ----------------------------------------------------------------------
# Eş dizim ve kalıp türü (kodla)
# ----------------------------------------------------------------------

_BAGLAYICI = {"a", "an", "the", "to", "of", "one's", "sb", "sth", "someone",
              "something", "somebody", "be", "is", "are", "was", "were"}


def esdizim_turu(desen, kelime, tur, bicimler=()):
    """
    Eş dizimin dilbilgisel şekli: make a DECISION -> verb_noun,
    HEAVILY dependent -> adv_adj. Öbür kelimenin türüne lemminflect
    sözlüğünden bakılıyor; karar verilemezse "other".
    """
    kendisi = {kelime, *bicimler}
    digerleri = [t for t in re.findall(r"[a-z][a-z'\-]*", desen.lower())
                 if t not in kendisi and t not in _BAGLAYICI]
    li = inflect._li()
    if not digerleri or li is None:
        return "other"
    try:
        turler = set(li.getAllLemmas(digerleri[0]).keys())
    except Exception:
        return "other"
    if tur == "noun":
        if "ADJ" in turler and "VERB" not in turler:
            return "adj_noun"
        if "VERB" in turler:
            return "verb_noun"
        if "NOUN" in turler:
            return "noun_noun"
        if "ADJ" in turler:
            return "adj_noun"
    elif tur == "adjective":
        if "ADV" in turler:
            return "adv_adj"
        if "NOUN" in turler:
            return "adj_noun"
    elif tur in ("verb", "phrasal_verb"):
        if "ADV" in turler:
            return "adv_verb"
        if "NOUN" in turler:
            return "verb_noun"
    elif tur == "adverb":
        if "ADJ" in turler:
            return "adv_adj"
        if "VERB" in turler:
            return "adv_verb"
    return "other"


_EDATLAR = r"on|in|at|to|for|with|from|of|about|into|against|by|between|over|upon|" \
           r"towards?|among|through|within|without|under|onto|across|behind|beyond"


def kalip_turu(desen):
    """Kalıbın türü: suggest DOING sth -> verb_form, depend ON sth -> preposition."""
    p = desen.lower()
    if re.search(r"\bto do\b|\bdoing\b|\bto \+ ?verb\b|\bverb-ing\b|\bto infinitive\b", p):
        return "verb_form"
    if re.search(r"\b(that|whether|if|what|how|why|who|which|where|when)\b", p):
        return "clause"
    if re.search(rf"\b({_EDATLAR})\b", p):
        return "preposition"
    return "structure"


# ----------------------------------------------------------------------
# Yazma
# ----------------------------------------------------------------------

def _en_kolay(seviyeler):
    sirali = [s for s in CEFR_SIRASI if s in seviyeler]
    return sirali[0] if sirali else "Belirtilmemiş"


_BICIM_TURU = {"v2Form": "past", "v3Form": "past_participle",
               "ingForm": "present_participle", "comparative": "comparative",
               "superlative": "superlative"}


def _bicimleri_yaz(kayit, cekim, diger_yazimlar):
    """
    WordForm satırları: inflect.rebuild_forms'un kural çıktısının üstüne
    1. aşamada üretilen çekimler (düzensizler, sözlükten gelen çoğullar,
    Amerikan/İngiliz ikinci yazımlar) eklenir. Metinde hangisi geçerse
    geçsin kelimeye dokunulabilsin.
    """
    from words.models import WordForm
    inflect.rebuild_forms(kayit)
    eklenecek = []
    for alan, yuzey in (cekim or {}).items():
        if not yuzey or " " in yuzey and kayit.pos != "phrasal_verb":
            continue    # "more important" metinde tek token değil
        if alan == "sVersion":
            tur = "plural" if kayit.pos == "noun" else "third_person"
        else:
            tur = _BICIM_TURU.get(alan)
        if tur:
            eklenecek.append((yuzey, tur))
    eklenecek += [(y, "other") for y in diger_yazimlar or []]
    for yuzey, tur in eklenecek:
        WordForm.objects.get_or_create(word=kayit, surface=yuzey[:120], defaults={"kind": tur})


@transaction.atomic
def aileyi_yaz(kok, kelimeler, kaynak):
    """
    Bir aileyi tek transaction'da yazar.

    kelimeler: [{"cevap": KelimeCevabi (denetlenmiş), "cekim": {...},
                 "diger_yazimlar": [...]}]
    Döner: sayaç sözlüğü. Var olan kelimenin anlamlarına DOKUNULMAZ (komut
    zaten anlamı olan kelimeyi sormuyor); anlamı olmayan var olan kelimeye
    anlam eklenir.
    """
    from words.models import (Collocation, ExampleSentence, Meaning, UsagePattern,
                              Word, WordFamily)

    sayac = dict(kelime=0, anlam=0, cumle=0, collocation=0, kalip=0, bicim=0, baska_aile=0)
    aile, _ = WordFamily.objects.get_or_create(root=kok)

    for oge in kelimeler:
        cevap = oge["cevap"]
        seviye = _en_kolay({a.cefr for a in cevap.meanings})
        cekim = oge.get("cekim") or {}
        fiil = cevap.type in ("verb", "phrasal_verb")
        kayit, yeni = Word.objects.get_or_create(
            text=cevap.word, pos=cevap.type,
            defaults={"family": aile, "cefr": seviye, "isBaseWord": True,
                      "visibility": "public",
                      "v2Form": (cekim.get("v2Form") or None) if fiil else None,
                      "v3Form": (cekim.get("v3Form") or None) if fiil else None},
        )
        if not yeni and kayit.family_id != aile.pk:
            sayac["baska_aile"] += 1
        if not yeni and kayit.cefr in ("", "Belirtilmemiş"):
            kayit.cefr = seviye
            kayit.save(update_fields=["cefr"])
        sayac["kelime"] += 1

        bicimler = [y for y, _t in inflect.forms_for(kayit.text, kayit.pos,
                                                      kayit.v2Form, kayit.v3Form)]
        sira = kayit.meanings.count()
        for anlam in cevap.meanings:
            m = Meaning.objects.create(
                word=kayit, meaning_tr=anlam.meaning_tr[:300],
                definition=(anlam.definition or "")[:600] or None,
                sentiment=anlam.sentiment,
                register=REGISTER_ESLEME.get(anlam.register, "neutral"),
                cefr=anlam.cefr, sort_order=sira)
            sira += 1
            sayac["anlam"] += 1
            # Kategoriler (konular) 11 Ekim'den beri yalnızca elle işaretlenir (rapor 18.39);
            # modelin yazdığı kategori yazılmaz.
            ExampleSentence.objects.bulk_create([
                ExampleSentence(meaning=m, text=c[:400], source=kaynak[:120], sort_order=i)
                for i, c in enumerate(anlam.sentences)])
            sayac["cumle"] += len(anlam.sentences)
            for i, e in enumerate(anlam.collocations):
                _, olustu = Collocation.objects.get_or_create(
                    meaning=m, pattern=e.pattern[:200],
                    defaults={"kind": esdizim_turu(e.pattern, kayit.text, kayit.pos, bicimler),
                              "meaning_tr": (getattr(e, "meaning_tr", "") or "")[:200] or None,
                              "example": (getattr(e, "example", "") or "")[:400] or None,
                              "sort_order": i})
                sayac["collocation"] += int(olustu)
            for i, k in enumerate(anlam.patterns):
                _, olustu = UsagePattern.objects.get_or_create(
                    meaning=m, pattern=k.pattern[:200],
                    defaults={"kind": kalip_turu(k.pattern),
                              "example": (k.example or "")[:400] or None,
                              "note": (k.note or "")[:300] or None,
                              "sort_order": i})
                sayac["kalip"] += int(olustu)

        _bicimleri_yaz(kayit, cekim, oge.get("diger_yazimlar"))
        sayac["bicim"] += kayit.forms.count()
    return sayac


def _anlam_anahtari(metin):
    """Karşılaştırma anahtarı: büyük/küçük harf ve Türkçe İ'nin artık noktası
    (d_2026_09_25.uygula_3 bunları temizledi) eşleşmeyi bozmasın."""
    metin = unicodedata.normalize("NFD", metin or "").casefold().replace("\u0307", "")
    return " ".join(metin.split())


def anlam_eslemesi(db_anlamlari, cevap_anlamlari):
    """
    Depodaki cevabın anlamlarını veritabanındaki Meaning satırlarına eşler.

    aileyi_yaz her cevap anlamı için meaning_tr[:300] ile bir Meaning açıyor;
    sonradan elle düzeltmeler (d_2026_09_25) bazı karşılıkları değiştirdi,
    bazı anlamları sildi ya da yeni anlam ekledi. Bu yüzden sıra numarasına
    değil METNE bakılıyor, üç geçişte: birebir meaning_tr, normalleştirilmiş
    meaning_tr, açıklama (definition — karşılık düzeltilince açıklama
    genelde aynı kalıyor). Bir Meaning en çok bir cevap anlamına verilir.

    db_anlamlari: Meaning listesi. cevap_anlamlari: dict ya da Anlam listesi.
    Döner: cevap_anlamlari ile aynı uzunlukta [Meaning | None].
    """
    def alan(a, ad):
        return (a.get(ad) if isinstance(a, dict) else getattr(a, ad, None)) or ""

    sonuc = [None] * len(cevap_anlamlari)
    kalan = list(db_anlamlari)
    gecisler = (
        (lambda a: alan(a, "meaning_tr")[:300], lambda m: m.meaning_tr),
        (lambda a: _anlam_anahtari(alan(a, "meaning_tr")[:300]),
         lambda m: _anlam_anahtari(m.meaning_tr)),
        (lambda a: _anlam_anahtari(alan(a, "definition")[:600]),
         lambda m: _anlam_anahtari(m.definition)),
    )
    for cevap_anahtari, db_anahtari in gecisler:
        for i, a in enumerate(cevap_anlamlari):
            if sonuc[i] is not None:
                continue
            aranan = cevap_anahtari(a)
            if not aranan:
                continue
            for m in kalan:
                if db_anahtari(m) == aranan:
                    sonuc[i] = m
                    kalan.remove(m)
                    break
    return sonuc


def bagla(kaynak, hedef, tur, anlam, not_=None):
    """
    (anlam, hedef, tür) bağını kurar; varsa dokunmaz. Döner: "var" /
    "atandi" (anlamı boş eski satır bu anlama verildi) / "kuruldu".

    Anlamı boş (kelime düzeyi, D1 öncesi) bir satır varsa yeni satır
    açılmaz, o satır bu anlama bağlanır — aynı bağ hem boş hem dolu iki
    satırda durmasın.
    """
    from words.models import WordRelation

    satirlar = WordRelation.objects.filter(from_word=kaynak, to_word=hedef, type=tur)
    if satirlar.filter(meaning=anlam).exists():
        return "var"
    if anlam is not None:
        bos = satirlar.filter(meaning__isnull=True).first()
        if bos is not None:
            bos.meaning = anlam
            bos.save(update_fields=["meaning"])
            return "atandi"
    WordRelation.objects.create(from_word=kaynak, to_word=hedef, type=tur,
                                meaning=anlam, note=not_)
    return "kuruldu"


def bag_tamamla(kayitlar):
    """
    Depodaki bütün anlam cevaplarının bağlarını (relations) kurmayı dener.

    kayitlar: depodaki anlam kayıtları ({"word", "type", "cevap": dict}).
    Bağ, cevaptaki anlamın veritabanındaki karşılığına (Meaning) bağlanır.
    Hedef kelime veritabanında yoksa bağ kurulmaz — uydurma hedef kaydı
    açmak, gerçek kelime gelince çift kayda yol açardı. Cevaptaki anlam
    veritabanında yoksa (elle silinmiş) bağı da kurulmaz: silinen anlamın
    bağları geri gelmesin. Döner: {"kurulan": n, "bekleyen": n, "anlamsiz": n}
    """
    from words.models import Word

    kurulan = bekleyen = anlamsiz = 0
    for kayit in kayitlar:
        cevap = kayit.get("cevap") or {}
        if not cevap.get("found") or kayit.get("durum") != "yazildi":
            continue
        kaynak = Word.objects.filter(text=kayit["word"], pos=kayit["type"]).first()
        if kaynak is None:
            continue
        cevap_anlamlari = cevap.get("meanings", [])
        eslesme = anlam_eslemesi(list(kaynak.meanings.all()), cevap_anlamlari)
        for anlam, meaning in zip(cevap_anlamlari, eslesme):
            for bag in anlam.get("relations", []):
                hedef = (Word.objects.filter(text=bag["to_word"], pos=kaynak.pos).first()
                         or Word.objects.filter(text=bag["to_word"]).first())
                if hedef is None or hedef.pk == kaynak.pk:
                    bekleyen += 1
                    continue
                if meaning is None:
                    anlamsiz += 1
                    continue
                kurulan += int(bagla(kaynak, hedef, bag["type"], meaning) != "var")
    return {"kurulan": kurulan, "bekleyen": bekleyen, "anlamsiz": anlamsiz}
