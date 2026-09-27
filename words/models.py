"""
Kelime çekirdeği.

Eski model her şeyi tek bir `Word` satırına tıkıştırıyordu: anlam, açıklama,
10 örnek cümle kolonu, virgülle ayrılmış eş/zıt anlamlılar, collocation'lar.
Bu yüzden `relate` ile `relation` birbirini tanımayan iki yabancıydı.

Yapı beş katmanlı:

    WordFamily   courage
      └ Word     courage (isim) · courageous (sıfat) · encourage (fiil) …
          ├ Meaning         anlam + açıklama + ton + üslup + alan
          │   ├ ExampleSentence  anlam başına 5 örnek cümle
          │   ├ Collocation      make a decision, heavily dependent
          │   └ UsagePattern     depend on sth, suggest doing sth
          ├ WordForm        çekimler: encouraged, encouraging, slower, went …
          └ FalseFriend     sympathetic ≠ sempatik

Üç ayrım bu dosyanın taşıdığı asıl bilgi:

  - TÜRETME (derivation) ayrı bir kelimedir: courage -> encouragement.
    Kendi türü, kendi anlamı, kendi cümleleri vardır -> ayrı `Word`.
  - ÇEKİM (inflection) yeni bir kelime değildir: encourage -> encouraged.
    Anlamı aynıdır, sözlük maddesi olmaz -> `WordForm`.
  - KELİME ≠ ANLAM. Öğrenmenin birimi anlamdır. `bank` tek bir isimdir ama
    "banka" ile "nehir kıyısı" aynı şeyi öğretmez: `open a bank account`
    sadece birine aittir, tonu, üslubu, alanı da öyle. Bu yüzden collocation,
    ton, üslup, alan ve örnek cümleler `Word`'e değil `Meaning`'e bağlıdır.

Kullanıcının kendi yazdıkları çekirdeğe hiç dokunmaz; `UserWordNote`,
`UserExampleSentence` ve `UserMeaning` üstüne biner.
"""

from django.db import models

from users.models import User


# ----------------------------------------------------------------------
# Sabitler
# ----------------------------------------------------------------------

class PartOfSpeech(models.TextChoices):
    NOUN = "noun", "isim"
    VERB = "verb", "fiil"
    ADJECTIVE = "adjective", "sıfat"
    ADVERB = "adverb", "zarf"
    PHRASAL_VERB = "phrasal_verb", "phrasal verb"
    PREPOSITION = "preposition", "edat"
    CONJUNCTION = "conjunction", "bağlaç"


class FormKind(models.TextChoices):
    """
    Çekim türü. Sadece "bu yazım şu kelimeye götürür" demekle yetinmiyoruz:
    `slower` bir sözlük maddesi değil ama sınavda sorulabilir bir şey
    (sıfatın derecelendirilmesi). Etiketi olmazsa quiz üretemeyiz.
    """
    PLURAL = "plural", "çoğul"
    THIRD_PERSON = "third_person", "3. tekil (-s)"
    PAST = "past", "2. hâl"
    PAST_PARTICIPLE = "past_participle", "3. hâl"
    PRESENT_PARTICIPLE = "present_participle", "-ing hâli"
    COMPARATIVE = "comparative", "karşılaştırma (-er)"
    SUPERLATIVE = "superlative", "en üstünlük (-est)"
    OTHER = "other", "diğer"


class RelationType(models.TextChoices):
    SYNONYM = "synonym", "eş anlamlı"
    ANTONYM = "antonym", "zıt anlamlı"
    # "Bilmediğini bildiğine benzetme": possess ≈ have (ama daha resmî).
    # Zor kelimeyi Türkçe karşılığıyla değil, öğrencinin zaten bildiği
    # İngilizce kelimeyle tanımlamak.
    SIMPLER = "simpler", "daha basit karşılığı"
    # affect/effect, sensible/sensitive, economic/economical.
    # Eş anlamlı DEĞİL — tam tersine, benzedikleri için karıştırılıyorlar.
    CONFUSED_WITH = "confused_with", "karıştırılan"


class Sentiment(models.TextChoices):
    """
    Anlamın tonu.

    Bu alan var çünkü TÜRKÇE KARŞILIK BU BİLGİYİ SİLİYOR. `notorious` ve
    `famous` sözlükte ikisi de "ünlü"; `skinny`, `slim`, `thin` üçü de
    "zayıf". Öğrenci Türkçesinden bunu asla öğrenemez.
    """
    NEUTRAL = "neutral", "nötr"
    POSITIVE = "positive", "olumlu"
    NEGATIVE = "negative", "olumsuz"


