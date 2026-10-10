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
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

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

    # Sıklık (rapor 18.16): wordfreq Zipf puanı (≈ 1 çok seyrek … 7 çok sık).
    # Ekranda HİÇ görünmez; yalnızca arka planda: L&P'de yeni kelimenin çıkma
    # olasılığı, şüpheli CEFR etiketi bulma, Google'dan gizleme.
    # Hesaplama: manage.py siklik_hesapla
    siklik = models.FloatField(blank=True, null=True, verbose_name="sıklık (Zipf)")

    # CEFR etiketinin kaynağı (rapor 18.16/8). Resmî kaynakla doğrulanmış
    # etiketler bir daha incelenmez; sonraki denetimler yalnızca "learnvocab"
    # (bizim etiketimiz) olanlara bakar.
    CEFR_KAYNAK_CHOICES = [
        ("oxford", "Oxford 3000/5000"),
        ("cambridge", "Cambridge (EVP)"),
        ("learnvocab", "LearnVocab (bizim etiketimiz)"),
    ]
    cefr_kaynak = models.CharField(max_length=12, choices=CEFR_KAYNAK_CHOICES,
                                   default="learnvocab", verbose_name="seviye kaynağı")

    # Nadir tür (rapor 18.16/7): kelimenin temel türü A1–B1 iken bu tür C1–C2
    # (dog fiil, tree fiil). Sözlükte durur; L&P'ye yalnızca C1–C2 kullanıcılara
    # girer, günün kelimesi olmaz. Hesaplama: manage.py siklik_hesapla
    nadir_tur = models.BooleanField(default=False, verbose_name="nadir tür")

    # Kalıcı adres (rapor 18.15): /sozluk/<slug>/. Yazımdan üretilir
    # (words.adres.slug_yap); aynı yazımın bütün türleri aynı sayfadadır.
    slug = models.CharField(max_length=140, blank=True, default="", db_index=True,
                            editable=False)
    # Kademeli dizine alma (rapor 18.15): yalnızca True olanların sayfası
    # arama motorlarına açılır ve sitemap'e girer. Açma: manage.py dizine_ac
    dizinde = models.BooleanField(default=False, db_index=True, verbose_name="Google'a açık")

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

    def save(self, *args, **kwargs):
        from .adres import slug_yap
        self.slug = slug_yap(self.text)
        if kwargs.get("update_fields") is not None and "text" in kwargs["update_fields"]:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"slug"}
        super().save(*args, **kwargs)

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
        (RelationType.SYNONYM, _("Benzer")),
        (RelationType.SIMPLER, _("Daha basit")),
        (RelationType.ANTONYM, _("Zıt")),
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

    # Bilinirlik (rapor 18.8): Günün İfadesi yalnızca "az bilinen"lerden seçilir.
    # İşaretleme elle: words/ifadeler/bilinirlik.py
    BILINIRLIK_CHOICES = [("yaygin", "Yaygın bilinen"), ("az", "Az bilinen")]
    bilinirlik = models.CharField(max_length=6, choices=BILINIRLIK_CHOICES, default="az",
                                  db_index=True)

    # Kalıcı adres ve kademeli dizine alma: Word'deki aynı adlı alanlar gibi.
    slug = models.CharField(max_length=220, blank=True, default="", db_index=True,
                            editable=False)
    dizinde = models.BooleanField(default=False, db_index=True, verbose_name="Google'a açık")

    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("text",)

    def __str__(self):
        return self.text

    def save(self, *args, **kwargs):
        from .adres import slug_yap
        self.slug = slug_yap(self.text)
        if kwargs.get("update_fields") is not None and "text" in kwargs["update_fields"]:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"slug"}
        super().save(*args, **kwargs)

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


# ----------------------------------------------------------------------
# Hazır listeler (ürün raporu 4.1, veri işi D7)
# ----------------------------------------------------------------------

class HazirListe(models.Model):
    """
    Kurumların kelime listeleri: ODTÜ 101, Bilkent upp-int, Cambridge B2 …

    Liste sayfasında kelimeler kapalı kartlar olarak durur. "Hepsini ekle"
    YOK (rapor 17): kullanıcı "Bu listeyle çalış" der, Learn & Pass'in yeni
    kelime kaynağı seviye yerine bu liste olur (bkz. HazirListeSecimi ve
    words.hazir_liste.aktif_liste). Veriyi `hazir_liste_yukle` komutu yükler.
    """

    ad = models.CharField(max_length=80)                        # "ODTÜ 101"
    slug = models.SlugField(max_length=80, unique=True)         # adres: /listeler/odtu-101/
    kurum = models.CharField(max_length=80, blank=True)         # "ODTÜ"
    aciklama = models.CharField(max_length=300, blank=True)
    # Arayüz diline göre ad ve açıklama (rapor 18.22). Boşsa Türkçesi gösterilir.
    ad_en = models.CharField("ad (İngilizce)", max_length=80, blank=True)
    ad_de = models.CharField("ad (Almanca)", max_length=80, blank=True)
    aciklama_en = models.CharField("açıklama (İngilizce)", max_length=300, blank=True)
    aciklama_de = models.CharField("açıklama (Almanca)", max_length=300, blank=True)
    sira = models.PositiveIntegerField(default=0)
    # Yüklenip gözden geçirilene kadar Keşfet'te görünmesin.
    yayinda = models.BooleanField(default=True)
    kelimeler = models.ManyToManyField(Word, through="HazirListeKelimesi",
                                       related_name="hazir_listeler", blank=True)
    olusturulma = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sira", "ad")
        verbose_name = "hazır liste"
        verbose_name_plural = "hazır listeler"

    def __str__(self):
        return self.ad

    def _yerel(self, alan):
        from django.utils.translation import get_language
        dil = (get_language() or "tr")[:2]
        return (getattr(self, f"{alan}_{dil}", "") if dil != "tr" else "") or getattr(self, alan)

    @property
    def yerel_ad(self):
        return self._yerel("ad")

    @property
    def yerel_aciklama(self):
        return self._yerel("aciklama")

    def sirali_kelimeler(self):
        """Listedeki kelimeler, listedeki sırasıyla (L&P de bu sırayı kullanabilir)."""
        return (Word.objects.filter(hazir_liste_uyelikleri__liste=self)
                .order_by("hazir_liste_uyelikleri__sira", "hazir_liste_uyelikleri__id"))


