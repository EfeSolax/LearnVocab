"""
Seviye testinin 2. kısmı: özet soruları (rapor 7, 18.27; veri D4).

"Bu 4 cümlelik paragrafı en iyi özetleyen cümle hangisi?" Kelime
ekranlarının sonucuna göre en çok 3 seviyeden birer soru sorulur
(tahmin.sorulacak_seviyeler). Sorular yalnızca DENETLENMİŞ havuzdan gelir;
istenen seviyede soru yoksa o soru atlanır.
"""

import random

from .models import OkumaSorusu


def havuz_var_mi():
    return OkumaSorusu.objects.filter(denetlendi=True).exists()


def sorulari_sec(seviyeler, rng=None):
    """[{"id", "cefr", "siklar": [metin, …]}] — şıklar karışık; eksik seviye atlanır."""
    rng = rng or random.Random()
    secilen = []
    for seviye in seviyeler:
        idler = list(OkumaSorusu.objects.filter(denetlendi=True, cefr=seviye)
                     .values_list("id", flat=True))
        if not idler:
            continue
        soru = OkumaSorusu.objects.get(pk=rng.choice(idler))
        siklar = [soru.dogru] + [c for c in soru.celdiriciler if c]
        rng.shuffle(siklar)
        secilen.append({"id": soru.id, "cefr": soru.cefr, "siklar": siklar})
    return secilen


def dogru_seviyeler(sorular, cevaplar):
    """cevaplar: {soru_id (str): seçilen şık metni} -> doğru cevaplananların seviyeleri."""
    dogrular = dict(OkumaSorusu.objects.filter(id__in=[s["id"] for s in sorular])
                    .values_list("id", "dogru"))
    return [s["cefr"] for s in sorular if cevaplar.get(str(s["id"])) == dogrular.get(s["id"])]
