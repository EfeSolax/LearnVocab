"""
Çalışma kayıtları.

Bu uygulama artık "quiz" üretmiyor; ÇALIŞMA yürütüyor. Fark tasarımın
tamamını belirlediği için baştan söylemek gerekiyor:

  Eski model:  kullanıcı tip seçer -> 10 soru üretilir -> puan çıkar.
  Yeni model:  sistem neyin ne zaman sorulacağını bilir -> öğrenci
               oturuma girer -> sırası gelenler sorulur.

Eskisi bir SINAVDI. Sınav bilgiyi ölçer, oluşturmaz. Kelimeyi kalıcı
yapan şey ölçüm değil, doğru zamanda yapılan hatırlama denemesidir —
ve "doğru zaman"a karar vermek bir programın işidir, kullanıcının değil.

ÜÇ TABLO
--------
ReviewItem   Zamanlamanın birimi. (kullanıcı × kelime × boyut) başına bir
             satır; kendi kararlılığı, zorluğu ve tekrar günü var.
ReviewLog    Her cevabın kalıcı kaydı. Silinmiyor.
StudySession Bir çalışma oturumu ve o oturumun kuyruğu.

REVIEWLOG NEDEN VAR — İLERİYE DÖNÜK TEK YATIRIM
-----------------------------------------------
ReviewItem yalnızca ŞU ANKİ durumu tutar; geçmişi tutmaz. Zamanlayıcının
parametreleri (scheduler.PARAMS) şu an genel varsayılanlar. Bir gün
kişiye özel hâle getirilecekse — ki FSRS'in asıl kazancı oradadır —
bunun tek yolu geçmiş cevapların kaydıdır: hangi kart, ne kadar aralıktan
sonra, hangi kararlılıkla soruldu ve hatırlandı mı. Bu kayıt tutulmazsa
o kapı sonsuza kadar kapanır, çünkü geçmiş geriye dönük üretilemez.
Satırlar küçük ve yalnızca ileri doğru büyüyor; maliyeti önemsiz.
"""

from datetime import timedelta

from django.db import models
from django.utils import timezone

from users.models import User
from words.models import (
    Collocation, FalseFriend, Meaning, UsagePattern, Word, WordRelation,
)

from .aspects import Aspect, Format


class ItemState(models.TextChoices):
    """
    Kartın yaşam evresi.

    NEW ve LEARNING ayrımı önemli: NEW hiç sorulmamış karttır ve günlük
    yeni kart kotasına tabidir; LEARNING sorulmuş ama henüz ilk aralığını
    tamamlamamış karttır ve kotaya tabi DEĞİLDİR. Aksi hâlde kotayı
    dolduran kullanıcı, o gün başladığı kartları bitiremeden kapıda kalırdı.
    """

    NEW = "new", "yeni"
    LEARNING = "learning", "öğreniliyor"
    REVIEW = "review", "tekrar"
    RELEARNING = "relearning", "yeniden öğreniliyor"


