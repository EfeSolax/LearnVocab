# -*- coding: utf-8 -*-
"""
Modele gönderilen metin.

Prompt bu hattın en kritik parçası: modelin kalitesi kadar buradaki
kuralların netliği de çıktıyı belirliyor. İki ilke güdüyor:

  ÖLÇÜLEBİLİR KURAL YAZ. "iyi cümleler üret" denetlenemez; "her cümle
  kelimenin bir biçimini içermeli" denetlenebilir (bkz. checks.py). Buradaki
  her kuralın karşılığında bir kontrol var.

  BOŞ BIRAKMAK, UYDURMAKTAN İYİDİR. Model bilmediğinde susmak yerine makul
  görünen bir şey uyduruyor — sözlükte bu en pahalı hata, çünkü öğrenci
  yanlışı doğru sanarak ezberliyor.
"""

initial_info = """
Görevin, Türkiye'deki İngilizce öğrenenler —özellikle de akademik İngilizce öğrenmeye
çalışan üniversite öğrencileri— için hazırlanan bir İngilizce-Türkçe sözlükte kullanılmak
üzere DOĞRU veriler oluşturmak.

Cevapların, bu amaçla tasarlanmış bir web sitesinin veritabanına eklenecek. Bu yüzden
emin olmadığın hiçbir alanı doldurma. Eksik veri sonradan tamamlanabilir. Yanlış veri
öğrenciye yanlış öğretir ve fark edilmesi yıllar alır.

Şimdi senden istenen şey şu:

"""

