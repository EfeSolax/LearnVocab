"""
İşlev kelimeleri — edatlar, bağlaçlar, zamirler, belirteçler.

NEDEN ELLE YAZILDI
------------------
Bu küme SAYILIDIR ve değişmez. Yaklaşık 250 kelime; bir kez yazılır,
sonsuza kadar doğru kalır. Küratörlü yanlış dost ve karıştırılan çift
tabloları (words/enrich/) ile aynı gerekçe.

Sıklık eşiğine bırakılamaz: `whereas`, `albeit`, `notwithstanding`,
`thereby` gibi bağlayıcılar sıklık listesinde ÇOK GERİDE (zipf 3'ün
altında) ve eşik onları "öğrenilmeye değer kelime" sayıp geçirir. Oysa
bunlar kelime değil, YAPI — ve LearnVocab'ın kelime modeline (aile,
anlam, eş dizim, ton) hiç uymuyorlar.

BUNLAR NEREYE GİDECEK
---------------------
Silinmiyorlar, AYRILIYORLAR. Çıkarım raporunda kendi bölümlerinde
listeleniyorlar; çünkü KELIME-HATTI-DEVAM.txt §11-[4]'te planlanan
Expression hattının hammaddesi tam olarak bu küme ("linker / connector /
prepositional phrase / idiom tek çatı altında").

PHRASAL VERB'LER BURADA DEĞİL
-----------------------------
`carry out`, `bring about` gibi yapılar edat İÇERİYOR ama işlev kelimesi
değil — anlamı olan, öğrenilmesi gereken sözlük maddeleri. Onları
phrasal.py ayrı yakalıyor ve çıktıda KALIYORLAR. Bu dosya yalnızca tek
başına duran edatı eliyor: "depend ON" içindeki `on` elenir, `carry out`
elenmez.
"""

# --- Edatlar -----------------------------------------------------------
EDATLAR = {
    "about", "above", "across", "after", "against", "along", "alongside",
    "amid", "amidst", "among", "amongst", "around", "as", "at", "before",
    "behind", "below", "beneath", "beside", "besides", "between", "beyond",
    "but", "by", "concerning", "despite", "down", "during", "except",
    "excluding", "following", "for", "from", "in", "including", "inside",
    "into", "like", "minus", "near", "of", "off", "on", "onto", "opposite",
    "out", "outside", "over", "past", "per", "plus", "regarding", "round", "since",
    "than", "through", "throughout", "till", "to", "toward", "towards",
    "under", "underneath", "unlike", "until", "up", "upon", "versus", "via",
    "with", "within", "without",
}

# --- Bağlaçlar ve bağlayıcı zarflar ------------------------------------
# Bunların çoğu akademik metinde çok geçer ama sıklık listesinde geridedir;
# eşiğe bırakılsa "öğrenilmeye değer kelime" sayılırlardı.
BAGLACLAR = {
    "and", "or", "nor", "so", "yet", "because", "although", "though",
    "whereas", "while", "whilst", "if", "unless", "whether", "since",
    "once", "whenever", "wherever", "however", "moreover", "furthermore",
    "nevertheless", "nonetheless", "therefore", "thus", "hence",
    "consequently", "accordingly", "meanwhile", "otherwise", "instead",
    "besides", "likewise", "similarly", "conversely", "albeit",
    "notwithstanding", "thereby", "thereafter", "therein", "thereof",
    "whereby", "wherein", "whereupon", "hereby", "herein", "provided",
    "supposing", "lest", "insofar", "inasmuch",
}

# --- Zamirler ----------------------------------------------------------
ZAMIRLER = {
    "i", "me", "my", "mine", "myself",
    "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "it", "its", "itself",
    "we", "us", "our", "ours", "ourselves",
    "they", "them", "their", "theirs", "themselves",
    "who", "whom", "whose", "which", "what", "that", "this", "these",
    "those", "there", "here", "everyone", "everybody", "everything",
    "someone", "somebody", "something", "anyone", "anybody", "anything",
    "noone", "nobody", "nothing", "one", "ones", "oneself", "each",
    "either", "neither", "both", "all", "any", "some", "none", "such",
    "other", "others", "another", "same",
}

