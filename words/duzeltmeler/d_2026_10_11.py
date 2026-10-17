# -*- coding: utf-8 -*-
"""
11 Ekim — "get"in anlamları ve kalıpları (Efe'nin isteği: get'in birlikte kullanıldığı
her kalıp). Claude elle yazdı, API yok.

Sözlükte get'in (fiil) yalnızca iki anlamı (almak · anlamak) ve üç kalıbı vardı.
Kalıplar anlama bağlı olduğu için önce eksik anlamlar eklendi (hâline gelmek,
varmak, getirmek, yaptırmak, hastalığa yakalanmak, taşıta binmek, fırsat bulmak,
başlamak, have got); her kalıp kendi anlamının altına yazıldı.

- Kalıplar Collocation'a yazılır (kartta Türkçesiyle görünsün diye); gösterim
  kalıp kuralına uyar (words/kalip_bicimi.py: sb / sth / doing sth / to do sth).
  get hafif fiil sorularında yok (egzersizler.sorular.HAFIF_FIILLER), egzersiz etkilenmez.
- Phrasal verb'ler (get up, get on …) ayrı kelime olarak sözlükte; burada yok.
- Var olan anlamlar Türkçe karşılığıyla bulunur, yenileri eklenir; anlam sırası
  sıklığa göre yeniden verilir. Eş anlamlılar ("Benzer") anlama bağlanır.

Çalıştırma:  python manage.py shell -c "from words.duzeltmeler import d_2026_10_11 as d; d.get_kaliplari()"
Tekrar çalıştırmak güvenli.
"""
from django.db import transaction

from words.models import (
    Collocation, CollocationKind, ExampleSentence, Meaning, PartOfSpeech, RelationType, Word,
    WordRelation,
)

KAYNAK = "claude-elle"
VN, DIGER = CollocationKind.VERB_NOUN, CollocationKind.OTHER

