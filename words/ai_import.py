"""
Yapay zeka ile kelime zenginleştirme.

Kullanıcı yalnızca kelimeleri yazıyor; anlam, açıklama, fiil halleri, eş/zıt
anlamlılar, kullanım kalıpları ve 10 örnek cümle Gemini tarafından dolduruluyor.

Neden JSON şeması kullanıyoruz
------------------------------
Cevabı serbest metin olarak isteyip elle ayrıştırmak kırılgan olurdu: model
bazen markdown kod bloğu içine koyar, bazen alan adını değiştirir, bazen bir
alanı atlar. `response_schema` verildiğinde Gemini şemaya UYAN geçerli bir JSON
döndürmek zorunda kalıyor ve cevap doğrudan pydantic nesnesine dönüşüyor.

Neden parçalara bölüyoruz, ama paralel DEĞİL
--------------------------------------------
20 kelime x 10 cümle tek istekte çok büyük bir çıktı demek; hem çıktı sınırına
takılma riski var hem de tek bir hata bütün partiyi götürür. O yüzden kelimeler
gruplara bölünüyor.

Gruplar önce paralel gönderiliyordu; bu yanlıştı. Gemini'nin ücretsiz katmanında
model başına DAKİKADA 5 istek sınırı var ve paralel gönderim bu sınıra anında
çarpıp 429 aldırıyordu. Artık gruplar sırayla gidiyor, aralarına
LearnVocab.gemini'deki sınırlayıcı boşluk koyuyor ve grup başına tekrar deneme
kapalı (max_retries=0) — böylece bir partide harcanan istek sayısı mümkün
olduğunca az tutuluyor.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional

from django.conf import settings
from pydantic import BaseModel, Field

from LearnVocab import gemini

logger = logging.getLogger(__name__)

# Örnek cümlelerin seviye dağılımı: artan zorlukta, ağırlık üst seviyelerde.
# Toplam sayı modeldeki cümle sayısıyla aynı olmalı (Word.EXAMPLE_SENTENCE_COUNT);
# fazlası kaydedilirken atılırdı.
SENTENCE_PLAN = [
    ("A2", 1),
    ("B1", 1),
    ("B2", 1),
    ("B2+", 1),
    ("C1", 1),
]
SENTENCE_COUNT = sum(count for _level, count in SENTENCE_PLAN)


# ---------------------------------------------------------------------------
# Gemini'nin döneceği JSON'un şeması
# ---------------------------------------------------------------------------

class ExampleSentence(BaseModel):
    level: str = Field(description="Cümlenin seviyesi: A2, B1, B2, B2+ veya C1")
    sentence: str = Field(description="Kelimenin geçtiği İngilizce örnek cümle")


class EnrichedWord(BaseModel):
    requested: str = Field(description="Kullanıcının yazdığı hâliyle kelime")
    found: bool = Field(
        description="Kelime İngilizce'de var mı (ya da yazım hatası düzeltilebildi mi)"
    )
    english_word: str = Field(default="", description="Kelimenin doğru İngilizce yazımı")
    was_corrected: bool = Field(
        default=False, description="Yazım hatası düzeltildiyse true"
    )
    is_verb: bool = Field(default=False, description="Kelime fiil olarak kullanılıyor mu")
    meaning_tr: str = Field(default="", description="Türkçe anlam(lar)ı")
    explanation: str = Field(default="", description="İngilizce açıklama(lar)ı")
    v2_form: str = Field(default="", description="Fiilse ikinci hâli, değilse boş")
    v3_form: str = Field(default="", description="Fiilse üçüncü hâli, değilse boş")
    synonyms: List[str] = Field(default_factory=list)
    antonyms: List[str] = Field(default_factory=list)
    collocations: List[str] = Field(default_factory=list)
    example_sentences: List[ExampleSentence] = Field(default_factory=list)


class EnrichmentResponse(BaseModel):
    words: List[EnrichedWord]


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_LEVEL_PLAN_TEXT = ", ".join(f"{count} adet {level}" for level, count in SENTENCE_PLAN)

PROMPT_TEMPLATE = """Sen İngilizce öğrenen Türk öğrenciler için kelime kartı hazırlayan bir dil uzmanısın.

Sana bir İngilizce kelime listesi vereceğim. Her kelime için aşağıdaki alanları
dolduracaksın. Cevabını SADECE istenen JSON şemasına uygun olarak vereceksin.