class HazirListeKelimesi(models.Model):
    """Sıralı üyelik: listenin kaçıncı kelimesi."""

    liste = models.ForeignKey(HazirListe, on_delete=models.CASCADE, related_name="uyelikler")
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="hazir_liste_uyelikleri")
    sira = models.PositiveIntegerField(default=0)
    # Listenin içindeki bölüm (ODTÜ'de hafta: "1", "2" …; ya da konu adı). Liste
    # sayfasında başlık olur; yalnızca rakamsa "1. hafta" diye yazılır. Boş olabilir.
    bolum = models.CharField(max_length=80, blank=True, default="")
    # Kaynağın kendi kelime ailesi (More to Read II'nin Academic Word List'i: abandon -> abandoned,
    # abandoning). Doluysa kartta sözlüğün ailesi yerine bu gösterilir. Yalnızca metin.
    aile = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ("sira", "id")
        unique_together = ("liste", "word")
        verbose_name = "hazır liste kelimesi"
        verbose_name_plural = "hazır liste kelimeleri"

    def __str__(self):
        return f"{self.liste} · {self.sira}. {self.word.text}"


class HazirListeSecimi(models.Model):
    """
    "Bu listeyle çalış": kullanıcının L&P'de yeni kelimeleri seviye yerine
    bu listeden alması. Kullanıcı başına en çok bir liste; satır yoksa
    seviye kullanılır. Okumak için: words.hazir_liste.aktif_liste(user).
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="hazir_liste_secimi")
    liste = models.ForeignKey(HazirListe, on_delete=models.CASCADE, related_name="secimler")
    secildi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "hazır liste seçimi"
        verbose_name_plural = "hazır liste seçimleri"

    def __str__(self):
        return f"{self.user} → {self.liste}"


# ----------------------------------------------------------------------
# Bulunamayan aramalar (ürün raporu 4.2 ve 8)
# ----------------------------------------------------------------------

class GununKelimesi(models.Model):
    """
    Giriş yapmış kullanıcının o günkü kelimesi (rapor 18.8). Kişiye özeldir ve
    gün boyunca değişmez; bu yüzden ilk gösterildiğinde buraya yazılır.
    Gün, kullanıcının YEREL günüdür (seri ile aynı). Misafirin kelimesi
    saklanmaz; o gün herkese aynı kelime hesaplanır (words/gunun.py).

    cevap: "" (henüz cevaplamadı) · "known" (Biliyordum) · "unknown" (Bilmiyordum)
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="gunun_kelimeleri")
    gun = models.DateField()
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="gunun_kelimesi_oldu")
    cevap = models.CharField(max_length=8, blank=True, default="")
    olusturuldu = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "gun")
        verbose_name = "günün kelimesi"
        verbose_name_plural = "günün kelimeleri"

    def __str__(self):
        return f"{self.user_id} · {self.gun} · {self.word_id}"


class BulunamayanArama(models.Model):
    """
    Sözlükte karşılığı çıkmayan sorgular. Hangi kelimelerin ekleneceğine bu
    kayıttan karar verilir (rapor 4.2). Aynı sorgu tek satır, sayaç artar.
    Okumalar'da dokunulup bulunamayan kelimeler de buraya yazılabilir
    (kaynak="okuma"); yazmak için words.arama.bulunamayan_kaydet.
    """

    KAYNAK_SOZLUK = "sozluk"
    KAYNAK_OKUMA = "okuma"
    KAYNAKLAR = [(KAYNAK_SOZLUK, "Sözlük"), (KAYNAK_OKUMA, "Okumalar")]

    sorgu = models.CharField(max_length=120)                 # küçük harfe çevrilmiş
    kaynak = models.CharField(max_length=10, choices=KAYNAKLAR, default=KAYNAK_SOZLUK)
    sayi = models.PositiveIntegerField(default=1, verbose_name="kaç kez")
    # Son aramada "Bunu mu demek istediniz?" önerisi çıktı mı (büyük
    # olasılıkla yazım hatası) yoksa hiçbir şey mi çıkmadı.
    oneri_vardi = models.BooleanField(default=False, verbose_name="öneri çıktı")
    ilk = models.DateTimeField(auto_now_add=True)
    son = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("sorgu", "kaynak")
        ordering = ("-sayi", "-son")
        verbose_name = "bulunamayan arama"
        verbose_name_plural = "bulunamayan aramalar"

    def __str__(self):
        return f"{self.sorgu} ({self.sayi})"
