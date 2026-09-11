import os
import sys

# Bu script'ler proje kökünün dışından (VocabLoaders/ içinden) çalıştırıldığında da
# 'LearnVocab.settings' ve 'words.models' import edilebilsin diye proje kökünü
# Python yoluna ekliyoruz. Örn: python VocabLoaders/101loader.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django

# Django ayarlarını yükle
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LearnVocab.settings")
django.setup()

from words.models import Word, UserWordLink
from users.models import User

# Kullanıcıyı al
owner_user = User.objects.filter(username="EfeSolax").first()

if owner_user is None:
    raise Exception("Kullanıcı bulunamadı: EfeSolax")

words_to_create = [
    {"englishWord": "abruptly", "meaningTr": "aniden, birdenbire", "explanation": "Happening quickly and without warning.", "note": "adverb", "isVerb": False, "exampleSentence1": "The car stopped abruptly when the cat ran onto the road."},
    {"englishWord": "absorption", "meaningTr": "emilim, soğurma", "explanation": "The process by which one thing absorbs or is absorbed by another.", "note": "noun", "isVerb": False, "exampleSentence1": "The sponge is good for the absorption of liquids."},
    {"englishWord": "abstain", "meaningTr": "kaçınmak, uzak durmak", "explanation": "To choose not to do or have something.", "note": "verb", "isVerb": True, "v2Form": "abstained", "v3Form": "abstained", "exampleSentence1": "You should abstain from smoking for your health."},
    {"englishWord": "account for", "meaningTr": "açıklamak, -den sorumlu olmak", "explanation": "To be the explanation or cause of something.", "note": "verb", "isVerb": True, "v2Form": "accounted for", "v3Form": "accounted for", "exampleSentence1": "High winds account for the power outage."},
    {"englishWord": "accumulate", "meaningTr": "biriktirmek, çoğalmak", "explanation": "To gather or acquire in increasing number or quantity.", "note": "verb", "isVerb": True, "v2Form": "accumulated", "v3Form": "accumulated", "exampleSentence1": "Dust tends to accumulate under the bed."},
    {"englishWord": "accumulation", "meaningTr": "birikim, toplama", "explanation": "A mass or quantity of something that has gradually gathered.", "note": "noun", "isVerb": False, "exampleSentence1": "The accumulation of snow made travel difficult."},
    {"englishWord": "acknowledge", "meaningTr": "kabul etmek, tanımak", "explanation": "To accept or admit that something is true or exists.", "note": "verb", "isVerb": True, "v2Form": "acknowledged", "v3Form": "acknowledged", "exampleSentence1": "He refused to acknowledge his mistake."},
    {"englishWord": "acknowledgement", "meaningTr": "onaylama, kabul", "explanation": "Acceptance of the truth or existence of something.", "note": "noun", "isVerb": False, "exampleSentence1": "She sent a letter as an acknowledgement of the gift."},
    {"englishWord": "address", "meaningTr": "ele almak, hitap etmek", "explanation": "To give attention to or deal with a matter or problem.", "note": "verb", "isVerb": True, "v2Form": "addressed", "v3Form": "addressed", "exampleSentence1": "We need to address the climate change issue."},
    {"englishWord": "adept at", "meaningTr": "becerikli, usta", "explanation": "Very skilled or proficient at something.", "note": "adjective", "isVerb": False, "exampleSentence1": "She is very adept at playing the piano."},
    {"englishWord": "adjacent", "meaningTr": "bitişik, komşu", "explanation": "Next to or adjoining something else.", "note": "adjective", "isVerb": False, "exampleSentence1": "The garage is adjacent to the main house."},
    {"englishWord": "adjoin", "meaningTr": "bitişik olmak, eklenmek", "explanation": "To be next to and joined with something.", "note": "verb", "isVerb": True, "v2Form": "adjoined", "v3Form": "adjoined", "exampleSentence1": "Our yard adjoins the local park."},
    {"englishWord": "admonish", "meaningTr": "uyarmak, azarlamak", "explanation": "To warn or reprimand someone firmly.", "note": "verb", "isVerb": True, "v2Form": "admonished", "v3Form": "admonished", "exampleSentence1": "The teacher admonished the students for being noisy."},
    {"englishWord": "adverse", "meaningTr": "olumsuz, zıt", "explanation": "Preventing success or development; harmful.", "note": "adjective", "isVerb": False, "exampleSentence1": "The match was cancelled due to adverse weather."},
    {"englishWord": "affection", "meaningTr": "şefkat, sevgi", "explanation": "A gentle feeling of fondness or liking.", "note": "noun", "isVerb": False, "exampleSentence1": "The child felt great affection for his dog."},
    {"englishWord": "affluent", "meaningTr": "zengin, varlıklı", "explanation": "Having a great deal of money; wealthy.", "note": "adjective", "isVerb": False, "exampleSentence1": "They live in an affluent neighborhood."},
    {"englishWord": "alleviate", "meaningTr": "hafifletmek, dindirmek", "explanation": "To make suffering or a problem less severe.", "note": "verb", "isVerb": True, "v2Form": "alleviated", "v3Form": "alleviated", "exampleSentence1": "The doctor gave me medicine to alleviate the pain."},
    {"englishWord": "amaze", "meaningTr": "şaşırtmak, hayran bırakmak", "explanation": "To fill someone with great surprise.", "note": "verb", "isVerb": True, "v2Form": "amazed", "v3Form": "amazed", "exampleSentence1": "The beauty of the mountain will amaze you."},
    {"englishWord": "appoint", "meaningTr": "atamak, görevlendirmek", "explanation": "To assign a job or role to someone.", "note": "verb", "isVerb": True, "v2Form": "appointed", "v3Form": "appointed", "exampleSentence1": "The manager decided to appoint a new assistant."},
    {"englishWord": "appreciate", "meaningTr": "takdir etmek, değerini bilmek", "explanation": "To recognize the full worth of something.", "note": "verb", "isVerb": True, "v2Form": "appreciated", "v3Form": "appreciated", "exampleSentence1": "I really appreciate your help with my project."},
    {"englishWord": "approve of", "meaningTr": "onaylamak, uygun bulmak", "explanation": "To believe that something is good or acceptable.", "note": "verb", "isVerb": True, "v2Form": "approved of", "v3Form": "approved of", "exampleSentence1": "My parents don't approve of my new hobby."},
    {"englishWord": "aptitude", "meaningTr": "yetenek, kabiliyet", "explanation": "A natural ability to do something.", "note": "noun", "isVerb": False, "exampleSentence1": "He has an aptitude for learning languages."},
    {"englishWord": "arise", "meaningTr": "ortaya çıkmak, doğmak", "explanation": "To happen; to start to exist.", "note": "verb", "isVerb": True, "v2Form": "arose", "v3Form": "arisen", "exampleSentence1": "Problems often arise during big projects."},
    {"englishWord": "arrangement", "meaningTr": "düzenleme, hazırlık", "explanation": "The action or process of arranging or being arranged.", "note": "noun", "isVerb": False, "exampleSentence1": "The flowers were in a beautiful arrangement."},
    {"englishWord": "assess", "meaningTr": "değerlendirmek, değer biçmek", "explanation": "To evaluate or estimate the nature, quality, or ability of.", "note": "verb", "isVerb": True, "v2Form": "assessed", "v3Form": "assessed", "exampleSentence1": "The teacher needs to assess the student's progress."},
    {"englishWord": "assessment", "meaningTr": "değerlendirme, ölçüm", "explanation": "The act of making a judgment about something.", "note": "noun", "isVerb": False, "exampleSentence1": "The final assessment will be a written exam."},
    {"englishWord": "assist in", "meaningTr": "yardımcı olmak", "explanation": "To help someone by doing a share of a work.", "note": "verb", "isVerb": True, "v2Form": "assisted in", "v3Form": "assisted in", "exampleSentence1": "A nurse will assist in the surgery."},
    {"englishWord": "astonish", "meaningTr": "hayretler içinde bırakmak", "explanation": "To surprise someone very much.", "note": "verb", "isVerb": True, "v2Form": "astonished", "v3Form": "astonished", "exampleSentence1": "Her sudden success will astonish everyone."},
    {"englishWord": "astonishing", "meaningTr": "şaşırtıcı, hayret verici", "explanation": "Extremely surprising or impressive.", "note": "adjective", "isVerb": False, "exampleSentence1": "The view from the top was astonishing."},
    {"englishWord": "astound", "meaningTr": "sersemletmek, şaşırtmak", "explanation": "To shock or greatly surprise.", "note": "verb", "isVerb": True, "v2Form": "astounded", "v3Form": "astounded", "exampleSentence1": "The magician's tricks astound the audience."},
    {"englishWord": "attain", "meaningTr": "elde etmek, ulaşmak", "explanation": "To succeed in getting something, usually after a lot of effort.", "note": "verb", "isVerb": True, "v2Form": "attained", "v3Form": "attained", "exampleSentence1": "She worked hard to attain her goals."},
    {"englishWord": "attribute", "meaningTr": "özellik, nitelik", "explanation": "A quality or characteristic that someone or something has.", "note": "noun", "isVerb": False, "exampleSentence1": "Patience is an essential attribute for a teacher."},
    {"englishWord": "authorize", "meaningTr": "yetki vermek", "explanation": "To give official permission for something to happen.", "note": "verb", "isVerb": True, "v2Form": "authorized", "v3Form": "authorized", "exampleSentence1": "Only the boss can authorize this payment."},
    {"englishWord": "award", "meaningTr": "ödül", "explanation": "A prize or other mark of recognition given in honor of an achievement.", "note": "noun", "isVerb": False, "exampleSentence1": "He won an award for the best short story."},
    {"englishWord": "board", "meaningTr": "binmek (gemi, uçak), kurul", "explanation": "To get on a ship, aircraft, or vehicle; or a group of people.", "note": "verb/noun", "isVerb": True, "v2Form": "boarded", "v3Form": "boarded", "exampleSentence1": "Passengers should board the plane now."},
    {"englishWord": "burden", "meaningTr": "yük, zahmet", "explanation": "A heavy load; or something difficult to carry or deal with.", "note": "noun", "isVerb": False, "exampleSentence1": "Debt can be a heavy burden for young people."},
    {"englishWord": "call off", "meaningTr": "iptal etmek", "explanation": "To cancel something that was planned.", "note": "verb", "isVerb": True, "v2Form": "called off", "v3Form": "called off", "exampleSentence1": "They decided to call off the wedding."},
    {"englishWord": "cease", "meaningTr": "durdurmak, kesmek", "explanation": "To bring or come to an end.", "note": "verb", "isVerb": True, "v2Form": "ceased", "v3Form": "ceased", "exampleSentence1": "The rain began to cease in the afternoon."},
    {"englishWord": "chief", "meaningTr": "başlıca, ana", "explanation": "Most important; main.", "note": "adjective", "isVerb": False, "exampleSentence1": "The chief reason for the meeting was the budget."},
    {"englishWord": "chiefly", "meaningTr": "başlıca, en çok", "explanation": "For the most part; mainly.", "note": "adverb", "isVerb": False, "exampleSentence1": "He is chiefly concerned with his own comfort."},
    {"englishWord": "cognitive", "meaningTr": "bilişsel, zihinsel", "explanation": "Related to the process of knowing, understanding, and learning.", "note": "adjective", "isVerb": False, "exampleSentence1": "Reading improves your cognitive skills."},
    {"englishWord": "coincidence", "meaningTr": "tesadüf", "explanation": "When two or more things happen at the same time by chance.", "note": "noun", "isVerb": False, "exampleSentence1": "It was a coincidence that we met in Paris."},
    {"englishWord": "come across", "meaningTr": "rastlamak, karşılaşmak", "explanation": "To find or meet someone or something by chance.", "note": "verb", "isVerb": True, "v2Form": "came across", "v3Form": "come across", "exampleSentence1": "I came across an old photo in the attic."},
    {"englishWord": "commerce", "meaningTr": "ticaret", "explanation": "The activity of buying and selling, especially on a large scale.", "note": "noun", "isVerb": False, "exampleSentence1": "The city is a major center of commerce."},
    {"englishWord": "commodity", "meaningTr": "ticari mal, eşya", "explanation": "A raw material or primary agricultural product that can be bought and sold.", "note": "noun", "isVerb": False, "exampleSentence1": "Oil is a very valuable commodity."},
    {"englishWord": "commonness", "meaningTr": "yaygınlık, sıradanlık", "explanation": "The state of being ordinary or occurring frequently.", "note": "noun", "isVerb": False, "exampleSentence1": "The commonness of the disease is worrying."},
    {"englishWord": "compel", "meaningTr": "zorlamak, mecbur etmek", "explanation": "To force or oblige someone to do something.", "note": "verb", "isVerb": True, "v2Form": "compelled", "v3Form": "compelled", "exampleSentence1": "The law will compel them to pay the fine."},
    {"englishWord": "compensate", "meaningTr": "tazmin etmek, telafi etmek", "explanation": "To give someone something, typically money, in recognition of loss or injury.", "note": "verb", "isVerb": True, "v2Form": "compensated", "v3Form": "compensated", "exampleSentence1": "The company will compensate you for your extra work."},
    {"englishWord": "compensate for", "meaningTr": "telafi etmek", "explanation": "To provide something good to balance the bad effects of something.", "note": "verb", "isVerb": True, "v2Form": "compensated for", "v3Form": "compensated for", "exampleSentence1": "His hard work compensated for his lack of experience."},
    {"englishWord": "competence", "meaningTr": "yetkinlik, beceri", "explanation": "The ability to do something successfully or efficiently.", "note": "noun", "isVerb": False, "exampleSentence1": "The job requires a high level of competence."},
    {"englishWord": "competent", "meaningTr": "yetkin, kabiliyetli", "explanation": "Having the necessary ability, knowledge, or skill to do something successfully.", "note": "adjective", "isVerb": False, "exampleSentence1": "She is a very competent lawyer."},
]


