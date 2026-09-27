"""
Kök bulma — metindeki yazımdan sözlük maddesine.

NEDEN GEREKLİ
-------------
Metinde `analyses`, `analysed`, `analysing` geçiyor; veritabanına
girmesi gereken tek bir madde var: `analyse`. Kök bulunmazsa aynı
kelime dört ayrı satır olarak çıkar, zenginleştirme hattı dördünü de
üretir ve dört ayrı aile kurulur — §7'de anlatılan sessiz bozulmanın
tam olarak aynısı, bu sefer girişte.

NEDEN HAZIR BİR KÜTÜPHANE KULLANILMADI
--------------------------------------
spaCy ya da NLTK bu işi yapar ama ikisi de büyük bağımlılık (spaCy'nin
modeli tek başına 40 MB'ın üstünde ve GitHub'dan iniyor). Bu komut yılda
birkaç kez, birkaç bin kelime üzerinde çalışacak; kural tabanlı bir
çözüm yeterli ve projenin geri kalanıyla tutarlı.

NASIL ÇALIŞIYOR — "ÜRET VE EN SIKI SEÇ"
---------------------------------------
Tek yönlü kural yazmak yerine (—s at, —ed at) bütün adaylar üretilip
aralarından EN SIK KULLANILANI seçiliyor:

  1. Düzensizler tablodan (went -> go, children -> child, better -> good)
  2. Bütün sonek kuralları uygulanır, her biri bir aday üretir
  3. Adayların sıklıkları karşılaştırılır, en sık olan kazanır
  4. Hiçbiri eşiği geçemezse kelime olduğu gibi bırakılır

ÖNCE "İLK GEÇERLİ ADAYI AL" YAZILMIŞTI VE YANLIŞTI. Sebebi şu:
sıklık verisi web metninden geliyor ve `analys`, `runn`, `mak`, `bigg`
gibi PARÇALAR da orada sıfırdan büyük bir değere sahip (kırık yazımlar,
bölünmüş kelimeler). Yani "gerçek kelime mi" sorusunun cevabı evet
çıkıyordu ve `making -> mak`, `running -> runn` oluyordu.

Karşılaştırma bunu kendiliğinden çözüyor, çünkü aradaki fark büyük:

  make 6.08  vs  mak  3.13
  run  5.49  vs  runn 1.47
  big  5.67  vs  bigg 2.73
  lie  4.84  vs  ly   3.37

KORUNAN KELİMELER
-----------------
Bazı kelimeler -s ile biter ama çoğul değildir: `analysis`, `basis`,
`crisis`, `bus`, `gas`, `news`, `species`, `series`, `means`. Bunlara
kural uygulanmıyor; uygulansaydı `analysis` -> `analysi` gibi
uydurma kökler çıkar ve sözlük kontrolünü şans eseri geçenler
veritabanına yazılırdı.
"""

import re

from . import frequency

# Sonu -s / -is / -us ile bitip çoğul OLMAYAN kelimeler.
KORUNANLAR = {
    "analysis", "basis", "crisis", "thesis", "hypothesis", "emphasis",
    "diagnosis", "synthesis", "parenthesis", "axis", "oasis",
    "bus", "gas", "plus", "virus", "focus", "status", "census", "campus",
    "consensus", "surplus", "nucleus", "stimulus", "apparatus", "corpus",
    "news", "series", "species", "means", "ethics", "physics", "politics",
    "economics", "statistics", "mathematics", "athletics", "linguistics",
    "this", "his", "its", "yes", "less", "unless", "across", "always",
    "perhaps", "process", "access", "success", "address", "express",
    "press", "class", "mass", "pass", "loss", "cross", "glass", "grass",
    "illness", "witness", "business", "progress", "congress", "stress",
    "discuss", "possess", "assess", "express", "distress",
    "various", "serious", "previous", "obvious", "curious", "anxious",
    "conscious", "religious", "ambitious", "precious", "numerous",
    "famous", "nervous", "dangerous", "enormous", "generous", "jealous",
    "is", "was", "has", "does", "goes", "us",
    "bias", "atlas", "canvas", "chaos", "bonus", "genius", "radius",
    "campus", "circus", "census", "thesis", "lens", "iris", "tennis",
}

# Latince/Yunanca çoğullar. Kuralla çözülemezler.
LATINCE_COGULLAR = {
    "analyses": "analysis", "bases": "basis", "crises": "crisis",
    "theses": "thesis", "hypotheses": "hypothesis", "diagnoses": "diagnosis",
    "syntheses": "synthesis", "parentheses": "parenthesis", "axes": "axis",
    "emphases": "emphasis", "oases": "oasis",
    "criteria": "criterion", "phenomena": "phenomenon",
    "curricula": "curriculum", "bacteria": "bacterium",
    # "data" ve "media" bilerek YOK: modern İngilizcede tekil/çoğul ayrımı
    # kalkmış, kitle ismi gibi kullanılıyorlar. "datum" üretmek öğrenciye
    # kullanmayacağı bir madde verir.
    "stimuli": "stimulus", "nuclei": "nucleus", "fungi": "fungus",
    "syllabi": "syllabus", "alumni": "alumnus", "cacti": "cactus",
    "indices": "index", "matrices": "matrix", "appendices": "appendix",
    "vertices": "vertex", "apices": "apex",
    "formulae": "formula", "vertebrae": "vertebra", "antennae": "antenna",
}