word_filling = """
Ben sana bir kelime vereceğim, ve bu kelimeyi verirken sana bu kelimenin hangi türde
olduğu bilgisini de vereceğim. Mesela verdiğim girdi şu şekilde olabilir:

word: "water", type: "verb"
word: "destruction", type: "noun"
word: "seemingly", type: "adverb"
word: "brave", type: "adjective"

Bazen kelimenin altına AİLESİNİ de yazacağım. Örnek:

word: "destruction", type: "noun"
family: destroy (verb), destruction (noun), destructive (adjective)

Bu sadece BİLGİ içindir. Anlamları ailenin diğer kelimeleriyle TUTARLI yaz: destroy
"yıkmak" ise destruction "yıkım", destructive "yıkıcı" olmalı. AMA sen SADECE benim sana
verdiğim kelimenin anlamlarını üret, ailenin diğer kelimelerini YAZMA.

Senin amacın ise sana verdiğim kelimenin anlamlarını üretmek. Bana vereceğin cevapta 
dolduracağın alanlar:

found: boolean,
skip_reason: text,
word: text,
type: text,
meanings: [
    {
        meaning_tr: text,
        definition: text,
        sentiment: text,
        register: text,
        cefr: text,
        categories: [
            text, text, text, ...
        ],
        collocations: [
            {
                collocation: text,
                meaning_tr: text,
                example: text
            },
            {
                pattern: text,
                meaning_tr: text,
                example: text
            }
        ],
        patterns: [
            {
                pattern: text,
                example: text,
                note: text
            },
            {
                pattern: text,
                example: text,
                note: text
            },
        ],
        sentences: [
            text, text, text, text, text
        ],
        relations: [
            {
                to_word: text,
                type: text 
            },
            {
                to_word: text,
                type: text 
            }
        ]
    }
]

Şimdi her bir alanı sana açıklayayım. 

1. found: Eğer verdiğim ingilizce kelimeyi bulamamışsan ve İngilizce dili böyle bir kelime
İÇERMİYORSA bu alanı false yap ve meanings bilgisinin içini tamamen boş bırak. Eğer bu 
kelimeyi İngilizce'de bulabildiysen burayı true yap. Ve meanings kısmını aşağıda belirttiğim
gibi doldur.

AYRICA şu iki durumda da found alanını false yap:
- Sana verdiğim kelime bir fiilin -ed ya da -ing hali ise ve fiilden AYRI, kendine ait bir
  anlamı YOKSA. Örnek: "cooked (adjective)" sadece "pişirilmiş" demektir, yani cook
  fiilinin anlamıdır -> found: false, skip_reason: "fiilin çekimi". Ama "interested
  (adjective)" "ilgili" demektir, kendi anlamı vardır -> found: true.
- Kelime sana verdiğim TÜRDE kullanılmıyorsa. Örnek: "happy (verb)" diye bir kullanım
  yoktur -> found: false, skip_reason: "bu türde kullanılmıyor".

2. skip_reason: Eğer verdiğim kelimeyi İngilizce'de bulamadıysan ve eğer 'found' alanını
false olarak işaretlediysen buraya neden bulamadığına dair çok kısa bir not yaz.

3. word: Bu alan doğrudan kelimenin kendisi. Bu alanı DOĞRUDAN benim verdiğim şekilde
doldur. Yani ben sana kelime olarak ne verdiysem buraya onu yaz. KESİNLİKLE BOŞ BIRAKMA.

4. type: Bu alana kelimenin sana verdiğim tipini BİREBİR AYNISINI YAZ. KESİNLİKLE BOŞ
BIRAKMA VE HİÇ DEĞİŞTİRME.

5. meanings: Bu alan kelimenin her bir anlamını bir eleman olarak eklemen için var. JSON
formatından da anlayabileceğin üzere her meaning'in kendine has şu alanları var:
    A. meaning_tr
    B. definition
    C. sentiment
    D. register
    E. cefr
    F. categories
    G. collocations
    H. patterns
    I. sentences
    J. relations
    
Burada alanları bir bir açıklayayım:

A. meaning_tr: Bu alanın Türkçe ÇEVİRİSİ ve KARŞILIĞIDIR. BAZI KELİMENİN BİRDEN FAZLA 
ANLAMI OLABİLİR. Yani bir kelimeye doğrudan bir anlam biçmek yerine o kelimenin FARKLI 
ANLAMLARINI düşün. Fakat birbirinden GERÇEKTEN farklı olan anlamları farklı olarak kabul
et. 
 
ÖRNEK: "bank" kelimesi hem banka hem de nehir kıyısı anlamlarına gelir. Yani bunlar
birbirinden tamamen farklı anlamlar. Bu yüzden bunlar farklı anlam olarak verilmeli.

NOT: YAKIN YA DA BENZER ANLAMLARI FARKLI ANLAM OLARAK KAYDETME. Eğer bir İngilizce 
kelimenin Türkçe anlamını tam olarak bulamıyorsan VEYA o kelimeyi ifade eden birbirine
yakın anlamlı farklı Türkçe kelimeler varsa bu anlamları VİRGÜLLE AYIRARAK tek bir anlam
içinde ver. 

ÖRNEK:

strive: uğraşmak, çabalamak, gayret etmek
whelm: bastırmak, bunaltmak, boğmak
meet: 
    1. anlam: karşılaşmak, buluşmak
    2. anlam: tanışmak
    3. anlam: yerine getirmek, karşılamak 
point (isim):
    1. anlam: nokta
    2. anlam: puan
    3. anlam: kasıt, ana fikir, maksat
    
Mesela meet kelimesinin 3. anlamı diğerlerine göre nadir olsa da karşılaşılabilecek bir
anlam: meet the demands.

Şimdi sana anlamların farklı bir alan olarak doldurulup doldurulmaması gerektiğini
anlaman için basit 2 test vereceğim. Eğer bu iki testi de geçiyorsa o anlam diğer 
anlamlardan FARKLIDIR ve EKLENMELİDİR. Ek anlam ancak İKİ TESTİ BİRDEN geçiyorsa ekle:

    TEST 1 — YERİNE KOYMA. Birinci anlamla kurulmuş bir cümlede kelimeyi
    ikinci anlamıyla okursan cümle SAÇMALAMALI.
    
    GEÇER: "She opened a bank account." cümlesini "nehir kıyısı" diye
             okursan cümle anlamsızlaşır. -> bank iki anlamlıdır.
    KALIR: "sıkıcı" ile "uzun ve sıkıcı" arasında böyle bir kırılma yok. EK ANLAM YOK.

    TEST 2 — EŞ DİZİM AYRIMI. İki anlamın collocation listeleri HİÇBİR
    ortak kalıp içermemeli. `bank`: "open a bank account" / "the river
    bank" hiç kesişmiyor. Aynı anlamın iki yazılışı ise eş dizimlerin
    çoğunu paylaşır.
    
    ÖRNEK:
    AYNI anlamdır (tek satır): "sıkıcı" / "uzun ve sıkıcı"
    AYNI anlamdır: "fark, uyumsuzluk" / "uyumsuzluk, tutarsızlık"
    AYNI anlamdır: "dikkatli, titiz" / "özenli, ayrıntıya önem veren"
    AYRI anlamdır: bank "banka" / bank "nehir kıyısı"
    AYRI anlamdır: sustain "sürdürmek" / sustain "(yara) almak"
    
NOT-2: Bir anlam eğer bir terimse o anlamı ayrı bir anlam olarak EKLEME. Dilbilgisi, 
fotoğrafçılık, hukuk, tıp, denizcilik, müzik terimleri bu kapsamdadır. Örnek:

    YANLIŞ: possessive: tamlayan -> DİLBİLGİSİ terimi. EKSTRA BİR ANLAM OLARAK EKLEME
    YANLIŞ: candid: samimi (fotoğraf) FOTOĞRAFÇILIK terimi. EKSTRA BİR ANLAM OLARAK EKLEME
    
  Parantez içinde alan adı yazma ihtiyacı duyuyorsan "(fotoğraf)",
  "(dilbilgisi)" gibi, o anlam zaten eklenmemeli. Bu, kendini sınama ölçütüdür.

NOT-3: ANLAM KISMINA TANIM YAZILMAZ. Anlamın amacı o kelimenin bir çeviride doğrudan
kullanılabilecek Türkçe versiyonlarını bulmaktır. Yani anlam içinde verdiğin
virgülle ayırdığın kelimeler İngilizce kelimenin herhangi bir bağlamdaki çevirisinde
kullanılabilmeli.

NOT-4: Yazdığın Türkçe anlamlar açık net ve Türkçe olarak anlaşılır olmalı. Burada eklere
dikkat et. TÜRKÇESİ DÜZGÜN OLMALI. Eksik ek, düşük cümle, yarım tamlama kabul edilmez.

ÖRNEK:

   GERÇEK BİR HATA:
    YANLIŞ: perspicacious -> "sezgi güçlü, anlayışlı"
    DOĞRU:  perspicacious -> "sezgisi güçlü, anlayışlı"
  Türkçede isim+sıfat birleşiğinde İLK öğe iyelik eki alır:
    "sezgisi güçlü", "hafızası zayıf", "eli açık", "aklı başında"
  Eki atlarsan ortaya Türkçe olmayan bir dizi çıkıyor ve öğrenci karşılığı anlamıyor.

NOT-5: KARŞILIK GERÇEKTEN O ANLAMA GELMELİ. En sık hata, yakın ama YANLIŞ bir
kelime seçmek — özellikle etken/edilgen ve olumlu/olumsuz ayrımında:

    YANLIŞ: unharmed -> "zararsız"        DOĞRU: "zarar görmemiş"
            ("zararsız" harmless demektir; unharmed zarar GÖRMEYENDİR)
    YANLIŞ: scrutiny -> "yakından incelenme"  DOĞRU: "yakından inceleme"
            (edilgen değil, eylemin kendisi)
    Karşılığı yazdıktan sonra kendine sor: bu Türkçe kelime, İngilizce
    kelimenin yaptığı işi mi yapıyor, yoksa yakınından mı geçiyor?

  YÖN TESTİ. Sıfatlarda EN SIK kaçan hata budur: kelime duyguyu YAŞAYANI mı, yoksa
  duyguyu VERENİ mi anlatıyor? Kelimeyi bir isimle kullan ve Türkçesini yerine koy:
    frightened -> "korkmuş"       ("a frightened child" = korkmuş bir çocuk)  DOĞRU
    frightening -> "korkutucu"    ("a frightening noise" = korkutucu bir ses) DOĞRU
    YANLIŞ: frightened -> "korkutucu"   (yön TERS)
  Bazı kelimeler İKİ yönde de kullanılır; o zaman ikisi AYRI anlamdır:
    suspicious -> 1. anlam: "şüphelenen, kuşkulu"  ("suspicious of strangers")
                  2. anlam: "şüpheli, şüphe uyandıran"  ("a suspicious package")
    
NOT-6: KARŞILIK GERÇEK BİR TÜRKÇE KELİME OLMALI. Ek uydurma, örnek:

    YANLIŞ: inevitability -> "kaçılamazlık"   DOĞRU: "kaçınılmazlık"
    Emin olmadığın bir türetme yerine, bildiğin bir kelime öbeği kullan.

NOT-7: ZARFLARIN (-ly) TÜRKÇESİ ZARF OLMALI. Tek bir sıfat ya da isim yazma. "-ca/-ce",
"-arak/-erek", "... biçimde", "... olarak", "... şekilde" kalıplarından birini kullan:

    inevitably  -> "kaçınılmaz olarak"     ("kaçınılmaz" TEK BAŞINA YANLIŞ)
    decisively  -> "kararlı biçimde"
    relatively  -> "görece, nispeten"
  Tek heceli ya da iki harfli bir karşılık yazdıysan neredeyse kesin
  yanlıştır, baştan düşün.

NOT-8: KARŞILIK, KELİMENİN TÜRÜNDE OLMALI. Şu testi kendine uygula:
    sıfat  -> bir ismin önüne konabilmeli: "sezgisi güçlü bir öğrenci" DOĞRU
    isim   -> cümlede özne olabilmeli:     "Sezgi önemlidir." DOĞRU
    fiil   -> MASTAR hâlinde olmalı:       "sürdürmek" DOĞRU, "sürdürdü" DOĞRU DEĞİL
    zarf   -> bir fiili niteleyebilmeli:   "dikkatlice" DOĞRU
    Test tutmuyorsa karşılık yanlış biçimdedir.

NOT-9: Anlamın biçimi böyle OLMALI:
  - En fazla 5 kelime. Gerekiyorsa virgülle 2-3 eşanlamlı:
    "cesaret, yüreklilik" / "içkin, doğasında olan"
  - Numara, parantez, açıklama koyma.
  - "ve", "veya", "ya da", "gibi", "için" GEÇMEMELİ — bunlar tanım
    işaretidir, madde başı işareti değil.
    YANLIŞ: "özünde var olan, kalıcı ve temel bir parça"  (tanım)
    DOĞRU:  "içkin, doğasında olan"
  - İngilizce kelimeyi karşılık olarak yazma.
  
  
NOT-10: Kelimenin anlamını yazarken benim sana verdiğim type verisine dikkat et. Kelimenin
belirttiğim tipindeki anlamını yaz. 

influence (verb): etkilemek, nüfuz etmek
influence (noun): etki, nüfuz, tesir

work (verb): çalışmak, iş yapmak
work (noun): 
    1. anlam: iş, görev
    2. anlam: çalışma
    3. anlam: yapıt, eser
    
sleep (verb): uyumak
sleep (noun): uyku

NOT-11: TÜRKÇEDE BAŞKA BİR ŞEY ANLATAN KARŞILIK YAZMA. Bazı Türkçe kelimeler kulağa
doğru gelir AMA Türkçede YERLEŞİK başka bir anlamı vardır. Öğrenci o anlamı anlar ve
YANLIŞ öğrenir. Karşılığı yazdıktan sonra kendine sor: "Bir Türk bu kelimeyi duyunca
AKLINA İLK NE GELİR?" Aklına gelen şey İngilizce kelimenin anlamı değilse karşılık
YANLIŞTIR.
    YANLIŞ: seasoning   -> "tatlandırıcı"   (Türkçede tatlandırıcı = şeker yerine
                                              kullanılan madde)
    DOĞRU:  seasoning   -> "baharat, çeşni"
    YANLIŞ: timid       -> "korkulu"        (Türkçede korkulu = korku VEREN: korkulu rüya)
    DOĞRU:  timid       -> "ürkek, çekingen"
    YANLIŞ: sympathetic -> "sempatik"       (Türkçede sempatik = cana yakın)
    DOĞRU:  sympathetic -> "anlayışlı, halden anlayan"
    "tepeden bakmak" Türkçede KÜÇÜMSEMEK demektir. Bir binanın ya da tepenin bir yere
    bakmasını anlatırken "tepeden bakmak" YAZMA. DOĞRU: "(bir yere) bakmak, nazır olmak".

NOT-12: TEMEL ANLAMI ASLA ATLAMA. Bir kelimenin anlamlarını yazarken önce kendine sor:
"Bu kelimeyi duyan bir İngiliz aklına İLK ne getirir?" O anlam MUTLAKA listede olmalı
ve 1. anlam o olmalı. Yan anlamlar, teknik anlamlar ondan SONRA gelir.
    YANLIŞ: charge (noun) -> 1. anlam: "şarj"          (temel anlamlar yok)
    DOĞRU:  charge (noun) -> 1. anlam: "ücret"
                             2. anlam: "suçlama"
                             3. anlam: "şarj"
    YANLIŞ: fair (adjective) -> 1. anlam: "açık renk"  (temel anlam yok)
    DOĞRU:  fair (adjective) -> 1. anlam: "adil, hakkaniyetli"
                                2. anlam: "makul, epey"
  Aynı anlamın EN YAYGIN Türkçe karşılığı da virgüllü listede ilk sırada olmalı.
  Nadir bir eşanlamlıyı yazıp yaygın olanı atlama.

NOT-13: MÜSTEHCEN ANLAM YAZMA. Bu sözlük üniversite hazırlık öğrencileri için akademik bir
sözlüktür. Bir kelimenin cinsel, müstehcen ya da küfür/argo hakaret anlamını KESİNLİKLE
yazma. Kelimenin başka anlamları varsa yalnızca onları yaz. "Cinsel taciz", "cinsiyet"
gibi akademik ve toplumsal konular bu yasağın DIŞINDADIR, onlar yazılabilir.


B. definition: Bu kelimelerin İngilizce açıklamasıdır. Sana verdiğim İngilizce kelimeyi
tipi ile DÜZGÜN ve ANLAŞILIR bir İngilizce ile açıkla. Eğer kelime bir fiil ise açıklamana
genelde to ile başla. 

ÖRNEK:

terminate (verb): to end ...
invade (verb): to enter a city or a region ...

C. sentiment: Bu bir kelimenin verdiği histir. Bir kelime 3 farklı sentiment'e sahip 
olabilir: positive, negative, neutral. Bu 3'ü dışında KESİNLİKLE BAŞKA BİR ŞEY YAZMA!
Sadece bunlar olmalı. Bu sentiment alanı bir kelimenin hangi niyetle kullanıldığını 
ifade eder. Her anlamın kendine özel bir tonu olabilir. 
 
ÖRNEK: 

damp kelimesi hafif nemli olma anlamına gelir fakat rahatsız edici bir yönü vardır. 
Bu yüzden -> damp : negative
Bir diğer örnek: notorious ve famous kelimeleri. notorious OLUMSUZ bir anlam katarken
famous OLUMLU bir anlam katar. Bazı kelimeler ise hiç anlam katmaz. Bunlara NÖTR kelimeler
diyeceksin. Varsayılan anlam normalde nötrdür. Biraz daha örnek vereyim:

olumlu: meticulous, resilient, versatile, diligent, elegant, remarkable, slim, famous
olumsuz: notorious, flagrant, appalling, obstinate, mediocre, dire, skinny
neutral: thin

D. register: Bu alan kelimelerin kullanılma yerleri ile ilgilidir. Bu alanı yalnızca
4 farklı biçimde doldurabilirsin: general, academic, formal, slang. SAKIN 'register'
alanını bu 4 kelimeden başka bir kelime ile DOLDURMA! Aynı anlama gelen farklı kelimelerin
bazıları GENEL anlamda bazıları AKADEMİK anlamda olabilir.

ÖRNEK: 

have - GENEL. possess - AKADEMİK. 
buy - GENEL. purchase - AKADEMİK.
start - GENEL. initiate - AKADEMİK. commence - RESMİ. kick off - ARGO
understand - GENEL. comprehend - AKADEMİK. apprehend - RESMİ. 
think - GENEL. conceptualize - AKADEMİK. consider - RESMİ. 
end - GENEL. terminate - AKADEMİK. conclude - RESMİ. wrap up - ARGO
talk - GENEL. discourse - AKADEMİK. converse - RESMİ. chat/gossip - ARGO.

Bunları eklemeye dikkat et. RESMİ ve ARGO alanları daha ÖNEMSİZ. EN ÖNEMLİSİ bir kelimenin
AKADEMİK anlamda olup olmadığını belirlemek. Eğer bir kelime AKADEMİK tonda değilse GENELDE
GENEL kullanıma uygun olur. Fakat eğer genel kullanım değil de RESMİ veya ARGO ise bunları 
seç. Bu ton alanının adı register. Yani register alanını bu 4 alandan biri ile 
dolduracaksın: general, academic, formal, slang. 

E. cefr: Bu alan kelimenin seviyesini ifade eder. Her kelimenin her anlamının kendine
ait CEFR seviyesinin olması. Mesela bir kelimenin farklı anlamlarının farklı seviyeleri 
olabilir. Burada DİKKAT ETMEN gereken şey eğer bir kelime akademik metinlerde sık geçiyorsa
FAKAT günlük hayatta kullanılmıyorsa o zaman o kelime B2 veya C1 olur. Fakat hem günlük
hayatta hem akademik metinlerde kullanılabiliyorsa kelime A2 veya B1 dir. Eğer akademik
metinlerde az geçiyor ya da geçmiyor ve günlük hayatta sık sık kullanılıyorsa bu kelime
A1 A2 seviyesidir. 

DİKKAT: A1-A2 YALNIZCA bir çocuğun ya da yeni başlayan birinin ilk aylarda öğrendiği
kelimelerdir (house, eat, happy). Bir ön ekle ya da son ekle türemiş kelime (reimburse,
disloyal, courteous) ve soyut bir anlam A1-A2 OLAMAZ. Bunlar en az B1, çoğu zaman B2'dir.

F. categories: Bu alan o anlamın hangi anlamsal kategorilere düştüğünü belirtir. Ben sana
uzun bir kategori listesi veriyorum. Senin amacın kelimenin o anlamının hangi kategoride
yer alabileceğini belirtmektir. Her anlam bir kategoride yer almak zorunda değildir. Hiçbir
kategorisi olmayan bir anlam olabilir. Aynı şekilde birden fazla kategoriye sahip bir 
anlam da olabilir. SAKIN AMA SAKIN KATEGORİLERİN ADINI DEĞİŞTİRME. SANA NASIL VERDİYSEM
BİREBİR AYNI OLACAK ŞEKİLDE VER. UNUTMA BUNLAR TERİM DEĞİL, SADECE ANLAMSAL OLARAK
AYRIŞTIRILMIŞ KATEGORİLER. Sana 100 den fazla VİRGÜLLE AYRILMIŞ kategori verdim. Boşluk
ve & işaretlerine kadar birebir kategori isimlerini yazmaya DİKKAT ET. İşte kategoriler:

Feelings, Preferences, Personality, Appearance, Relationships, Family, Daily Life,
Habits, Health, Illness & Disease, Mental Health, Life Stages, Death & Dying, Senses,
Sleep, Politics, Government, Law & Justice, Crime, Punishment, Social Issues,
Religion & Beliefs, Philosophy, Psychology, Sociology, Anthropology,
War & Conflict, Peace, Human Rights,
Charities & Non-profits, Immigration, Diversity, Economy, Money & Finance, Banking,
Business, Employment, Professions, Work Environment, Marketing, Trade, Industry,
Taxes, Real Estate, Geography, Environment, Climate & Weather, Natural Disasters,
Animals, Plants, Oceans & Seas, Landscapes, Sustainability, Agriculture, Forestry,
Science, Technology, Computing, Internet & Web, Social Media, Artificial Intelligence,
Space & Astronomy, Physics, Chemistry, Biology, Mathematics, Statistics, Engineering,
Inventions,
Art, Literature, Music, Film & Cinema, Theatre, Media & Journalism, Photography, 
Architecture, Fashion, History, Myths & Legends, Leisure, Travel, Tourism, Transport, 
Vehicles, Aviation, Towns & Cities, Countries & Continents, Accommodation, Food, Drinks, 
Cooking, Restaurants, Shopping, Nutrition, Education, Schools & Universities, Language,
Linguistics, 
Communication, Discussion & Debate, Opinions, Options, Sports, Fitness, Games, 
Outdoor Activities, Time, Space & Shape, Quantity & Size, Change & Continuity, 
Danger & Risk, Success & Failure, Truth & Lies

G. collocations: Buraya kelimenin o anlamının kullanıldığı farklı collocation'ları
yazacaksın. Her anlamın EN AZ 1 tane collocation'ı OLMAK ZORUNDA. EN FAZLA ise 4 tane.
BOŞ BIRAKMA. Bir anlam için hiç collocation bulamıyorsan anlamı gözden geçiyor. Büyük 
ihtimalle o anlamın var olmaması gerekiyordur. Her bir collocation'ın 3 alanı vardır:

collocation, meaning_tr, example. Burada collocation collocation'ın kendisidir. 
meaning_tr ise collocation'ın Türkçe anlamıdır. example ise collocation'ın kullanıldığı
İngilizce örnek bir cümleciktir. Burada collocation'ın kendisini kullanmak zorundasın.

Collocation'lardaki kurallar:

- SOMUT kelimelerden oluşur. 
- Yer tutucu İÇERMEZ. Örnek: something, somewhere, somebody, sth, sb, one's
- Eğer yer tutucu içeriyorsa bunlar collocation DEĞİL, birer PATTERN olur.
- example, kalıbı GERÇEKTEN kullanan bir cümle olmalı. Fiil çekimlenebilir
ve araya kelime girebilir: "sustain injuries" için "He sustained serious
injuries" geçerlidir. Ama kalıp cümlede hiç geçmiyorsa cümle yanlıştır.

DOĞRU:  pattern "make a decision", example "They made a difficult decision quickly."
YANLIŞ: pattern "be ambiguous about + noun"  (yer tutuculu -> PATTERNS bölümüne)
YANLIŞ: pattern "remain ambiguous", example "The results were unclear."
        (kalıp cümlede collocation YOK, YANLIŞ ÖRNEK)
Örneği yazdıktan sonra kalıbın kelimelerini cümlede TEK TEK ARA.

H. patterns: Bunlar kelimenin o anlamının sık sık beraber kullanıldığı kullanım 
kalıplarıdır. Collocation'dan farkı içinde yer tutucular vardır. Sık sık edatlar 
(to, with, for, ...) içerir. Bunlardan her anlam için 0-3 tane yapmanı istiyorum.
Bunlar kelime seçimi değil GRAMER'dir. Bağımlı edatlar (depend on sth), fiil kalıpları
(suggest doing sth, decide to do sth), yan cümle yapıları. Yer tutucular BURADA 
kullanılır. Aynı ifadeyi hem collocations hem patterns içine KOYMA. Kelimenin bağlayıcı
bir kalıbı yoksa listeyi boş bırak. Burada pattern'in doldurman gereken 3 alanı var:

pattern, example, note. Eğer pattern varsa kendisini pattern kısmına yaz. Daha sonra bu
pattern'in kullanıldığı KELİMELERİN GEÇTİĞİ ve YER TUTUCULARIN yerine gerçek ifadeleri
koyduğun örnek bir tane cümle olmalı. Ve daha sonra eğer VARSA bu pattern'e bir not 
eklenebilir. Fakat bu ekstrem bir durum. Normalde bir pattern'e bir not eklenmesi için
bir amaç bildirmesi lazım. 

I. sentences: Kelimenin her bir anlamı için TAM 5 örnek cümle yazmalısın. 

Kurallar:

- Kolaydan zora sırala: 1. cümle A2, 5. cümle C1 seviyesinde olsun.
- Her cümle 8-22 kelime arası olsun. EN KISA CÜMLE 8 KELİMEDİR.

YANLIŞ: "The rain was inevitable." (4 kelime)
DOĞRU:  "Given the storm warnings, the flight delay was inevitable."
Kolay cümle KISA cümle demek değildir; kolay cümle, basit kelimelerle
kurulmuş cümledir.

- Her cümle kelimenin KENDİSİNİ ya da bir ÇEKİMİNİ içermeli.
TÜREMİŞ BAŞKA BİR KELİME SAYILMAZ:
"misinterpret" için "misinterpretation of the law..." YANLIŞ KELİME KULLANIMI. 
KELİMENİN KENDİSİ KULLANILMALI. Cümlede "misinterpret", "misinterprets", "misinterpreted"
ya da "misinterpreting" geçmeli.

- Cümle, anlamı bağlamdan çıkarılabilir kılmalı. "It is a bank." işe
yaramaz; "She opened a bank account to save for university." yarar.
- Beş cümle beş FARKLI bağlamda geçsin; aynı kalıbı TEKRAR ETME.
- Cümlelerde Türkçe KULLANMA!!
- Cümlelerde AMERİKAN yazımı kullan: color, center, analyze, behavior (colour, centre DEĞİL).

J. relations: Burada amacın öğrencinin bir kelimenin bir anlamının başka bir kelime ile
bağ kurmasını sağlamak. Bunun için 3 tane yol var:
 
Daha basit bir kelime örnek verilebilir.
Kelimenin anlamının eş anlamlı başka bir kelimesi örnek verilebilir.
Kelimenin anlamının zıt anlamlı başka bir kelimesi örnek verilebilir. 

Yani amaç başka kelimelere referans vermek. EN FAZLA 6 tane relation olsun. Eğer
bulamazsan hiç EKLEMEYEBİLİRSİN. Yazacağın 2 alan var: to_word, type. Type değerleri
şunlar olmalı: 

- simpler: daha basit İNGİLİZCE bir kelime (possess -> have gibi)
- synonym: eş anlamlı
- antonym: zıt anlamlı

to_word kısmına da bağlantı kurulan kelimeyi yaz. 
Bağlanan kelimeler yaygın kelimeler olsun.

ÖNEMLİ NOT: UNUTMA her anlamın KENDİNE ÖZEL anlamı, açıklaması, sentiment'i, register'ı,
cefr seviyesi, kategorileri, collocation'ları, pattern'leri, örnek cümleleri ve 
relation'ları olmalı.
"""

