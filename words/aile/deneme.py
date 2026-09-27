"""
Aile hattının ölçüm listeleri: BEKLENTİLERİYLE birlikte, sürüm sürüm.

Prompt'u değiştirip "daha iyi oldu mu" diye bakmak, rastgele bir liste
çalıştırıp çıktıyı okumakla ölçülemez: hangi kelimenin ne vermesi
gerektiğini bilmiyorsan aldığın cevabın doğru olup olmadığını da
bilemezsin. (Eski hattın test_batch listesiyle aynı gerekçe.)

    python manage.py aile_olc --write                    # listeyi yaz
    python manage.py aile_uret --file listeler/aile-deneme.txt --depo ara-depo-deneme-2
    python manage.py aile_birlestir --depo ara-depo-deneme-2
    python manage.py aile_olc --depo ara-depo-deneme-2     # puanla

Deneme ayrı bir depoya yazılıyor ki asıl deponun içine karışmasın.

ALTI AMAÇ
---------
  A  TUTARLILIK  Aynı aileye farklı kapılardan giriliyor (analysis, analyst,
                 analytical). Hepsi aynı kökü vermeli ve birleştirmede TEK
                 aileye düşmeli. Modelin en önemli sınavı bu.
  B  ÖNEK        understand, undertake, overcome, discover: önekle başlayan
                 ama önekli OLMAYAN kelimeler. Kendi köklerinde kalmalı;
                 stand / take / come / cover aileye girmemeli.
                 overestimate ise TERSİ: "over" aşırılık öneki, kök estimate.
  C  TEK BAŞINA  arduous, salient, tacit, lucid: kök uydurma tuzağı.
  D  AYRIM       conscience/conscious, station/stationery: yalnızca yazımı
                 benzeyen kelimeler aynı aileye girmemeli.
  E  ÇEKİM       -ed/-ing kuralı: interest ailesinde interested ve
                 interesting OLMALI (bağımsız sıfat); build ailesinde
                 building OLMALI (isim, "bina") ama built OLMAMALI.
  F  UYDURMA     creative ailesinde "uncreatively" (sıklık 0) olmamalı.
  G  YAZIM       colour, centre, defence İngiliz yazımıyla soruluyor; cevap
                 Amerikan yazımıyla gelmeli (color, center, defense).
"""

# aile: A grubunda "aynı birleşik aileye düşmeli" kontrolü için etiket.
#
# 2. SÜRÜM (19 Eylül). İlk liste prompt'un KENDİ örnekleriyle doluydu
# (destroy, educate, conscience, arduous…) — model cevabı prompt'tan
# kopyalayabildiği için ölçtüğü şey genelleme değil ezberdi. Bu listedeki
# hiçbir kelime ve hiçbir beklenen kök prompt'ta geçmiyor; bunu
# words/test_aile.py · test_deneme_listesi_prompt_ile_kesismiyor denetliyor.
SURUM_2 = [
    # --- A: tutarlılık ---------------------------------------------------
    {"tohum": "organization", "grup": "A", "aile": "organize", "kok": ["organize"],
     "icermeli": ["organizational"]},
    {"tohum": "organizational", "grup": "A", "aile": "organize", "kok": ["organize"]},
    {"tohum": "disorganized", "grup": "A", "aile": "organize", "kok": ["organize"]},

    {"tohum": "justification", "grup": "A", "aile": "justify", "kok": ["justify"],
     "icermeli": ["justifiable"]},
    {"tohum": "unjustified", "grup": "A", "aile": "justify", "kok": ["justify"]},
    {"tohum": "justifiable", "grup": "A", "aile": "justify", "kok": ["justify"]},

    {"tohum": "reliable", "grup": "A", "aile": "rely", "kok": ["rely"],
     "icermeli": ["reliability", "unreliable"]},
    {"tohum": "reliability", "grup": "A", "aile": "rely", "kok": ["rely"]},
    {"tohum": "unreliable", "grup": "A", "aile": "rely", "kok": ["rely"]},

    {"tohum": "comparison", "grup": "A", "aile": "compare", "kok": ["compare"],
     "icermeli": ["comparative"]},
    {"tohum": "incomparable", "grup": "A", "aile": "compare", "kok": ["compare"]},

    {"tohum": "explanation", "grup": "A", "aile": "explain", "kok": ["explain"],
     "icermeli": ["explanatory"]},
    {"tohum": "unexplained", "grup": "A", "aile": "explain", "kok": ["explain"]},

    {"tohum": "successful", "grup": "A", "aile": "succeed", "kok": ["succeed", "success"],
     "icermeli": ["unsuccessful"]},
    {"tohum": "unsuccessful", "grup": "A", "aile": "succeed", "kok": ["succeed", "success"]},

    {"tohum": "persuasion", "grup": "A", "aile": "persuade", "kok": ["persuade"],
     "icermeli": ["persuasive"]},
    {"tohum": "persuasive", "grup": "A", "aile": "persuade", "kok": ["persuade"]},

    {"tohum": "inaccurate", "grup": "A", "aile": "accurate", "kok": ["accurate"],
     "icermeli": ["accuracy"]},
    {"tohum": "accuracy", "grup": "A", "aile": "accurate", "kok": ["accurate"]},

    # --- B: önek ---------------------------------------------------------
    {"tohum": "withdraw", "grup": "B", "kok": ["withdraw"], "icermemeli": ["draw"]},
    {"tohum": "represent", "grup": "B", "kok": ["represent"], "icermemeli": ["present"]},
    {"tohum": "outcome", "grup": "B", "kok": ["outcome"], "icermemeli": ["come"]},
    {"tohum": "overreact", "grup": "B", "kok": ["react"], "icermeli": ["reaction"]},
    {"tohum": "misbehave", "grup": "B", "kok": ["behave"], "icermeli": ["behavior"]},
    {"tohum": "disagree", "grup": "B", "kok": ["agree"], "icermeli": ["disagreement"]},

    # --- C: tek başına ---------------------------------------------------
    {"tohum": "meticulous", "grup": "C", "kok": ["meticulous"]},
    {"tohum": "ubiquitous", "grup": "C", "kok": ["ubiquitous"]},
    {"tohum": "candid", "grup": "C", "kok": ["candid"]},
    {"tohum": "prudent", "grup": "C", "kok": ["prudent"]},

    # --- D: ayrım --------------------------------------------------------
    {"tohum": "affect", "grup": "D", "kok": ["affect"], "icermemeli": ["effect", "effective"]},
    {"tohum": "effect", "grup": "D", "kok": ["effect"], "icermemeli": ["affect"]},
    {"tohum": "principle", "grup": "D", "kok": ["principle"], "icermemeli": ["principal"]},
    {"tohum": "compliment", "grup": "D", "kok": ["compliment"],
     "icermemeli": ["complement", "complementary"]},

    # --- E: çekim --------------------------------------------------------
    {"tohum": "boring", "grup": "E", "kok": ["bore"],
     "icermeli": ["bored", "boring"], "icermemeli": ["bores"]},
    {"tohum": "painting", "grup": "E", "kok": ["paint"],
     "icermeli": ["painting", "painter"], "icermemeli": ["painted", "paints"]},
    {"tohum": "achievement", "grup": "E", "kok": ["achieve"],
     "icermemeli": ["achieved", "achieving", "achievements"]},
    {"tohum": "argument", "grup": "E", "kok": ["argue"],
     "icermemeli": ["arguments", "argued"]},

    # --- F: uydurma ve nadir ---------------------------------------------
    {"tohum": "creative", "grup": "F", "kok": ["create"],
     "icermemeli": ["uncreatively", "creativeness"]},
    {"tohum": "harmful", "grup": "F", "kok": ["harm"],
     "icermemeli": ["unharmful", "harmfulness"]},
    {"tohum": "polite", "grup": "F", "kok": ["polite"],
     "icermeli": ["impolite", "politeness"], "icermemeli": ["impolitely"]},

    # --- G: Amerikan yazımı (tohum İngiliz yazımıyla veriliyor) -----------
    {"tohum": "colour", "grup": "G", "kok": ["color"],
     "icermemeli": ["colour", "colourful"]},
    {"tohum": "centre", "grup": "G", "kok": ["center"], "icermemeli": ["centre"]},
    {"tohum": "defence", "grup": "G", "kok": ["defend"],
     "icermeli": ["defense"], "icermemeli": ["defence"]},
]

