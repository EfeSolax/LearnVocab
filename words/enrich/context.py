"""
Modele verilecek veritabanı özeti.

Modelin DB'ye erişimi olmadığı için "bu kelime zaten var mı, ailesi kurulu mu,
hangi anlamları ekli?" sorusunu KOD cevaplıyor ve cevabı hazır metin olarak
prompt'a koyuyor. Model yalnızca eksik olanı üretiyor.

Aileyi bulmak bir tahmin işi: `encouragement` geldiğinde `courage` ailesine
girmesi gerektiğini bilmenin garantili yolu yok. Üç yoldan deneniyor:
kelimenin kendisi bir aile kökü mü, modelin önerdiği kök var mı, ve ekleri
soyulmuş hâli bir aile köküne uyuyor mu.
"""

from words.models import Category, Word, WordFamily

# Ek soyma denemeleri: en uzun ekten başlayarak.
ONEKLER = ("un", "in", "im", "ir", "il", "dis", "en", "em", "re", "mis",
           "over", "under", "non", "pre", "anti", "sub", "inter")
SONEKLER = ("ationally", "fulness", "lessness", "ability", "ibility", "ization",
            "isation", "ousness", "iveness", "ation", "ition", "ement", "ances",
            "ences", "ments", "ional", "ously", "fully", "ingly", "ness", "ment",
            "ance", "ence", "tion", "sion", "ible", "able", "ical", "ious",
            "ful", "ish", "ist", "ism", "ity", "ive", "ize", "ise", "ous",
            "ly", "al", "er", "or", "ed", "es", "ing", "y", "s")

VARSAYILAN_ALANLAR = [
    "Akademik", "Gündelik", "Psikoloji", "Sosyoloji", "Ekonomi", "Hukuk",
    "Tıp", "Coğrafya", "Tarih", "Siyaset", "Eğitim", "Teknoloji", "Çevre",
    "İş Dünyası", "Bilim", "Edebiyat",
]


def alan_listesi():
    """
    Modelin seçebileceği alanlar.

    DB'de kayıtlı alanlar esas; hiç yoksa varsayılan liste kullanılır. Modele
    açık uçlu "bir alan yaz" dersek her kelimede yeni bir alan uyduruyor ve
    kategori tablosu çöpe dönüyor — bu yüzden kapalı liste veriliyor.
    """
    kayitli = list(Category.objects.values_list("name", flat=True))
    return kayitli or VARSAYILAN_ALANLAR


def _kok_adaylari(text):
    """Ekleri soyarak olası kökleri üretir; en uzun aday önce."""
    text = text.lower().strip()
    adaylar = [text]

    for sonek in SONEKLER:
        if text.endswith(sonek) and len(text) - len(sonek) >= 3:
            govde = text[: -len(sonek)]
            adaylar.append(govde)
            # "encouragement" -> "encourag" -> "encourage"
            adaylar.append(govde + "e")
            if len(govde) > 3 and govde[-1] == govde[-2]:
                adaylar.append(govde[:-1])
            if govde.endswith("i"):
                adaylar.append(govde[:-1] + "y")

    for onek in ONEKLER:
        if text.startswith(onek) and len(text) - len(onek) >= 3:
            adaylar.append(text[len(onek):])

    gorulen, sonuc = set(), []
    for aday in adaylar:
        if aday and aday not in gorulen:
            gorulen.add(aday)
            sonuc.append(aday)
    return sonuc


def aile_bul(text, onerilen_kok=""):
    """
    Kelimenin gireceği aileyi arar; bulunamazsa None döner.

    ÜÇ YÖNLÜ arama, çünkü tek yön yetmiyor:

      AŞAĞI  kelimenin kökü bir aile mi? (encouragement -> courage)
      YANA   kelimenin kendisi bir ailenin üyesi mi?
      YUKARI kelimenin TÜREVİ zaten bir aile kurmuş mu?

    Üçüncüsü olmadan sessiz bir bozulma oluyordu: `interpretation` önce gelip
    kendi ailesini kuruyor, aylar sonra `interpret` geldiğinde ikinci bir aile
    açılıyor ve ikisi bir daha birleşmiyor. Metinlerden kelime toplandığı için
    türevin tabandan önce gelmesi kural, istisna değil.
    """
    denenecek = []
    if onerilen_kok:
        denenecek.append(onerilen_kok.lower().strip())
    denenecek += _kok_adaylari(text)

    for aday in denenecek:
        aile = WordFamily.objects.filter(root=aday).first()
        if aile:
            return aile

    # Kök olarak kayıtlı değil ama ailenin bir üyesi olabilir.
    for aday in denenecek:
        kelime = Word.objects.filter(text=aday).select_related("family").first()
        if kelime:
            return kelime.family

    # YUKARI: bu kelimenin bir TÜREVİ zaten aile kurmuş olabilir.
    # "interpret" için "interpretation", "remark" için "remarkable".
    # Doğrulamayı checks'e yaptırıyoruz: kelime, o ailenin kökü olabilir mi?
    from words.enrich.checks import kok_gecerli_mi

    kucuk = text.lower().strip()
    for aile in WordFamily.objects.filter(root__startswith=kucuk).exclude(root=kucuk):
        gecerli, _sebep = kok_gecerli_mi(kucuk, aile.root)
        if gecerli:
            return aile

    return None