class ReviewItem(models.Model):
    """
    Zamanlanan tek birim: bir kullanıcının bir kelimenin bir boyutu.

    HEDEFİN GENEL ANAHTARLA (generic FK) TUTULMAMASI BİLİNÇLİ
    ---------------------------------------------------------
    Boyuta göre hedef değişiyor: tanıma bir Meaning'e, eş dizim bir
    Collocation'a, karıştırılan çift bir WordRelation'a bakıyor. Doğal
    çözüm Django'nun GenericForeignKey'i olurdu; kullanılmadı. Sebep:
    bu tablodaki EN SIK sorgu "bu kullanıcının bugün sırası gelen
    kartları" ve o sorgunun hızlı olması gerekiyor. GenericForeignKey
    her erişimde content_type üzerinden ikinci bir sorgu açar ve
    select_related edilemez.

    Onun yerine: `word` her zaman dolu (filtrelemenin ve birleştirmenin
    tuttuğu yer), `meaning` anlama bağlı boyutlarda dolu, `target_id`
    ise ilgili satırın birincil anahtarı — çözümlemesi `target`
    özelliğinde, yalnızca soru üretilirken yapılıyor.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="review_items")

    # Her zaman dolu: kartın ait olduğu kelime.
    word = models.ForeignKey(Word, on_delete=models.CASCADE,
                             related_name="review_items")
    # Anlama bağlı boyutlarda dolu (tanıma, üretim, bağlam, eş dizim,
    # kalıp, ton). Kelime düzeyindeki boyutlarda (çekim, yanlış dost,
    # karıştırılan çift, aile) boş.
    meaning = models.ForeignKey(Meaning, on_delete=models.CASCADE,
                                blank=True, null=True,
                                related_name="review_items")

    aspect = models.CharField(max_length=20, choices=Aspect.choices,
                              verbose_name="boyut")
    # İlgili satırın pk'sı; 0 = hedef yok (boyut zaten meaning/word ile belli).
    target_id = models.PositiveIntegerField(default=0)

    # --- hafıza durumu (bkz. scheduler.py) ---------------------------------
    state = models.CharField(max_length=12, choices=ItemState.choices,
                             default=ItemState.NEW)
    stability = models.FloatField(blank=True, null=True, verbose_name="kararlılık")
    difficulty = models.FloatField(blank=True, null=True, verbose_name="zorluk")

    due_at = models.DateTimeField(blank=True, null=True, db_index=True,
                                  verbose_name="sırası geldiği an")
    last_reviewed_at = models.DateTimeField(blank=True, null=True)
    last_interval_days = models.FloatField(default=0)

    reps = models.PositiveIntegerField(default=0, verbose_name="tekrar sayısı")
    lapses = models.PositiveIntegerField(default=0, verbose_name="unutma sayısı")

    # Yüksek güvenli hatanın zorunlu tekrar tarihi.
    # Hızlı verilen yanlış cevap, düzeltildikten sonra bir hafta içinde
    # geri gelme eğilimindedir (bkz. scheduler.yuksek_guvenli_hata).
    # Zamanlayıcı daha uzak bir gün hesaplasa bile kart bu tarihe kadar
    # mutlaka bir kez daha sorulur.
    recheck_by = models.DateTimeField(blank=True, null=True,
                                      verbose_name="en geç tekrar")

    # Kart hangi kelime listesinden geldi (varsa) — oturumu listeye
    # daraltmak için. Silinirse kart kalır, yalnızca bağ kopar.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("due_at", "id")
        indexes = [
            models.Index(fields=["user", "due_at"]),
            models.Index(fields=["user", "state"]),
            models.Index(fields=["user", "word"]),
            models.Index(fields=["user", "aspect"]),
        ]
        constraints = [
            # Anlama bağlı kartlarda tekillik anlam üzerinden;
            # kelime düzeyindekilerde kelime üzerinden. İki ayrı kısıt
            # olmasının sebebi SQL'de NULL'un NULL'a eşit sayılmaması:
            # tek bir unique_together, meaning boşken hiçbir şeyi
            # engellemezdi ve aynı kart defalarca oluşurdu.
            models.UniqueConstraint(
                fields=["user", "meaning", "aspect", "target_id"],
                condition=models.Q(meaning__isnull=False),
                name="uniq_review_item_meaning",
            ),
            models.UniqueConstraint(
                fields=["user", "word", "aspect", "target_id"],
                condition=models.Q(meaning__isnull=True),
                name="uniq_review_item_word",
            ),
        ]

    def __str__(self):
        return f"{self.user.username} · {self.word.text} · {self.get_aspect_display()}"

    # --- hedef çözümleme ---------------------------------------------------

    #: Boyut -> hedefin bulunduğu model. target_id 0 ise hedef yoktur.
    TARGET_MODELS = {
        Aspect.COLLOCATION: Collocation,
        Aspect.PATTERN: UsagePattern,
        Aspect.FALSE_FRIEND: FalseFriend,
        Aspect.CONFUSABLE: WordRelation,
    }

    @property
    def target(self):
        """Kartın dayandığı satır (eş dizim, kalıp, yanlış dost, bağ)."""
        model = self.TARGET_MODELS.get(self.aspect)
        if model is None or not self.target_id:
            return None
        return model.objects.filter(pk=self.target_id).first()

    @property
    def is_due(self):
        return self.due_at is not None and self.due_at <= timezone.now()

    @property
    def is_new(self):
        return self.state == ItemState.NEW

    @property
    def elapsed_days(self) -> float:
        """En son sorulmasından bu yana geçen gün (kesirli)."""
        if not self.last_reviewed_at:
            return 0.0
        fark = timezone.now() - self.last_reviewed_at
        return max(fark.total_seconds() / 86400.0, 0.0)

    @property
    def retrievability(self) -> float:
        """
        Şu anda sorulsa hatırlanma olasılığı.

        İlerleme göstergesi olarak DOĞRU ölçü budur, "kaç kelime
        çalıştım" değil. Bir kullanıcının bilgisi, kartlarının
        hatırlanabilirlik toplamıdır; zamanla kendiliğinden erir ve
        yalnızca tekrarla geri gelir. Sayfada gösterilen "kalıcı bilgi"
        değeri bunun toplamı.
        """
        from . import scheduler

        if self.stability is None:
            return 0.0
        return scheduler.hatirlanabilirlik(self.elapsed_days, self.stability)

    def memory(self):
        """Zamanlayıcının anlayacağı hafıza nesnesi (yoksa None)."""
        from . import scheduler

        if self.stability is None or self.difficulty is None:
            return None
        return scheduler.Hafiza(kararlilik=self.stability, zorluk=self.difficulty)


class ReviewLog(models.Model):
    """
    Tek bir cevabın kalıcı kaydı.

    Kart silinse bile kayıt durur (`item` boşa düşer, `user` kalır):
    parametre eğitimi için geçmişin bütünlüğü, tek tek kartların
    varlığından önemli.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="review_logs")
    item = models.ForeignKey(ReviewItem, on_delete=models.SET_NULL,
                             blank=True, null=True, related_name="logs")
    session = models.ForeignKey("StudySession", on_delete=models.SET_NULL,
                                blank=True, null=True, related_name="logs")

    # Kaydın kendi başına anlamlı olması için kopyalanan alanlar.
    # (item silinse bile hangi kelimenin hangi boyutuydu, bilinsin.)
    word_text = models.CharField(max_length=120)
    aspect = models.CharField(max_length=20, choices=Aspect.choices)
    format = models.CharField(max_length=16, choices=Format.choices)

    is_correct = models.BooleanField()
    grade = models.PositiveSmallIntegerField(verbose_name="not (1-4)")
    seconds = models.FloatField(blank=True, null=True)
    used_hint = models.BooleanField(default=False)
    # Hızlı verilmiş yanlış cevap — bkz. ReviewItem.recheck_by
    was_confident_error = models.BooleanField(default=False)

    # Cevap ANINDAKİ durum (öncesi) ve sonrasındaki durum.
    # İkisi birden tutuluyor çünkü parametre eğitimi "şu kararlılıkla,
    # şu kadar gün sonra sorulduğunda hatırlandı mı" sorusunu sorar.
    elapsed_days = models.FloatField(default=0)
    stability_before = models.FloatField(blank=True, null=True)
    difficulty_before = models.FloatField(blank=True, null=True)
    stability_after = models.FloatField(blank=True, null=True)
    difficulty_after = models.FloatField(blank=True, null=True)
    scheduled_days = models.FloatField(default=0)

    answered_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-answered_at", "-id")
        indexes = [
            models.Index(fields=["user", "answered_at"]),
        ]

    def __str__(self):
        sonuc = "doğru" if self.is_correct else "yanlış"
        return f"{self.user.username} · {self.word_text} · {sonuc}"


