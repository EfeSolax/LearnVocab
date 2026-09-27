"""
Kart üretimi — kelime modelinden çalışma kartlarına.

Bu dosya "hangi kartlar var olmalı" sorusunun tek cevabıdır. Soru
üretmez (bkz. questions.py), zamanlama yapmaz (bkz. scheduler.py);
yalnızca ReviewItem satırlarının doğru zamanda ortaya çıkmasını sağlar.

İKİ TETİKLEYİCİ
---------------
1. `ensure_entry_items` — kullanıcı bir kelimeyi listesine eklediğinde
   ya da çalışmaya başladığında, o kelimenin GİRİŞ kartlarını açar.
2. `unlock_after_review` — bir kart yeterince kararlı hâle geldiğinde
   üstündeki kademeyi açar.

İkincisi olmadan sistem sonsuza kadar tanıma sorardı. Birincisi olmadan
hiç başlamazdı.

KART SAYISI NEDEN SINIRLI
-------------------------
Zengin bir kelimenin 6 eş dizimi, 4 kalıbı, 5 örnek cümlesi olabiliyor.
Hepsinden kart açılsa tek bir kelime 20 karta dönüşür ve günlük yük
öğrenciyi boğar. Üstelik faydası da yoktur: `make a decision` ile
`reach a decision` aynı bilginin iki örneğidir, ikisini ayrı ayrı
zamanlamak ezberi değil yorgunluğu artırır.

Bu yüzden her boyut için kelime başına üst sınır var (bkz. LIMITS) ve
sıralamada `sort_order` öndekiler seçiliyor — zenginleştirme hattı
zaten en yaygın olanı başa koyuyor.
"""

from django.db.models import Q

from words.models import (
    Collocation, FalseFriend, Meaning, PartOfSpeech, RelationType,
    Sentiment, UsagePattern, Word, WordRelation,
)

from . import aspects
from .aspects import Aspect
from .models import ItemState, ReviewItem


# Bir kelime için boyut başına açılacak en fazla kart sayısı.
LIMITS = {
    Aspect.COLLOCATION: 3,
    Aspect.PATTERN: 2,
    Aspect.FALSE_FRIEND: 2,
    Aspect.CONFUSABLE: 2,
}

# Bir kelimenin kaç anlamı için kart açılacağı. Çok anlamlı kelimelerde
# ilk anlamlar en yaygın olanlar; altıncı anlamı çalışmak hazırlık
# öğrencisinin işi değil.
MAX_MEANINGS = 3


def user_words(user):
    """Kullanıcının listesindeki kelimeler."""
    return (Word.objects
            .filter(Q(owner=user) | Q(saved_by=user))
            .distinct())


# ----------------------------------------------------------------------
# Kart açma
# ----------------------------------------------------------------------

def _create(user, word, aspect, meaning=None, target_id=0):
    """Kart yoksa açar, varsa dokunmaz. (kart, yeni_mi) döner."""
    if meaning is not None:
        item, created = ReviewItem.objects.get_or_create(
            user=user, meaning=meaning, aspect=aspect, target_id=target_id,
            defaults={"word": word},
        )
    else:
        item, created = ReviewItem.objects.get_or_create(
            user=user, word=word, aspect=aspect, target_id=target_id,
            meaning=None,
        )
    return item, created


