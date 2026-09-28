"""
Diyalogda doğru kelime (ürün raporu 9.2).

Diyaloglar önceden üretilmiş ve denetlenmiş bir havuzdan gelir (D6), canlı
üretilmez. Hedef kelime kullanıcının listesinden seçilir. Kullanıcı boşluğa
İngilizce kelimeyi YAZAR:

  - Çekimli hâl kabul edilir: boşluk "postponed" isterken "postpone" doğru
    sayılır, altında "Bu cümlede: postponed" yazar.
  - Tek harf hatasında (eksik, fazla, yanlış ya da yer değiştirmiş harf)
    "Neredeyse! Doğrusu: postponed".
  - Cevaptan sonra register (resmî/samimi) ve duygu tonu notu gösterilir.
"""

import random
import re
from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

from texts.models import Diyalog, DiyalogCevabi
from words import inflect
from words.models import Register, Sentiment, UserWordLink

DOGRU = "dogru"
NEREDEYSE = "neredeyse"
YANLIS = "yanlis"
BOS = "bos"

# Bu kadar harften kısa cevaplarda tek harf farkı başka bir kelime demek
# (do/go); "neredeyse" denmez.
NEREDEYSE_EN_KISA = 4

_TIRNAK = str.maketrans({"’": "'", "‘": "'"})


def normalle(yazi):
    yazi = (yazi or "").translate(_TIRNAK).strip().lower()
    yazi = re.sub(r"\s+", " ", yazi)
    return yazi.strip(" .,!?;:\"")


def tek_harf_farki_mi(a, b):
    """
    a ile b arasında tam olarak bir düzenleme mi var? (Damerau: ekleme,
    silme, değiştirme ya da yan yana iki harfin yer değiştirmesi)
    """
    if a == b:
        return False
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        farklar = [i for i in range(la) if a[i] != b[i]]
        if len(farklar) == 1:
            return True
        if len(farklar) == 2:
            i, j = farklar
            return j == i + 1 and a[i] == b[j] and a[j] == b[i]
        return False
    # Uzunluk farkı bir: kısa olan, uzundan bir harf silinerek elde edilebilmeli.
    kisa, uzun = (a, b) if la < lb else (b, a)
    for i in range(len(uzun)):
        if uzun[:i] + uzun[i + 1:] == kisa:
            return True
    return False


def kabul_edilen_bicimler(diyalog):
    """Cevap + kelimenin bütün çekimli biçimleri (WordForm ve kural çıktısı)."""
    kelime = diyalog.word
    bicimler = {normalle(diyalog.cevap), normalle(kelime.text)}
    bicimler.update(normalle(y) for y, _t in
                    inflect.forms_for(kelime.text, kelime.pos, kelime.v2Form, kelime.v3Form))
    bicimler.update(normalle(s) for s in kelime.forms.values_list("surface", flat=True))
    bicimler.discard("")
    return bicimler


@dataclass
class Sonuc:
    durum: str
    dogrusu: str
    mesaj: str

    def sozluk(self):
        return {"durum": self.durum, "dogrusu": self.dogrusu, "mesaj": self.mesaj}


def cevabi_degerlendir(diyalog, girdi):
    cevap = diyalog.cevap.strip()
    yazilan = normalle(girdi)
    if not yazilan:
        return Sonuc(BOS, cevap, "Boşluğa bir kelime yaz.")

    hedef = normalle(cevap)
    if yazilan == hedef:
        return Sonuc(DOGRU, cevap, "Doğru!")

    bicimler = kabul_edilen_bicimler(diyalog)
    if yazilan in bicimler:
        return Sonuc(DOGRU, cevap, f"Doğru! Bu cümlede: {cevap}")

    if len(hedef) >= NEREDEYSE_EN_KISA and any(
            tek_harf_farki_mi(yazilan, b) for b in bicimler if len(b) >= NEREDEYSE_EN_KISA):
        return Sonuc(NEREDEYSE, cevap, f"Neredeyse! Doğrusu: {cevap}")

    return Sonuc(YANLIS, cevap, f"Bu sefer olmadı. Doğrusu: {cevap}")


def register_notu(diyalog):
    """Cevaptan sonra gösterilen not: havuzdaki not, yoksa register/ton etiketleri."""
    if diyalog.not_metni:
        return diyalog.not_metni
    parcalar = []
    if diyalog.register and diyalog.register != Register.NEUTRAL:
        parcalar.append(f"Üslup: {Register(diyalog.register).label}")
    if diyalog.sentiment and diyalog.sentiment != Sentiment.NEUTRAL:
        parcalar.append(f"Ton: {Sentiment(diyalog.sentiment).label}")
    return " · ".join(parcalar)


# ---------------------------------------------------------------------------
# Seçim
# ---------------------------------------------------------------------------

# Doğru cevaplanan diyalog bu süre boyunca yeniden sorulmaz.
DOGRU_BEKLEME = timedelta(days=7)


def havuz_bos_mu():
    return not Diyalog.objects.filter(denetlendi=True).exists()


def siradaki(user, haric=None):
    """
    Kullanıcının listesindeki kelimeler için sıradaki diyalog; yoksa None.
    Önce hiç görülmeyenler, sonra yanlış/neredeyse cevaplananlar, en son
    yakın zamanda doğru cevaplanmamış olanlar.
    """
    kelime_idleri = UserWordLink.objects.filter(user=user).values_list("word_id", flat=True)
    adaylar = list(Diyalog.objects.filter(denetlendi=True, word_id__in=kelime_idleri)
                   .exclude(pk=haric).values_list("pk", flat=True))
    if not adaylar:
        return None

    son_cevaplar = {}
    for diyalog_id, sonuc, zaman in (DiyalogCevabi.objects
                                     .filter(user=user, diyalog_id__in=adaylar)
                                     .order_by("olusturuldu")
                                     .values_list("diyalog_id", "sonuc", "olusturuldu")):
        son_cevaplar[diyalog_id] = (sonuc, zaman)

    esik = timezone.now() - DOGRU_BEKLEME
    gorulmemis = [d for d in adaylar if d not in son_cevaplar]
    tekrar = [d for d in adaylar if d in son_cevaplar and son_cevaplar[d][0] != DOGRU]
    eski_dogru = [d for d in adaylar if d in son_cevaplar
                  and son_cevaplar[d][0] == DOGRU and son_cevaplar[d][1] < esik]

    for grup in (gorulmemis, tekrar, eski_dogru):
        if grup:
            return Diyalog.objects.select_related("word").get(pk=random.choice(grup))
    # Hepsi yakın zamanda doğru cevaplandı: yine de birini ver, boş ekran olmasın.
    return Diyalog.objects.select_related("word").get(pk=random.choice(adaylar))


def satirlari_hazirla(diyalog):
    """Şablon için: [{"kisi", "once", "sonra", "bosluk"}] — boşluklu satır ikiye bölünür."""
    satirlar = []
    for satir in diyalog.satirlar:
        metin = satir.get("metin", "")
        if Diyalog.BOSLUK in metin:
            once, _, sonra = metin.partition(Diyalog.BOSLUK)
            satirlar.append({"kisi": satir.get("kisi", ""), "once": once, "sonra": sonra, "bosluk": True})
        else:
            satirlar.append({"kisi": satir.get("kisi", ""), "once": metin, "sonra": "", "bosluk": False})
    return satirlar