# 3. SÜRÜM (19 Eylül). 1. ve 2. sürümle, prompt'la HİÇ kesişmeyen kelimeler.
# 2. denemenin hatalarını yeniden ölçen yerler: rely/reliable'daki kök
# beraberliği (A: predict / predictable), withdraw'daki koparan önek
# (B: outline, foresee, withhold, become), painted'daki katılım sıfatı
# (E: writing, meeting, collection, announcement).
SURUM_3 = [
    # --- A: tutarlılık ---------------------------------------------------
    {"tohum": "prediction", "grup": "A", "aile": "predict", "kok": ["predict"],
     "icermeli": ["predictable", "unpredictable"]},
    {"tohum": "unpredictable", "grup": "A", "aile": "predict", "kok": ["predict"]},
    {"tohum": "predictable", "grup": "A", "aile": "predict", "kok": ["predict"]},

    {"tohum": "hesitation", "grup": "A", "aile": "hesitate", "kok": ["hesitate"],
     "icermeli": ["hesitant"]},
    {"tohum": "hesitant", "grup": "A", "aile": "hesitate", "kok": ["hesitate"]},

    {"tohum": "unconvincing", "grup": "A", "aile": "convince", "kok": ["convince"]},
    {"tohum": "convincingly", "grup": "A", "aile": "convince", "kok": ["convince"]},

    {"tohum": "generosity", "grup": "A", "aile": "generous", "kok": ["generous"],
     "icermeli": ["generously"]},
    {"tohum": "generously", "grup": "A", "aile": "generous", "kok": ["generous"]},

    {"tohum": "weakness", "grup": "A", "aile": "weak", "kok": ["weak"],
     "icermeli": ["weaken"]},
    {"tohum": "weaken", "grup": "A", "aile": "weak", "kok": ["weak"]},

    {"tohum": "productive", "grup": "A", "aile": "produce", "kok": ["produce"],
     "icermeli": ["productivity", "unproductive"]},
    {"tohum": "productivity", "grup": "A", "aile": "produce", "kok": ["produce"]},
    {"tohum": "unproductive", "grup": "A", "aile": "produce", "kok": ["produce"]},

    {"tohum": "unfortunately", "grup": "A", "aile": "fortune", "kok": ["fortune"],
     "icermeli": ["fortunate"]},
    {"tohum": "fortunate", "grup": "A", "aile": "fortune", "kok": ["fortune"]},

    {"tohum": "pollution", "grup": "A", "aile": "pollute", "kok": ["pollute"]},
    {"tohum": "pollutant", "grup": "A", "aile": "pollute", "kok": ["pollute"]},

    {"tohum": "simplify", "grup": "A", "aile": "simple", "kok": ["simple"],
     "icermeli": ["simplicity"]},
    {"tohum": "simplicity", "grup": "A", "aile": "simple", "kok": ["simple"]},

    # --- B: önek ---------------------------------------------------------
    {"tohum": "outline", "grup": "B", "kok": ["outline"], "icermemeli": ["line"]},
    {"tohum": "foresee", "grup": "B", "kok": ["foresee"], "icermemeli": ["see"]},
    {"tohum": "withhold", "grup": "B", "kok": ["withhold"], "icermemeli": ["hold"]},
    {"tohum": "become", "grup": "B", "kok": ["become"], "icermemeli": ["come"]},
    {"tohum": "irregular", "grup": "B", "kok": ["regular"], "icermeli": ["irregularity"]},
    {"tohum": "nonexistent", "grup": "B", "kok": ["exist"], "icermeli": ["existence"]},
    {"tohum": "disappear", "grup": "B", "kok": ["appear"], "icermeli": ["appearance"]},

    # --- C: tek başına ---------------------------------------------------
    {"tohum": "ephemeral", "grup": "C", "kok": ["ephemeral"]},
    {"tohum": "gregarious", "grup": "C", "kok": ["gregarious"]},
    {"tohum": "benevolent", "grup": "C", "kok": ["benevolent"]},
    {"tohum": "frugal", "grup": "C", "kok": ["frugal"]},

    # --- D: ayrım --------------------------------------------------------
    {"tohum": "adapt", "grup": "D", "kok": ["adapt"], "icermemeli": ["adopt", "adoption"]},
    {"tohum": "adopt", "grup": "D", "kok": ["adopt"], "icermemeli": ["adapt", "adaptation"]},
    {"tohum": "precede", "grup": "D", "kok": ["precede"], "icermemeli": ["proceed"]},
    {"tohum": "proceed", "grup": "D", "kok": ["proceed"], "icermemeli": ["precede"]},

    # --- E: çekim --------------------------------------------------------
    {"tohum": "writing", "grup": "E", "kok": ["write"],
     "icermeli": ["writer", "writing"], "icermemeli": ["wrote", "writes"]},
    {"tohum": "meeting", "grup": "E", "kok": ["meet"],
     "icermeli": ["meeting"], "icermemeli": ["met", "meets"]},
    {"tohum": "collection", "grup": "E", "kok": ["collect"],
     # "collected" bilerek yok: "calm and collected" (sakin) fiilden ayrı bir
     # anlam; 3. denemede model haklıydı, beklenti yanlıştı.
     "icermemeli": ["collections", "collecting"]},
    {"tohum": "announcement", "grup": "E", "kok": ["announce"],
     "icermemeli": ["announcements", "announced", "announcing"]},

    # --- F: uydurma ve nadir ---------------------------------------------
    {"tohum": "careful", "grup": "F", "kok": ["care"],
     "icermeli": ["careless", "carefully"], "icermemeli": ["uncarefully", "carefulness"]},
    {"tohum": "hopeful", "grup": "F", "kok": ["hope"],
     "icermeli": ["hopefully"], "icermemeli": ["unhopeful", "hopefulness"]},
    {"tohum": "thankful", "grup": "F", "kok": ["thank"],
     "icermemeli": ["unthankful"]},

    # --- G: Amerikan yazımı ----------------------------------------------
    {"tohum": "favour", "grup": "G", "kok": ["favor"],
     "icermeli": ["favorite"], "icermemeli": ["favour", "favourite"]},
    {"tohum": "neighbour", "grup": "G", "kok": ["neighbor"],
     "icermeli": ["neighborhood"], "icermemeli": ["neighbour", "neighbourhood"]},
    {"tohum": "humour", "grup": "G", "kok": ["humor"],
     "icermemeli": ["humour", "humourous"]},
]