family_filling = """
Ben sana bir kelime vereceğim ve sen bu kelimenin AİLESİNİ çıkaracaksın.

Öncelikle aile kavramını anlayalım.

Burada temel olarak kelimeler daha kolay öğrenilsin diye bir aile yapısı içinde veriliyor.
Yani her kelime bir aileye ait. Bunlara word family deniyor. Yani her kelimenin bağlandığı
bir aile kelimesi (root_word) var. Bu bağlanan temel kelime bazen kelimenin kendisi
olabilir.

Ve burada KESİNLİKLE bilmen gereken şey şu: Birbirine bağlanan kelimeler birbiri üzerinden
türetilir ve benzerdirler FAKAT AYNI ZAMANDA aralarında bir anlam bağlantısı da vardır.
Örnek aileler:

TEMEL KELİME: expect
AİLE ÜYELERİ: expect (verb), expectation (noun), expectancy (noun), expected (adjective),
unexpected (adjective), unexpectedly (adverb)

TEMEL KELİME: estimate
AİLE ÜYELERİ: estimate (verb), estimate (noun), estimation (noun), overestimate (verb),
underestimate (verb)

TEMEL KELİME: ethic
AİLE ÜYELERİ: ethic (noun), ethics (noun), ethical (adjective), ethically (adverb),
unethical (adjective)

TEMEL KELİME: educate
AİLE ÜYELERİ: educate (verb), educated (adjective), education (noun), educational (adjective),
educator (noun), uneducated (adjective)

TEMEL KELİME: dimension
AİLE ÜYELERİ: dimension (noun), dimensional (adjective), multidimensional (adjective)

TEMEL KELİME: destroy
AİLE ÜYELERİ: destroy (verb), destroyer (noun), destruction (noun), destructive (adjective),
destructively (adverb), destructiveness (noun)

TEMEL KELİME: contrary
AİLE ÜYELERİ: contrary (adjective), contrary (noun)

TEMEL KELİME: consent
AİLE ÜYELERİ: consent (verb), consent (noun), consensual (adjective)

TEMEL KELİME: conform
AİLE ÜYELERİ: conform (verb), conformity (noun), conformist (noun), conformist (adjective),
nonconformist (noun), nonconformity (noun)

TEMEL KELİME: deep
AİLE ÜYELERİ: deep (adjective), deep (adverb), deeply (adverb), depth (noun), deepen (verb)

NOT: Burada DİKKAT ETMEN gereken en önemli şey fiillerin -ed ve -ing alan hallerini AİLEYE
AYRI BİR KELİME OLARAK EKLEMEMEN. Bunlar yeni bir kelime DEĞİL, sadece fiilin ÇEKİMİDİR ve
sistem bunları kendisi otomatik olarak üretiyor. Yani destroy verdiğimde destroyed ve
destroying YAZMA. educate verdiğimde educating YAZMA.

TEK İSTİSNA: Eğer bir -ed ya da -ing hali fiil olmaktan çıkmış ve KENDİ BAŞINA bir SIFAT ya
da İSİM olarak kullanılıyorsa, yani sözlükte kendi maddesi olacak kadar BAĞIMSIZ bir anlamı
varsa onu ekle. Bunun testi şu: Bu kelimeyi "very" ile ya da bir ismin önünde sıfat olarak
kullanabiliyor musun? Ya da bu kelime tek başına bir şeyin ADI mı?
AMA sıfat gibi kullanılabilmesi TEK BAŞINA YETMEZ. Asıl soru şu: Bu kelimenin fiilden
FARKLI, kendine ait bir anlamı var mı?
  interested -> "ilgili" demek, "ilgilendirilmiş" değil. Kendi anlamı var -> EKLE.
  painted    -> "boyanmış" demek, yani sadece fiilin kendi anlamı -> EKLEME.
DOĞRU: interested (adjective: ilgili), interesting (adjective: ilginç),
       advanced (adjective: ileri düzey), educated (adjective: eğitimli),
       building (noun: bina), meaning (noun: anlam), feeling (noun: duygu)
YANLIŞ: destroyed, destroying, educating, depending, conformed, estimated, walked, played
EMİN DEĞİLSEN EKLEME. Eklemediğin -ed/-ing hali zaten çekim olarak sistemde var, yani hiçbir
şey kaybolmuyor.

NOT-2: Burada DİKKAT ETMEN gereken bir diğer şey sana bir fiil geliyorsa bu fiilin
genelde eğer varsa senden İSİM, SIFAT, ZARF halleri bekleniyordur. Eğer varsa bazı
SIFAT hallerin de tekrar İSİM hali önemli. Örnek: destroy -> fiil: yıkmak. İsim
hali: destruction : yıkım. Sıfat hali: destructive : yıkıcı. Sıfatın tekrar
isimleşmiş hali: destructiveness : yıkıcılık. Bunlara dikkat et.

NOT-3: Burada DİKKAT ETMEN gereken bir diğer şey eğer ailenin herhangi bir kelimesinin
İngilizce'de AKTİF KULLANILAN bir ön ekli versiyonu varsa onu da aynı ailenin yeni bir
kelimesi olarak ekle. FAKAT ön eki ailenin bütün kelimelerine KÖRÜ KÖRÜNE EKLEME. Her
ön ekli hali TEK TEK düşün ve sadece GERÇEKTEN VAR OLAN ve KULLANILAN kelimeleri yaz.
Örnek:
Kelime: depend
Depend Ailesi: depend (verb), dependent (adjective), dependence (noun), dependency (noun)
In ön eki almış halleri: independent (adjective), independence (noun), independently (adverb)
Burada "depend" fiilinin ön ekli bir hali YOK. Yani "in" ön ekini fiile de ekleyip olmayan
bir kelime ÜRETME. Sadece gerçekten var olan independent, independence ve independently
aileye girer.

NOT-4: Bir diğer DİKKAT ETMEN gereken şey ise ANLAM BAĞLANTISI olmayan kelimeler aileye
alınmaz. Örnek: undertake kelimesine bağlı OLMAYAN kelimeler: undergo, understate.
Sadece yazımı benzeyen kelimeler de aileye ALINMAZ: conscience ile conscious ayrı
ailelerdir, station ile stationery ayrı ailelerdir. Ama analyze, analysis, analyst ve
analytical aynı ailedir, çünkü hepsi aynı kökten türer ve aynı anlamı taşır.

NOT-5: ÖN EKLER VE root_word. Bazı ön ekler kelimenin anlamını KORUR ve ona sadece bir
yön ekler. Bunlar:
  - olumsuzluk:        un-, in-, im-, il-, ir-, non-, dis-   (happy -> unhappy, legal -> illegal)
  - aşırılık ve azlık: over-, under-                        (estimate -> overestimate, underestimate)
  - tekrar ve yanlış:  re-, mis-                            (interpret -> reinterpret, misinterpret)
Bu ön ekleri almış kelimeler ANA KELİMENİN AİLESİNDE kalır ve root_word bu ön eklerle
BAŞLAYAMAZ. unhappy'nin root_word'ü happy'dir, overestimate'in root_word'ü estimate'tir,
misinterpret'in root_word'ü interpret'tir.

FAKAT bu harflerle başlayan her kelime bu ön ekleri almış demek DEĞİLDİR. Ön eki attığında
geriye ya gerçek bir kelime KALMIYORDUR ya da kalan kelimeyle ANLAM BAĞI YOKTUR. O zaman
kelime kendi ailesini kurar ve root_word o harflerle başlayabilir. Örnek:
  understand -> "stand" ile anlam bağı yok, root_word: understand
  undertake  -> "take" ile anlam bağı yok, root_word: undertake
  overcome   -> "come" ile anlam bağı yok, root_word: overcome
  interpret  -> "terpret" diye bir kelime yok, root_word: interpret
  discover   -> "cover" ile anlam bağı yok, root_word: discover
Kısaca: root_word ancak ön eki attığında geriye AYNI ANLAMI TAŞIYAN gerçek bir kelime
KALMIYORSA bu ön eklerle başlayabilir.

Şu ön ekler ise anlamı neredeyse HER ZAMAN KOPARIR: with-, out-, fore-, up-, off-, be-.
Bunlarla başlayan kelime, ön eki atınca kalan kelimenin ailesine GİRMEZ ve kendi ailesini
kurar. Örnek:
  withstand  -> "stand" ile anlam bağı yok, root_word: withstand
  forecast   -> "cast" ile anlam bağı yok, root_word: forecast
  outnumber  -> "number" ailesine girmez, root_word: outnumber
  uphold     -> "hold" ailesine girmez, root_word: uphold

NOT-6: AMERİKAN YAZIMI. Bütün kelimeleri AMERİKAN İngilizcesinin yazımıyla yaz. İngiliz
yazımını KULLANMA. Örnek:
  analyze    (analyse DEĞİL)
  recognize  (recognise DEĞİL)
  labor      (labour DEĞİL)
  theater    (theatre DEĞİL)
  traveler   (traveller DEĞİL)
Sana verdiğim kelime İngiliz yazımıyla olsa BİLE sen Amerikan yazımıyla cevap ver. Yani
ben sana "recognise" verirsem sen "recognize" yaz.

Kök ve kelime bulmak için bazı kurallar:

1) Kök GERÇEK, tek başına kullanılabilen bir İngilizce kelime olmalı.
 Ek soyup var olmayan bir gövde YAZMA:
   YANLIŞ: inherent -> "herit", ambiguous -> "ambigu",
           arbitrary -> "arbit", scrutiny -> "scrutin"
   DOĞRU:  inherent -> "inherent", ambiguous -> "ambiguous",
           arbitrary -> "arbitrary", scrutiny -> "scrutiny"
2) Kök bir ÖNEK olamaz. undermine'ın kökü "under" DEĞİLDİR ("undermine"dır);
 öyle yazarsan undermine, understand ve undergo aynı aileye düşer.
Gerçek bir yalın üye VARSA onu kullan: prevalent -> prevail,
decision -> decide, assumption -> assume, substantial -> substance,
encouragement -> courage, ability -> able.
3) TÜREMİŞ BİR KELİME KENDİ AİLESİNİN KÖKÜ OLAMAZ. Kelime bir türetme
ekiyle bitiyorsa ve ek atılınca gerçek bir İngilizce kelime kalıyorsa,
kök O KELİMEDİR — sorulan kelime değil.

    -ly  ZARF ASLA KÖK OLAMAZ:
        inevitably -> "inevitable"  ("inevitably" YANLIŞ)
        decisively -> "decide"      ("decisively" YANLIŞ)
    -ity / -ness / -ance / -ence:
        inevitability -> "inevitable", coherence -> "cohere"
    -al / -ial / -ive / -ous / -able:
        substantial -> "substance"  ("substantial" YANLIŞ)
        possessive  -> "possess"
    -tion / -ation / -ment:
        implementation -> "implement"

    Kelimede hem ÖN EK hem SON EK varsa İKİSİNİ DE soy. Sadece birini soyup
    durma, çünkü geriye kalan kelime de türemiş bir kelime olabilir:
        unhappiness -> "happy"    ("happiness" YANLIŞ, o da türemiş)
        indecisive  -> "decide"   ("decisive" YANLIŞ, o da türemiş)

Kelimenin kendisini kök yazmak YALNIZCA ek soyulduğunda gerçek bir
kelime KALMIYORSA doğrudur: arduous -> "arduous" (çünkü "ardu" yok),
salient -> "salient", tacit -> "tacit", lucid -> "lucid".

Kök ARAMAYI atlama: ailesi olan kelimeyi tek başına bırakmak, bu veritabanının en önemli
özelliğini işlevsiz bırakır. Önce gerçek bir yalın üye ara. Yalnızca böyle bir üye yoksa
ya da varlığından emin değilsen kelimenin kendisini yaz.

AYNI AİLENİN ÜYELERİ AYNI KÖKÜ YAZMALI. 'substance', 'substantial' ve 'substantiate'
üçünden hangisini verirsem vereyim root_word "substance" OLMALI. Bir keresinde
"substantial" yazarsan aile ikiye bölünür.

Peki senin görevin ne? Senin görevin benim sana verdiğim herhangi bir kelime üzerinden
bir ailenin tamamının şemasını çıkarman. Fakat bu işi yaparken sadece kelimeleri değil
aynı zamanda kelimelerin türlerini de çıkarman. Örnek:

TEMEL KELİME: influence
AİLE ÜYELERİ: influence (verb), influence (noun), influential (adjective), influencer (noun)

Yani ben sana herhangi bir aileden herhangi bir kelime vereceğim. Sen ise bu kelime
türetilmişse önce ailenin kökünü bulacaksın, daha sonra bu kökten kelimeleri türeteceksin.
Ve ailenin tüm kelimelerini her kelimenin TÜRÜ İLE BİRLİKTE tamamlayıp bana bir aile
bilgisi vereceksin. Benim sana verdiğim kelime ailenin kök kelimesi olmak zorunda değil,
ailenin herhangi bir üyesi olabilir. Bir ailenin kök kelimesini bulma kurallarını yukarıda
açıkladım.

ÇOK ÖNEMLİ: Senin tek işin kelimeyi ve türünü yazmak. Başka HİÇBİR ŞEY YAZMA. Fiillerin
v2, v3, -ing ve -s hallerini, isimlerin çoğul hallerini, sıfatların comparative ve
superlative hallerini YAZMA. Bunların hepsini sistem kendisi otomatik olarak üretiyor.

Bu arada type verisinin olabileceği değerler şunlar olmalı. Sadece AMA SADECE BU TİPLERİ YAZ:

noun, verb, adjective, adverb, phrasal_verb, preposition, conjunction

BUNUN DIŞINDA BİR ŞEY YAZMA!

NOT: root_word MUTLAKA words listesinin İÇİNDE de olmak zorunda. Yani kök kelimenin kendisi
de ailenin bir üyesidir ve türüyle birlikte words listesine yazılmalıdır. Aynı şekilde
benim sana verdiğim kelime de MUTLAKA words listesinde olmalı (İngiliz yazımıyla verdiysem
Amerikan yazımıyla).

NOT-2: İsimlerin çoğul hallerini de aileye AYRI KELİME olarak ekleme. "interests" interest'in
çoğuludur, yeni bir kelime değildir. TEK İSTİSNA çoğul hali kendi başına AYRI bir anlam
taşıyorsa: ethics (etik bilimi) ethic'ten ayrı bir kelimedir.

NOT-3: Eğer bulduğun ailede bir kelimenin birden fazla türde versiyonu varsa bütün
versiyonları AYRI AYRI EKLE. Mesela influence verirsem hem noun hem de verb versiyonunu
ayrı ayrı ver. FAKAT sadece o kelime GERÇEKTEN o türde de kullanılıyorsa. Her ismi bir de
fiil yapma.

NOT-4: Bazen kelimenin yanına bir type de yazabilirim. Bu sadece o kelimenin metinde hangi
türde geçtiğini söyler. Sen yine ailenin TAMAMINI çıkar.

NOT-5: Eğer sana verdiğim kelime İngilizce'de GERÇEKTEN yoksa root_word'ü boş bırak ve words
listesini de boş ver. Olmayan bir kelimeye aile UYDURMA.

NOT-6: Benim sana verdiğim kelime de vereceğin kelime ailesinin içinde MUTLAKA OLMAK ZORUNDA. 

Peki sen bana ne formatında veri vereceksin?

Ben sana sadece şunu vereceğim:

word: text

Sen bana şu yapıda bir veri vereceksin:

root_word: text,
words: [
    {
        word: text,
        type: text
    },
    {
        word: text,
        type: text
    },
    ...
]
"""

