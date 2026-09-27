"""
3. aşamanın KONTROL katmanı — üretici modelin anlamlarını ikinci bir model denetler.

Kod denetimi (anlam.denetle) biçimi yakalıyor: tanım gibi karşılık,
mastarsız fiil, Türkçede olmayan kelime. ANLAMI yakalayamıyor:
"hopefully = umarak", "underwriter = sigorta yazarı", "simplistic = sade"
biçim olarak kusursuz ama yanlış. 2. doldurma denemesinde 180 anlamın
yaklaşık 10'u (%5) böyleydi. Hedef %1'in altı.

AKIŞ (aile_doldur içinde, kelime başına)
----------------------------------------
    üret -> kod denetimi -> (sorun varsa ikinci deneme) -> KONTROL -> uygula -> yaz

Kontrolcü her anlam için karar veriyor (prompt.kontrol_filling):
    dogru            -> kalır (seviyesi kontrolcününkiyle değiştirilir)
    karsilik_yanlis  -> kontrolcünün doğru karşılığı yazılır — ama o karşılık
                        da kod denetiminden (Türkçe yazım, mastar) geçmeli
    anlam_yanlis     -> anlam silinir
Ayrıca hatalı cümleler ve collocation'lar silinir; "bu kelime bu türde
kullanılmıyor" derse kelime yazılmaz.

Bütün anlamlar silinirse kelime, kontrolcünün gerekçeleriyle bir kez daha
üretilir ve yeniden kontrol edilir. Yine hiçbir şey kalmazsa YAZILMAZ.

ÖLÇÜ: kontrolcünün yanlış bulduğu anlam oranı, üretici modelin hata oranının
tahmini. Bu oran %1'in altına inene kadar prompt ve model iyileştirilecek.

Ayar (.env): LLM_KONTROL_MODEL boşsa bu katman atlanır.
"""

from typing import List, Literal

from django.conf import settings
from pydantic import BaseModel

from LearnVocab import llm
from words.aile import turkce
from words.enrich import prompt

from words.aile.anlam import CEFR_SIRASI, parantezsiz, tanimsiz  # noqa: E402
from words.enrich.checks import TANIM_ISARETLERI  # noqa: E402
from words import inflect  # noqa: E402

CEFR = Literal["A1", "A2", "B1", "B2", "C1", "C2"]


class AnlamKarari(BaseModel):
    index: int
    verdict: Literal["dogru", "karsilik_yanlis", "anlam_yanlis"]
    reason: str
    correct_tr: str
    cefr: CEFR
    bad_sentences: List[int]
    bad_collocations: List[int]


class KontrolCevabi(BaseModel):
    word_valid: bool
    word_reason: str
    # Temel anlam listede yoksa onun Türkçesi. Varsayılan: önbellekteki eski
    # kontrol cevaplarında bu alan yok (24 Eylül'de eklendi).
    missing_meaning: str = ""
    meanings: List[AnlamKarari]


def ayarli_mi():
    return bool(getattr(settings, "LLM_KONTROL_MODEL", ""))


def model_adi():
    return getattr(settings, "LLM_KONTROL_MODEL", "")


def dusunme():
    return getattr(settings, "LLM_KONTROL_REASONING_EFFORT", "") or "low"


def kimlik():
    """Önbellek anahtarı: model + düşünme derinliği. Derinlik değişirse
    eski kontroller yeniden kullanılmaz."""
    return f"{model_adi()}|{dusunme()}"


def sor(kelime, tur, aile, anlamlar):
    """Kontrolcüye tek istek (iş parçacığında çağrılabilir). Hata döndürür."""
    metin = prompt.kontrol_kullanici_metni(kelime, tur, aile, anlamlar)
    ayar = lambda ad, v="": getattr(settings, ad, v)  # noqa: E731
    try:
        return llm.chat_json(
            prompt.KONTROL_SISTEM, metin, KontrolCevabi,
            model=model_adi(), base_url=ayar("LLM_KONTROL_BASE_URL") or None,
            api_key=ayar("LLM_KONTROL_API_KEY") or None,
            reasoning=dusunme(), sicaklik_gonder=False, onbellek=True,
            siralama=getattr(settings, "LLM_KONTROL_PROVIDER_SORT", "price")), None
    except llm.LLMError as hata:
        return None, hata


