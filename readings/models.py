"""
Okuma metinleri.

Metinlerin kaynağı proje kökündeki reading-texts/ klasöründeki düz metin
dosyaları. Veritabanı bir kopya tutuyor; kaynak dosyalar değiştiğinde
`python manage.py import_readings` tekrar çalıştırılıp güncelleniyor.
Metnin kimliği kitaptaki sıra numarası (number) — dosya adı ya da başlık
değişse bile kayıt aynı kalıyor.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User


# Okuma konuları admin'den yönetilir (OkumaKonusu, Efe 17 Ekim). Renk, Tailwind'in derlediği
# renklerden biri olmalı (tailwind.config.js safelist ile aynı liste).
RENKLER = ("indigo", "emerald", "amber", "rose", "sky", "teal", "orange", "lime", "fuchsia", "cyan", "pink")
_KONU_ONBELLEK = "okuma-konulari"


class OkumaKonusu(models.Model):
    """Kütüphanedeki okuma metinlerinin konusu (Hukuk, Psikoloji …). Admin'den eklenir."""

    anahtar = models.SlugField(max_length=20, unique=True,
                               help_text="Adreste ve kayıtta kullanılan kısa ad (ör. ekonomi). Sonradan değiştirme.")
    ad = models.CharField(max_length=60, verbose_name="ad (Türkçe)")
    ad_en = models.CharField(max_length=60, blank=True, verbose_name="ad (İngilizce)")
    ad_de = models.CharField(max_length=60, blank=True, verbose_name="ad (Almanca)")
    renk = models.CharField(max_length=10, choices=[(r, r) for r in RENKLER], default="indigo")
    sira = models.PositiveIntegerField(default=0, help_text="Konu düğmelerinin sırası (küçük önce).")

    class Meta:
        ordering = ("sira", "ad")
        verbose_name = "okuma konusu"
        verbose_name_plural = "okuma konuları"

    def __str__(self):
        return self.ad

    @property
    def yerel_ad(self):
        from django.utils.translation import get_language
        dil = (get_language() or "tr")[:2]
        return (getattr(self, f"ad_{dil}", "") if dil != "tr" else "") or self.ad

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        _konu_onbellegini_sil()

    def delete(self, *args, **kwargs):
        sonuc = super().delete(*args, **kwargs)
        _konu_onbellegini_sil()
        return sonuc


def _konu_onbellegini_sil():
    from django.core.cache import cache
    cache.delete(_KONU_ONBELLEK)


def okuma_konulari():
    """[{anahtar, ad (Türkçe), ad_en, ad_de, renk}] sırasıyla; önbellekte (her metin satırı sorgu açmasın)."""
    from django.core.cache import cache
    konular = cache.get(_KONU_ONBELLEK)
    if konular is None:
        konular = list(OkumaKonusu.objects.values("anahtar", "ad", "ad_en", "ad_de", "renk"))
        cache.set(_KONU_ONBELLEK, konular, 600)
    return konular


def _yerel(konu):
    from django.utils.translation import get_language
    dil = (get_language() or "tr")[:2]
    return (konu.get(f"ad_{dil}") if dil != "tr" else "") or konu["ad"]


def konu_listesi():
    """Sayfadaki konu düğmeleri: [{anahtar, ad (sayfanın dilinde), renk}]."""
    return [{"anahtar": k["anahtar"], "ad": _yerel(k), "renk": k["renk"]} for k in okuma_konulari()]


def konu_adi(anahtar):
    return next((_yerel(k) for k in okuma_konulari() if k["anahtar"] == anahtar), anahtar)


def konu_rengi(anahtar):
    return next((k["renk"] for k in okuma_konulari() if k["anahtar"] == anahtar), "slate")


# Ortalama okuma hızı (kelime/dakika). Yetişkin bir okur ana dilinde ~250,
# yabancı dilde belirgin biçimde daha yavaş okur; hazırlık seviyesi için
# 150 gerçekçi bir tahmin.
WORDS_PER_MINUTE = 150

# Kaynak satırı veritabanında Türkçe yazılı; bilinen kaynaklar sayfanın dilinde gösterilir (rapor 18.22).
KAYNAK_CEVIRILERI = {
    "Örnek metin (LearnVocab, Claude tarafından yazıldı)": _("Örnek metin (LearnVocab, Claude tarafından yazıldı)"),
}


