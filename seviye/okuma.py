"""
Seviye testinin 2. kısmı: okuduğunu anlama (rapor 7, veri D4).

3 kısa metin (kolay, orta, zor), her birinde "metni en iyi özetleyen cümle".
Sorular yalnızca DENETLENMİŞ havuzdan gelir. Havuzda üç zorluğun her birinden
en az bir soru yoksa 2. kısım bütünüyle atlanır ve tahmin yalnızca 1.
kısımdan yapılır (havuz yapay zekâ üretimi gerektirdiği için şimdilik boş).
"""

import random

from .models import OkumaSorusu, OkumaZorlugu


def havuz_hazir_mi():
    denetli = OkumaSorusu.objects.filter(denetlendi=True)
    return all(denetli.filter(zorluk=z).exists() for z in OkumaZorlugu.values)


def sorulari_sec(rng=None):
    """
    Kolaydan zora 3 soru: [{"id", "siklar": [metin, …]}] — şıklar karışık.
    Havuz eksikse [] (2. kısım atlanır).
    """
    rng = rng or random.Random()
    secilen = []
    for zorluk in OkumaZorlugu.values:
        idler = list(OkumaSorusu.objects.filter(denetlendi=True, zorluk=zorluk)
                     .values_list("id", flat=True))
        if not idler:
            return []
        soru = OkumaSorusu.objects.get(pk=rng.choice(idler))
        siklar = [soru.dogru] + [c for c in soru.celdiriciler if c]
        rng.shuffle(siklar)
        secilen.append({"id": soru.id, "siklar": siklar})
    return secilen


def dogru_sayisi(sorular, cevaplar):
    """cevaplar: {soru_id (str): seçilen şık metni} -> doğru sayısı."""
    dogrular = dict(OkumaSorusu.objects.filter(id__in=[s["id"] for s in sorular])
                    .values_list("id", "dogru"))
    return sum(1 for s in sorular if cevaplar.get(str(s["id"])) == dogrular.get(s["id"]))