def ensure_entry_items(user, word) -> int:
    """
    Bir kelimenin giriş kartlarını açar: tanıma + ayırt etme boyutları.

    Ayırt etme boyutlarının (yanlış dost, karıştırılan çift, ton) burada
    açılmasının sebebi aspects.py'da anlatılıyor: bunlar öğrenmeyi
    ilerletmiyor, hatayı önlüyor ve geç kalmaları pahalıya mal oluyor.

    Yeni açılan kart sayısını döner.
    """
    acilan = 0
    anlamlar = list(word.meanings.all()[:MAX_MEANINGS])

    for anlam in anlamlar:
        _, yeni = _create(user, word, Aspect.RECOGNIZE, meaning=anlam)
        acilan += int(yeni)

        # Ton kartı yalnızca TONU nötr olmayan anlamlarda açılıyor.
        #
        # `is_marked` (ton VEYA üslup nötr değil) ilk denemede kullanıldı ve
        # gerçek veride şu çıktı: 198 anlamın 51'i "akademik" üsluplu, ton
        # farkı olan ise 51 tane. Üslubu sormak akademik kelime yığınında
        # neredeyse hep aynı cevabı veriyor — öğrenci kelimeyi bilmeden de
        # "akademik" diyerek tutturur, kart hiçbir şey öğretmez.
        #
        # Ton öyle değil: `notorious` ile `famous` sözlükte aynı, tonda zıt
        # ve bu fark Türkçe karşılıkta tamamen kayboluyor. Üslup bilgisi de
        # değerli ama sorulacak değil GÖSTERİLECEK bir bilgi — kelime
        # detayında ve üretim sorusunun geri bildiriminde yerini alıyor.
        if anlam.sentiment != Sentiment.NEUTRAL:
            _, yeni = _create(user, word, Aspect.NUANCE, meaning=anlam)
            acilan += int(yeni)

    # Yanlış dostlar kelime düzeyinde.
    for yanlis_dost in word.false_friends.all()[:LIMITS[Aspect.FALSE_FRIEND]]:
        _, yeni = _create(user, word, Aspect.FALSE_FRIEND,
                          target_id=yanlis_dost.id)
        acilan += int(yeni)

    # Karıştırılan çiftler de kelime düzeyinde.
    baglar = (WordRelation.objects
              .filter(from_word=word, type=RelationType.CONFUSED_WITH)
              .select_related("to_word")[:LIMITS[Aspect.CONFUSABLE]])
    for bag in baglar:
        _, yeni = _create(user, word, Aspect.CONFUSABLE, target_id=bag.id)
        acilan += int(yeni)

    return acilan


def ensure_all_entry_items(user) -> int:
    """Kullanıcının bütün kelimeleri için giriş kartlarını tamamlar."""
    toplam = 0
    kelimeler = (user_words(user)
                 .prefetch_related("meanings", "false_friends"))
    for kelime in kelimeler:
        toplam += ensure_entry_items(user, kelime)
    return toplam


# ----------------------------------------------------------------------
# Kademe açma
# ----------------------------------------------------------------------

def _unlock_production(user, word, meaning) -> int:
    """Kademe 2: üretim ve çekim."""
    acilan = 0

    _, yeni = _create(user, word, Aspect.PRODUCE, meaning=meaning)
    acilan += int(yeni)

    # Çekim kartı yalnızca DÜZENSİZ fiillerde açılıyor. Düzensiz olup
    # olmadığını anlamanın yolu inflect.py'ın kuralla ürettiği biçimle
    # kayıtlı biçimi karşılaştırmak: kural zaten doğruyu veriyorsa
    # ezberlenecek bir şey yok, kart açmak boş yere yük olur.
    if word.pos in (PartOfSpeech.VERB, PartOfSpeech.PHRASAL_VERB) and word.v2Form:
        if _duzensiz_mi(word):
            _, yeni = _create(user, word, Aspect.FORM)
            acilan += int(yeni)

    return acilan


def _duzensiz_mi(word) -> bool:
    """
    Fiilin 2. hâli kuralla üretilenden farklı mı?

    Düzenli fiilde ezberlenecek bir şey yok: `walk -> walked` kuraldan
    çıkıyor. Kart yalnızca kuralın yanıldığı yerde (go -> went) açılıyor.
    Aksi hâlde her fiil bir çekim kartı üretir ve öğrenci zaten bildiği
    bir kuralı yüzlerce kez tekrar eder.
    """
    try:
        from words import inflect
    except ImportError:  # pragma: no cover
        return True

    try:
        kural_bicimleri = inflect.verb_forms(word.text)
    except Exception:  # pragma: no cover
        return True

    kurall = next((bicim for bicim, tur in kural_bicimleri if tur == "past"), None)
    if kurall is None:
        return True
    return kurall.lower() != (word.v2Form or "").lower()


