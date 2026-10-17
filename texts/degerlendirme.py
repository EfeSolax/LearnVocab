"""
Serbest yazmanın değerlendirilmesi (ürün raporu 9.1).

Eski sistem (10 kriter, 100 puan, akademik rubrik, uzun düz metin cevap)
tamamen bırakıldı. Yeni sistemde model YALNIZCA JSON döndürür:

    {
      "puan": 3.5,
      "iyi": [{"alinti": "...", "aciklama": "..."}],
      "hatalar": [{"alinti": "...", "dogrusu": "...", "neden": "..."}],
      "kullanilan_kelimeler": ["aim", "decide"]
    }

Listeleri arayüz çizer. Modelin çıktısına körü körüne güvenilmez
(`cevabi_coz`): JSON dışı metin ayıklanır, eksik/boş maddeler ve metinde
geçmeyen alıntılar atılır, puan [1, 5] aralığına ve yarım adıma yuvarlanır,
hata sayısı sertliğin (ve türün: günlük / akademik) sınırına kırpılır.

İstemci, tekrar deneme ve yedek model mantığı `LearnVocab/gemini.py`'de.
"""

import json
import logging
import math
import re

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from pydantic import BaseModel

from LearnVocab import gemini
from texts import limits, sinyaller
from texts.konular import konu_yonergesi
from texts.models import Sertlik, YaziDurumu, YaziTuru

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sertlik
# ---------------------------------------------------------------------------

# Sertlik yalnızca hata listesini etkiler; puan bantları her sertlikte aynı
# (rapor 9.1, varsayım). Titiz için raporda sınır yok; ekran boğulmasın diye 10.
EN_COK_HATA = {
    Sertlik.NAZIK: 3,
    Sertlik.NORMAL: 6,
    Sertlik.TITIZ: 10,
}

# Akademik türde hem dilbilgisi hem Forefront kriterleri denetlendiği için sınır daha geniş.
EN_COK_HATA_AKADEMIK = {
    Sertlik.NAZIK: 4,
    Sertlik.NORMAL: 8,
    Sertlik.TITIZ: 12,
}

EN_COK_IYI = 4

# Akademik metin daha uzun ve hata listesi daha kalabalık: tek çağrıya 60 sn.
AKADEMIK_ZAMAN_ASIMI = 60

_SERTLIK_KURALI = {
    Sertlik.NAZIK: (
        "SERTLİK: NAZİK. Yalnızca ANLAMI BOZAN hataları yaz: okuyanın cümleyi "
        "yanlış anlamasına ya da hiç anlamamasına yol açan hatalar. Anlam yerindeyse "
        "küçük dilbilgisi kusurlarını, noktalama ve büyük harfi YAZMA. En çok 3 hata."
    ),
    Sertlik.NORMAL: (
        "SERTLİK: NORMAL. Dilbilgisi hatalarını (zaman, özne-fiil uyumu, edat, "
        "tekil/çoğul, artikel, kelime sırası) ve yanlış kelime seçimini yaz. "
        "Noktalama, büyük harf ve resmiyet (formal/informal) hata SAYILMAZ. En çok 6 hata."
    ),
    Sertlik.TITIZ: (
        "SERTLİK: TİTİZ. Dilbilgisi ve kelime hatalarına ek olarak noktalama, büyük "
        "harf ve bağlama uymayan resmiyet (ör. resmî bir metinde argo) hatalarını da "
        "yaz. En çok 10 hata; en önemlilerden başla."
    ),
}


_SERTLIK_KURALI_AKADEMIK = {
    Sertlik.NAZIK: (
        "SERTLİK: NAZİK. Anlamı bozan dilbilgisi hatalarını ve en belirgin akademik sorunları "
        "(mantık hatası, kanıt yerine kişisel anekdot, okuyucuya hitap, kısaltma) yaz. En çok 4 hata."
    ),
    Sertlik.NORMAL: (
        "SERTLİK: NORMAL. Dilbilgisi ve kelime hatalarını ve aşağıdaki akademik kuralların hepsini yaz. "
        "Noktalama ve büyük harf hata SAYILMAZ. En çok 8 hata."
    ),
    Sertlik.TITIZ: (
        "SERTLİK: TİTİZ. Dilbilgisi, kelime, noktalama ve büyük harf hatalarını ve aşağıdaki akademik "
        "kuralların hepsini yaz. En çok 12 hata; en önemlilerden başla."
    ),
}


