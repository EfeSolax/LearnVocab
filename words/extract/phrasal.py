"""
Phrasal verb yakalama.

NEDEN AYRI BİR DOSYA
--------------------
`out`, `up`, `off` tek başına işlev kelimesidir ve elenir. Ama
`carry out`, `point out`, `bring about` elenmemeli: bunlar anlamı
parçalarından çıkmayan, öğrenilmesi gereken sözlük maddeleridir ve
LearnVocab'ın kelime modelinde zaten kendi türleri var
(PartOfSpeech.PHRASAL_VERB). Kelime hattı da onları kabul ediyor
(KELIME-HATTI-DEVAM.txt §7-KARAR 3: "Phrasal verb'ler geçer").

İKİ YOLLU YAKALAMA
------------------
1. KÜRATÖRLÜ LİSTE — aşağıdaki tablo. Metinde geçen bunlar doğrudan
   çıktıya giriyor. Küme sayılıdır ve akademik metinde işe yarayanlar
   birkaç yüz tanedir; bir kez yazılır, doğru kalır.

2. ADAY YAKALAMA — listede olmayan fiil+edat ikilileri sayılıp AYRI bir
   dosyaya yazılıyor. Otomatik kabul EDİLMİYORLAR, çünkü kural her zaman
   yanılır: "go to the store"daki `go to` phrasal verb değildir, "look at
   the table"daki `look at` sınırdadır. Bu bir KARAR LİSTESİDİR —
   merge_families --list gibi, göz gezdirilip elle seçilecek.

Bu ayrım projenin her yerindeki biçimin aynısı: kod arar, insan yargılar.
"""

import re

# Phrasal verb'lerde geçen parçacıklar.
PARCACIKLAR = (
    "about", "across", "after", "against", "ahead", "along", "apart",
    "around", "aside", "at", "away", "back", "behind", "between", "by",
    "down", "for", "forth", "forward", "from", "in", "into", "of", "off",
    "on", "onto", "out", "over", "past", "round", "through", "to",
    "together", "towards", "under", "up", "upon", "with", "without",
)

# --- Küratörlü liste --------------------------------------------------
# Akademik ve genel metinde sık geçenler. Genişletilebilir; ölçüt
# "anlamı parçalarından çıkmıyor mu" olmalı. `walk into` gibi anlamı
# apaçık olanlar girmemeli, yoksa liste değersizleşir.
KURATORLU = {
    "account for", "add up", "allow for", "back up", "break down",
    "break out", "break through", "bring about", "bring forward",
    "bring out", "bring up", "build on", "build up", "call for",
    "call off", "carry on", "carry out", "catch on", "catch up",
    "check out", "clear up", "come about", "come across", "come along",
    "come down to", "come out", "come up", "come up with", "count on",
    "cut back", "cut down", "cut off", "deal with", "depend on",
    "die out", "do away with", "draw on", "draw up", "drop out",
    "end up", "figure out", "fill in", "fill out", "find out",
    "focus on", "follow up", "get across", "get around", "get by",
    "get on", "get over", "get through", "give in", "give off",
    "give out", "give rise to", "give up", "go on", "go over",
    "go through", "grow up", "hand in", "hand out", "hold back",
    "hold on", "keep on", "keep up", "lay out", "lead to", "leave out",
    "let down", "live up to", "look after", "look back", "look down on",
    "look for", "look forward to", "look into", "look out", "look over",
    "look up", "look up to", "make out", "make up", "make up for",
    "pass on", "pay off", "phase out", "pick up", "point out",
    "put aside", "put down", "put forward", "put off", "put together",
    "put up with", "rely on", "result from", "result in", "rule out",
    "run out", "run into", "set apart", "set aside", "set out", "set up",
    "settle down", "sort out", "stand for", "stand out", "stem from",
    "stick to", "sum up", "take account of", "take apart", "take away",
    "take in", "take off", "take on", "take over", "take up", "talk over",
    "tear down", "think over", "throw away", "touch on", "try out",
    "turn down", "turn into", "turn out", "turn to", "turn up",
    "wear off", "work out", "wipe out", "write down", "write off",
}

# Aday yakalamada bu fiiller dikkate alınmıyor: yardımcı/kip fiilleri ve
# hareket fiilleri, edatla birleştiklerinde neredeyse hep düz anlamlıdır
# ("walk to", "is in", "was on").
ADAY_DISI_FIILLER = {
    "be", "is", "are", "was", "were", "been", "being", "am",
    "have", "has", "had", "having", "do", "does", "did", "done",
    "will", "would", "shall", "should", "can", "could", "may", "might",
    "must", "walk", "drive", "fly", "swim", "sit", "stand", "lie",
    "say", "said", "tell", "ask",
}


def _ikili_uret(tokenler, lemma_fonksiyonu):
    """
    Metindeki fiil+parçacık ikililerini üretir.

    Araya en fazla bir kelime girebiliyor: "carry it out", "point them
    out". İkiden fazlası phrasal verb olmaktan çıkıp ayrı bir cümle
    öğesine dönüşüyor.
    """
    n = len(tokenler)
    for i, token in enumerate(tokenler):
        kok = lemma_fonksiyonu(token)
        if kok in ADAY_DISI_FIILLER:
            continue
        for mesafe in (1, 2):
            j = i + mesafe
            if j >= n:
                break
            if tokenler[j] in PARCACIKLAR:
                yield f"{kok} {tokenler[j]}", mesafe
                # Üç parçalı olanlar: "come up with", "look forward to"
                if j + 1 < n and tokenler[j + 1] in PARCACIKLAR:
                    yield f"{kok} {tokenler[j]} {tokenler[j + 1]}", mesafe


def bul(tokenler, lemma_fonksiyonu):
    """
    Metinden phrasal verb'leri çıkarır.

    (bulunanlar, adaylar) döner. İkisi de {ifade: sayı} sözlüğü.
    Bulunanlar küratörlü listede olanlar — doğrudan çıktıya girerler.
    Adaylar listede olmayanlar — ayrı dosyaya, göz gezdirilmek üzere.
    """
    bulunanlar, adaylar = {}, {}
    for ifade, mesafe in _ikili_uret(tokenler, lemma_fonksiyonu):
        if ifade in KURATORLU:
            bulunanlar[ifade] = bulunanlar.get(ifade, 0) + 1
        elif mesafe == 1:
            # Adaylarda yalnızca bitişik ikililer sayılıyor: araya kelime
            # girmiş olanların phrasal verb olma ihtimali düşük ve aday
            # listesi zaten gürültülü.
            adaylar[ifade] = adaylar.get(ifade, 0) + 1
    return bulunanlar, adaylar


# Aday listesine girmek için gereken en az tekrar sayısı. Tek seferlik
# eşleşmelerin neredeyse tamamı gürültü ("increase in", "change from").
ADAY_EN_AZ_TEKRAR = 3