# Sıra = kartta gösterim sırası. "eski" doluysa var olan anlam (meaning_tr ile bulunur).
GET = [
    {"eski": "almak, elde etmek", "tr": "almak, elde etmek, edinmek", "cefr": "A1",
     "en": "to obtain, receive, or acquire something",
     "benzer": ["obtain", "receive", "acquire"],
     "kaliplar": [
        ("get a job", VN, "iş bulmak", "She finally got a job after months of searching."),
        ("get a gift", VN, "hediye almak", "He got a beautiful gift for his birthday."),
        ("get a letter", VN, "mektup almak", "I got a letter from my grandmother today."),
        ("get a message", VN, "mesaj almak", "Did you get my message?"),
        ("get a call", VN, "telefon almak, aranmak", "I got a call from the hospital."),
        ("get an answer", VN, "cevap almak", "I still haven't got an answer from them."),
        ("get help", VN, "yardım almak", "You should get help from a teacher."),
        ("get advice", VN, "tavsiye almak", "It's a good idea to get advice from a lawyer."),
        ("get information", VN, "bilgi almak", "Where can I get information about the course?"),
        ("get permission", VN, "izin almak", "You need to get permission to film here."),
        ("get a grade", VN, "not almak", "She got a good grade in math."),
        ("get a degree", VN, "diploma almak, mezun olmak", "She got a degree in law."),
        ("get a prize", VN, "ödül almak", "Our class got a prize for the best project."),
        ("get a salary", VN, "maaş almak", "Nurses don't get a very high salary."),
        ("get a discount", VN, "indirim almak", "Students get a 20% discount."),
        ("get a ticket", VN, "bilet almak", "We got tickets for the concert."),
        ("get a visa", VN, "vize almak", "It took two months to get a visa."),
        ("get a result", VN, "sonuç almak", "We got some surprising results."),
        ("get experience", VN, "deneyim kazanmak", "This job is a good way to get experience."),
        ("get support", VN, "destek almak", "The plan got support from most people."),
        ("get attention", VN, "ilgi görmek, dikkat çekmek", "The story got a lot of attention online."),
        ("get some sleep", VN, "biraz uyumak", "Try to get some sleep before the exam."),
        ("get some rest", VN, "biraz dinlenmek", "You look tired. Get some rest."),
        ("get some fresh air", VN, "biraz temiz hava almak", "Let's go out and get some fresh air."),
        ("get a look at sb/sth", DIGER, "-e bakma fırsatı bulmak, -i görmek", "Did you get a look at his face?"),
        ("get the impression that …", DIGER, "-diği izlenimini edinmek", "I got the impression that she was unhappy."),
        ("get a feeling that …", DIGER, "-diği hissine kapılmak", "I get the feeling that something is wrong."),
        ("get sth from sb", DIGER, "birinden bir şey almak", "I got this book from my uncle."),
        ("get sth for sth", DIGER, "bir şeyi bir fiyata almak", "I got this jacket for $20."),
        ("get your own way", DIGER, "dediğini yaptırmak, istediğini elde etmek", "He always gets his own way."),
        ("get the better of sb", DIGER, "birine galip gelmek, ağır basmak", "In the end, curiosity got the better of me."),
        ("get even with sb", DIGER, "biriyle ödeşmek, intikam almak", "He wanted to get even with his brother."),
        ("get a kick out of sth", DIGER, "bir şeyden zevk almak", "She gets a kick out of solving puzzles."),
        ("get the most out of sth", DIGER, "bir şeyden en iyi şekilde yararlanmak", "Here's how to get the most out of your trip."),
        ("get a word in", DIGER, "(konuşmada) söz alabilmek", "She talked so much that I couldn't get a word in."),
     ]},
    {"tr": "olmak, hâline gelmek; (bir duruma) girmek", "cefr": "A2",
     "en": "to become or start to be; to reach a particular state",
     "ornekler": ["It's getting dark.", "I got tired after the long walk."],
     "benzer": ["become", "grow", "turn"],
     "kaliplar": [
        ("get tired", DIGER, "yorulmak", "I get tired easily these days."),
        ("get bored", DIGER, "sıkılmak", "The children got bored and started to play."),
        ("get angry", DIGER, "kızmak, sinirlenmek", "Don't get angry with me!"),
        ("get upset", DIGER, "üzülmek", "She got upset when she heard the news."),
        ("get annoyed", DIGER, "canı sıkılmak, sinirlenmek", "He gets annoyed when people are late."),
        ("get nervous", DIGER, "heyecanlanmak, gerilmek", "I always get nervous before exams."),
        ("get excited", DIGER, "heyecanlanmak", "The kids got excited about the trip."),
        ("get worried", DIGER, "endişelenmek", "Your mother will get worried if you're late."),
        ("get scared", DIGER, "korkmak", "I got scared when the lights went out."),
        ("get confused", DIGER, "kafası karışmak", "I always get confused by these rules."),
        ("get hungry", DIGER, "acıkmak", "I'm getting hungry. Let's eat."),
        ("get thirsty", DIGER, "susamak", "You get thirsty quickly in this heat."),
        ("get cold", DIGER, "üşümek; soğumak", "Your tea is getting cold."),
        ("get hot", DIGER, "ısınmak, sıcaklamak", "It gets very hot here in July."),
        ("get wet", DIGER, "ıslanmak", "We got wet in the rain."),
        ("get dark", DIGER, "(hava) kararmak", "It gets dark early in winter."),
        ("get late", DIGER, "(saat) geç olmak", "It's getting late. I should go."),
        ("get sick", DIGER, "hastalanmak", "He got sick after eating the fish."),
        ("get well", DIGER, "iyileşmek", "Get well soon!"),
        ("get better", DIGER, "iyileşmek, düzelmek", "Your English is getting better."),
        ("get worse", DIGER, "kötüleşmek", "The traffic gets worse every year."),
        ("get older", DIGER, "yaşlanmak, büyümek", "As you get older, you see things differently."),
        ("get rich", DIGER, "zengin olmak", "He got rich by selling software."),
        ("get ready", DIGER, "hazırlanmak", "Get ready, we're leaving in five minutes."),
        ("get dressed", DIGER, "giyinmek", "I got dressed and had breakfast."),
        ("get undressed", DIGER, "soyunmak", "He got undressed and went to bed."),
        ("get washed", DIGER, "yıkanmak", "Go and get washed before dinner."),
        ("get married", DIGER, "evlenmek", "They got married last summer."),
        ("get engaged", DIGER, "nişanlanmak", "My sister got engaged yesterday."),
        ("get divorced", DIGER, "boşanmak", "His parents got divorced when he was ten."),
        ("get lost", DIGER, "kaybolmak, yolunu kaybetmek", "We got lost in the old town."),
        ("get stuck", DIGER, "sıkışmak, takılıp kalmak", "We got stuck in traffic for an hour."),
        ("get hurt", DIGER, "yaralanmak, incinmek", "Be careful or you'll get hurt."),
        ("get injured", DIGER, "yaralanmak, sakatlanmak", "Two players got injured in the match."),
        ("get caught", DIGER, "yakalanmak", "He got caught cheating in the exam."),
        ("get fired", DIGER, "kovulmak, işten atılmak", "She got fired for being late every day."),
        ("get promoted", DIGER, "terfi etmek", "He got promoted to manager."),
        ("get paid", DIGER, "maaş almak, para almak", "We get paid at the end of the month."),
        ("get elected", DIGER, "seçilmek", "She got elected as class president."),
        ("get accepted", DIGER, "kabul edilmek", "I got accepted to the university."),
        ("get invited", DIGER, "davet edilmek", "We got invited to their wedding."),
        ("get stolen", DIGER, "çalınmak", "My bike got stolen last week."),
        ("get broken", DIGER, "kırılmak", "Two plates got broken in the move."),
        ("get involved in sth", DIGER, "bir işe karışmak, dahil olmak", "I don't want to get involved in their argument."),
        ("get used to sth/doing sth", DIGER, "-e alışmak", "It took me a month to get used to getting up early."),
        ("get into trouble", DIGER, "başını belaya sokmak", "He got into trouble for talking in class."),
        ("get out of hand", DIGER, "kontrolden çıkmak", "The party got out of hand."),
        ("get in the way", DIGER, "engel olmak, ayak altında olmak", "Don't let fear get in the way of your dreams."),
        ("get on sb's nerves", DIGER, "birinin sinirine dokunmak", "That noise is getting on my nerves."),
        ("get carried away", DIGER, "kendini kaptırmak, ölçüyü kaçırmak", "I got carried away and spent too much money."),
        ("get cold feet", DIGER, "son anda cesaretini kaybetmek", "He got cold feet before the wedding."),
     ]},
    {"tr": "varmak, ulaşmak, gitmek", "cefr": "A1",
     "en": "to arrive at or reach a place, or to move to a place",
     "ornekler": ["What time did you get home?", "How do I get to the station?"],
     "benzer": ["arrive", "reach"],
     "kaliplar": [
        ("get home", DIGER, "eve varmak", "I got home at midnight."),
        ("get here", DIGER, "buraya varmak, gelmek", "How long did it take you to get here?"),
        ("get there", DIGER, "oraya varmak; (amacına) ulaşmak", "We got there just in time."),
        ("get to a place", DIGER, "bir yere varmak", "We got to London at six."),
        ("get to work", DIGER, "işe varmak", "I usually get to work at nine."),
        ("get to school", DIGER, "okula varmak", "How do you get to school?"),
        ("get somewhere", DIGER, "bir yere varmak, ilerleme kaydetmek", "At last we're getting somewhere!"),
        ("get nowhere", DIGER, "hiçbir yere varamamak, sonuç alamamak", "We talked for hours but got nowhere."),
        ("get as far as sth", DIGER, "-e kadar gelebilmek", "We only got as far as the bridge."),
        ("get in touch with sb", DIGER, "biriyle iletişime geçmek", "I'll get in touch with you next week."),
        ("get hold of sb/sth", DIGER, "birine ulaşmak; bir şeyi bulmak", "I couldn't get hold of him all day."),
        ("get to the point", DIGER, "sadede gelmek", "Please get to the point – we don't have much time."),
     ]},
    {"eski": "anlamak, kavramak", "tr": "anlamak, kavramak", "cefr": "B1",
     "en": "to become aware of or comprehend something",
     "benzer": ["understand", "comprehend"],
     "kaliplar": [
        ("get the idea", VN, "fikri anlamak", "It took me a while, but I finally got the idea behind the algorithm."),
        ("get it", DIGER, "anlamak", "I don't get it. Can you explain again?"),
        ("get the joke", VN, "şakayı anlamak", "Everyone laughed, but I didn't get the joke."),
        ("get the point", VN, "ana fikri anlamak", "OK, I get the point – you don't like it."),
        ("get the message", VN, "mesajı almak, ne denmek istendiğini anlamak", "He didn't call back, so I got the message."),
        ("get the picture", VN, "durumu kavramak", "You don't need to explain any more – I get the picture."),
        ("get what sb means", DIGER, "birinin ne demek istediğini anlamak", "I get what you mean."),
        ("get sb wrong", DIGER, "birini yanlış anlamak", "Don't get me wrong – I like him."),
        ("get sth right", DIGER, "bir şeyi doğru yapmak / anlamak", "It's important to get the details right."),
        ("get sth wrong", DIGER, "bir şeyi yanlış yapmak / anlamak", "I got the date wrong and missed the meeting."),
        ("get the hang of sth", DIGER, "bir şeyin inceliğini kavramak, alışmak", "Driving is hard at first, but you'll get the hang of it."),
        ("get to grips with sth", DIGER, "bir şeyi kavramaya başlamak, üstesinden gelmek", "I'm still getting to grips with the new software."),
     ]},
    {"tr": "getirmek, (gidip) almak", "cefr": "A2",
     "en": "to go somewhere and bring back someone or something",
     "ornekler": ["Can you get me a glass of water?", "I'll go and get the children from school."],
     "benzer": ["fetch", "bring", "buy"],
     "kaliplar": [
        ("get sth for sb", DIGER, "biri için bir şey almak / getirmek", "I got a present for my mom."),
        ("get a drink", VN, "bir şey içmek için almak", "Let's get a drink after work."),
        ("get sth to eat", DIGER, "yiyecek bir şey almak, bir şeyler yemek", "We stopped to get something to eat."),
        ("get the phone", DIGER, "telefona bakmak", "Can you get the phone? I'm in the shower."),
        ("get the door", DIGER, "kapıya bakmak", "Someone's knocking – can you get the door?"),
        ("get a doctor", VN, "doktor çağırmak", "Quick, get a doctor!"),
     ]},
    {"tr": "(birine bir şey) yaptırmak; ikna edip yaptırmak", "cefr": "B1",
     "en": "to make someone do something, or to arrange for something to be done",
     "ornekler": ["I got my brother to help me.", "I need to get my car repaired."],
     "benzer": ["persuade", "convince"],
     "kaliplar": [
        ("get sb to do sth", DIGER, "birine bir şey yaptırmak, ikna etmek", "I finally got him to stop smoking."),
        ("get sth done", DIGER, "bir şeyi (başkasına) yaptırmak; bitirmek", "I need to get this work done by Friday."),
        ("get your hair cut", DIGER, "saçını kestirmek", "I got my hair cut yesterday."),
        ("get sth fixed", DIGER, "bir şeyi tamir ettirmek", "Where can I get my phone fixed?"),
        ("get sth repaired", DIGER, "bir şeyi onarttırmak", "We got the roof repaired."),
        ("get sth cleaned", DIGER, "bir şeyi temizletmek", "I got my coat cleaned."),
        ("get sth checked", DIGER, "bir şeyi kontrol ettirmek", "You should get your eyes checked."),
        ("get sth ready", DIGER, "bir şeyi hazırlamak", "Can you get the room ready for the guests?"),
        ("get sb/sth doing sth", DIGER, "birini / bir şeyi harekete geçirmek, çalıştırmak", "The film got everyone talking."),
        ("get sth working", DIGER, "bir şeyi çalışır hâle getirmek", "I can't get this printer working."),
        ("get the job done", DIGER, "işi bitirmek, işi görmek", "It's not perfect, but it gets the job done."),
     ]},
    {"tr": "(hastalığa) yakalanmak, -e tutulmak", "cefr": "A2",
     "en": "to catch an illness or start to have a pain",
     "ornekler": ["I think I'm getting a cold.", "She gets headaches when she's tired."],
     "benzer": ["catch", "develop"],
     "kaliplar": [
        ("get a cold", VN, "soğuk algınlığına yakalanmak", "I got a cold after the trip."),
        ("get the flu", VN, "gripe yakalanmak", "Half the class got the flu."),
        ("get a headache", VN, "başı ağrımak", "I get a headache if I don't drink enough water."),
        ("get a stomachache", VN, "midesi ağrımak", "I got a stomachache after lunch."),
        ("get a fever", VN, "ateşi çıkmak", "The baby got a fever in the night."),
     ]},
    {"tr": "(taşıta) binmek, ile gitmek", "cefr": "A2",
     "en": "to travel somewhere on a bus, train, plane or taxi",
     "ornekler": ["I usually get the bus to work.", "We got a taxi to the airport."],
     "benzer": ["take", "catch"],
     "kaliplar": [
        ("get the bus", VN, "otobüse binmek, otobüsle gitmek", "I got the bus into town."),
        ("get the train", VN, "trene binmek, trenle gitmek", "We got the train to Ankara."),
        ("get a taxi", VN, "taksiye binmek, taksi tutmak", "It's late – let's get a taxi."),
        ("get a flight", VN, "uçakla gitmek, uçuş bulmak", "We got a cheap flight to Rome."),
     ]},
    {"tr": "(bir şeyi yapma) fırsatı bulmak, -ebilmek", "cefr": "B1",
     "en": "to have the opportunity to do something",
     "ornekler": ["I got to meet my favorite singer.", "Do you ever get to travel for work?"],
     "kaliplar": [
        ("get to do sth", DIGER, "bir şeyi yapma fırsatı bulmak", "We got to see the stars at the planetarium."),
        ("get the chance to do sth", DIGER, "bir şeyi yapma şansı bulmak", "I never got the chance to thank her."),
        ("get a chance", VN, "fırsat bulmak", "Call me when you get a chance."),
        ("get to know sb", DIGER, "birini tanımak, tanışmak", "I'd like to get to know you better."),
        ("get to know sth", DIGER, "bir yeri / bir şeyi tanımak", "It takes time to get to know a new city."),
     ]},
    {"tr": "(bir işe) başlamak, koyulmak", "cefr": "B1",
     "en": "to start doing something, or to start to move",
     "ornekler": ["Let's get started.", "We'd better get going or we'll be late."],
     "benzer": ["start", "begin"],
     "kaliplar": [
        ("get started", DIGER, "başlamak", "Let's get started on the project."),
        ("get going", DIGER, "yola koyulmak, harekete geçmek", "It's late – we should get going."),
        ("get moving", DIGER, "acele etmek, harekete geçmek", "Get moving! The bus is leaving."),
        ("get doing sth", DIGER, "bir şeyi yapmaya koyulmak", "Once they got talking, they couldn't stop."),
        ("get to work", DIGER, "işe koyulmak", "Right, let's get to work."),
        ("get on with sth", DIGER, "bir işe devam etmek, koyulmak", "Stop talking and get on with your work."),
        ("get a move on", DIGER, "acele etmek", "Get a move on or we'll miss the train!"),
        ("get the ball rolling", DIGER, "işi başlatmak, ilk adımı atmak", "Let me get the ball rolling with a few questions."),
     ]},
    {"tr": "(have got) sahip olmak; (have got to) -mek zorunda olmak", "cefr": "A1",
     "en": "have got: to have or own something; have got to: to have to do something",
     "ornekler": ["I've got two brothers.", "I've got to go now."],
     "benzer": ["have", "own", "possess"],
     "kaliplar": [
        ("have got sth", DIGER, "bir şeye sahip olmak, -si olmak", "She's got a new car."),
        ("have got to do sth", DIGER, "bir şeyi yapmak zorunda olmak", "You've got to try this cake!"),
        ("have got sth to do", DIGER, "yapacak bir işi olmak", "I've got a lot of homework to do."),
        ("have got a cold", VN, "soğuk algınlığı olmak", "I've got a terrible cold."),
     ]},
]

