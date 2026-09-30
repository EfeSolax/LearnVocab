"""
Learn & Pass ve egzersiz karşılaşmalarının kayıtları (rapor 18.2 tekrar kuralı).

İKİ KATMANLI VERİ
-----------------
WordEncounter  kullanıcı+kelime başına TEK satır: güncel durum, sayaçlar ve
               tekrar kuralının basamağı.
EncounterLog   her cevabın ayrı kaydı. Tekrar biriminin (1 gün) doğru olup
               olmadığını ölçmek için (rapor 18.31: basamak başına unutma
               oranı) cevap anındaki basamak da yazılır.

TEKRAR KURALI (rapor 18.2; kuralın kendisi learnpass/tekrar.py)
---------------------------------------------------------------
- Bilinen kelime 1 · 3 · 7 · 21 gün arayla gelir (21'den sonra 21 günde bir).
  `basamak` art arda kaç kez bilindiğini, `sonraki_tekrar` ne zaman yeniden
  aday olacağını tutar.
- Bilemezse ("bilmiyorum", "yanılmışım", egzersizde yanlış) bütün ilerleme
  sıfırlanır: basamak 0, `son_basarili` False (her zaman aday). Sayaçlar
  SİLİNMEZ; zorlanma oranı onlardan hesaplanır.
- "Öğrenildi" kavramı YOK (rapor 17).
"""

from django.db import models

from users.models import User
from words.models import Word


class WordEncounter(models.Model):
    # L&P kararları (18.1)
    UNKNOWN = "unknown"        # "Bilmiyorum"
    KNOWN = "known"            # "Biliyorum" -> "Evet, eminim"
    MISJUDGED = "misjudged"    # "Biliyorum" -> "Hayır, yanılmışım"
    # Egzersiz sonuçları (yalnızca günlükte)
    DOGRU = "dogru"
    YANLIS = "yanlis"

    VERDICT_CHOICES = [
        (UNKNOWN, "Bilmiyordu"),
        (KNOWN, "Biliyordu"),
        (MISJUDGED, "Bildiğini sanıyordu"),
        (DOGRU, "Egzersizde doğru"),
        (YANLIS, "Egzersizde yanlış"),
    ]

    # Kartın / cevabın nereden geldiği
    MODE_MINE = "mine"
    MODE_NEW = "new"
    MODE_EGZERSIZ = "egzersiz"
    MODE_CHOICES = [
        (MODE_MINE, "Tekrar"),
        (MODE_NEW, "Yeni Kelimeler"),
        (MODE_EGZERSIZ, "Egzersiz"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="word_encounters")
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="encounters")

    last_verdict = models.CharField(max_length=20, choices=VERDICT_CHOICES)
    last_mode = models.CharField(max_length=10, choices=MODE_CHOICES, default=MODE_NEW)

    # Toplam karşılaşma (L&P + egzersiz). Zorlanma oranının paydası.
    times_seen = models.PositiveIntegerField(default=0)

    # Sayaçlar: sıfırlamada SİLİNMEZ (rapor 18.2 e).
    unknown_count = models.PositiveIntegerField(default=0)
    known_count = models.PositiveIntegerField(default=0)
    misjudged_count = models.PositiveIntegerField(default=0)
    egz_dogru = models.PositiveIntegerField(default=0)
    egz_yanlis = models.PositiveIntegerField(default=0)

    # --- Tekrar kuralı (rapor 18.2) ---
    # Art arda kaç kez bilindiği. 0 = zincir yok (yeni ya da sıfırlandı).
    basamak = models.PositiveSmallIntegerField(default=0)
    # Son sonuç başarılı mı? False ise kelime "zorlandığı" kelimedir ve her
    # zaman adaydır; Listem'deki "Zorlandıklarım" da budur.
    son_basarili = models.BooleanField(default=True)
    # Aralığın başladığı an: çalışmada en son görülüp BİLİNDİĞİ an (18.2 b).
    son_bilinen_at = models.DateTimeField(blank=True, null=True)
    # Bu andan sonra yeniden aday olur. Zorlanan kelimede boş (hep aday).
    sonraki_tekrar = models.DateTimeField(blank=True, null=True)
    # Listede olmasa da tekrar takibinde mi? L&P'de bilmediği ya da yanıldığı
    # her kelime takibe girer; yeni kelimeye ilk seferde "eminim" denirse girmez.
    takipte = models.BooleanField(default=False)

    # "Bilmiyorum" denmiş, listede OLMAYAN ve kullanıcıya henüz "listene
    # ekleyelim mi?" diye sorulmamış kelime (rapor 6.1).
    listeye_sorulacak = models.BooleanField(default=False)

    first_seen_at = models.DateTimeField(auto_now_add=True)
    # Son karşılaşma (L&P ve egzersiz ortak). Sıralamanın ilk ölçütü (18.2/3).
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "word")
        indexes = [
            models.Index(fields=["user", "last_seen_at"]),
            models.Index(fields=["user", "son_basarili"]),
            models.Index(fields=["user", "sonraki_tekrar"]),
        ]

    def __str__(self):
        return f"{self.user.username} · {self.word.text} · {self.get_last_verdict_display()}"

    @property
    def miss_count(self):
        """Bilinemeyen karşılaşma sayısı (bilmiyorum + yanılmışım + egzersizde yanlış)."""
        return self.unknown_count + self.misjudged_count + self.egz_yanlis

    @property
    def zorlanma_orani(self):
        """0-1: karşılaşmaların ne kadarında bilinemedi (sıralamanın ikinci ölçütü)."""
        if not self.times_seen:
            return 0.0
        return min(self.miss_count / self.times_seen, 1.0)