def sertlik_gecerli(deger):
    return deger if deger in EN_COK_HATA else Sertlik.NORMAL


def tur_gecerli(deger):
    return deger if deger in YaziTuru.values else YaziTuru.GUNLUK


def hata_siniri(sertlik, tur=YaziTuru.GUNLUK):
    tablo = EN_COK_HATA_AKADEMIK if tur == YaziTuru.AKADEMIK else EN_COK_HATA
    return tablo[sertlik_gecerli(sertlik)]


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

class _Iyi(BaseModel):
    alinti: str
    aciklama: str


class _Hata(BaseModel):
    alinti: str
    dogrusu: str
    neden: str


class DegerlendirmeSemasi(BaseModel):
    """Gemini'ye verilen JSON şeması (çıktıyı şemaya uymaya zorlar)."""
    puan: float
    iyi: list[_Iyi]
    hatalar: list[_Hata]
    kullanilan_kelimeler: list[str]


GERI_BILDIRIM_DILLERI = {"tr": "TÜRKÇE", "en": "İNGİLİZCE (English)", "de": "ALMANCA (Deutsch)"}


def geri_bildirim_dili(user):
    """Yazarın arayüz dili (Ayarlar'daki dil seçimi); yoksa Türkçe."""
    from usersettings.models import UserSettings
    kod = UserSettings.objects.filter(user=user).values_list("arayuz_dili", flat=True).first() or "tr"
    return kod if kod in GERI_BILDIRIM_DILLERI else "tr"


_GIRIS_GUNLUK = """Sen İngilizce öğrenen Türk öğrencilere yardım eden, sıcak ve dürüst bir yazma öğretmenisin.
Öğrenci 3–8 cümlelik kısa bir İngilizce metin yazdı. Akademik yazı BEKLENMİYOR:
konu cümlesi, paragraf yapısı, özet, resmî dil ya da uzunluk puanlanmaz.
Amaç öğrencinin kelimeleri doğru kullanmayı öğrenmesi ve cesaretinin kırılmaması."""

# Akademik tür (Efe, 17 Ekim): Forefront, "Features of Academic Writing" (s. 14–35). Kısa alıştırmada
# denetlenebilenler: cümle düzeyinde alıntılanabilen sorunlar. İntihal, atıf, kaynakça ve başlık
# denetlenmez (öğrenciden kaynak istenmiyor). Taslak ve gerekçe: ozetler/akademik-yazma-prompt-taslagi.md
_GIRIS_AKADEMIK = """Sen İngilizce öğrenen Türk üniversite öğrencilerine akademik yazmayı öğreten, sıcak ama titiz bir öğretmensin.
Öğrenci kısa bir AKADEMİK İngilizce metin yazdı (1–3 paragraf). Kaynak okuması ya da kaynakça eklemesi
BEKLENMİYOR; atıf biçimi, başlıklar ve intihal DENETLENMEZ. Metni hem dilbilgisi hem de aşağıdaki
akademik yazım kurallarına göre değerlendir."""