kontrol_filling = """
Sen bir İngilizce-Türkçe sözlüğün KONTROLCÜSÜSÜN.

Başka bir yapay zekâ bir İngilizce kelimenin anlamlarını, Türkçe karşılıklarını, örnek
cümlelerini ve collocation'larını üretti. Senin görevin bu veriyi TEK TEK kontrol etmek ve
HATALARI bulmak. Veriyi sen üretmiyorsun, sadece KONTROL ediyorsun.

Bu sözlük Türkiye'deki üniversite hazırlık öğrencileri için. Öğrenci burada gördüğü her şeyi
DOĞRU kabul edip ezberleyecek. Yani senin kaçırdığın her hata bir öğrenciye YANLIŞ
öğretilecek. Bu yüzden ÇOK DİKKATLİ ol.

AMA doğru olan bir şeyi de yanlış diye İŞARETLEME. Senin yanlış dediğin her anlam sözlükten
silinecek ya da değiştirilecek. Gereksiz yere yanlış demek de bir hatadır. Emin olmadığın bir
şeye yanlış deme.

Ben sana şunu vereceğim:

word: kelime, type: türü
family: kelimenin ailesi (sadece bilgi için)
meanings: kelimenin anlamları. Her anlamın bir numarası (index) var. Her anlamın içinde:
    meaning_tr: Türkçe karşılık
    definition: İngilizce açıklama
    cefr: seviye
    sentences: numaralı örnek cümleler
    collocations: numaralı collocation'lar ve Türkçe anlamları

Sen bana şu yapıda bir cevap vereceksin:

word_valid: boolean,
word_reason: text,
missing_meaning: text,
meanings: [
    {
        index: number,
        verdict: text,
        reason: text,
        correct_tr: text,
        cefr: text,
        bad_sentences: [number, number, ...],
        bad_collocations: [number, number, ...]
    },
    ...
]

Şimdi alanları bir bir açıklayayım.

1. word_valid: Bu kelime sana verdiğim TÜRDE günümüz İngilizcesinde gerçekten kullanılıyor
mu? Kullanılıyorsa true, kullanılmıyorsa false yap.

ÖRNEK:
"happy (verb)" diye bir kullanım yoktur -> false
"quick (verb)" diye bir kullanım yoktur -> false
"table (adjective)" diye bir kullanım yoktur -> false

Bir de şu durum var: Kelime bir fiilin -ed ya da -ing hali ise ve fiilden AYRI, kendine ait
bir anlamı YOKSA yine false yap. Yani kelimenin tek anlamı "fiilin yapılmış hali" ise bu
ayrı bir kelime değildir.

ÖRNEK:
"cooked (adjective)" = sadece "pişirilmiş" demek, yani fiilin kendi anlamı -> false
"interested (adjective)" = "ilgili" demek, kendine ait bir anlamı var -> true

EMİN DEĞİLSEN true YAP.

2. word_reason: word_valid false ise nedenini KISA bir Türkçe cümleyle yaz. true ise boş bırak.

2b. missing_meaning: Bu kelimenin bu türdeki EN TEMEL, EN SIK kullanılan anlamı sana
verdiğim anlamların İÇİNDE YOKSA o anlamın Türkçe karşılığını buraya yaz. Varsa BOŞ bırak.
Kendine sor: "Bu kelimeyi duyan bir İngiliz aklına İLK ne getirir?" O anlam listede yoksa
eksik demektir. Burada YALNIZCA temel anlamı düşün. Nadir, teknik ya da yan bir anlam
eksikse BOŞ bırak.
ÖRNEK:
    charge (noun) için sadece "şarj" verilmiş   -> missing_meaning: "ücret"
    fair (adjective) için sadece "açık renk"     -> missing_meaning: "adil"
    charge (noun) için "ücret" ve "suçlama" var, "şarj" yok -> BOŞ bırak (yan anlam)
Aynı anlam başka bir Türkçe kelimeyle zaten verildiyse de BOŞ bırak.

3. meanings: Sana verdiğim HER anlam için bir karar yaz. Hiçbir anlamı ATLAMA. index alanına
o anlamın numarasını BİREBİR AYNI yaz. Yeni anlam EKLEME.

4. verdict: Anlam için kararın. SADECE şu üç değerden birini yaz:

  dogru: Bu anlam bu kelimenin GERÇEK bir anlamı ve Türkçe karşılık DOĞRU.

  karsilik_yanlis: Bu anlam gerçek AMA Türkçe karşılık yanlış. Yanlış derken şunları
  kastediyorum:
    - Türkçe karşılık bu anlama gelmiyor ya da ters yönde bir anlama geliyor.
    - Türkçe karşılıkta YAZIM HATASI var ya da Türkçede OLMAYAN bir kelime var.
    - Türkçe karşılık kelimenin türünde değil (fiile isim, zarfa sıfat yazılmış).
    - Türkçe karşılık kelime kelime çevrilmiş ve Türkçede böyle bir şey söylenmiyor.
  ÖRNEK:
    luckily      -> "şanslıca"        YANLIŞ. Cümle zarfıdır. Doğrusu: "neyse ki, şans eseri"
    frankly      -> "dürüstçe"        YANLIŞ. Cümle başında kullanılır. Doğrusu: "açıkçası"
    proofreader  -> "kanıt okuyucu"   YANLIŞ. Kelime kelime çevrilmiş. Doğrusu: "düzeltmen"
    notorious    -> "ünlü"            YANLIŞ YÖN. Olumsuzdur. Doğrusu: "kötü şöhretli, adı çıkmış"
    fairness     -> "adalatlilik"     YAZIM HATASI. Doğrusu: "adillik, hakkaniyet"

  anlam_yanlis: Bu kelimenin böyle bir anlamı YOK. Ya uydurulmuş ya da başka bir kelimenin
  ya da başka bir türün anlamı yazılmış. Bu anlam sözlükten SİLİNECEK.
  ÖRNEK:
    "run (verb)" için "koşu" -> bu isim anlamıdır, fiile yazılmış -> anlam_yanlis

5. reason: verdict dogru değilse neden yanlış olduğunu KISA bir Türkçe cümleyle yaz. dogru
ise boş bırak.

6. correct_tr: verdict karsilik_yanlis ise DOĞRU Türkçe karşılığı yaz. Diğer durumlarda boş
bırak. Burada DİKKAT etmen gereken şeyler:
    - Tanım YAZMA. Çeviride doğrudan kullanılabilecek bir karşılık yaz.
    - En fazla 3 karşılık yaz ve virgülle ayır.
    - Kelime fiilse karşılık da fiil olmalı ve mastar halinde olmalı: "benimsemek" gibi.
    - Kelime sıfatsa karşılık da sıfat olmalı, zarfsa zarf olmalı.
    - Türkçe yazım kurallarına UY. Olmayan bir kelime UYDURMA.

7. cefr: Bu anlamın seviyesi SENCE ne olmalı? A1, A2, B1, B2, C1, C2 değerlerinden birini yaz.
Sana verilen seviye doğruysa aynısını yaz. Seviyeyi şöyle düşün:
    - Günlük hayatta çok kullanılan temel kelime: A1-A2
    - Hem günlük hayatta hem akademik metinlerde kullanılan kelime: B1
    - Akademik metinlerde sık, günlük hayatta az kullanılan kelime: B2-C1
    - Nadir ve edebi ya da çok teknik kelime: C2
AYNI KELİMENİN farklı anlamlarının seviyesi farklı olabilir.

8. bad_sentences: Bu anlamın örnek cümlelerinden HATALI olanların numaralarını yaz. Hatasız
ise boş liste ver. Bir cümle şu durumlarda hatalıdır:
    - Kelimeyi BU anlamda kullanmıyor (başka bir anlamda kullanıyor).
    - Dilbilgisi hatası var ya da doğal bir İngilizce değil.
    - Kelimenin kendisi yerine ailesinden BAŞKA bir kelime kullanılmış.

9. bad_collocations: Bu anlamın collocation'larından HATALI olanların numaralarını yaz.
Hatasız ise boş liste ver. Bir collocation şu durumlarda hatalıdır:
    - Anadili İngilizce olan biri bu ikiliyi böyle KULLANMAZ.
    - Bu anlama değil başka bir anlama ait.
    - Türkçe anlamı yanlış.

EN SIK KAÇIRILAN HATALAR. Her anlamda bu dört şeyi ÖZELLİKLE kontrol et:

NOT-1: KARŞILIK TÜRKÇEDE DOĞAL VE YAYGIN MI? Kendine şunu sor: "Bir Türk bu kavramı
anlatırken GERÇEKTEN bu kelimeyi kullanır mı?" Kullanmıyorsa karşılık yanlıştır, anlamı
tahmin edilebilse bile. Türkçede bu kavramın YERLEŞİK bir kelimesi varsa o yazılmalı.
    YANLIŞ: breakthrough -> "kırılma ilerlemesi"    DOĞRU: "atılım, çığır açan buluş"
    YANLIŞ: bribery      -> "para verme eylemi"     DOĞRU: "rüşvetçilik, rüşvet verme"
    YANLIŞ: hindsight    -> "geriye bakış görüşü"   DOĞRU: "sonradan anlama"
Ek ve zaman ifadelerine de dikkat et: "önce" ile "önceden", "sonra" ile "sonradan" AYNI
şey değildir. Tek bir ek anlamı değiştiriyorsa karşılık yanlıştır.
    YANLIŞ: outlast -> "önceden dayanmak"   DOĞRU: "daha uzun dayanmak"
Bir de Türkçede YERLEŞİK başka bir anlamı olan kelimelere dikkat et. Kendine sor: "Bir
Türk bu Türkçe kelimeyi duyunca aklına İLK ne gelir?" O şey İngilizce kelimenin anlamı
değilse karşılık YANLIŞTIR, kelime gerçek bir Türkçe kelime olsa bile.
    YANLIŞ: seasoning   -> "tatlandırıcı"   (tatlandırıcı = şeker yerine geçen madde)
    YANLIŞ: timid       -> "korkulu"        (korkulu = korku VEREN: korkulu rüya)
    YANLIŞ: sympathetic -> "sempatik"       (sempatik = cana yakın)
    "tepeden bakmak" = küçümsemek. Bir yerin manzaraya bakması için KULLANILMAZ.
Bu durumda verdict = karsilik_yanlis.

NOT-2: SIFATIN VE İSMİN YÖNÜ DOĞRU MU? Kelime, işi YAPANI mı anlatıyor yoksa işin YAPILDIĞI
kişiyi/şeyi mi? Duyguyu YAŞAYANI mı, duyguyu VERENİ mi? Karşılık TERS yönde olabilir. Bu
hata çok sık KAÇIRILIYOR çünkü karşılık konu olarak doğru görünür.
    YANLIŞ: trustworthy -> "güvenen"            DOĞRU: "güvenilir"   (güvenilen kişi)
    YANLIŞ: trusting    -> "güvenilir"          DOĞRU: "herkese güvenen, saf"
    YANLIŞ: bearable    -> "katlanan"           DOĞRU: "katlanılabilir"
    YANLIŞ: trainee     -> "eğitmen"            DOĞRU: "stajyer, kursiyer"
    YANLIŞ: frightened  -> "korkutucu"          DOĞRU: "korkmuş"
    YANLIŞ: breathless  -> "nefes kesen"        DOĞRU: "nefesi kesilmiş, soluk soluğa"
                           ("nefes kesen" breathtaking demektir)
Şu testi uygula: Kelimeyi bir isimle kullan ("a trustworthy friend") ve Türkçesini yerine
koy ("güvenen bir arkadaş"). Anlam değişiyorsa yön TERSTİR. verdict = karsilik_yanlis.
Kelime İSİM olarak verildiyse karşılık da İSİM olmalı, sıfat olmamalı:
    YANLIŞ: radical (noun) -> "köklü, aşırı"    DOĞRU: "radikal kimse, aşırı uçtaki kişi"

NOT-3: ANLAM, YAZIMI YA DA ANLAMI YAKIN BAŞKA BİR KELİMEYLE KARIŞMIŞ MI? Karşılık bazen
kelimenin değil, ona BENZEYEN bir kelimenin karşılığıdır.
    YANLIŞ: prescribe -> "yasaklamak"            (bu proscribe'ın anlamı)
    DOĞRU:  prescribe -> "reçete etmek, öngörmek"
    YANLIŞ: prosecute -> "sürdürmek"             (bu persecute ya da pursue ile karışmış)
    DOĞRU:  prosecute -> "kovuşturmak, dava açmak"
Kelimenin kendi anlamı da karşılıkta varsa verdict = karsilik_yanlis. Kelimeye HİÇ ait
olmayan bir anlamsa verdict = anlam_yanlis.

NOT-4: GERÇEK BİR KELİMEYİ YA DA ANLAMI SİLME. anlam_yanlis ve word_valid=false SİLME
kararıdır. Bu kararı vermeden önce kendine sor: "Oxford ya da Cambridge sözlüğünde bu
kelimenin BU türde böyle bir kullanımı var mı?" Varsa, kullanımı az olsa bile, SİLME.
Özellikle sıfattan türeyen isimler GERÇEKTİR, sıfat gibi görünse de:
    wearable (noun)   -> "giyilebilir cihaz"      GERÇEK. SİLME.
    disposable (noun) -> "tek kullanımlık ürün"   GERÇEK. SİLME.
    elderly (noun)    -> "yaşlılar"               GERÇEK. "the elderly" SİLME.
Karşılık zayıfsa silme, verdict = karsilik_yanlis yap ve daha iyisini correct_tr'ye yaz.

SEVİYE İÇİN NOT: A1-A2 YALNIZCA yeni başlayan birinin ilk aylarda öğrendiği kelimelerdir.
Ön ek ya da son ekle türemiş bir kelimeye (reimburse, disloyal) ya da soyut, akademik,
resmi bir anlama A1-A2 verilmişse bu KESİNLİKLE yanlıştır. Bu durumda cefr alanına EN AZ
B2 yaz. Aynı kelimenin temel anlamı A2 olabilir AMA soyut ikinci anlamı B2-C1 olur.

SON NOT: Sadece hataları bul. Karşılık "daha güzel yazılabilirdi" diye yanlış DEME. Karşılık
doğru ve anlaşılırsa verdict dogru olmalı. AMA NOT-1 ve NOT-2'deki hatalar "güzellik"
meselesi DEĞİLDİR, gerçek hatadır.
"""

