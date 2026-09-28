"""
"Yazın değerlendirildi" bildirimi (rapor 9.1 ve 10).

Yalnızca ARKA PLANDA (`yazilari_yeniden_dene` komutuyla) değerlendirilen
yazılar için gönderilir. Kullanıcı sonucu ekranda beklerken bildirim gereksiz.
"""

from django.dispatch import receiver
from django.urls import reverse

from texts.sinyaller import yazi_degerlendirildi

from . import gonder

BASLIK = "Yazın değerlendirildi"
GOVDE = "Geri bildirimin hazır. Neleri iyi yaptığına bir bak!"


@receiver(yazi_degerlendirildi, dispatch_uid="bildirimler.yazi_degerlendirildi")
def yazi_degerlendirildi_bildir(sender, yazi, arka_planda=False, **kwargs):
    if not arka_planda:
        return
    gonder.kullaniciya(yazi.owner, BASLIK, GOVDE,
                       reverse("review_text", args=[yazi.pk]))