# 4. SÜRÜM (24 Eylül). 3. aşamanın (anlam + kontrolcü) ölçümü için de
# kullanılıyor: A grubu bilerek YÖN tuzaklarıyla dolu (admirable = takdire
# DEĞER, employer/employee, respectful/respectable, imaginary/imaginative,
# exhausting/exhausted); D grubu yazımı yakın çiftler. 3. sürümde kaçan
# hatalar (adoptive, favoritism, precede) bu tür hatalardı.
SURUM_4 = [
    # --- A: tutarlılık ---------------------------------------------------
    {"tohum": "admiration", "grup": "A", "aile": "admire", "kok": ["admire"],
     "icermeli": ["admirable"]},
    {"tohum": "admirable", "grup": "A", "aile": "admire", "kok": ["admire"]},

    {"tohum": "employer", "grup": "A", "aile": "employ", "kok": ["employ"],
     "icermeli": ["employee", "unemployment"]},
    {"tohum": "employee", "grup": "A", "aile": "employ", "kok": ["employ"]},
    {"tohum": "unemployment", "grup": "A", "aile": "employ", "kok": ["employ"]},

    {"tohum": "strengthen", "grup": "A", "aile": "strong", "kok": ["strong"],
     "icermeli": ["strength"]},
    {"tohum": "strength", "grup": "A", "aile": "strong", "kok": ["strong"]},

    {"tohum": "respectful", "grup": "A", "aile": "respect", "kok": ["respect"],
     "icermeli": ["respectable"]},
    {"tohum": "respectable", "grup": "A", "aile": "respect", "kok": ["respect"]},

    {"tohum": "forgiveness", "grup": "A", "aile": "forgive", "kok": ["forgive"]},
    {"tohum": "forgivable", "grup": "A", "aile": "forgive", "kok": ["forgive"]},

    {"tohum": "offensive", "grup": "A", "aile": "offend", "kok": ["offend"],
     "icermeli": ["offender"]},
    {"tohum": "offender", "grup": "A", "aile": "offend", "kok": ["offend"]},

    {"tohum": "imaginary", "grup": "A", "aile": "imagine", "kok": ["imagine"],
     "icermeli": ["imaginative", "imagination"]},
    {"tohum": "imaginative", "grup": "A", "aile": "imagine", "kok": ["imagine"]},

    {"tohum": "exhausting", "grup": "A", "aile": "exhaust", "kok": ["exhaust"],
     "icermeli": ["exhaustion"]},
    {"tohum": "exhaustion", "grup": "A", "aile": "exhaust", "kok": ["exhaust"]},

    # --- B: önek ---------------------------------------------------------
    {"tohum": "overlook", "grup": "B", "kok": ["overlook"], "icermemeli": ["look"]},
    {"tohum": "outweigh", "grup": "B", "kok": ["outweigh"], "icermemeli": ["weigh", "weight"]},
    {"tohum": "mislead", "grup": "B", "kok": ["mislead"], "icermemeli": ["lead", "leader"]},
    {"tohum": "unaware", "grup": "B", "kok": ["aware"], "icermeli": ["awareness"]},
    {"tohum": "impatient", "grup": "B", "kok": ["patient"], "icermeli": ["patience"]},
    {"tohum": "dishonest", "grup": "B", "kok": ["honest"], "icermeli": ["honesty"]},

    # --- C: tek başına ---------------------------------------------------
    {"tohum": "obsolete", "grup": "C", "kok": ["obsolete"]},
    {"tohum": "tedious", "grup": "C", "kok": ["tedious"]},
    {"tohum": "vivid", "grup": "C", "kok": ["vivid"]},
    {"tohum": "shrewd", "grup": "C", "kok": ["shrewd"]},
    {"tohum": "reluctant", "grup": "C", "kok": ["reluctant"], "icermeli": ["reluctance"]},

    # --- D: ayrım --------------------------------------------------------
    {"tohum": "eminent", "grup": "D", "kok": ["eminent"], "icermemeli": ["imminent"]},
    {"tohum": "imminent", "grup": "D", "kok": ["imminent"], "icermemeli": ["eminent"]},
    {"tohum": "loose", "grup": "D", "kok": ["loose"], "icermemeli": ["lose", "loss"]},
    {"tohum": "lose", "grup": "D", "kok": ["lose"], "icermemeli": ["loose", "loosen"]},
    {"tohum": "desert", "grup": "D", "kok": ["desert"], "icermemeli": ["dessert"]},
    {"tohum": "dessert", "grup": "D", "kok": ["dessert"], "icermemeli": ["desert"]},

    # --- E: çekim --------------------------------------------------------
    {"tohum": "gathering", "grup": "E", "kok": ["gather"],
     "icermeli": ["gathering"], "icermemeli": ["gathers", "gathered"]},
    {"tohum": "warning", "grup": "E", "kok": ["warn"],
     "icermeli": ["warning"], "icermemeli": ["warned", "warns"]},
    {"tohum": "arrangement", "grup": "E", "kok": ["arrange"],
     "icermemeli": ["arrangements", "arranging"]},
    {"tohum": "payment", "grup": "E", "kok": ["pay"],
     "icermemeli": ["payments", "paying", "pays"]},

    # --- F: uydurma ve nadir ---------------------------------------------
    {"tohum": "useful", "grup": "F", "kok": ["use"],
     "icermeli": ["useless"], "icermemeli": ["unuseful"]},
    {"tohum": "powerful", "grup": "F", "kok": ["power"],
     "icermeli": ["powerless"], "icermemeli": ["unpowerful"]},
    {"tohum": "doubtful", "grup": "F", "kok": ["doubt"],
     "icermemeli": ["undoubtful"]},
    {"tohum": "fearful", "grup": "F", "kok": ["fear"],
     "icermeli": ["fearless"], "icermemeli": ["unfearful"]},

    # --- G: Amerikan yazımı ----------------------------------------------
    {"tohum": "rumour", "grup": "G", "kok": ["rumor"],
     "icermemeli": ["rumour"]},
    {"tohum": "honour", "grup": "G", "kok": ["honor"],
     "icermeli": ["honorable"], "icermemeli": ["honour", "honourable"]},
    {"tohum": "flavour", "grup": "G", "kok": ["flavor"],
     "icermemeli": ["flavour"]},
]

