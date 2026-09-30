"""
Elle yazılmış kelimeleri sözlüğe ekler (rapor 18.16: Oxford'da olup bizde
olmayan kelimeler; Claude elle yazar, API yok).

    manage.py elle_kelime_yukle veri/oxford_eksik/a1.jsonl --dry-run
    manage.py elle_kelime_yukle veri/oxford_eksik/a1.jsonl

Satır başına bir kelime (JSONL):

    {"text": "banana", "pos": "noun", "cefr": "A1",
     "aile": "banana",                    # isteğe bağlı: ailesi (var olan bir kelimenin yazımı)
     "v2": "was/were", "v3": "been",      # isteğe bağlı: düzensiz fiil hâlleri
     "bicimler": [["am", "other"], ["is", "third_person"]],   # isteğe bağlı: çekimleri elle
                                          # verir (be, have gibi kurala uymayanlar)
     "anlamlar": [
        {"tr": "muz", "en": "a long curved fruit with a yellow skin",
         "ornekler": ["I eat a banana every morning.", "Monkeys love bananas."]}
     ]}

Kurallar:
  - Aynı (yazım, tür) sözlükte varsa ATLANIR (üzerine yazılmaz).
  - Kelime ortak sözlüğe girer; seviye kaynağı "oxford" (cefr Oxford listesinden).
  - Sıklık (wordfreq) ve çekimler (WordForm) kendiliğinden hesaplanır.
  - Her anlamda Türkçe anlam, İngilizce açıklama ve en az 1 örnek zorunlu.
Tekrar çalıştırmak güvenlidir.
"""

import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from words import inflect
from words.models import (
    CEFR_LEVELS, ExampleSentence, Meaning, PartOfSpeech, Word, WordFamily, WordForm,
)
from words.siklik import siklik_puani

KAYNAK = "claude-elle"


def dogrula(k, satir_no):
    hatalar = []
    if not str(k.get("text") or "").strip():
        hatalar.append("text boş")
    if k.get("pos") not in PartOfSpeech.values:
        hatalar.append(f"bilinmeyen tür: {k.get('pos')}")
    if k.get("cefr") not in CEFR_LEVELS:
        hatalar.append(f"bilinmeyen seviye: {k.get('cefr')}")
    anlamlar = k.get("anlamlar") or []
    if not anlamlar:
        hatalar.append("anlam yok")
    for i, a in enumerate(anlamlar, 1):
        if not (a.get("tr") and a.get("en") and a.get("ornekler")):
            hatalar.append(f"{i}. anlamda tr / en / ornekler eksik")
    if hatalar:
        raise CommandError(f"{satir_no}. satır ({k.get('text')}): " + "; ".join(hatalar))


def aile_bul(k):
    kok = (k.get("aile") or k["text"]).strip()
    var = Word.objects.filter(text__iexact=kok).select_related("family").first()
    if var:
        return var.family
    aile, _ = WordFamily.objects.get_or_create(root=kok.lower())
    return aile


class Command(BaseCommand):
    help = "Elle yazılmış kelimeleri (JSONL) sözlüğe ekler; var olanları atlar."

    def add_arguments(self, parser):
        parser.add_argument("dosya")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, dosya, dry_run, **o):
        kayitlar = []
        with open(dosya, encoding="utf-8") as f:
            for no, satir in enumerate(f, 1):
                if satir.strip():
                    k = json.loads(satir)
                    dogrula(k, no)
                    kayitlar.append(k)
        eklenen, atlanan = [], []
        with transaction.atomic():
            for k in kayitlar:
                text = k["text"].strip()
                if Word.objects.filter(text__iexact=text, pos=k["pos"]).exists():
                    atlanan.append(f"{text}:{k['pos']}")
                    continue
                eklenen.append(f"{text}:{k['pos']}")
                if dry_run:
                    continue
                w = Word.objects.create(
                    family=aile_bul(k), text=text, pos=k["pos"], cefr=k["cefr"],
                    cefr_kaynak="oxford", v2Form=k.get("v2"), v3Form=k.get("v3"),
                    isBaseWord=True, visibility="public", siklik=siklik_puani(text))
                for sira, a in enumerate(k["anlamlar"]):
                    m = Meaning.objects.create(word=w, meaning_tr=a["tr"].strip(),
                                               definition=a["en"].strip(), sort_order=sira)
                    ExampleSentence.objects.bulk_create([
                        ExampleSentence(meaning=m, text=o.strip(), source=KAYNAK, sort_order=i)
                        for i, o in enumerate(a["ornekler"][:Meaning.EXAMPLE_SENTENCE_COUNT])])
                if k.get("bicimler"):
                    WordForm.objects.filter(word=w).delete()
                    bicimler = {}
                    for b, tur in k["bicimler"]:
                        bicimler.setdefault(b.lower(), tur)      # aynı yazım bir kez
                    WordForm.objects.bulk_create([WordForm(word=w, surface=b, kind=tur)
                                                  for b, tur in bicimler.items()])
                else:
                    inflect.rebuild_forms(w)
        onek = "(dry-run) " if dry_run else ""
        self.stdout.write(f"{onek}{len(kayitlar)} kayıt: {len(eklenen)} eklendi, {len(atlanan)} zaten vardı.")
        if atlanan:
            self.stdout.write("Atlanan: " + ", ".join(atlanan))