def _benzer_hedef(yazim):
    adaylar = list(Word.objects.filter(text__iexact=yazim))
    for w in adaylar:
        if w.pos == PartOfSpeech.VERB:
            return w
    return None


@transaction.atomic
def get_kaliplari():
    get = Word.objects.get(text="get", pos=PartOfSpeech.VERB)
    yeni_anlam = yeni_kalip = yeni_bag = 0
    bulunamayan = []
    for sira, a in enumerate(GET):
        if a.get("eski"):
            m = get.meanings.get(meaning_tr=a["eski"]) if get.meanings.filter(meaning_tr=a["eski"]).exists() \
                else get.meanings.get(meaning_tr=a["tr"])
        else:
            m = get.meanings.filter(meaning_tr=a["tr"]).first()
        if m is None:
            m = Meaning.objects.create(word=get, meaning_tr=a["tr"], definition=a["en"],
                                       cefr=a["cefr"], sort_order=sira)
            yeni_anlam += 1
        m.meaning_tr, m.definition, m.sort_order = a["tr"], a["en"], sira
        m.cefr = m.cefr or a["cefr"]
        m.save()
        for i, o in enumerate(a.get("ornekler", [])):
            ExampleSentence.objects.get_or_create(meaning=m, text=o,
                                                  defaults={"source": KAYNAK, "sort_order": i})
        for i, (kalip, tur, tr, ornek) in enumerate(a["kaliplar"]):
            _, yeni = Collocation.objects.update_or_create(
                meaning=m, pattern=kalip,
                defaults={"kind": tur, "meaning_tr": tr, "example": ornek, "sort_order": i})
            yeni_kalip += yeni
        for yazim in a.get("benzer", []):
            hedef = _benzer_hedef(yazim)
            if hedef is None:
                bulunamayan.append(yazim)
                continue
            _, yeni = WordRelation.objects.get_or_create(
                from_word=get, to_word=hedef, type=RelationType.SYNONYM, meaning=m)
            yeni_bag += yeni
    print(f"get: {get.meanings.count()} anlam ({yeni_anlam} yeni), "
          f"{Collocation.objects.filter(meaning__word=get).count()} kalıp ({yeni_kalip} yeni), "
          f"{yeni_bag} yeni benzer bağı.")
    if bulunamayan:
        print("Sözlükte bulunmayan benzer:", ", ".join(bulunamayan))


