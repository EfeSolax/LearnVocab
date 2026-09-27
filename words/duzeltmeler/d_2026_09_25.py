# -*- coding: utf-8 -*-
"""
25 Eylül — Claude'un elle incelemesinde bulunan anlam hataları.
Çalıştırma:  python manage.py shell -c "from words.duzeltmeler import d_2026_09_25 as d; d.uygula()"
Tekrar çalıştırmak güvenli (her adım önce durumu kontrol eder).
"""
from django.db import transaction

from words.models import ExampleSentence, Meaning, Word


def _yeni_anlam(kelime, tur, meaning_tr, definition, cefr, cumleler, bas=True):
    w = Word.objects.get(text=kelime, pos=tur)
    if w.meanings.filter(meaning_tr=meaning_tr).exists():
        return
    if bas:
        for m in w.meanings.all():
            m.sort_order += 1
            m.save(update_fields=["sort_order"])
    m = Meaning.objects.create(word=w, meaning_tr=meaning_tr, definition=definition,
                               cefr=cefr, sort_order=0 if bas else 99)
    for i, c in enumerate(cumleler):
        ExampleSentence.objects.create(meaning=m, text=c, sort_order=i)


def _karsilik(kelime, tur, eski, yeni):
    Meaning.objects.filter(word__text=kelime, word__pos=tur, meaning_tr=eski).update(meaning_tr=yeni)


@transaction.atomic
def uygula():
    # --- Parti 1 (24 Eylül) ---
    _karsilik("dishonorable", "adjective", "onursuz, aşağılayıcı", "onursuz, şerefsiz, yüz kızartıcı")
    _karsilik("peer", "noun", "eş, yaşıt", "akran, yaşıt, emsal")
    _yeni_anlam("smell", "noun", "koku", "the quality of something that people or animals can sense through the nose", "A2", [
        "There was a strong smell of coffee in the kitchen.",
        "I love the smell of fresh bread in the morning.",
        "The smell of smoke woke everyone up.",
        "Some flowers have a very sweet smell.",
        "Researchers found that certain smells can trigger strong memories.",
    ])
    Word.objects.filter(text="children", pos="noun").delete()   # child'ın çoğulu (WordForm'da var)

    # --- Parti 2 (25 Eylül) ---
    _yeni_anlam("unrelated", "adjective", "ilgisiz, alakasız, bağlantısız", "not connected with something else", "B1", [
        "The two events are completely unrelated.",
        "He asked a question that was unrelated to the topic.",
        "The police believe the crimes are unrelated.",
        "She changed the subject to something unrelated.",
        "The study found that income was largely unrelated to happiness.",
    ])
    _karsilik("curse", "verb", "küfretmek", "küfretmek, sövmek, lanet okumak")
    _karsilik("possessed", "adjective", "sahip", "sahip olan, -e sahip")
    _yeni_anlam("possessed", "adjective", "ele geçirilmiş, cin çarpmış", "controlled by an evil spirit, in stories and beliefs", "B2", [
        "In the film, the girl behaves as if she were possessed.",
        "The villagers believed the old house was possessed.",
        "He fought like a man possessed.",
        "The story is about a doll that seems to be possessed.",
        "In many old legends, possessed people were taken to priests.",
    ])
    _karsilik("inflammatory", "adjective", "iltihaplı, kışkırtıcı", "iltihap yapan, kışkırtıcı")
    Meaning.objects.filter(word__text="stripper", meaning_tr="striptiz yapan kişi").delete()


@transaction.atomic
def uygula_2():
    """Gerçek yazımda (kuru denemede olmayan) gelen ~180 kelimenin incelemesi."""
    Word.objects.filter(text="horny", pos="adjective").delete()          # hassas anlam
    Word.objects.filter(text__in=["symptoms", "implications"], pos="noun").delete()  # tekilin çoğulu
    _karsilik("lay", "adjective", "laik, din dışı, uzman olmayan",
              "meslekten olmayan, uzman olmayan, din adamı olmayan")
    _karsilik("sinful", "adjective", "günah, günah dolu, ahlaka aykırı", "günahkâr, günah dolu, ahlaka aykırı")
    _karsilik("kind", "adjective", "iyi niyetli, yardımsever", "nazik, iyi kalpli, yardımsever")
    _karsilik("blade", "noun", "bıçak ağzı, namlu, jilet", "bıçak ağzı, bıçak, jilet")


