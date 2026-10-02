"""
"Yazın değerlendirildi" bildirimi (rapor 9.1 ve 10).

Yalnızca ARKA PLANDA (`yazilari_yeniden_dene` komutuyla) değerlendirilen
yazılar için gönderilir. Kullanıcı sonucu ekranda beklerken bildirim gereksiz.
"""

from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from LearnVocab.diller import kullanici_dilinde

from texts.sinyaller import yazi_degerlendirildi

from . import gonder

BASLIK = _("Yazın değerlendirildi")
GOVDE = _("Geri bildirimin hazır. Neleri iyi yaptığına bir bak!")


@receiver(yazi_degerlendirildi, dispatch_uid="bildirimler.yazi_degerlendirildi")
def yazi_degerlendirildi_bildir(sender, yazi, arka_planda=False, **kwargs):
    if not arka_planda:
        return
    with kullanici_dilinde(yazi.owner):   # alıcının arayüz dilinde (rapor 18.22)
        baslik, govde, adres = str(BASLIK), str(GOVDE), reverse("review_text", args=[yazi.pk])
    gonder.kullaniciya(yazi.owner, baslik, govde, adres)