class Register(models.TextChoices):
    """
    Üslup / resmiyet düzeyi.

    `possess` ile `have` aynı anlama gelir ama aynı cümleye girmez. Essay
    yazan öğrencinin ihtiyacı olan bilgi tam olarak budur.
    """
    NEUTRAL = "neutral", "nötr"
    FORMAL = "formal", "resmî"
    ACADEMIC = "academic", "akademik"
    INFORMAL = "informal", "gündelik"
    SLANG = "slang", "argo"
    LITERARY = "literary", "edebî"


class CollocationKind(models.TextChoices):
    """
    Birlikte kullanım kalıbının dilbilgisel şekli.

    Tek bir metin alanı yetmiyor: `make a decision` (fiil+isim) ile
    `heavily dependent` (zarf+sıfat) farklı soru tipleri üretir.
    """
    VERB_NOUN = "verb_noun", "fiil + isim"
    ADJ_NOUN = "adj_noun", "sıfat + isim"
    NOUN_NOUN = "noun_noun", "isim + isim"
    ADV_ADJ = "adv_adj", "zarf + sıfat"
    ADV_VERB = "adv_verb", "zarf + fiil"
    OTHER = "other", "diğer"


class PatternKind(models.TextChoices):
    """
    Kullanım kalıbı türü. Collocation'dan farkı: bu kelime seçimi değil,
    GRAMER. `depend on`, `suggest doing` ama `decide to do`. Hazırlık
    öğrencisinin en çok puan kaybettiği yer burası.
    """
    PREPOSITION = "preposition", "bağımlı edat"
    VERB_FORM = "verb_form", "fiil kalıbı"
    CLAUSE = "clause", "yan cümle kalıbı"
    STRUCTURE = "structure", "yapı"
    OTHER = "other", "diğer"


class ExpressionKind(models.TextChoices):
    IDIOM = "idiom", "deyim"
    FIXED = "fixed", "kalıp ifade"
    PROVERB = "proverb", "atasözü"
    LINKER = "linker", "bağlayıcı ifade"
    OTHER = "other", "diğer"


VISIBILITY_CHOICES = [
    ("public", "Herkese Açık"),
    ("private", "Gizli"),
]

# Seviye artık ODTÜ kuru (101–501) değil, CEFR. Kur bilgisi kelimenin bir
# özelliği değil, kelimeye takılan bir liste etiketi — oraya taşınacak.
CEFR_CHOICES = [
    ("Belirtilmemiş", "Belirtilmemiş"),
    ("A1", "A1 — Başlangıç"),
    ("A2", "A2 — Temel"),
    ("B1", "B1 — Orta öncesi"),
    ("B2", "B2 — Orta"),
    ("C1", "C1 — Orta üstü"),
    ("C2", "C2 — İleri"),
]

CEFR_LEVELS = [kod for kod, _ in CEFR_CHOICES if kod != "Belirtilmemiş"]


# ----------------------------------------------------------------------
# Alan (konu) etiketi
# ----------------------------------------------------------------------

class Category(models.Model):
    """
    Anlamın ait olduğu konu alanı: psikoloji, ekonomi, hukuk, tıp, gündelik…

    Okuma metinleriyle doğrudan çalışır: sisteme psikoloji metni girdiğinde
    içindeki kelimelerin hangi alana ait olduğu buradan bilinir.
    """

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


# ----------------------------------------------------------------------
# Çekirdek
# ----------------------------------------------------------------------

class WordFamily(models.Model):
    """
    Türetme ailesi. Öğrenmenin birimi tek kelime değil, aile.

    Aile zamanla büyür: bugün bir metin `relate`'i getirir, aile kurulur;
    üç ay sonra başka bir metin `relation`'ı getirir ve yanına eklenir.
    Eşi olmayan kelime de bir aileye girer — tek kişilik aile.
    """

    root = models.CharField(max_length=100, unique=True)
    note = models.CharField(max_length=500, blank=True, null=True)

    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("root",)
        verbose_name_plural = "word families"

    def __str__(self):
        return self.root

    @property
    def members(self):
        """Ailedeki kelimeler, kök önce gelecek şekilde."""
        return sorted(self.words.all(), key=lambda w: (w.text != self.root, w.text))