words_to_create2 = [
    {"englishWord": "completion", "meaningTr": "tamamlama, bitirme", "explanation": "The action or process of finishing something.", "note": "noun", "isVerb": False, "exampleSentence1": "The project is nearing completion."},
    {"englishWord": "conceptual", "meaningTr": "kavramsal", "explanation": "Based on or relating to ideas or concepts.", "note": "adjective", "isVerb": False, "exampleSentence1": "The architect presented a conceptual design."},
    {"englishWord": "conduct", "meaningTr": "yürütmek, idare etmek", "explanation": "To organize and carry out a particular activity.", "note": "verb", "isVerb": True, "v2Form": "conducted", "v3Form": "conducted", "exampleSentence1": "Scientists will conduct a new experiment."},
    {"englishWord": "confine", "meaningTr": "sınırlandırmak, hapsetmek", "explanation": "To keep or restrict someone or something within certain limits.", "note": "verb", "isVerb": True, "v2Form": "confined", "v3Form": "confined", "exampleSentence1": "Please confine your comments to the topic."},
    {"englishWord": "consecutive", "meaningTr": "ardışık, birbirini izleyen", "explanation": "Following each other continuously.", "note": "adjective", "isVerb": False, "exampleSentence1": "It rained for three consecutive days."},
    {"englishWord": "consent", "meaningTr": "razı olmak, izin vermek", "explanation": "Permission for something to happen or agreement to do something.", "note": "noun/verb", "isVerb": True, "v2Form": "consented", "v3Form": "consented", "exampleSentence1": "You need parental consent to go on the trip."},
    {"englishWord": "conserve", "meaningTr": "korumak, muhafaza etmek", "explanation": "To protect something from harm or destruction.", "note": "verb", "isVerb": True, "v2Form": "conserved", "v3Form": "conserved", "exampleSentence1": "We must conserve water during the drought."},
    {"englishWord": "consistency", "meaningTr": "tutarlılık, istikrar", "explanation": "The quality of always behaving or performing in a similar way.", "note": "noun", "isVerb": False, "exampleSentence1": "Consistency is the key to success in sports."},
    {"englishWord": "constitute", "meaningTr": "oluşturmak, kurmak", "explanation": "To be the parts that form something.", "note": "verb", "isVerb": True, "v2Form": "constituted", "v3Form": "constituted", "exampleSentence1": "Twelve people constitute a jury."},
    {"englishWord": "constraint", "meaningTr": "kısıtlama, zorlama", "explanation": "A limitation or restriction.", "note": "noun", "isVerb": False, "exampleSentence1": "Time is a major constraint for our project."},
    {"englishWord": "contract", "meaningTr": "sözleşme, daralmak", "explanation": "A written or spoken agreement; or to become smaller.", "note": "noun/verb", "isVerb": True, "v2Form": "contracted", "v3Form": "contracted", "exampleSentence1": "Metals contract when they get cold."},
    {"englishWord": "cope with", "meaningTr": "baş etmek, üstesinden gelmek", "explanation": "To deal effectively with something difficult.", "note": "verb", "isVerb": True, "v2Form": "coped with", "v3Form": "coped with", "exampleSentence1": "She is learning how to cope with stress."},
    {"englishWord": "cover up", "meaningTr": "gizlemek, örtbas etmek", "explanation": "An attempt to prevent people from discovering the truth.", "note": "verb", "isVerb": True, "v2Form": "covered up", "v3Form": "covered up", "exampleSentence1": "They tried to cover up the scandal."},
    {"englishWord": "crave", "meaningTr": "can atmak, çok istemek", "explanation": "To feel a powerful desire for something.", "note": "verb", "isVerb": True, "v2Form": "craved", "v3Form": "craved", "exampleSentence1": "Many people crave success and fame."},
    {"englishWord": "criterion", "meaningTr": "kriter, ölçüt", "explanation": "A principle or standard by which something may be judged.", "note": "noun", "isVerb": False, "exampleSentence1": "Safety is the main criterion for the project."},
    {"englishWord": "cumulative", "meaningTr": "birikmiş, kümülatif", "explanation": "Increasing or growing by accumulation or successive additions.", "note": "adjective", "isVerb": False, "exampleSentence1": "The cumulative effect of smoking is very harmful."},
    {"englishWord": "curb", "meaningTr": "kontrol altına almak, dizginlemek", "explanation": "To check or restrain something.", "note": "verb", "isVerb": True, "v2Form": "curbed", "v3Form": "curbed", "exampleSentence1": "We need to curb our spending this month."},
    {"englishWord": "cut down", "meaningTr": "azaltmak, kesmek", "explanation": "To reduce the size, amount, or quantity of something.", "note": "verb", "isVerb": True, "v2Form": "cut down", "v3Form": "cut down", "exampleSentence1": "I am trying to cut down on sugar."},
    {"englishWord": "decaying", "meaningTr": "çürüyen", "explanation": "Rotting or decomposing through the action of bacteria and fungi.", "note": "adjective", "isVerb": False, "exampleSentence1": "The smell of decaying leaves filled the forest."},
    {"englishWord": "decline", "meaningTr": "azalmak, reddetmek", "explanation": "To become smaller, fewer, or less; or to refuse politely.", "note": "verb", "isVerb": True, "v2Form": "declined", "v3Form": "declined", "exampleSentence1": "The population of the village began to decline."},
    {"englishWord": "delightful", "meaningTr": "hoş, verici", "explanation": "Causing great pleasure or delight.", "note": "adjective", "isVerb": False, "exampleSentence1": "We had a delightful evening with our friends."},
    {"englishWord": "depth", "meaningTr": "derinlik", "explanation": "The distance from the top or surface to the bottom of something.", "note": "noun", "isVerb": False, "exampleSentence1": "The depth of the pool is two meters."},
    {"englishWord": "derive from", "meaningTr": "-den türemek, gelmek", "explanation": "To obtain something from a specific source.", "note": "verb", "isVerb": True, "v2Form": "derived from", "v3Form": "derived from", "exampleSentence1": "Many English words derive from Latin."},
    {"englishWord": "desirability", "meaningTr": "çekicilik, arzu edilebilirlik", "explanation": "The quality of being worth having or doing.", "note": "noun", "isVerb": False, "exampleSentence1": "There is no doubt about the desirability of peace."},
    {"englishWord": "deteriorate", "meaningTr": "kötüleşmek, bozulmak", "explanation": "To become progressively worse.", "note": "verb", "isVerb": True, "v2Form": "deteriorated", "v3Form": "deteriorated", "exampleSentence1": "The weather began to deteriorate rapidly."},
    {"englishWord": "determination", "meaningTr": "azim, kararlılık", "explanation": "The quality of being determined; firmness of purpose.", "note": "noun", "isVerb": False, "exampleSentence1": "His determination helped him win the race."},
    {"englishWord": "detrimental", "meaningTr": "zararlı", "explanation": "Tending to cause harm.", "note": "adjective", "isVerb": False, "exampleSentence1": "Smoking is detrimental to your health."},
    {"englishWord": "dilemma", "meaningTr": "ikilem, çıkmaz", "explanation": "A situation in which a difficult choice has to be made.", "note": "noun", "isVerb": False, "exampleSentence1": "She was in a dilemma about whether to stay or leave."},
    {"englishWord": "diminish", "meaningTr": "azalmak, eksilmek", "explanation": "To make or become less.", "note": "verb", "isVerb": True, "v2Form": "diminished", "v3Form": "diminished", "exampleSentence1": "Our resources began to diminish as the winter went on."},
    {"englishWord": "dispense with", "meaningTr": "-den vazgeçmek, bırakmak", "explanation": "To manage without or get rid of.", "note": "verb", "isVerb": True, "v2Form": "dispensed with", "v3Form": "dispensed with", "exampleSentence1": "They decided to dispense with traditional formalities."},
    {"englishWord": "disputable", "meaningTr": "tartışmalı", "explanation": "Open to argument or debate.", "note": "adjective", "isVerb": False, "exampleSentence1": "The facts of the case are highly disputable."},
    {"englishWord": "disregard", "meaningTr": "göz ardı etmek, önemsememek", "explanation": "To pay no attention to; ignore.", "note": "verb", "isVerb": True, "v2Form": "disregarded", "v3Form": "disregarded", "exampleSentence1": "Please disregard the previous email."},
    {"englishWord": "diversely", "meaningTr": "çeşitli şekillerde", "explanation": "In a way that is varied or different.", "note": "adverb", "isVerb": False, "exampleSentence1": "The students were diversely talented."},
    {"englishWord": "diversity", "meaningTr": "çeşitlilik", "explanation": "The state of being diverse; variety.", "note": "noun", "isVerb": False, "exampleSentence1": "Cultural diversity is important in a society."},
    {"englishWord": "drowsy", "meaningTr": "uykulu, mahmur", "explanation": "Sleepy and lethargic; half asleep.", "note": "adjective", "isVerb": False, "exampleSentence1": "The medicine made him feel very drowsy."},
    {"englishWord": "dwindle", "meaningTr": "azalmak, küçülmek", "explanation": "To diminish gradually in size, amount, or strength.", "note": "verb", "isVerb": True, "v2Form": "dwindled", "v3Form": "dwindled", "exampleSentence1": "Supplies began to dwindle as the storm continued."},
    {"englishWord": "dwindling", "meaningTr": "azalan, tükenen", "explanation": "Gradually becoming smaller in size or amount.", "note": "adjective", "isVerb": False, "exampleSentence1": "The team had to work with dwindling resources."},
    {"englishWord": "elderly", "meaningTr": "yaşlı", "explanation": "A polite word for old people.", "note": "adjective", "isVerb": False, "exampleSentence1": "We must show respect to the elderly."},
    {"englishWord": "elevation", "meaningTr": "yükseklik, rakım", "explanation": "Height above a given level, especially sea level.", "note": "noun", "isVerb": False, "exampleSentence1": "The mountain has an elevation of 3,000 meters."},
    {"englishWord": "emergence", "meaningTr": "ortaya çıkma, oluşum", "explanation": "The process of coming into view or becoming exposed.", "note": "noun", "isVerb": False, "exampleSentence1": "The emergence of new technology changed everything."},
    {"englishWord": "endorse", "meaningTr": "onaylamak, desteklemek", "explanation": "To declare one's public approval or support of.", "note": "verb", "isVerb": True, "v2Form": "endorsed", "v3Form": "endorsed", "exampleSentence1": "The celebrity was paid to endorse the new product."},
    {"englishWord": "endure", "meaningTr": "dayanmak, katlanmak", "explanation": "To suffer something difficult or painful patiently.", "note": "verb", "isVerb": True, "v2Form": "endured", "v3Form": "endured", "exampleSentence1": "Athletes must endure hard training sessions."},
    {"englishWord": "entail", "meaningTr": "gerektirmek, kapsamak", "explanation": "To involve something as a necessary part or consequence.", "note": "verb", "isVerb": True, "v2Form": "entailed", "v3Form": "entailed", "exampleSentence1": "This job will entail a lot of travel."},
    {"englishWord": "enthusiasm", "meaningTr": "coşku, heves", "explanation": "Intense and eager enjoyment, interest, or approval.", "note": "noun", "isVerb": False, "exampleSentence1": "He showed great enthusiasm for the new project."},
    {"englishWord": "enthusiastic about", "meaningTr": "hevesli, coşkulu", "explanation": "Having or showing intense enjoyment or interest.", "note": "adjective", "isVerb": False, "exampleSentence1": "She is very enthusiastic about learning music."},
    {"englishWord": "eradicate", "meaningTr": "kökünü kazımak, yok etmek", "explanation": "To destroy completely; put an end to.", "note": "verb", "isVerb": True, "v2Form": "eradicated", "v3Form": "eradicated", "exampleSentence1": "The government aims to eradicate poverty."},
    {"englishWord": "escort", "meaningTr": "eşlik etmek, korumak", "explanation": "To accompany someone or something for protection or as a courtesy.", "note": "verb", "isVerb": True, "v2Form": "escorted", "v3Form": "escorted", "exampleSentence1": "Security guards will escort the VIP to the stage."},
    {"englishWord": "exaggerate", "meaningTr": "abartmak", "explanation": "To represent something as being better or worse than it really is.", "note": "verb", "isVerb": True, "v2Form": "exaggerated", "v3Form": "exaggerated", "exampleSentence1": "Don't exaggerate; the fish wasn't that big!"},
    {"englishWord": "fade", "meaningTr": "solmak, gözden kaybolmak", "explanation": "To gradually grow faint and disappear.", "note": "verb", "isVerb": True, "v2Form": "faded", "v3Form": "faded", "exampleSentence1": "The colors of the old photo began to fade."},
    {"englishWord": "fading", "meaningTr": "solan, zayıflayan", "explanation": "Becoming less bright, loud, or strong.", "note": "adjective", "isVerb": False, "exampleSentence1": "I could hear the fading sound of the train."},
    {"englishWord": "fallibility", "meaningTr": "yanılabilirlik", "explanation": "The tendency to make mistakes or be wrong.", "note": "noun", "isVerb": False, "exampleSentence1": "The case proved the fallibility of memory."},
]