_AKADEMIK_KURALLAR = """AKADEMİK HATALAR (her biri "hatalar" listesinde ayrı madde; "dogrusu" akademik karşılık):
A. Resmî dil
  A1. Kısaltmalar: don't, can't, it's, they're, haven't → do not, cannot, it is, they are, have not.
  A2. Gündelik kelime ve ifadeler, YALNIZCA açıkça konuşma diliyse: kids, stuff, lots of, a lot of, kind of,
      gonna/wanna, like (= such as), etc., by the way, on top of that, after all (geçiş olarak) → children,
      materials, many/numerous, partly, going to/want to, such as, and so on, furthermore/in addition.
      Tek kelimelik akademik karşılığı olan phrasal verb'ler: look at → examine, look into → investigate,
      find out → discover/conclude, go up → increase/rise, build up → accumulate, get rid of → eliminate.
      get / good / big / thing / happen gibi kelimeleri yalnızca belirsizlik ya da açık gündelik ton yaratıyorsa yaz.
  A3. Okuyucuya hitap: you/your, retorik soru, ünlem, emoji, yarım bırakılan cümle (...) →
      edilgen çatı ("It can be observed that"), üçüncü şahıs ("students ... they") ya da "one".
  A4. Dayanaksız kişisel görüş: "I think", "I feel", "In my opinion" → "It can be argued that", "This suggests that".
      DİKKAT: "I argue that", "I will first discuss", "I agree with X's view that" HATA DEĞİLDİR.
  A5. Cinsiyetçi dil: mankind, freshman, "every student ... he/she" → humanity, first-year students, "students ... they".
  A6. Gereksiz uzatma: due to the fact that → because; inside of → inside; in spite of the fact that → although.
  A7. Belirsiz ifade: "around 1000", "many people", "some reasons", "things" → daha kesin bir ifade
      ("approximately 1,000", "a majority of the participants", nedenleri adlarıyla).
B. İhtiyatlı dil (hedging)
  B1. Kanıtsız mutlak ya da buyurgan ifade: always, never, all/everyone, definitely, certainly, obviously,
      impossible, will (kesin tahmin), must/should (buyurgan) → often, rarely, many/most, likely to, may, can,
      tend to, suggest. Kanıtlanmış genel gerçeklere ve zaten ihtiyatlı ifadelere DOKUNMA.
C. Nesnellik ve mantık
  C1. Kişisel anekdotu kanıt olarak sunma (my neighbour, my friend, in my family) → genel ve kişisiz ifade.
  C2. Duygusal dil (the saddest thing, it makes me sad, terrible) → nötr ifade.
  C3. Mantık hataları: aceleci genelleme, aşırı basitleştirme, kaygan zemin, sahte ikilem, konuyu saptırma,
      çoğunluğa başvurma, duygu sömürüsü, varsayımı olgu gibi sunma. "neden"de hatanın adını söyle ve tek
      cümleyle açıkla; "dogrusu" dengeli bir yeniden yazım olsun.
  C4. Konudan sapma geçişleri ("By the way, turning to the previous issue") → paragrafı tek fikre bağlayan bir geçiş.
ALINTI: Her zaman metinden HARFİ HARFİNE, 2–10 kelimelik kesintisiz bir parça seç; tek kelime alıntılama
("you" değil "you can see"). Aynı sorun birkaç yerde varsa her yer ayrı madde; sınır dolacaksa en önemlilerini
seç. "dogrusu" ASLA boş ya da alıntıyla aynı olmasın.
ÖNCELİK: anlamı bozan dilbilgisi > mantık ve nesnellik (C) > ihtiyatlı dil (B) > resmî dil (A).
"iyi" maddelerinde akademik güçlü yanları da öv (ihtiyatlı dil, resmî kelime, edilgen çatı, açık konu cümlesi, bağlaçlar)."""

_PUAN_GUNLUK = """   1 = yalnızca çok çok kötü (neredeyse hiç anlaşılmıyor)
   2 = çok kötü
   3 = kötü
   3.5 = ortalama
   4 = azıcık iyi
   4.5–5 = çok iyi
   Pratikte puanlar 2–5 arasındadır. Puanı sertlikten bağımsız ver: aynı metin her sertlikte aynı puanı alır."""

_PUAN_AKADEMIK = """   Puan AKADEMİK yazı ölçütüne göredir; üslup, ihtiyatlı dil ve mantık sorunları puanı düşürür:
   5 = dilbilgisi sağlam; resmî ve ihtiyatlı; kişisel ya da duygusal dil yok
   4–4.5 = birkaç üslup kusuru
   3.5 = belirgin gündelik dil ya da kanıtsız genellemeler
   3 = metnin çoğu sohbet dilinde ya da mantık hataları var
   2 = akademik metin özelliği neredeyse yok ya da dilbilgisi anlamı bozuyor
   Puanı sertlikten bağımsız ver: aynı metin her sertlikte aynı puanı alır."""


