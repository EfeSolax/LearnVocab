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
     "cefr_kaynak": "learnvocab",         # isteğe bağlı: oxford (varsayılan) / cambridge / learnvocab
     "anlamlar": [
        {"tr": "muz", "en": "a long curved fruit with a yellow skin",
         "ornekler": ["I eat a banana every morning.", "Monkeys love bananas."],
         "benzer": ["plantain"]}          # isteğe bağlı: bu anlamın eş anlamlıları (sözlükte varsa bağlanır)
     ]}

Phrasal verb'de (pos "phrasal_verb", 18.38): ailesi ve `base_verb`'ü ilk kelimedeki
fiil (give up -> give); v2/v3 verilmezse kuralla üretilir (gave up / given up).

Kurallar:
  - Aynı (yazım, tür) sözlükte varsa ATLANIR (üzerine yazılmaz). Büyük harfli yazım tam
    eşleşmeyle bakılır: "March" (mart), "march" (yürüyüş) varken de eklenir.
  - Kelime ortak sözlüğe girer; seviye kaynağı varsayılan "oxford" (cefr Oxford listesinden).
  - "benzer" bağları anlama yazılır (eş anlamlı); fiil karşılığı varsa o seçilir,
    sözlükte olmayan atlanır ve raporlanır.
  - Sıklık (wordfreq) ve çekimler (WordForm) kendiliğinden hesaplanır.
  - Her anlamda Türkçe anlam, İngilizce açıklama ve en az 1 örnek zorunlu.
Tekrar çalıştırmak güvenlidir.
"""

import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from words import inflect
from words.models import (
    CEFR_LEVELS, ExampleSentence, Meaning, PartOfSpeech, RelationType, Word, WordFamily,
    WordForm, WordRelation,
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
    if k.get("cefr_kaynak", "oxford") not in dict(Word.CEFR_KAYNAK_CHOICES):
        hatalar.append(f"bilinmeyen seviye kaynağı: {k.get('cefr_kaynak')}")
    anlamlar = k.get("anlamlar") or []
    if not anlamlar:
        hatalar.append("anlam yok")
    for i, a in enumerate(anlamlar, 1):
        if not (a.get("tr") and a.get("en") and a.get("ornekler")):
            hatalar.append(f"{i}. anlamda tr / en / ornekler eksik")
    if hatalar:
        raise CommandError(f"{satir_no}. satır ({k.get('text')}): " + "; ".join(hatalar))


def _phrasal_fiil(k):
    """Phrasal verb'ün ilk kelimesindeki fiil (give up -> give); yoksa None."""
    if k["pos"] != PartOfSpeech.PHRASAL_VERB or " " not in k["text"].strip():
        return None
    ilk = k["text"].strip().split(" ")[0]
    return Word.objects.filter(text__iexact=ilk, pos=PartOfSpeech.VERB).select_related("family").first()


def _benzer_hedef(yazim, pos):
    """Eş anlamlının sözlükteki kaydı: aynı tür önce, phrasal verb için fiil önce."""
    adaylar = list(Word.objects.filter(text__iexact=yazim.strip()))
    if pos == PartOfSpeech.PHRASAL_VERB:
        sira = [PartOfSpeech.VERB, PartOfSpeech.PHRASAL_VERB]
    else:
        sira = [pos]
    for tur in sira:
        for w in adaylar:
            if w.pos == tur:
                return w
    return None


def aile_bul(k):
    fiil = None if k.get("aile") else _phrasal_fiil(k)
    if fiil and fiil.family:
        return fiil.family
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
        eklenen, atlanan, bulunamayan_benzer = [], [], []
        with transaction.atomic():
            for k in kayitlar:
                text = k["text"].strip()
                # Büyük harfli yazım ayrı kelimedir: "March" (mart) "march" (yürüyüş) varken de eklenir.
                ayni = (Word.objects.filter(text=text, pos=k["pos"]) if text != text.lower()
                        else Word.objects.filter(text__iexact=text, pos=k["pos"]))
                if ayni.exists():
                    atlanan.append(f"{text}:{k['pos']}")
                    continue
                eklenen.append(f"{text}:{k['pos']}")
                if dry_run:
                    continue
                v2, v3 = k.get("v2"), k.get("v3")
                if k["pos"] == PartOfSpeech.PHRASAL_VERB and " " in text and not (v2 and v3):
                    cekim = inflect.cekimler(text, k["pos"])["cekim"]
                    v2, v3 = v2 or cekim["v2Form"] or None, v3 or cekim["v3Form"] or None
                w = Word.objects.create(
                    family=aile_bul(k), text=text, pos=k["pos"], cefr=k["cefr"],
                    cefr_kaynak=k.get("cefr_kaynak", "oxford"), v2Form=v2, v3Form=v3,
                    base_verb=_phrasal_fiil(k),
                    isBaseWord=True, visibility="public", siklik=siklik_puani(text))
                for sira, a in enumerate(k["anlamlar"]):
                    m = Meaning.objects.create(word=w, meaning_tr=a["tr"].strip(),
                                               definition=a["en"].strip(), sort_order=sira)
                    ExampleSentence.objects.bulk_create([
                        ExampleSentence(meaning=m, text=o.strip(), source=KAYNAK, sort_order=i)
                        for i, o in enumerate(a["ornekler"][:Meaning.EXAMPLE_SENTENCE_COUNT])])
                    for yazim in a.get("benzer") or []:
                        hedef = _benzer_hedef(yazim, w.pos)
                        if hedef is None or hedef.pk == w.pk:
                            bulunamayan_benzer.append(f"{text} = {yazim}")
                            continue
                        WordRelation.objects.get_or_create(
                            from_word=w, to_word=hedef, type=RelationType.SYNONYM, meaning=m)
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
        if bulunamayan_benzer:
            self.stdout.write("Sözlükte bulunmayan benzer: " + ", ".join(bulunamayan_benzer))
