"""
Öğrenme boyutları — bir kelimeyi "bilmek"in kaç ayrı parçası var.

BU DOSYA NEDEN VAR
------------------
Eski sistemde öğrenmenin birimi kelimeydi: `UserWordLink.correctCount`
tek bir sayaçtı ve "bu kelimeyi biliyor mu" sorusuna tek bir cevap
veriyordu. Ama "bilmek" tek bir şey değil. Öğrenci:

    sustain  -> "sürdürmek"        bunu TANIYABİLİR,
    "sürdürmek" -> sustain         ama bunu ÜRETEMEZ,
    sustain injuries               ve bunu hiç duymamıştır,
    sustained / sustaining         çekimini bilmiyordur,
    sustain ≠ "sustain etmek"      ve Türkçeye benzediği için yanılıyordur.

Bunlar aynı kelimeye ait BEŞ AYRI BİLGİDİR ve farklı hızlarda öğrenilir,
farklı hızlarda unutulur. Tek sayaçla takip edilirse hiçbiri düzgün
zamanlanamaz: tanıma kolay olduğu için sayaç şişer, sistem kelimeyi
"öğrenildi" sayar, öğrenci onu essay'de kullanamaz.

Bu yüzden zamanlamanın birimi kelime değil, (kelime × boyut) çiftidir.
Her boyutun kendi kararlılığı, kendi zorluğu, kendi tekrar günü var.

MERDİVEN — HEPSİ AYNI ANDA AÇILMAZ
----------------------------------
Bütün boyutları ilk günden açmak iki şeyi bozardı: günlük yük beş katına
çıkardı ve öğrenciden tanımadığı kelimeyi üretmesi istenirdi. Üretim,
tanımanın üstüne kurulur (alıcı bilgi -> üretici bilgi sırası).

Bu yüzden boyutlar KADEMELİ açılıyor:

  Kademe 1  tanıma            her zaman açık
  Kademe 2  üretim, çekim     tanıma kararlılığı ~3 günü geçince
  Kademe 3  bağlam, eş dizim, aile, kalıp    üretim kararlılığı ~7 günü geçince

Ayırt etme boyutları (yanlış dost, karıştırılan çift, ton/üslup) bu
merdivene GİRMEZ; veri varsa ve kelime bir kez doğru tanınmışsa hemen
açılır. Sebebi: bunlar öğrenmeyi ilerletmiyor, HATAYI ÖNLÜYOR. `sensible`i
"hassas" sanan öğrencinin bunu geç öğrenmesi, hiç öğrenmemesinden çok da
iyi değil — yanlış kullanım bir kez yerleşince sökülmesi zorlaşıyor.

BİÇİM DEĞİŞKENLİĞİ
------------------
Boyut NE sorulduğunu söyler, biçim NASIL sorulduğunu. Aynı boyut her
tekrarda aynı biçimde sorulmaz: bir sefer çoktan seçmeli, bir sefer
yazarak, bir sefer cümle içinde. Bunun sebebi zenginlik değil, hafıza:
aynı bilgiye farklı yollardan ulaşmak o bilgiye giden yol sayısını
artırır (kodlama değişkenliği). Tek biçimde çalışılan kelime o biçimin
ipuçlarına bağlanır ve şık görmediği anda erişilemez hâle gelir.
"""

from django.db import models


class Aspect(models.TextChoices):
    """Bir kelimenin öğrenilebilir boyutları."""

    RECOGNIZE = "recognize", "anlamını tanıma"
    PRODUCE = "produce", "kelimeyi üretme"
    CONTEXT = "context", "bağlamda kullanma"
    COLLOCATION = "collocation", "eş dizim"
    PATTERN = "pattern", "kalıp ve edat"
    FALSE_FRIEND = "false_friend", "yanlış dost"
    CONFUSABLE = "confusable", "karıştırılan çift"
    NUANCE = "nuance", "ton ve üslup"
    FAMILY = "family", "kelime ailesi"
    FORM = "form", "çekim biçimi"


class Format(models.TextChoices):
    """Bir boyutun sorulabileceği biçimler."""

    CHOICE = "choice", "çoktan seçmeli"
    CHOICE_CONTEXT = "choice_context", "cümleyle çoktan seçmeli"
    TYPE = "type", "yazarak"
    BLANK = "blank", "boşluk doldurma"
    PAIR = "pair", "ikili ayrım"
    TRUE_FALSE = "true_false", "doğru / yanlış"


# Kademeler
STAGE_ENTRY = 1        # tanıma
STAGE_PRODUCTION = 2   # üretim
STAGE_USE = 3          # kullanım
STAGE_GUARD = 0        # ayırt etme — merdivene girmez, veri varsa açılır


# Kademe açılma eşikleri (gün cinsinden kararlılık).
# Kararlılık "hatırlama olasılığının %90'a düştüğü süre" olduğu için
# 3 gün, kelimenin üç gün sonra hâlâ bilinmesi demek. Üretim için bu
# yeterli bir taban; 7 gün ise kullanım boyutları için.
UNLOCK_PRODUCTION_STABILITY = 3.0
UNLOCK_USE_STABILITY = 7.0


class AspectInfo:
    """Bir boyutun sabit özellikleri."""

    __slots__ = ("aspect", "stage", "production", "expected_seconds",
                 "formats", "weight", "explanation")

    def __init__(self, aspect, stage, production, expected_seconds,
                 formats, weight, explanation):
        self.aspect = aspect
        self.stage = stage
        # production: öğrenci İngilizce biçimi kendisi mi üretiyor?
        # Not üretiminde (scheduler.not_uret) KOLAY notu yalnızca üretim
        # sorularında verilebiliyor — şık işaretlemenin hızı bilgi değildir.
        self.production = production
        # expected_seconds: "normal" cevap süresi. Notu buna göre üretiyoruz;
        # mutlak bir ölçü değil, oran için bir ölçek.
        self.expected_seconds = expected_seconds
        self.formats = formats
        # weight: oturum kuyruğu doldurulurken göreli ağırlık.
        self.weight = weight
        self.explanation = explanation