class Word(models.Model):
    """
    Bir sözlük maddesi: belirli bir türdeki belirli bir kelime.

    `progress (isim)` ve `progress (fiil)` AYRI kayıtlardır; anlamları,
    örnek cümleleri ve kullanım kalıpları farklı olduğu için.

    Bu satırda duran şeyler kelimenin BÜTÜNÜNE ait olanlar: yazımı, türü,
    fiil hâlleri, zorluğu, yaygınlığı. Anlama göre değişen her şey (ton,
    üslup, alan, collocation, örnek cümle) `Meaning` üzerinde durur.
    """

    family = models.ForeignKey(
        WordFamily, on_delete=models.CASCADE, related_name="words",
    )

    text = models.CharField(max_length=120)
    pos = models.CharField(
        max_length=20, choices=PartOfSpeech.choices, default=PartOfSpeech.NOUN,
        verbose_name="tür",
    )

    # Fiil hâlleri. Düzensizler kuralla üretilemediği için burada duruyor;
    # WordForm satırları da bunlardan besleniyor.
    v2Form = models.CharField(max_length=80, blank=True, null=True)
    v3Form = models.CharField(max_length=80, blank=True, null=True)

    # Phrasal verb ise bağlı olduğu ana fiil: "run into" -> "run"
    base_verb = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True,
        related_name="phrasal_verbs",
    )

    cefr = models.CharField(max_length=15, choices=CEFR_CHOICES,
                            default="Belirtilmemiş", verbose_name="seviye")

    # Yaygınlık sırası: 1 = en sık geçen. Boş = ölçülmemiş.
    # İçerik hattının hangi kelimeyi önce üreteceğine bu karar veriyor;
    # okuma metinlerinde ölçülen dağılım burada yaşıyor.
    frequency_rank = models.PositiveIntegerField(blank=True, null=True,
                                                 verbose_name="yaygınlık sırası")

    isBaseWord = models.BooleanField(default=False)

    owner = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.CASCADE, related_name="words",
    )
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES,
                                  default="private")

    saved_by = models.ManyToManyField(
        User, related_name="saved_words", blank=True, through="UserWordLink",
    )

    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("text", "pos")
        # Aynı yazım + aynı tür iki kez olamaz; ama progress(n)/progress(v) olur.
        unique_together = ("text", "pos")
        indexes = [
            models.Index(fields=["text"]),
            models.Index(fields=["family", "text"]),
        ]

    def __str__(self):
        return f"{self.text} ({self.get_pos_display()})"

    # --- kısayollar -----------------------------------------------------

    @property
    def primary_meaning(self):
        """İlk (ana) anlam. Kelimenin en az bir anlamı olması beklenir."""
        return self.meanings.first()

    @property
    def meaningTr(self):
        """Ana anlamın Türkçesi. Şablonlar için kısayol."""
        anlam = self.primary_meaning
        return anlam.meaning_tr if anlam else ""

    @property
    def explanation(self):
        """Ana anlamın İngilizce açıklaması."""
        anlam = self.primary_meaning
        return anlam.definition if anlam else ""

    @property
    def has_multiple_meanings(self):
        return self.meanings.count() > 1

    @property
    def example_sentences(self):
        """
        Kelimenin bütün cümleleri, anlam sırasına göre düzleştirilmiş.

        Cümleler artık anlama bağlı; tek anlamlı kelimelerde fark yok, ama
        `bank` için hangi cümlenin hangi anlama ait olduğu artık belli.
        """
        return [c.text for c in ExampleSentence.objects
                .filter(meaning__word=self)
                .order_by("meaning__sort_order", "sort_order", "id")]

    @property
    def collocations(self):
        return (Collocation.objects.filter(meaning__word=self)
                .order_by("meaning__sort_order", "sort_order", "id"))

    @property
    def patterns(self):
        return (UsagePattern.objects.filter(meaning__word=self)
                .order_by("meaning__sort_order", "sort_order", "id"))

    @property
    def categories(self):
        """Kelimenin bütün anlamlarında geçen alanlar, tekrarsız."""
        return Category.objects.filter(meanings__word=self).distinct()

    @property
    def is_verb(self):
        return self.pos in (PartOfSpeech.VERB, PartOfSpeech.PHRASAL_VERB)

    @property
    def verb_forms(self):
        """Fiilse "went · gone" gibi gösterilecek metin."""
        return [f for f in (self.v2Form, self.v3Form) if f]

    def relations(self, kind):
        """
        Bu kelimeden çıkan belirli türdeki bağlar, HEDEF BAŞINA BİR satır.

        Bağlar anlama bağlı (D1): bank -> shore yalnızca "nehir kıyısı"
        anlamında. Aynı hedef birden çok anlamda geçiyorsa (aim -> goal hem
        "amaç" hem "hedef" anlamında) veritabanında birden çok satır var;
        kelime düzeyindeki görünümler (eski detay sayfası, düzenleme formu)
        hedefi iki kez göstermesin diye her hedefin ilk satırı dönüyor.
        Anlam başına bağlar: Meaning.iliskiler / Meaning.iliski_satirlari.
        """
        ilkler = (self.relations_from.filter(type=kind)
                  .values("to_word").annotate(ilk=models.Min("id")).values("ilk"))
        return (WordRelation.objects.filter(pk__in=ilkler)
                .select_related("to_word").order_by("id"))

    @property
    def synonyms(self):
        return self.relations(RelationType.SYNONYM)

    @property
    def antonyms(self):
        return self.relations(RelationType.ANTONYM)

    @property
    def simpler_words(self):
        """possess -> have gibi "daha basit karşılığı" bağları."""
        return self.relations(RelationType.SIMPLER)

    @property
    def confusables(self):
        """affect -> effect gibi "karıştırılan" bağları."""
        return self.relations(RelationType.CONFUSED_WITH)

    def is_editable_by(self, user):
        """
        Bu kullanıcı kelimenin ÇEKİRDEĞİNİ değiştirebilir mi?

        Kural pozitif: yalnızca kelimeyi kendi ekleyen kişi. Eskiden kural
        olumsuzdu ("sahibi varsa ve o değilse engelle") ve sahibi boş olan
        kelimeler herkese açık kalıyordu — listesine ekleyen herkes ortak
        sözlüğü değiştirebiliyordu.

        Yönetici de buradan değiştiremez: ortak sözlüğün bakımı Django
        admin üzerinden yapılır, kullanıcı formundan değil.
        """
        if not user or not user.is_authenticated:
            return False
        return not self.isBaseWord and self.owner_id == user.id

    def saved_by_others_count(self, user=None):
        """Bu kelimeyi kaç BAŞKA kullanıcı listesine almış?"""
        baglar = self.userLinks.all()
        if self.owner_id:
            baglar = baglar.exclude(user_id=self.owner_id)
        if user is not None and user.is_authenticated:
            baglar = baglar.exclude(user_id=user.id)
        return baglar.count()

    def note_of(self, user):
        """Kullanıcının bu kelimeye yazdığı kişisel not (yoksa None)."""
        if not user or not user.is_authenticated:
            return None
        return self.user_notes.filter(user=user).first()

    def meanings_of(self, user):
        """Kullanıcının bu kelimeye kendi eklediği anlamlar."""
        if not user or not user.is_authenticated:
            return UserMeaning.objects.none()
        return self.user_meanings.filter(user=user)


