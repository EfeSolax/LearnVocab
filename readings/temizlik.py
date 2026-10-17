"""
Kendi metinlerimde okumayı bölen kalıntıları ayıklar (Efe, 17 Ekim).

Kitaplardan (PDF ya da kopyala-yapıştır) gelen metinde iki tür gürültü olur:
  1. Bağlantılar: "https://…", "www.…", e-posta adresleri; kısa altbilgi
     satırlarında çıplak alan adları ("Planet eBook.com").
  2. Her sayfada tekrar eden üst/alt bilgiler: kitap adı, yazar adı, sayfa
     numarasıyla birlikte ("12 ANIMAL FARM", "George Orwell").

Kural sade tutulur ve metnin kendisine dokunmamaya çalışır:
  - Bağlantı paragrafın içinden silinir; geriye harf kalmazsa paragraf düşer.
  - Tekrar eden satır: en çok 10 kelimelik, cümle gibi bitmeyen ve
    (sayılar atıldıktan sonra) metinde en az 3 kez geçen paragraf. Bölüm
    başlıkları ("Chapter 2", "CHAPTER II") korunur.
Üst/alt bilgi atılınca ikiye bölünmüş cümle ("…was already" + "snoring.")
yeniden birleşir. PDF'te sayfa bilgisi de vardır; orada sayfanın başında/sonunda en az 3
sayfada tekrar eden bloklar ayrıca atılır (readings/pdf.py).

Yükleme sırasında ve okurken (eski metinler de temizlensin diye) çalışır;
diskteki metin değiştirilmez.
"""

import re
from collections import Counter

# Her zaman bağlantı olanlar: adres, www, e-posta.
_BAGLANTI = re.compile(r"(?:https?://|www\.)[^\s<>\"“”()]+[^\s<>\"“”().,;:!?]|\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b", re.IGNORECASE)
# Çıplak alan adı: yalnızca kısa (altbilgi gibi) paragraflarda silinir;
# cümle içindeki "Amazon.com" gibi kullanımlara dokunulmaz.
_ALAN_ADI = re.compile(r"\b[\w-]+(?:\.[\w-]+)*\.(?:com|org|net|edu|gov|io|co|info|uk|tr)(?:/[^\s]*)?\b", re.IGNORECASE)
KISA_PARAGRAF = 12          # kelime

TEKRAR_ESIGI = 3
TEKRAR_EN_COK_KELIME = 10
_CUMLE_SONU = re.compile(r"[.?!…\"”’:;]$")
_BOLUM_BASLIGI = re.compile(r"^(chapter|part|book|section|bölüm|kapitel|teil)\b", re.IGNORECASE)


def baglantilari_sil(p):
    """Paragraftan bağlantıları siler; geriye okunacak bir şey kalmazsa "" döner."""
    yeni = _BAGLANTI.sub("", p)
    if len(yeni.split()) <= KISA_PARAGRAF:
        yeni = _ALAN_ADI.sub("", yeni)
    if yeni == p:
        return p
    # Boş kalan parantez: "(see )", "[ ]"
    yeni = re.sub(r"[(\[<]\s*(?:see|bkz\.?|at|from|via)?\s*[)\]>]", "", yeni, flags=re.IGNORECASE)
    yeni = re.sub(r"\s+([,.;:!?])", r"\1", yeni)
    yeni = re.sub(r"\s{2,}", " ", yeni).strip(" -–—|·:,")
    # Kısa satır bağlantı için yazılmışsa ("Free eBooks at …") kırıntısı da gider.
    if len(p.split()) <= KISA_PARAGRAF and len(yeni.split()) <= 4:
        return ""
    return yeni if re.search(r"[A-Za-zÀ-ɏ]{2}", yeni) else ""


def anahtar(p):
    """Tekrar karşılaştırması için: küçük harf, sayılar ve işaretler atılmış."""
    return " ".join(re.sub(r"[^a-zà-ɏ]+", " ", p.lower()).split())


def tekrar_eden_mi_aday(p):
    """Üst/alt bilgi olabilecek kısa satır mı? (bölüm başlıkları değil)"""
    a = anahtar(p)
    return (len(a) >= 4 and len(p.split()) <= TEKRAR_EN_COK_KELIME
            and not _CUMLE_SONU.search(p.strip()) and not _BOLUM_BASLIGI.match(a))


def paragraflari_temizle(paragraflar):
    """
    Bağlantıları siler, metinde en az 3 kez tekrar eden kısa üst/alt bilgileri
    atar. Atılan satırın iki yanında ikiye bölünmüş cümle birleşir: önceki harf
    ya da virgülle bitip sonraki küçük harfle başlıyorsa ("…where Mrs. Jones
    was already" + [üst bilgi] + "snoring.").
    """
    temiz = [baglantilari_sil(p) for p in paragraflar]
    sayac = Counter(anahtar(p) for p in temiz if p and tekrar_eden_mi_aday(p))
    sonuc, atildi = [], False
    for p in temiz:
        if not p or (tekrar_eden_mi_aday(p) and sayac[anahtar(p)] >= TEKRAR_ESIGI):
            atildi = True
            continue
        if atildi and sonuc and re.search(r"[A-Za-z,]$", sonuc[-1]) and re.match(r"[a-z]", p):
            sonuc[-1] = sonuc[-1] + " " + p
        else:
            sonuc.append(p)
        atildi = False
    return sonuc
