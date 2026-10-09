"""
Gemini erişimi için ortak katman.

Projede Gemini'yi kullanan birden fazla özellik var (metin değerlendirme,
kelime zenginleştirme). İstemci kurulumu, hata sınıflandırma, tekrar deneme ve
yedek modele geçme mantığı burada tek yerde duruyor; özellikler yalnızca kendi
prompt'larını yazıyor.

Ayarlar (.env):
    GEMINI_API_TOKEN              - API anahtarı
    GEMINI_MODEL                  - kullanılacak model
    GEMINI_FALLBACK_MODELS        - asıl model cevap veremezse denenecekler
    GEMINI_TIMEOUT_SECONDS        - tek isteğin zaman aşımı
    GEMINI_MAX_RETRIES            - geçici hatada asıl modelin tekrar denenmesi
    GEMINI_RETRY_BACKOFF_SECONDS  - denemeler arası bekleme

Hangi modellere erişebildiğini görmek için:
    python manage.py list_gemini_models
"""

import json
import logging
import re
import threading
import time

from django.conf import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Hatalar
# ---------------------------------------------------------------------------

class GeminiError(Exception):
    """Gemini ile ilgili tüm hataların ortak atası."""


class GeminiUnconfigured(GeminiError):
    """Anahtar yok, paket kurulu değil ya da istemci kurulamadı."""


class GeminiRateLimit(GeminiError):
    """
    Kota/oran sınırı aşıldı (429). Model değiştirmek işe yaramaz.

    `detail` alanı, Google'ın döndüğü ayrıntıdan çıkarılan okunur bir açıklama
    tutar: hangi kota (dakikalık istek / dakikalık token / günlük istek) dolmuş
    ve ne kadar sonra tekrar denenebilir. Bu bilgi olmadan "kota doldu" mesajı
    hiçbir işe yaramıyor.
    """

    def __init__(self, message, detail=""):
        super().__init__(message)
        self.detail = detail


class GeminiUnavailable(GeminiError):
    """Servis geçici olarak cevap veremiyor (503, 500, zaman aşımı)."""


class GeminiFatal(GeminiError):
    """Kalıcı hata: geçersiz anahtar, bilinmeyen model, hatalı istek."""


RATE_LIMIT_MARKERS = ("429", "RESOURCE_EXHAUSTED", "quota")
TRANSIENT_MARKERS = (
    "503", "UNAVAILABLE", "high demand", "overloaded",
    "500", "INTERNAL", "504", "DEADLINE_EXCEEDED", "timeout",
)


_QUOTA_LABELS = (
    ("per_day", "günlük istek kotası"),
    ("PerDay", "günlük istek kotası"),
    ("input_token_count", "dakikalık token kotası"),
    ("InputTokensPerMinute", "dakikalık token kotası"),
    ("TokensPerMinute", "dakikalık token kotası"),
    ("per_minute", "dakikalık istek kotası"),
    ("PerMinute", "dakikalık istek kotası"),
)


def describe_quota_error(message):
    """
    429 mesajından okunur bir açıklama çıkarır.

    Google hata gövdesinde hangi kotanın dolduğunu (quotaId / quotaMetric) ve
    ne kadar beklenmesi gerektiğini (retryDelay) döndürüyor; mesajın tamamı
    kullanıcıya gösterilemeyecek kadar uzun ve teknik olduğu için özetliyoruz.
    """
    parts = []

    quota_id = ""
    match = re.search(r'"quotaId"\s*:\s*"([^"]+)"', message)
    if match:
        quota_id = match.group(1)
    else:
        match = re.search(r'"quotaMetric"\s*:\s*"([^"]+)"', message)
        if match:
            quota_id = match.group(1)

    if quota_id:
        label = next((text for key, text in _QUOTA_LABELS if key in quota_id), "")
        parts.append(f"{label} ({quota_id})" if label else quota_id)

    match = re.search(r'"retryDelay"\s*:\s*"([^"]+)"', message)
    if match:
        parts.append(f"önerilen bekleme: {match.group(1)}")

    match = re.search(r'"quotaValue"\s*:\s*"?(\d+)"?', message)
    if match:
        parts.append(f"sınır: {match.group(1)}")

    return " | ".join(parts)


def classify_error(message):
    """Hata mesajını 'rate_limit' / 'transient' / 'fatal' olarak sınıflar."""
    if any(marker in message for marker in RATE_LIMIT_MARKERS):
        return "rate_limit"
    if any(marker in message for marker in TRANSIENT_MARKERS):
        return "transient"
    return "fatal"


