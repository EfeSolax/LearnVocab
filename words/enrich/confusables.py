# -*- coding: utf-8 -*-
"""
Karıştırılan kelime çiftleri: küratörlü sabit tablo.

NEDEN MODELDEN İSTEMİYORUZ: `confused_with` bağını model üretiyor ama yanlış
üretiyor. 50 kelimelik denemede `principle` ve `principal` yan yana
sorulduğu hâlde ikisini birbirine bağlamadı; onun yerine `principle ->
confused_with -> law` ve `principal -> confused_with -> main` dedi. İkisi de
EŞ ANLAMLI, karıştırılan değil. Model bu alanın ne demek olduğunu kavramıyor.

Oysa karıştırılan çiftler de sayılıdır ve sınavda puan kaybettiren yer tam
burasıdır. Yazım benzerliği ya da anlam yakınlığı yüzünden öğrencinin
sistematik olarak yanlış seçtiği çiftler — ezberlenecek değil, AYIRT
EDİLECEK bilgi.

Çift bir kez yazılır, iki yöne de otomatik açılır: `principle` sayfasında
`principal`, `principal` sayfasında `principle` görünür.

Biçim:
    (kelime_a, tür_a, kelime_b, tür_b, ayrımı anlatan not)
"""

CIFTLER = [
    # --- Yazımı neredeyse aynı ---
    ("principle", "noun", "principal", "noun",
     "Principle ilke/kural; principal okul müdürü ya da 'ana, başlıca'."),
    ("complement", "noun", "compliment", "noun",
     "Complement tamamlayan şey; compliment iltifat."),
    ("personal", "adjective", "personnel", "noun",
     "Personal kişisel; personnel bir kurumun çalışanları."),
    ("stationary", "adjective", "stationery", "noun",
     "Stationary hareketsiz; stationery kırtasiye malzemesi."),
    ("conscience", "noun", "conscious", "adjective",
     "Conscience vicdan; conscious bilinçli/farkında."),
    ("desert", "noun", "dessert", "noun",
     "Desert çöl (ilk hecede vurgu); dessert tatlı."),
    ("quiet", "adjective", "quite", "adverb",
     "Quiet sessiz; quite oldukça."),
    ("loose", "adjective", "lose", "verb",
     "Loose gevşek (sıfat); lose kaybetmek (fiil)."),
    ("later", "adverb", "latter", "adjective",
     "Later daha sonra; latter ikisinden sonuncusu."),
    ("precede", "verb", "proceed", "verb",
     "Precede önce gelmek; proceed devam etmek."),
    ("eminent", "adjective", "imminent", "adjective",
     "Eminent seçkin, saygın; imminent çok yakında olacak."),
    ("allusion", "noun", "illusion", "noun",
     "Allusion üstü kapalı gönderme; illusion yanılsama."),
    ("elicit", "verb", "illicit", "adjective",
     "Elicit ortaya çıkarmak (fiil); illicit yasa dışı (sıfat)."),
    ("discreet", "adjective", "discrete", "adjective",
     "Discreet ağzı sıkı, ihtiyatlı; discrete ayrık, birbirinden bağımsız."),
    ("ingenious", "adjective", "ingenuous", "adjective",
     "Ingenious dâhiyane; ingenuous saf, art niyetsiz."),
    ("emigrate", "verb", "immigrate", "verb",
     "Emigrate bir ülkeden ayrılmak; immigrate bir ülkeye yerleşmek."),
    ("envelop", "verb", "envelope", "noun",
     "Envelop sarmak (fiil); envelope zarf (isim)."),
    ("advice", "noun", "advise", "verb",
     "Advice tavsiye (isim); advise tavsiye etmek (fiil)."),
    ("device", "noun", "devise", "verb",
     "Device cihaz (isim); devise tasarlamak (fiil)."),
    ("effect", "noun", "affect", "verb",
     "Effect etki (isim); affect etkilemek (fiil)."),
    ("council", "noun", "counsel", "noun",
     "Council kurul, meclis; counsel öğüt ya da avukat."),
    ("moral", "adjective", "morale", "noun",
     "Moral ahlaki (sıfat); morale motivasyon, maneviyat (isim)."),
    ("statue", "noun", "statute", "noun",
     "Statue heykel; statute yasa, tüzük."),
    ("suit", "noun", "suite", "noun",
     "Suit takım elbise; suite otel süiti ya da takım."),
    ("wander", "verb", "wonder", "verb",
     "Wander amaçsızca dolaşmak; wonder merak etmek."),
    ("cite", "verb", "site", "noun",
     "Cite kaynak göstermek (fiil); site alan, yer (isim)."),
    ("than", "conjunction", "then", "adverb",
     "Than karşılaştırmada kullanılır; then 'sonra' demektir."),

    # --- Aynı kökten ama anlamı ayrışmış ---
    ("economic", "adjective", "economical", "adjective",
     "Economic ekonomiyle ilgili; economical tasarruflu, az harcayan."),
    ("continuous", "adjective", "continual", "adjective",
     "Continuous hiç kesilmeden; continual tekrar tekrar, aralıklarla."),
    ("historic", "adjective", "historical", "adjective",
     "Historic tarihe geçecek kadar önemli; historical tarihle ilgili."),
    ("classic", "adjective", "classical", "adjective",
     "Classic türünün en iyisi; classical klasik döneme ait."),
    ("electric", "adjective", "electronic", "adjective",
     "Electric elektrikle çalışan; electronic elektronik devreli."),
    ("comprehensible", "adjective", "comprehensive", "adjective",
     "Comprehensible anlaşılabilir; comprehensive kapsamlı."),
    ("respectable", "adjective", "respectful", "adjective",
     "Respectable saygın; respectful saygılı davranan."),
    ("respectful", "adjective", "respective", "adjective",
     "Respectful saygılı; respective 'her birinin kendi' demektir."),
    ("literal", "adjective", "literary", "adjective",
     "Literal birebir, harfi harfine; literary edebiyatla ilgili."),
    ("industrial", "adjective", "industrious", "adjective",
     "Industrial sanayiyle ilgili; industrious çalışkan."),
    ("credible", "adjective", "credulous", "adjective",
     "Credible inandırıcı; credulous kolay kanan."),
    ("childish", "adjective", "childlike", "adjective",
     "Childish çocukça (olumsuz); childlike çocuksu (olumlu)."),
    ("momentary", "adjective", "momentous", "adjective",
     "Momentary bir anlık; momentous son derece önemli."),
    ("temporary", "adjective", "temporal", "adjective",
     "Temporary geçici; temporal zamanla ilgili."),
    ("urban", "adjective", "urbane", "adjective",
     "Urban kentsel; urbane kibar, dünya görmüş."),
    ("human", "adjective", "humane", "adjective",
     "Human insana ait; humane insancıl, merhametli."),
    ("successful", "adjective", "successive", "adjective",
     "Successful başarılı; successive art arda gelen."),
    ("official", "adjective", "officious", "adjective",
     "Official resmî; officious burnunu sokan, emir veren."),
    ("perspective", "noun", "prospective", "adjective",
     "Perspective bakış açısı (isim); prospective müstakbel (sıfat)."),
    ("politics", "noun", "policy", "noun",
     "Politics siyaset; policy izlenen politika, kural."),
    ("formerly", "adverb", "formally", "adverb",
     "Formerly eskiden; formally resmî biçimde."),
    ("especially", "adverb", "specially", "adverb",
     "Especially özellikle, en çok; specially özel olarak, bu amaçla."),
    ("valuable", "adjective", "invaluable", "adjective",
     "İkisi de değerlidir. Invaluable 'değersiz' DEĞİL, 'paha biçilmez' demektir."),
    ("observance", "noun", "observation", "noun",
     "Observance kurala uyma; observation gözlem."),
    ("incidence", "noun", "incident", "noun",
     "Incidence görülme sıklığı; incident olay."),
    ("stimulus", "noun", "stimulant", "noun",
     "Stimulus uyaran; stimulant uyarıcı madde."),

    # --- Anlamı yakın, kullanımı farklı ---
    ("imply", "verb", "infer", "verb",
     "Imply konuşan ima eder; infer dinleyen çıkarım yapar."),
    ("ensure", "verb", "assure", "verb",
     "Ensure bir şeyi garanti altına almak; assure birine güvence vermek."),
    ("ensure", "verb", "insure", "verb",
     "Ensure sağlamak; insure sigortalamak."),
    ("borrow", "verb", "lend", "verb",
     "Borrow ödünç almak; lend ödünç vermek."),
    ("rise", "verb", "raise", "verb",
     "Rise kendiliğinden yükselir (nesne almaz); raise bir şeyi yükseltir."),
    ("lie", "verb", "lay", "verb",
     "Lie uzanmak (nesne almaz); lay bir şeyi yatırmak (nesne alır)."),
    ("remember", "verb", "remind", "verb",
     "Remember kendi hatırlar; remind başkasına hatırlatır."),
    ("steal", "verb", "rob", "verb",
     "Steal çalınan ŞEYİ alır; rob soyulan KİŞİYİ ya da yeri alır."),
    ("deny", "verb", "refuse", "verb",
     "Deny bir iddiayı reddeder (inkâr); refuse bir teklifi reddeder."),
    ("win", "verb", "beat", "verb",
     "Win maçı/ödülü kazanır; beat rakibi yener."),
    ("say", "verb", "tell", "verb",
     "Say söylenen şeye odaklanır; tell kime söylendiğine."),
    ("fewer", "adjective", "less", "adjective",
     "Fewer sayılabilenlerde; less sayılamayanlarda."),
    ("amount", "noun", "number", "noun",
     "Amount sayılamayanlarda; number sayılabilenlerde."),
    ("among", "preposition", "between", "preposition",
     "Between ikisi (ya da ayrı ayrı düşünülenler) arasında; among bir topluluğun içinde."),
    ("beside", "preposition", "besides", "preposition",
     "Beside yanında; besides ayrıca, -in dışında."),
    ("alone", "adjective", "lonely", "adjective",
     "Alone yalnız başına (durum); lonely yalnızlık hisseden (duygu)."),
    ("farther", "adverb", "further", "adverb",
     "Farther fiziksel mesafe; further derece ya da 'ayrıca'."),
    ("practice", "noun", "practise", "verb",
     "İngiliz yazımında practice isim, practise fiildir (ABD'de ikisi de practice)."),
]


