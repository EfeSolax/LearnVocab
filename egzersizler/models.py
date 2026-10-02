"""
Egzersiz modelleri.

  EgzersizOturumu     bir tur: sorular + verilen cevaplar SUNUCUDA durur.
                      Sayfa yenilense, sekme kapansa bile kaldığı yerden
                      devam edilir (rapor 6.2).
  EgzersizCevabi      her cevabın kelime başına kaydı. Listem'in
                      "Zorlandıklarım" filtresi buradan beslenir (kayit.py).
  BaglacCumlesi       D2: bağlaç/ifade cümle havuzu (yükleme komutu:
                      baglac_havuzu_yukle). Havuz boşken bu soru tipi
                      "yakında" görünür, karışık turda atlanır.
  EsdizimCeldiricisi  D3: hafif fiilli eş dizimlerde (make/take/do/give/have)
                      çeldiricinin "gerçekten yanlış" olduğunun doğrulama
                      kaydı (komut: esdizim_celdiricileri). Doğrulanmamış
                      çeldirici HİÇBİR ZAMAN soruya girmez.
"""

from django.db import models

from users.models import User
from words.models import CEFR_CHOICES, Collocation, Expression, Word


class EgzersizOturumu(models.Model):
    TUR_HIZLI = "hizli"
    TUR_TEMPOLU = "tempolu"
    TURLER = [(TUR_HIZLI, "Kısa Sınav"), (TUR_TEMPOLU, "Deneme Sınavı")]   # adlar: Efe, 2 Ekim

    DURUM_DEVAM = "devam"
    DURUM_BITTI = "bitti"
    DURUM_BIRAKILDI = "birakildi"
    DURUMLAR = [(DURUM_DEVAM, "devam ediyor"), (DURUM_BITTI, "bitti"),
                (DURUM_BIRAKILDI, "bırakıldı")]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="egzersiz_oturumlari")
    tur = models.CharField(max_length=10, choices=TURLER)
    # Tempolu'da seçilen tip ("karisik" ya da tek bir tip anahtarı); Hızlı'da "anlam".
    tip = models.CharField(max_length=20, default="karisik")
    # İstenen soru sayısı ("Yeni tur" aynı ayarla başlasın diye saklanıyor).
    istenen = models.PositiveSmallIntegerField(default=10)

    # Soru sözlüklerinin listesi (biçim: sorular.py başındaki açıklama).
    sorular = models.JSONField(default=list)
    # Soruyla aynı sırada: {"secim": ..., "dogru_mu": bool}. Cevaplanmamış soru yok.
    cevaplar = models.JSONField(default=list)
    # Ekrandaki sorunun sırası (0'dan). Cevap verilince DEĞİŞMEZ; "Devam" ile artar.
    sira = models.PositiveSmallIntegerField(default=0)
    durum = models.CharField(max_length=10, choices=DURUMLAR, default=DURUM_DEVAM)

    # "Yanlışları tekrar çöz" ile açıldıysa kaynağı.
    kaynak = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="tekrarlar")

    olusturma = models.DateTimeField(auto_now_add=True)
    guncelleme = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-olusturma",)
        verbose_name = "egzersiz oturumu"
        verbose_name_plural = "egzersiz oturumları"

    def __str__(self):
        return f"{self.user} · {self.get_tur_display()} · {len(self.sorular)} soru"

    @property
    def soru_sayisi(self):
        return len(self.sorular)

    @property
    def dogru_sayisi(self):
        return sum(1 for c in self.cevaplar if c and c.get("dogru_mu"))

    @property
    def bitti_mi(self):
        return self.durum == self.DURUM_BITTI

    def cevaplandi_mi(self, i):
        return i < len(self.cevaplar) and bool(self.cevaplar[i])


class EgzersizCevabi(models.Model):
    """
    Bir cevabın KELİME BAŞINA kaydı (eşleştirmede her çift ayrı satır).
    Kelimesi olmayan sorular (bağlaç) kelimesiz kaydedilir.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="egzersiz_cevaplari")
    word = models.ForeignKey(Word, on_delete=models.CASCADE, null=True, blank=True,
                             related_name="egzersiz_cevaplari")
    oturum = models.ForeignKey(EgzersizOturumu, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="cevap_kayitlari")
    soru_tipi = models.CharField(max_length=20)
    dogru = models.BooleanField()
    tarih = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-tarih",)
        indexes = [models.Index(fields=["user", "dogru", "tarih"])]
        verbose_name = "egzersiz cevabı"
        verbose_name_plural = "egzersiz cevapları"

    def __str__(self):
        return f"{self.user} · {self.word or '-'} · {'doğru' if self.dogru else 'yanlış'}"


class BaglacCumlesi(models.Model):
    """
    D2 — bağlaç/ifade sorusu: boşluklu cümle + tek doğru + 3 çeldirici.

    Şıklardan YALNIZCA biri anlamı doğru verir (rapor 6.2); noktalama
    inceliği sorulmaz. Yapay zekâyla üretilip denetlenecek; yalnızca
    `denetlendi=True` olan satırlar soruya girer.
    """

    BOSLUK = "___"

    cumle = models.CharField(max_length=400)          # "It rained. ___, we went out."
    dogru = models.CharField(max_length=80)           # "However"
    celdiriciler = models.JSONField(default=list)     # ["Therefore", "For example", "Similarly"]
    aciklama = models.CharField(max_length=200, blank=True)   # tek satır, Türkçe
    cefr = models.CharField(max_length=15, choices=CEFR_CHOICES, default="B1")
    ifade = models.ForeignKey(Expression, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name="baglac_cumleleri")
    denetlendi = models.BooleanField(default=False)
    kaynak = models.CharField(max_length=80, blank=True)      # üreten model / kişi
    olusturma = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cumle", "dogru")
        verbose_name = "bağlaç cümlesi (D2)"
        verbose_name_plural = "bağlaç cümleleri (D2)"

    def __str__(self):
        return self.cumle[:60]


class EsdizimCeldiricisi(models.Model):
    """
    D3 — hafif fiilli eş dizimde bir çeldiricinin doğrulama kaydı.

    "make a mistake" için "do" çeldiricisi: yapay zekâ "do a mistake
    gerçekten yanlış mı?" sorusuna evet derse gercekten_yanlis=True olur.
    None = henüz doğrulanmadı, False = aslında kabul edilebilir (ör. İngiliz
    İngilizcesinde "take a decision") -> ASLA çeldirici olmaz.
    """

    collocation = models.ForeignKey(Collocation, on_delete=models.CASCADE,
                                    related_name="celdiriciler")
    celdirici = models.CharField(max_length=30)       # "do"
    gercekten_yanlis = models.BooleanField(null=True, blank=True)
    kaynak = models.CharField(max_length=80, blank=True)     # doğrulayan model
    not_metni = models.CharField(max_length=300, blank=True)
    dogrulama_tarihi = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("collocation", "celdirici")
        verbose_name = "eş dizim çeldiricisi (D3)"
        verbose_name_plural = "eş dizim çeldiricileri (D3)"

    def __str__(self):
        durum = {True: "doğrulandı", False: "reddedildi", None: "bekliyor"}[self.gercekten_yanlis]
        return f"{self.collocation.pattern} ✗ {self.celdirici} ({durum})"
