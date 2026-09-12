"""
Modelin döndürmek zorunda olduğu yapı.

Alan adları bilerek Django modelindeki adlarla aynı: `writer.py` çeviri
yapmadan yazabilsin diye.

KATI KİP NOTU: sağlayıcıya `strict: true` ile gönderildiğinde şemadaki her
alan zorunlu olur; isteğe bağlı alan diye bir şey kalmaz. Bu yüzden hiçbir
alanda Optional yok — doldurulamayan yerler `""` ve `[]` ile geçilir.
`llm.strict_schema()` bunu şema üretirken zaten dayatıyor.
"""

import warnings
from typing import List, Literal

from pydantic import BaseModel, Field

# `register` alanı BaseModel'in ABCMeta'dan gelen `register` sınıf metodunu
# gölgeliyor. Örnek üzerinde alan kazanıyor, şema da doğru üretiliyor; yalnızca
# pydantic bilgi amaçlı uyarıyor. Alanın adını değiştirmek Django modeliyle
# eşleşmeyi bozacağı için uyarıyı susturuyoruz.
warnings.filterwarnings("ignore", message='Field name "register"')
warnings.filterwarnings("ignore", message=".*non-serializable-default.*")
warnings.filterwarnings("ignore", message=".*is not JSON serializable.*")

# Django modelindeki TextChoices değerleriyle birebir aynı olmalı.
POS = Literal["noun", "verb", "adjective", "adverb", "phrasal_verb",
              "preposition", "conjunction"]
CEFR = Literal["A1", "A2", "B1", "B2", "C1", "C2"]
SENTIMENT = Literal["neutral", "positive", "negative"]
REGISTER = Literal["neutral", "formal", "academic", "informal", "slang", "literary"]
COLLOCATION_KIND = Literal["verb_noun", "adj_noun", "noun_noun", "adv_adj",
                           "adv_verb", "other"]
PATTERN_KIND = Literal["preposition", "verb_form", "clause", "structure", "other"]
RELATION_TYPE = Literal["synonym", "antonym", "simpler", "confused_with"]


class Collocation(BaseModel):
    pattern: str = Field(description="Birlikte kullanım: 'make a decision'")
    kind: COLLOCATION_KIND
    meaning_tr: str = Field(description="Kalıbın Türkçesi: 'karar vermek'")
    example: str = Field(description="Kalıbı BİREBİR içeren tam cümle")


class UsagePattern(BaseModel):
    pattern: str = Field(description="Gramer kalıbı: 'depend on sth'")
    kind: PATTERN_KIND
    example: str = Field(description="Kalıbı kullanan tam cümle")
    note: str = Field(description="Kısa uyarı; yoksa boş bırak")


class Meaning(BaseModel):
    meaning_tr: str = Field(description="Türkçe karşılık; tek anlam, virgülle 2-3 eşanlamlı olabilir")
    definition: str = Field(description="İngilizce tanım; öğrencinin anlayacağı sadelikte")
    sentiment: SENTIMENT
    register: REGISTER
    categories: List[str] = Field(description="Yalnızca verilen alan listesinden seç; uymuyorsa boş")
    collocations: List[Collocation]
    patterns: List[UsagePattern]
    sentences: List[str] = Field(description="TAM 5 cümle, kolaydan zora (A2 -> C1)")


class FalseFriend(BaseModel):
    turkish_lookalike: str = Field(description="Benzediği Türkçe kelime: 'sempatik'")
    assumed_meaning: str = Field(description="Öğrencinin sandığı anlam")
    correct_english: str = Field(description="O sanılan anlamın gerçek İngilizcesi")
    note: str


class Relation(BaseModel):
    to_word: str = Field(description="Bağlanılan kelimenin İngilizcesi")
    to_pos: POS
    type: RELATION_TYPE
    note: str = Field(description="Nüans: 'aynı anlam ama daha resmî'")


class Word(BaseModel):
    """Tek bir sözlük maddesi: belirli türdeki belirli bir kelime."""

    found: bool = Field(description="Kelime gerçek İngilizce mi ve emin misin")
    skip_reason: str = Field(description="found=false ise sebebi; değilse boş")

    text: str
    pos: POS
    cefr: CEFR
    family_root: str = Field(description="Türetme ailesinin en yalın üyesi: 'courage'")
    v2Form: str = Field(description="Yalnızca fiilse 2. hâl; değilse boş")
    v3Form: str = Field(description="Yalnızca fiilse 3. hâl; değilse boş")

    meanings: List[Meaning]
    false_friends: List[FalseFriend]
    relations: List[Relation]
