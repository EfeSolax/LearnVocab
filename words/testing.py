"""
Testler için kelime kurma yardımcısı.

Yeni modelde bir kelime tek satır değil: aile + kelime + anlam + anlama
bağlı örnek cümleler. Her test dosyasının bunu ayrı ayrı kurması hem uzun
hem de model değiştiğinde her yeri elle düzeltmek anlamına gelirdi.

    kelime = make_word("immaculate", meaning="tertemiz")
    fiil   = make_word("go", pos="verb", v2="went", v3="gone")
    zengin = make_word("decision", collocations=[("make a decision", "verb_noun")])
"""

from .models import (
    Category, Collocation, ExampleSentence, Meaning, PartOfSpeech, Register,
    Sentiment, UsagePattern, Word, WordFamily,
)
from . import inflect


def make_word(text="immaculate", *, pos=PartOfSpeech.NOUN, meaning=None,
              definition="a test definition", sentences=None, family=None,
              v2=None, v3=None, level="B2", is_base=True, visibility="public",
              owner=None, extra_meanings=(), forms=True,
              sentiment=Sentiment.NEUTRAL, register=Register.NEUTRAL,
              categories=(), collocations=(), patterns=(), **kwargs):
    """
    Test için eksiksiz bir kelime kurar.

    family verilmezse kelimenin kendi adıyla tek kişilik bir aile açılır —
    gerçek davranışın aynısı.

    collocations ve patterns ANA ANLAMA bağlanır: ("make a decision",
    "verb_noun") gibi ikililer ya da doğrudan sözlük olarak verilebilir.
    """
    if family is None:
        family, _ = WordFamily.objects.get_or_create(root=text.lower())
    elif isinstance(family, str):
        family, _ = WordFamily.objects.get_or_create(root=family.lower())

    kelime = Word.objects.create(
        family=family, text=text, pos=pos,
        v2Form=v2, v3Form=v3,
        cefr=level, isBaseWord=is_base, visibility=visibility, owner=owner,
        **kwargs,
    )

    ana_anlam = Meaning.objects.create(
        word=kelime, meaning_tr=meaning or f"{text}-tr",
        definition=definition, sentiment=sentiment, register=register,
        sort_order=0,
    )
    for ad in categories:
        kategori, _ = Category.objects.get_or_create(
            slug=ad.lower(), defaults={"name": ad},
        )
        ana_anlam.categories.add(kategori)

    for i, (anlam, aciklama) in enumerate(extra_meanings, start=1):
        Meaning.objects.create(word=kelime, meaning_tr=anlam,
                               definition=aciklama, sort_order=i)

    if sentences is None:
        sentences = [f"A sentence with {text}."]
    ExampleSentence.objects.bulk_create([
        ExampleSentence(meaning=ana_anlam, text=c, source="test", sort_order=i)
        for i, c in enumerate(sentences[:Meaning.EXAMPLE_SENTENCE_COUNT])
    ])

    for i, ham in enumerate(collocations):
        veri = _ikili_coz(ham, "pattern", "kind")
        Collocation.objects.create(meaning=ana_anlam, sort_order=i, **veri)

    for i, ham in enumerate(patterns):
        veri = _ikili_coz(ham, "pattern", "kind")
        UsagePattern.objects.create(meaning=ana_anlam, sort_order=i, **veri)

    if forms:
        inflect.rebuild_forms(kelime)

    return kelime


def _ikili_coz(ham, birinci, ikinci):
    """("make a decision", "verb_noun") ya da {"pattern": …} kabul eder."""
    if isinstance(ham, dict):
        return dict(ham)
    if isinstance(ham, str):
        return {birinci: ham}
    return {birinci: ham[0], ikinci: ham[1]}