# ----------------------------------------------------------------------
# Temel (dilbilgisi) kelimeleri — rapor 18.36. Claude elle yazdı, API yok.
# Veri: veri/temel_kelimeler/*.txt (araclar/phrasal_jsonl.py ile *.jsonl).
#
#   python manage.py shell -c "from words.duzeltmeler import d_2026_10_11 as d; d.temel_kelimeler()"
#
# 1) Yanlış türle duran kayıtlar doğru türe çevrilir (kimlikleri, kullanıcı bağları korunur).
#    Dosyada aynı (yazım, yeni tür) varsa anlamları dosyadakiyle değiştirilir (can: "yapabilmek"
#    tek anlamı yerine yetenek / izin / rica / olasılık).
# 2) Dosyalar `elle_kelime_yukle` ile yüklenir (var olan atlanır).
# 3) Zamir aileleri kurulur: I · me · my · mine · myself … ("it" zamiri IT ailesine düşmesin).
# Tekrar çalıştırmak güvenli.
# ----------------------------------------------------------------------
import json
from pathlib import Path

from django.core.management import call_command

from words import inflect
from words.models import WordFamily

TEMEL_DOSYALAR = sorted(Path("veri/temel_kelimeler").glob("*.jsonl"))

# (yazım, eski tür) -> yeni tür
TUR_DONUSUMU = {
    ("can", "verb"): "modal_verb", ("might", "verb"): "modal_verb", ("ought", "verb"): "modal_verb",
    ("every", "adjective"): "determiner", ("some", "adjective"): "determiner",
    ("few", "adjective"): "determiner", ("several", "adjective"): "determiner",
    ("someone", "noun"): "pronoun", ("somebody", "noun"): "pronoun",
    ("something", "noun"): "pronoun", ("anybody", "noun"): "pronoun",
    ("hello", "noun"): "exclamation", ("goodbye", "noun"): "exclamation", ("bye", "noun"): "exclamation",
}