# ---------------------------------------------------------------------------
# İstemci
# ---------------------------------------------------------------------------

def get_client():
    """
    Gemini istemcisini oluşturur; oluşturulamazsa None döner.

    SDK import'u bilerek fonksiyon içinde: paket kurulu değilse projenin
    tamamı değil, yalnızca Gemini'ye bağlı özellikler devre dışı kalır.
    """
    api_key = getattr(settings, "GEMINI_API_TOKEN", None)
    if not api_key:
        logger.error("GEMINI_API_TOKEN tanımlı değil. .env dosyanıza anahtarınızı ekleyin.")
        return None

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.error("google-genai paketi kurulu değil. Kurmak için: pip install google-genai")
        return None

    try:
        # Çağrılar senkron bir istek içinde yapılıyor: asılı kalan bir çağrı
        # web sunucusunun zaman aşımına takılmasına yol açar.
        return genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=int(settings.GEMINI_TIMEOUT_SECONDS * 1000)
            ),
        )
    except Exception:
        logger.exception("Gemini istemcisi oluşturulamadı.")
        return None


# ---------------------------------------------------------------------------
# İstek aralığı sınırlayıcı
# ---------------------------------------------------------------------------
#
# Gemini'nin ücretsiz katmanında MODEL BAŞINA DAKİKADA 5 istek sınırı var.
# Birkaç istek atan bir özellik (kelime zenginleştirme gibi) istekleri arka
# arkaya gönderirse bu sınıra anında çarpıyor ve 429 alıyor.
#
# Buradaki sınırlayıcı iki istek arasına asgari bir boşluk koyuyor. Tek istek
# atan özellikler (metin değerlendirme) hiç beklemez; art arda istek atanlar
# kendiliğinden yavaşlar. Süre 0 verilirse sınırlayıcı tamamen kapanır.

_throttle_lock = threading.Lock()
_last_request_at = 0.0


def _throttle():
    """Ayarlanan asgari aralığı sağlamak için gerekiyorsa bekler."""
    global _last_request_at

    try:
        min_interval = float(getattr(settings, "GEMINI_MIN_SECONDS_BETWEEN_REQUESTS", 0) or 0)
    except (TypeError, ValueError):
        min_interval = 0.0

    if min_interval <= 0:
        return

    with _throttle_lock:
        wait = (_last_request_at + min_interval) - time.monotonic()
        if wait > 0:
            logger.info("Kota sınırına takılmamak için %.1f sn bekleniyor.", wait)
            time.sleep(wait)
        _last_request_at = time.monotonic()


def models_to_try():
    """Sırayla denenecek modeller: önce ayarlardaki, sonra yedekler."""
    models = [settings.GEMINI_MODEL]
    for fallback in getattr(settings, "GEMINI_FALLBACK_MODELS", []):
        if fallback and fallback not in models:
            models.append(fallback)
    return models


# ---------------------------------------------------------------------------
# Üretim
# ---------------------------------------------------------------------------

def _build_config(response_schema, temperature, timeout=None):
    """İstek yapılandırmasını hazırlar; şema verilirse JSON çıktısı zorlanır."""
    from google.genai import types

    kwargs = {}
    if temperature is not None:
        kwargs["temperature"] = temperature

    # İstemcideki genel zaman aşımını bu istek için geçersiz kıl.
    # Kelime zenginleştirme gibi büyük çıktı üreten istekler, metin
    # değerlendirmeye göre çok daha uzun sürüyor.
    if timeout is not None:
        kwargs["http_options"] = types.HttpOptions(timeout=int(float(timeout) * 1000))

    if response_schema is not None:
        # response_mime_type + response_schema ikilisi, modelin şemaya UYAN
        # geçerli bir JSON döndürmesini garanti eder. Böylece "bazen markdown
        # kod bloğu içinde JSON döndürdü" gibi durumlarla uğraşmak gerekmez.
        kwargs["response_mime_type"] = "application/json"
        kwargs["response_schema"] = response_schema

    return types.GenerateContentConfig(**kwargs) if kwargs else None


