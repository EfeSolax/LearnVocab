# -*- coding: utf-8 -*-
"""
14 Ekim (2) — kural taramasının (araclar/veri_kural_taramasi.py) r02 / r06 / r07 bulguları.
Claude elle okudu, API yok. Kararlar veri/kalite_olcumu/duzeltme/ altında.

  r02_sil        8 anlam: phrasal verb kaydı aynı anlamı veriyor (wrap up, sum up…) ve fiilin
                 başka anlamı var → fiil satırındaki anlam silinir (kopyası veri/kalite_olcumu/
                 duzeltme/silinen-anlamlar.tsv'ye yazılır; geri yüklemek için yeter).
  r02_etiket     32 anlam: anlam yalnızca "fiil + parçacık" ile geçiyor (ward off, flesh out…);
                 karşılığın başına "(off ile)" yazılır, anlam ve örnekler korunur.
                 8 kayıt (jump, scramble, bounce…) yanlış alarmdı, dokunulmadı (r02-degismedi.tsv).
  r06_ornek_sirasi  Birinci örneği "The teacher explained…/textbook explains…" gibi genel kalıp olan
                 308 anlamda, kalıp olmayan örnek öne alınır (örnek silinmez, yalnızca sıra).
  r07_ornek      2 örnek: grafik şiddet içeren birincil cümle nötr cümleyle değiştirilir.

Çalıştırma (önce kuru deneme, hiçbir şey yazmaz):
  python manage.py shell -c "from words.duzeltmeler import d_2026_10_14b as d; print(d.hepsi(kuru=True))"
Gerçek yazım (önce db.sqlite3'ün proje dışına yedeğini al):
  python manage.py shell -c "from words.duzeltmeler import d_2026_10_14b as d; print(d.hepsi())"
Hepsi tekrar çalıştırmak güvenli (uyuşmayan satır atlanır).
"""
import re
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.db import transaction

from words.models import ExampleSentence, Meaning

KLASOR = Path(settings.BASE_DIR) / "veri" / "kalite_olcumu" / "duzeltme"
YEDEK = KLASOR / "silinen-anlamlar.tsv"
SABLON = re.compile(
    r"\b(textbook explains|teacher explained|in simple terms|for beginners|the teacher said|"
    r"the manager said|the professor explained|the book describes)\b", re.I)


class Geri(Exception):
    """kuru=True: işlemi geri almak için."""


def oku(ad):
    for satir in (KLASOR / ad).read_text(encoding="utf-8").splitlines():
        if satir and not satir.startswith("#"):
            yield satir.split("\t")


def _sirala(kelime):
    """Silme sonrası kalan anlamların sort_order'ını 0..n-1 yapar."""
    for i, m in enumerate(kelime.meanings.order_by("sort_order", "id")):
        if m.sort_order != i:
            m.sort_order = i
            m.save(update_fields=["sort_order"])


def _calistir(is_fonksiyonu, kuru):
    try:
        with transaction.atomic():
            sayac = is_fonksiyonu()
            if kuru:
                raise Geri
    except Geri:
        pass
    return sayac


def r02_sil(kuru=False):
    def is_():
        sayac, yedek = Counter(), []
        for mid, kelime, tur, eski, _neden in oku("r02-sil.tsv"):
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
            yeni = not YEDEK.exists()
            with YEDEK.open("a", encoding="utf-8") as f:
                if yeni:
                    f.write("# r02 ile silinen anlamlar (geri yüklemek için).\n# id\tkelime\ttür\ttr\ttanım\törnekler\tkalıp\tkullanım_kalıbı\tilişki\tkonular\n")
                f.write("\n".join(yedek) + "\n")
        return sayac
    return _calistir(is_, kuru)


def r02_etiket(kuru=False):
    def is_():
        sayac = Counter()
        for mid, kelime, tur, eski, yeni in oku("r02-etiket.tsv"):
            m = Meaning.objects.filter(pk=mid, word__text=kelime, word__pos=tur).first()
            if not m:
                sayac["yok"] += 1
            elif m.meaning_tr == yeni:
                sayac["zaten yapılmış"] += 1
            elif m.meaning_tr != eski:
                sayac["uymadı (elle değişmiş)"] += 1
            else:
                m.meaning_tr = yeni
                m.save(update_fields=["meaning_tr"])
                sayac["etiketlendi"] += 1
        return sayac
    return _calistir(is_, kuru)


def r06_ornek_sirasi(kuru=False):
    def is_():
        sayac = Counter()
        for m in Meaning.objects.filter(examples__text__iregex=SABLON.pattern).distinct():
            ex = list(m.examples.order_by("sort_order", "id"))
            if not ex or not SABLON.search(ex[0].text):
                continue
            iyi = [e for e in ex if not SABLON.search(e.text)]
            if not iyi:
                sayac["hepsi kalıp: atlandı"] += 1
                continue
            yeni = iyi + [e for e in ex if SABLON.search(e.text)]
            for i, e in enumerate(yeni):
                if e.sort_order != i:
                    e.sort_order = i
                    e.save(update_fields=["sort_order"])
            sayac["öne alındı"] += 1
        return sayac
    return _calistir(is_, kuru)


def r07_ornek(kuru=False):
    def is_():
        sayac = Counter()
        for eid, _kelime, eski, yeni in oku("r07-ornek.tsv"):
            e = ExampleSentence.objects.filter(pk=eid).first()
            if not e:
                sayac["yok"] += 1
            elif e.text == yeni:
                sayac["zaten yapılmış"] += 1
            elif e.text != eski:
                sayac["uymadı"] += 1
            else:
                e.text = yeni
                e.save(update_fields=["text"])
                sayac["değişti"] += 1
        return sayac
    return _calistir(is_, kuru)


def hepsi(kuru=False):
    return {"r02_sil": r02_sil(kuru), "r02_etiket": r02_etiket(kuru),
            "r06_ornek_sirasi": r06_ornek_sirasi(kuru), "r07_ornek": r07_ornek(kuru)}