def aday_aileler(text, bulunan=None, sinir=5):
    """
    Ortak yazım paylaşan ama kesin olmayan aileler — karara MODEL varacak.

    `analyse` ailesi varken `analyst` geldiğinde ek soyma çalışmıyor: ikisinin
    ortak yanı yalnızca "analy" ön eki. Kod burada karar veremez (`conscience`
    ile `conscious` da altı harf paylaşır ama ayrı ailelerdir), model ise
    verebilir. Bu yüzden kod ADAYLARI bulur, kararı modele bırakır.
    """
    kucuk = text.lower().strip()
    if len(kucuk) < 5:
        return []

    onek = kucuk[:5]
    adaylar = []
    for aile in WordFamily.objects.filter(root__startswith=onek):
        if bulunan is not None and aile.pk == bulunan.pk:
            continue
        if aile.root == kucuk:
            continue
        adaylar.append(aile)
        if len(adaylar) >= sinir:
            break
    return adaylar


def kelime_ozeti(text, onerilen_kok=""):
    """
    Bir kelime için modele verilecek DB durumu.

    Döndürdüğü sözlük:
        var_olan  - bu yazımla kayıtlı Word'ler (tür + mevcut anlamlar)
        aile      - bulunan WordFamily ya da None
        uyeler    - ailedeki kelimeler (tür bilgisiyle)
    """
    var_olan = list(
        Word.objects.filter(text=text.lower().strip())
        .prefetch_related("meanings")
    )
    aile = aile_bul(text, onerilen_kok)
    uyeler = list(aile.words.all()) if aile else []
    adaylar = aday_aileler(text, aile)

    return {"var_olan": var_olan, "aile": aile, "uyeler": uyeler,
            "adaylar": adaylar}


def ozeti_metne_cevir(ozet):
    """DB durumunu prompt'a konacak düz metne çevirir."""
    satirlar = []

    if ozet["aile"]:
        aile = ozet["aile"]
        uyeler = ", ".join(f"{k.text} ({k.pos})" for k in ozet["uyeler"]) or "—"
        satirlar.append(f"Bu kelimenin ailesi veritabanında KAYITLI: \"{aile.root}\"")
        satirlar.append(f"Ailedeki mevcut kelimeler: {uyeler}")
        satirlar.append("family_root alanına BU kökü yaz.")
    else:
        satirlar.append("Bu kelimenin ailesi veritabanında YOK; yeni aile kurulacak.")

    if ozet.get("adaylar"):
        satirlar.append("")
        satirlar.append("Yazımı benzeyen KAYITLI aileler:")
        for aday in ozet["adaylar"]:
            uyeler = ", ".join(k.text for k in aday.words.all()[:6]) or "—"
            satirlar.append(f"  - \"{aday.root}\"  (üyeler: {uyeler})")
        satirlar.append(
            "Bunlardan biri bu kelimenin TÜRETME ailesiyse family_root alanına "
            "o kökü BİREBİR yaz. Yalnızca yazımı benziyorsa (aynı kökten "
            "gelmiyorsa) yok say.")

    if ozet["var_olan"]:
        satirlar.append("")
        satirlar.append("DİKKAT — bu yazım zaten kayıtlı:")
        for kelime in ozet["var_olan"]:
            anlamlar = [a.meaning_tr for a in kelime.meanings.all()]
            liste = "; ".join(anlamlar) if anlamlar else "(anlamı yok)"
            satirlar.append(f"  - {kelime.text} ({kelime.pos}) → {liste}")
        satirlar.append(
            "Yukarıda YAZAN anlamları TEKRAR ÜRETME. Yalnızca eksik olan "
            "anlamları döndür; eksik yoksa meanings listesini boş bırak."
        )
    else:
        satirlar.append("Bu yazım veritabanında hiç yok; sıfırdan üretilecek.")

    return "\n".join(satirlar)