class SessionMode(models.TextChoices):
    """
    Oturum modu.

    DUE tek gerçek moddur; diğer ikisi kullanıcının kendi isteğiyle
    programın dışına çıktığı hâllerdir ve bilinçli olarak zamanlamayı
    BOZMAZLAR: serbest çalışmada verilen cevaplar da kaydedilir ve
    kartları ilerletir, yalnızca kart seçimi sıraya değil kullanıcının
    seçtiği listeye göre yapılır.
    """

    DUE = "due", "Sırası gelenler"
    LIST = "list", "Seçili liste"
    WEAK = "weak", "Zorlandıklarım"


class StudySession(models.Model):
    """
    Bir çalışma oturumu.

    Kuyruk veritabanında tutuluyor, oturum (session) çerezinde değil:
    kullanıcı sayfayı yenilediğinde, telefondan devam ettiğinde ya da
    sunucu birden çok süreçle çalıştığında kaldığı yerden devam etsin.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="study_sessions")
    mode = models.CharField(max_length=10, choices=SessionMode.choices,
                            default=SessionMode.DUE)

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    planned_count = models.PositiveIntegerField(default=0,
                                                verbose_name="planlanan soru")
    answered_count = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)

    # Kuyruk: sırası gelen ReviewItem id'leri.
    # Yanlış cevaplanan kart bu listenin İÇİNE geri konuyor (oturum içi
    # tekrar), o yüzden liste çalışma sırasında hem kısalıyor hem uzuyor.
    queue = models.JSONField(default=list, blank=True)
    # Bu oturumda en az bir kez yanlış cevaplanmış kart id'leri —
    # oturum sonu özetinde "bunlar takıldıkların" diye gösteriliyor.
    missed = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ("-started_at",)
        indexes = [models.Index(fields=["user", "started_at"])]

    def __str__(self):
        return f"{self.user.username} · {self.started_at:%d.%m.%Y %H:%M}"

    @property
    def is_finished(self):
        return self.finished_at is not None

    @property
    def remaining(self):
        return len(self.queue or [])

    @property
    def accuracy(self):
        if not self.answered_count:
            return 0
        return round(100 * self.correct_count / self.answered_count)

    @property
    def duration_seconds(self):
        bitis = self.finished_at or timezone.now()
        return int((bitis - self.started_at).total_seconds())

    @property
    def formatted_duration(self):
        toplam = self.duration_seconds
        dakika, saniye = divmod(toplam, 60)
        if dakika:
            return f"{dakika} dk {saniye} sn"
        return f"{saniye} sn"

    def finish(self):
        if self.finished_at is None:
            self.finished_at = timezone.now()
            self.save(update_fields=["finished_at"])


class DailyGoalDefaults:
    """
    Günlük yeni kart sınırının varsayılanları.

    UserSettings.dailyGoal "günde kaç kelime" olarak zaten var ve
    kullanıcıya sorulmuş bir sayı; yenisini sormak yerine o kullanılıyor.
    Sıfır seçilmişse yeni kart hiç açılmaz — yalnızca tekrar yapılır,
    bu da geçerli bir çalışma biçimidir (sınav haftası).
    """

    NEW_ITEMS_FALLBACK = 5
    # Birikmiş tekrar bu sayıyı aşarsa yeni kelime AÇILMAZ.
    # Aralıklı tekrar uygulamalarının klasik ölüm sarmalı budur: kullanıcı
    # her gün yeni kart ekler, birikmiş tekrar büyür, bir gün 300 kart
    # görüp uygulamayı siler. Borç varken yeni borç açılmıyor.
    BACKLOG_BLOCK_THRESHOLD = 60


def due_items(user, now=None):
    """Sırası gelmiş kartlar (yeni olanlar hariç)."""
    now = now or timezone.now()
    return (ReviewItem.objects
            .filter(user=user, due_at__lte=now)
            .exclude(state=ItemState.NEW))


def new_items(user):
    """Hiç sorulmamış kartlar."""
    return ReviewItem.objects.filter(user=user, state=ItemState.NEW)


def overdue_count(user, now=None):
    """Gecikmiş kart sayısı — yeni kart açılıp açılmayacağına bu karar verir."""
    return due_items(user, now).count()


def studied_today(user, now=None):
    """Bugün cevaplanan kart sayısı (yeni kart kotası için)."""
    now = now or timezone.now()
    bugun = now.astimezone(timezone.get_current_timezone()).date()
    return ReviewLog.objects.filter(user=user, answered_at__date=bugun).count()


def new_items_introduced_today(user, now=None):
    """Bugün ilk kez açılan kart sayısı."""
    now = now or timezone.now()
    bugun = now.astimezone(timezone.get_current_timezone()).date()
    return (ReviewItem.objects
            .filter(user=user, reps=1, last_reviewed_at__date=bugun)
            .count())


def knowledge_score(user):
    """
    "Kalıcı bilgi" — kullanıcının kartlarının hatırlanabilirlik toplamı.

    Kaç kelime çalıştığından farklı bir şey ölçer: çalışılan kelime
    sayısı yalnızca artar, bu değer çalışılmadığında düşer. Gerçekte
    olan da budur. Kullanıcıya gösterilen sayının gerçeği yansıtması,
    motive edici olmasından önemli — şişirilmiş bir ilerleme çubuğu
    öğrenciyi çalışmaması gerektiğine ikna eder.
    """
    toplam = 0.0
    for item in ReviewItem.objects.filter(user=user).exclude(stability=None):
        toplam += item.retrievability
    return round(toplam, 1)


def study_streak(user, now=None):
    """Kaç gündür aralıksız çalışıyor."""
    now = now or timezone.now()
    tz = timezone.get_current_timezone()
    gunler = set(
        ReviewLog.objects.filter(user=user)
        .values_list("answered_at", flat=True)
    )
    tarihler = {an.astimezone(tz).date() for an in gunler}
    if not tarihler:
        return 0

    bugun = now.astimezone(tz).date()
    # Bugün henüz çalışmadıysa seri dünden sayılır; bugünü kaçırmak
    # seriyi anında sıfırlamamalı (gün daha bitmedi).
    baslangic = bugun if bugun in tarihler else bugun - timedelta(days=1)
    if baslangic not in tarihler:
        return 0

    seri = 0
    gun = baslangic
    while gun in tarihler:
        seri += 1
        gun -= timedelta(days=1)
    return seri