# 5. SÜRÜM (24 Eylül). 4. ölçümden sonra üretici prompt'una yön, "Türkçede
# başka anlamı olan karşılık" ve "temel anlamı atlama" kuralları, kontrolcüye
# missing_meaning alanı eklendi. A grubu yine duygu sıfatlarıyla dolu
# (-ing / -ed yönü: annoying, confusing, embarrassing...) ve -er / -ee
# çiftleri (interviewer / interviewee, entertainer / attendee).
SURUM_5 = [
    # --- A: tutarlılık ---------------------------------------------------
    {"tohum": "entertaining", "grup": "A", "aile": "entertain", "kok": ["entertain"],
     "icermeli": ["entertainment", "entertainer"]},
    {"tohum": "entertainer", "grup": "A", "aile": "entertain", "kok": ["entertain"]},

    {"tohum": "annoying", "grup": "A", "aile": "annoy", "kok": ["annoy"],
     "icermeli": ["annoyance"]},
    {"tohum": "annoyance", "grup": "A", "aile": "annoy", "kok": ["annoy"]},

    {"tohum": "satisfactory", "grup": "A", "aile": "satisfy", "kok": ["satisfy"],
     "icermeli": ["satisfaction"]},
    {"tohum": "dissatisfaction", "grup": "A", "aile": "satisfy", "kok": ["satisfy"]},

    {"tohum": "attendee", "grup": "A", "aile": "attend", "kok": ["attend"],
     "icermeli": ["attendance"]},
    {"tohum": "attendance", "grup": "A", "aile": "attend", "kok": ["attend"]},

    {"tohum": "interviewee", "grup": "A", "aile": "interview", "kok": ["interview"],
     "icermeli": ["interviewer"]},
    {"tohum": "interviewer", "grup": "A", "aile": "interview", "kok": ["interview"]},

    {"tohum": "confusing", "grup": "A", "aile": "confuse", "kok": ["confuse"],
     "icermeli": ["confusion"]},
    {"tohum": "confusion", "grup": "A", "aile": "confuse", "kok": ["confuse"]},

    {"tohum": "embarrassing", "grup": "A", "aile": "embarrass", "kok": ["embarrass"],
     "icermeli": ["embarrassment"]},
    {"tohum": "embarrassment", "grup": "A", "aile": "embarrass", "kok": ["embarrass"]},

    {"tohum": "disappointing", "grup": "A", "aile": "disappoint", "kok": ["disappoint"],
     "icermeli": ["disappointment"]},
    {"tohum": "disappointment", "grup": "A", "aile": "disappoint", "kok": ["disappoint"]},

    {"tohum": "amusing", "grup": "A", "aile": "amuse", "kok": ["amuse"],
     "icermeli": ["amusement"]},
    {"tohum": "amusement", "grup": "A", "aile": "amuse", "kok": ["amuse"]},

    # --- B: önek ---------------------------------------------------------
    {"tohum": "outgrow", "grup": "B", "kok": ["outgrow"], "icermemeli": ["grow", "growth"]},
    {"tohum": "overthrow", "grup": "B", "kok": ["overthrow"], "icermemeli": ["throw"]},
    {"tohum": "unkind", "grup": "B", "kok": ["kind"], "icermeli": ["kindness"]},
    {"tohum": "irresponsible", "grup": "B", "kok": ["responsible"],
     "icermeli": ["responsibility"]},
    {"tohum": "uncertain", "grup": "B", "kok": ["certain"], "icermeli": ["certainty"]},

    # --- C: tek başına ---------------------------------------------------
    {"tohum": "stubborn", "grup": "C", "kok": ["stubborn"]},
    {"tohum": "arrogant", "grup": "C", "kok": ["arrogant"], "icermeli": ["arrogance"]},
    {"tohum": "fragile", "grup": "C", "kok": ["fragile"]},
    {"tohum": "vague", "grup": "C", "kok": ["vague"]},

    # --- D: ayrım --------------------------------------------------------
    {"tohum": "moral", "grup": "D", "kok": ["moral"], "icermemeli": ["morale"]},
    {"tohum": "morale", "grup": "D", "kok": ["morale"], "icermemeli": ["moral", "morality"]},
    {"tohum": "council", "grup": "D", "kok": ["council"], "icermemeli": ["counsel"]},
    {"tohum": "counsel", "grup": "D", "kok": ["counsel"], "icermemeli": ["council"]},
    {"tohum": "accept", "grup": "D", "kok": ["accept"], "icermemeli": ["except"]},
    {"tohum": "except", "grup": "D", "kok": ["except"], "icermemeli": ["accept"]},

    # --- E: çekim --------------------------------------------------------
    {"tohum": "finding", "grup": "E", "kok": ["find"],
     "icermeli": ["finding"], "icermemeli": ["finds"]},
    {"tohum": "setting", "grup": "E", "kok": ["set"],
     "icermeli": ["setting"], "icermemeli": ["sets"]},
    {"tohum": "shipment", "grup": "E", "kok": ["ship"],
     "icermemeli": ["shipments", "ships"]},
    {"tohum": "treatment", "grup": "E", "kok": ["treat"],
     "icermemeli": ["treatments", "treating"]},

    # --- F: uydurma ve nadir ---------------------------------------------
    {"tohum": "playful", "grup": "F", "kok": ["play"],
     "icermeli": ["player"], "icermemeli": ["unplayful"]},
    {"tohum": "restful", "grup": "F", "kok": ["rest"],
     "icermeli": ["restless"], "icermemeli": ["unrestful"]},
    {"tohum": "tasteful", "grup": "F", "kok": ["taste"],
     "icermeli": ["tasteless"], "icermemeli": ["untasteful"]},
    {"tohum": "painful", "grup": "F", "kok": ["pain"],
     "icermeli": ["painless"], "icermemeli": ["unpainful"]},

    # --- G: Amerikan yazımı ----------------------------------------------
    {"tohum": "jewellery", "grup": "G", "kok": ["jewelry"],
     "icermemeli": ["jewellery"]},
    {"tohum": "catalogue", "grup": "G", "kok": ["catalog"],
     "icermemeli": ["catalogue"]},
    {"tohum": "apologise", "grup": "G", "kok": ["apologize"],
     "icermeli": ["apology"], "icermemeli": ["apologise"]},
    {"tohum": "licence", "grup": "G", "kok": ["license"],
     "icermemeli": ["licence"]},
]

# 6. SÜRÜM (24 Eylül). Claude'un kendi yürüttüğü ilk ölçüm. Parantez temizliği,
# cümlesiz anlamın yeniden üretimi, sözlük korumalı silme ve LLM_PROVIDER_SORT=price
# ile. A grubu yine yön tuzaklı (exciting / tempting / inspiring).
SURUM_6 = [
    {'tohum': 'exciting', 'grup': 'A', 'aile': 'excite', 'kok': ['excite'], 'icermeli': ['excitement']},
    {'tohum': 'excitement', 'grup': 'A', 'aile': 'excite', 'kok': ['excite']},
    {'tohum': 'hostility', 'grup': 'A', 'aile': 'hostile', 'kok': ['hostile']},
    {'tohum': 'hostile', 'grup': 'A', 'aile': 'hostile', 'kok': ['hostile']},
    {'tohum': 'curiosity', 'grup': 'A', 'aile': 'curious', 'kok': ['curious']},
    {'tohum': 'curious', 'grup': 'A', 'aile': 'curious', 'kok': ['curious']},
    {'tohum': 'persistence', 'grup': 'A', 'aile': 'persist', 'kok': ['persist'], 'icermeli': ['persistent']},
    {'tohum': 'persistent', 'grup': 'A', 'aile': 'persist', 'kok': ['persist']},
    {'tohum': 'competitive', 'grup': 'A', 'aile': 'compete', 'kok': ['compete'], 'icermeli': ['competition', 'competitor']},
    {'tohum': 'competitor', 'grup': 'A', 'aile': 'compete', 'kok': ['compete']},
    {'tohum': 'tempting', 'grup': 'A', 'aile': 'tempt', 'kok': ['tempt'], 'icermeli': ['temptation']},
    {'tohum': 'temptation', 'grup': 'A', 'aile': 'tempt', 'kok': ['tempt']},
    {'tohum': 'inspiring', 'grup': 'A', 'aile': 'inspire', 'kok': ['inspire'], 'icermeli': ['inspiration']},
    {'tohum': 'inspiration', 'grup': 'A', 'aile': 'inspire', 'kok': ['inspire']},
    {'tohum': 'frustrating', 'grup': 'A', 'aile': 'frustrate', 'kok': ['frustrate'], 'icermeli': ['frustration']},
    {'tohum': 'frustration', 'grup': 'A', 'aile': 'frustrate', 'kok': ['frustrate']},
    {'tohum': 'overwhelming', 'grup': 'B', 'kok': ['overwhelm'], 'icermemeli': ['whelm']},
    {'tohum': 'overhear', 'grup': 'B', 'kok': ['overhear'], 'icermemeli': ['hear', 'hearing']},
    {'tohum': 'outlive', 'grup': 'B', 'kok': ['outlive'], 'icermemeli': ['live', 'life']},
    {'tohum': 'disobey', 'grup': 'B', 'kok': ['obey'], 'icermeli': ['obedience']},
    {'tohum': 'immature', 'grup': 'B', 'kok': ['mature'], 'icermeli': ['maturity']},
    {'tohum': 'inaccessible', 'grup': 'B', 'kok': ['access'], 'icermeli': ['accessible']},
    {'tohum': 'reckless', 'grup': 'C', 'kok': ['reckless']},
    {'tohum': 'feasible', 'grup': 'C', 'kok': ['feasible'], 'icermeli': ['feasibility']},
    {'tohum': 'brittle', 'grup': 'C', 'kok': ['brittle']},
    {'tohum': 'dubious', 'grup': 'C', 'kok': ['dubious']},
    {'tohum': 'vulnerable', 'grup': 'C', 'kok': ['vulnerable'], 'icermeli': ['vulnerability']},
    {'tohum': 'outspoken', 'grup': 'C', 'kok': ['outspoken'], 'icermemeli': ['speak']},
    {'tohum': 'discreet', 'grup': 'D', 'kok': ['discreet'], 'icermemeli': ['discrete']},
    {'tohum': 'discrete', 'grup': 'D', 'kok': ['discrete'], 'icermemeli': ['discreet', 'discretion']},
    {'tohum': 'elicit', 'grup': 'D', 'kok': ['elicit'], 'icermemeli': ['illicit']},
    {'tohum': 'illicit', 'grup': 'D', 'kok': ['illicit'], 'icermemeli': ['elicit']},
    {'tohum': 'ensure', 'grup': 'D', 'kok': ['ensure'], 'icermemeli': ['insure', 'insurance']},
    {'tohum': 'insure', 'grup': 'D', 'kok': ['insure'], 'icermemeli': ['ensure']},
    {'tohum': 'crossing', 'grup': 'E', 'kok': ['cross'], 'icermeli': ['crossing'], 'icermemeli': ['crossed', 'crosses']},
    {'tohum': 'beginning', 'grup': 'E', 'kok': ['begin'], 'icermeli': ['beginning', 'beginner'], 'icermemeli': ['began', 'begun']},
    {'tohum': 'swimming', 'grup': 'E', 'kok': ['swim'], 'icermeli': ['swimmer'], 'icermemeli': ['swam', 'swum']},
    {'tohum': 'suffering', 'grup': 'E', 'kok': ['suffer'], 'icermeli': ['suffering'], 'icermemeli': ['suffered', 'suffers']},
    {'tohum': 'cheerful', 'grup': 'F', 'kok': ['cheer'], 'icermemeli': ['uncheerful']},
    {'tohum': 'faithful', 'grup': 'F', 'kok': ['faith'], 'icermeli': ['unfaithful']},
    {'tohum': 'stressful', 'grup': 'F', 'kok': ['stress'], 'icermemeli': ['unstressful']},
    {'tohum': 'wasteful', 'grup': 'F', 'kok': ['waste'], 'icermemeli': ['unwasteful']},
    {'tohum': 'programme', 'grup': 'G', 'kok': ['program'], 'icermemeli': ['programme']},
    {'tohum': 'grey', 'grup': 'G', 'kok': ['gray'], 'icermemeli': ['grey']},
    {'tohum': 'moustache', 'grup': 'G', 'kok': ['mustache'], 'icermemeli': ['moustache']},
]

