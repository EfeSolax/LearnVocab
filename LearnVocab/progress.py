"""
Uzun süren işler için ilerleme takibi.

Kelime zenginleştirme ve metin değerlendirme, Gemini'yi beklerken yarım dakikayı
aşabiliyor. Kullanıcının boş ekrana bakmaması için iş arka planda çalışıyor,
tarayıcı da ilerlemeyi periyodik olarak soruyor.

İlerleme neden cache'te?
------------------------
İşi yürüten iş parçacığı ile ilerlemeyi soran istek AYNI SÜREÇTE olmayabilir:
canlı sunucuda (Passenger) birden çok süreç var ve istekler aralarında
dağıtılıyor. Bu yüzden ilerleme, süreçler arasında paylaşılan dosya tabanlı
cache'te tutuluyor (bkz. settings.CACHES).

Durumlar:
    running   - iş devam ediyor
    done      - başarıyla bitti, `result` dolu
    failed    - hata ile bitti, `message` sebebi anlatıyor
"""

import logging
import time
import uuid

from django.core.cache import cache

logger = logging.getLogger(__name__)

# İş kaydının cache'te kalma süresi. Uzun tutmanın anlamı yok; tarayıcı
# saniyede bir soruyor ve iş bittikten hemen sonra sonucu alıyor.
JOB_TTL_SECONDS = 30 * 60

STATE_RUNNING = "running"
STATE_DONE = "done"
STATE_FAILED = "failed"


def _key(job_id):
    return f"job:{job_id}"


def create(owner_id, message="Hazırlanıyor...", percent=1):
    """Yeni bir iş kaydı oluşturur ve kimliğini döner."""
    job_id = uuid.uuid4().hex
    write(
        job_id,
        {
            "owner_id": owner_id,
            "state": STATE_RUNNING,
            "percent": percent,
            "message": message,
            "result": None,
            "baslangic": time.time(),
        },
    )
    return job_id


def write(job_id, data):
    cache.set(_key(job_id), data, JOB_TTL_SECONDS)


def read(job_id):
    """İş kaydını döner; yoksa None."""
    return cache.get(_key(job_id))


def delete(job_id):
    cache.delete(_key(job_id))


def update(job_id, *, percent=None, message=None, state=None, result=None):
    """
    İş kaydını günceller.

    Yüzde ASLA geri gitmez: farklı adımlar farklı tahminler üretebiliyor ve
    çubuğun geri sarması kullanıcıya bir şeylerin bozulduğunu düşündürüyor.
    """
    job = read(job_id)
    if job is None:
        return None

    if percent is not None:
        job["percent"] = max(job.get("percent", 0), min(100, int(percent)))
    if message is not None:
        job["message"] = message
    if state is not None:
        job["state"] = state
    if result is not None:
        job["result"] = result

    write(job_id, job)
    return job


def finish(job_id, result, message="Tamamlandı."):
    return update(job_id, percent=100, message=message, state=STATE_DONE, result=result)


def fail(job_id, message):
    return update(job_id, percent=100, message=message, state=STATE_FAILED)


class Reporter:
    """
    Bir işin belirli bir aralığında ilerleme bildiren yardımcı.

    Adımlar iç içe olduğu için (parti -> grup -> model denemesi) her katman
    kendi payını bilmeli. `slice(başlangıç, bitiş)` ile alt aralık açılır:

        reporter = Reporter(job_id, 5, 95)
        grup = reporter.slice_for(index, toplam)   # bu grubun payı
        grup.set(0.5, "yarısı bitti")
    """

    def __init__(self, job_id, start=0, end=100):
        self.job_id = job_id
        self.start = float(start)
        self.end = float(end)

    def set(self, ratio, message=None):
        """ratio: 0.0 - 1.0 arası, bu aralıktaki konum."""
        ratio = max(0.0, min(1.0, float(ratio)))
        percent = self.start + (self.end - self.start) * ratio
        update(self.job_id, percent=round(percent), message=message)

    def message(self, text):
        update(self.job_id, message=text)

    def slice_for(self, index, total):
        """Toplam `total` adımın `index`. adımına düşen alt aralığı döner."""
        total = max(1, total)
        span = (self.end - self.start) / total
        return Reporter(self.job_id, self.start + span * index, self.start + span * (index + 1))
