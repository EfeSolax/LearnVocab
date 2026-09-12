# -*- coding: utf-8 -*-
"""
Türkçe-İngilizce yanlış dostlar: küratörlü sabit tablo.

NEDEN MODELDEN İSTEMİYORUZ: 50 kelimelik iki turluk denemede model tek bir
yanlış dost üretmedi — `fabric`, `magazine`, `chef`, `college`, `physician`
gibi en bariz olanlarda bile. Dahası `chef`in Türkçesini "aşçı, şef" yazarak
tuzağa kendisi düştü. Bu bilgi modelin taşımadığı bir şey; istemekte ısrar
etmek ya boş sonuç ya uydurma getirir.

Oysa bu küme SAYILIDIR. Türkçeye Fransızca/İtalyanca üzerinden girmiş,
İngilizcedeki karşılığıyla anlamı ayrışmış birkaç yüz kelime. Bir kez
yazılır, sonsuza kadar doğru kalır. Hiçbir genel sözlükte bu bilgi yok ve
Türk öğrencinin sistematik olarak yanlış yaptığı yer tam burası.

Biçim:
    KELİME: [(benzeyen Türkçe kelime, sanılan anlam, o anlamın doğru
              İngilizcesi, ek not)]

Listeyi genişletmek serbest — tek kural, GERÇEKTEN yanılttığından emin olmak.
`restaurant/restoran` gibi anlamı aynı olanlar buraya girmez.
"""

