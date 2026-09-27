"""
Öğren-Geç kayıtları.

BU BÖLÜMÜN İŞİ NEDİR
--------------------
Öğren-Geç bir alıştırma değil, bir ÖLÇÜM. Kullanıcıya soru sormuyor,
puan vermiyor, kartları zamanlamıyor — onu Çalışma bölümü yapıyor
(quizzes/). Öğren-Geç'in topladığı şey başka türden ve başka hiçbir
yerden elde edilemeyen bir veri:

    Kullanıcı bu kelimeyi BİLDİĞİNİ DÜŞÜNÜYOR MU?

Bu, "doğru cevap verdi mi" sorusundan farklıdır ve ondan bağımsız olarak
yanlış olabilir. İnsan kendi bilgisini sistematik olarak fazla tahmin
eder; bir kelimeye bakıp "bunu biliyorum" deyip anlamı görünce
yanıldığını fark etmek, o kelimenin kendi başına ASLA çalışılmayacağı
anlamına gelir — çünkü öğrenci onu eksik saymıyor.

İKİ KATMANLI VERİ
-----------------
WordEncounter  kullanıcı+kelime başına TEK satır, güncel durum.
EncounterLog   her dokunuşun ayrı kaydı, hiç silinmez.

İkincisi Çalışma'daki ReviewLog ile aynı gerekçeyle var: geçmiş geriye
dönük üretilemez. Bugün yalnızca sayaç tutup yarın "kullanıcı bu kelimeyi
kaçıncı karşılaşmada öğrendi" diye sorulduğunda cevap veremeyiz.
Satırlar küçük, yalnızca ileri doğru büyüyor.

KULLANICININ KENDİ BEYANI
-------------------------
Sayaçların söyleyemediği bir şey var: kullanıcı bir kelimeyi kaç kez
görürse görsün, o kelimeyle arasındaki ilişkiyi en iyi kendisi bilir.
İki beyan toplanıyor ve ikisi de yalnızca kelime YETERİNCE GÖRÜLDÜKTEN
sonra sorulabiliyor (bkz. BEYAN_ESIGI):

  MASTERED  "artık öğrendim, karşıma çıka çıka halloldu"
  STUCK     "bu kadar çok çıkmasına rağmen hâlâ öğrenemedim"

İkincisi birincisinden daha değerli. "Öğrendim" zaten sayaçlardan tahmin
edilebilir; "bu kadar gördüm ve hâlâ olmuyor" ise tahmin edilemez ve
başka türlü bir müdahale gerektirir: o kelime daha sık sorulmakla
öğrenilmiyor, farklı bir yoldan çalışılması gerekiyor.

BEYANLAR ZAMANLAMAYI DEĞİŞTİRMEZ
--------------------------------
Bilerek: aralıklı tekrarın aralıkları CEVAPLARDAN hesaplanıyor
(quizzes/scheduler.py) ve kullanıcının kendi hakkındaki yargısı o
hesabın girdisi değil — olsaydı, sistemin kendisini yanıltmasına izin
vermiş olurduk. Beyan yalnızca SIRALAMAYI etkiliyor: aynı gün sırası
gelmiş kartlar arasında "hâlâ öğrenemedim" denenler öne alınıyor.
Sıralama değiştirmek zamanlamayı bozmaz.
"""

from django.db import models
from django.utils import timezone

from users.models import User
from words.models import Word


# Kullanıcıya "öğrendim / öğrenemedim" beyanının sorulması için kelimenin
# en az kaç kez görülmüş olması gerekir.
#
# Üç sayısı keyfî değil: beyanın anlamı "bu kadar çok çıkmasına RAĞMEN".
# İlk ya da ikinci karşılaşmada "hâlâ öğrenemedim" demek bir bilgi
# taşımaz — henüz öğrenme fırsatı olmamıştır.
BEYAN_ESIGI = 3


class Declaration(models.TextChoices):
    """Kullanıcının kelime hakkındaki kendi beyanı."""

    NONE = "none", "beyan yok"
    MASTERED = "mastered", "artık öğrendim"
    STUCK = "stuck", "hâlâ öğrenemedim"