class ReadingText(models.Model):
    """Tek bir okuma parçası."""

    # Kitaptaki sıra numarası. Kaydın kalıcı kimliği bu.
    number = models.PositiveIntegerField(unique=True)

    # OkumaKonusu.anahtar (seçenekler admin formunda tablodan gelir; sütun düz metin kaldı)
    topic = models.CharField(max_length=20, verbose_name="konu")
    title = models.CharField(max_length=200)

    # Paragraflar boş satırla ayrılmış olarak tutuluyor; ayrı bir tablo
    # açmaya değecek bir ihtiyaç yok, sıraları da böyle korunuyor.
    body = models.TextField()

    word_count = models.PositiveIntegerField(default=0)

    # Kütüphane (rapor 8, veri işi D5) için: metnin seviyesi ve kaynağı
    # ("Project Gutenberg", "Yapay zekâ ile üretildi" …). İkisi de boş olabilir;
    # kitaptan gelen ilk 40 metinde yok.
    cefr = models.CharField(max_length=15, blank=True, default="", verbose_name="seviye")
    source = models.CharField(max_length=200, blank=True, default="", verbose_name="kaynak")

    # Kalıcı adres (rapor 18.15): /okumalar/<slug>/. Başlıktan üretilir;
    # aynı başlık ikinci kez gelirse sonuna numara eklenir. Bir kez verilince
    # başlık değişse de değişmez (dizine girmiş adres kaybolmasın).
    slug = models.SlugField(max_length=220, unique=True, blank=True, null=True, editable=False)

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("number",)
        indexes = [models.Index(fields=["topic", "number"])]

    @property
    def yerel_kaynak(self):
        return KAYNAK_CEVIRILERI.get(self.source, self.source)

    def __str__(self):
        return f"{self.number} {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._slug_uret()
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = set(kwargs["update_fields"]) | {"slug"}
        super().save(*args, **kwargs)

    def _slug_uret(self):
        from django.utils.text import slugify
        kok = slugify(self.title)[:200] or f"metin-{self.number}"
        # "metinlerim" kendi metinlerimin adres öneki; başlıkla çakışmasın.
        if kok == "metinlerim" or ReadingText.objects.filter(slug=kok).exclude(pk=self.pk).exists():
            kok = f"{kok}-{self.number}"
        return kok

    @property
    def paragraphs(self):
        """Boş olmayan paragraflar, metindeki sırayla."""
        return paragraflara_bol(self.body)

    @property
    def topic_label(self):
        return konu_adi(self.topic)

    @property
    def topic_color(self):
        return konu_rengi(self.topic)

    @property
    def reading_minutes(self):
        """Kaba okuma süresi; en az 1 dakika."""
        return max(1, round(self.word_count / WORDS_PER_MINUTE))


class ReadingProgress(models.Model):
    """
    Kullanıcının bir metni okuduğu bilgisi.

    Satırın varlığı "okundu" demek; okunmamış metinler için kayıt tutulmuyor.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reading_progress")
    text = models.ForeignKey(ReadingText, on_delete=models.CASCADE, related_name="progress")
    read_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "text")
        indexes = [models.Index(fields=["user", "read_at"])]

    def __str__(self):
        return f"{self.user.username} · {self.text}"


def paragraflara_bol(metin):
    """Boş satırla ayrılmış paragraflar; boş olanlar atılır."""
    return [p.strip() for p in (metin or "").split("\n\n") if p.strip()]


class UserTextQuerySet(models.QuerySet):
    def gorunen(self):
        """Silinmemiş (çöpte olmayan) metinler."""
        return self.filter(deleted_at__isnull=True)


class UserText(models.Model):
    """
    "Kendi metinlerim" (rapor 8): kullanıcının yüklediği PDF'ten çıkarılan
    ya da yapıştırdığı metin. YALNIZCA SAHİBİ görür; telif riski olmaması
    bunun üstüne kurulu.

    PDF dosyasının kendisi saklanmıyor, yalnızca çıkarılan metin: dosyayı
    tutmak gizlilik açısından gereksiz bir yük olurdu.

    Metnin gövdesi VERİTABANINDA DEĞİL, diskte sıkıştırılmış dosyada durur
    (rapor 18.24; readings/depo.py). `body` bir özelliktir: okurken dosya
    açılır, atanınca kaydederken dosyaya yazılır. Satır silinince dosya da
    silinir (readings/sinyaller.py).

    Silme onaysız ve "Geri al"lı (rapor 12.7): önce `deleted_at` dolar
    (yumuşak silme), metin çöp kutusuna gider. Çöpteki metinler bir hafta
    sonra kalıcı olarak temizlenir (bkz. views._copu_bosalt).
    """

    SOURCE_PDF = "pdf"
    SOURCE_PASTE = "paste"
    SOURCE_CHOICES = [(SOURCE_PDF, "PDF"), (SOURCE_PASTE, "Yapıştırma")]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reading_texts")
    title = models.CharField(max_length=200)
    # Gövdenin depodaki dosya adı: "okumalar/<kullanıcı>/<rastgele>.txt.z"
    dosya = models.CharField(max_length=80, blank=True, default="", editable=False)
    source_kind = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    word_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = UserTextQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [models.Index(fields=["owner", "deleted_at", "created_at"])]

    def __str__(self):
        return f"{self.owner_id} · {self.title}"

    # --- gövde: diskteki sıkıştırılmış dosya -----------------------------
    _body = None
    _body_degisti = False

    @property
    def body(self):
        if self._body is None:
            from . import depo
            self._body = depo.oku(self.dosya) if self.dosya else ""
        return self._body

    @body.setter
    def body(self, metin):
        self._body = metin or ""
        self._body_degisti = True

    def save(self, *args, **kwargs):
        if self._body_degisti:
            from . import depo
            if not self.dosya:
                self.dosya = depo.yeni_ad(self.owner_id)
                if kwargs.get("update_fields") is not None:
                    kwargs["update_fields"] = set(kwargs["update_fields"]) | {"dosya"}
            depo.yaz(self.dosya, self._body)
            self._body_degisti = False
        super().save(*args, **kwargs)

    @property
    def paragraphs(self):
        return paragraflara_bol(self.body)

    @property
    def reading_minutes(self):
        return max(1, round(self.word_count / WORDS_PER_MINUTE))