# Aile kökü -> üyeler (yalnızca dilbilgisi türleri taşınır).
ZAMIR_AILELERI = {
    "I": ["I", "me", "my", "mine", "myself"],
    "you": ["you", "your", "yours", "yourself", "yourselves"],
    "he": ["he", "him", "his", "himself"],
    "she": ["she", "her", "hers", "herself"],
    "itself": ["it", "its", "itself"],      # kök "it" değil: o kök IT (bilişim) ailesinin
    "we": ["we", "us", "our", "ours", "ourselves"],
    "they": ["they", "them", "their", "theirs", "themselves"],
    "a": ["a", "an"],
    "this": ["this", "these"],
    "that": ["that", "those"],
}


def _temel_kayitlar():
    kayitlar = {}
    for yol in TEMEL_DOSYALAR:
        for satir in open(yol, encoding="utf-8"):
            k = json.loads(satir)
            kayitlar[(k["text"].lower(), k["pos"])] = k
    return kayitlar


def _anlamlari_yaz(word, k):
    word.meanings.all().delete()
    for sira, a in enumerate(k["anlamlar"]):
        m = Meaning.objects.create(word=word, meaning_tr=a["tr"], definition=a["en"], sort_order=sira)
        ExampleSentence.objects.bulk_create([
            ExampleSentence(meaning=m, text=o, source=KAYNAK, sort_order=i)
            for i, o in enumerate(a["ornekler"][:Meaning.EXAMPLE_SENTENCE_COUNT])])