def _dizin_kur():
    """Çiftleri iki yöne de açar: her kelime diğerini görür."""
    dizin = {}
    for a, pos_a, b, pos_b, not_ in CIFTLER:
        dizin.setdefault(a.lower(), []).append((b.lower(), pos_b, not_))
        dizin.setdefault(b.lower(), []).append((a.lower(), pos_a, not_))
    return dizin


DIZIN = _dizin_kur()


def bul(metin):
    """Kelimenin küratörlü karıştırılan çiftleri; yoksa boş liste."""
    return DIZIN.get((metin or "").strip().lower(), [])


def ekle(kelime):
    """
    Küratörlü `confused_with` bağlarını ekler ve modelin uydurduklarını ayıklar.

    Model bu alana eş anlamlı yazıyor (principle -> law). Küratörlü bir kayıt
    varsa modelinkini ELİYORUZ: bu alanın değeri doğruluğunda, yarısı yanlış
    bir alan öğrenciye zarar verir.
    Döner: eklenen kayıt sayısı.
    """
    from words.enrich.schema import Relation

    kayitlar = bul(kelime.text)
    if not kayitlar:
        return 0

    kelime.relations = [b for b in kelime.relations if b.type != "confused_with"]

    for hedef, pos, not_ in kayitlar:
        kelime.relations.append(Relation(
            to_word=hedef, to_pos=pos, type="confused_with", note=not_,
        ))
    return len(kayitlar)
