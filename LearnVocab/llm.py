"""
OpenAI uyumlu sohbet API'si için ortak katman.

Gemini'ye giden yol `LearnVocab/gemini.py`'de duruyor; burası ONDAN AYRI ve
bilerek öyle. Gemini katmanı kullanıcının tarayıcıda başlattığı işler için
(metin değerlendirme, tek tek kelime ekleme); burası toplu içerik üretimi
için: binlerce kelimeyi ucuz bir modelle, arka planda, tekrar tekrar
çalıştırılabilir biçimde üretmek.

Neden OpenAI uyumlu?
    gpt-oss, DeepSeek, Qwen, GLM ve Ollama'nın hepsi aynı `/chat/completions`
    arayüzünü konuşuyor. Tek bir istemci yazıp sağlayıcıyı .env'den değiştirmek,
    model başına ayrı SDK kurmaktan hem ucuz hem sağlam. Model pahalılaşırsa
    ya da kapanırsa tek satır ayar değişiyor.

Ayarlar (.env):
    LLM_BASE_URL          - sağlayıcının kök adresi (sonunda /v1)
    LLM_API_KEY           - API anahtarı (Ollama'da gerekmez)
    LLM_MODEL             - model adı
    LLM_TIMEOUT_SECONDS   - tek isteğin zaman aşımı
    LLM_MAX_TOKENS        - cevap için üst sınır (düşünme tokenları dahil)
    LLM_MAX_RETRIES       - geçici hatada tekrar deneme sayısı
    LLM_TEMPERATURE       - üretim sıcaklığı (sözlük için düşük tutulmalı)
    LLM_STRICT_SCHEMA     - katı JSON şeması zorlansın mı
    LLM_REASONING_EFFORT  - düşünen modellerde düşünme derinliği (low/medium/high)
    LLM_PROVIDER_SORT     - OpenRouter sağlayıcı seçimi (throughput/price/latency)
    LLM_PRICE_INPUT       - 1M girdi tokenının doları (maliyet raporu için)
    LLM_PRICE_OUTPUT      - 1M çıktı tokenının doları

Kullanım:
    from LearnVocab import llm
    sonuc = llm.chat_json(system=..., user=..., schema=PydanticModel)
    print(sonuc.data, sonuc.usage.cost_usd)
"""

import json
import logging
import time
from dataclasses import dataclass, field

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Hatalar
# ---------------------------------------------------------------------------

class LLMError(Exception):
    """Bu katmandaki tüm hataların ortak atası."""


class LLMUnconfigured(LLMError):
    """Adres ya da anahtar tanımlı değil."""


class LLMRateLimit(LLMError):
    """Kota / oran sınırı (429). Beklemekten başka çare yok."""


class LLMUnavailable(LLMError):
    """Servis geçici olarak cevap veremiyor (5xx, zaman aşımı, bağlantı)."""


class LLMFatal(LLMError):
    """Kalıcı hata: geçersiz anahtar, bilinmeyen model, bozuk istek."""


class LLMInvalidOutput(LLMError):
    """Model cevap verdi ama şemaya uymayan bir şey döndü."""


class LLMEmptyOutput(LLMInvalidOutput):
    """
    Model hiç içerik döndürmedi.

    Düşünen modellerde bu çoğunlukla tek seferliktir: düşünme tokenları üst
    sınırı yiyor ve geriye cevap kalmıyor, ya da sağlayıcı boş gövde
    döndürüyor. Şema ihlalinden farklı olarak İSTEĞİ TEKRARLAMAK işe yarıyor,
    bu yüzden ayrı sınıf ve tekrar döngüsünün içinde.
    """


# ---------------------------------------------------------------------------
# Token ve maliyet sayacı
# ---------------------------------------------------------------------------