@transaction.atomic
def uygula_3():
    """Parti 3 (700 aile, 2.650 kelime) incelemesi."""
    Word.objects.filter(text__in=["footsteps", "inhabitants"], pos="noun").delete()   # çoğul
    Word.objects.filter(text="swinger", pos="noun").delete()                          # hassas
    Meaning.objects.filter(word__text="intimate", word__pos="adjective",
                           meaning_tr="özel, cinsel anlamda yakın").delete()
    Meaning.objects.filter(word__text="polish", word__pos="noun", meaning_tr="lehçe").delete()  # Polish (dil)
    _karsilik("drink", "noun", "alkollü içki", "içki, içecek")
    _karsilik("twisted", "adjective", "sapık, hastalıklı", "çarpık, sapkın, hastalıklı")
    _karsilik("pat", "verb", "birini aramak, el ile kontrol etmek", "üstünü aramak")
    _yeni_anlam("pat", "verb", "hafifçe vurmak, sıvazlamak, okşamak",
                "to touch someone or something gently several times with a flat hand", "B1", [
        "She patted the dog on the head.",
        "He patted his friend on the back and smiled.",
        "The teacher patted the child's shoulder to calm her down.",
        "He patted his pockets, looking for his keys.",
        "She patted the cushion and asked him to sit next to her.",
    ])
    _yeni_anlam("blow", "noun", "darbe, vuruş",
                "a hard hit with the hand or a weapon; a sudden event that causes damage or disappointment", "B1", [
        "He received a blow to the head during the fight.",
        "The loss of the contract was a serious blow to the company.",
        "She fell after a heavy blow from the wave.",
        "The news of his death came as a terrible blow to the family.",
        "Rising prices dealt another blow to small businesses.",
    ])
    _yeni_anlam("blow", "verb", "üflemek", "to send air out from the mouth", "A2", [
        "She blew out the candles on her birthday cake.",
        "He blew on his hot soup before eating it.",
        "The referee blew the whistle to end the match.",
        "The children blew bubbles in the garden.",
        "He blew his nose loudly.",
    ], bas=False)
    _yeni_anlam("dish", "noun", "tabak, çanak", "a flat container for cooking or serving food", "A2", [
        "Please put the dishes in the sink.",
        "She served the salad in a large glass dish.",
        "It is your turn to wash the dishes tonight.",
        "He dropped a dish and it broke into pieces.",
        "Bake the mixture in a shallow dish for thirty minutes.",
    ], bas=False)
    _yeni_anlam("constructor", "noun", "inşaat şirketi, yapımcı", "a person or company that builds things, especially buildings or roads", "C1", [
        "The constructor finished the bridge ahead of schedule.",
        "Several constructors bid for the new hospital project.",
        "The constructor was fined for using poor materials.",
        "Local constructors employ thousands of workers.",
        "The racing team is the most successful constructor in the championship.",
    ])
    _yeni_anlam("swollen", "adjective", "şişmiş, şiş", "larger than usual, often because of injury or illness", "B2", [
        "Her ankle was swollen after the fall.",
        "His eyes were red and swollen from crying.",
        "The river was swollen after days of heavy rain.",
        "Put some ice on your swollen knee.",
        "She had a swollen face after the dental operation.",
    ])
    # Birleşen nokta (U+0307) temizliği
    from words.models import Collocation
    for m in Meaning.objects.filter(meaning_tr__contains="̇"):
        m.meaning_tr = m.meaning_tr.replace("i̇", "i").replace("̇", "")
        m.save(update_fields=["meaning_tr"])
    for k in Collocation.objects.filter(meaning_tr__contains="̇"):
        k.meaning_tr = k.meaning_tr.replace("i̇", "i").replace("̇", "")
        k.save(update_fields=["meaning_tr"])


