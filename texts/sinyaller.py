"""
Yazma bölümünün kancaları.

"Yazın değerlendirildi" bildirimi (rapor 9.1 ve 10) uygulama planının 11.
adımında (Bildirimler ve PWA) eklenecek. Bildirimin gönderileceği yer burası:
bir metnin değerlendirmesi tamamlandığında `degerlendirildi()` çağrılır.

11. adımda yapılacak: `yazi_degerlendirildi` sinyaline bir alıcı bağlamak
(ya da bu fonksiyonun içini doldurmak). `arka_planda=True` ise kullanıcı
sonucu beklerken değil, `yazilari_yeniden_dene` komutuyla sonradan
değerlendirildi demektir; bildirim asıl o durumda anlamlıdır.
"""

import logging

from django.dispatch import Signal

logger = logging.getLogger(__name__)

# Gönderen: Text sınıfı. Argümanlar: yazi, arka_planda
yazi_degerlendirildi = Signal()


def degerlendirildi(yazi, arka_planda=False):
    """Bir metnin değerlendirmesi tamamlandı. Bildirim kancası (adım 11)."""
    logger.info("Yazı değerlendirildi (metin=%s, arka planda=%s).", yazi.pk, arka_planda)
    # Alıcı hatası değerlendirmeyi bozmamalı.
    yazi_degerlendirildi.send_robust(sender=type(yazi), yazi=yazi, arka_planda=arka_planda)