@transaction.atomic
def _turleri_cevir(kayitlar):
    for (yazim, eski), yeni in TUR_DONUSUMU.items():
        w = Word.objects.filter(text=yazim, pos=eski).first()
        if w is None:
            continue
        w.pos = yeni
        k = kayitlar.get((yazim, yeni))
        if k:
            w.cefr, w.cefr_kaynak = k["cefr"], k["cefr_kaynak"]
            _anlamlari_yaz(w, k)
        w.save()
        inflect.rebuild_forms(w)
        print(f"tür: {yazim} {eski} -> {yeni}" + (" (anlamlar dosyadan)" if k else ""))


@transaction.atomic
def _aileleri_kur():
    from words.models import DILBILGISI_TURLERI
    for kok, uyeler in ZAMIR_AILELERI.items():
        aile, _ = WordFamily.objects.get_or_create(root=kok.lower())
        qs = Word.objects.filter(text__in=uyeler, pos__in=DILBILGISI_TURLERI).exclude(family=aile)
        eski_aileler = set(qs.values_list("family_id", flat=True))
        qs.update(family=aile)
        WordFamily.objects.filter(id__in=eski_aileler, words__isnull=True).delete()


# Dosya içi sıra yüzünden yüklemede kurulamayan bağlar: (yazım, tür, anlam sırası, hedef, hedef türü)
SONRADAN_BAGLAR = [
    ("that", "pronoun", 1, "which", "pronoun"),
    ("although", "conjunction", 0, "though", "conjunction"),
    ("sorry", "exclamation", 1, "pardon", "exclamation"),
]