words_to_create3 = [
    {"englishWord": "fatally", "meaningTr": "ölümcül şekilde", "explanation": "In a way that causes death.", "note": "adverb", "isVerb": False, "exampleSentence1": "The driver was fatally injured in the accident."},
    {"englishWord": "flagrantly", "meaningTr": "küstahça, göze batacak şekilde", "explanation": "In a conspicuously or obviously offensive way.", "note": "adverb", "isVerb": False, "exampleSentence1": "The rules were flagrantly ignored by the players."},
    {"englishWord": "flourish", "meaningTr": "gelişmek, serpilmek", "explanation": "To grow or develop in a healthy or vigorous way.", "note": "verb", "isVerb": True, "v2Form": "flourished", "v3Form": "flourished", "exampleSentence1": "Plants flourish in this sunny climate."},
    {"englishWord": "fluctuation", "meaningTr": "dalgalanma", "explanation": "An irregular rising and falling in number or amount.", "note": "noun", "isVerb": False, "exampleSentence1": "Prices are subject to constant fluctuation."},
    {"englishWord": "fond of", "meaningTr": "düşkün, seven", "explanation": "Having an affection or liking for.", "note": "adjective", "isVerb": False, "exampleSentence1": "My grandmother is very fond of cats."},
    {"englishWord": "foretell", "meaningTr": "kehanette bulunmak, önceden haber vermek", "explanation": "To predict the future.", "note": "verb", "isVerb": True, "v2Form": "foretold", "v3Form": "foretold", "exampleSentence1": "No one can foretell what will happen next year."},
    {"englishWord": "foster", "meaningTr": "geliştirmek, teşvik etmek", "explanation": "To encourage the development of something.", "note": "verb", "isVerb": True, "v2Form": "fostered", "v3Form": "fostered", "exampleSentence1": "The teacher tried to foster a love of reading."},
    {"englishWord": "fragile", "meaningTr": "hassas, kırılgan", "explanation": "Easily broken or damaged.", "note": "adjective", "isVerb": False, "exampleSentence1": "Please be careful; this glass vase is fragile."},
    {"englishWord": "framework", "meaningTr": "iskelet, çerçeve, yapı", "explanation": "An essential supporting structure of an object or system.", "note": "noun", "isVerb": False, "exampleSentence1": "The legal framework protects the rights of citizens."},
    {"englishWord": "gifted", "meaningTr": "üstün yetenekli", "explanation": "Having exceptional talent or natural ability.", "note": "adjective", "isVerb": False, "exampleSentence1": "He is a gifted musician who plays five instruments."},
    {"englishWord": "govern", "meaningTr": "yönetmek", "explanation": "To conduct the policy, actions, and affairs of a state or organization.", "note": "verb", "isVerb": True, "v2Form": "governed", "v3Form": "governed", "exampleSentence1": "The laws govern how we should behave in society."},
    {"englishWord": "gradually", "meaningTr": "kademeli olarak, yavaş yavaş", "explanation": "Slowly, over a period of time.", "note": "adverb", "isVerb": False, "exampleSentence1": "The weather is gradually getting warmer."},
    {"englishWord": "gratification", "meaningTr": "memnuniyet, tatmin", "explanation": "Pleasure, especially when gained from the satisfaction of a desire.", "note": "noun", "isVerb": False, "exampleSentence1": "Some people seek instant gratification from shopping."},
    {"englishWord": "grimly", "meaningTr": "sert bir şekilde, amansızca", "explanation": "In a very serious, gloomy, or depressing manner.", "note": "adverb", "isVerb": False, "exampleSentence1": "He grimly accepted the bad news."},
    {"englishWord": "halt", "meaningTr": "durmak, durdurmak", "explanation": "To bring or come to an abrupt stop.", "note": "verb/noun", "isVerb": True, "v2Form": "halted", "v3Form": "halted", "exampleSentence1": "The production was forced to halt due to a strike."},
    {"englishWord": "handicapped", "meaningTr": "engelli", "explanation": "Having a physical or mental disability.", "note": "adjective", "isVerb": False, "exampleSentence1": "The building has special ramps for handicapped people."},
    {"englishWord": "hazard", "meaningTr": "tehlike, risk", "explanation": "A danger or risk.", "note": "noun", "isVerb": False, "exampleSentence1": "Icy roads are a hazard for drivers."},
    {"englishWord": "hinder", "meaningTr": "engellemek, mani olmak", "explanation": "To create difficulties for someone or something, resulting in delay.", "note": "verb", "isVerb": True, "v2Form": "hindered", "v3Form": "hindered", "exampleSentence1": "Bad weather can hinder the rescue efforts."},
    {"englishWord": "hold back", "meaningTr": "tutmak, durdurmak", "explanation": "To prevent someone or something from moving forward.", "note": "verb", "isVerb": True, "v2Form": "held back", "v3Form": "held back", "exampleSentence1": "The police tried to hold back the crowd."},
    {"englishWord": "idle", "meaningTr": "boş, aylak, çalışmayan", "explanation": "Not working or active; lazy.", "note": "adjective", "isVerb": False, "exampleSentence1": "The machines have been idle for months."},
    {"englishWord": "imitation", "meaningTr": "taklit", "explanation": "A thing intended to simulate or copy something else.", "note": "noun", "isVerb": False, "exampleSentence1": "Children learn many things by imitation."},
    {"englishWord": "impede", "meaningTr": "engellemek, geciktirmek", "explanation": "To delay or prevent someone or something by obstructing them.", "note": "verb", "isVerb": True, "v2Form": "impeded", "v3Form": "impeded", "exampleSentence1": "A broken leg will impede his ability to walk."},
    {"englishWord": "impulse", "meaningTr": "dürtü, itki", "explanation": "A sudden strong and unreflective urge to act.", "note": "noun", "isVerb": False, "exampleSentence1": "I bought this dress on an impulse."},
    {"englishWord": "impurity", "meaningTr": "safsızlık, kirlilik", "explanation": "The quality or condition of being impure.", "note": "noun", "isVerb": False, "exampleSentence1": "The filter removes every impurity from the water."},
    {"englishWord": "incentive", "meaningTr": "teşvik, güdü", "explanation": "A thing that motivates or encourages someone to do something.", "note": "noun", "isVerb": False, "exampleSentence1": "Bonus payments are an incentive for hard work."},
    {"englishWord": "indispensable", "meaningTr": "vazgeçilmez, çok gerekli", "explanation": "Absolutely necessary.", "note": "adjective", "isVerb": False, "exampleSentence1": "Computers are indispensable in the modern office."},
    {"englishWord": "indispensable to", "meaningTr": "için vazgeçilmez", "explanation": "Absolutely necessary for a person or task.", "note": "adjective", "isVerb": False, "exampleSentence1": "Water is indispensable to all living things."},
    {"englishWord": "induce", "meaningTr": "ikna etmek, sebep olmak", "explanation": "To succeed in persuading or influencing someone to do something.", "note": "verb", "isVerb": True, "v2Form": "induced", "v3Form": "induced", "exampleSentence1": "The doctor tried to induce labor."},
    {"englishWord": "indulge in", "meaningTr": "keyif almak, şımartmak", "explanation": "To allow oneself to enjoy the pleasure of something.", "note": "verb", "isVerb": True, "v2Form": "indulged in", "v3Form": "indulged in", "exampleSentence1": "I like to indulge in a big dessert once a week."},
    {"englishWord": "infer", "meaningTr": "sonuç çıkarmak, anlam çıkarmak", "explanation": "To deduce or conclude information from evidence and reasoning.", "note": "verb", "isVerb": True, "v2Form": "inferred", "v3Form": "inferred", "exampleSentence1": "I can infer from your face that you are unhappy."},
    {"englishWord": "inhibition", "meaningTr": "çekince, engelleme", "explanation": "A feeling that makes one self-conscious and unable to act naturally.", "note": "noun", "isVerb": False, "exampleSentence1": "Alcohol can lower a person's inhibition."},
    {"englishWord": "interval", "meaningTr": "aralık, mola", "explanation": "A space of time between events or states.", "note": "noun", "isVerb": False, "exampleSentence1": "There was a short interval between the two plays."},
    {"englishWord": "intricate", "meaningTr": "karmaşık, girift", "explanation": "Very complicated or detailed.", "note": "adjective", "isVerb": False, "exampleSentence1": "The watch has an intricate mechanism."},
    {"englishWord": "invade", "meaningTr": "istila etmek", "explanation": "To enter a country or place in order to take control of it.", "note": "verb", "isVerb": True, "v2Form": "invaded", "v3Form": "invaded", "exampleSentence1": "Germany decided to invade Poland in 1939."},
    {"englishWord": "keep on", "meaningTr": "devam etmek", "explanation": "To continue doing something.", "note": "verb", "isVerb": True, "v2Form": "kept on", "v3Form": "kept on", "exampleSentence1": "You must keep on trying until you succeed."},
    {"englishWord": "leading", "meaningTr": "önde gelen, başlıca", "explanation": "Most important or most successful.", "note": "adjective", "isVerb": False, "exampleSentence1": "He is a leading expert in the field of medicine."},
    {"englishWord": "legitimacy", "meaningTr": "meşruiyet, yasallık", "explanation": "Conformity to the law or to rules.", "note": "noun", "isVerb": False, "exampleSentence1": "The people questioned the legitimacy of the election."},
    {"englishWord": "light", "meaningTr": "ışık, hafif", "explanation": "The natural agent that stimulates sight; or not heavy.", "note": "noun/adjective", "isVerb": False, "exampleSentence1": "The suitcase is very light; I can carry it."},
    {"englishWord": "likelihood", "meaningTr": "olasılık, ihtimal", "explanation": "The state or fact of something's being likely; probability.", "note": "noun", "isVerb": False, "exampleSentence1": "There is a high likelihood of rain today."},
    {"englishWord": "marginal", "meaningTr": "marjinal, çok az, önemsiz", "explanation": "Relating to or at the edge or margin; insignificant.", "note": "adjective", "isVerb": False, "exampleSentence1": "The differences between the two products are marginal."},
    {"englishWord": "measure", "meaningTr": "ölçmek, önlem", "explanation": "To ascertain the size, amount, or degree of something.", "note": "verb/noun", "isVerb": True, "v2Form": "measured", "v3Form": "measured", "exampleSentence1": "We need to measure the distance between the walls."},
    {"englishWord": "mechanism", "meaningTr": "mekanizma", "explanation": "A system of parts working together in a machine.", "note": "noun", "isVerb": False, "exampleSentence1": "The clock's mechanism is very old and delicate."},
    {"englishWord": "merit", "meaningTr": "erdem, hak, değer", "explanation": "The quality of being particularly good or worthy.", "note": "noun", "isVerb": False, "exampleSentence1": "The student was awarded a scholarship for his merit."},
    {"englishWord": "metallic", "meaningTr": "metalik", "explanation": "Of, relating to, or resembling metal.", "note": "adjective", "isVerb": False, "exampleSentence1": "The car has a beautiful metallic finish."},
    {"englishWord": "modest", "meaningTr": "mütevazı", "explanation": "Unassuming or moderate in the estimation of one's abilities.", "note": "adjective", "isVerb": False, "exampleSentence1": "Despite his wealth, he lives in a modest house."},
    {"englishWord": "naive", "meaningTr": "saf, tecrübesiz", "explanation": "Showing a lack of experience, wisdom, or judgment.", "note": "adjective", "isVerb": False, "exampleSentence1": "It was naive of him to believe everything they said."},
    {"englishWord": "obligatory", "meaningTr": "zorunlu", "explanation": "Required by a legal, moral, or other rule.", "note": "adjective", "isVerb": False, "exampleSentence1": "Wearing a seatbelt is obligatory for all passengers."},
    {"englishWord": "obstinate", "meaningTr": "inatçı", "explanation": "Stubbornly refusing to change one's opinion or chosen course of action.", "note": "adjective", "isVerb": False, "exampleSentence1": "The child was being very obstinate about eating his vegetables."},
    {"englishWord": "occasionally", "meaningTr": "ara sıra, bazen", "explanation": "At infrequent or irregular intervals; now and then.", "note": "adverb", "isVerb": False, "exampleSentence1": "I occasionally go to the cinema on weekends."},
    {"englishWord": "opponent", "meaningTr": "rakip", "explanation": "Someone who competes against or fights another in a contest or game.", "note": "noun", "isVerb": False, "exampleSentence1": "He shook hands with his opponent after the match."},
    {"englishWord": "oppression", "meaningTr": "zulüm, baskı", "explanation": "Prolonged cruel or unjust treatment or control.", "note": "noun", "isVerb": False, "exampleSentence1": "The people fought against the government's oppression."},
]