# 7. SÜRÜM (24 Eylül). 6. ölçümün tekrarı: sonuç tesadüf mü? Kontrolcü
# önbelleği (cache_control) ve üretici fiyat tavanıyla.
SURUM_7 = [
    {'tohum': 'admission', 'grup': 'A', 'aile': 'admit', 'kok': ['admit']},
    {'tohum': 'admittance', 'grup': 'A', 'aile': 'admit', 'kok': ['admit']},
    {'tohum': 'appreciative', 'grup': 'A', 'aile': 'appreciate', 'kok': ['appreciate'], 'icermeli': ['appreciation']},
    {'tohum': 'appreciation', 'grup': 'A', 'aile': 'appreciate', 'kok': ['appreciate']},
    {'tohum': 'resentful', 'grup': 'A', 'aile': 'resent', 'kok': ['resent'], 'icermeli': ['resentment']},
    {'tohum': 'resentment', 'grup': 'A', 'aile': 'resent', 'kok': ['resent']},
    {'tohum': 'deceptive', 'grup': 'A', 'aile': 'deceive', 'kok': ['deceive'], 'icermeli': ['deception']},
    {'tohum': 'deception', 'grup': 'A', 'aile': 'deceive', 'kok': ['deceive']},
    {'tohum': 'irritating', 'grup': 'A', 'aile': 'irritate', 'kok': ['irritate'], 'icermeli': ['irritation']},
    {'tohum': 'irritation', 'grup': 'A', 'aile': 'irritate', 'kok': ['irritate']},
    {'tohum': 'reassuring', 'grup': 'A', 'aile': 'reassure', 'kok': ['reassure'], 'icermeli': ['reassurance']},
    {'tohum': 'reassurance', 'grup': 'A', 'aile': 'reassure', 'kok': ['reassure']},
    {'tohum': 'respondent', 'grup': 'A', 'aile': 'respond', 'kok': ['respond'], 'icermeli': ['response']},
    {'tohum': 'response', 'grup': 'A', 'aile': 'respond', 'kok': ['respond']},
    {'tohum': 'enforceable', 'grup': 'A', 'aile': 'enforce', 'kok': ['enforce'], 'icermeli': ['enforcement']},
    {'tohum': 'enforcement', 'grup': 'A', 'aile': 'enforce', 'kok': ['enforce']},
    {'tohum': 'negotiator', 'grup': 'A', 'aile': 'negotiate', 'kok': ['negotiate'], 'icermeli': ['negotiation']},
    {'tohum': 'negotiation', 'grup': 'A', 'aile': 'negotiate', 'kok': ['negotiate']},
    {'tohum': 'outperform', 'grup': 'B', 'kok': ['outperform'], 'icermemeli': ['perform', 'performance']},
    {'tohum': 'disapprove', 'grup': 'B', 'kok': ['approve'], 'icermeli': ['approval']},
    {'tohum': 'irrational', 'grup': 'B', 'kok': ['rational'], 'icermeli': ['rationally']},
    {'tohum': 'uncommon', 'grup': 'B', 'kok': ['common'], 'icermeli': ['commonly']},
    {'tohum': 'nonverbal', 'grup': 'B', 'kok': ['verbal'], 'icermeli': ['verbally']},
    {'tohum': 'cunning', 'grup': 'C', 'kok': ['cunning']},
    {'tohum': 'eloquent', 'grup': 'C', 'kok': ['eloquent'], 'icermeli': ['eloquence']},
    {'tohum': 'tangible', 'grup': 'C', 'kok': ['tangible']},
    {'tohum': 'mundane', 'grup': 'C', 'kok': ['mundane']},
    {'tohum': 'lenient', 'grup': 'C', 'kok': ['lenient']},
    {'tohum': 'adverse', 'grup': 'D', 'kok': ['adverse'], 'icermemeli': ['averse']},
    {'tohum': 'averse', 'grup': 'D', 'kok': ['averse'], 'icermemeli': ['adverse', 'adversity']},
    {'tohum': 'emigrate', 'grup': 'D', 'kok': ['emigrate'], 'icermemeli': ['immigrate', 'immigrant']},
    {'tohum': 'immigrate', 'grup': 'D', 'kok': ['immigrate'], 'icermemeli': ['emigrate', 'emigrant']},
    {'tohum': 'flaunt', 'grup': 'D', 'kok': ['flaunt'], 'icermemeli': ['flout']},
    {'tohum': 'flout', 'grup': 'D', 'kok': ['flout'], 'icermemeli': ['flaunt']},
    {'tohum': 'hunting', 'grup': 'E', 'kok': ['hunt'], 'icermeli': ['hunter'], 'icermemeli': ['hunted', 'hunts']},
    {'tohum': 'washing', 'grup': 'E', 'kok': ['wash'], 'icermemeli': ['washed', 'washes']},
    {'tohum': 'fishing', 'grup': 'E', 'kok': ['fish'], 'icermemeli': ['fished', 'fishes']},
    {'tohum': 'baking', 'grup': 'E', 'kok': ['bake'], 'icermeli': ['baker'], 'icermemeli': ['baked', 'bakes']},
    {'tohum': 'boastful', 'grup': 'F', 'kok': ['boast'], 'icermemeli': ['unboastful']},
    {'tohum': 'resourceful', 'grup': 'F', 'kok': ['resource'], 'icermemeli': ['unresourceful']},
    {'tohum': 'shameful', 'grup': 'F', 'kok': ['shame'], 'icermeli': ['shameless'], 'icermemeli': ['unshameful']},
    {'tohum': 'tactful', 'grup': 'F', 'kok': ['tact'], 'icermeli': ['tactless'], 'icermemeli': ['untactful']},
    {'tohum': 'plough', 'grup': 'G', 'kok': ['plow'], 'icermemeli': ['plough']},
    {'tohum': 'sceptical', 'grup': 'G', 'kok': ['skeptic'], 'icermeli': ['skeptical'], 'icermemeli': ['sceptical']},
    {'tohum': 'manoeuvre', 'grup': 'G', 'kok': ['maneuver'], 'icermemeli': ['manoeuvre']},
]