@transaction.atomic
def _sonradan_baglar():
    for yazim, tur, sira, hedef, hedef_tur in SONRADAN_BAGLAR:
        m = Meaning.objects.get(word__text=yazim, word__pos=tur, sort_order=sira)
        h = Word.objects.get(text=hedef, pos=hedef_tur)
        WordRelation.objects.get_or_create(from_word=m.word, to_word=h, type=RelationType.SYNONYM, meaning=m)


def temel_kelimeler():
    kayitlar = _temel_kayitlar()
    _turleri_cevir(kayitlar)
    for yol in TEMEL_DOSYALAR:
        call_command("elle_kelime_yukle", str(yol))
    _aileleri_kur()
    _sonradan_baglar()


# ----------------------------------------------------------------------
# Konular (kategoriler) — rapor 18.39. Efe'nin kararı: modelin 114 kategorisi silinir; öğrenciye
# gerekli 34 konu elle işaretlenir (yalnızca o konuda önemli kelimeler, doğru anlamlarıyla).
# Veri: veri/kategoriler/*.txt.
#
#   python manage.py shell -c "from words.duzeltmeler import d_2026_10_11 as d; d.konulari_kur(kuru=True)"
#   python manage.py shell -c "from words.duzeltmeler import d_2026_10_11 as d; d.konulari_kur()"
#
# Gerçek çalıştırma eski kategori bağlarını ~/LearnVocab-yedekler/'e TSV olarak yazar, hepsini
# siler ve konuları baştan kurar (tekrar çalıştırmak güvenli; elle eklenen bağlar dosyadan gelir).
# ----------------------------------------------------------------------
import os
import re as _re

KONU_DOSYALARI = sorted(Path("veri/kategoriler").glob("*.txt"))
KISA_TUR = {"n": "noun", "v": "verb", "adj": "adjective", "adv": "adverb", "pv": "phrasal_verb",
            "prep": "preposition", "conj": "conjunction", "pron": "pronoun", "det": "determiner",
            "excl": "exclamation", "mv": "modal_verb"}


def _konu_dosyalari():
    """[(slug, ad, ad_en, [madde, …]), …]"""
    konular = []
    for yol in KONU_DOSYALARI:
        for satir in open(yol, encoding="utf-8"):
            satir = satir.strip()
            if not satir or (satir.startswith("#") and not satir.startswith("## ")):
                continue
            if satir.startswith("## "):
                slug, ad, ad_en = [p.strip() for p in satir[3:].split("|")]
                konular.append((slug, ad, ad_en, []))
            else:
                konular[-1][3].extend(m.strip() for m in satir.split(",") if m.strip())
    return konular


def _madde_coz(madde):
    """'bat:n=yarasa' -> ('bat', 'noun', 'yarasa')"""
    m = _re.fullmatch(r"(.+?)(?::(\w+))?(?:=(.+))?", madde)
    yazim, tur, ipucu = m.group(1).strip(), m.group(2), m.group(3)
    return yazim, KISA_TUR.get(tur, tur) if tur else None, ipucu


# Çok anlamlı kelimede doğru anlam dosyadaki ipucuyla seçilir. (İlk kurulumda modelin eski
# kategorileri de ipucu olarak kullanılıyordu; eski kategoriler silinince yeniden kurulumda bu ipucu
# kayboldu ve 92 kelime ilk anlamına düştü — land "elde etmek" Ulaşım'a girdi. 11 Ekim'de o seçimler
# dosyalara açık ipucu olarak yazıldı; artık her şey dosyadan gelir, kaç kez kurulursa kurulsun aynı.)

_SEVIYE = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
_TUR_ONCELIK = {"noun": 0, "adjective": 1, "verb": 2, "adverb": 3, "phrasal_verb": 4}


def _tr(s):
    return (s or "").replace("İ", "i").replace("I", "ı").lower()