# Düzensiz çoğullar.
DUZENSIZ_COGULLAR = {
    "children": "child", "men": "man", "women": "woman", "people": "person",
    "teeth": "tooth", "feet": "foot", "geese": "goose", "mice": "mouse",
    "lice": "louse", "oxen": "ox", "knives": "knife", "wives": "wife",
    "lives": "life", "leaves": "leaf", "wolves": "wolf", "halves": "half",
    "shelves": "shelf", "thieves": "thief", "loaves": "loaf",
    "calves": "calf", "selves": "self", "elves": "elf",
}

# Düzensiz fiiller: çekimli biçim -> kök.
# Yalnızca akademik metinde geçme ihtimali olanlar; tam liste gereksiz.
DUZENSIZ_FIILLER = {
    "was": "be", "were": "be", "been": "be", "being": "be", "am": "be",
    "is": "be", "are": "be",
    "had": "have", "has": "have", "having": "have",
    "did": "do", "does": "do", "done": "do", "doing": "do",
    "went": "go", "gone": "go", "goes": "go",
    "said": "say", "made": "make", "took": "take", "taken": "take",
    "came": "come", "saw": "see", "seen": "see", "knew": "know",
    "known": "know", "got": "get", "gotten": "get", "gave": "give",
    "given": "give", "found": "find", "thought": "think", "told": "tell",
    "became": "become", "left": "leave", "felt": "feel", "brought": "bring",
    "began": "begin", "begun": "begin", "kept": "keep", "held": "hold",
    "wrote": "write", "written": "write", "stood": "stand", "heard": "hear",
    "let": "let", "meant": "mean", "set": "set", "met": "meet",
    "ran": "run", "paid": "pay", "sat": "sit", "spoke": "speak",
    "spoken": "speak", "lay": "lie", "led": "lead", "grew": "grow",
    "grown": "grow", "lost": "lose", "fell": "fall", "fallen": "fall",
    "sent": "send", "built": "build", "understood": "understand",
    "drew": "draw", "drawn": "draw", "broke": "break", "broken": "break",
    "spent": "spend", "rose": "rise", "risen": "rise", "driven": "drive",
    "drove": "drive", "bought": "buy", "wore": "wear", "worn": "wear",
    "chose": "choose", "chosen": "choose", "sought": "seek",
    "taught": "teach", "caught": "catch", "fought": "fight",
    "arose": "arise", "arisen": "arise", "shown": "show", "showed": "show",
    "borne": "bear", "bore": "bear", "dealt": "deal", "meant": "mean",
    "sold": "sell", "told": "tell", "won": "win", "led": "lead",
    "struck": "strike", "hidden": "hide", "hid": "hide",
}

# Düzensiz sıfat dereceleri.
DUZENSIZ_SIFATLAR = {
    "better": "good", "best": "good", "worse": "bad", "worst": "bad",
    "further": "far", "furthest": "far", "farther": "far", "farthest": "far",
    "more": "many", "most": "many", "less": "little", "least": "little",
}

TUM_DUZENSIZLER = {}
TUM_DUZENSIZLER.update(LATINCE_COGULLAR)
TUM_DUZENSIZLER.update(DUZENSIZ_COGULLAR)
TUM_DUZENSIZLER.update(DUZENSIZ_FIILLER)
TUM_DUZENSIZLER.update(DUZENSIZ_SIFATLAR)

SESLI = set("aeiou")


