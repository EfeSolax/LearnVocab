"""
Metinden kelime listesine — süzme hattı.

AMAÇ
----
Elde bir yığın İngilizce metin var. Bunların içinden ÖĞRENİLMEYE DEĞER
kelimeleri çıkarıp zenginleştirme hattının yiyeceği listeye çevirmek
(listeler/*.txt, `aile_uret --file` ile okunuyor).

"Öğrenilmeye değer" üç şeyi birden dışarıda bırakmak demek:

  1. ZATEN BİLİNENLER — en sık N kelime. Hazırlık öğrencisi `people`,
     `important`, `different` bilmiyorsa sorun kelime listesinde değil.
  2. İŞLEV KELİMELERİ — edat, bağlaç, zamir, belirteç. Bunlar kelime
     değil yapı; kelime modeline (aile/anlam/eş dizim/ton) uymuyorlar
     ve Expression hattının konusu.
  3. AŞIRI TEKNİKLER — `mitochondrion`, `heteroscedasticity`. Metinde
     bir kez geçip bir daha görülmeyecek terimler.

Geriye kalan bant: hazırlık öğrencisinin karşılaşacağı ama bilmediği
akademik kelimeler. Phrasal verb'ler bu bandın içinde KALIYOR
(bkz. phrasal.py).

HER ADIM RAPORA YAZILIYOR
-------------------------
Hangi kelimenin neden elendiği tek tek kaydediliyor. Sebebi
zenginleştirme hattındakiyle aynı: süzgeç sessizce yanlış çalışırsa
kimse fark etmez — sadece veritabanı eksik kalır. Rapora bakan kişi
"bu kelime neden yok" sorusunu cevaplayabilmeli.
"""

import re
from collections import Counter, defaultdict
from pathlib import Path

from . import frequency, function_words, phrasal
from .lemmatize import lemma as kok_bul

# Tokenizer: kesme işareti ve tire kelimenin parçası sayılıyor
# ("teacher's", "long-term"), gerisi ayraç.
TOKEN_DESENI = re.compile(r"[A-Za-z][A-Za-z'\-]*")

# Bundan kısa kelimeler hiç değerlendirilmiyor.
EN_KISA_KELIME = 3

# Tür tahmininde kullanılan sonekler.
ISIM_SONLARI = ("tion", "sion", "ment", "ness", "ity", "ance", "ence",
                "ship", "hood", "ism", "ist", "age", "ure", "cy", "logy")

# `-ist` soneki isim yapar (art -> artist) AMA bu fiiller de öyle biter.
# Sayılı bir küme; kuralla ayırmaya çalışmak yerine elle yazıldı.
IST_ILE_BITEN_FIILLER = {
    "persist", "resist", "insist", "consist", "assist", "exist",
    "subsist", "desist", "enlist", "twist", "list",
}
SIFAT_SONLARI = ("ous", "ful", "less", "ive", "able", "ible", "ical",
                 "ic", "al", "ish", "ent", "ant", "ary", "ory")
FIIL_SONLARI = ("ise", "ize", "ate", "ify", "en")


