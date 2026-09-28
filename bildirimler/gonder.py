"""
Web Push gönderici.

    from bildirimler import gonder
    gonder.kullaniciya(user, "Başlık", "Gövde", "/adres/")

Kullanıcının bütün cihazlarına gönderir ve kaç cihaza ulaştığını döner.
VAPID anahtarı yoksa hiçbir şey yapmaz (0). Push servisi aboneliğin artık
geçersiz olduğunu söylerse (404/410) abonelik silinir. Hiçbir hata çağırana
taşmaz: bildirim gidemedi diye asıl iş (değerlendirme, komut) bozulmamalı.
"""

import json
import logging

from django.utils import timezone

from . import ayar
from .models import PushAboneligi

logger = logging.getLogger(__name__)

ZAMAN_ASIMI = 10          # saniye
YASAM_SURESI = 12 * 3600  # push servisi cihaz kapalıysa en çok bu kadar saklasın
GECERSIZ_DURUMLAR = (404, 410)


def _webpush():
    # Test ve paketin kurulu olmadığı ortam için geç yükleniyor.
    from pywebpush import WebPushException, webpush
    return webpush, WebPushException


def aboneye(abonelik, baslik, govde, url="/"):
    """Tek aboneliğe gönderir. Başarılıysa True."""
    if not ayar.acik():
        return False
    try:
        webpush, WebPushException = _webpush()
    except ImportError:
        logger.warning("pywebpush kurulu değil; bildirim gönderilmedi.")
        return False

    veri = json.dumps({"baslik": baslik, "govde": govde, "url": url}, ensure_ascii=False)
    try:
        webpush(
            subscription_info=abonelik.bilgi(),
            data=veri,
            vapid_private_key=ayar.ozel_anahtar(),
            vapid_claims={"sub": ayar.iletisim()},
            timeout=ZAMAN_ASIMI,
            ttl=YASAM_SURESI,
        )
    except WebPushException as exc:
        durum = getattr(getattr(exc, "response", None), "status_code", None)
        if durum in GECERSIZ_DURUMLAR:
            logger.info("Geçersiz abonelik silindi (kullanıcı=%s, durum=%s).", abonelik.user_id, durum)
            abonelik.delete()
        else:
            logger.warning("Bildirim gönderilemedi (kullanıcı=%s, durum=%s).", abonelik.user_id, durum)
        return False
    except Exception:
        logger.exception("Bildirim gönderilirken beklenmedik hata (kullanıcı=%s).", abonelik.user_id)
        return False

    abonelik.son_basari = timezone.now()
    abonelik.save(update_fields=["son_basari"])
    return True


def kullaniciya(user, baslik, govde, url="/"):
    """Kullanıcının bütün cihazlarına gönderir; ulaşılan cihaz sayısını döner."""
    if not ayar.acik() or user is None:
        return 0
    return sum(
        1 for abonelik in list(PushAboneligi.objects.filter(user=user))
        if aboneye(abonelik, baslik, govde, url)
    )