words_to_create4 = [
    {"englishWord": "originate", "meaningTr": "kaynaklanmak, başlamak", "explanation": "To have a specified beginning.", "note": "verb", "isVerb": True, "v2Form": "originated", "v3Form": "originated", "exampleSentence1": "The tradition originated in the 19th century."},
    {"englishWord": "outcome", "meaningTr": "sonuç", "explanation": "The way a thing turns out; a consequence.", "note": "noun", "isVerb": False, "exampleSentence1": "We are waiting for the outcome of the medical tests."},
    {"englishWord": "outlook", "meaningTr": "bakış açısı, görünüm", "explanation": "A person's point of view or general attitude to life.", "note": "noun", "isVerb": False, "exampleSentence1": "She has a very positive outlook on life."},
    {"englishWord": "overrule", "meaningTr": "geçersiz kılmak, reddetmek", "explanation": "To reject or disallow by exercising one's superior authority.", "note": "verb", "isVerb": True, "v2Form": "overruled", "v3Form": "overruled", "exampleSentence1": "The judge decided to overrule the lawyer's objection."},
    {"englishWord": "peculiarity", "meaningTr": "özellik, tuhaflık", "explanation": "An odd or unusual feature or habit.", "note": "noun", "isVerb": False, "exampleSentence1": "One peculiarity of the island is its unique wildlife."},
    {"englishWord": "peel", "meaningTr": "soymak (meyve, sebze)", "explanation": "To remove the outer covering or skin from a fruit or vegetable.", "note": "verb", "isVerb": True, "v2Form": "peeled", "v3Form": "peeled", "exampleSentence1": "You need to peel the potatoes before boiling them."},
    {"englishWord": "perceive", "meaningTr": "algılamak, sezmek", "explanation": "To become aware or conscious of something; come to realize.", "note": "verb", "isVerb": True, "v2Form": "perceived", "v3Form": "perceived", "exampleSentence1": "He could perceive a slight change in her tone."},
    {"englishWord": "perception", "meaningTr": "algı", "explanation": "The ability to see, hear, or become aware of something through the senses.", "note": "noun", "isVerb": False, "exampleSentence1": "The public perception of the company is improving."},
    {"englishWord": "petty", "meaningTr": "küçük, önemsiz", "explanation": "Of little importance; trivial.", "note": "adjective", "isVerb": False, "exampleSentence1": "Don't waste time on such petty details."},
    {"englishWord": "plentiful", "meaningTr": "bol, bereketli", "explanation": "Existing in or yielding great quantities; abundant.", "note": "adjective", "isVerb": False, "exampleSentence1": "Food was plentiful during the summer harvest."},
    {"englishWord": "praise", "meaningTr": "övmek", "explanation": "Express warm approval or admiration of.", "note": "verb/noun", "isVerb": True, "v2Form": "praised", "v3Form": "praised", "exampleSentence1": "The teacher decided to praise the student for her hard work."},
    {"englishWord": "precede", "meaningTr": "önce gelmek", "explanation": "To come before something in time, order, or rank.", "note": "verb", "isVerb": True, "v2Form": "preceded", "v3Form": "preceded", "exampleSentence1": "The lightning will precede the thunder."},
    {"englishWord": "preliminary", "meaningTr": "ön, başlangıç", "explanation": "Preceding or done in preparation for something fuller or more important.", "note": "adjective", "isVerb": False, "exampleSentence1": "The preliminary results of the study are promising."},
    {"englishWord": "principal", "meaningTr": "asıl, temel, okul müdürü", "explanation": "First in order of importance; main.", "note": "adjective", "isVerb": False, "exampleSentence1": "The principal reason for the meeting was the new project."},
    {"englishWord": "prior", "meaningTr": "önceki", "explanation": "Existing or coming before in time, order, or importance.", "note": "adjective", "isVerb": False, "exampleSentence1": "I had a prior engagement and couldn't attend."},
    {"englishWord": "progressive", "meaningTr": "ilerici, gelişen", "explanation": "Happening or developing gradually or in stages.", "note": "adjective", "isVerb": False, "exampleSentence1": "The company has a very progressive attitude towards technology."},
    {"englishWord": "prolong", "meaningTr": "uzatmak", "explanation": "To make something last longer.", "note": "verb", "isVerb": True, "v2Form": "prolonged", "v3Form": "prolonged", "exampleSentence1": "The medicine can prolong the patient's life."},
    {"englishWord": "propensity", "meaningTr": "eğilim, meyil", "explanation": "An inclination or natural tendency to behave in a particular way.", "note": "noun", "isVerb": False, "exampleSentence1": "He has a propensity for getting into trouble."},
    {"englishWord": "prospect", "meaningTr": "olasılık, umut, beklenti", "explanation": "The possibility or likelihood of some future event occurring.", "note": "noun", "isVerb": False, "exampleSentence1": "The prospect of a new job is very exciting."},
    {"englishWord": "prosper", "meaningTr": "refaha kavuşmak, işleri iyi gitmek", "explanation": "To succeed in material terms; be financially successful.", "note": "verb", "isVerb": True, "v2Form": "prospered", "v3Form": "prospered", "exampleSentence1": "The small business began to prosper after the investment."},
    {"englishWord": "punctuality", "meaningTr": "dakiklik", "explanation": "The fact or quality of being on time.", "note": "noun", "isVerb": False, "exampleSentence1": "Punctuality is very important in Japanese culture."},
    {"englishWord": "pursue", "meaningTr": "peşinden koşmak, takip etmek", "explanation": "To follow someone or something in order to catch or achieve them.", "note": "verb", "isVerb": True, "v2Form": "pursued", "v3Form": "pursued", "exampleSentence1": "She decided to pursue a career in medicine."},
    {"englishWord": "pursuit", "meaningTr": "kovalama, arayış", "explanation": "The action of following or pursuing someone or something.", "note": "noun", "isVerb": False, "exampleSentence1": "He spent his life in the pursuit of happiness."},
    {"englishWord": "range", "meaningTr": "aralık, çeşitlilik", "explanation": "The area of variation between upper and lower limits on a particular scale.", "note": "noun", "isVerb": False, "exampleSentence1": "The store offers a wide range of products."},
    {"englishWord": "reconcile", "meaningTr": "uzlaştırmak, barıştırmak", "explanation": "To restore friendly relations between.", "note": "verb", "isVerb": True, "v2Form": "reconciled", "v3Form": "reconciled", "exampleSentence1": "It is difficult to reconcile the two differing opinions."},
    {"englishWord": "reformer", "meaningTr": "reformcu", "explanation": "A person who makes changes to something in order to improve it.", "note": "noun", "isVerb": False, "exampleSentence1": "He was a great social reformer in the 19th century."},
    {"englishWord": "refrain from", "meaningTr": "sakınmak, kaçınmak", "explanation": "To stop oneself from doing something.", "note": "verb", "isVerb": True, "v2Form": "refrained from", "v3Form": "refrained from", "exampleSentence1": "Please refrain from talking during the movie."},
    {"englishWord": "regard", "meaningTr": "saygı, düşünmek", "explanation": "To consider or think of someone or something in a specified way.", "note": "verb", "isVerb": True, "v2Form": "regarded", "v3Form": "regarded", "exampleSentence1": "I regard him as my best friend."},
    {"englishWord": "regression", "meaningTr": "gerileme", "explanation": "A return to a former or less developed state.", "note": "noun", "isVerb": False, "exampleSentence1": "The patient's condition showed signs of regression."},
    {"englishWord": "regulatory", "meaningTr": "düzenleyici", "explanation": "Serving or intended to regulate something.", "note": "adjective", "isVerb": False, "exampleSentence1": "The government set up a new regulatory body."},
    {"englishWord": "reject", "meaningTr": "reddetmek", "explanation": "To dismiss as inadequate, inappropriate, or not to one's taste.", "note": "verb", "isVerb": True, "v2Form": "rejected", "v3Form": "rejected", "exampleSentence1": "The school decided to reject his application."},
    {"englishWord": "relative", "meaningTr": "akraba, göreceli", "explanation": "Considered in relation or in proportion to something else.", "note": "adjective", "isVerb": False, "exampleSentence1": "The success of the mission is relative."},
    {"englishWord": "relatively", "meaningTr": "nispeten, oranla", "explanation": "To a certain degree, especially when compared with other things.", "note": "adverb", "isVerb": False, "exampleSentence1": "The exam was relatively easy for most students."},
    {"englishWord": "reproach", "meaningTr": "sitem etmek, azarlamak", "explanation": "To express disapproval or disappointment.", "note": "verb", "isVerb": True, "v2Form": "reproached", "v3Form": "reproached", "exampleSentence1": "His mother reproached him for his bad behavior."},
    {"englishWord": "resemble", "meaningTr": "benzemek", "explanation": "To have a similar appearance to or qualities in common with someone or something.", "note": "verb", "isVerb": True, "v2Form": "resembled", "v3Form": "resembled", "exampleSentence1": "The baby looks like she will resemble her father."},
    {"englishWord": "resolve", "meaningTr": "çözmek, halletmek", "explanation": "To find a solution to a problem or dispute.", "note": "verb", "isVerb": True, "v2Form": "resolved", "v3Form": "resolved", "exampleSentence1": "We need to resolve this issue as soon as possible."},
    {"englishWord": "resourcefulness", "meaningTr": "beceriklilik, işini bilme", "explanation": "The ability to find quick and clever ways to overcome difficulties.", "note": "noun", "isVerb": False, "exampleSentence1": "His resourcefulness helped them survive in the forest."},
    {"englishWord": "restrain", "meaningTr": "zapt etmek, kısıtlamak", "explanation": "To prevent someone or something from doing something.", "note": "verb", "isVerb": True, "v2Form": "restrained", "v3Form": "restrained", "exampleSentence1": "He had to restrain himself from shouting."},
    {"englishWord": "retain", "meaningTr": "sürdürmek, tutmak", "explanation": "To continue to have something; keep possession of.", "note": "verb", "isVerb": True, "v2Form": "retained", "v3Form": "retained", "exampleSentence1": "The company managed to retain its best employees."},
    {"englishWord": "retard", "meaningTr": "geciktirmek, yavaşlatmak", "explanation": "To delay or hold back in terms of progress or development.", "note": "verb", "isVerb": True, "v2Form": "retarded", "v3Form": "retarded", "exampleSentence1": "The cold weather will retard the growth of the plants."},
    {"englishWord": "revoke", "meaningTr": "iptal etmek, yürürlükten kaldırmak", "explanation": "To officially cancel a decree, decision, or promise.", "note": "verb", "isVerb": True, "v2Form": "revoked", "v3Form": "revoked", "exampleSentence1": "The authorities decided to revoke his driver's license."},
    {"englishWord": "reward", "meaningTr": "ödül", "explanation": "A thing given in recognition of one's service, effort, or achievement.", "note": "noun", "isVerb": False, "exampleSentence1": "Hard work usually brings its own reward."},
    {"englishWord": "roughly", "meaningTr": "yaklaşık olarak, kabaca", "explanation": "In a manner that is not precise; approximately.", "note": "adverb", "isVerb": False, "exampleSentence1": "There were roughly 200 people at the concert."},
    {"englishWord": "rumor", "meaningTr": "söylenti, dedikodu", "explanation": "A currently circulating story or report of uncertain or doubtful truth.", "note": "noun", "isVerb": False, "exampleSentence1": "I heard a rumor that they are getting married."},
    {"englishWord": "sack", "meaningTr": "kovmak (işten), çuval", "explanation": "To dismiss someone from their job; or a large bag.", "note": "verb/noun", "isVerb": True, "v2Form": "sacked", "v3Form": "sacked", "exampleSentence1": "The boss decided to sack him for being late."},
    {"englishWord": "scarce", "meaningTr": "kıt, az", "explanation": "Insufficient for the demand; rare.", "note": "adjective", "isVerb": False, "exampleSentence1": "Food was scarce during the winter months."},
    {"englishWord": "scarcely", "meaningTr": "neredeyse hiç, güçbela", "explanation": "Only just; almost not.", "note": "adverb", "isVerb": False, "exampleSentence1": "I could scarcely believe my eyes when I saw him."},
    {"englishWord": "schooling", "meaningTr": "öğrenim, okul eğitimi", "explanation": "Education received at school.", "note": "noun", "isVerb": False, "exampleSentence1": "He had very little formal schooling as a child."},
    {"englishWord": "severely", "meaningTr": "ciddi şekilde, sertçe", "explanation": "In a very strict or intense manner.", "note": "adverb", "isVerb": False, "exampleSentence1": "The town was severely damaged by the earthquake."},
    {"englishWord": "severity", "meaningTr": "şiddet, ciddiyet", "explanation": "The fact or condition of being severe.", "note": "noun", "isVerb": False, "exampleSentence1": "The severity of the punishment surprised everyone."},
    {"englishWord": "shrink", "meaningTr": "küçülmek, çekmek", "explanation": "To become smaller in size or amount.", "note": "verb", "isVerb": True, "v2Form": "shrank", "v3Form": "shrunk", "exampleSentence1": "The sweater will shrink if you wash it in hot water."},
]