def _bagla(madde, konu=None):
    """-> (anlamlar, ifadeler, uyarı ya da None)"""
    from words.models import DILBILGISI_TURLERI, Expression
    yazim, tur, ipucu = _madde_coz(madde)
    kelimeler = list(Word.objects.filter(text__iexact=yazim).exclude(pos__in=DILBILGISI_TURLERI)
                     .prefetch_related("meanings"))
    if tur:
        kelimeler = [w for w in kelimeler if w.pos == tur]
    if not kelimeler:
        ifadeler = list(Expression.objects.filter(text__iexact=yazim))
        return [], ifadeler, (None if ifadeler else "yok")
    anlamlar = [m for w in kelimeler for m in w.meanings.all()]
    if yazim[:1].isupper() and any(w.text == yazim for w in kelimeler):
        kelimeler = [w for w in kelimeler if w.text == yazim]          # "March" ay, "march" yürüyüş değil
        anlamlar = [m for w in kelimeler for m in w.meanings.all()]
    if ipucu:
        if ipucu.startswith("^"):                                       # "memory:n=^bellek": bununla başlayan
            bas = [m for m in anlamlar if _tr(m.meaning_tr).startswith(_tr(ipucu[1:]))]
            return (bas[:1], [], None) if bas else ([], [], "ipucu tutmadı")
        tam = ipucu.startswith("=")                                     # "degree==derece": birebir
        ipucu = ipucu.lstrip("=")
        birebir = [m for m in anlamlar if _tr(m.meaning_tr).strip() == _tr(ipucu)]
        uyan = birebir if (birebir or tam) else [m for m in anlamlar if _tr(ipucu) in _tr(m.meaning_tr)]
        return (uyan[:1], [], None) if uyan else ([], [], "ipucu tutmadı")
    secim_notu = ""
    if len(kelimeler) > 1:          # tür verilmemiş: en temel tür (nadir değil, en düşük seviye, isim önce)
        kelimeler.sort(key=lambda w: (w.nadir_tur, _SEVIYE.get(w.cefr, 9), _TUR_ONCELIK.get(w.pos, 9)))
        secim_notu = f"tür: {kelimeler[0].pos}; "
    w = kelimeler[0]
    ilk = sorted(w.meanings.all(), key=lambda m: m.sort_order)
    if not ilk:
        return [], [], "anlamı yok"
    if len(ilk) > 1 or secim_notu:
        return ilk[:1], [], f"{secim_notu}{len(ilk)} anlam, ilki: {ilk[0].meaning_tr}"
    return ilk[:1], [], None


def konulari_kur(kuru=False):
    from words.models import Category, Expression
    konular = _konu_dosyalari()
    sonuc, sorunlar, cok_anlam = [], [], []
    for slug, ad, ad_en, maddeler in konular:
        anlam_idler, ifade_idler = set(), set()
        for madde in dict.fromkeys(maddeler):
            anlamlar, ifadeler, uyari = _bagla(madde, slug)
            anlam_idler |= {m.id for m in anlamlar}
            ifade_idler |= {e.id for e in ifadeler}
            if uyari in ("yok", "ipucu tutmadı", "anlamı yok"):
                sorunlar.append(f"{slug}\t{madde}\t{uyari}")
            elif uyari:
                cok_anlam.append(f"{slug}\t{madde}\t{uyari}")
        sonuc.append((slug, ad, ad_en, anlam_idler, ifade_idler))
    os.makedirs("veri/kategoriler/rapor", exist_ok=True)
    open("veri/kategoriler/rapor/sorunlar.tsv", "w").write("\n".join(sorunlar) + "\n")
    open("veri/kategoriler/rapor/cok-anlamli.tsv", "w").write("\n".join(cok_anlam) + "\n")
    for slug, _, _, a, e in sonuc:
        print(f"{slug}: {len(a)} anlam, {len(e)} ifade")
    print(f"sorun: {len(sorunlar)} · çok anlamlı (ilk anlam alındı): {len(cok_anlam)} -> veri/kategoriler/rapor/")
    if kuru:
        return
    with transaction.atomic():
        yedek = os.path.expanduser("~/LearnVocab-yedekler/kategoriler-eski-20261011.tsv")
        if not os.path.exists(yedek):
            with open(yedek, "w") as f:
                for mid, ad in Meaning.categories.through.objects.values_list("meaning_id", "category__name"):
                    f.write(f"anlam\t{mid}\t{ad}\n")
                for eid, ad in Expression.categories.through.objects.values_list("expression_id", "category__name"):
                    f.write(f"ifade\t{eid}\t{ad}\n")
        Meaning.categories.through.objects.all().delete()
        Expression.categories.through.objects.all().delete()
        Category.objects.all().delete()
        for slug, ad, ad_en, anlam_idler, ifade_idler in sonuc:
            k = Category.objects.create(name=ad, slug=slug)
            Meaning.categories.through.objects.bulk_create(
                [Meaning.categories.through(meaning_id=i, category=k) for i in anlam_idler])
            Expression.categories.through.objects.bulk_create(
                [Expression.categories.through(expression_id=i, category=k) for i in ifade_idler])
    print(f"kuruldu: {len(sonuc)} konu")