# 8-10. SÜRÜM (24 Eylül). Efe'nin hedefi: 500 kelimede hata %0.8-1'in altında.
# Üç liste birlikte ~500 kelime veriyor. Kontrolcü: fiyat sıralaması + önbellek.
SURUM_8 = [
    {'tohum': 'absorption', 'grup': 'A', 'aile': 'absorb', 'kok': ['absorb'], 'icermeli': ['absorbent']},
    {'tohum': 'absorbent', 'grup': 'A', 'aile': 'absorb', 'kok': ['absorb']},
    {'tohum': 'accusation', 'grup': 'A', 'aile': 'accuse', 'kok': ['accuse']},
    {'tohum': 'accused', 'grup': 'A', 'aile': 'accuse', 'kok': ['accuse']},
    {'tohum': 'betrayal', 'grup': 'A', 'aile': 'betray', 'kok': ['betray']},
    {'tohum': 'betray', 'grup': 'A', 'aile': 'betray', 'kok': ['betray']},
    {'tohum': 'coincidence', 'grup': 'A', 'aile': 'coincide', 'kok': ['coincide'], 'icermeli': ['coincidental']},
    {'tohum': 'coincidental', 'grup': 'A', 'aile': 'coincide', 'kok': ['coincide']},
    {'tohum': 'dominance', 'grup': 'A', 'aile': 'dominate', 'kok': ['dominate'], 'icermeli': ['dominant']},
    {'tohum': 'dominant', 'grup': 'A', 'aile': 'dominate', 'kok': ['dominate']},
    {'tohum': 'endurance', 'grup': 'A', 'aile': 'endure', 'kok': ['endure']},
    {'tohum': 'endurable', 'grup': 'A', 'aile': 'endure', 'kok': ['endure']},
    {'tohum': 'imitation', 'grup': 'A', 'aile': 'imitate', 'kok': ['imitate'], 'icermeli': ['imitator']},
    {'tohum': 'imitator', 'grup': 'A', 'aile': 'imitate', 'kok': ['imitate']},
    {'tohum': 'obsession', 'grup': 'A', 'aile': 'obsess', 'kok': ['obsess'], 'icermeli': ['obsessive']},
    {'tohum': 'obsessive', 'grup': 'A', 'aile': 'obsess', 'kok': ['obsess']},
    {'tohum': 'prevention', 'grup': 'A', 'aile': 'prevent', 'kok': ['prevent'], 'icermeli': ['preventive']},
    {'tohum': 'preventive', 'grup': 'A', 'aile': 'prevent', 'kok': ['prevent']},
    {'tohum': 'overturn', 'grup': 'B', 'kok': ['overturn'], 'icermemeli': ['turn']},
    {'tohum': 'unfold', 'grup': 'B', 'kok': ['unfold'], 'icermemeli': ['fold']},
    {'tohum': 'discontinue', 'grup': 'B', 'kok': ['continue'], 'icermeli': ['continuous']},
    {'tohum': 'impractical', 'grup': 'B', 'kok': ['practical'], 'icermeli': ['practically']},
    {'tohum': 'illiterate', 'grup': 'B', 'kok': ['literate'], 'icermeli': ['literacy']},
    {'tohum': 'serene', 'grup': 'C', 'kok': ['serene']},
    {'tohum': 'blatant', 'grup': 'C', 'kok': ['blatant']},
    {'tohum': 'ruthless', 'grup': 'C', 'kok': ['ruthless']},
    {'tohum': 'frivolous', 'grup': 'C', 'kok': ['frivolous']},
    {'tohum': 'obscure', 'grup': 'C', 'kok': ['obscure'], 'icermeli': ['obscurity']},
    {'tohum': 'censor', 'grup': 'D', 'kok': ['censor'], 'icermemeli': ['censure']},
    {'tohum': 'censure', 'grup': 'D', 'kok': ['censure'], 'icermemeli': ['censor', 'censorship']},
    {'tohum': 'illusion', 'grup': 'D', 'kok': ['illusion'], 'icermemeli': ['allusion']},
    {'tohum': 'allusion', 'grup': 'D', 'kok': ['allusion'], 'icermemeli': ['illusion']},
    {'tohum': 'loath', 'grup': 'D', 'kok': ['loath'], 'icermemeli': ['loathe']},
    {'tohum': 'loathe', 'grup': 'D', 'kok': ['loathe'], 'icermemeli': ['loath']},
    {'tohum': 'gardening', 'grup': 'E', 'kok': ['garden'], 'icermeli': ['gardener'], 'icermemeli': ['gardened']},
    {'tohum': 'sailing', 'grup': 'E', 'kok': ['sail'], 'icermeli': ['sailor'], 'icermemeli': ['sailed']},
    {'tohum': 'planning', 'grup': 'E', 'kok': ['plan'], 'icermeli': ['planner'], 'icermemeli': ['planned', 'plans']},
    {'tohum': 'recording', 'grup': 'E', 'kok': ['record'], 'icermeli': ['recording'], 'icermemeli': ['recorded']},
    {'tohum': 'fruitful', 'grup': 'F', 'kok': ['fruit'], 'icermeli': ['fruitless'], 'icermemeli': ['unfruitful']},
    {'tohum': 'joyful', 'grup': 'F', 'kok': ['joy'], 'icermeli': ['joyless'], 'icermemeli': ['unjoyful']},
    {'tohum': 'fateful', 'grup': 'F', 'kok': ['fate'], 'icermemeli': ['unfateful']},
    {'tohum': 'spiteful', 'grup': 'F', 'kok': ['spite'], 'icermemeli': ['unspiteful']},
    {'tohum': 'sulphur', 'grup': 'G', 'kok': ['sulfur'], 'icermemeli': ['sulphur']},
    {'tohum': 'cosy', 'grup': 'G', 'kok': ['cozy'], 'icermemeli': ['cosy']},
    {'tohum': 'pyjamas', 'grup': 'G', 'kok': ['pajamas'], 'icermemeli': ['pyjamas']},
]