class EncounterLog(models.Model):
    """
    Her cevabın kalıcı kaydı (L&P ve egzersiz).

    WordEncounter yalnızca şu anki durumu tutar; geçmiş geriye dönük
    üretilemez. `basamak_once` ile "hangi basamakta ne kadar unutuluyor"
    ölçülür ve tekrar birimi ona göre ayarlanır (rapor 18.2 a, 18.31).
    Rapor 18.32: ayrıntılı kayıtlar 90 gün tutulur; daha eskileri kişisiz
    günlük özetlere (KarsilasmaOzeti) çevrilip silinir: manage.py karsilasma_ozetle
    """

    VERDICT = "verdict"
    KIND_CHOICES = [(VERDICT, "karşılaşma")]

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="encounter_logs")
    # Kelime silinse bile kayıt kalsın: word_text kopyalanıyor.
    word = models.ForeignKey(Word, on_delete=models.SET_NULL, blank=True, null=True,
                             related_name="encounter_logs")
    word_text = models.CharField(max_length=120)

    kind = models.CharField(max_length=12, choices=KIND_CHOICES, default=VERDICT)
    verdict = models.CharField(max_length=20, blank=True, null=True,
                               choices=WordEncounter.VERDICT_CHOICES)
    mode = models.CharField(max_length=10, blank=True, null=True,
                            choices=WordEncounter.MODE_CHOICES)

    # Bu kayıt sırasında kelimenin kaçıncı kez görüldüğü.
    seen_index = models.PositiveIntegerField(default=0)
    # Cevaptan ÖNCEKİ basamak (0 = zincir yok).
    basamak_once = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self):
        return f"{self.user.username} · {self.word_text} · {self.verdict or '?'}"


class KarsilasmaOzeti(models.Model):
    """
    90 günden eski EncounterLog kayıtlarının KİŞİSİZ günlük özeti (rapor 18.32).
    Veritabanı 1 GB sınırının altında kalsın diye ayrıntı silinir, yalnızca
    toplu sayı kalır. Kullanıcı ya da kelime bilgisi YOKTUR.
    İstatistik ekranı (LearnVocab/istatistik.py) ayrıntılı kayıtlarla birlikte
    bunu da okur.

    gun: kaydın tarihi (sunucu saatiyle) · mode · basamak_once · verdict · sayi
    """

    gun = models.DateField()
    mode = models.CharField(max_length=10, blank=True, default="")
    basamak_once = models.PositiveSmallIntegerField(default=0)
    verdict = models.CharField(max_length=20, blank=True, default="")
    sayi = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "karşılaşma özeti"
        verbose_name_plural = "karşılaşma özetleri"
        constraints = [models.UniqueConstraint(fields=["gun", "mode", "basamak_once", "verdict"],
                                               name="karsilasma_ozeti_tek")]

    def __str__(self):
        return f"{self.gun} · {self.mode} · b{self.basamak_once} · {self.verdict}: {self.sayi}"