YANLIS_DOSTLAR = {
    # --- Eğitim ve meslek ---
    "college": [("kolej", "özel lise", "private high school",
                 "College yükseköğretim kurumudur; Türkiye'deki 'kolej' lise demek.")],
    "physician": [("fizikçi", "fizik bilimci", "physicist",
                   "Physician hekimdir. Fizikçi = physicist.")],
    "chef": [("şef", "yönetici, patron", "boss / chief / manager",
              "Chef yalnızca mutfak şefidir. İş yerindeki şef = boss.")],
    "faculty": [("fakülte", "üniversite bölümü", "school / department",
                 "Faculty ABD'de öğretim üyeleri topluluğudur.")],
    "gymnasium": [("jimnastik", "jimnastik sporu", "gymnastics",
                   "Gymnasium spor salonudur.")],
    "master": [("master", "yüksek lisans", "master's degree",
                "Tek başına master 'usta, uzman' demektir.")],
    "manager": [("menajer", "sanatçı/sporcu menajeri", "agent",
                 "Manager yöneticidir; sanatçı menajeri = agent.")],
    "director": [("direktör", "yalnızca üst yönetici", "executive",
                  "Director ayrıca film yönetmeni demektir.")],
    "veteran": [("veteriner", "hayvan doktoru", "veterinarian / vet",
                 "Veteran kıdemli/gazi demektir.")],
    "personal": [("personel", "çalışanlar", "personnel / staff",
                  "Personal 'kişisel' demektir; çalışanlar = personnel.")],
    "critic": [("kritik", "kritik, önemli", "critical",
                "Critic eleştirmendir; sıfat hâli critical.")],
    "curse": [("kurs", "ders, eğitim", "course",
               "Curse lanet demektir.")],
    "stage": [("staj", "işletmede eğitim", "internship",
               "Stage sahne ya da aşama demektir.")],
    "expertise": [("ekspertiz", "değer biçme, hasar tespiti", "appraisal / valuation",
                   "Expertise uzmanlık demektir.")],

    # --- Duygu, kişilik, davranış ---
    "sympathetic": [("sempatik", "cana yakın, hoş", "likeable / friendly",
                     "Sympathetic 'anlayışlı, derdini paylaşan' demektir.")],
    "sympathy": [("sempati", "hoşlanma, ilgi duyma", "liking / affection",
                  "Sympathy anlayış ya da başsağlığıdır.")],
    "sensible": [("hassas", "duyarlı, kolay etkilenen", "sensitive",
                  "Sensible 'mantıklı, sağduyulu' demektir.")],
    "sensitive": [("sansasyonel", "çarpıcı, ses getiren", "sensational",
                   "Sensitive hassas/duyarlı demektir.")],
    "genial": [("dahi", "olağanüstü zeki", "brilliant / a genius",
                "Genial 'güler yüzlü, cana yakın' demektir.")],
    "terrific": [("korkunç", "dehşet verici", "terrible / terrifying",
                  "Terrific 'harika' demektir — olumlu bir kelimedir.")],
    "moral": [("moral", "ruh hâli, motivasyon", "morale",
               "Moral 'ahlaki' demektir. Ruh hâli = morale.")],
    "ambitious": [("ambisyon", "hırs (olumsuz)", "ruthless ambition",
                   "Ambitious İngilizcede çoğunlukla OLUMLUDUR.")],
    "pretend": [("prezante", "sunmak, tanıtmak", "present",
                 "Pretend '-mış gibi yapmak' demektir.")],

    # --- Gündelik nesneler ---
    "fabric": [("fabrika", "üretim tesisi", "factory / plant",
                "Fabric kumaş demektir.")],
    "magazine": [("magazin", "dedikodu haberleri", "gossip column / tabloid",
                  "Magazine her türlü dergidir.")],
    "camera": [("kamera", "video kamerası", "video camera / camcorder",
                "Camera öncelikle fotoğraf makinesidir.")],
    "collar": [("kolye", "boyna takılan takı", "necklace",
                "Collar yaka ya da tasma demektir.")],
    "kiosk": [("köşk", "büyük konak", "mansion / pavilion",
               "Kiosk büfe ya da satış kulübesidir.")],
    "cartoon": [("karton", "mukavva", "cardboard",
                 "Cartoon çizgi film ya da karikatürdür.")],
    "pasta": [("pasta", "yaş pasta", "cake",
               "Pasta makarna demektir.")],
    "smoking": [("smokin", "resmi ceket", "tuxedo / dinner jacket",
                 "Smoking sigara içmek demektir.")],
    "confection": [("konfeksiyon", "hazır giyim", "ready-to-wear clothing",
                    "Confection şekerleme demektir.")],
    "costume": [("kostüm", "takım elbise", "suit",
                 "Costume genelde tiyatro/karnaval kıyafetidir.")],
    "jersey": [("jarse", "kumaş türü", "jersey fabric",
                "Jersey ayrıca forma demektir.")],

    # --- Yer ve mekân ---
    "apartment": [("apartman", "bina", "apartment building / block of flats",
                   "Apartment tek bir dairedir.")],
    "salon": [("salon", "oturma odası", "living room",
               "Salon kuaför ya da güzellik salonudur.")],
    "market": [("market", "bakkal, süpermarket", "grocery store / supermarket",
                "Market pazar ya da piyasa demektir.")],
    "pension": [("pansiyon", "küçük konaklama yeri", "boarding house / guesthouse",
                 "Pension emekli maaşıdır.")],
    "barracks": [("baraka", "derme çatma kulübe", "shack / hut",
                  "Barracks kışla demektir.")],
    "local": [("lokal", "dernek lokali, mekân", "venue / club",
               "Local 'yerel' demektir.")],
    "cabinet": [("kabin", "küçük bölme", "cabin / booth",
                 "Cabinet dolap ya da bakanlar kuruludur.")],
    "terrace": [("teras", "çatı katı", "rooftop",
                 "Terrace sıra ev ya da taraça anlamına da gelir.")],

    # --- Sağlık ve beden ---
    "tension": [("tansiyon", "kan basıncı", "blood pressure",
                 "Tension gerilim demektir.")],
    "regime": [("rejim", "zayıflama diyeti", "diet",
                "Regime siyasi rejim ya da düzendir.")],
    "diet": [("diyet", "zayıflama rejimi", "weight-loss diet",
              "Diet genel olarak beslenme düzenidir.")],
    "operation": [("operasyon", "yalnızca ameliyat", "surgery",
                   "Operation işletme/çalıştırma anlamına da gelir.")],
    "preservative": [("prezervatif", "doğum kontrol ürünü", "condom",
                      "Preservative gıdadaki koruyucu katkı maddesidir.")],
    "injection": [("enjeksiyon", "yalnızca iğne", "shot / jab",
                   "Injection ayrıca 'para enjekte etmek' gibi kullanılır.")],
    "resistance": [("rezistans", "ısıtıcı tel", "heating element",
                    "Resistance direniş ya da direnç demektir.")],

    # --- Soyut ve akademik ---
    "actual": [("aktüel", "güncel, şimdiki", "current / topical",
                "Actual 'gerçek, asıl' demektir.")],
    "actually": [("aktüel olarak", "şu anda", "currently / at present",
                  "Actually 'aslında' demektir.")],
    "eventually": [("eventüel", "olası olarak", "possibly",
                    "Eventually 'sonunda, en nihayetinde' demektir.")],
    "eventual": [("eventüel", "olası", "possible / potential",
                  "Eventual 'nihai, sonunda gerçekleşen' demektir.")],
    "realize": [("realize etmek", "hayata geçirmek", "carry out / implement",
                 "Realize öncelikle 'fark etmek' demektir.")],
    "scheme": [("şema", "diyagram, çizim", "diagram / chart",
                "Scheme plan ya da düzen demektir.")],
    "scenario": [("senaryo", "film metni", "screenplay / script",
                  "Scenario 'olası durum, senaryo' demektir.")],
    "motive": [("motif", "desen, süsleme", "motif / pattern",
                "Motive güdü, sebep demektir.")],
    "formation": [("formasyon", "öğretmenlik sertifikası", "teaching certificate",
                   "Formation oluşum ya da düzen demektir.")],
    "promotion": [("promosyon", "indirim kampanyası", "special offer / discount",
                   "Promotion terfi ya da tanıtım demektir.")],
    "prospectus": [("prospektüs", "ilaç kullanma talimatı", "package insert / leaflet",
                    "Prospectus tanıtım kataloğudur.")],
    "parole": [("parola", "şifre", "password",
                "Parole şartlı tahliyedir.")],
    "argument": [("argüman", "yalnızca sav", "claim / point",
                  "Argument çoğu zaman 'tartışma, kavga' demektir.")],
    "record": [("rekor", "yalnızca spor rekoru", "record (sports)",
                "Record kayıt, sicil, plak anlamlarına da gelir.")],
    "service": [("servis", "okul/işyeri aracı", "shuttle bus",
                 "Service hizmet demektir.")],
    "session": [("seans", "terapi/spor seansı", "session (that sense is fine)",
                 "Session ayrıca 'oturum, dönem' demektir.")],
    "solution": [("solüsyon", "sıvı karışım", "liquid solution",
                  "Solution öncelikle 'çözüm' demektir.")],
    "mechanic": [("mekanik", "mekanik, makineyle ilgili", "mechanical",
                  "Mechanic tamircidir; sıfat hâli mechanical.")],
    "novel": [("novel", "kısa roman", "novella",
               "Novel roman demektir; sıfat olarak 'yeni, özgün'.")],
    "lecture": [("lektür", "okuma parçası", "reading / reading passage",
                 "Lecture ders ya da konferanstır.")],
    "patron": [("patron", "işveren", "boss / employer",
                "Patron müşteri ya da hami demektir.")],
    "figure": [("figür", "yalnızca şekil/dans figürü", "figure (dance move)",
                "Figure ayrıca rakam ve önemli kişi demektir.")],
    "concrete": [("konkre", "somut", "concrete (that sense is fine)",
                  "Concrete ayrıca beton demektir.")],
    "banquet": [("banket", "yol banketi", "hard shoulder",
                 "Banquet ziyafet demektir.")],
    "conductor": [("kondüktör", "bilet kontrolörü", "ticket inspector",
                   "Conductor orkestra şefi ya da iletken demektir.")],
    "garnish": [("garnitür", "yemeğin yanındakiler", "side dish / trimmings",
                 "Garnish tabağı süsleyen şeydir.")],
    "visit": [("vizite", "doktor muayenesi", "doctor's visit / consultation fee",
               "Visit genel olarak ziyarettir.")],
    "spot": [("spot", "spot ışık", "spotlight",
              "Spot nokta, leke ya da yer demektir.")],
    "serial": [("seri", "dizi, sıra", "series",
                "Serial 'seri hâlinde, dizi şeklinde' demektir.")],
}