ALANLAR
-------
- requested       : Kullanıcının yazdığı hâliyle kelime (aynen geri ver, değiştirme)
- found           : Bu kelime İngilizce'de gerçekten var mı (aşağıdaki kurallara bak)
- english_word    : Kelimenin doğru İngilizce yazımı (küçük harfle)
- was_corrected   : Kullanıcı yanlış yazdıysa ve sen düzelttiysen true
- is_verb         : Kelime fiil olarak da kullanılıyorsa true
- meaning_tr      : Türkçe anlamı
- explanation     : İngilizce açıklaması (sözlük tanımı gibi, kısa ve net)
- v2_form         : Fiilse ikinci hâli (past simple). Fiil değilse BOŞ BIRAK.
- v3_form         : Fiilse üçüncü hâli (past participle). Fiil değilse BOŞ BIRAK.
- synonyms        : 2-4 eş anlamlı kelime
- antonyms        : 2-4 zıt anlamlı kelime (yoksa boş liste)
- collocations    : 2-4 doğal kullanım kalıbı (örn: "reach a conclusion")
- example_sentences : {sentence_count} adet örnek cümle (aşağıya bak)

KURAL 1 - OLMAYAN KELİMELER
---------------------------
Eğer kullanıcının yazdığı şey İngilizce'de gerçekten yoksa VE bilinen hiçbir
İngilizce kelimeye yakın da değilse, o kelime için found=false ver ve diğer
alanları boş bırak. Uydurma kelime ÜRETME, zorlama.

KURAL 2 - YAZIM HATALARI
------------------------
Kullanıcının yazdığı şey bilinen bir İngilizce kelimeye çok yakınsa (tipik bir
yazım hatası ise) bunu bir hata olarak kabul et, doğru kelimeyi bul ve o kelimeye
göre doldur. found=true, was_corrected=true ver ve english_word alanına DOĞRU
yazımı koy. Örnek: "recieve" -> "receive", "definately" -> "definitely".
Ama gerçekten farklı bir kelimeye benziyorsa zorlamadan found=false ver.

KURAL 3 - BİRDEN FAZLA ANLAM
----------------------------
Bir kelimenin birbirinden belirgin şekilde farklı, yaygın olarak kullanılan iki
anlamı varsa İKİSİNİ birden ver ve şu biçimi kullan:

  meaning_tr  : "1. birinci anlam / 2. ikinci anlam"
  explanation : "1. first meaning explained / 2. second meaning explained"

Bu durumda örnek cümleleri iki anlam arasında paylaştır (yaklaşık yarı yarıya).
Kelimenin tek yaygın anlamı varsa numaralandırma KULLANMA, düz yaz.
İkiden fazla anlam verme; sadece en yaygın iki anlamı seç.

KURAL 4 - ÖRNEK CÜMLELER
------------------------
Her kelime için tam {sentence_count} adet örnek cümle yaz. Zorluk sırayla ARTSIN;
listenin başı en kolay, sonu en zor olsun. Seviye dağılımı şöyle olsun:
{level_plan}

Her cümlede kelimenin KENDİSİ geçmeli (çekimli hâli olabilir: "retain" için
"retained" gibi). Kelimeyi eş anlamlısıyla değiştirme; cümleden kelimeyi
çıkarıp boşluk doldurma sorusu üretiyoruz, o yüzden kelime cümlede mutlaka
geçmeli.

Cümleler doğal, anlamlı ve birbirinden farklı bağlamlarda olsun. Aynı kalıbı
tekrar etme.