SURUM_9 = [
    {'tohum': 'exaggeration', 'grup': 'A', 'aile': 'exaggerate', 'kok': ['exaggerate']},
    {'tohum': 'exaggerated', 'grup': 'A', 'aile': 'exaggerate', 'kok': ['exaggerate']},
    {'tohum': 'humiliating', 'grup': 'A', 'aile': 'humiliate', 'kok': ['humiliate'], 'icermeli': ['humiliation']},
    {'tohum': 'humiliation', 'grup': 'A', 'aile': 'humiliate', 'kok': ['humiliate']},
    {'tohum': 'intimidating', 'grup': 'A', 'aile': 'intimidate', 'kok': ['intimidate'], 'icermeli': ['intimidation']},
    {'tohum': 'intimidation', 'grup': 'A', 'aile': 'intimidate', 'kok': ['intimidate']},
    {'tohum': 'manipulative', 'grup': 'A', 'aile': 'manipulate', 'kok': ['manipulate'], 'icermeli': ['manipulation']},
    {'tohum': 'manipulation', 'grup': 'A', 'aile': 'manipulate', 'kok': ['manipulate']},
    {'tohum': 'provocative', 'grup': 'A', 'aile': 'provoke', 'kok': ['provoke'], 'icermeli': ['provocation']},
    {'tohum': 'provocation', 'grup': 'A', 'aile': 'provoke', 'kok': ['provoke']},
    {'tohum': 'restoration', 'grup': 'A', 'aile': 'restore', 'kok': ['restore']},
    {'tohum': 'restorative', 'grup': 'A', 'aile': 'restore', 'kok': ['restore']},
    {'tohum': 'ventilation', 'grup': 'A', 'aile': 'ventilate', 'kok': ['ventilate'], 'icermeli': ['ventilator']},
    {'tohum': 'ventilator', 'grup': 'A', 'aile': 'ventilate', 'kok': ['ventilate']},
    {'tohum': 'violation', 'grup': 'A', 'aile': 'violate', 'kok': ['violate'], 'icermeli': ['violator']},
    {'tohum': 'violator', 'grup': 'A', 'aile': 'violate', 'kok': ['violate']},
    {'tohum': 'eruption', 'grup': 'A', 'aile': 'erupt', 'kok': ['erupt']},
    {'tohum': 'outsmart', 'grup': 'B', 'kok': ['outsmart'], 'icermemeli': ['smart']},
    {'tohum': 'overdue', 'grup': 'B', 'kok': ['overdue'], 'icermemeli': ['due']},
    {'tohum': 'unwind', 'grup': 'B', 'kok': ['unwind'], 'icermemeli': ['wind']},
    {'tohum': 'inconsistent', 'grup': 'B', 'kok': ['consistent'], 'icermeli': ['consistency']},
    {'tohum': 'unaffordable', 'grup': 'B', 'kok': ['afford'], 'icermeli': ['affordable']},
    {'tohum': 'haughty', 'grup': 'C', 'kok': ['haughty']},
    {'tohum': 'nimble', 'grup': 'C', 'kok': ['nimble']},
    {'tohum': 'tenacious', 'grup': 'C', 'kok': ['tenacious'], 'icermeli': ['tenacity']},
    {'tohum': 'gullible', 'grup': 'C', 'kok': ['gullible']},
    {'tohum': 'aloof', 'grup': 'C', 'kok': ['aloof']},
    {'tohum': 'ingenious', 'grup': 'D', 'kok': ['ingenious'], 'icermemeli': ['ingenuous']},
    {'tohum': 'ingenuous', 'grup': 'D', 'kok': ['ingenuous'], 'icermemeli': ['ingenious', 'ingenuity']},
    {'tohum': 'wander', 'grup': 'D', 'kok': ['wander'], 'icermemeli': ['wonder']},
    {'tohum': 'wonder', 'grup': 'D', 'kok': ['wonder'], 'icermemeli': ['wander']},
    {'tohum': 'breath', 'grup': 'D', 'kok': ['breath'], 'icermemeli': ['breathe']},
    {'tohum': 'breathe', 'grup': 'D', 'kok': ['breathe']},
    {'tohum': 'carving', 'grup': 'E', 'kok': ['carve'], 'icermeli': ['carving'], 'icermemeli': ['carved']},
    {'tohum': 'sewing', 'grup': 'E', 'kok': ['sew'], 'icermeli': ['sewing'], 'icermemeli': ['sewed', 'sewn']},
    {'tohum': 'landing', 'grup': 'E', 'kok': ['land'], 'icermeli': ['landing'], 'icermemeli': ['landed']},
    {'tohum': 'suspension', 'grup': 'E', 'kok': ['suspend'], 'icermeli': ['suspension'], 'icermemeli': ['suspends']},
    {'tohum': 'tearful', 'grup': 'F', 'kok': ['tear'], 'icermemeli': ['untearful']},
    {'tohum': 'youthful', 'grup': 'F', 'kok': ['youth'], 'icermemeli': ['unyouthful']},
    {'tohum': 'hateful', 'grup': 'F', 'kok': ['hate'], 'icermemeli': ['unhateful']},
    {'tohum': 'merciful', 'grup': 'F', 'kok': ['mercy'], 'icermeli': ['merciless']},
    {'tohum': 'sombre', 'grup': 'G', 'kok': ['somber'], 'icermemeli': ['sombre']},
    {'tohum': 'mould', 'grup': 'G', 'kok': ['mold'], 'icermemeli': ['mould']},
    {'tohum': 'paediatric', 'grup': 'G', 'kok': ['pediatric'], 'icermemeli': ['paediatric']},
    {'tohum': 'enrol', 'grup': 'G', 'kok': ['enroll'], 'icermeli': ['enrollment'], 'icermemeli': ['enrol']},
]

SURUM_10 = [
    {'tohum': 'contamination', 'grup': 'A', 'aile': 'contaminate', 'kok': ['contaminate'], 'icermeli': ['contaminant']},
    {'tohum': 'contaminant', 'grup': 'A', 'aile': 'contaminate', 'kok': ['contaminate']},
    {'tohum': 'distraction', 'grup': 'A', 'aile': 'distract', 'kok': ['distract'], 'icermeli': ['distracting']},
    {'tohum': 'distracting', 'grup': 'A', 'aile': 'distract', 'kok': ['distract']},
    {'tohum': 'donation', 'grup': 'A', 'aile': 'donate', 'kok': ['donate'], 'icermeli': ['donor']},
    {'tohum': 'donor', 'grup': 'A', 'aile': 'donate', 'kok': ['donate']},
    {'tohum': 'fascinating', 'grup': 'A', 'aile': 'fascinate', 'kok': ['fascinate'], 'icermeli': ['fascination']},
    {'tohum': 'fascination', 'grup': 'A', 'aile': 'fascinate', 'kok': ['fascinate']},
    {'tohum': 'interruption', 'grup': 'A', 'aile': 'interrupt', 'kok': ['interrupt']},
    {'tohum': 'investor', 'grup': 'A', 'aile': 'invest', 'kok': ['invest'], 'icermeli': ['investment']},
    {'tohum': 'investment', 'grup': 'A', 'aile': 'invest', 'kok': ['invest']},
    {'tohum': 'isolation', 'grup': 'A', 'aile': 'isolate', 'kok': ['isolate']},
    {'tohum': 'rejection', 'grup': 'A', 'aile': 'reject', 'kok': ['reject']},
    {'tohum': 'elimination', 'grup': 'A', 'aile': 'eliminate', 'kok': ['eliminate']},
    {'tohum': 'overshadow', 'grup': 'B', 'kok': ['overshadow'], 'icermemeli': ['shadow']},
    {'tohum': 'unfit', 'grup': 'B', 'kok': ['fit'], 'icermeli': ['fitness']},
    {'tohum': 'disproportionate', 'grup': 'B', 'kok': ['proportion'], 'icermeli': ['proportional']},
    {'tohum': 'immobile', 'grup': 'B', 'kok': ['mobile'], 'icermeli': ['mobility']},
    {'tohum': 'invisible', 'grup': 'B', 'kok': ['visible'], 'icermeli': ['visibility']},
    {'tohum': 'sluggish', 'grup': 'C', 'kok': ['sluggish']},
    {'tohum': 'vibrant', 'grup': 'C', 'kok': ['vibrant']},
    {'tohum': 'ominous', 'grup': 'C', 'kok': ['ominous']},
    {'tohum': 'lavish', 'grup': 'C', 'kok': ['lavish']},
    {'tohum': 'earnest', 'grup': 'C', 'kok': ['earnest']},
    {'tohum': 'personal', 'grup': 'D', 'kok': ['personal'], 'icermemeli': ['personnel']},
    {'tohum': 'personnel', 'grup': 'D', 'kok': ['personnel'], 'icermemeli': ['personal']},
    {'tohum': 'addition', 'grup': 'D', 'kok': ['add'], 'icermemeli': ['edition']},
    {'tohum': 'edition', 'grup': 'D', 'kok': ['edition'], 'icermemeli': ['addition']},
    {'tohum': 'quiet', 'grup': 'D', 'kok': ['quiet'], 'icermemeli': ['quite']},
    {'tohum': 'quite', 'grup': 'D', 'kok': ['quite'], 'icermemeli': ['quiet']},
    {'tohum': 'dwelling', 'grup': 'E', 'kok': ['dwell'], 'icermeli': ['dwelling'], 'icermemeli': ['dwelt', 'dwells']},
    {'tohum': 'coaching', 'grup': 'E', 'kok': ['coach'], 'icermeli': ['coaching'], 'icermemeli': ['coached']},
    {'tohum': 'farming', 'grup': 'E', 'kok': ['farm'], 'icermeli': ['farmer'], 'icermemeli': ['farmed']},
    {'tohum': 'boarding', 'grup': 'E', 'kok': ['board'], 'icermeli': ['boarding'], 'icermemeli': ['boarded']},
    {'tohum': 'pitiful', 'grup': 'F', 'kok': ['pity'], 'icermeli': ['pitiless'], 'icermemeli': ['unpitiful']},
    {'tohum': 'sorrowful', 'grup': 'F', 'kok': ['sorrow'], 'icermemeli': ['unsorrowful']},
    {'tohum': 'eventful', 'grup': 'F', 'kok': ['event'], 'icermeli': ['uneventful']},
    {'tohum': 'dreadful', 'grup': 'F', 'kok': ['dread'], 'icermemeli': ['undreadful']},
    {'tohum': 'savour', 'grup': 'G', 'kok': ['savor'], 'icermemeli': ['savour']},
    {'tohum': 'armour', 'grup': 'G', 'kok': ['armor'], 'icermemeli': ['armour']},
    {'tohum': 'vigour', 'grup': 'G', 'kok': ['vigor'], 'icermemeli': ['vigour']},
    {'tohum': 'harbour', 'grup': 'G', 'kok': ['harbor'], 'icermemeli': ['harbour']},
    {'tohum': 'odour', 'grup': 'G', 'kok': ['odor'], 'icermemeli': ['odour']},
]