# --- Belirteçler, sayılar, ölçü sözleri --------------------------------
BELIRTECLER = {
    "a", "an", "the", "every", "no", "much", "many", "more", "most",
    "few", "fewer", "fewest", "little", "less", "least", "several",
    "enough", "half", "whole", "own",
    "first", "second", "third", "fourth", "fifth", "sixth", "seventh",
    "eighth", "ninth", "tenth", "last", "next", "previous",
    "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "twenty", "thirty", "forty",
    "fifty", "hundred", "thousand", "million", "billion",
}

# --- Yardımcı ve kip fiilleri ------------------------------------------
# Bunlar gramerin parçası; sözlük maddesi olarak öğrenilmiyorlar.
YARDIMCI_FIILLER = {
    "be", "am", "is", "are", "was", "were", "been", "being",
    "have", "has", "had", "having",
    "do", "does", "did", "done", "doing",
    "will", "would", "shall", "should", "can", "could", "may", "might",
    "must", "ought", "need", "dare", "let", "get", "got", "gotten",
}

# --- Çok geçen işlev zarfları ------------------------------------------
ISLEV_ZARFLARI = {
    "not", "very", "too", "also", "just", "only", "even", "still",
    "already", "yet", "again", "ever", "never", "always", "often",
    "sometimes", "usually", "rarely", "seldom", "perhaps", "maybe",
    "probably", "possibly", "certainly", "indeed", "rather", "quite",
    "almost", "nearly", "hardly", "barely", "scarcely", "merely",
    "simply", "then", "now", "soon", "later", "today", "tomorrow",
    "yesterday", "ago", "away", "back", "forward", "together", "apart",
    "yes", "no", "ok", "okay", "well", "why", "how", "when", "where",
}


ISLEV_KELIMELERI = (
    EDATLAR | BAGLACLAR | ZAMIRLER | BELIRTECLER
    | YARDIMCI_FIILLER | ISLEV_ZARFLARI
)


# Hangi kelimenin hangi gruptan elendiğini rapora yazabilmek için.
# Eski (arkaik) İngilizce: Moby Dick, Platon, Marcus Aurelius çevirilerinde
# binlerce kez geçiyor (thou 1072, unto 451 — 24 Eylül PDF denemesi).
# Günümüz İngilizcesinde kullanılmıyor; hazırlık öğrencisine yük.
ARKAIK = {
    "thou", "thee", "thy", "thine", "thyself", "ye", "yea", "nay",
    "unto", "hath", "doth", "dost", "hast", "shalt", "wilt", "art", "wert",
    "canst", "couldst", "wouldst", "shouldst", "mayst", "didst", "hadst",
    "whence", "hither", "thither", "whither", "hence", "ere", "oft",
    "betwixt", "twixt", "tis", "twas", "methinks", "perchance", "anon",
    "aught", "naught", "wherefore", "thereunto", "herewith", "forsooth",
}
# "art" (sanat) ve "hence" gerçek kelimeler; "art" arkaik "are" olarak da
# geçiyor ama sanat anlamı çok daha yaygın, bu yüzden listeden çıkarılıyor.
ARKAIK -= {"art", "hence"}
ISLEV_KELIMELERI = ISLEV_KELIMELERI | ARKAIK

GRUPLAR = (
    ("edat", EDATLAR),
    ("bağlaç", BAGLACLAR),
    ("zamir", ZAMIRLER),
    ("belirteç", BELIRTECLER),
    ("yardımcı fiil", YARDIMCI_FIILLER),
    ("işlev zarfı", ISLEV_ZARFLARI),
    ("arkaik", ARKAIK),
)


def islev_kelimesi_mi(kelime: str) -> bool:
    return kelime.lower() in ISLEV_KELIMELERI


def grubu(kelime: str) -> str:
    """Kelimenin hangi işlev grubuna ait olduğu (yoksa boş)."""
    kelime = kelime.lower()
    for ad, kume in GRUPLAR:
        if kelime in kume:
            return ad
    return ""