def prompt_olustur(metin, sertlik=Sertlik.NORMAL, kelimeler=(), konu="", dil="tr", tur=YaziTuru.GUNLUK):
    """Değerlendirme prompt'u. Açıklamalar `dil`de (varsayılan Türkçe), çıktı yalnızca JSON.
    Akademik türde giriş, hata kuralları, sertlik ve puan bantları akademik sürümleriyle değişir."""
    dil_adi = GERI_BILDIRIM_DILLERI.get(dil, GERI_BILDIRIM_DILLERI["tr"])
    sertlik = sertlik_gecerli(sertlik)
    akademik = tur_gecerli(tur) == YaziTuru.AKADEMIK
    kelime_satiri = ", ".join(k for k in kelimeler if k) or "(yok)"
    yonerge = konu_yonergesi(konu) if konu else ""
    konu_satiri = f"{konu} — {yonerge}" if yonerge else (konu or "serbest")
    if akademik:
        gercek_hata = ("   - Dilbilgisi hataları ve aşağıdaki AKADEMİK HATALAR yazılır. Bunların dışındaki üslup\n"
                       "     tercihleri ve \"daha güzel söylenebilirdi\" önerileri HATA DEĞİLDİR; yazma.")
        sertlik_kurali = _SERTLIK_KURALI_AKADEMIK[sertlik]
    else:
        gercek_hata = ("   - YALNIZCA GERÇEK HATALAR: dilbilgisi, yanlış kelime, anlamı bozan kullanım.\n"
                       "     Üslup tercihi, \"daha güzel söylenebilirdi\" önerileri ve yeniden yazımlar HATA DEĞİLDİR; yazma.")
        sertlik_kurali = _SERTLIK_KURALI[sertlik]

    return f"""{_GIRIS_AKADEMIK if akademik else _GIRIS_GUNLUK}

GÖREVİN: Metni oku ve YALNIZCA aşağıdaki biçimde bir JSON döndür. JSON dışında hiçbir şey yazma.

{{
  "puan": 3.5,
  "iyi": [{{"alinti": "...", "aciklama": "..."}}],
  "hatalar": [{{"alinti": "...", "dogrusu": "...", "neden": "..."}}],
  "kullanilan_kelimeler": ["..."]
}}

KURALLAR:
1. Bütün açıklamalar {dil_adi} olsun ("alinti" ve "dogrusu" İngilizce, metindeki gibi).
2. "iyi": 1 ile 4 arası madde. Her madde TEK CÜMLE: neyin iyi olduğunu ve NEDEN iyi olduğunu söyle.
   Her madde metinden somut bir alıntıya dayansın. Boş övgü ("Güzel metin!") yazma.
3. "hatalar": Her madde TEK BİR hataya değinir.
   - "alinti": hatalı kısım, metinden HARFİ HARFİNE kopyala (en kısa anlamlı parça, en çok {10 if akademik else 8} kelime).
   - "dogrusu": o parçanın düzeltilmiş hâli.
   - "neden": tek cümlelik açıklama ({dil_adi}). Türkçe örnek:
     {{"alinti": "he go to school", "dogrusu": "he goes to school", "neden": "Tekil öznede fiile -s eklenir."}}
{gercek_hata}
   - Hata yoksa boş liste döndür. "Geliştirilebilir", "öneriler" gibi başka bir bölüm YOKTUR.
4. {sertlik_kurali}
5. "puan": 5 üzerinden, yarım adımlı (1, 1.5, 2, … 5). Bantlar:
{_PUAN_AKADEMIK if akademik else _PUAN_GUNLUK}
6. "kullanilan_kelimeler": aşağıdaki "kullanmayı dene" kelimelerinden metinde (çekimli hâli dahil)
   kullanılanlar, listedeki yazımıyla. Kullanmak zorunlu değildir; kullanılmaması puanı düşürmez.
7. Metin İngilizce değilse ya da değerlendirilecek bir metin değilse "puan": 0 ver ve listeleri boş bırak.
8. Markdown, yıldız, başlık ya da kod bloğu kullanma.
{chr(10) + _AKADEMIK_KURALLAR + chr(10) if akademik else ""}
Konu: {konu_satiri}
Kullanmayı dene kelimeleri: {kelime_satiri}

ÖĞRENCİNİN METNİ:
<<<
{metin}
>>>
"""


# ---------------------------------------------------------------------------
# Cevabın doğrulanması
# ---------------------------------------------------------------------------

class GecersizCevap(ValueError):
    """Model cevabı kullanılamaz (JSON değil, puan yok…). Yeniden denenir."""


_KOD_BLOGU = re.compile(r"```[a-zA-Z0-9]*")
_BICIM = re.compile(r"(\*\*|__|`)")