ASPECTS = {
    Aspect.RECOGNIZE: AspectInfo(
        Aspect.RECOGNIZE, STAGE_ENTRY, False, 8.0,
        (Format.CHOICE, Format.CHOICE_CONTEXT), 10,
        "İngilizce kelimeyi görüp Türkçe anlamını bilmek. Her şeyin girişi. "
        "İkinci biçimde kelime bir cümlenin içinde gösteriliyor: çok anlamlı "
        "kelimelerde (bank) doğru anlamı ancak bağlam seçtirir.",
    ),
    Aspect.PRODUCE: AspectInfo(
        Aspect.PRODUCE, STAGE_PRODUCTION, True, 12.0,
        (Format.TYPE, Format.CHOICE), 10,
        "Türkçe anlamdan İngilizce kelimeyi üretmek. Asıl zor yön budur ve "
        "essay yazarken kullanılan yön de budur.",
    ),
    Aspect.CONTEXT: AspectInfo(
        Aspect.CONTEXT, STAGE_USE, True, 18.0,
        (Format.BLANK,), 8,
        "Kelimeyi gerçek bir cümlenin boşluğuna yerleştirmek. Anlamı "
        "bilmekle cümlede kullanabilmek arasındaki farkı ölçer.",
    ),
    Aspect.COLLOCATION: AspectInfo(
        Aspect.COLLOCATION, STAGE_USE, True, 15.0,
        (Format.BLANK, Format.CHOICE), 7,
        "make a decision / do a decision ayrımı. Türkçeden çeviren öğrencinin "
        "en çok hata yaptığı yer.",
    ),
    Aspect.PATTERN: AspectInfo(
        Aspect.PATTERN, STAGE_USE, True, 12.0,
        (Format.BLANK, Format.CHOICE), 7,
        "depend ON, suggest DOING, decide TO DO. Kelime seçimi değil gramer; "
        "sınavda en çok puan kaybedilen yer.",
    ),
    Aspect.FALSE_FRIEND: AspectInfo(
        Aspect.FALSE_FRIEND, STAGE_GUARD, False, 12.0,
        (Format.TRUE_FALSE, Format.CHOICE), 6,
        "sympathetic 'sempatik' değildir. Türkçe konuşanın sistematik hatası; "
        "veri olarak tutulabildiği için önlenebilir.",
    ),
    Aspect.CONFUSABLE: AspectInfo(
        Aspect.CONFUSABLE, STAGE_GUARD, False, 14.0,
        (Format.PAIR,), 6,
        "affect / effect, principle / principal. İki kelime yan yana "
        "sorulur — ayrı ayrı sorulduğunda ayrım öğrenilmiyor.",
    ),
    Aspect.NUANCE: AspectInfo(
        Aspect.NUANCE, STAGE_GUARD, False, 10.0,
        (Format.CHOICE,), 4,
        "notorious ile famous sözlükte aynı, kullanımda zıt. Türkçe karşılık "
        "bu bilgiyi siliyor; ton ve üslup alanları onu geri getiriyor.",
    ),
    Aspect.FAMILY: AspectInfo(
        Aspect.FAMILY, STAGE_USE, True, 15.0,
        (Format.BLANK, Format.CHOICE), 5,
        "Cümleye ailenin hangi üyesi giriyor: analyse mi analysis mi? "
        "Kelime ailesi bilgisinin tek gerçek sınavı.",
    ),
    Aspect.FORM: AspectInfo(
        Aspect.FORM, STAGE_PRODUCTION, True, 10.0,
        (Format.TYPE, Format.CHOICE), 4,
        "Düzensiz fiilin 2. ve 3. hâli. Kural üretemediği için ezberlenmesi "
        "gereken, sayısı sınırlı bir küme.",
    ),
}


# Oturumda aynı kelimenin iki boyutunun arka arkaya gelmemesi için
# kullanılan en küçük mesafe (araya girmesi gereken soru sayısı).
AYNI_KELIME_MESAFESI = 3


def info(aspect) -> AspectInfo:
    return ASPECTS[aspect]


def is_production(aspect) -> bool:
    return ASPECTS[aspect].production


def expected_seconds(aspect) -> float:
    return ASPECTS[aspect].expected_seconds


def stage_of(aspect) -> int:
    return ASPECTS[aspect].stage


def guard_aspects():
    """Merdivene girmeyen, veri varsa hemen açılan ayırt etme boyutları."""
    return tuple(a for a, bilgi in ASPECTS.items() if bilgi.stage == STAGE_GUARD)


def aspects_for_stage(stage):
    return tuple(a for a, bilgi in ASPECTS.items() if bilgi.stage == stage)


def format_for_rep(aspect, rep_count: int):
    """
    Bu tekrarda hangi biçimde sorulsun?

    Biçimler sırayla dönüyor. Rastgele seçmek yerine sıra kullanılmasının
    sebebi: rastgelelik kısa vadede aynı biçimi üst üste verebiliyor ve
    biçim değişkenliğinin bütün faydası tam olarak bunu önlemekte.

    İlk tekrar her zaman listenin ilk biçimidir; boyut tanımlarında ilk
    biçim en kolay olan seçildi (yeni kartta önce tanıma, sonra üretim).
    """
    bicimler = ASPECTS[aspect].formats
    if not bicimler:
        return Format.CHOICE
    return bicimler[rep_count % len(bicimler)]