# Temizlik: boş/eksik satırlar kazara eklenirse yüklemeyi bozmasın.
YANLIS_DOSTLAR = {
    kelime: [k for k in kayitlar if k[0] and k[2]]
    for kelime, kayitlar in YANLIS_DOSTLAR.items()
}
YANLIS_DOSTLAR = {k: v for k, v in YANLIS_DOSTLAR.items() if v}


def bul(metin):
    """Kelimenin küratörlü yanlış dostları; yoksa boş liste."""
    return YANLIS_DOSTLAR.get((metin or "").strip().lower(), [])


def ekle(kelime):
    """
    Modelin ürettiklerinin üstüne küratörlü kayıtları ekler.

    Aynı Türkçe benzeri iki kez girmesin diye eşleştirme yapılır; çakışmada
    küratörlü kayıt kazanır, çünkü modelinki doğrulanmamıştır.
    Döner: eklenen kayıt sayısı.
    """
    from words.enrich.schema import FalseFriend

    kayitlar = bul(kelime.text)
    if not kayitlar:
        return 0

    mevcut = {(d.turkish_lookalike or "").strip().lower() for d in kelime.false_friends}
    eklenen = 0
    for benzeyen, sanilan, dogru, not_ in kayitlar:
        if benzeyen.strip().lower() in mevcut:
            continue
        kelime.false_friends.append(FalseFriend(
            turkish_lookalike=benzeyen, assumed_meaning=sanilan,
            correct_english=dogru, note=not_,
        ))
        eklenen += 1
    return eklenen