def _json_ayikla(ham):
    """Cevaptan JSON nesnesini çıkarır: kod bloğu, önündeki/arkasındaki metin atılır."""
    if isinstance(ham, dict):
        return ham
    ham = _KOD_BLOGU.sub("", str(ham or "")).strip()
    try:
        return json.loads(ham)
    except (TypeError, ValueError):
        pass
    bas, son = ham.find("{"), ham.rfind("}")
    if bas == -1 or son <= bas:
        raise GecersizCevap("Cevapta JSON yok.")
    try:
        return json.loads(ham[bas:son + 1])
    except ValueError as exc:
        raise GecersizCevap("Cevaptaki JSON bozuk.") from exc


def puan_yuvarla(deger):
    """Puanı [1, 5] aralığına ve en yakın yarım adıma getirir (x.25 -> x.5)."""
    deger = min(5.0, max(1.0, float(deger)))
    return math.floor(deger * 2 + 0.5) / 2


def _puan_oku(ham):
    if isinstance(ham, bool) or ham is None:
        raise GecersizCevap("Puan yok.")
    if isinstance(ham, str):
        ham = ham.strip().replace(",", ".").split("/")[0].strip()
    try:
        deger = float(ham)
    except (TypeError, ValueError) as exc:
        raise GecersizCevap("Puan sayı değil.") from exc
    if math.isnan(deger) or math.isinf(deger):
        raise GecersizCevap("Puan geçersiz.")
    return deger


def _temiz(deger):
    """Bir alanı düz, tek satırlık metne indirger; metin değilse boş string."""
    if not isinstance(deger, str):
        return ""
    deger = _BICIM.sub("", deger)
    return re.sub(r"\s+", " ", deger).strip()


_TIRNAK = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})


def alinti_bul(metin, alinti):
    """
    Alıntının metindeki ilk yeri: (başlangıç, bitiş) ya da None.

    Büyük/küçük harf, boşluk sayısı ve kıvrık/düz tırnak farkı önemsenmez;
    bulunan aralık metnin kendisine aittir (altı çizilen parça metinden gelir).
    """
    alinti = (alinti or "").translate(_TIRNAK).strip().strip('"').strip()
    if not alinti or not metin:
        return None
    parcalar = [re.escape(p) for p in alinti.split()]
    desen = r"\s+".join(parcalar).replace("'", "['’‘]").replace('"', '["“”]')
    m = re.search(desen, metin, flags=re.IGNORECASE)
    return (m.start(), m.end()) if m else None


def _kelime_gecer_mi(metin_kucuk, kelime):
    """Kelime ya da çekimli biçimlerinden biri metinde tam kelime olarak geçiyor mu?"""
    from words import inflect

    yuzeyler = {y for y, _tur in inflect.forms_for(kelime.text, kelime.pos,
                                                  kelime.v2Form, kelime.v3Form)}
    yuzeyler.update(kelime.forms.values_list("surface", flat=True))
    for yuzey in yuzeyler:
        if yuzey and re.search(rf"(?<![a-z]){re.escape(yuzey.lower())}(?![a-z])", metin_kucuk):
            return True
    return False


def kullanilan_kelimeleri_bul(metin, kelimeler, modelin_listesi=()):
    """
    Önerilen kelimelerden metinde kullanılanlar (öneri sırasıyla).
    Kendi aramamız (çekimler dahil) ile modelin listesi birleştirilir; model
    ancak önerilen bir kelimeyi söylerse dikkate alınır.
    """
    metin_kucuk = (metin or "").translate(_TIRNAK).lower()
    modelinki = {str(k).strip().lower() for k in (modelin_listesi or []) if isinstance(k, str)}
    sonuc = []
    for kelime in kelimeler:
        ad = kelime.text.lower()
        if ad in sonuc:
            continue
        if ad in modelinki or _kelime_gecer_mi(metin_kucuk, kelime):
            sonuc.append(ad)
    return sonuc


