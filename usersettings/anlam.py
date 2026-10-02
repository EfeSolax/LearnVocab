"""
"Türkçe anlamlar" ayarı (rapor 18.22). Arayüz dilinden bağımsızdır; varsayılan açık.

Kapalıysa Türkçe anlam hiçbir yerde gösterilmez ve sorulmaz; yerine İngilizce açıklama
(Meaning.definition) kullanılır:
  - kelime kartı / sayfası, ana sayfa tablosu, günün kelimesi: words.kart.kart_verisi
    Türkçeyi boşaltır, şablonlar "{% firstof meaning_tr definition %}" ile açıklamaya düşer
  - Listem satırları (words.listem), Learn & Pass kartı (learnpass.views),
    okuma baloncuğu (readings.api), öneri kutusu (words.arama): açıklama ya da boş
  - egzersizler: Türkçe anlam soruları yerine açıklama soruları (egzersizler.sorular)
  - diyalog ipucu: açıklama (texts.views)
Misafir için her zaman açık.
"""


def turkce_acik(user):
    if not getattr(user, "is_authenticated", False):
        return True
    onbellek = getattr(user, "_turkce_anlamlar", None)
    if onbellek is None:
        from .models import UserSettings
        deger = UserSettings.objects.filter(user=user).values_list("turkce_anlamlar", flat=True).first()
        onbellek = True if deger is None else bool(deger)
        user._turkce_anlamlar = onbellek      # aynı istekte tek sorgu
    return onbellek


def baglam(request):
    """Context processor: şablonlarda `turkce_acik`."""
    return {"turkce_acik": turkce_acik(request.user)}