class WordEncounter(models.Model):
    # Kullanıcının karara bağladığı üç sonuç
    UNKNOWN = "unknown"        # "Bilmiyorum"
    KNOWN = "known"            # "Biliyorum" -> "Evet, aklımdaki buydu"
    MISJUDGED = "misjudged"    # "Biliyorum" -> "Hayır, yanılmışım"

    VERDICT_CHOICES = [
        (UNKNOWN, "Bilmiyordu"),
        (KNOWN, "Biliyordu"),
        (MISJUDGED, "Bildiğini sanıyordu"),
    ]

    # Kartın hangi modda geldiği
    MODE_MINE = "mine"
    MODE_NEW = "new"
    MODE_CHOICES = [
        (MODE_MINE, "Kendi Kelimelerim"),
        (MODE_NEW, "Yeni Kelimeler"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="word_encounters")
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="encounters")

    last_verdict = models.CharField(max_length=20, choices=VERDICT_CHOICES)
    last_mode = models.CharField(max_length=10, choices=MODE_CHOICES, default=MODE_NEW)

    times_seen = models.PositiveIntegerField(default=0)

    # Karar sayaçları. `misjudged_count` eskiden tek başına tutuluyordu;
    # diğer ikisi eklendi çünkü zorlanma oranı ancak üçü birlikte
    # hesaplanabiliyor (5 kez görülüp 4'ünde bilinmeyen bir kelimeyle,
    # 5 kez görülüp 1'inde bilinmeyen kelime aynı şey değil).
    unknown_count = models.PositiveIntegerField(default=0)
    known_count = models.PositiveIntegerField(default=0)
    misjudged_count = models.PositiveIntegerField(default=0)

    # "Öğrenildi" işareti: kelime listeden SİLİNMİYOR, yalnızca Öğren-Geç'te
    # bir daha karşısına çıkmıyor ve egzersizlerde en son sıraya düşüyor.
    # Kullanıcı yanılırsa işaret kendiliğinden kalkıyor (bkz. record()).
    is_learned = models.BooleanField(default=False)

    # Kullanıcının kendi beyanı (bkz. dosya başındaki açıklama).
    declaration = models.CharField(max_length=10, choices=Declaration.choices,
                                   default=Declaration.NONE,
                                   verbose_name="kullanıcının beyanı")
    declared_at = models.DateTimeField(blank=True, null=True)
    # Beyan verildiği ANDAKİ karşılaşma sayısı. "Kaçıncı karşılaşmada
    # öğrendiğini söyledi" sorusunun cevabı; sonradan times_seen büyüdüğü
    # için ayrıca saklanması gerekiyor.
    declared_after_seen = models.PositiveIntegerField(default=0)

    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "word")
        indexes = [
            models.Index(fields=["user", "is_learned"]),
            models.Index(fields=["user", "last_seen_at"]),
            models.Index(fields=["user", "declaration"]),
        ]

    def __str__(self):
        return f"{self.user.username} · {self.word.text} · {self.get_last_verdict_display()}"

    @property
    def was_misjudged(self):
        """Kullanıcı bu kelimede en az bir kez bildiğini sanıp yanıldı mı?"""
        return self.misjudged_count > 0

    @property
    def miss_count(self):
        """Bilinemeyen karşılaşma sayısı (bilmiyorum + yanılmışım)."""
        return self.unknown_count + self.misjudged_count

    @property
    def miss_ratio(self):
        """
        Zorlanma oranı (0-1).

        `misjudged` ağırlıklı sayılıyor: bildiğini sanıp yanılmak, düpedüz
        bilmemekten daha kötü bir durumdur. Bilmediğini bilen öğrenci o
        kelimeyi çalışır; bildiğini sanan çalışmaz.

        Oran 1.0'da doyuyor: bütün karşılaşmaları kaçırılmış iki kelime
        eşit sayılıyor. Ağırlık yalnızca karışık durumlarda ayrım yapıyor
        ki asıl anlamlı olan da orası — hepsini kaçırdığı kelimelerin
        ikisi de azami derecede sorunlu.
        """
        if not self.times_seen:
            return 0.0
        agirlikli = self.unknown_count + (self.misjudged_count * 1.5)
        return min(agirlikli / self.times_seen, 1.0)

    @property
    def can_declare(self):
        """Kullanıcıya 'öğrendim / öğrenemedim' sorulabilir mi?"""
        return self.times_seen >= BEYAN_ESIGI

    @property
    def is_stuck(self):
        return self.declaration == Declaration.STUCK

    @property
    def is_mastered(self):
        return self.declaration == Declaration.MASTERED

    @classmethod
    def record(cls, user, word, verdict, mode):
        """
        Bir karşılaşmayı kaydeder ve güncel satırı döner.

        "Öğrenildi" işareti yalnızca kullanıcı bildiğini DOĞRULADIĞINDA
        konuyor. Sonradan aynı kelimede yanılırsa işaret kalkıyor: bir kez
        "biliyorum" demiş olmak kelimeyi sonsuza kadar gözden kaçırmamıza
        sebep olmamalı.

        Kullanıcı daha önce "hâlâ öğrenemedim" demiş ve sonra kelimeyi
        DOĞRULAYARAK bildiyse beyan kalkıyor — takıldığı yerden çıkmış
        demektir ve eski beyanı onu sonsuza kadar zor kelime saymamalı.
        """
        encounter, _ = cls.objects.get_or_create(user=user, word=word, defaults={
            "last_verdict": verdict,
            "last_mode": mode,
        })

        encounter.last_verdict = verdict
        encounter.last_mode = mode
        encounter.times_seen += 1

        if verdict == cls.MISJUDGED:
            encounter.misjudged_count += 1
            encounter.is_learned = False
        elif verdict == cls.KNOWN:
            encounter.known_count += 1
            encounter.is_learned = True
            if encounter.declaration == Declaration.STUCK:
                encounter.declaration = Declaration.NONE
                encounter.declared_at = None
        else:  # UNKNOWN
            encounter.unknown_count += 1
            encounter.is_learned = False
            # "Artık öğrendim" demiş ama bilemediyse beyan düşüyor.
            if encounter.declaration == Declaration.MASTERED:
                encounter.declaration = Declaration.NONE
                encounter.declared_at = None

        encounter.save()

        EncounterLog.objects.create(
            user=user, word=word, word_text=word.text,
            kind=EncounterLog.VERDICT, verdict=verdict, mode=mode,
            seen_index=encounter.times_seen,
        )
        return encounter

    def declare(self, declaration):
        """
        Kullanıcının beyanını kaydeder.

        MASTERED aynı zamanda kelimeyi Öğren-Geç havuzundan çıkarıyor
        (is_learned): kullanıcı zaten "bir daha karşıma çıkmasın" diyor.
        STUCK çıkarmıyor — tam tersine kelimeyi en öne alıyor.
        """
        if declaration not in (Declaration.MASTERED, Declaration.STUCK):
            return self

        self.declaration = declaration
        self.declared_at = timezone.now()
        self.declared_after_seen = self.times_seen
        if declaration == Declaration.MASTERED:
            self.is_learned = True
        else:
            self.is_learned = False
        self.save()

        EncounterLog.objects.create(
            user=self.user, word=self.word, word_text=self.word.text,
            kind=EncounterLog.DECLARATION, declaration=declaration,
            mode=self.last_mode, seen_index=self.times_seen,
        )
        return self