def metinleri_oku(yollar):
    """
    Dosyaları okur. (dosya_adı, metin) çiftleri döner.

    Kodlama sorunları sessizce geçilmiyor: okunamayan dosya rapora
    düşüyor, çünkü eksik okunan bir dosya eksik kelime demek ve bu
    fark edilmez.
    """
    from words.extract import pdf
    okunanlar, hatalar = [], []
    for yol in yollar:
        yol = Path(yol)
        if pdf.pdf_mi(yol):
            try:
                metin, _bilgi = pdf.pdf_metni(yol)
                okunanlar.append((yol.name, metin))
            except pdf.PdfHatasi as hata:
                hatalar.append((str(yol), str(hata)))
            continue
        try:
            okunanlar.append((yol.name, yol.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            try:
                okunanlar.append((yol.name, yol.read_text(encoding="latin-1")))
            except Exception as hata:      # pragma: no cover
                hatalar.append((str(yol), str(hata)))
        except Exception as hata:          # pragma: no cover
            hatalar.append((str(yol), str(hata)))
    return okunanlar, hatalar


def tokenle(metin):
    """Metni küçük harfli kelimelere ayırır."""
    return [t.lower().strip("'-") for t in TOKEN_DESENI.findall(metin)]


# Cümle sonu sanılmaması gereken kısaltmalar ("Dr. Hendricks" tek cümle).
KISALTMALAR = re.compile(
    r"\b(Dr|Mr|Mrs|Ms|Prof|St|Jr|Sr|vs|etc|al|Fig|Vol|No|pp|ed|eds|e\.g|i\.e|cf)\.",
    re.IGNORECASE)


def _sozlukte(kelime):
    """
    İngilizce sözlük (lemminflect) bu kelimeyi herhangi bir türde tanıyor mu?
    None: sözlük yok (paket kurulu değil) — karar verilemez.
    """
    from words import inflect
    sonuclar = [inflect.tur_sozlukte(kelime, t) for t in ("noun", "verb", "adjective", "adverb")]
    if all(r is None for r in sonuclar) and inflect._li() is None:
        return None
    return any(r is True for r in sonuclar)


def isim_sayaclari(metin):
    """
    Özel isim kararı için sayaçlar: (büyük harfle, cümle ortasında büyük
    harfle, küçük harfle) geçiş sayıları. Karar BÜTÜN dosyaların toplamıyla
    verilir (ozel_isim_karari): bir romanda isim olan "Fudge" başka bir
    kitapta küçük harfle geçiyorsa kelimedir.
    """
    buyuk_hepsi, buyuk_ortada, kucuk = Counter(), Counter(), Counter()
    metin = KISALTMALAR.sub(lambda m: m.group(0)[:-1], metin)
    for cumle in re.split(r"(?<=[.!?])\s+|\n{2,}", metin):
        tokenler = TOKEN_DESENI.findall(cumle)
        for i, token in enumerate(tokenler):
            temiz = re.sub(r"'s$", "", token.strip("'-"))
            if not temiz:
                continue
            if temiz[0].isupper():
                buyuk_hepsi[temiz.lower()] += 1
                if i > 0:                      # cümle başı değil
                    buyuk_ortada[temiz.lower()] += 1
            else:
                kucuk[temiz.lower()] += 1
    return buyuk_hepsi, buyuk_ortada, kucuk


# Küçük harfle geçişlerin payı bunun altındaysa kelime "hep büyük harfle"
# sayılır. Sıfır değil: romanlarda "hermione" bir yerde yazım hatasıyla
# küçük geçebiliyor ve eski kural onu kelime sanıyordu (24 Eylül).
ISIM_KUCUK_PAYI = 0.10
# Sözlükte OLAN kelime (Harry = rahatsız etmek) ancak çok güçlü kanıtla isim
# sayılır: cümle ortasında en az 10 kez büyük harfle ve neredeyse hiç küçük.
SOZLUK_ISIM_EN_AZ = 10
SOZLUK_ISIM_KUCUK_PAYI = 0.02


def ozel_isim_karari(buyuk_hepsi, buyuk_ortada, kucuk):
    """
    KURAL (24 Eylül, 17 PDF'lik ilk denemeden sonra):
      a) İngilizce sözlükte YOK + küçük harfle geçiş payı <= %10
         -> özel isim (Vygotsky, Hermione; cümle başında olsa da)
      b) Sözlükte VAR -> kelimedir (Brown, Smith, University), YALNIZCA
         cümle ortasında >= 10 kez büyük harfle ve küçük harf payı <= %2 ise
         isim (Harry Potter'daki "Harry").
      Sözlük kurulu değilse eski kural: cümle ortasında büyük, hiç küçük yok.
    """
    sonuc = set()
    for k, buyuk in buyuk_hepsi.items():
        toplam = buyuk + kucuk[k]
        kucuk_payi = kucuk[k] / toplam
        sozlukte = _sozlukte(k)
        if sozlukte is None:
            if buyuk_ortada[k] and not kucuk[k]:
                sonuc.add(k)
        elif not sozlukte:
            if kucuk_payi <= ISIM_KUCUK_PAYI:
                sonuc.add(k)
        elif buyuk_ortada[k] >= SOZLUK_ISIM_EN_AZ and kucuk_payi <= SOZLUK_ISIM_KUCUK_PAYI:
            sonuc.add(k)
    return sonuc


def ozel_isimleri_bul(metin):
    """Tek bir metnin özel isimleri (bkz. ozel_isim_karari)."""
    return ozel_isim_karari(*isim_sayaclari(duz_tirnak(metin)))


def duz_tirnak(metin):
    """Kıvrık kesme işaretleri: "didn’t" -> "didn't" (yoksa "didn" + "t" oluyordu)."""
    return metin.replace("\u2019", "'").replace("\u2018", "'").replace("\u02bc", "'")


# Fiil iddiası için metinde gereken en az çekim görülmesi.
# Tek bir `-ing` yetmiyor: `fingerprinting`, `tutoring`, `volunteering`
# isimden türemiş biçimler olabiliyor ve ilk denemede `fingerprint:verb`,
# `tutor:verb` gibi yanlış türler çıktı. İki kanıt istemek bunları eliyor,
# gerçek fiilleri (metinde hem `sustained` hem `sustaining` geçen) tutuyor.
FIIL_ICIN_EN_AZ_KANIT = 2

# Bu soneklerle biten kelimeler çekim görülse bile fiil sayılmıyor:
# `mediation`, `implementation` isimdir, `-ing` alması onları fiil yapmaz.
FIIL_OLAMAZ_SONLARI = ("tion", "sion", "ment", "ness", "ity", "ance",
                       "ence", "ship", "ism", "ist", "logy")


def tur_tahmin(kok, bicim_sayaci):
    """
    Kelimenin türünü tahmin eder; emin değilse BOŞ döner.

    İki kaynak: metinde görülen çekimler ve sonekler. Birincisi daha
    güvenilir — `implement`, `implemented`, `implementing` görülmüşse bu
    bir fiildir, sonekine bakmaya gerek yok.

    Boş dönmek bir başarısızlık değil, bir karar: tür yazılmazsa
    zenginleştirme hattındaki model kendisi seçiyor. Yanlış tür yazmak,
    tür yazmamaktan kötüdür — model yanlış türe göre anlam, cümle ve eş
    dizim üretir ve hepsi çöpe gider.

    Tür belirtmenin sebebi KELIME-HATTI-DEVAM.txt §12: tür yazılmadığında
    model bir turda `advocate`i isim, başka turda fiil sayıyordu.
    Gerçekten iki türlü olan kelimeler için liste dosyasına iki satır
    yazmak gerekiyor; bu komut bunu otomatik yapmıyor, çünkü hangi
    kelimenin gerçekten iki türlü olduğuna metindeki kanıt karar veremiyor
    (`-s` eki hem çoğul hem 3. tekil olabiliyor).
    """
    # 1. Metindeki kanıt
    if not kok.endswith(FIIL_OLAMAZ_SONLARI):
        kanit = bicim_sayaci.get(kok + "ed", 0) + bicim_sayaci.get(kok + "ing", 0)
        if kok.endswith("e"):
            kanit += (bicim_sayaci.get(kok + "d", 0)
                      + bicim_sayaci.get(kok[:-1] + "ing", 0))
        if kanit >= FIIL_ICIN_EN_AZ_KANIT:
            return "verb"

    # 2. Sonekler
    if kok.endswith("ly") and len(kok) > 4:
        return "adverb"
    if kok in IST_ILE_BITEN_FIILLER:
        return "verb"
    if kok.endswith(ISIM_SONLARI):
        return "noun"
    if kok.endswith(SIFAT_SONLARI):
        return "adjective"
    if kok.endswith(FIIL_SONLARI):
        return "verb"
    return ""


def calistir(yollar, *, top_skip=2000, min_zipf=frequency.VARSAYILAN_MIN_ZIPF,
             min_count=1, mevcut_kelimeler=None, limit=None,
             phrasal_dahil=True):
    """
    Süzme hattını çalıştırır.

    mevcut_kelimeler: veritabanında zaten olan kelimeler (küçük harfli
    küme). Verilirse çıktıdan düşülüyorlar — komut defalarca
    çalıştırılacağı için şart.

    Dönen sözlük hem sonucu hem raporu taşıyor.
    """
    mevcut_kelimeler = {k.lower() for k in (mevcut_kelimeler or set())}

    okunanlar, okuma_hatalari = metinleri_oku(yollar)

    ham_sayac = Counter()                    # kök -> metindeki toplam geçiş
    bicim_izleri = defaultdict(Counter)      # kök -> yüzey biçimi sayaçları
    belge_sayaci = defaultdict(set)          # kök -> geçtiği dosyalar
    ozel_isimler = set()
    phrasal_bulunan, phrasal_aday = Counter(), Counter()

    isim_sayac = (Counter(), Counter(), Counter())
    for dosya_adi, metin in okunanlar:
        metin = duz_tirnak(metin)
        for toplam, parca in zip(isim_sayac, isim_sayaclari(metin)):
            toplam.update(parca)
        tokenler = tokenle(metin)

        if phrasal_dahil:
            bulunan, aday = phrasal.bul(tokenler, kok_bul)
            phrasal_bulunan.update(bulunan)
            phrasal_aday.update(aday)

        for token in tokenler:
            if len(token) < EN_KISA_KELIME or not token.isalpha():
                continue
            kok = kok_bul(token)
            ham_sayac[kok] += 1
            bicim_izleri[kok][token] += 1
            belge_sayaci[kok].add(dosya_adi)

    ozel_isimler = ozel_isim_karari(*isim_sayac)

    # En sık N kelime — kök hâlleriyle
    sik_kokler = frequency.en_sik(top_skip, kok_bul) if top_skip else set()

    sonuc = []
    elenenler = defaultdict(list)

    for kok, sayi in ham_sayac.most_common():
        # Kök ya da metindeki BÜTÜN yüzey biçimleri özel isimse at
        # ("hendricks" köke "hendrick" diye inse bile).
        if kok in ozel_isimler or (bicim_izleri[kok]
                                   and set(bicim_izleri[kok]) <= ozel_isimler):
            elenenler["özel isim"].append(kok)
            continue
        if function_words.islev_kelimesi_mi(kok):
            elenenler[f"işlev kelimesi ({function_words.grubu(kok)})"].append(kok)
            continue
        if sayi < min_count:
            elenenler["metinde yeterince geçmiyor"].append(kok)
            continue
        if kok in sik_kokler:
            elenenler[f"en sık {top_skip} kelime içinde"].append(kok)
            continue

        siklik = frequency.zipf(kok)
        if siklik < min_zipf:
            elenenler["aşırı teknik / bilinmeyen"].append(kok)
            continue
        if kok in mevcut_kelimeler:
            elenenler["veritabanında zaten var"].append(kok)
            continue

        sonuc.append({
            "word": kok,
            "count": sayi,
            "zipf": round(siklik, 2),
            "pos": tur_tahmin(kok, bicim_izleri[kok]),
            "forms": sorted(bicim_izleri[kok]),
            "form_counts": dict(bicim_izleri[kok]),
            "documents": sorted(belge_sayaci[kok]),
        })

    # Sıralama: metinde çok geçen ve yaygın olan önce. Yaygınlık ikinci
    # ölçüt çünkü aynı sıklıkta iki kelimeden daha genel olanı öğrenmek
    # daha çok işe yarar.
    sonuc.sort(key=lambda s: (-s["count"], -s["zipf"], s["word"]))

    if limit:
        sonuc = sonuc[:limit]

    phrasal_listesi = [
        {"phrase": ifade, "count": sayi}
        for ifade, sayi in phrasal_bulunan.most_common()
        if ifade.split()[0] not in mevcut_kelimeler or True
    ]
    aday_listesi = [
        {"phrase": ifade, "count": sayi}
        for ifade, sayi in phrasal_aday.most_common()
        if sayi >= phrasal.ADAY_EN_AZ_TEKRAR
    ]

    return {
        "words": sonuc,
        "phrasal": phrasal_listesi,
        "phrasal_candidates": aday_listesi,
        "dropped": {sebep: sorted(kelimeler) for sebep, kelimeler in elenenler.items()},
        "stats": {
            "files": len(okunanlar),
            "read_errors": okuma_hatalari,
            "distinct_lemmas": len(ham_sayac),
            "proper_nouns": len(ozel_isimler),
            "kept": len(sonuc),
            "dropped_total": sum(len(v) for v in elenenler.values()),
            "wordfreq": frequency.wordfreq_var_mi(),
        },
    }
