"""
Öğren-Geç kayıtları.

Kullanıcı bir kelimeyi gördüğünde verdiği karar burada tutuluyor. İki işi var:

1) "Yeni Kelimeler" modunda aynı kelimenin yarın tekrar karşısına çıkmaması.
2) "Bildiğini sanma" verisini biriktirmek: kullanıcı "biliyorum" deyip anlamı
   gördükten sonra yanıldığını kabul ettiyse, bu kelime onun kendi başına asla
   çalışmayacağı bir kelimedir — egzersizlerde öne alınıyor.

Kullanıcı+kelime başına TEK satır tutuluyor; her karşılaşmada güncelleniyor.
Tam geçmiş (her dokunuşun ayrı kaydı) gerekmediği için sayaçlar yeterli.
"""

from django.db import models

from users.models import User
from words.models import Word


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
    misjudged_count = models.PositiveIntegerField(default=0)

    # "Öğrenildi" işareti: kelime listeden SİLİNMİYOR, yalnızca Öğren-Geç'te
    # bir daha karşısına çıkmıyor ve egzersizlerde en son sıraya düşüyor.
    # Kullanıcı yanılırsa işaret kendiliğinden kalkıyor (bkz. record()).
    is_learned = models.BooleanField(default=False)

    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "word")
        indexes = [
            models.Index(fields=["user", "is_learned"]),
            models.Index(fields=["user", "last_seen_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} · {self.word.englishWord} · {self.get_last_verdict_display()}"

    @property
    def was_misjudged(self):
        """Kullanıcı bu kelimede en az bir kez bildiğini sanıp yanıldı mı?"""
        return self.misjudged_count > 0

    @classmethod
    def record(cls, user, word, verdict, mode):
        """
        Bir karşılaşmayı kaydeder ve güncel satırı döner.

        "Öğrenildi" işareti yalnızca kullanıcı bildiğini DOĞRULADIĞINDA konuyor.
        Sonradan aynı kelimede yanılırsa işaret kalkıyor: bir kez "biliyorum"
        demiş olmak kelimeyi sonsuza kadar gözden kaçırmamıza sebep olmamalı.
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
            encounter.is_learned = True
        else:  # UNKNOWN
            encounter.is_learned = False

        encounter.save()
        return encounter