def cevabi_coz(ham, metin, sertlik=Sertlik.NORMAL, kelimeler=(), tur=YaziTuru.GUNLUK):
    """
    Model cevabını doğrular ve temiz bir sözlüğe çevirir.

    Döner:
        {"uygun_degil": True}  -> model metni değerlendirilebilir bulmadı (puan 0)
        {"puan", "iyi", "hatalar", "kullanilan_kelimeler"}
    Kullanılamaz cevapta GecersizCevap fırlatır.
    """
    veri = _json_ayikla(ham)
    if not isinstance(veri, dict):
        raise GecersizCevap("JSON bir nesne değil.")

    ham_puan = _puan_oku(veri.get("puan"))
    if ham_puan <= 0:
        return {"uygun_degil": True}

    iyi = []
    for madde in veri.get("iyi") or []:
        if not isinstance(madde, dict):
            continue
        aciklama = _temiz(madde.get("aciklama"))
        yer = alinti_bul(metin, _temiz(madde.get("alinti")))
        if not aciklama or yer is None:
            continue
        iyi.append({"alinti": metin[yer[0]:yer[1]], "aciklama": aciklama})
        if len(iyi) >= EN_COK_IYI:
            break

    en_cok = hata_siniri(sertlik, tur)
    hatalar, gorulen = [], set()
    for madde in veri.get("hatalar") or []:
        if not isinstance(madde, dict):
            continue
        dogrusu = _temiz(madde.get("dogrusu"))
        neden = _temiz(madde.get("neden"))
        yer = alinti_bul(metin, _temiz(madde.get("alinti")))
        if not dogrusu or not neden or yer is None:
            continue
        alinti = metin[yer[0]:yer[1]]
        # "Düzeltme" aynıysa hata değil; aynı parça iki kez yazılmışsa birini tut.
        if alinti.strip() == dogrusu.strip() or yer in gorulen:
            continue
        gorulen.add(yer)
        hatalar.append({"alinti": alinti, "dogrusu": dogrusu, "neden": neden})
        if len(hatalar) >= en_cok:
            break

    return {
        "puan": puan_yuvarla(ham_puan),
        "iyi": iyi,
        "hatalar": hatalar,
        "kullanilan_kelimeler": kullanilan_kelimeleri_bul(
            metin, kelimeler, veri.get("kullanilan_kelimeler")),
    }


# ---------------------------------------------------------------------------
# Görünüm yardımcıları
# ---------------------------------------------------------------------------

PUAN_BANTLARI = (
    (4.5, _("Çok iyi")),
    (4.0, _("İyi")),
    (3.5, _("Ortalama")),
    (3.0, _("Biraz daha çalışalım")),
    (2.0, _("Zorlanmışsın")),
    (1.0, _("Başlangıç")),
)


def puan_etiketi(puan):
    """Puanın yanında duran kısa, cesaretlendirici etiket."""
    if puan is None:
        return ""
    for alt, etiket in PUAN_BANTLARI:
        if puan >= alt:
            return etiket
    return PUAN_BANTLARI[-1][1]


def puan_yazisi(puan):
    """3.0 -> "3", 3.5 -> "3,5"."""
    if puan is None:
        return ""
    return f"{puan:g}".replace(".", ",")


def metin_parcalari(metin, hatalar):
    """
    Metni altı çizili gösterim için parçalara böler:
        [{"metin": "...", "hata": None | hata_sırası}, ...]
    Her hatanın alıntısı metinde bulunur (birden çok geçiyorsa ilki);
    üst üste binen alıntılardan önce başlayan çizilir, diğeri yalnızca listede kalır.
    """
    araliklar = []
    for sira, hata in enumerate(hatalar or []):
        yer = alinti_bul(metin, hata.get("alinti"))
        if yer:
            araliklar.append((yer[0], yer[1], sira))
    araliklar.sort()

    parcalar, konum = [], 0
    for bas, son, sira in araliklar:
        if bas < konum:
            continue
        if bas > konum:
            parcalar.append({"metin": metin[konum:bas], "hata": None})
        parcalar.append({"metin": metin[bas:son], "hata": sira})
        konum = son
    if konum < len(metin):
        parcalar.append({"metin": metin[konum:], "hata": None})
    return parcalar


def duz_metin(sonuc):
    """Değerlendirmenin düz metin hâli (Text.response; dışa aktarmada görünür)."""
    satirlar = [f"Puan: {puan_yazisi(sonuc['puan'])} / 5"]
    if sonuc["iyi"]:
        satirlar.append("\nİyi yaptıkların:")
        satirlar += [f'- "{m["alinti"]}": {m["aciklama"]}' for m in sonuc["iyi"]]
    if sonuc["hatalar"]:
        satirlar.append("\nHatalar:")
        satirlar += [f'- {m["alinti"]} -> {m["dogrusu"]} · {m["neden"]}' for m in sonuc["hatalar"]]
    return "\n".join(satirlar)


# ---------------------------------------------------------------------------
# Değerlendirme
# ---------------------------------------------------------------------------