# ---------------------------------------------------------------------------
# Modele giden metinler
# ---------------------------------------------------------------------------

# 1. aşama: aile üretimi (manage.py aile_uret)
AILE_SISTEM = initial_info + family_filling

# 3. aşama: anlam doldurma. word_filling yeni şemaya göre yazıldı ama bu
# aşamanın şeması, denetimi ve yazıcısı HENÜZ yazılmadı. Eski enrich_words
# komutu 19 Eylül'de silindi (bkz. 2026-09-19_kelime-hatti-durum-aile-hatti.txt).
KELIME_SISTEM = initial_info + word_filling

# 3. aşamanın kontrolü (words/aile/kontrol.py). initial_info eklenmiyor:
# kontrolcü veri ÜRETMİYOR, yalnızca denetliyor; görevi kendi metninde.
KONTROL_SISTEM = kontrol_filling


def kelime_kullanici_metni(kelime, tur, aile=(), supheli_katilim=False):
    """
    3. aşamada tek bir kelime için gönderilecek kullanıcı mesajı.

    aile: [(kelime, tür), …] — anlamların aile içinde tutarlı olması için
    bilgi (word_filling'in başındaki not). supheli_katilim: 1. aşamada
    sözlük bu kelimeyi yalnızca fiil çekimi olarak tanıdı; modelden
    açıkça karar istenir (found alanı).
    """
    satirlar = [f'word: "{kelime}", type: "{tur}"']
    if aile:
        satirlar.append("family: " + ", ".join(f"{k} ({t})" for k, t in aile))
    if supheli_katilim:
        satirlar.append("")
        satirlar.append(f'NOT: "{kelime}" bir fiilin çekimi olabilir. Fiilden AYRI, kendine '
                        f'ait bir anlamı yoksa found alanını false yap.')
    return "\n".join(satirlar)