class Meaning(models.Model):
    """
    Kelime ≠ anlam. Öğrenmenin gerçek birimi bu satır.

    `bank` tek bir isim ama iki anlamı var: banka ve nehir kıyısı. Eski
    modelde bu, AI'ın ürettiği "1. … / 2. …" biçiminde tek bir metin
    alanına sıkıştırılıyordu; artık gerçek satırlar — ve her biri kendi
    tonunu, üslubunu, alanını, collocation'larını ve cümlelerini taşıyor.
    """

    EXAMPLE_SENTENCE_COUNT = 5

    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="meanings")

    meaning_tr = models.CharField(max_length=300, verbose_name="anlamı")
    definition = models.CharField(max_length=600, blank=True, null=True,
                                  verbose_name="açıklaması")

    sentiment = models.CharField(max_length=12, choices=Sentiment.choices,
                                 default=Sentiment.NEUTRAL, verbose_name="ton")
    register = models.CharField(max_length=12, choices=Register.choices,
                                default=Register.NEUTRAL, verbose_name="üslup")
    # Anlamın kendi seviyesi. Aynı kelimenin anlamları farklı seviyede
    # olabilir (meet: "tanışmak" A1, "karşılamak (ihtiyacı)" B2). Word.cefr
    # kelimenin EN KOLAY anlamının seviyesi olarak tutuluyor; seçim ve
    # çeldirici sorguları onu kullanıyor.
    cefr = models.CharField(max_length=15, choices=CEFR_CHOICES,
                            default="Belirtilmemiş", verbose_name="seviye")
    categories = models.ManyToManyField(Category, related_name="meanings", blank=True,
                                        verbose_name="alanlar")

    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "id")

    def __str__(self):
        return f"{self.word.text}: {self.meaning_tr}"

    @property
    def is_marked(self):
        """Nötr olmayan bir tonu ya da üslubu var mı? (rozet gösterilsin mi)"""
        return (self.sentiment != Sentiment.NEUTRAL
                or self.register != Register.NEUTRAL)

    # --- Anlama özel bağlar (D1) ---------------------------------------
    # Kelime kartı her anlamın altında "Benzer / Daha basit / Zıt" çip
    # satırlarını gösterecek (rapor 4.3). Karıştırılan (confused_with)
    # burada yok: o kelime düzeyinde kalıyor, bkz. WordRelation.

    # Kartta satırların sırası ve etiketleri.
    ILISKI_SATIRLARI = (
        (RelationType.SYNONYM, "Benzer"),
        (RelationType.SIMPLER, "Daha basit"),
        (RelationType.ANTONYM, "Zıt"),
    )

    def iliskiler(self, tur):
        """Bu anlama bağlı, belirli türdeki bağlar (eklenme sırasıyla)."""
        return self.relations.filter(type=tur).select_related("to_word").order_by("id")

    @property
    def synonyms(self):
        return self.iliskiler(RelationType.SYNONYM)

    @property
    def antonyms(self):
        return self.iliskiler(RelationType.ANTONYM)

    @property
    def simpler_words(self):
        return self.iliskiler(RelationType.SIMPLER)

    def iliski_satirlari(self, en_cok=4):
        """
        Kart için çip satırları: [("Benzer", [Word, …]), ("Daha basit", […]), …]

        Boş satır dönmez; her satırda en çok `en_cok` kelime. `self.relations`
        üzerinden Python'da grupluyor: çağıran
        `prefetch_related("relations__to_word")` yaparsa kart başına ek sorgu
        olmaz.
        """
        gruplar = {tur: [] for tur, _ in self.ILISKI_SATIRLARI}
        for bag in sorted(self.relations.all(), key=lambda b: b.pk):
            liste = gruplar.get(bag.type)
            if liste is not None and len(liste) < en_cok and bag.to_word not in liste:
                liste.append(bag.to_word)
        return [(etiket, gruplar[tur]) for tur, etiket in self.ILISKI_SATIRLARI if gruplar[tur]]