@transaction.atomic
def uygula_4():
    """Parti 4 (1.500 aile, 4.644 kelime) incelemesi."""
    Word.objects.filter(pos="noun", text__in=[
        "oars", "oarsmen", "onlookers", "participants", "guidelines", "lice",
        "restrictions", "sophists",                                  # çoğul
        "busty", "negro", "slapper", "streaker"]).delete()            # hassas / aşağılayıcı
    Word.objects.filter(pos="adjective", text="busty").delete()
    for kelime, tur, anlam in [
        ("goose", "verb", "poposunu ellemek, parmak atmak, dürtmek"),
        ("grope", "verb", "elle taciz etmek"),
        ("lid", "noun", "esrar"),
        ("prick", "noun", "pislik, hıyar, hergele"),
        ("snort", "verb", "burundan toz çekmek"),
        ("streak", "verb", "çıplak koşmak, vücudunu göstererek koşmak"),
        ("tease", "verb", "cilve yapmak, tahrik etmek, baştan çıkarmak"),
    ]:
        Meaning.objects.filter(word__text=kelime, word__pos=tur, meaning_tr=anlam).delete()
    _karsilik("accord", "verb", "bahşetmek, tanımak, bahşetmek", "bahşetmek, tanımak")
    _karsilik("appreciation", "noun", "minnet, şükran", "takdir, minnet, şükran")
    _karsilik("barb", "noun", "çentik, damak, çengel", "diken, çengel, kanca")
    _karsilik("diary", "noun", "ajanda", "günlük, ajanda")
    _karsilik("exasperation", "noun", "bıkkınlık, çileden çıkma, cinnet", "bıkkınlık, çileden çıkma")
    _karsilik("looker", "noun", "çekici kimse, afet, fıstık", "çekici kimse, güzel kimse")
    _karsilik("butt", "noun", "kalça, popo", "kalça")
    _karsilik("arab", "adjective", "arap", "Arap")
    _karsilik("arab", "noun", "arap", "Arap")
    _karsilik("arabic", "adjective", "arap, arapça ile ilgili", "Arap, Arapça ile ilgili")
    _karsilik("arabic", "noun", "arapça", "Arapça")
    _yeni_anlam("benefit", "noun", "fayda, yarar, kazanç", "an advantage or good effect that something brings", "B1", [
        "Regular exercise has many health benefits.",
        "The new law will be of benefit to small businesses.",
        "One benefit of living in the city is good public transport.",
        "Students can see the benefits of studying abroad.",
        "The study examined the costs and benefits of the policy.",
    ])
    _yeni_anlam("gut", "noun", "bağırsak, karın", "the stomach or intestines", "B2", [
        "Healthy bacteria in the gut help digestion.",
        "He felt a sharp pain in his gut.",
        "The fish's guts were removed before cooking.",
        "Scientists study how the gut affects mood.",
        "She had a knot in her gut before the exam.",
    ])
    _yeni_anlam("fraction", "noun", "kesir", "a number that is not a whole number, such as 1/2 or 3/4", "B1", [
        "One half is a simple fraction.",
        "The children are learning to add fractions.",
        "Write the answer as a fraction.",
        "Three quarters is a larger fraction than two thirds.",
        "Convert the decimal 0.25 into a fraction.",
    ], bas=False)


@transaction.atomic
def uygula_5():
    """Parti 5 (2.089 kelime) incelemesi."""
    Word.objects.filter(pos="noun", text__in=["fireworks", "troops", "strata"]).delete()   # çoğul
    Word.objects.filter(pos="adjective", text="stoned").delete()                           # uyuşturucu argosu
    for kelime, tur, anlam in [
        ("bottom", "noun", "kıç, popo"),
        ("cleavage", "noun", "göğüs dekoltesi"),
    ]:
        Meaning.objects.filter(word__text=kelime, word__pos=tur, meaning_tr=anlam).delete()
    _karsilik("bastard", "noun", "piç, aşağılık herif", "gayri meşru çocuk")
    _karsilik("gay", "adjective", "neşeli, mutlu", "neşeli, şen (eski kullanım)")
    _karsilik("lick", "verb", "yenecek şekilde yenmek, alt etmek", "yenmek, alt etmek")
    _karsilik("developer", "noun", "yazılım geliştiricisi", "geliştirici, yazılım geliştiricisi")