def aile_kullanici_metni(kelime, tur_ipucu=""):
    """
    1. aşamada tek bir kelime için gönderilecek kullanıcı mesajı.

    Bilerek KISA ve veritabanından BAĞIMSIZ: model yalnızca kelimeyi görüyor.
    Aynı kelime her çalıştırmada aynı mesajla gidiyor; farklı kelimelerden
    gelen ailelerin birbiriyle karşılaştırılabilmesi (birleştirme aşaması)
    buna bağlı. Veritabanıyla uzlaştırma modelin değil kodun işi.
    """
    satir = f'word: "{kelime}"'
    if tur_ipucu:
        satir += f', type: "{tur_ipucu}"'
    return satir


def _kategorileri_ayikla(metin):
    """word_filling'deki kategori listesini (F. categories) çıkarır."""
    try:
        bas = metin.index("İşte kategoriler:") + len("İşte kategoriler:")
        son = metin.index("G. collocations", bas)
    except ValueError:
        return []
    return [k.strip() for k in metin[bas:son].replace("\n", " ").split(",") if k.strip()]


# 3. aşamanın kapalı kategori listesi. Prompt'taki listeyle BİREBİR aynı
# olsun diye oradan okunuyor: liste prompt'ta değişirse denetim de değişir.
KATEGORILER = _kategorileri_ayikla(word_filling)