KURAL 5 - BİÇİM
---------------
Alanların içinde Markdown veya LaTeX KULLANMA. Yıldız (*), alt çizgi (_),
ters tırnak (`), # başlığı, $ ... $ gibi hiçbir işaret olmasın. Düz metin yaz.

ÖRNEKLER
--------
Girdi: "recieve"
  requested: "recieve", found: true, english_word: "receive", was_corrected: true,
  is_verb: true, meaning_tr: "almak, teslim almak",
  explanation: "to get or be given something",
  v2_form: "received", v3_form: "received",
  synonyms: ["get", "obtain", "accept"], antonyms: ["send", "give"],
  collocations: ["receive a letter", "receive support", "receive an award"],
  example_sentences: A2 seviyesinden C1'e doğru zorlaşan {sentence_count} cümle.

Girdi: "spring"  (iki yaygın anlamı olan bir kelime)
  meaning_tr: "1. ilkbahar / 2. yay, zemberek"
  explanation: "1. the season between winter and summer / 2. a coiled piece of metal that returns to its shape"
  example_sentences: cümlelerin yaklaşık yarısı birinci anlam, yarısı ikinci anlam.

Girdi: "asdqwe"
  requested: "asdqwe", found: false, diğer alanlar boş.

ŞİMDİ ŞU KELİMELERİ İŞLE
------------------------
{words}
"""


def build_prompt(words):
    """Verilen kelime listesi için Gemini prompt'unu hazırlar."""
    level_plan = "\n".join(
        f"  - {count} adet {level} seviyesinde cümle" for level, count in SENTENCE_PLAN
    )
    listed = "\n".join(f"- {word}" for word in words)
    return PROMPT_TEMPLATE.format(
        sentence_count=SENTENCE_COUNT,
        level_plan=level_plan,
        words=listed,
    )


# ---------------------------------------------------------------------------
# Girdinin temizlenmesi
# ---------------------------------------------------------------------------

def parse_input_words(raw_text):
    """
    Kullanıcının girdiği metni kelime listesine çevirir.

    Satır, virgül ve noktalı virgülle ayrılmış girdileri kabul eder; boşları
    atar, tekrar edenleri (büyük/küçük harf duyarsız) teker teker alır ve
    ayardaki üst sınıra kadar keser.

    Dönüş: (kelimeler, sınırı_aştı_mı)
    """
    if not raw_text:
        return [], False

    text = raw_text.replace(";", "\n").replace(",", "\n")

    seen = set()
    words = []
    for line in text.splitlines():
        word = " ".join(line.split()).strip()
        if not word:
            continue
        key = word.lower()
        if key in seen:
            continue
        seen.add(key)
        words.append(word)

    limit = getattr(settings, "AI_WORD_IMPORT_MAX_WORDS", 20)
    return words[:limit], len(words) > limit


def _chunks(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]


# ---------------------------------------------------------------------------
# Gemini çağrısı
# ---------------------------------------------------------------------------

@dataclass
class ImportOutcome:
    """Zenginleştirme sonucunun tamamı."""
    words: List[EnrichedWord] = field(default_factory=list)
    error: Optional[str] = None  # None | rate_limit | unavailable | unconfigured | failed
    detail: str = ""             # kota hatalarında Google'ın verdiği ayrıntı

    @property
    def is_total_failure(self):
        return self.error is not None and not self.words


def _chunk_event_handler(reporter, word_count):
    """
    Gemini olaylarını ilerleme çubuğuna çevirir.

    Bir grup içinde birden çok model denenebiliyor. Her deneme çubuğu biraz
    daha ilerletiyor ki "servis yoğun, yedek model deneniyor" durumunda
    kullanıcı takıldığını değil, çalıştığını görsün.
    """
    if reporter is None:
        return None

    def handle(name, info):
        model_count = max(1, info.get("model_count", 1))
        model_index = info.get("model_index", 0)

        # Bir grup içinde denemeler ilerledikçe %10 -> %80 arası dolar.
        ratio = 0.10 + 0.70 * (model_index / model_count)

        if name == "attempt":
            if model_index == 0 and info.get("attempt", 1) == 1:
                reporter.set(ratio, f"{word_count} kelime yapay zekaya gönderiliyor...")
            else:
                reporter.set(ratio, f"Yedek model deneniyor ({info.get('model')})...")

        elif name == "error":
            kind = info.get("kind")
            if kind == "transient":
                reporter.message("Servis yoğun, birazdan yeniden denenecek...")
            elif kind == "rate_limit":
                reporter.message("İstek kotası doldu, bekleniyor...")

        elif name == "success":
            reporter.set(0.85, "Cevap alındı, kelimeler işleniyor...")

    return handle


def _enrich_chunk(words, reporter=None):
    """
    Tek bir grup kelimeyi zenginleştirir.

    Dönüş: (kelime_listesi, hata_kodu). Hata varsa liste boş olur.
    """
    prompt = build_prompt(words)

    try:
        # max_retries=0: kota bütçesini korumak için aynı modelde ısrar etme,
        # başarısız olursa doğrudan yedek modele geç.
        response = gemini.generate(
            prompt,
            response_schema=EnrichmentResponse,
            max_retries=0,
            # Bir grup için 10 kelime x 10 cümle üretiliyor; metin
            # değerlendirmeye göre çok daha uzun sürüyor ve varsayılan
            # zaman aşımına sığmayıp 504 alıyordu.
            timeout=getattr(settings, "AI_WORD_IMPORT_TIMEOUT_SECONDS", 60),
            on_event=_chunk_event_handler(reporter, len(words)),
        )
    except gemini.GeminiRateLimit as exc:
        return [], ("rate_limit", getattr(exc, "detail", ""))
    except gemini.GeminiUnavailable:
        return [], ("unavailable", "")
    except gemini.GeminiUnconfigured:
        return [], ("unconfigured", "")
    except gemini.GeminiError:
        return [], ("failed", "")

    parsed = getattr(response, "parsed", None)

    # Şema verildiğinde SDK cevabı zaten pydantic nesnesine çeviriyor; yine de
    # eski/farklı SDK sürümlerinde bu alan boş gelebiliyor, o yüzden metinden
    # ayrıştırmaya da düşebiliyoruz.
    if parsed is None:
        try:
            parsed = EnrichmentResponse.model_validate_json(response.text or "")
        except Exception:
            logger.warning("Gemini cevabı şemaya uymadı: %s", (response.text or "")[:300])
            return [], ("failed", "")

    return list(parsed.words), None


def enrich_words(words, reporter=None):
    """
    Kelimeleri (gerekirse birden fazla istekte) zenginleştirir.

    Gruplar paralel gönderilir: 20 kelimeyi tek tek sırayla beklemek kullanıcı
    için çok uzun sürerdi. Bir grup başarısız olursa diğerlerinin sonucu yine
    kullanılır (kısmi başarı).
    """
    if not words:
        return ImportOutcome()

    chunk_size = max(1, getattr(settings, "AI_WORD_IMPORT_CHUNK_SIZE", 10))
    groups = list(_chunks(words, chunk_size))

    # Toplam süre sınırı: istek aralığı sınırlayıcısı ve yedek modeller
    # üst üste bindiğinde bekleme uzayabiliyor. Kullanıcı bir web isteğinin
    # içinde beklediği için bir noktada durup eldekini kaydetmek gerekiyor.
    budget = float(getattr(settings, "AI_WORD_IMPORT_TIME_BUDGET_SECONDS", 120) or 0)
    started_at = time.monotonic()

    results = []
    errors = {}

    for index, group in enumerate(groups):
        group_reporter = reporter.slice_for(index, len(groups)) if reporter else None

        if index and budget and (time.monotonic() - started_at) > budget:
            logger.warning(
                "Kelime zenginleştirme süre bütçesini aştı; kalan %s grup işlenmedi.",
                len(groups) - index,
            )
            errors.setdefault("failed", "")
            break

        chunk_words, error = _enrich_chunk(group, reporter=group_reporter)
        results.extend(chunk_words)

        if group_reporter:
            group_reporter.set(1.0, f"{len(results)} kelime hazırlandı.")

        if error:
            code, detail = error
            errors.setdefault(code, detail)

            # Kota dolduysa kalan gruplar da kesin başarısız olur; boşuna
            # istek harcayıp beklemenin anlamı yok.
            if code in ("rate_limit", "unconfigured"):
                break

    # Öncelik sırası: yapılandırma hatası > kota > geçici > diğer
    error = None
    detail = ""
    for candidate in ("unconfigured", "rate_limit", "unavailable", "failed"):
        if candidate in errors:
            error = candidate
            detail = errors[candidate]
            break

    return ImportOutcome(words=results, error=error, detail=detail)


# ---------------------------------------------------------------------------
# Gemini cevabından Word alanlarına
# ---------------------------------------------------------------------------

def _fit(value, max_length):
    """
    Değeri alanın sınırına sığdırır.

    Model ara sıra sınırı aşan metinler döndürebiliyor (özellikle iki anlamlı
    kelimelerde). MySQL katı kipte bunu hata olarak reddeder, o yüzden kaydetmeden
    önce kırpıyoruz.
    """
    text = " ".join(str(value or "").split())
    if not text:
        return ""
    return text[:max_length].strip()


def _join(items, max_length=500):
    """Liste alanlarını virgüllü metne çevirir (modeldeki biçim)."""
    cleaned = []
    seen = set()
    for item in items or []:
        value = " ".join(str(item or "").split())
        if not value or value.lower() in seen:
            continue
        seen.add(value.lower())
        cleaned.append(value)

    joined = ", ".join(cleaned)
    return joined[:max_length].rstrip(", ") or ""


def build_word_kwargs(enriched):
    """
    Gemini'den gelen bir kelimeyi Word(**kwargs) hâline getirir.

    Anlam, örnek cümle, eş/zıt anlamlı gibi alanlar artık ayrı tablolarda;
    bunlar `_extras` altında birlikte döner ve `save_enriched_words`
    tarafından yazılır.

    Kaydedilemeyecek durumda None döner:
      - found=false (İngilizce'de yok)
      - kelimenin kendisi ya da Türkçe anlamı boş
      - hiç örnek cümle yok
    """
    if not enriched.found:
        return None

    english = _fit(enriched.english_word, 120).lower() or _fit(enriched.requested, 120).lower()
    meaning = _fit(enriched.meaning_tr, 300)
    if not english or not meaning:
        return None

    sentences = [
        _fit(item.sentence, 400)
        for item in (enriched.example_sentences or [])
        if _fit(item.sentence, 400)
    ]
    if not sentences:
        return None

    is_verb = bool(enriched.is_verb)
    pos = "verb" if is_verb else "noun"

    return {
        "text": english,
        "pos": pos,
        "v2Form": (_fit(enriched.v2_form, 80) or None) if is_verb else None,
        "v3Form": (_fit(enriched.v3_form, 80) or None) if is_verb else None,
        # İstenen sabitler: seviye belirtilmemiş, kelime kullanıcıya özel
        "cefr": "Belirtilmemiş",
        "visibility": "private",
        "isBaseWord": False,
        "_extras": {
            "meaning": meaning,
            "definition": _fit(enriched.explanation, 600) or None,
            # Cümleler geldiği sırada; sıra zorluk sırasıdır (A2 -> C1)
            "sentences": sentences,
            "synonyms": [w for w in (enriched.synonyms or []) if w],
            "antonyms": [w for w in (enriched.antonyms or []) if w],
        },
    }


# ---------------------------------------------------------------------------
# Kaydetme
# ---------------------------------------------------------------------------

def save_enriched_words(user, outcome):
    """
    Zenginleştirilmiş kelimeleri kullanıcının listesine ekler.

    Görünüm katmanından ayrı tutuluyor: aynı iş hem normal istekte hem de
    arka plan iş parçacığında (ilerleme çubuğu akışı) çalışıyor.

    Yeni modelde bir kelime tek satır değil: aile + kelime + anlam +
    anlama bağlı örnek cümleler + çekim biçimleri. Eş/zıt anlamlı bağları yalnızca
    hedef kelime sözlükte varsa kurulur.

    Dönüş: özet sözlüğü. Mesajları görünüm katmanı üretiyor.
    """
    from words import inflect
    from words.models import (
        ExampleSentence, Meaning, UserWordLink, Word, WordFamily, WordRelation,
    )

    existing = {
        value.lower()
        for value in Word.objects.filter(userLinks__user=user)
        .values_list("text", flat=True)
    }

    summary = {
        "added": [], "corrected": [], "duplicates": [],
        "not_found": [], "unusable": [],
        "error": outcome.error, "detail": outcome.detail,
    }

    for item in outcome.words:
        requested = (item.requested or "").strip()

        kwargs = build_word_kwargs(item)
        if kwargs is None:
            (summary["unusable"] if item.found else summary["not_found"]).append(requested)
            continue

        extras = kwargs.pop("_extras")
        english = kwargs["text"]

        if english in existing:
            summary["duplicates"].append(english)
            continue

        # Aynı yazım + tür zaten varsa yeni satır açmak yerine listeye bağla
        mevcut = Word.objects.filter(text=english, pos=kwargs["pos"]).first()
        if mevcut is not None:
            UserWordLink.objects.get_or_create(user=user, word=mevcut)
            existing.add(english)
            summary["duplicates"].append(english)
            continue

        # Tek kişilik aile; ileride aynı kökten türev gelirse yanına eklenir
        aile, _ = WordFamily.objects.get_or_create(root=english)
        word = Word.objects.create(owner=user, family=aile, **kwargs)

        anlam = Meaning.objects.create(word=word, meaning_tr=extras["meaning"],
                                       definition=extras["definition"], sort_order=0)

        # Cümleler kelimeye değil ANLAMA bağlı; AI tek anlam ürettiği için
        # hepsi ana anlama gidiyor.
        ExampleSentence.objects.bulk_create([
            ExampleSentence(meaning=anlam, text=cumle, source="AI", sort_order=i)
            for i, cumle in enumerate(extras["sentences"][:Meaning.EXAMPLE_SENTENCE_COUNT])
        ])

        inflect.rebuild_forms(word)

        # Bağlar iki KAYIT arasındadır; sözlükte olmayan kelimeye bağ kurulmaz.
        for tur, adlar in (("synonym", extras["synonyms"]), ("antonym", extras["antonyms"])):
            for ad in adlar:
                hedef = Word.objects.filter(text__iexact=(ad or "").strip()).exclude(id=word.id).first()
                if hedef is not None:
                    WordRelation.objects.get_or_create(
                        from_word=word, to_word=hedef, type=tur,
                    )

        UserWordLink.objects.create(user=user, word=word)
        existing.add(english)
        summary["added"].append(english)

        if item.was_corrected and requested.lower() != english:
            summary["corrected"].append(f"{requested} -> {english}")

    return summary