class ExampleSentence(models.Model):
    """
    Çekirdek örnek cümle. Anlam başına 5 tane.

    Kullanıcının kendi yazdıkları buraya değil, UserExampleSentence'a gider.
    """

    meaning = models.ForeignKey(Meaning, on_delete=models.CASCADE,
                                related_name="examples")
    text = models.CharField(max_length=400)
    # Nereden geldiği: "core", "AI", "Okuma 12" gibi.
    source = models.CharField(max_length=120, blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "id")

    def __str__(self):
        return self.text[:60]


class Collocation(models.Model):
    """
    Birlikte kullanılan yapı: `make a decision`, `heavily dependent`.

    Kelimeyi bilmekle kullanabilmek arasındaki farkın çoğu burada. Türkçe
    "karar vermek" dediği için öğrenci `do a decision` yazıyor; bunu ancak
    doğrusunu veri olarak görerek öğreniyor.
    """

    meaning = models.ForeignKey(Meaning, on_delete=models.CASCADE,
                                related_name="collocations")
    pattern = models.CharField(max_length=200, verbose_name="yapı")
    kind = models.CharField(max_length=16, choices=CollocationKind.choices,
                            default=CollocationKind.OTHER, verbose_name="türü")
    meaning_tr = models.CharField(max_length=200, blank=True, null=True,
                                  verbose_name="Türkçesi")
    example = models.CharField(max_length=400, blank=True, null=True,
                               verbose_name="örnek cümle")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "id")
        unique_together = ("meaning", "pattern")

    def __str__(self):
        return self.pattern


class UsagePattern(models.Model):
    """
    Kullanım kalıbı: `depend on sth`, `suggest doing sth`, `decide to do sth`.

    Collocation kelime seçimidir, bu gramerdir. Ayrı durmalarının sebebi
    quizlerinin de ayrı olması: collocation'da eksik kelime sorulur,
    kalıpta eksik edat ya da fiil biçimi.
    """

    meaning = models.ForeignKey(Meaning, on_delete=models.CASCADE,
                                related_name="patterns")
    pattern = models.CharField(max_length=200, verbose_name="kalıp")
    kind = models.CharField(max_length=16, choices=PatternKind.choices,
                            default=PatternKind.OTHER, verbose_name="türü")
    example = models.CharField(max_length=400, blank=True, null=True,
                               verbose_name="örnek cümle")
    note = models.CharField(max_length=300, blank=True, null=True,
                            verbose_name="not")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "id")
        unique_together = ("meaning", "pattern")

    def __str__(self):
        return self.pattern


