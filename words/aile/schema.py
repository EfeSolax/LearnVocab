"""
1. aşamada modelin döndürmek zorunda olduğu yapı.

Bilerek ÇOK KÜÇÜK: model yalnızca kelimeyi ve türünü yazıyor. Çekimler
(v2/v3/-ing/-s, çoğul, comparative/superlative) kodla üretiliyor
(words/inflect.py · cekimler). Şemada olmayan alanı model dolduramaz —
yani katı kip, prompt'taki "başka hiçbir şey yazma" kuralını API
seviyesinde de dayatıyor.

Tür değerleri Django modelindeki PartOfSpeech ile birebir aynı.
"""

from typing import List, Literal

from pydantic import BaseModel, Field

POS = Literal["noun", "verb", "adjective", "adverb", "phrasal_verb",
              "preposition", "conjunction"]


class AileUyesi(BaseModel):
    word: str = Field(description="Ailedeki kelime, küçük harfle: 'destruction'")
    type: POS


class AileCevabi(BaseModel):
    root_word: str = Field(description="Ailenin kökü; words listesinde de olmalı. "
                                       "Kelime İngilizcede yoksa boş.")
    words: List[AileUyesi] = Field(description="Kök dahil ailenin bütün kelimeleri, "
                                               "türleriyle. -ed/-ing çekimleri YOK.")
