"""
Cümlede kelime maskeleme ve cevap karşılaştırma.

Boşluk doldurma sorularının tamamı buradan geçiyor. İşin göründüğünden
zor olmasının sebebi şu: sözlükte `retain` yazar, cümlede `retained`
geçer. Birebir arayan bir maskeleyici cümlelerin yarısında kelimeyi
bulamaz ve o cümleler sessizce kullanılamaz hâle gelir.

ÇÖZÜM HAZIRDI
-------------
Bu problem projede zaten çözülmüş: `WordForm` tablosu tam olarak
"metinde karşılaşılan yazımdan sözlük maddesine köprü" olmak için var
ve zenginleştirme hattı her kelime için bütün yüzey biçimlerini oraya
yazıyor (ortalama kelime başına iki buçuk biçim). Yani maskeleyicinin
kendi çekim kuralları yazmasına gerek yok — veritabanına sorması yeter.

Kural üretmek yerine veriye bakmanın ikinci faydası: düzensiz fiiller
(go/went/gone) ve düzensiz çoğullar da bedavaya doğru çalışıyor.
"""

import re
import unicodedata

BLANK = "____"

# Cevap karşılaştırmasında yok sayılan yer tutucular.
YER_TUTUCULAR = {"sb", "sth", "smb", "smth", "somebody", "something",
                 "someone", "one's", "sb's", "sth's"}

# Cevabın başından ve sonundan atılan işaretler.
KIRPILAN = " \t\n.,!?;:'\"()[]"


def normalize(metin: str) -> str:
    """Karşılaştırma için sadeleştirilmiş biçim."""
    metin = (metin or "").strip().lower().strip(KIRPILAN)
    # Türkçe klavyeden gelen kıvrık kesme işaretleri düz hâle getiriliyor.
    metin = metin.replace("’", "'").replace("‘", "'")
    metin = unicodedata.normalize("NFKC", metin)
    return re.sub(r"\s+", " ", metin)


def surfaces_for_word(word) -> list[str]:
    """
    Bir kelimenin cümlede görünebileceği bütün yazımları.

    Sıra UZUNDAN KISAYA. Bunun sebebi maskelemede: `run` ve `running`
    aynı cümlede aranıyorsa ve önce `run` denenirse, `running`in içindeki
    `run`a takılma riski var. Kelime sınırı (\\b) çoğu durumu kurtarıyor
    ama phrasal verb'lerde ("run into") sınır yetmiyor.
    """
    yazimlar = {(word.text or "").lower()}
    for alan in ("v2Form", "v3Form"):
        deger = getattr(word, alan, None)
        if deger:
            yazimlar.add(deger.lower())
    try:
        for bicim in word.forms.all():
            if bicim.surface:
                yazimlar.add(bicim.surface.lower())
    except Exception:  # pragma: no cover — kelime henüz kaydedilmemişse
        pass
    return sorted((y for y in yazimlar if y), key=len, reverse=True)


def _kelime_deseni(yazim: str) -> str:
    """
    Bir yazımı cümlede arayan desen.

    Çok kelimeli maddelerde (phrasal verb) aradaki boşluk esnetiliyor:
    "carry out" cümlede "carry it out" olarak geçebilir.
    """
    parcalar = [p for p in re.split(r"\s+", yazim.strip()) if p]
    if len(parcalar) <= 1:
        return r"\b" + re.escape(yazim) + r"\b"
    # Araya en fazla iki kelime girebilir.
    ara = r"(?:\s+\S+){0,2}\s+"
    return r"\b" + ara.join(re.escape(p) for p in parcalar) + r"\b"


def blank_word(sentence: str, surfaces: list[str], blank: str = BLANK):
    """
    Cümlede verilen yazımlardan ilk bulunanı boşlukla değiştirir.

    (maskelenmiş_cümle, bulunan_yazım) döner; hiçbiri bulunamazsa
    (None, None). Çağıran taraf None gelirse o cümleyi KULLANMAZ —
    yanlış maskelenmiş bir soru sormaktansa soru sormamak iyidir.
    """
    if not sentence:
        return None, None

    for yazim in surfaces:
        desen = re.compile(_kelime_deseni(yazim), re.IGNORECASE)
        eslesme = desen.search(sentence)
        if eslesme:
            maskeli = sentence[:eslesme.start()] + blank + sentence[eslesme.end():]
            return maskeli, eslesme.group(0)
    return None, None