# degerlendir() dönüş kodları
TAMAM = "tamam"
UYGUN_DEGIL = "uygun_degil"
def _baglantiyi_tazele():
    """
    Gemini beklenirken (kota beklemesi + yeniden deneme, dakikalar sürebilir) veritabanı bağlantısı
    boşta kalır; paylaşımlı sunucudaki MySQL onu kapatır ve sonraki yazma "MySQL server has gone
    away" ile düşer (17 Ekim, yazilari_yeniden_dene). Bağlantı kapatılır, sonraki sorgu yenisini açar.
    Bir işlem (atomic) içindeyken dokunulmaz.
    """
    from django.db import connection
    if not connection.in_atomic_block:
        connection.close()


KOTA = "kota"            # Gemini kotası doldu
SERVIS = "servis"        # Gemini geçici olarak cevap vermedi
YOGUN = "yogun"          # bizim dakikalık sınırımız doldu, istek atılmadı
YAPILANDIRMA = "yapilandirma"  # anahtar/paket/model sorunu
BOZUK = "bozuk"          # cevap kullanılamadı

BEKLEYEN_SONUCLAR = (KOTA, SERVIS, YOGUN, YAPILANDIRMA, BOZUK)


def degerlendir(yazi, on_event=None, arka_planda=False):
    """
    Metni Gemini'ye değerlendirtir ve sonucu metne yazar.

    Başarısız olursa metin KAYBOLMAZ: `bekliyor` durumunda kalır (listede sarı
    "Henüz değerlendirilmedi" etiketi) ve `yazilari_yeniden_dene` komutu
    sonra yeniden dener. Dönüş: yukarıdaki kodlardan biri.
    """
    if yazi.durum != YaziDurumu.BEKLIYOR:
        return TAMAM if yazi.durum == YaziDurumu.TAMAM else UYGUN_DEGIL

    if not limits.cagri_hakki_al():
        return YOGUN

    kelimeler = list(yazi.words.all())
    akademik = yazi.tur == YaziTuru.AKADEMIK
    prompt = prompt_olustur(yazi.content, yazi.sertlik, [k.text for k in kelimeler], yazi.konu,
                            geri_bildirim_dili(yazi.owner), yazi.tur)

    yazi.deneme_sayisi += 1
    yazi.son_deneme = timezone.now()
    yazi.save(update_fields=["deneme_sayisi", "son_deneme"])

    try:
        cevap = gemini.generate(
            prompt,
            response_schema=DegerlendirmeSemasi,
            temperature=0.2,
            on_event=on_event,
            bekle=arka_planda,     # kullanıcı beklerken uyunmaz (rapor 18.37)
            timeout=AKADEMIK_ZAMAN_ASIMI if akademik else None,
        )
    except gemini.GeminiRateLimit:
        return KOTA
    except gemini.GeminiUnavailable:
        return SERVIS
    except gemini.GeminiError:
        return YAPILANDIRMA
    except Exception:
        logger.exception("Gemini çağrısı beklenmedik şekilde hata verdi.")
        return SERVIS
    finally:
        _baglantiyi_tazele()

    try:
        sonuc = cevabi_coz(getattr(cevap, "text", None) or "", yazi.content, yazi.sertlik, kelimeler, yazi.tur)
    except GecersizCevap as exc:
        logger.warning("Yazma değerlendirmesi kullanılamadı (metin=%s): %s", yazi.pk, exc)
        return BOZUK

    yazi.degerlendirildi = timezone.now()
    if sonuc.get("uygun_degil"):
        yazi.durum = YaziDurumu.UYGUN_DEGIL
        yazi.response = "Bu metin değerlendirilemedi."
        yazi.save(update_fields=["durum", "response", "degerlendirildi"])
        return UYGUN_DEGIL

    yazi.durum = YaziDurumu.TAMAM
    yazi.puan = sonuc["puan"]
    yazi.geri_bildirim = {
        "iyi": sonuc["iyi"],
        "hatalar": sonuc["hatalar"],
        "kullanilan_kelimeler": sonuc["kullanilan_kelimeler"],
    }
    yazi.response = duz_metin(sonuc)
    yazi.save(update_fields=["durum", "puan", "geri_bildirim", "response", "degerlendirildi"])

    sinyaller.degerlendirildi(yazi, arka_planda=arka_planda)
    return TAMAM
