# -*- coding: utf-8 -*-
"""
17 Ekim — Opus turunun belirsiz bıraktığı anlamlardan (veri/kalite_olcumu/opus/efe.tsv) Efe'nin
silinmesini onayladığı 4 anlam (B listesi: yanlış başlıkta ya da şiddet içeren). Karar dosyası
veri/kalite_olcumu/duzeltme/efe-sil.tsv; silinenin kopyası silinen-anlamlar.tsv'ye eklenir.

Çalıştırma (önce kuru deneme):
  python manage.py shell -c "from words.duzeltmeler import d_2026_10_17 as d; print(d.efe_sil(kuru=True))"
  python manage.py shell -c "from words.duzeltmeler import d_2026_10_17 as d; print(d.efe_sil())"
Tekrar çalıştırmak güvenli (uyuşmayan satır atlanır).
"""
from collections import Counter

from words.duzeltmeler.d_2026_10_14b import YEDEK, _calistir, _sirala, oku
from words.models import Meaning


def efe_sil(kuru=False):
    def is_():
        sayac, yedek = Counter(), []
        for mid, kelime, tur, eski, _neden in oku("efe-sil.tsv"):
            m = Meaning.objects.filter(pk=mid, word__text=kelime, word__pos=tur, meaning_tr=eski).select_related("word").first()
            if not m:
                sayac["yok/uymadı"] += 1
                continue
            if m.word.meanings.count() < 2:
                sayac["tek anlam: atlandı"] += 1
                continue
            yedek.append("\t".join([
                str(m.pk), kelime, tur, m.meaning_tr, m.definition or "",
                " / ".join(e.text for e in m.examples.all()),
                str(m.collocations.count()), str(m.patterns.count()),
                str(m.relations.count()),
                ", ".join(c.name for c in m.categories.all())]))
            kelime_obj = m.word
            m.delete()
            _sirala(kelime_obj)
            sayac["silindi"] += 1
        if yedek and not kuru:
            with YEDEK.open("a", encoding="utf-8") as f:
                f.write("\n".join(yedek) + "\n")
        return sayac
    return _calistir(is_, kuru)