def maliyet(tuketim):
    girdi = float(getattr(settings, "LLM_KONTROL_PRICE_INPUT", 0) or 0)
    cikti = float(getattr(settings, "LLM_KONTROL_PRICE_OUTPUT", 0) or 0)
    return tuketim.prompt_tokens / 1e6 * girdi + tuketim.completion_tokens / 1e6 * cikti


def _karsilik_gecerli(karsilik, tur):
    """Kontrolcünün önerdiği karşılık da kod denetiminden geçmeli."""
    karsilik = tanimsiz(parantezsiz(karsilik))
    if any(i in f" {karsilik.lower()} " for i in TANIM_ISARETLERI):
        return False
    if not karsilik or len(karsilik.split()) > 8:
        return False
    if turkce.bilinmeyenler(karsilik):
        return False
    if tur in ("verb", "phrasal_verb"):
        parcalar = [p.strip() for p in karsilik.split(",") if p.strip()]
        if not any(p.endswith(("mak", "mek")) for p in parcalar):
            return False
    return True


def uygula(cevap, karar, tur, rapor):
    """
    Kontrolcünün kararını KelimeCevabi'na uygular (yerinde değiştirir).

    Döner: sayaç sözlüğü + "gerekceler" (silinen anlamların nedenleri; hepsi
    silinirse yeniden üretim mesajında kullanılıyor).
    """
    s = dict(kontrol_anlam=len(cevap.meanings), dogru=0, karsilik_duzeltildi=0,
             anlam_silindi=0, cumle_silindi=0, esdizim_silindi=0, cefr_degisti=0,
             karar_yok=0, eksik_anlam=0, gerekceler=[], eksik="", cumlesiz=[],
             sozlukte_var=False)
    # Kontrolcü 5. ölçümde gerçek kullanımları sildi: overthrow (isim,
    # "devrilme"), moral (isim, "kıssadan hisse"). Sözlük bu türü tanıyorsa
    # "kelime bu türde yok" kararı YOK SAYILIR; anlam kararları yine uygulanır.
    s["sozlukte_var"] = inflect.tur_sozlukte(cevap.word, tur) is True
    # 25 Eylül: participants, restrictions, guidelines "sözlük tanıyor" diye
    # yazıldı; kontrolcü haklıydı (tekilin çoğulu). Çoğul isimde ret geçerli.
    if s["sozlukte_var"] and tur == "noun" and _tekilin_cogulu(cevap.word):
        s["sozlukte_var"] = False

    if not karar.word_valid and s["sozlukte_var"]:
        rapor.ekle("uyari", "kontrol_kelime_ret_yok_sayildi",
                   f"Kontrolcü 'bu türde kullanılmıyor' dedi ({karar.word_reason}) ama "
                   f"sözlük tanıyor; anlam kararlarına bakıldı.")
    elif not karar.word_valid:
        rapor.ekle("hata", "kontrol_kelime_ret",
                   f"Kontrolcü: kelime bu türde kullanılmıyor — {karar.word_reason}")
        s["gerekceler"].append(karar.word_reason or "kelime bu türde kullanılmıyor")
        s["anlam_silindi"] = len(cevap.meanings)
        cevap.meanings = []
        return s

    eksik = (karar.missing_meaning or "").strip()
    if eksik:
        s["eksik_anlam"] = 1
        s["eksik"] = eksik
        rapor.ekle("uyari", "kontrol_eksik_anlam", f"Temel anlam eksik: '{eksik}'.")

    kararlar = {k.index: k for k in karar.meanings}
    kalan = []
    for no, anlam in enumerate(cevap.meanings, 1):
        k = kararlar.get(no)
        etiket = f"anlam {no} ('{anlam.meaning_tr}')"
        if k is None:
            s["karar_yok"] += 1
            rapor.ekle("uyari", "kontrol_karar_yok", f"{etiket}: kontrolcü karar vermedi.")
            kalan.append(anlam)
            continue

        if k.verdict == "anlam_yanlis":
            s["anlam_silindi"] += 1
            s["gerekceler"].append(f"'{anlam.meaning_tr}': {k.reason}")
            rapor.ekle("uyari", "kontrol_anlam_yanlis", f"{etiket}: silindi — {k.reason}")
            continue

        if k.verdict == "karsilik_yanlis":
            if _karsilik_gecerli(k.correct_tr, tur):
                rapor.ekle("uyari", "kontrol_karsilik",
                           f"{etiket} -> '{k.correct_tr}' — {k.reason}")
                anlam.meaning_tr = tanimsiz(parantezsiz(k.correct_tr))
                s["karsilik_duzeltildi"] += 1
            else:
                s["anlam_silindi"] += 1
                s["gerekceler"].append(f"'{anlam.meaning_tr}': {k.reason}")
                rapor.ekle("uyari", "kontrol_karsilik_kullanilamadi",
                           f"{etiket}: karşılık yanlış ({k.reason}); önerilen "
                           f"'{k.correct_tr}' denetimden geçmedi, anlam silindi.")
                continue
        else:
            s["dogru"] += 1

        # Seviye konusunda kontrolcü de kesin değil: yalnızca İKİ ve üstü
        # basamak farkta (B1 -> C1 gibi) onun seviyesini kabul et. Tek basamak
        # fark (B1 -> B2) zevk meselesi, üreticinin seviyesi kalır.
        # İSTİSNA: üretici A1-A2 demiş, kontrolcü yukarı çekiyorsa tek basamak
        # da kabul (4. ölçüm: overpay A2, unaware A2 — üretici A'da cömert).
        if (k.cefr in CEFR_SIRASI and anlam.cefr in CEFR_SIRASI
                and (abs(CEFR_SIRASI.index(k.cefr) - CEFR_SIRASI.index(anlam.cefr)) >= 2
                     or (anlam.cefr in ("A1", "A2")
                         and CEFR_SIRASI.index(k.cefr) > CEFR_SIRASI.index(anlam.cefr)))):
            s["cefr_degisti"] += 1
            anlam.cefr = k.cefr

        kotu = {i for i in k.bad_sentences if 1 <= i <= len(anlam.sentences)}
        if kotu:
            yeni = [c for i, c in enumerate(anlam.sentences, 1) if i not in kotu]
            if len(yeni) < 2:
                s["anlam_silindi"] += 1
                s["cumlesiz"].append(anlam.meaning_tr)
                s["gerekceler"].append(f"'{anlam.meaning_tr}': örnek cümlelerin çoğu hatalı")
                rapor.ekle("uyari", "kontrol_cumlesiz",
                           f"{etiket}: cümlelerin çoğu hatalı bulundu, anlam silindi.")
                continue
            s["cumle_silindi"] += len(kotu)
            anlam.sentences = yeni

        kotu = {i for i in k.bad_collocations if 1 <= i <= len(anlam.collocations)}
        if kotu:
            s["esdizim_silindi"] += len(kotu)
            anlam.collocations = [e for i, e in enumerate(anlam.collocations, 1)
                                  if i not in kotu]
        kalan.append(anlam)

    # Kontrolcünün düzeltmesi iki anlamı AYNI karşılığa getirebilir (7. ölçüm:
    # washboard "çamaşır tahtası" iki kez). Kod denetimi bundan ÖNCE çalıştığı
    # için yakalayamıyordu; burada ikincisi atılır.
    gorulen, tekil = set(), []
    for anlam in kalan:
        anahtar = " ".join(anlam.meaning_tr.lower().split())
        if anahtar in gorulen:
            rapor.ekle("uyari", "kontrol_sonrasi_tekrar",
                       f"'{anlam.meaning_tr}' düzeltmeden sonra önceki anlamla aynı; atıldı.")
            continue
        gorulen.add(anahtar)
        tekil.append(anlam)
    kalan = tekil

    cevap.meanings = kalan
    if not kalan and s["sozlukte_var"]:
        # Yazılmıyor (yanlış öğretmektense eksik olsun) ama ayrı sayılıyor:
        # bu listedekiler kontrolcünün muhtemel HATALI silmeleri.
        rapor.ekle("hata", "kontrol_ret_tartismali",
                   "Kontrolden sonra hiç anlam kalmadı; sözlük bu türü tanıyor (tartışmalı).")
    elif not kalan:
        rapor.ekle("hata", "kontrol_ret", "Kontrolden sonra hiç anlam kalmadı.")
    return s