@dataclass
class Usage:
    """
    Bir ya da birden çok isteğin token tüketimi.

    Maliyet raporu bu projede süs değil: bütçe sınırlı, ve hangi prompt
    değişikliğinin maliyeti artırdığını ancak ölçerek görürüz.
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    requests: int = 0

    def __iadd__(self, other):
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.requests += other.requests
        return self

    @property
    def total_tokens(self):
        return self.prompt_tokens + self.completion_tokens

    @property
    def cost_usd(self):
        girdi = float(getattr(settings, "LLM_PRICE_INPUT", 0) or 0)
        cikti = float(getattr(settings, "LLM_PRICE_OUTPUT", 0) or 0)
        return (self.prompt_tokens / 1_000_000) * girdi + \
               (self.completion_tokens / 1_000_000) * cikti

    def __str__(self):
        return (f"{self.requests} istek · {self.prompt_tokens:,} girdi + "
                f"{self.completion_tokens:,} çıktı token · ${self.cost_usd:.4f}")


@dataclass
class Result:
    """Bir isteğin sonucu: doğrulanmış veri + ham metin + tüketim."""

    data: object = None
    raw: str = ""
    usage: Usage = field(default_factory=Usage)


# ---------------------------------------------------------------------------
# Katı JSON şeması
# ---------------------------------------------------------------------------

def strict_schema(model):
    """
    Pydantic modelinden sağlayıcıların kabul ettiği KATI şema üretir.

    Katı kip (`strict: true`) modelin şema dışına çıkmasını API seviyesinde
    engelliyor — yani "bazen markdown kod bloğu döndürdü", "bir alanı unuttu"
    gibi dertler hiç doğmuyor. Karşılığında iki kural var:

        - her nesnede `additionalProperties: false` olmalı
        - her alan `required` listesinde olmalı (isteğe bağlı alan yok)

    Bu yüzden şemadaki alanların hiçbiri opsiyonel değil; boş bırakılacak
    yerler için `""` ve `[]` kullanılıyor.
    """
    sema = model.model_json_schema()
    _katilastir(sema)
    return sema


def _katilastir(dugum):
    if isinstance(dugum, list):
        for eleman in dugum:
            _katilastir(eleman)
        return
    if not isinstance(dugum, dict):
        return

    # Varsayılan değerler katı kiple çelişiyor: alan zaten zorunlu.
    dugum.pop("default", None)

    if dugum.get("type") == "object" and "properties" in dugum:
        dugum["additionalProperties"] = False
        dugum["required"] = list(dugum["properties"].keys())

    for deger in dugum.values():
        _katilastir(deger)


# ---------------------------------------------------------------------------
# İstek
# ---------------------------------------------------------------------------

def _ayar(ad, varsayilan):
    return getattr(settings, ad, varsayilan)


def _hata_sinifi(durum, govde):
    """HTTP durumunu hata sınıfına çevirir."""
    if durum == 429:
        return LLMRateLimit
    if durum >= 500:
        return LLMUnavailable
    if durum in (401, 403):
        return LLMFatal
    # 400: çoğu zaman şema reddi ya da bilinmeyen model — kalıcı.
    return LLMFatal


def chat_json(system, user, schema, *, model=None, temperature=None,
              max_retries=None, timeout=None):
    """
    Modele bir istek atar ve cevabı `schema` (pydantic modeli) ile doğrular.

    Doğrulanmış nesne `Result.data` içinde döner. Model şemaya uymayan bir şey
    döndürürse `LLMInvalidOutput` fırlatılır — çağıran taraf bunu yakalayıp
    kelimeyi "incelenecek" kuyruğuna atabilir. Sessizce yarım veri YAZILMAZ.

    Geçici hatalarda (5xx, zaman aşımı, 429) artan bekleme ile tekrar denenir.
    """
    base_url = (_ayar("LLM_BASE_URL", "") or "").rstrip("/")
    api_key = _ayar("LLM_API_KEY", "") or ""
    model = model or _ayar("LLM_MODEL", "")

    if not base_url or not model:
        raise LLMUnconfigured(
            "LLM_BASE_URL ve LLM_MODEL tanımlı değil. .env dosyanı doldur."
        )

    if temperature is None:
        temperature = float(_ayar("LLM_TEMPERATURE", 0.3))
    if max_retries is None:
        max_retries = int(_ayar("LLM_MAX_RETRIES", 3))
    if timeout is None:
        timeout = float(_ayar("LLM_TIMEOUT_SECONDS", 120))

    govde = {
        "model": model,
        "temperature": temperature,
        "max_tokens": int(_ayar("LLM_MAX_TOKENS", 8000)),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }

    if _ayar("LLM_STRICT_SCHEMA", True):
        govde["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": schema.__name__.lower(),
                "strict": True,
                "schema": strict_schema(schema),
            },
        }
    else:
        # Katı kipi desteklemeyen sağlayıcılar için: en azından JSON zorla.
        govde["response_format"] = {"type": "json_object"}

    # Düşünen modellerde (gpt-oss gibi) düşünme tokenları ÇIKTI olarak
    # faturalanıyor ve süreyi de onlar uzatıyor. Sözlük doldurmak muhakeme
    # gerektiren bir iş değil — şema zaten yapıyı dayatıyor — bu yüzden
    # varsayılan "low". Kalite düşerse "medium" denenebilir.
    caba = _ayar("LLM_REASONING_EFFORT", "low")
    if caba:
        govde["reasoning"] = {"effort": caba}

    # OpenRouter aynı modeli birçok sağlayıcıdan sunuyor ve aralarında 5 kat
    # hız farkı var. Varsayılan yönlendirme ucuzu seçip yavaş olabiliyor.
    saglayici = {}
    sirala = _ayar("LLM_PROVIDER_SORT", "")
    if sirala:
        saglayici["sort"] = sirala

    if govde["response_format"]["type"] == "json_schema":
        # Katı şema gönderiyorsak yalnızca onu DESTEKLEYEN sağlayıcılara git.
        # Desteklemeyen bir sağlayıcıya düşünce üst taraftan "Generated JSON
        # does not match the expected schema" hatası geliyor.
        saglayici["require_parameters"] = True

    yasakli = [a for a in (_ayar("LLM_PROVIDER_IGNORE", "") or "").split(",") if a.strip()]
    if yasakli:
        saglayici["ignore"] = [a.strip() for a in yasakli]

    if saglayici:
        govde["provider"] = saglayici

    basliklar = {"Content-Type": "application/json"}
    if api_key:
        basliklar["Authorization"] = f"Bearer {api_key}"

    son_hata = None
    for deneme in range(max_retries + 1):
        try:
            cevap = requests.post(
                f"{base_url}/chat/completions",
                headers=basliklar, json=govde, timeout=timeout,
            )
        except requests.Timeout as hata:
            son_hata = LLMUnavailable(f"Zaman aşımı ({timeout} sn).")
            son_hata.__cause__ = hata
        except requests.RequestException as hata:
            son_hata = LLMUnavailable(f"Bağlantı hatası: {hata}")
        else:
            if cevap.status_code == 200:
                try:
                    return _cozumle(cevap.json(), schema)
                except (LLMEmptyOutput, LLMUnavailable) as hata:
                    # İkisi de geçici: boş cevap ve sağlayıcı hatası.
                    # Tekrar denemeye DEVAM et — buradan aşağı düşersek
                    # durum kodu 200 olduğu için "kalıcı hata" sayılır ve
                    # çalışma boşuna durur.
                    son_hata = hata
            else:
                metin = cevap.text[:400]
                sinif = _hata_sinifi(cevap.status_code, metin)
                son_hata = sinif(f"HTTP {cevap.status_code}: {metin}")
                if sinif is LLMFatal:
                    raise son_hata

        if deneme < max_retries:
            bekleme = 2 ** deneme
            logger.warning("İstek başarısız (%s). %s sn sonra tekrar denenecek.",
                           son_hata, bekleme)
            time.sleep(bekleme)

    raise son_hata


def _govde_hatasi(govde):
    """
    HTTP 200 ama içinde hata olan cevabı yakalar.

    OpenRouter üst sağlayıcıdan gelen hatayı 200 gövdesinin İÇİNE koyuyor:
    finish_reason "error" oluyor ve yanında bir `error` nesnesi geliyor.
    Durum koduna bakıp "başarılı" saymak, bu cevabı ayrıştırmaya çalışıp
    anlamsız bir hata üretmek demek. Bunlar sağlayıcı kaynaklı ve GEÇİCİ —
    tekrar denendiğinde OpenRouter çoğunlukla başka sağlayıcıya yönlendiriyor.
    """
    hata = govde.get("error")
    secimler = govde.get("choices") or []
    if not hata and secimler:
        ilk = secimler[0] or {}
        if ilk.get("error"):
            hata = ilk["error"]
        elif ilk.get("finish_reason") == "error":
            hata = {"message": "sağlayıcı hata bildirdi"}

    if not hata:
        return None

    saglayici = govde.get("provider", "?")
    mesaj = hata.get("message") if isinstance(hata, dict) else str(hata)
    return f"{saglayici}: {str(mesaj)[:200]}"


def _cozumle(govde, schema):
    """Başarılı cevabı ayrıştırır, şemayla doğrular, tüketimi çıkarır."""
    ust_hata = _govde_hatasi(govde)
    if ust_hata:
        raise LLMUnavailable(f"Sağlayıcı hatası — {ust_hata}")

    try:
        icerik = govde["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as hata:
        raise LLMInvalidOutput(f"Beklenmeyen cevap yapısı: {str(govde)[:300]}") from hata

    ham = (icerik or "").strip()
    if not ham:
        # Sebebi bilmeden tekrar denemek körlemesine olur: "length" üst sınıra
        # çarpıldığını, "content_filter" içeriğin engellendiğini söyler.
        sebep = (govde["choices"][0] or {}).get("finish_reason", "?")
        tuketim = govde.get("usage") or {}
        raise LLMEmptyOutput(
            f"Model boş cevap döndü (finish_reason={sebep}, "
            f"çıktı tokenı={tuketim.get('completion_tokens', '?')})."
        )

    # Katı kip kapalıyken bazı modeller JSON'u kod bloğuna sarıyor.
    if ham.startswith("```"):
        ham = ham.split("```")[1] if "```" in ham[3:] else ham[3:]
        ham = ham.removeprefix("json").strip()

    try:
        veri = json.loads(ham)
    except json.JSONDecodeError as hata:
        raise LLMInvalidOutput(f"Cevap geçerli JSON değil: {ham[:300]}") from hata

    try:
        nesne = schema.model_validate(veri)
    except Exception as hata:
        raise LLMInvalidOutput(f"Cevap şemaya uymuyor: {hata}") from hata

    tuketim = govde.get("usage") or {}
    return Result(
        data=nesne,
        raw=ham,
        usage=Usage(
            prompt_tokens=int(tuketim.get("prompt_tokens", 0) or 0),
            completion_tokens=int(tuketim.get("completion_tokens", 0) or 0),
            requests=1,
        ),
    )
