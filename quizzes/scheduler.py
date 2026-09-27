"""
Aralıklı tekrar zamanlayıcısı.

Bu dosya tek bir soruya cevap verilmesiyle "bu kartı bir daha ne zaman
sor" arasındaki bütün hesabı yapar. Veritabanına dokunmaz, Django'ya
bağlı değildir, tamamı saf fonksiyondur — bu yüzden test edilmesi kolay
ve istenirse başka bir yere taşınabilir.

NEDEN BİR ZAMANLAYICI VAR
--------------------------
Eski quiz sisteminde bir kelimenin ne zaman tekrar sorulacağına kimse
karar vermiyordu. Kullanıcı "Çoktan Seçmeli, 10 soru" diyor, rastgele 10
kelime geliyordu. Hafıza araştırmasında tekrar ZAMANLAMASI, soru tipinden
de soru sayısından da daha büyük bir etken: bir kelimeyi unutmaya yakın
anda hatırlamak, aynı kelimeyi beş kez arka arkaya görmekten kalıcıdır
(aralık etkisi). Zamanlayıcı bu "unutmaya yakın an"ı tahmin eder.

HANGİ MODEL
-----------
FSRS (Free Spaced Repetition Scheduler), DSR modeli. Üç değişken:

  D — zorluk (difficulty, 1-10). Kartın kendi doğasından gelen zorluk.
  S — kararlılık (stability, gün). Hatırlama olasılığı %90'a düşene kadar
      geçen süre. Öğrendikçe büyür.
  R — hatırlanabilirlik (retrievability, 0-1). Şu anda sorulsa hatırlama
      olasılığı. Zaman geçtikçe düşer.

Burada FSRS-4.5 denklemleri ve onun varsayılan 17 parametresi kullanılıyor.
FSRS-6 (21 parametre) daha yeni ama kişiye özel optimizasyon olmadan
kazancı küçük; LearnVocab'da henüz optimizasyona yetecek tekrar geçmişi
yok. Yükseltmek gerekirse değişmesi gereken yer üç şey: PARAMS listesi,
`hatirlanabilirlik()` ve `aralik()`. Denklemlerin geri kalanı aynı.

PUANLAMA — BU PROJEYE ÖZGÜ KISIM
--------------------------------
FSRS kullanıcının kendi verdiği 1-4 arası nota (Again/Hard/Good/Easy)
göre çalışır. Anki'de kullanıcı bu düğmeye kendisi basar. Burada BASMIYOR:
sorular otomatik değerlendiriliyor. Notu biz üretiyoruz — doğruluk, cevap
süresi ve ipucu kullanımından. Bkz. `not_uret()`.

Kendi kendini notlandırmanın kaldırılmasının sebebi yalnızca kolaylık
değil: insan kendi bilgisini sistematik olarak fazla tahmin eder
(bilme yanılsaması). "Biliyordum" düğmesi olan bir sistemde kullanıcı
zor kartları kolay işaretleyip aralıkları şişirir ve sonra unutur.
Cevabın kendisi yalan söyleyemez.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


# ----------------------------------------------------------------------
# Parametreler
# ----------------------------------------------------------------------

# FSRS-4.5 varsayılanları (w0 … w16).
# Bunlar milyonlarca tekrar üzerinde eğitilmiş genel değerlerdir; kişiye
# özel eğitim için yeterli veri biriktiğinde yeniden hesaplanabilir.
PARAMS = (
    0.40, 0.60, 2.40, 5.80,   # w0-w3  : ilk kararlılık (nota göre)
    4.93, 0.94,               # w4-w5  : ilk zorluk
    0.86, 0.01,               # w6-w7  : zorluk güncellemesi + ortalamaya dönüş
    1.49, 0.14, 0.94,         # w8-w10 : başarılı tekrarda kararlılık artışı
    2.18, 0.05, 0.34, 1.26,   # w11-w14: unutmada kararlılık düşüşü
    0.29, 2.61,               # w15-w16: "zor" cezası, "kolay" ödülü
)

# Hedef hatırlanabilirlik. Kart bu olasılığa düştüğünde sorulur.
# 0.90 FSRS'in varsayılanı ve iyi bir denge: daha yükseği tekrar sayısını
# hızla artırır, daha düşüğü unutmayı artırır.
VARSAYILAN_HEDEF_R = 0.90

# Aralık sınırları (gün).
EN_KISA_ARALIK = 1
EN_UZUN_ARALIK = 365          # Hazırlık öğrencisinin ufku bir yıl.

# Zorluk sınırları.
EN_DUSUK_ZORLUK = 1.0
EN_YUKSEK_ZORLUK = 10.0

# Kararlılığın altına düşemeyeceği taban (gün).
EN_DUSUK_KARARLILIK = 0.1

# Aralığa eklenen rastgelelik oranı. Aynı gün eklenen kartların sonsuza
# kadar aynı günde toplanmasını engeller — yoksa kullanıcı bir gün 5,
# ertesi gün 120 kartla karşılaşır.
SACILMA = 0.05


# ----------------------------------------------------------------------
# Notlar
# ----------------------------------------------------------------------

YENIDEN = 1   # Again — bilemedi
ZOR = 2       # Hard  — bildi ama zorlandı
IYI = 3       # Good  — normal
KOLAY = 4     # Easy  — anında ve kesin

NOT_ADLARI = {
    YENIDEN: "bilemedi",
    ZOR: "zorlandı",
    IYI: "bildi",
    KOLAY: "kolay bildi",
}


@dataclass
class Hafiza:
    """Bir kartın hafıza durumu. Modeldeki üç alanın saf karşılığı."""

    kararlilik: float       # S, gün
    zorluk: float           # D, 1-10

    def kopya(self) -> "Hafiza":
        return Hafiza(self.kararlilik, self.zorluk)


# ----------------------------------------------------------------------
# Temel denklemler
# ----------------------------------------------------------------------

def hatirlanabilirlik(gecen_gun: float, kararlilik: float) -> float:
    """
    R(t,S) — t gün geçtikten sonra hatırlama olasılığı.

    FSRS-4.5: R = (1 + t / (9S))^-1
    Tanım gereği R(S, S) = 0.9 — yani "kararlılık", hatırlama olasılığının
    %90'a düştüğü süredir.
    """
    if kararlilik <= 0:
        return 0.0
    gecen_gun = max(0.0, gecen_gun)
    return (1.0 + gecen_gun / (9.0 * kararlilik)) ** -1.0


def aralik(kararlilik: float, hedef_r: float = VARSAYILAN_HEDEF_R) -> float:
    """
    I(r,S) — hatırlanabilirlik hedef_r'ye düşene kadar geçecek gün.

    FSRS-4.5: I = 9S (1/r - 1)
    hedef_r = 0.9 iken I = S çıkar.
    """
    hedef_r = min(max(hedef_r, 0.70), 0.99)
    return 9.0 * kararlilik * (1.0 / hedef_r - 1.0)


def _ilk_kararlilik(nota: int) -> float:
    return max(PARAMS[nota - 1], EN_DUSUK_KARARLILIK)


def _ilk_zorluk(nota: int) -> float:
    """D0(G) = w4 - (G-3)·w5"""
    d = PARAMS[4] - (nota - 3) * PARAMS[5]
    return _zorluk_sinirla(d)


def _zorluk_sinirla(d: float) -> float:
    return min(max(d, EN_DUSUK_ZORLUK), EN_YUKSEK_ZORLUK)


def _sonraki_zorluk(zorluk: float, nota: int) -> float:
    """
    D' = w7·D0(3) + (1-w7)·(D - w6·(G-3))

    İkinci terim asıl güncelleme: yanlış cevap zorluğu artırır, kolay
    cevap düşürür. Birinci terim "ortalamaya dönüş": zorluk sonsuza kadar
    tek yönde kaymasın diye her tekrarda bir miktar başlangıç değerine
    çekilir. w7 = 0.01, yani çekim çok hafif.
    """
    yeni = zorluk - PARAMS[6] * (nota - 3)
    yeni = PARAMS[7] * _ilk_zorluk(IYI) + (1 - PARAMS[7]) * yeni
    return _zorluk_sinirla(yeni)


def _basarili_kararlilik(zorluk: float, kararlilik: float,
                         r: float, nota: int) -> float:
    """
    S'(D,S,R,G) — doğru cevaptan sonraki kararlılık.

    Üç şey aynı anda söylenir:
      (11 - D)      zor kart daha az kazanır
      S^-w9         zaten kararlı olan kart daha az kazanır (doygunluk)
      e^(w10(1-R))  hatırlanabilirlik DÜŞÜKKEN hatırlamak daha çok kazandırır

    Üçüncüsü "istenen zorluk" ilkesinin denklemdeki karşılığı: zar zor
    hatırlanan bir kelime, kolayca hatırlanandan daha fazla iz bırakır.
    Sistemin kartları erken değil, tam zamanında sormasının sebebi bu.
    """
    ceza = PARAMS[15] if nota == ZOR else 1.0
    odul = PARAMS[16] if nota == KOLAY else 1.0

    artis = (
        math.exp(PARAMS[8])
        * (11.0 - zorluk)
        * (kararlilik ** -PARAMS[9])
        * (math.exp(PARAMS[10] * (1.0 - r)) - 1.0)
        * ceza
        * odul
    ) + 1.0

    return max(kararlilik * artis, EN_DUSUK_KARARLILIK)


def _basarisiz_kararlilik(zorluk: float, kararlilik: float, r: float) -> float:
    """
    S'f(D,S,R) — unutulduktan sonraki kararlılık.

    Sıfırlanmaz. Bir kez öğrenilmiş kelime unutulsa bile hiç görülmemiş
    kelimeden ileridedir (tasarruf etkisi); denklem bunu korur. Ama asla
    eski kararlılığın üstüne çıkamaz — alttaki min() bunun için.
    """
    dusus = (
        PARAMS[11]
        * (zorluk ** -PARAMS[12])
        * (((kararlilik + 1.0) ** PARAMS[13]) - 1.0)
        * math.exp(PARAMS[14] * (1.0 - r))
    )
    return max(min(dusus, kararlilik), EN_DUSUK_KARARLILIK)


# ----------------------------------------------------------------------
# Dışarıya açık arayüz
# ----------------------------------------------------------------------

def ilk_hafiza(nota: int) -> Hafiza:
    """Kart ilk kez cevaplandığında oluşan hafıza durumu."""
    return Hafiza(kararlilik=_ilk_kararlilik(nota), zorluk=_ilk_zorluk(nota))


def guncelle(hafiza: Hafiza | None, nota: int, gecen_gun: float) -> Hafiza:
    """
    Bir cevaptan sonraki yeni hafıza durumu.

    hafiza None ise kart ilk kez cevaplanıyordur.
    gecen_gun, kartın en son sorulmasından bu yana geçen gün sayısıdır.
    """
    if hafiza is None:
        return ilk_hafiza(nota)

    r = hatirlanabilirlik(gecen_gun, hafiza.kararlilik)
    yeni_zorluk = _sonraki_zorluk(hafiza.zorluk, nota)

    if nota == YENIDEN:
        yeni_kararlilik = _basarisiz_kararlilik(hafiza.zorluk, hafiza.kararlilik, r)
    else:
        yeni_kararlilik = _basarili_kararlilik(
            hafiza.zorluk, hafiza.kararlilik, r, nota
        )

    return Hafiza(kararlilik=yeni_kararlilik, zorluk=yeni_zorluk)


def sonraki_aralik(hafiza: Hafiza, hedef_r: float = VARSAYILAN_HEDEF_R,
                   rng=None) -> int:
    """
    Kaç gün sonra sorulacak (tam gün).

    Sonuca ±%5 rastgelelik ekleniyor. Bu kozmetik bir detay değil: aynı
    gün eklenen kartlar aynı aralıkları paylaştığı için serpiştirme
    olmadan sonsuza kadar aynı güne yığılırlar.
    """
    ham = aralik(hafiza.kararlilik, hedef_r)
    ham = min(max(ham, EN_KISA_ARALIK), EN_UZUN_ARALIK)

    rng = rng or random
    sapma = ham * SACILMA
    ham = rng.uniform(ham - sapma, ham + sapma)

    return int(min(max(round(ham), EN_KISA_ARALIK), EN_UZUN_ARALIK))


# ----------------------------------------------------------------------
# Otomatik değerlendirmeden not üretme
# ----------------------------------------------------------------------

# Bir cevabın "hızlı" sayılması için beklenen sürenin bu oranının altında
# kalması gerekir; "yavaş" sayılması için üstüne çıkması.
HIZLI_ESIK = 0.5
YAVAS_ESIK = 2.0


def not_uret(dogru: bool, saniye: float | None, beklenen_saniye: float,
             ipucu_kullanildi: bool = False, uretim_mi: bool = False) -> int:
    """
    Otomatik değerlendirilen bir cevaptan FSRS notu (1-4) üretir.

    Kural basit tutuldu çünkü karmaşık bir eşleme kalibre edilemez:

      yanlış                                   -> YENIDEN
      doğru ama ipuçlu ya da yavaş             -> ZOR
      doğru, hızlı ve üretim sorusu            -> KOLAY
      diğer doğrular                           -> İYİ

    "Üretim sorusu" ayrımı önemli: dört şıktan birini hızlı işaretlemek
    kelimeyi bildiğini göstermez, eleme de aynı hızı verir. Kelimeyi
    kendi yazıp hızlı yazmak ise gerçekten akıcı bilgidir. KOLAY notu
    aralığı w16 = 2.61 katına çıkardığı için yalnızca gerçekten hak
    edildiğinde verilmeli.
    """
    if not dogru:
        return YENIDEN

    if ipucu_kullanildi:
        return ZOR

    if saniye is None or beklenen_saniye <= 0:
        return IYI

    oran = saniye / beklenen_saniye

    if oran >= YAVAS_ESIK:
        return ZOR
    if uretim_mi and oran <= HIZLI_ESIK:
        return KOLAY
    return IYI


def yuksek_guvenli_hata(dogru: bool, saniye: float | None,
                        beklenen_saniye: float) -> bool:
    """
    Bu cevap "yüksek güvenli hata" mı?

    Hızlı verilen yanlış cevap, kullanıcının tereddüt etmediği anlamına
    gelir: yanlış olduğunu bilmiyordu, doğru sandığı bir şey vardı.
    Araştırmada bu hataların düzeltmesi en iyi akılda kalan düzeltmedir
    (hypercorrection etkisi) — ama düzeltme yaklaşık BİR HAFTA sonra
    çözülür ve eski yanlış geri gelir; tekrar sorulmazsa.

    Bu yüzden böyle bir hata iki şey tetikler (bkz. session.py):
      1. aynı oturumda sonunda tekrar sorulur,
      2. bir hafta içinde mutlaka tekrar sorulması için işaretlenir.

    Tereddütlü yanlış (yavaş + yanlış) bu muameleyi görmez: orada
    kullanıcı zaten bilmediğini biliyor, sürpriz yok.
    """
    if dogru or saniye is None or beklenen_saniye <= 0:
        return False
    return (saniye / beklenen_saniye) <= HIZLI_ESIK