def generate(prompt, *, response_schema=None, temperature=None, max_retries=None,
             timeout=None, on_event=None, bekle=True):
    """
    Gemini'ye bir istek atar ve cevap nesnesini döner.

    Geçici hatalarda önce aynı model tekrar denenir, sonra yedek modellere
    geçilir. Sonunda da olmazsa uygun bir GeminiError fırlatılır:

        GeminiUnconfigured - anahtar/paket/istemci sorunu
        GeminiRateLimit    - kota aşımı
        GeminiUnavailable  - servis geçici olarak cevap veremiyor
        GeminiFatal        - kalıcı hata

    `response_schema` verilirse (pydantic modeli ya da types.Schema) cevap
    şemaya uygun JSON olur ve `response.parsed` üzerinden okunabilir.

    `max_retries` ayardaki değeri geçersiz kılar. Art arda birden çok istek
    atan özellikler 0 vererek kota tüketimini yarıya indirebilir.

    `timeout` (saniye) bu istek için zaman aşımını değiştirir. Büyük çıktı
    üreten istekler varsayılan süreye sığmayıp 504 alabiliyor.

    `bekle=False` istek aralığı sınırlayıcısını (_throttle) atlar. Kullanıcının
    beklediği istekler (metin değerlendirme) için: onların sınırı
    texts/limits.py'deki dakikalık sayaç; uyumak yerine "yoğun" denir.

    `on_event(ad, bilgi)` verilirse her deneme, hata ve başarıda çağrılır.
    Kullanıcıya gösterilen ilerleme çubuğu bunu kullanıyor: ikinci istek
    gittiğinde çubuk gerçekten ilerlesin diye.
    """
    def notify(name, **info):
        if on_event is None:
            return
        try:
            on_event(name, info)
        except Exception:
            # İlerleme bildirimi asıl işi bozmamalı
            logger.debug("İlerleme bildirimi başarısız.", exc_info=True)
    client = get_client()
    if client is None:
        raise GeminiUnconfigured("Gemini istemcisi oluşturulamadı.")

    config = _build_config(response_schema, temperature, timeout)

    # Denemeler boyunca görülen EN AÇIKLAYICI hatayı saklıyoruz.
    # Yedek model listesinde ölü bir model varsa (örn. artık kapatılmış bir
    # sürüm 404 dönerse) bu "kalıcı hata" sayılıp asıl sorunu -- servisin
    # yoğun olmasını -- gizliyordu. Geçici hata, kalıcı hatayı bastırır.
    seen_transient = False
    last_kind = "fatal"
    last_message = ""

    models = models_to_try()

    for model_index, model in enumerate(models):
        # Yalnızca ilk (asıl) model tekrar denenir; yedeklerde tek deneme
        # yapılır, yoksa kullanıcı çok uzun süre bekler.
        retries = settings.GEMINI_MAX_RETRIES if max_retries is None else max_retries
        attempts = 1 + retries if model_index == 0 else 1

        for attempt in range(attempts):
            notify(
                "attempt",
                model=model,
                model_index=model_index,
                model_count=len(models),
                attempt=attempt + 1,
                attempts=attempts,
            )

            if bekle:
                _throttle()

            try:
                if config is not None:
                    response = client.models.generate_content(
                        model=model, contents=prompt, config=config
                    )
                else:
                    response = client.models.generate_content(model=model, contents=prompt)
            except Exception as exc:
                last_message = str(exc)
                last_kind = classify_error(last_message)
                notify("error", model=model, kind=last_kind, message=last_message)

                if last_kind == "transient":
                    seen_transient = True
                elif last_kind == "fatal":
                    # Ayarlardaki bir model geçersizse bunu net biçimde söyle
                    logger.error(
                        "Gemini modeli kullanılamıyor (model=%s). Ayarlarınızdaki "
                        "GEMINI_MODEL / GEMINI_FALLBACK_MODELS değerlerini kontrol edin. "
                        "Kullanılabilir modeller: python manage.py list_gemini_models",
                        model,
                    )
                logger.warning(
                    "Gemini isteği başarısız (model=%s, deneme=%s/%s, tür=%s): %s",
                    model, attempt + 1, attempts, last_kind, last_message,
                )

                if last_kind == "transient" and attempt + 1 < attempts:
                    time.sleep(settings.GEMINI_RETRY_BACKOFF_SECONDS * (attempt + 1))
                    continue

                # Kota hatasında model değiştirmek işe yaramaz (kota hesaba bağlı)
                if last_kind == "rate_limit":
                    detail = describe_quota_error(last_message)
                    logger.error(
                        "Gemini kota hatası (model=%s). Ayrıntı: %s | Tam mesaj: %s",
                        model, detail or "belirtilmemiş", last_message,
                    )
                    raise GeminiRateLimit(last_message, detail=detail) from exc
                break

            if model_index > 0:
                logger.info("Gemini cevabı yedek modelden alındı: %s", model)

            notify("success", model=model, model_index=model_index)
            return response

    if seen_transient or last_kind == "transient":
        raise GeminiUnavailable(last_message)
    raise GeminiFatal(last_message)
