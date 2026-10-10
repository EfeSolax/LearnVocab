"""
Telefonda "metni seç → Paylaş → LearnVocab" (rapor 11, mobil).

Site ana ekrana eklenince (PWA, rapor 10) Android paylaş menüsünde görünür:
manifest'teki share_target paylaşılanı GET /paylas/?metin=…&baslik=…&adres=… ile
buraya gönderir (bildirimler/views.manifest). Google uygulaması, Chrome, WhatsApp,
PDF okuyucu, hangi uygulamadan seçilirse.

  - En çok KISA_IFADE kelimeyse sözlük araması (/sozluk/?q=…; tam eşleşme kelimenin
    kendi sayfasına 301 ile gider).
  - Daha uzunsa "Kendi metinlerim"e yapıştırılmış olarak açılır. Metin adrese
    değil oturuma yazılır (uzun olabilir; adreste ve kayıtlarda kalmasın).
  - İngilizce kelime yoksa Sözlük'ün boş hâli.

Uygulamalar seçilen metne çoğu zaman tırnak ve sayfa adresi ekliyor
('"reshape" https://…'); adresler ve tırnaklar atılır.
"""

import re
from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_safe

KISA_IFADE = 4
OTURUM_ANAHTARI = "paylasilan_metin"
EN_COK = 150_000

_ADRES = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_KELIME = re.compile(r"[A-Za-z][A-Za-z'’\-]*")


def temizle(ham):
    metin = _ADRES.sub(" ", ham or "")
    metin = re.sub(r"[\"“”«»]", " ", metin)
    return re.sub(r"[ \t]+", " ", metin).strip()


@require_safe
def paylas(request):
    metin = temizle(request.GET.get("metin")) or temizle(request.GET.get("baslik"))
    kelimeler = _KELIME.findall(metin)
    if not kelimeler:
        return redirect("sozluk")
    if len(metin.split()) <= KISA_IFADE:
        return redirect(f"{reverse('sozluk')}?{urlencode({'q': ' '.join(kelimeler).lower()})}")
    request.session[OTURUM_ANAHTARI] = metin[:EN_COK]
    return redirect(f"{reverse('readings_add')}?tur=yapistir")