class WordForm(models.Model):
    """
    Çekim biçimi: metinde karşılaşılan yazımdan sözlük maddesine köprü.

    Metinde "encouraged", "families", "ran", "slower" geçer; sözlükte
    "encourage", "family", "run", "slow" vardır. Bu tablo olmadan okuma
    sayfasında kelimeye dokunmak çalışmaz.

    Aynı yazım birden fazla kelimeye bağlanabilir — "decided" hem
    decide'ın 2. hâli hem de bağımsız bir sıfattır.
    """

    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="forms")
    surface = models.CharField(max_length=120, db_index=True)
    kind = models.CharField(max_length=24, choices=FormKind.choices,
                            default=FormKind.OTHER)

    class Meta:
        unique_together = ("word", "surface")
        ordering = ("surface",)

    def __str__(self):
        return f"{self.surface} → {self.word.text}"


class WordRelation(models.Model):
    """
    Kelimeler arası anlam bağı: eş anlamlı, zıt anlamlı, daha basit
    karşılığı, karıştırılan.

    `note` nüansı taşır: "possess ≈ have, ama daha resmî". Zor kelimeyi
    öğrencinin bildiği kelimeyle tanımlamak, Türkçe karşılığını ezberletmekten
    daha iyi sonuç veriyor.
    """

    from_word = models.ForeignKey(Word, on_delete=models.CASCADE,
                                  related_name="relations_from")
    to_word = models.ForeignKey(Word, on_delete=models.CASCADE,
                                related_name="relations_to")
    type = models.CharField(max_length=16, choices=RelationType.choices)
    note = models.CharField(max_length=200, blank=True, null=True)
    # Bağın ait olduğu anlam (D1). Eş, zıt ve basit anlamlılar anlama
    # özeldir: bank -> shore yalnızca "nehir kıyısı" anlamında. Aynı hedef
    # birden çok anlamda geçiyorsa her (anlam, hedef, tür) ayrı satır.
    # Boş kalanlar:
    #   - confused_with: karışıklık biçimden (yazılış/ses: affect/effect)
    #     gelir, bir anlamdan değil; küratörlü tablodan (seed_confusables)
    #     kelime çifti olarak yazılır ve kartta kelime düzeyinde uyarı olur.
    #   - kaynağı anlam başına olmayan eski/elle bağlar (kullanıcı formu,
    #     seed_words, silinmiş ya da elle eklenmiş anlamlar).
    meaning = models.ForeignKey(Meaning, on_delete=models.CASCADE, null=True, blank=True,
                                related_name="relations", verbose_name="anlam")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("from_word", "to_word", "type", "meaning"),
                                    name="iliski_anlam_tekil"),
            # NULL != NULL: anlamsız (kelime düzeyi) bağın tekrarını ilk
            # kural yakalamaz. MySQL koşullu kısıtı desteklemiyor (yalnızca
            # uyarı verir, W036); orada bu tekillik kodda (get_or_create)
            # korunuyor.
            models.UniqueConstraint(fields=("from_word", "to_word", "type"),
                                    condition=models.Q(meaning__isnull=True),
                                    name="iliski_kelime_tekil"),
        ]

    def __str__(self):
        return f"{self.from_word.text} –{self.get_type_display()}→ {self.to_word.text}"


class FalseFriend(models.Model):
    """
    Yanlış dost: Türkçeye benzediği için yanlış anlaşılan kelime.

    `sympathetic` "sempatik" değil, "anlayışlı"dır. `actual` "aktüel"
    değil, "gerçek"tir. `sensible` "hassas" değil, "mantıklı"dır.
    Bu hatalar Türkçe konuşanda sistematik ve tahmin edilebilir — yani
    veri olarak tutulabilir. Hiçbir genel sözlükte bu bilgi yok.
    """

    word = models.ForeignKey(Word, on_delete=models.CASCADE,
                             related_name="false_friends")
    turkish_lookalike = models.CharField(max_length=100,
                                         verbose_name="benzediği Türkçe kelime")
    assumed_meaning = models.CharField(max_length=200, blank=True, null=True,
                                       verbose_name="sanılan anlam")
    correct_english = models.CharField(max_length=200, blank=True, null=True,
                                       verbose_name="o anlam için doğru kelime")
    note = models.CharField(max_length=400, blank=True, null=True)

    class Meta:
        unique_together = ("word", "turkish_lookalike")
        ordering = ("turkish_lookalike",)

    def __str__(self):
        return f"{self.word.text} ≠ {self.turkish_lookalike}"