def _unlock_use(user, word, meaning) -> int:
    """Kademe 3: bağlam, eş dizim, kalıp, aile."""
    acilan = 0

    # Bağlam kartı örnek cümle gerektirir.
    if meaning.examples.exists():
        _, yeni = _create(user, word, Aspect.CONTEXT, meaning=meaning)
        acilan += int(yeni)

    # Eş dizim: yalnızca ÖRNEK CÜMLESİ OLANLAR kart olur. Örneksiz bir
    # eş dizimden boşluk sorusu üretilemez ve çoktan seçmelide bağlamsız
    # kalır — öğrenci neyi seçtiğini anlamadan seçer.
    esdizimler = (meaning.collocations
                  .exclude(example__isnull=True).exclude(example="")
                  [:LIMITS[Aspect.COLLOCATION]])
    for esdizim in esdizimler:
        _, yeni = _create(user, word, Aspect.COLLOCATION, meaning=meaning,
                          target_id=esdizim.id)
        acilan += int(yeni)

    kaliplar = (meaning.patterns
                .exclude(example__isnull=True).exclude(example="")
                [:LIMITS[Aspect.PATTERN]])
    for kalip in kaliplar:
        _, yeni = _create(user, word, Aspect.PATTERN, meaning=meaning,
                          target_id=kalip.id)
        acilan += int(yeni)

    # Aile kartı AİLE BAŞINA bir tane.
    #
    # İlk sürümde her kelimeye ayrı bir aile kartı açılıyordu ve gerçek
    # veride şu oldu: `acquire`, `acquisitive` ve `acquisition`
    # kartlarının üçü de aynı cümleyi sorabiliyordu. Öğrenmenin birimi
    # burada tek kelime değil ailenin kendisi — "bu cümleye hangi türev
    # girer" sorusu ailede bir kez sorulur, üç kez değil.
    if word.family_id and word.family.words.count() >= 2:
        aile_karti_var = ReviewItem.objects.filter(
            user=user, aspect=Aspect.FAMILY, word__family_id=word.family_id
        ).exists()
        if not aile_karti_var:
            _, yeni = _create(user, word, Aspect.FAMILY)
            acilan += int(yeni)

    return acilan


def unlock_after_review(item) -> int:
    """
    Bir kart cevaplandıktan sonra üst kademeyi açmayı dener.

    Eşik KARARLILIK üzerinden, doğru cevap sayısı üzerinden değil.
    "Üç kez doğru bildi" bir şey söylemez — aynı oturumda üç kez
    bilmiş olabilir. Kararlılık zamanı hesaba katar: 3 gün kararlılık,
    kelimenin üç gün sonra da bilineceği anlamına gelir.
    """
    if item.stability is None:
        return 0

    user, word, meaning = item.user, item.word, item.meaning

    if (item.aspect == Aspect.RECOGNIZE
            and item.stability >= aspects.UNLOCK_PRODUCTION_STABILITY
            and meaning is not None):
        return _unlock_production(user, word, meaning)

    if (item.aspect == Aspect.PRODUCE
            and item.stability >= aspects.UNLOCK_USE_STABILITY
            and meaning is not None):
        return _unlock_use(user, word, meaning)

    return 0


# ----------------------------------------------------------------------
# Durum özeti
# ----------------------------------------------------------------------

def aspect_breakdown(user):
    """
    Kullanıcının kartlarının boyuta göre dağılımı — ilerleme sayfası için.

    "Kaç kelime biliyorum" sorusuna tek sayıyla cevap vermek yanıltıcı;
    bu tablo "tanıdığın 400 kelimenin 90'ını üretebiliyorsun" diyebilmek
    için var.
    """
    ozet = {}
    kayitlar = (ReviewItem.objects.filter(user=user)
                .values_list("aspect", "state", "stability"))
    for aspect, state, stability in kayitlar:
        satir = ozet.setdefault(aspect, {
            "aspect": aspect,
            "label": Aspect(aspect).label,
            "total": 0, "new": 0, "learning": 0, "mature": 0,
        })
        satir["total"] += 1
        if state == ItemState.NEW:
            satir["new"] += 1
        elif stability is not None and stability >= 21:
            # 21 gün: Anki'nin "olgun kart" eşiği. Üç haftalık kararlılık,
            # kelimenin dönem sonunda hâlâ bilineceğinin makul göstergesi.
            satir["mature"] += 1
        else:
            satir["learning"] += 1
    return ozet