def _aday_uret(kelime: str):
    """
    Bir yazımdan olabilecek kökleri sırayla üretir.

    Sıra önemli: daha özel kural önce denenmeli. `studies` için önce
    "ies -> y" denenip `study` bulunuyor; "s -> ''" önce denenseydi
    `studie` çıkar ve sözlükte olmadığı için zaten elenirdi — ama
    `dies` gibi kelimelerde yanlış sonuç verebilirdi.
    """
    k = kelime

    # --- çoğul / 3. tekil ---
    if k.endswith("ies") and len(k) > 4:
        yield k[:-3] + "y"
    if k.endswith("ves") and len(k) > 4:
        yield k[:-3] + "f"
        yield k[:-3] + "fe"
    if k.endswith(("ches", "shes", "sses", "xes", "zes")) and len(k) > 4:
        yield k[:-2]
    if k.endswith("es") and len(k) > 3:
        yield k[:-2]
        yield k[:-1]
    if k.endswith("s") and not k.endswith("ss") and len(k) > 3:
        yield k[:-1]

    # --- geçmiş zaman / sıfat-fiil ---
    if k.endswith("ied") and len(k) > 4:
        yield k[:-3] + "y"
    if k.endswith("ed") and len(k) > 3:
        yield k[:-2]          # walked -> walk
        yield k[:-1]          # used -> use
        if len(k) > 4 and k[-3] == k[-4] and k[-3] not in SESLI:
            yield k[:-3]      # stopped -> stop

    # --- -ing ---
    if k.endswith("ing") and len(k) > 4:
        yield k[:-3]          # reading -> read
        yield k[:-3] + "e"    # making -> make
        if len(k) > 5 and k[-4] == k[-5] and k[-4] not in SESLI:
            yield k[:-4]      # running -> run
        if k.endswith("ying") and len(k) >= 5:
            yield k[:-4] + "ie"   # lying -> lie

    # --- derece ekleri ---
    if k.endswith("ier") and len(k) > 4:
        yield k[:-3] + "y"
    if k.endswith("iest") and len(k) > 5:
        yield k[:-4] + "y"
    if k.endswith("er") and len(k) > 4:
        yield k[:-2]
        yield k[:-1]
        if len(k) > 4 and k[-3] == k[-4] and k[-3] not in SESLI:
            yield k[:-3]
    if k.endswith("est") and len(k) > 5:
        yield k[:-3]
        yield k[:-2]
        if len(k) > 5 and k[-4] == k[-5] and k[-4] not in SESLI:
            yield k[:-4]


# Bir adayın kök sayılabilmesi için gereken en düşük mutlak sıklık.
# 2.5 ile parçalar (analys 1.36, runn 1.47, studie 1.98) eleniyor,
# gerçek ama seyrek kelimeler (analyse 3.47) geçiyor.
EN_DUSUK_ADAY_SIKLIGI = 2.5

# Aday, kelimenin kendisinden en fazla bu kadar daha seyrek olabilir.
#
# Mutlak eşik tek başına yetmedi: `bias` (4.42) için üretilen `bia` da
# 2.79 ile eşiği geçiyordu ve `bias -> bia` oluyordu. Göreli eşik bunu
# çözüyor çünkü gerçek kök çekimli biçimden pek seyrek olmaz:
#
#   analysed 3.55 -> analyse 3.47   fark 0.08  (kök, kabul)
#   bias     4.42 -> bia     2.79   fark 1.63  (parça, ret)
#
# 0.5 ikisinin arasında geniş bir boşlukta duruyor.
EN_COK_SIKLIK_DUSUSU = 0.5


def lemma(kelime: str) -> str:
    """
    Kelimenin kök hâli. Bulunamazsa kelimenin kendisi döner.

    Yalnızca ÇEKİM geri alınıyor, TÜRETME değil: `encouragement` kök
    olarak kalıyor, `encourage`a indirilmiyor. Sebebi words/models.py'ın
    açılış yorumunda: türetme ayrı bir kelimedir, kendi anlamı ve kendi
    cümleleri vardır. Aileyi kurmak zenginleştirme hattının işi, bu
    dosyanın değil.
    """
    k = (kelime or "").strip().lower()
    if not k or len(k) < 2:
        return k

    if k in TUM_DUZENSIZLER:
        return TUM_DUZENSIZLER[k]

    if k in KORUNANLAR:
        return k

    # Kelimenin kendisi çekim eki taşımıyorsa dokunma.
    # (Bu kontrol olmadan `focus` -> `focu`, `less` -> `les` denenirdi.)
    if not re.search(r"(s|ed|ing|er|est)$", k):
        return k

    # Başlangıç puanı eşiğin hemen ALTINDA; yani eşiği geçen herhangi bir
    # aday kelimenin kendisini yener.
    #
    # Karşılaştırmaya kelimenin KENDİ sıklığı katılmıyor ve bu bilinçli:
    # çekimli biçim kökten daha sık olabiliyor (`analysed` 3.55 > `analyse`
    # 3.47, `sustained` > `sustain`). Kendi sıklığıyla yarıştırılsaydı bu
    # kelimeler hiç köke inmezdi ve veritabanına çekimli hâlleriyle
    # girerlerdi.
    kendi_puani = frequency.zipf(k)
    esik = max(EN_DUSUK_ADAY_SIKLIGI, kendi_puani - EN_COK_SIKLIK_DUSUSU)

    en_iyi, en_iyi_puan = k, esik - 0.001
    for aday in _aday_uret(k):
        if len(aday) < 2 or aday == k:
            continue
        if aday in KORUNANLAR:
            return aday
        puan = frequency.zipf(aday)
        if puan >= esik and puan > en_iyi_puan:
            en_iyi, en_iyi_puan = aday, puan

    return en_iyi