def blank_token(sentence: str, token: str, blank: str = BLANK):
    """
    Cümlede tek bir kelimeyi (edat, artikel, yardımcı fiil) maskeler.

    Kalıp sorularında kullanılıyor: `depend on sth` kalıbının örnek
    cümlesinde maskelenmesi gereken şey kelimenin kendisi değil, EDAT.
    """
    if not sentence or not token:
        return None, None
    desen = re.compile(r"\b" + re.escape(token.strip()) + r"\b", re.IGNORECASE)
    eslesme = desen.search(sentence)
    if not eslesme:
        return None, None
    maskeli = sentence[:eslesme.start()] + blank + sentence[eslesme.end():]
    return maskeli, eslesme.group(0)


def pattern_tokens(pattern: str) -> list[str]:
    """
    Bir kalıptan ya da eş dizimden anlamlı kelimeleri çıkarır.

    Yer tutucular (sth, sb) atılıyor: onlar kalıbın parçası değil,
    kalıbın nereye ne geleceğini anlatan not.
    """
    parcalar = [p for p in re.split(r"[^\w'-]+", (pattern or "").lower()) if p]
    return [p for p in parcalar if p not in YER_TUTUCULAR]


def answer_matches(user_input: str, accepted: list[str]) -> bool:
    """
    Yazılan cevap kabul edilenlerden birine uyuyor mu?

    YAZIM TOLERANSI YOK — bilerek.

    Eski sistemde `WritingQuestion` %80 benzerlik kabul ediyordu. Kelime
    öğrenmede bu ayar ters çalışıyor: `retain` ile `retail` arasındaki
    benzerlik %83, yani gerçek bir yazım hatasıyla tamamen farklı bir
    kelime aynı eşiğin içinde kalıyor. Tolerans, yazım hatasını affetmek
    yerine yanlış kelimeyi doğru saymaya yarıyordu.

    Tolerans yerine KABUL LİSTESİ genişletiliyor ve bu listeyi çağıran
    taraf kuruyor (bkz. questions.py): kelimenin bütün yüzey biçimleri
    kabul edilir. Yani `retained` beklenirken `retain` yazan öğrenci
    doğru sayılır — kelimeyi biliyor, cümlenin zamanını kaçırmış; geri
    bildirimde cümledeki doğru biçim gösteriliyor. Ama `retail` yanlıştır,
    çünkü listede yok. Karar kelimenin kendisinde veriliyor, harf
    benzerliğinde değil.
    """
    girdi = normalize(user_input)
    if not girdi:
        return False

    girdi_kume = {k for k in re.split(r"\W+", girdi) if k and k not in YER_TUTUCULAR}

    for dogru in accepted:
        hedef = normalize(dogru)
        if girdi == hedef:
            return True
        hedef_kume = {k for k in re.split(r"\W+", hedef)
                      if k and k not in YER_TUTUCULAR}
        # Yer tutucular atıldıktan sonra aynı kelimeler kaldıysa doğru.
        if hedef_kume and girdi_kume == hedef_kume:
            return True
    return False


def highlight(sentence: str, surfaces: list[str]) -> str:
    """
    Geri bildirimde kelimeyi cümle içinde işaretler (<mark> ile).

    Geri bildirim ekranında doğru cevabı sadece söylemek yetmiyor;
    kelimenin cümle içinde NEREDE durduğunu görmek, o cümleyi hafızada
    kelimeye bağlayan şey.
    """
    if not sentence:
        return ""
    for yazim in surfaces:
        desen = re.compile(_kelime_deseni(yazim), re.IGNORECASE)
        eslesme = desen.search(sentence)
        if eslesme:
            return (sentence[:eslesme.start()]
                    + "<mark>" + eslesme.group(0) + "</mark>"
                    + sentence[eslesme.end():])
    return sentence