class ExpressionStructure(models.TextChoices):
    """
    İfadenin cümledeki dilbilgisel görevi. Noktalama kuralı buna bağlı:
    "but" (bağlaç) ile "however" (bağlayıcı zarf) aynı anlama gelir ama
    virgülü farklı kullanılır; "although" (yan cümle) ile "despite" (edat)
    da öyle — birinden sonra cümle, ötekinden sonra isim gelir.
    """
    COORDINATING = "baglac", "bağlaç (iki cümleyi bağlar)"
    SUBORDINATING = "yan_cumle", "yan cümle bağlacı"
    LINKING_ADVERB = "cumle_zarfi", "bağlayıcı zarf"
    PREPOSITION = "edat", "edat (+ isim / -ing)"
    CORRELATIVE = "cift", "çift bağlaç"
    PHRASE = "ifade", "kalıp ifade"


class ExpressionGroup(models.Model):
    """
    İfadenin İŞLEVİ ("yönü"): karşıtlık, ekleme, örnek verme, sonuç…
    Aynı gruptaki ifadeler birbirinin benzeridir: "but" sayfasında
    however, nevertheless, nonetheless görünür; öğrenci birinden ötekine
    atlayarak öğrenir. Tüm Kelimeler'de ifadeler bu başlıklarla sıralanır.
    """

    slug = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=60, verbose_name="işlev")          # "Karşıtlık"
    heading = models.CharField(max_length=120, verbose_name="başlık")     # "Anlamı tersine çevirenler"
    description = models.CharField(max_length=400, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "name")

    def __str__(self):
        return self.name


class Expression(models.Model):
    """
    Kelime olmayan ama öğrenilen birim: deyim, kalıp ifade, bağlayıcı.

    "in the long run", "on the other hand", "by and large". Anlamı
    parçalarından çıkmaz, yani `Word` + `WordForm` bunu çözemez; kendi
    satırı olmak zorunda. Bir ya da birkaç kelimeye bağlanabilir —
    "in the long run" hem `long` hem `run` sayfasında görünmeli.
    """

    text = models.CharField(max_length=200, unique=True)
    meaning_tr = models.CharField(max_length=300, verbose_name="anlamı")
    definition = models.CharField(max_length=600, blank=True, null=True,
                                  verbose_name="açıklaması")

    kind = models.CharField(max_length=12, choices=ExpressionKind.choices,
                            default=ExpressionKind.FIXED, verbose_name="türü")
    cefr = models.CharField(max_length=15, choices=CEFR_CHOICES,
                            default="Belirtilmemiş", verbose_name="seviye")
    sentiment = models.CharField(max_length=12, choices=Sentiment.choices,
                                 default=Sentiment.NEUTRAL, verbose_name="ton")
    register = models.CharField(max_length=12, choices=Register.choices,
                                default=Register.NEUTRAL, verbose_name="üslup")

    # 25 Eylül: bağlayıcı ifadeler (but, however, for example…) için
    group = models.ForeignKey(ExpressionGroup, on_delete=models.SET_NULL, null=True,
                              blank=True, related_name="expressions", verbose_name="işlev")
    # İki işlevi olan ifadeler: "while" hem Zaman (-iken) hem Karşıtlık (oysa)
    extra_groups = models.ManyToManyField(ExpressionGroup, blank=True,
                                          related_name="extra_expressions",
                                          verbose_name="ek işlevler")
    structure = models.CharField(max_length=12, choices=ExpressionStructure.choices,
                                 default=ExpressionStructure.PHRASE, verbose_name="yapı")
    pattern = models.CharField(max_length=120, blank=True, verbose_name="kalıp")  # "although + cümle"
    punctuation_note = models.TextField(blank=True, verbose_name="noktalama")
    academic_note = models.CharField(max_length=300, blank=True, verbose_name="akademik kullanım")
    sort_order = models.PositiveIntegerField(default=0)

    categories = models.ManyToManyField(Category, related_name="expressions", blank=True)
    words = models.ManyToManyField(Word, related_name="expressions", blank=True)

    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE,
                              related_name="expressions")
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES,
                                  default="private")
    saved_by = models.ManyToManyField(User, related_name="saved_expressions", blank=True)

    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("text",)

    def __str__(self):
        return self.text

    @property
    def similar(self):
        """Aynı işi yapan ifadeler (aynı işlev grubu), kendisi hariç."""
        gruplar = [self.group_id] + list(self.extra_groups.values_list("id", flat=True))
        gruplar = [g for g in gruplar if g]
        if not gruplar:
            return Expression.objects.none()
        return (Expression.objects
                .filter(models.Q(group_id__in=gruplar) | models.Q(extra_groups__in=gruplar),
                        visibility="public")
                .exclude(id=self.id).distinct().order_by("sort_order", "text"))


class ExampleKind(models.TextChoices):
    EXAMPLE = "ornek", "örnek cümle"
    CORRECT = "dogru", "doğru noktalama"
    WRONG = "yanlis", "yanlış noktalama"