@transaction.atomic
def uygula_6():
    """Parti 6 (3.056 kelime) incelemesi."""
    Word.objects.filter(text="horsemen", pos="noun").delete()                 # çoğul
    Word.objects.filter(text="shit", pos="noun").delete()                     # küfür
    Word.objects.filter(text="neck", pos="verb").delete()                     # "öpüşmek" argosu
    Word.objects.filter(text="bitch", pos="verb").delete()
    Word.objects.filter(text="bitchy", pos="adjective").delete()
    for kelime, tur, anlam in [
        ("ass", "noun", "kıç, göt"),
        ("bitch", "noun", "orospu, kaltak, cadı"),
        ("march", "noun", "mart ayı"),
        ("ten", "noun", "çok çekici, onluk"),
        ("tripper", "noun", "halüsinasyon gören kişi"),
        ("turkey", "noun", "türkiye"),
        ("upper", "noun", "uyarıcı ilaç, uyarıcı madde"),
    ]:
        Meaning.objects.filter(word__text=kelime, word__pos=tur, meaning_tr=anlam).delete()
    _karsilik("leer", "noun", "şehvetli bakış, ahlaksızca bakış, yan bakış", "sinsi bakış, yan bakış")
    _karsilik("juggler", "noun", "çoklu işi yöneten kişi", "hokkabaz, jonglör")
    _karsilik("juggle", "verb", "birden çok işi yürütmek", "birden çok işi idare etmek, hokkabazlık yapmak")
    _karsilik("card", "noun", "tebrik kartı", "kart, tebrik kartı")
    _karsilik("china", "noun", "çin", "Çin")
    _karsilik("chinese", "adjective", "çin, çinli", "Çin, Çinli")
    _karsilik("chinese", "adjective", "çince", "Çince")
    _karsilik("chinese", "noun", "çinli", "Çinli")
    _karsilik("chinese", "noun", "çince", "Çince")
    _karsilik("ark", "noun", "nuh'un gemisi, büyük gemi, sığınak tekne", "Nuh'un gemisi, büyük gemi, sığınak tekne")
    _karsilik("wasted", "adjective", "boşa gitmiş, heba olmuş", "boşa gitmiş, heba olmuş")
    Meaning.objects.filter(word__text="wasted", word__pos="adjective",
                           meaning_tr="zilzurna sarhoş, kafası güzel").update(meaning_tr="zilzurna sarhoş")
    _yeni_anlam("charge", "verb", "ücret almak, fiyat istemek", "to ask an amount of money for something", "A2", [
        "The hotel charges fifty dollars a night.",
        "How much do you charge for a haircut?",
        "The bank charged a small fee for the transfer.",
        "Museums in the city do not charge for entry on Sundays.",
        "They charged us too much for the repair.",
    ])
    _yeni_anlam("charge", "verb", "suçlamak, itham etmek", "to formally accuse someone of a crime", "B2", [
        "The police charged him with theft.",
        "She was charged with dangerous driving.",
        "No one has been charged in connection with the attack.",
        "He was arrested but later released without being charged.",
        "The man was charged with fraud after a long investigation.",
    ], bas=False)
    _yeni_anlam("croak", "verb", "vraklamak, boğuk sesle konuşmak", "to make a deep rough sound like a frog, or to speak with a rough voice", "C1", [
        "Frogs croaked loudly by the pond.",
        "'Water,' he croaked, barely able to speak.",
        "She had a cold and could only croak a few words.",
        "We heard the frogs croaking all night.",
        "The old man croaked a greeting from his chair.",
    ])


@transaction.atomic
def uygula_7():
    """Parti 7 (son parti, 1.659 kelime) incelemesi + Efe: gay silinsin."""
    Word.objects.filter(text="gay").delete()                                            # Efe'nin kararı
    Word.objects.filter(pos="noun", text__in=["kinsmen", "workmen", "fumes"]).delete()  # çoğul
    Word.objects.filter(text="high", pos="noun").delete()                               # tek anlamı "uyuşturucu etkisi"
    for kelime, tur, anlam in [
        ("high", "adjective", "kafası iyi, uçmuş, uyuşturucu etkisinde"),
        ("user", "noun", "uyuşturucu bağımlısı"),
    ]:
        Meaning.objects.filter(word__text=kelime, word__pos=tur, meaning_tr=anlam).delete()
    _karsilik("sensual", "adjective", "tensel, bedensel hazla ilgili, şehvetli", "tensel, duyusal")
    _karsilik("sensuality", "noun", "duyusal haz, cinselliğe ilişkin duyuların yoğunluğu", "tensellik, duyusal haz")
    _yeni_anlam("bind", "verb", "bağlamak, bağlayıcı olmak", "to tie something tightly; to make someone legally or morally obliged", "B2", [
        "They bound his hands with a rope.",
        "The agreement binds both countries to reduce emissions.",
        "Shared values bind the community together.",
        "She bound the papers together with a ribbon.",
        "The contract binds the company to pay the fee.",
    ])
    _yeni_anlam("depressed", "adjective", "üzgün, morali bozuk, depresif", "very unhappy and without hope", "B1", [
        "He felt depressed after losing his job.",
        "She was depressed for weeks after the exam results.",
        "Many students feel depressed during the long winter.",
        "Don't get depressed about one bad grade.",
        "He looked tired and depressed.",
    ])
    _yeni_anlam("revolt", "verb", "isyan etmek, ayaklanmak", "to take violent action against a government or authority", "B2", [
        "The people revolted against the cruel king.",
        "Soldiers revolted and took control of the capital.",
        "The workers revolted against the new rules.",
        "Several cities revolted after the election.",
        "Students revolted against the strict school system.",
    ])