def eksik_anlam_notu(eksik="", cumlesiz=()):
    """
    Temel anlam eksikse ya da bir anlam yalnızca örnek cümleleri kötü diye
    silindiyse üreticiye giden uyarı. (5. ölçüm: play (isim) "oyun" anlamı
    cümleleri yüzünden silindi, geriye "tiyatro eseri" kaldı.)
    """
    satirlar = ["", "", "DİKKAT: Bu kelime için önceki cevabın bir kontrolcü tarafından "
                "incelendi ve şu sorunlar bulundu:"]
    if eksik:
        satirlar.append(f"- Kelimenin EN TEMEL anlamı EKSİKTİ: \"{eksik}\". Bu anlam MUTLAKA "
                        f"listede ve 1. sırada olsun.")
    for anlam in cumlesiz:
        satirlar.append(f"- \"{anlam}\" anlamının örnek cümleleri HATALIYDI (kelimeyi bu "
                        f"anlamda kullanmıyordu). Bu anlamı KORU, cümlelerini kelimeyi TAM "
                        f"BU anlamda kullanarak yeniden yaz.")
    satirlar.append("Bütün anlamları BAŞTAN ver. Doğru olan diğer anlamları da unutma. "
                    "Karşılıklarda parantez KULLANMA.")
    return "\n".join(satirlar)