words_to_create5 = [
    {"englishWord": "skillful in", "meaningTr": "becerikli, yetenekli", "explanation": "Having or showing skill.", "note": "adjective", "isVerb": False, "exampleSentence1": "She is very skillful in repairing old watches."},
    {"englishWord": "slim", "meaningTr": "ince, zayıf", "explanation": "Gracefully thin; or small in amount.", "note": "adjective", "isVerb": False, "exampleSentence1": "He has a slim chance of winning the race."},
    {"englishWord": "spacious", "meaningTr": "geniş, ferah", "explanation": "Having ample space.", "note": "adjective", "isVerb": False, "exampleSentence1": "The living room is very bright and spacious."},
    {"englishWord": "stability", "meaningTr": "istikrar, denge", "explanation": "The state of being stable.", "note": "noun", "isVerb": False, "exampleSentence1": "Economic stability is vital for the country's growth."},
    {"englishWord": "steady", "meaningTr": "istikrarlı, sabit", "explanation": "Firmly fixed, supported, or balanced; not shaking.", "note": "adjective", "isVerb": False, "exampleSentence1": "The patient's condition is now steady."},
    {"englishWord": "steeply", "meaningTr": "dik bir şekilde, hızla", "explanation": "At a sharp angle or in a sudden way.", "note": "adverb", "isVerb": False, "exampleSentence1": "The prices of houses have risen steeply this year."},
    {"englishWord": "stretch", "meaningTr": "esnetmek, uzatmak", "explanation": "To make something longer or wider by pulling it.", "note": "verb", "isVerb": True, "v2Form": "stretched", "v3Form": "stretched", "exampleSentence1": "You should stretch your muscles before exercising."},
    {"englishWord": "subsequent", "meaningTr": "ardından gelen, sonraki", "explanation": "Coming after something in time; following.", "note": "adjective", "isVerb": False, "exampleSentence1": "The first meeting was successful, and subsequent ones were even better."},
    {"englishWord": "subside", "meaningTr": "alçalmak, hafiflemek", "explanation": "To become less intense, violent, or severe.", "note": "verb", "isVerb": True, "v2Form": "subsided", "v3Form": "subsided", "exampleSentence1": "The flood waters began to subside after two days."},
    {"englishWord": "substantial", "meaningTr": "önemli, büyük", "explanation": "Of considerable importance, size, or worth.", "note": "adjective", "isVerb": False, "exampleSentence1": "The company made a substantial profit this year."},
    {"englishWord": "successive", "meaningTr": "ardışık", "explanation": "Following one another or following others.", "note": "adjective", "isVerb": False, "exampleSentence1": "He won the tournament for three successive years."},
    {"englishWord": "superior to", "meaningTr": "-den üstün", "explanation": "Higher in rank, status, or quality.", "note": "adjective", "isVerb": False, "exampleSentence1": "This new model is superior to the old one."},
    {"englishWord": "supplement", "meaningTr": "takviye", "explanation": "Something that completes or enhances something else when added to it.", "note": "noun/verb", "isVerb": True, "v2Form": "supplemented", "v3Form": "supplemented", "exampleSentence1": "He took vitamins to supplement his diet."},
    {"englishWord": "surpass", "meaningTr": "aşmak, geçmek", "explanation": "To be greater than or better than.", "note": "verb", "isVerb": True, "v2Form": "surpassed", "v3Form": "surpassed", "exampleSentence1": "The beauty of the lake surpassed all my expectations."},
    {"englishWord": "surroundings", "meaningTr": "çevre, civar", "explanation": "The things and conditions around a person or thing.", "note": "noun", "isVerb": False, "exampleSentence1": "The hotel is set in beautiful surroundings."},
    {"englishWord": "take part in", "meaningTr": "katılmak, yer almak", "explanation": "To be involved in an activity with other people.", "note": "verb", "isVerb": True, "v2Form": "took part in", "v3Form": "taken part in", "exampleSentence1": "Many students decided to take part in the marathon."},
    {"englishWord": "take place", "meaningTr": "gerçekleşmek, meydana gelmek", "explanation": "To happen or occur, especially after being planned.", "note": "verb", "isVerb": True, "v2Form": "took place", "v3Form": "taken place", "exampleSentence1": "The festival will take place in July."},
    {"englishWord": "tear up", "meaningTr": "yırtmak, parçalamak", "explanation": "To pull something into pieces.", "note": "verb", "isVerb": True, "v2Form": "tore up", "v3Form": "torn up", "exampleSentence1": "He decided to tear up the old letters."},
    {"englishWord": "thrifty", "meaningTr": "tutumlu", "explanation": "Using money and other resources carefully and not wastefully.", "note": "adjective", "isVerb": False, "exampleSentence1": "She is very thrifty and always looks for deals."},
    {"englishWord": "trait", "meaningTr": "kişisel özellik, karakter özelliği", "explanation": "A distinguishing quality or characteristic.", "note": "noun", "isVerb": False, "exampleSentence1": "Patience is a very important trait for a doctor."},
    {"englishWord": "trajectory", "meaningTr": "yörünge, izlenen yol", "explanation": "The path followed by a projectile or object.", "note": "noun", "isVerb": False, "exampleSentence1": "The missile followed a curved trajectory."},
    {"englishWord": "transition", "meaningTr": "geçiş", "explanation": "The process of changing from one state or condition to another.", "note": "noun", "isVerb": False, "exampleSentence1": "The transition to a new school can be difficult."},
    {"englishWord": "trivial", "meaningTr": "önemsiz", "explanation": "Of little value or importance.", "note": "adjective", "isVerb": False, "exampleSentence1": "Don't worry about such trivial matters."},
    {"englishWord": "ultimately", "meaningTr": "eninde sonunda", "explanation": "Finally; in the end.", "note": "adverb", "isVerb": False, "exampleSentence1": "Ultimately, the decision is yours to make."},
    {"englishWord": "unanimous", "meaningTr": "oy birliğiyle", "explanation": "Fully in agreement; shared by everyone involved.", "note": "adjective", "isVerb": False, "exampleSentence1": "The jury reached a unanimous verdict."},
    {"englishWord": "undeniability", "meaningTr": "inkar edilemezlik", "explanation": "The quality of being impossible to deny or dispute.", "note": "noun", "isVerb": False, "exampleSentence1": "The undeniability of the facts was clear to everyone."},
    {"englishWord": "undesirable", "meaningTr": "istenmeyen", "explanation": "Not wanted or desirable because harmful or unpleasant.", "note": "adjective", "isVerb": False, "exampleSentence1": "The drug has some undesirable side effects."},
    {"englishWord": "uneasiness", "meaningTr": "huzursuzluk", "explanation": "A feeling of anxiety or discomfort.", "note": "noun", "isVerb": False, "exampleSentence1": "The news caused a lot of uneasiness among the residents."},
    {"englishWord": "unfavorable", "meaningTr": "elverişsiz, olumsuz", "explanation": "Not encouraging or approving; negative.", "note": "adjective", "isVerb": False, "exampleSentence1": "The report gave an unfavorable view of the company's future."},
    {"englishWord": "unmistakable", "meaningTr": "kusursuz, apaçık", "explanation": "Not able to be mistaken for anything else; very clear.", "note": "adjective", "isVerb": False, "exampleSentence1": "The smell of fresh coffee is unmistakable."},
    {"englishWord": "unskillful", "meaningTr": "beceriksiz", "explanation": "Lacking skill or proficiency.", "note": "adjective", "isVerb": False, "exampleSentence1": "The work was done in a very unskillful way."},
    {"englishWord": "upbringing", "meaningTr": "yetiştirilme", "explanation": "The treatment and instruction received by a child from its parents.", "note": "noun", "isVerb": False, "exampleSentence1": "He had a very strict upbringing in a small town."},
    {"englishWord": "vague", "meaningTr": "belirsiz, net olmayan", "explanation": "Not clearly expressed or understood; uncertain.", "note": "adjective", "isVerb": False, "exampleSentence1": "I have only a vague memory of the accident."},
    {"englishWord": "vital", "meaningTr": "hayati, çok önemli", "explanation": "Absolutely necessary or important; essential.", "note": "adjective", "isVerb": False, "exampleSentence1": "Vitamins are vital for maintaining good health."},
    {"englishWord": "voice", "meaningTr": "seslendirmek, dile getirmek", "explanation": "To express something in words; or the sound from the mouth.", "note": "verb/noun", "isVerb": True, "v2Form": "voiced", "v3Form": "voiced", "exampleSentence1": "Many people came to voice their concerns."}
]

# =========================
# VERİTABANINA EKLEME
# =========================

created_count = 0

part = words_to_create2

def delete():
    Word.objects.filter(owner = owner_user).delete()
    
#delete()

for word_data in part:
    new_word = Word.objects.create(
        owner=owner_user,
        visibility="private",
        wordLevel="Belirtilmemiş",
        isBaseWord=False,

        englishWord=word_data["englishWord"],
        meaningTr=word_data["meaningTr"],
        explanation=word_data["explanation"],
        note=word_data.get("note"),
        isVerb=word_data["isVerb"],

        v2Form=word_data.get("v2Form"),
        v3Form=word_data.get("v3Form"),

        exampleSentence1=word_data["exampleSentence1"],
        exampleSentence2=word_data.get("exampleSentence2"),
        exampleSentence3=word_data.get("exampleSentence3"),
    )
    
    UserWordLink.objects.create(user = owner_user, word = new_word)

    created_count += 1
    print(f"Eklendi: {word_data['englishWord']}")

print(f"\nİşlem tamamlandı. {created_count} kelime eklendi.")