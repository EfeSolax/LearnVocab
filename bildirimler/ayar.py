"""
Bildirim ayarları (rapor 10).

VAPID anahtarları `.env`'den gelir (`manage.py vapid_anahtari_uret`). Anahtar
yoksa bildirimler bütünüyle KAPALIDIR: izin kartı gösterilmez, abonelik uçları
404 döner, gönderim sessizce atlanır. Site bundan etkilenmez.
"""

from django.conf import settings


def acik():
    """Web Push kullanılabilir mi (iki anahtar da tanımlı mı)?"""
    return bool(genel_anahtar() and ozel_anahtar())


def genel_anahtar():
    return getattr(settings, "VAPID_PUBLIC_KEY", "") or ""


def ozel_anahtar():
    return getattr(settings, "VAPID_PRIVATE_KEY", "") or ""


def iletisim():
    """VAPID 'sub' iddiası: push servisi sorun olursa bu adrese yazar."""
    eposta = (getattr(settings, "VAPID_ADMIN_EMAIL", "")
              or getattr(settings, "DEFAULT_FROM_EMAIL", "")
              or "admin@learnvocab.com.tr")
    return eposta if eposta.startswith("mailto:") else f"mailto:{eposta}"