SURUMLER = {"2": SURUM_2, "3": SURUM_3, "4": SURUM_4, "5": SURUM_5, "6": SURUM_6, "7": SURUM_7,
            "8": SURUM_8, "9": SURUM_9, "10": SURUM_10}

# 11. SÜRÜM: 8-10'dan sonraki düzeltmelerle (tanım parçası atma, yön/isim örnekleri)
# 500 kelimeyi tamamlayan doğrulama listesi.
SURUM_11 = [
    {'tohum': 'abolition', 'grup': 'A', 'aile': 'abolish', 'kok': ['abolish'], 'icermeli': ['abolitionist']},
    {'tohum': 'abolitionist', 'grup': 'A', 'aile': 'abolish', 'kok': ['abolish']},
    {'tohum': 'assertive', 'grup': 'A', 'aile': 'assert', 'kok': ['assert'], 'icermeli': ['assertion']},
    {'tohum': 'assertion', 'grup': 'A', 'aile': 'assert', 'kok': ['assert']},
    {'tohum': 'assessor', 'grup': 'A', 'aile': 'assess', 'kok': ['assess'], 'icermeli': ['assessment']},
    {'tohum': 'assessment', 'grup': 'A', 'aile': 'assess', 'kok': ['assess']},
    {'tohum': 'captivating', 'grup': 'A', 'aile': 'captivate', 'kok': ['captivate']},
    {'tohum': 'cooperative', 'grup': 'A', 'aile': 'cooperate', 'kok': ['cooperate'], 'icermeli': ['cooperation']},
    {'tohum': 'cooperation', 'grup': 'A', 'aile': 'cooperate', 'kok': ['cooperate']},
    {'tohum': 'deprivation', 'grup': 'A', 'aile': 'deprive', 'kok': ['deprive'], 'icermeli': ['deprived']},
    {'tohum': 'deprived', 'grup': 'A', 'aile': 'deprive', 'kok': ['deprive']},
    {'tohum': 'empathetic', 'grup': 'A', 'aile': 'empathy', 'kok': ['empathy'], 'icermeli': ['empathize']},
    {'tohum': 'empathize', 'grup': 'A', 'aile': 'empathy', 'kok': ['empathy']},
    {'tohum': 'forgery', 'grup': 'A', 'aile': 'forge', 'kok': ['forge'], 'icermeli': ['forger']},
    {'tohum': 'forger', 'grup': 'A', 'aile': 'forge', 'kok': ['forge']},
    {'tohum': 'hazardous', 'grup': 'A', 'aile': 'hazard', 'kok': ['hazard']},
    {'tohum': 'informant', 'grup': 'A', 'aile': 'inform', 'kok': ['inform'], 'icermeli': ['informative']},
    {'tohum': 'informative', 'grup': 'A', 'aile': 'inform', 'kok': ['inform']},
    {'tohum': 'liberation', 'grup': 'A', 'aile': 'liberate', 'kok': ['liberate'], 'icermeli': ['liberator']},
    {'tohum': 'liberator', 'grup': 'A', 'aile': 'liberate', 'kok': ['liberate']},
    {'tohum': 'articulation', 'grup': 'A', 'aile': 'articulate', 'kok': ['articulate']},
    {'tohum': 'disposal', 'grup': 'A', 'aile': 'dispose', 'kok': ['dispose']},
    {'tohum': 'unravel', 'grup': 'B', 'kok': ['unravel'], 'icermemeli': ['ravel']},
    {'tohum': 'impartial', 'grup': 'B', 'kok': ['partial'], 'icermeli': ['impartiality']},
    {'tohum': 'nonprofit', 'grup': 'B', 'kok': ['profit'], 'icermeli': ['profitable']},
    {'tohum': 'irreversible', 'grup': 'B', 'kok': ['reverse'], 'icermeli': ['reversible']},
    {'tohum': 'implausible', 'grup': 'B', 'kok': ['plausible'], 'icermeli': ['plausibility']},
    {'tohum': 'pragmatic', 'grup': 'C', 'kok': ['pragmatic']},
    {'tohum': 'affluent', 'grup': 'C', 'kok': ['affluent'], 'icermeli': ['affluence']},
    {'tohum': 'fragrant', 'grup': 'C', 'kok': ['fragrant'], 'icermeli': ['fragrance']},
    {'tohum': 'complacent', 'grup': 'D', 'kok': ['complacent'], 'icermemeli': ['complaisant']},
    {'tohum': 'complaisant', 'grup': 'D', 'kok': ['complaisant'], 'icermemeli': ['complacent']},
    {'tohum': 'flair', 'grup': 'D', 'kok': ['flair'], 'icermemeli': ['flare']},
    {'tohum': 'flare', 'grup': 'D', 'kok': ['flare'], 'icermemeli': ['flair']},
    {'tohum': 'cite', 'grup': 'D', 'kok': ['cite'], 'icermemeli': ['site']},
    {'tohum': 'site', 'grup': 'D', 'kok': ['site'], 'icermemeli': ['cite', 'citation']},
    {'tohum': 'bathing', 'grup': 'E', 'kok': ['bathe'], 'icermeli': ['bathing'], 'icermemeli': ['bathed', 'bathes']},
    {'tohum': 'knitting', 'grup': 'E', 'kok': ['knit'], 'icermeli': ['knitting'], 'icermemeli': ['knits']},
    {'tohum': 'weaving', 'grup': 'E', 'kok': ['weave'], 'icermeli': ['weaver'], 'icermemeli': ['wove']},
    {'tohum': 'graceful', 'grup': 'F', 'kok': ['grace'], 'icermeli': ['graceless']},
    {'tohum': 'mournful', 'grup': 'F', 'kok': ['mourn'], 'icermeli': ['mourner']},
    {'tohum': 'zealous', 'grup': 'F', 'kok': ['zeal']},
    {'tohum': 'gaol', 'grup': 'G', 'kok': ['jail'], 'icermemeli': ['gaol']},
    {'tohum': 'aeroplane', 'grup': 'G', 'kok': ['airplane'], 'icermemeli': ['aeroplane']},
    {'tohum': 'kerb', 'grup': 'G', 'kok': ['curb'], 'icermemeli': ['kerb']},
]
SURUMLER["11"] = SURUM_11
SON_SURUM = "11"
BEKLENTILER = SURUMLER[SON_SURUM]

GRUP_ADLARI = {
    "A": "Tutarlılık", "B": "Önek", "C": "Tek başına",
    "D": "Ayrım", "E": "Çekim", "F": "Uydurma", "G": "Amerikan yazımı",
}


def liste_metni(surum=SON_SURUM):
    beklentiler = SURUMLER[surum]
    satirlar = [
        f"# LearnVocab — aile hattı ölçüm listesi, {surum}. sürüm "
        f"(prompt'ta ve önceki sürümlerde geçmeyen kelimeler)",
        "# words/aile/deneme.py içinden üretildi; elle düzenleme.",
        "#",
        f"# python manage.py aile_uret --file listeler/aile-deneme-{surum}.txt "
        f"--depo ara-depo-deneme-{surum}",
        f"# python manage.py aile_birlestir --depo ara-depo-deneme-{surum}",
        f"# python manage.py aile_olc --surum {surum} --depo ara-depo-deneme-{surum}",
        "",
    ]
    grup = None
    for b in beklentiler:
        if b["grup"] != grup:
            grup = b["grup"]
            satirlar.append(f"# {grup} — {GRUP_ADLARI[grup]}")
        satirlar.append(b["tohum"])
    return "\n".join(satirlar) + "\n"
