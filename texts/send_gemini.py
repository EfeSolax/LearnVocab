from google.generativeai import configure, GenerativeModel
from django.conf import settings

def send_message_to_gemini(text: str, words : list) -> str:

    api_key = settings.GEMINI_API_TOKEN

    if not api_key:
        print("HATA: GOOGLE_API_KEY bulunamadı.")
        print("Lütfen .env dosyasını oluşturup anahtarınızı oraya eklediğinizden emin olun.")
        return ""

    # 3. API'yi Yapılandır
    try:
        configure(api_key=api_key)
    except ValueError:
        print("HATA: API Anahtarı geçersiz görünüyor.")
        return ""

    # 4. Modeli Başlat
    #    Bir önceki adımda öğrendiğimiz, senin hesabına tanımlı olan modeli kullanıyoruz.
    try:
        model = GenerativeModel('models/gemini-pro-latest') 
        print("Gemini modeli ('models/gemini-pro-latest') başarıyla yüklendi.")
    except Exception as e:
        print(f"HATA: Model yüklenirken bir sorun oluştu: {e}")
        return ""
    
    words_text = ""

    for word in words:
        words_text += word + ", "

    words_text.lower()
    words_text = words_text[:len(words_text)-1]

    # 5. Prompt'u Hazırla
    prompt = f"""
Birazdan sana bir ingilizce metin gönderilecek. Bu metni ingilizce öğrenmeye çalışan
biri yazdı. Bu metnin yazılma amacı kullanıcının yazma yeteneklerini geliştirmesi ve
kullanıcının öğrendiği kelimeler ile ilgili pratik yapmak. Senin görevin ise bu metni
şimdi vereceğim kriterlere göre puanlamak ve metnin düzeltilmiş veya geliştirilmiş bir
versiyonunu yazman.

Kriterler ikiye ayrılıyor: 1.Metnin içerik ve konu akışı. 2.Dilin kullanımı.

Maddeleri sırasıyla açıklayayım:

1.Metnin içeriği ve konu akışı:
Dikkat etmen gerekenler: metin formal,akademik bir dille yazılmış olmalı. Buna aykırı
olan kısımlar eksik puan almalı. Metnin bir konusu olmalı ve kullanıcı bunu metinde
yeteri kadar açık bir şekilde belirtmiş olmalı. Mesela metine konuyu belirten bir cümle
ile başlamasını tavsiye ederiz. Bunu yapmışsa veya bunu yapmasa bile konuyu yeteri kadar
açık bir şekilde belirtmişse konuyu belirtme kısmından yeteri kadar puan verebilirsin.
Yeteri kadar iyi konu belirtme kısmından 10 puan vereceksin. Bu kullanıcı konuyu 10 üzerinden
ne kadar iyi belirtmiş. Bir diğer kriter ise kullanıcı metinde bu konuyu destekleyecek 
fikirler sunmalı. Bunlar en az iki tane olmalı ve bunlardan bahsederken YETERİ KADAR detaya 
inmeli. Ne fazla detaylı olmalı ne de detay verme kısmı yetersiz kalmalı. Bunlara major 1 ve
major 2, eğer devam ediyorsa major 3 şeklinde devam et. Ve bir major'dan bahsedildikten sonra
direkt diğerine geçilmemeli. İki major arasında major'u açıklayacak bir minor olmalı. Bu minor,
major hakkında örnekler verebilir, açıklamalarda bulunabilir, detaylar verebilir. Fakat 
verilen örnekler çok fazla kişisel olmamalı. Genelde çoğu insanın rahatlıkla bilecebileceği
veya araştırıp bilgi sahibi olabileceği objektif örnekler seçilmeli. Bu major, minor ve konuyu
destekleme kısımlarından kullanıcıya 25 puan ver. Ne kadar iyi yansıtıldığı ve konunun ne kadar
güzel bir şekilde örneklendirilip açıklandığına göre puanı yüksek veya alçak tutabilirsin.
Son major ve minor'dan da bahsettikten sonra ufak bir summary (özet) kısmı olmalı. Bu kısımda
kullanıcı metininde bahsettiği şeylerden genel olarak bahsetmeli, bu kısımda bir tahmin yapabilir,
bir sonuca varabilir, bir söz (quote) paylaşabilir, ya da sadece durumu özetleyebilir. Buna göre
ve yapılan özetin metnin içeriğiyle ilgili kısmına 5 üzerinden puan ver. Son olarak ise metnin
konu ve içerik akışına göre 10 puan daha ver. Konunun akıcı ve anlaşılabilir bir şekilde işlenmiş
olmasına dikkat et. Konudan konuya ani geçişler olmamalı. Olabildiğince doğal hissettirmeli.
Buradan da metne 10 puan ver. Bu kısımı da yaptıktan sonra metnin formal (akademik) olmasına bir
puan ver. Yani metinde ne kadar formal ifadeler kullanılmış. Günlük hayatta kullanılan kelimeler
elbette KULLANILABİLİR. Ya da günlük hayatta kullanılan ifadeler KULLANILABİLİR. Fakat metnin
formal olması da gerekli. Mesela 'you gotta do that' gibi bir kullanım uygun değildir. Buradan
da metne 10 puan ver.

Yani context (metnin konu ve içerik akışının) puan dağılımı:
- Konu yeterince açık bir şekilde belirtilmiş mi? (10 puan)
- Major ve minor'lar başarılı ve dengeli bir şekilde yazılmış mı? (25 puan)
- Metnin bir özet (summary) kısmı var mı, ve ne kadar başarılı yazılmış? (5 puan)
- Metin içinde konu akışı ve ifadeler yeteri kadar akıcı ve doğal mı? (10 puan)
- Metin formal,akademik bir dille mi yazılmış? (10 puan)

2.Dilin Kullanımı:
Burada metin içinde ingilizce'nin ne ölçüde kullanıldığını test edeceksin.
Metin içinde ingilizce'nin grammer kullanımı, bağlaçların kullanımı, noun clauses ve 
relative clauses kullanımı (tabii ki bunlar kullanılmışsa), preposition'ların kullanımı
ve yerine uygunluğu gibi konulardan 20 puan vereceksin. Özellikle burada tense'lerin ve
modal'ların konu içindeki anlam bütünlüğüne ne kadar uyduğuna dikkat et. Eğer kullanılmaması
gereken bir yerde bir tense kullanılmışsa oradan puan kırabilirsin. Bu kısımdan sonra kullanıcının
kullanması gereken kelimelerin listesini sana vereceğim. Kullanıcı bu kelimelerin ne kadarını
bağlama uygun bir şekilde kullanmış, kelime türleri (noun, verb, adjective, etc.) kullanıldığı
yerlere ne kadar uygun. Buna göre bir puan ver. Tabii ki çok fazla kelime olması durumunda
kullanıcı kelimelerin çoğunu kullanamayacaktır. Bu çok sıkıntı değil. Asıl sıkıntı olan kelimelerin 
hiçbirinin ya da sadece bir tanesinin kullanılması. Eğer hiçbir kelime kullanılmamışsa veya
kelimelerden sadece bir tanesi kullanılmışsa kelime kısmında düşük ver. Fakat bir taneden daha fazla
kelime kullanılmışsa çok puan kırmamaya çalış. Buradan en fazla 1-2 puan kır. Asıl ÖNEMLİ olan
kelimelerin anlam ve yer olarak doğru yerde kullanılıp kullanılmaması. Buradan da metine 5 puan
ver. Bu kısımı da yaptıktan sonra metini noktalama işaretlerini ve büyük küçük harfleri doğru
kullanmasına göre değerlendireceksin. Eğer metin noktalama işaretlerine ve büyük küçük harfe
uygun bir şekilde kullanılmışsa buradan kullanıcıya 5 puan vereceksin. Ne kadar kötü 
kullanıldıysa veya hiç kullanılmadıysa buradan o kadar çok puan kırabilirsin.
Bu kısmı önemsiz deyip geçme özellikle noktalama işaretlerinin kullanımı önemli. (Ufak not: 
Bildiğin üzere formal yazımda bir cümleyi bitirdikten sonra ... .And, ... deyip cümleye
başlamak doğru bir kullanım değil. Özellikle bu kısımın da hatalı olduğunu dikkate almanı 
istiyorum.) Bu kısımı da yaptıktan sonra metine kullanılan özne açısından puan vermeni istiyorum.
Yani sürekli he/she his/her you gibi kullanımlar yapılması formal metinlerde doğru değil. Genellikle
people, they gibi kapsayıcı kelimelerin kullanılması doğrudur. Ayrıca bir paragraf içinde sürekli
hitabet şeklinin ve öznenin değişmesi de doğru değildir. Sana bununla ilgili doğru olmayan bir 
örnek vereyim:

People need to study English by reading a lot of materials. If a person reads a lot, he or she can learn new vocabulary easily. You see the words in different texts often. Then, a student remembers words the next time he or she sees the words. In this way, we can learn many words.

Gördüğün gibi bu metinde sürekli olarak özne değişmiş ve people, a person, he, she, we, you, a student
olmuş. Bu kullanım doğru değildir. Farklı paragraflar arasında özne değişimleri olabilir fakat bir 
paragraf içinde bu olmamalı. Buradan da metine 5 puan ver.

Bundan sonra ise metine cümlelerin kesin olup olmamaları hakkında puan ver. Çok net ve bilimsel
olarak %100 doğru olan ifadelerin aksine always, all, none gibi kullanımlar pek tasvip edilmez.
Daha çok some, many, most, often, may, can, usually, tend to, be likely to gibi kullanımlar tercih
edilmelidir. Yanlış bir kullanım örneği:

Smoking cause cancer. (Bu cümlede yargı çok kesin bir dille belirtilmiş. Bu ifade değiştirilmeli.)
Smoking can/may cause cancer. (Bu daha doğru bir kullanım.)

Kullanıcıya bu konuşma tarzına göre de puan ver. Buradan da 5 puan vermeni istiyorum.

Yani language (dilin etkin bir şekilde kullanılması) puan dağılımı:
- Grammer kurallar, özne-yüklem uyumluluğu, cümle conjunction ve prepositionları doğru kullanılmış mı? (20 puan)
- Sana gönderdiğim kelime listesinden kelimeler ne kadar anlamı ve konumu uygun olacak şekilde kullanılmış? (5 puan)
- Metnin noktalama ve büyük küçük harfleri kullanımı doğru mu? (5 puan)
- Metin içinde öznelerin kullanımı ve değişimleri doğru bir şekilde mi yapılmış? (5 puan)
- Metindeki kullanımlar ne kesinlikle, çok kesin ifadelerden yeteri kadar kaçınılmış mı? (5 puan)

Dikkate almaman ya da değerlendirmene katmaman gereken kriterler:

Kullanıcı daha yeteri kadar ingilizce öğrenememiş ya da metni yazarken ingilizce'yi yeteri
kadar aktif bir şekilde kullanamamış olabilir. Cümlelerin kompleksliği ve kullanılan kelimelerin
üst düzey olması güzeldir fakat bunu yapmamak bir sıkıntı OLMAMALI! Cümleler basit yapıda olabilir,
kullanılan ifadeler kompleks veya üst düzey olmak zorunda değil. Metnin üst düzey ifadeler içermesi
güzel bir şey ama unutma metnin bu yapıda olmaması bir değerlendirme kriteri değil. Önemli olan
kullanılan ifadeler ve cümleler konuyu başarılı bir şekilde yansıtmış mı? Kullanılan ifadelerde
gramatik olarak bir sıkıntı var mı? Değerlendirme kriteri olanlar bunlar.

Şimdi sana örnek bir metin göndereceğim. Sırasıyla her bir parçayı açıklayacağım.

There are two significant advantages of studying in a workstation. (Topic - konu bahsedilmiş.)

The first advantage is that a workstation provides a dedicated and organized space for learning, which helps effectively minimize distractions. (Major 1'den bahsedilmiş. )

When students have a specific area reserved solely for their studies, they face fewer interruptions. They are less likely to be disturbed by noise or other activities. This helps them fully immerse themselves in their tasks. This focused and distraction-free environment improves concentration and efficiency. As a result, students study more effectively and achieve better academic results. (Major 1 burada minor 1 ile başarılı bir şekilde açıklanmış.)
  
The second advantage is that studying in a workstation often means being in an environment where others are also working. (Major 2'den bahsedilmiş.)

Seeing peers engaged in their studies can be highly inspiring and energizing, encouraging students to stay focused and maintain their study routines. This sense of shared commitment and collective discipline can foster a strong work ethic, reinforce positive study habits, and increase overall motivation. (Major 2 burada minor 2 ile başarılı bir şekilde açıklanmış.)

In summary, studying in a workstation minimizes distractions, boosts focus, enhances motivation, and provides structure, creating an ideal environment for academic success. (Konuyu ve içerikleri güzelce yansıtan bir özet yapılmış.)

Bir metin bu şekilde olmalı. Dikkat ettiysen noktalama ve yazım kurallarına, grammer kurallarına ve
kullanımlara başarılı bir şekilde uyulmuş.

Şimdi ise sana metini gönderiyorum. Unutma metinde kullanılması beklenen kelimeler şunlar:

{words_text}

Bu kelimelerin ne ölçüde kullanıldığı dediğim gibi o kadar da önemli değil. Asıl önemli olan
kelimelerin kullanılan bağlam içinde uygun bir şekilde kullanılmış olması.

Şimdi sana metini yolluyorum. Metin bu:

{text}

Şimdi bu metini yukarıda verdiğim kriterlere göre değerlendir. Ve daha sonra her bir alana
ne kadar puan verdiğini açık bir şekilde belirterek fakat çok uzatmadan söyle. Daha sonra
yukarıdaki kriterlere göre uygun olacak şekilde metinde yapılabilecek ufak değişiklikleri 
belirt. Özellikle metnin language kısmı ile ilgili olan kısımlarını değerlendirmen ve düzeltme
önerilerini sunman önemli. Metnin context ve language kısımları hakkında YORUM YAPABİLİRSİN
ve AYNI ZAMANDA DÜZELTME HAKKINA DA SAHİPSİN. Eğer gidişat ve akıcılık metin içinde iyiyse
yine olabildiğince kullanıcının yazdığı metin akışına dokunma! Fakat eğer gerçekten konu 
bütünlüğü, major ve minor kısımlar yeterince güzel açıklanamamış ve konu eksik kalmış 
hissettiriyorsa metni derğiştirebilirsin. Fakat yine de EĞER GÜZEL BİR AKIŞ VARSA metnin
context kısmında OLABİLDİĞİNCE DEĞİŞİKLİK YAPMA! Fakat language kısmında gördüğün her yanlışı
düzelt. Bu gramatik hatalar, noktalama hataları, büyük küçük harf hataları, kesinlikten yeteri
kadar kaçınmama sonucu çıkan hatalar, sürekli özne değişimi ve öznelerin akademik dile uymaması
olabilir. BU HATALARI ELİNDEN GELDİĞİNCE DÜZELT!

Şimdi metine yukarıdaki kriterlere göre her kısımdan kaç puan verdiğini açıkla ve metin hakkındaki
önerilerini paylaş. Yapacaksak bahsettiğim gibi language kısmı ile ilgili düzeltmeleri yap. Ve 
sonucu bir text çıktısı olarak ver.

Ve son olarak senden şunu bekliyorum bana her bir kriterden kaç puan verdiğini EN SON SATIRINDA ver.
Sırasıyla puanların yazılacağı kriterlerin sırası:

- Konu yeterince açık bir şekilde belirtilmiş mi? (10 puan)
- Major ve minor'lar başarılı ve dengeli bir şekilde yazılmış mı? (25 puan)
- Metnin bir özet (summary) kısmı var mı, ve ne kadar başarılı yazılmış? (5 puan)
- Metin içinde konu akışı ve ifadeler yeteri kadar akıcı ve doğal mı? (10 puan)
- Metin formal,akademik bir dille mi yazılmış? (10 puan)
- Grammer kurallar, özne-yüklem uyumluluğu, cümle conjunction ve prepositionları doğru kullanılmış mı? (20 puan)
- Sana gönderdiğim kelime listesinden kelimeler ne kadar anlamı ve konumu uygun olacak şekilde kullanılmış? (5 puan)
- Metnin noktalama ve büyük küçük harfleri kullanımı doğru mu? (5 puan)
- Metin içinde öznelerin kullanımı ve değişimleri doğru bir şekilde mi yapılmış? (5 puan)
- Metindeki kullanımlar ne kesinlikle, çok kesin ifadelerden yeteri kadar kaçınılmış mı? (5 puan)

Eğer sana bir ingilizce metin örneği gönderilmemişse direkt 'Bu metin değerlendirilmedi.' şeklinde
bir cevap ver.

Eğer sana bir kelime listesi gönderilmemişse veya 1-2 kelimelik çok az kelime içeren bir 
kelime listesi gönderilmişse kelimeler kısmını dikkate alma ve kelimelerden kullanıcıya 
tam puan ver.

Senden verdiğin cevabın EN SON SATIRINDA (son satırda istiyorum çünkü cevabı \\n'e göre split ettiğimde
son elemanda cevabı açık bir şekilde görebilmek istiyorum.) cevabı bana tam olarak şu şekilde ver:

Cevabın: 
'
...
...
...

// son satır
[8,22,3,9,6,16,3,2,5,1]
'
cevabın tam olarak bu şekilde bitsin. (örnek olarak ben bu sayıları verdim, sen sırasıyla verdiğin
puanları listeye koy.)

"""

    # 6. Prompt'u Gönder ve Cevabı Al
    try:
        print("Cevap alınıyor... Lütfen bekleyin...")
        response = model.generate_content(prompt)
        
        return response.text

    except Exception as e:
        print(f"HATA: API'den cevap alınırken bir sorun oluştu: {e}")
        if "429" in e:
            return "ERROR:429"
        else:
            return ""