class ExpressionExample(models.Model):
    expression = models.ForeignKey(Expression, on_delete=models.CASCADE,
                                   related_name="examples")
    text = models.CharField(max_length=400)
    kind = models.CharField(max_length=8, choices=ExampleKind.choices,
                            default=ExampleKind.EXAMPLE)
    note = models.CharField(max_length=300, blank=True)   # yanlış ise neden yanlış
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "id")

    def __str__(self):
        return self.text[:60]


# ----------------------------------------------------------------------
# Kullanıcı katmanı — çekirdeğe dokunmaz, üstüne biner
# ----------------------------------------------------------------------

class UserMeaning(models.Model):
    """
    Kullanıcının bir kelimeye kendi eklediği anlam. Yalnızca kendisi görür.

    Çekirdek sözlük hiçbir zaman tamamlanmaz: öğrenci metinde kelimeyi
    listedeki anlamlarına uymayan bir yerde görür. Eskiden yapabileceği tek
    şey nota yazmaktı. Artık anlamı anlam olarak ekliyor — ve kendi anlamı
    çekirdeğe dokunmuyor, başkasının sayfasında görünmüyor.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="word_meanings")
    word = models.ForeignKey(Word, on_delete=models.CASCADE,
                             related_name="user_meanings")

    meaning_tr = models.CharField(max_length=300, verbose_name="anlamı")
    definition = models.CharField(max_length=600, blank=True, null=True,
                                  verbose_name="açıklaması")

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("createdAt", "id")

    def __str__(self):
        return f"{self.user.username} · {self.word.text}: {self.meaning_tr}"


class UserWordNote(models.Model):
    """
    Kullanıcının bir kelimeye yazdığı kişisel not.

    Eski modelde `note` paylaşılan Word satırının üzerinde bir alandı; yani
    "Kişisel Not" aslında kişisel değildi. Artık gerçekten kişisel.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="word_notes")
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="user_notes")
    note = models.TextField(max_length=800)

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "word")

    def __str__(self):
        return f"{self.user.username} · {self.word.text}"


class UserExampleSentence(models.Model):
    """Kullanıcının kendi yazdığı örnek cümle. Yalnızca kendisi görür."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="word_examples")
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="user_examples")
    sentence = models.CharField(max_length=400)

    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("createdAt",)

    def __str__(self):
        return f"{self.user.username} · {self.sentence[:40]}"


class UserExpressionLink(models.Model):
    """
    Kullanıcının ifade listesi (kelime listesinden ayrı): ifade bir Word
    değil, UserWordLink'e giremez. Çalışma istatistikleri kelimedekiyle aynı
    biçimde; çalışma ekranları sonra buna göre düzenlenecek.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expressionLinks")
    expression = models.ForeignKey(Expression, on_delete=models.CASCADE,
                                   related_name="userLinks")
    dateAdded = models.DateTimeField(auto_now_add=True)
    correctCount = models.IntegerField(default=0)
    wrongCount = models.IntegerField(default=0)

    class Meta:
        unique_together = ("user", "expression")

    def __str__(self):
        return f"{self.user.username} <-> {self.expression.text}"


class UserWordLink(models.Model):
    """Kullanıcının listesindeki kelime + çalışma istatistikleri."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wordLinks")
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="userLinks")

    dateAdded = models.DateTimeField(auto_now_add=True)

    correctCount = models.IntegerField(default=0)
    wrongCount = models.IntegerField(default=0)

    class Meta:
        unique_together = ("user", "word")

    def __str__(self):
        return f"{self.user.username} <-> {self.word.text} (D:{self.correctCount} / Y:{self.wrongCount})"

    @property
    def totalAttempts(self):
        return self.correctCount + self.wrongCount

    @property
    def wrongRatio(self):
        toplam = self.totalAttempts
        if toplam == 0:
            return 0
        return (self.wrongCount / toplam) * 100


class WordList(models.Model):
    """Kullanıcının kendi kelime klasörü."""

    COLOR_CHOICES = [
        ("indigo", "Indigo"), ("blue", "Mavi"), ("emerald", "Yeşil"),
        ("amber", "Sarı"), ("rose", "Kırmızı"), ("purple", "Mor"),
        ("teal", "Turkuaz"), ("slate", "Gri"),
    ]

    owner = models.ForeignKey(User, related_name="word_lists", on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default="indigo")

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    words = models.ManyToManyField(Word, related_name="in_user_lists", blank=True)

    class Meta:
        ordering = ("name",)
        unique_together = ("owner", "name")

    def __str__(self):
        return f"{self.owner.username} · {self.name}"