class EncounterLog(models.Model):
    """
    Her dokunuşun kalıcı kaydı.

    WordEncounter yalnızca ŞU ANKİ durumu tutuyor. Bu tablo geçmişi
    tutuyor ve şu soruların cevabı yalnızca burada var:

      - Kullanıcı bu kelimeyi kaçıncı karşılaşmada öğrendiğini söyledi?
      - "Bildiğini sanma" hataları zamanla azalıyor mu?
      - Hangi kelimeler çok görülmesine rağmen öğrenilmiyor? (İçerik
        sorunu olabilir: kötü örnek cümle, yanlış anlam, fazla soyut.)
      - Bir kelimeyi "öğrendim" dedikten sonra Çalışma'da kaç kez unuttu?
        (= kullanıcının kendine güveni ne kadar kalibre?)

    Bu sorular bugün sorulmuyor ama sorulacakları gün veri yoksa cevap
    üretilemez; geçmiş geriye dönük uydurulamaz. Satır başına birkaç
    bayt, yılda birkaç bin satır.
    """

    VERDICT = "verdict"
    DECLARATION = "declaration"
    KIND_CHOICES = [
        (VERDICT, "karşılaşma"),
        (DECLARATION, "beyan"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="encounter_logs")
    # Kelime silinse bile kayıt kalsın: word_text kopyalanıyor.
    word = models.ForeignKey(Word, on_delete=models.SET_NULL, blank=True, null=True,
                             related_name="encounter_logs")
    word_text = models.CharField(max_length=120)

    kind = models.CharField(max_length=12, choices=KIND_CHOICES, default=VERDICT)
    verdict = models.CharField(max_length=20, blank=True, null=True,
                               choices=WordEncounter.VERDICT_CHOICES)
    declaration = models.CharField(max_length=10, blank=True, null=True,
                                   choices=Declaration.choices)
    mode = models.CharField(max_length=10, blank=True, null=True,
                            choices=WordEncounter.MODE_CHOICES)

    # Bu kayıt sırasında kelimenin kaçıncı kez görüldüğü.
    seen_index = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self):
        etiket = self.verdict or self.declaration or "?"
        return f"{self.user.username} · {self.word_text} · {etiket}"