def yeniden_uretim_notu(gerekceler):
    """Bütün anlamlar silindiğinde üreticiye giden uyarı."""
    return ("\n\nDİKKAT: Bu kelime için önceki cevabın bir kontrolcü tarafından YANLIŞ "
            "bulundu. Gerekçeler:\n" + "\n".join(f"- {g}" for g in gerekceler)
            + "\nBu hataları yapmadan cevabı BAŞTAN ver. Kelime bu türde gerçekten "
              "kullanılmıyorsa found alanını false yap.")


def _tekilin_cogulu(kelime):
    """participants -> participant, cities -> city: tekili ayrı bir isimse True."""
    k = (kelime or "").lower()
    if k in KENDI_BASINA_COGUL or not k.endswith("s") or k.endswith("ss"):
        return False
    adaylar = [k[:-1]]
    if k.endswith("es"):
        adaylar.append(k[:-2])
    if k.endswith("ies"):
        adaylar.append(k[:-3] + "y")
    return any(a and inflect.tur_sozlukte(a, "noun") is True for a in adaylar)


# Çoğul biçimli ama kendi başına kelime olan isimler (tekili başka anlam).
KENDI_BASINA_COGUL = set("""
acoustics aesthetics analytics arms athletics basics belongings ceramics clothes
customs dynamics earnings economics electronics ethics genetics glasses goods graphics
gymnastics headquarters humanities jeans linguistics logistics manners mathematics
means mechanics news odds optics outskirts phonetics physics politics premises
proceeds remains robotics savings scissors semantics series shorts species stairs
statistics surroundings thanks tropics trousers whereabouts
""".split())