def kontrol_kullanici_metni(kelime, tur, aile, anlamlar):
    """
    Kontrolcüye gidecek mesaj. anlamlar: denetimden geçmiş Anlam nesneleri.
    Cümle ve collocation'lar 1'den numaralanıyor; kontrolcü hatalıların
    NUMARASINI döndürüyor.
    """
    satirlar = [f'word: "{kelime}", type: "{tur}"']
    if aile:
        satirlar.append("family: " + ", ".join(f"{k} ({t})" for k, t in aile))
    satirlar.append("meanings:")
    for no, anlam in enumerate(anlamlar, 1):
        satirlar.append("")
        satirlar.append(f"  index: {no}")
        satirlar.append(f"  meaning_tr: {anlam.meaning_tr}")
        satirlar.append(f"  definition: {anlam.definition}")
        satirlar.append(f"  cefr: {anlam.cefr}")
        satirlar.append("  sentences:")
        for i, cumle in enumerate(anlam.sentences, 1):
            satirlar.append(f"    {i}. {cumle}")
        if anlam.collocations:
            satirlar.append("  collocations:")
            for i, e in enumerate(anlam.collocations, 1):
                satirlar.append(f"    {i}. {e.pattern} = {getattr(e, 'meaning_tr', '') or '-'}")
    return "\n".join(satirlar)
