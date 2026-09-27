"""
1. aşamanın deterministik denetimi.

Modelin cevabı buraya HAM gelir; buradan ara depoya yazılacak TASLAK
olarak çıkar. Aradaki işler:

  1. Yazımı temizle, tekrarları at, türü düzelt.
  2. OLMAYAN kelimeleri at. Model "independing", "uneducating" gibi
     kelimeler üretebiliyor (eski prompt'un örneklerinde bile vardı).
     Bunun kodla ölçülebilir tek cevabı sıklık verisi: wordfreq'te
     sıklığı tam 0 olan dizi İngilizcede yazılmıyor demek.
  3. ÇEKİMİ kelime diye yazılmış üyeleri ayıkla (destroyed, destroying).
  4. Kökü denetle: listede mi, anlamı koruyan bir önekle mi başlıyor,
     -ly zarfı mı?
  5. Kalan her üyenin çekimlerini KODLA üret (inflect.cekimler).

İki seviye var: "hata" taslağı kusurlu yapar (birleştirmeye girmez ama
raporda görünür), "uyari" yazılır ama işaretlenir. Katman ONARIR: tek bir
uydurma kelime yüzünden bütün aile çöpe gitmez.
"""

import re
from dataclasses import asdict, dataclass

from words import inflect
from words.extract import frequency

# Anlamı KORUYAN önekler (prompt.py · family_filling · NOT-5). Bunlarla
# başlayan kelime ana kelimenin ailesinde kalır ve kök bu öneklerle
# BAŞLAYAMAZ — ön ek atılınca kalan kelime ailedeyse.
# Uzun önek önce: "non" "no"dan, "under" "un"dan önce denensin.
KORUYAN_ONEKLER = ("under", "over", "non", "dis", "mis", "un", "in", "im",
                   "il", "ir", "re")

# Sıklık eşikleri (Zipf). Ölçülmüş değerlerle seçildi:
#   influentially 1.37 · overcomer 1.52 · discoverability 1.68
#   consensually 1.88 · unethically 1.98 · destructiveness 2.06
#   educationally 2.35 · conformist 2.55
# 0 -> İngilizcede yazılmıyor (uneducating, independing, nonconformed: 0.00)
# İlk gerçek çalıştırmadan sonra (19 Eylül) ayıklama eşiği 1.5'ten 2.0'a
# çıkarıldı: 1.5-2.0 arasında kalanların hepsi gerçek ama öğrenciye yük.
AYIKLAMA_ESIGI = 2.0    # altı atılır
NADIR_ESIGI = 2.5       # altı uyarı: tutulur, raporda işaretlenir
# Kök için ayrı eşik: kök nadir olabilir ama UYDURMA olmamalı. Ek soyulmuş
# gövdeler ("herit" 1.03, "ambigu" 1.04) web metninde yazım hatası olarak
# geçtiği için tam 0 değil.
KOK_ESIGI = 1.5
# -ly zarfları için ayrı, daha yüksek eşik (2. deneme, 19 Eylül): 2.0-2.5
# arasında tutulan kelimelerin çoğu ailedeki sıfattan türemiş nadir
# zarflardı (unjustifiably 2.2, comparably 2.47, colorfully 2.07). Sıfatı
# bilen öğrenci zarfı zaten çıkarabiliyor; sözlüğe ayrı madde olarak
# girmesi yük. Sıfatı ailede OLMAYAN zarf bu eşiğe takılmaz.
ZARF_AYIKLAMA_ESIGI = 2.5

# Anlamı KOPARAN önekler. Bunlarla başlayan kelime, önek atılınca kalan
# kelimenin ailesine GİRMEZ: withdraw ≠ draw, become ≠ come, outline ≠
# line, foresee ≠ see, upset ≠ set, offset ≠ set. (over- ve under- burada
# YOK: aşırılık/azlık anlamında ailede kalıyorlar, bkz. KORUYAN_ONEKLER.)
# 2. denemede model "withdraw"ın kökünü "draw" yazdı; bu liste o hatayı
# kodla yakalamak için.
KOPARAN_ONEKLER = ("with", "fore", "out", "off", "up", "be")

YAZIM_DESENI = re.compile(r"^[a-z][a-z' \-]*[a-z]$")


@dataclass
class Sorun:
    seviye: str     # "hata" | "uyari" | "bilgi"
    kod: str
    mesaj: str

    def __str__(self):
        isaret = {"hata": "X", "uyari": "!"}.get(self.seviye, "·")
        return f"{isaret} [{self.kod}] {self.mesaj}"


# ----------------------------------------------------------------------
# Varlık denetimi
# ----------------------------------------------------------------------

def varlik_kaynagi():
    """
    Hangi kaynakla "bu kelime var mı" sorusuna cevap verilebiliyor?

      "wordfreq"  güvenilir: sıklık 0 ise yok
      "sozluk"    zayıf: sistem sözlüğü birçok türemiş kelimeyi içermez,
                  bu yüzden yalnızca UYARI verilir, hiçbir şey atılmaz
      None        denetim yapılamıyor

    Komut başlarken bunu ekrana yazıyor: denetim sessizce zayıflamasın.
    """
    if frequency.wordfreq_var_mi():
        return "wordfreq"
    from words.enrich.checks import _sozluk
    return "sozluk" if _sozluk() else None


def siklik(kelime):
    """wordfreq varsa Zipf değeri, yoksa None."""
    if not frequency.wordfreq_var_mi():
        return None
    return round(frequency.zipf(kelime), 2)


def _sistem_sozlugunde(kelime):
    from words.enrich.checks import _sozluk
    sozluk = _sozluk()
    return (not sozluk) or kelime in sozluk or " " in kelime


# ----------------------------------------------------------------------
# Yardımcılar
# ----------------------------------------------------------------------

def normalize(metin):
    """Küçük harf, tek boşluk, tipografik kesme işareti düz, Amerikan yazımı."""
    metin = (metin or "").strip().strip("\"'`").lower()
    metin = metin.replace("’", "'").replace("‘", "'")
    # Veritabanı AMERİKAN yazımıyla tutuluyor: analyse -> analyze.
    return inflect.amerikan(re.sub(r"\s+", " ", metin))


def _zarf_tabani(zarf, metinler):
    """
    -ly zarfının ailedeki sıfat tabanı: inevitably -> inevitable,
    happily -> happy, basically -> basic, quickly -> quick. Yoksa None.
    """
    for aday in sorted(metinler, key=len, reverse=True):
        if aday == zarf:
            continue
        if zarf in (aday + "ly", aday[:-1] + "y", aday[:-1] + "ily",
                    aday + "ally"):
            return aday
    return None


def _yalin_uye(kok, metinler):
    """
    Kök, ailedeki DAHA KISA bir üyeyle başlıyorsa o üye: dependent ->
    depend, interpretation -> interpret, consciousness -> conscious.
    En kısa aday seçilir. 4 harften kısa üyeler sayılmaz ("a", "in").

    Bu kural modelin koyduğu üyelere güveniyor: aileye yanlışlıkla
    "station" girmişse "stationery" kökü ona iner. Ama o durumda aile
    zaten yanlış kurulmuştur ve birleştirme bunu örtüşme üzerinden yakalar.
    """
    adaylar = []
    for m in metinler:
        if len(m) < 4 or m == kok or " " in m:
            continue
        govdeler = {m}
        if m.endswith("y"):
            govdeler.add(m[:-1] + "i")          # happy -> happi(ness)
        if m.endswith("de"):
            govdeler.add(m[:-2] + "s")          # decide -> decis(ive)
        if m.endswith("e"):
            govdeler.add(m[:-1])                # create -> creat(ive)
        if any(len(g) >= 4 and len(kok) > len(g) and kok.startswith(g) for g in govdeler):
            adaylar.append(m)
    return min(adaylar, key=len) if adaylar else None


def _koparan_onek(kelime, metinler):
    """
    Kelime, anlamı koparan bir önek + ailedeki bir kelime mi? Öyleyse önek.
    withdraw + {draw} -> "with"; become + {come} -> "be".
    """
    for onek in KOPARAN_ONEKLER:
        if kelime.startswith(onek) and kelime[len(onek):] in metinler:
            return onek
    return None


def _onek_duzelt(kok, metinler):
    """
    Kök, anlamı koruyan bir önekle başlıyor VE önek atılınca kalan kelime
    ailede varsa o kelimeyi döndürür: unexpected -> expected (-> expect
    aşağıda tekrar denenir). Değilse None.
    """
    for onek in KORUYAN_ONEKLER:
        if kok.startswith(onek):
            kalan = kok[len(onek):]
            if len(kalan) >= 3 and kalan in metinler:
                return kalan
    return None


# ----------------------------------------------------------------------
# Ana fonksiyon
# ----------------------------------------------------------------------

def denetle(cevap, tohum, tur_ipucu=""):
    """
    Modelin AileCevabi'nı taslağa çevirir.

    Döner: {"kok", "uyeler", "ayiklanan", "sorunlar", "durum"}
      durum: "tamam"       birleştirmeye girer
             "bulunamadi"  model kelimeyi tanımadı (boş cevap)
             "kusurlu"     kök kurtarılamadı; raporda, birleştirmede yok
    """
    sorunlar, ayiklanan = [], []

    def ekle(seviye, kod, mesaj):
        sorunlar.append(Sorun(seviye, kod, mesaj))

    ham_tohum = (tohum or "").strip().lower()
    tohum = normalize(tohum)
    if tohum != ham_tohum:
        ekle("bilgi", "amerikan_yazimi", f"Sorulan '{ham_tohum}' -> '{tohum}'.")
    kok = normalize(cevap.root_word)
    kaynak = varlik_kaynagi()

    # --- 1. Boş cevap -------------------------------------------------
    if not cevap.words:
        ekle("hata", "bulunamadi",
             "Model bu kelimeyi tanımadı (boş aile döndü).")
        return _taslak(kok, [], ayiklanan, sorunlar, "bulunamadi")

    # --- 2. Yazım, tür, tekrar ----------------------------------------
    uyeler, gorulen = [], set()
    for uye in cevap.words:
        metin, tur = normalize(uye.word), uye.type
        ham = (uye.word or "").strip().lower()
        if metin != ham and YAZIM_DESENI.match(ham or "-"):
            ekle("uyari", "amerikan_yazimi", f"'{ham}' İngiliz yazımı; '{metin}' yapıldı.")

        if not metin or not YAZIM_DESENI.match(metin):
            ayiklanan.append({"word": metin, "type": tur, "sebep": "gecersiz_yazim"})
            ekle("uyari", "gecersiz_yazim", f"'{uye.word}' kelime biçiminde değil; atıldı.")
            continue

        if " " in metin and tur != "phrasal_verb":
            if tur == "verb":
                tur = "phrasal_verb"
                ekle("uyari", "tur_duzeltildi", f"'{metin}' çok kelimeli fiil: phrasal_verb yapıldı.")
            else:
                ayiklanan.append({"word": metin, "type": tur, "sebep": "cok_kelimeli"})
                ekle("uyari", "cok_kelimeli",
                     f"'{metin}' ({tur}) çok kelimeli bir ifade; kelime hattına girmez, atıldı.")
                continue
        if tur == "phrasal_verb" and " " not in metin:
            tur = "verb"
            ekle("uyari", "tur_duzeltildi", f"'{metin}' tek kelime: phrasal_verb değil, verb yapıldı.")

        if (metin, tur) in gorulen:
            continue
        gorulen.add((metin, tur))
        uyeler.append({"word": metin, "type": tur})

    # --- 3. Varlık ------------------------------------------------------
    korunan = {tohum, kok}   # tohum metinde geçti; nadir olsa da atılmaz
    tum_metinler = {u["word"] for u in uyeler}
    kalan = []
    for uye in uyeler:
        metin = uye["word"]
        z = siklik(metin)
        uye["zipf"] = z

        if kaynak == "wordfreq":
            if z == 0 and metin != tohum:
                ayiklanan.append({**uye, "sebep": "olmayan_kelime"})
                ekle("uyari", "olmayan_kelime",
                     f"'{metin}' İngilizcede geçmiyor (sıklık 0); atıldı.")
                continue
            if z < AYIKLAMA_ESIGI and metin not in korunan:
                ayiklanan.append({**uye, "sebep": "cok_nadir"})
                ekle("uyari", "cok_nadir",
                     f"'{metin}' çok nadir (zipf {z}); öğrenciye yük, atıldı.")
                continue
            if (uye["type"] == "adverb" and z < ZARF_AYIKLAMA_ESIGI
                    and metin not in korunan and _zarf_tabani(metin, tum_metinler)):
                ayiklanan.append({**uye, "sebep": "nadir_zarf"})
                ekle("uyari", "nadir_zarf",
                     f"'{metin}' nadir bir zarf (zipf {z}) ve sıfatı ailede var; atıldı.")
                continue
            if z < NADIR_ESIGI:
                ekle("uyari", "nadir", f"'{metin}' nadir (zipf {z}); tutuldu.")
        elif kaynak == "sozluk" and not _sistem_sozlugunde(metin):
            ekle("uyari", "dogrulanamadi",
                 f"'{metin}' sistem sözlüğünde yok (wordfreq kurulu değil, atılmadı).")
        kalan.append(uye)
    uyeler = kalan

    # --- 4. Çekimi kelime diye yazılmış üyeler ------------------------
    # destroy ailesinde "destroyed (verb)" bir kelime değil, destroy'un
    # 2. hâli. Sıfat/isim olarak yazılmışsa (interested, building)
    # prompt'un izin verdiği istisna olabilir: tutulur ama işaretlenir.
    #
    # İsimlerin çoğulu da aynı: "interests (noun)" interest'in çoğulu.
    # Ama "ethics" ethic'in çoğulu OLDUĞU hâlde ayrı bir kelime (etik bilimi).
    # Ayrım sıklıkla: -s hâli tekilinden DAHA SIK kullanılıyorsa bağımsız
    # kelimedir (ethics 4.19 > ethic 3.54), değilse çekimdir
    # (arguments 4.33 < argument 4.64).
    cekim_yuzeyleri = {}
    tekiller = {}
    for uye in uyeler:
        if uye["type"] == "noun":
            cogul = inflect.cekimler(uye["word"], "noun")["cekim"]["sVersion"]
            if cogul and cogul != uye["word"]:
                tekiller[cogul] = uye["word"]
        if uye["type"] in ("verb", "phrasal_verb"):
            sonuc = inflect.cekimler(uye["word"], uye["type"])
            s_hali = sonuc["cekim"]["sVersion"]
            if s_hali and s_hali != uye["word"]:
                tekiller.setdefault(s_hali, uye["word"])
            for alan in ("v2Form", "v3Form", "ingForm"):
                yuzey = sonuc["cekim"][alan]
                if yuzey and yuzey != uye["word"]:
                    cekim_yuzeyleri[yuzey] = uye["word"]
            for yuzey in sonuc["diger_yazimlar"]:
                cekim_yuzeyleri.setdefault(yuzey, uye["word"])

    kalan = []
    for uye in uyeler:
        tekil = tekiller.get(uye["word"])
        if tekil and uye["word"] not in korunan and uye["type"] in ("noun", "verb"):
            z_cogul, z_tekil = siklik(uye["word"]), siklik(tekil)
            if (z_cogul is None or z_tekil is None or z_cogul < z_tekil
                    or uye["word"] in DUZENSIZ_COGUL_AT):
                ayiklanan.append({**uye, "sebep": "cekim_uyesi"})
                ekle("uyari", "cekim_uyesi",
                     f"'{uye['word']}' {tekil} kelimesinin -s hâli, ayrı kelime değil; atıldı.")
                continue
            ekle("bilgi", "bagimsiz_cogul",
                 f"'{uye['word']}' {tekil} kelimesinin -s hâli ama ondan daha sık "
                 f"kullanılıyor; ayrı kelime sayıldı.")
        kalan.append(uye)
    uyeler = kalan

    kalan = []
    for uye in uyeler:
        fiil = cekim_yuzeyleri.get(uye["word"])
        if fiil and uye["word"] not in korunan:
            if uye["type"] in ("verb", "phrasal_verb"):
                ayiklanan.append({**uye, "sebep": "cekim_uyesi"})
                ekle("uyari", "cekim_uyesi",
                     f"'{uye['word']}' {fiil} fiilinin çekimi, ayrı kelime değil; atıldı.")
                continue
            # İlk gerçek çalıştırmada 7 uyarının 7'si de gerçekten bağımsız
            # kelimeydi (understanding, interesting, expected): uyarı değil bilgi.
            ekle("bilgi", "katilim_sifati",
                 f"'{uye['word']}' ({uye['type']}) aynı zamanda {fiil} fiilinin çekimi.")
        kalan.append(uye)
    uyeler = kalan

    metinler = {u["word"] for u in uyeler}

    # --- 4a. Tür ---------------------------------------------------------
    # Kelime gerçek ama bu türde kullanılmıyor: become (adjective),
    # weak (noun), existent (noun). Ölçüt lemminflect sözlüğü (tur_sozlukte).
    #
    # -ed/-ing hâlleri AYRI tutuluyor: sözlük "polluted"ı yalnızca fiil
    # olarak tanıyor, bu doğru bir işaret (fiilden ayrı anlamı yok); ama
    # "caring" ve "written" da öyle görünüyor ve ikisi de gerçek sıfat.
    # Bu yüzden katılımlar ATILMIYOR, "şüpheli" işaretleniyor ve kararı
    # 3. aşama veriyor: model fiilden ayrı bir anlam üretemezse
    # (found=false) kelime veritabanına girmiyor.
    # Kök de denetlenir (weak kökü "weak (noun)" diye yazılmışsa o satır
    # gider, "weak (adjective)" kalır). Tek istisna: sorulan kelimenin TEK
    # satırı buysa atılmaz — kelime metinde geçti, türü 3. aşamada belli olur.
    kalan = []
    for uye in uyeler:
        sozlukte = inflect.tur_sozlukte(uye["word"], uye["type"])
        tek_tohum = uye["word"] == tohum and sum(
            1 for u in uyeler if u["word"] == tohum) == 1
        if sozlukte is False and not tek_tohum:
            katilim = (uye["word"].endswith(("ed", "ing", "en"))
                       and inflect.tur_sozlukte(uye["word"], "verb"))
            if katilim:
                uye["supheli_katilim"] = True
                ekle("bilgi", "supheli_katilim",
                     f"'{uye['word']}' ({uye['type']}) sözlükte yalnızca fiil çekimi; "
                     f"3. aşamada fiilden ayrı anlamı yoksa düşecek.")
            else:
                ayiklanan.append({**uye, "sebep": "supheli_tur"})
                ekle("uyari", "supheli_tur",
                     f"'{uye['word']}' {uye['type']} olarak kullanılmıyor (sözlük); atıldı.")
                continue
        kalan.append(uye)
    uyeler = kalan
    metinler = {u["word"] for u in uyeler}

    # --- 4b. Anlamı koparan önekler -------------------------------------
    # Sorulan kelime = koparan önek + kök ise model öneki yanlışlıkla
    # soyup BAŞKA bir kelimenin ailesini kurmuş demek (withdraw -> draw).
    # Bu aile sorulan kelimenin ailesi değil: taslak kusurlu. Komut bu
    # durumda bir kez, uyarıyla tekrar soruyor (aile_uret · _isle).
    onek = _koparan_onek(tohum, {kok})
    if onek:
        ekle("hata", "koparan_onek",
             f"'{tohum}' = '{onek}' + '{kok}', ama '{onek}-' anlamı koruyan bir önek "
             f"değil: kök '{kok}' olamaz, '{tohum}' kendi ailesini kurar.")
        return _taslak(kok, uyeler, ayiklanan, sorunlar, "kusurlu")

    # Üyeler arasında "koparan önek + başka üye" olanlar ailede olmamalı
    # (draw ailesinde withdraw, come ailesinde become).
    kalan = []
    for uye in uyeler:
        onek = _koparan_onek(uye["word"], metinler - {uye["word"]})
        if onek and uye["word"] != tohum:
            ayiklanan.append({**uye, "sebep": "koparan_onek"})
            ekle("uyari", "koparan_onek",
                 f"'{uye['word']}' '{onek}-' ile başlıyor; bu önek anlamı koparır, "
                 f"ayrı bir ailedir. Atıldı.")
            continue
        kalan.append(uye)
    uyeler = kalan
    metinler = {u["word"] for u in uyeler}

    # --- 5. Kök ---------------------------------------------------------
    if not kok:
        ekle("hata", "kok_bos", "Model aile döndürdü ama kök yazmadı.")
        return _taslak(kok, uyeler, ayiklanan, sorunlar, "kusurlu")

    # Kökü ailenin daha yalın üyesine indir. Üç kural, sırayla ve
    # birbirini tetikleyebildiği için birkaç tur:
    #   önek    independent  -> dependent   (anlamı koruyan önek atılır)
    #   türev   dependent    -> depend      (prompt kural 3: türemiş
    #                                        kelime kök olamaz)
    #   zarf    inevitably   -> inevitable
    for _ in range(4):
        duzgun = _onek_duzelt(kok, metinler)
        if duzgun:
            ekle("uyari", "onekli_kok_duzeltildi",
                 f"Kök '{kok}' anlamı koruyan bir önekle başlıyor ve '{duzgun}' "
                 f"ailede; kök '{duzgun}' yapıldı.")
            kok = duzgun
            continue
        duzgun = _yalin_uye(kok, metinler)
        if duzgun:
            ekle("uyari", "turemis_kok_duzeltildi",
                 f"Kök '{kok}' ailedeki '{duzgun}' kelimesinden türemiş; "
                 f"kök '{duzgun}' yapıldı.")
            kok = duzgun
            continue
        if kok.endswith("ly"):
            duzgun = _zarf_tabani(kok, metinler)
            if duzgun:
                ekle("uyari", "zarf_kok_duzeltildi",
                     f"-ly zarfı kök olamaz: '{kok}' yerine '{duzgun}'.")
                kok = duzgun
                continue
        break

    # Kök eşiği için bkz. KOK_ESIGI. Sorulan kelimenin kendisi kökse nadir
    # olabilir (metinde geçti), ona dokunulmuyor.
    if kaynak == "wordfreq" and kok != tohum and siklik(kok) < KOK_ESIGI:
        ekle("hata", "uydurma_kok",
             f"Kök '{kok}' İngilizcede (neredeyse) geçmiyor (zipf {siklik(kok)}).")
        return _taslak(kok, uyeler, ayiklanan, sorunlar, "kusurlu")

    if kok not in metinler:
        ekle("uyari", "kok_listede_yok",
             f"Kök '{kok}' aile listesinde yok (prompt kuralı: kök de bir üyedir).")

    if tohum and tohum not in metinler:
        ekle("uyari", "tohum_ailede_yok",
             f"Sorulan kelime '{tohum}' kendi ailesinde yok.")

    # --- 6. Çekimler ----------------------------------------------------
    for uye in uyeler:
        sonuc = inflect.cekimler(uye["word"], uye["type"])
        uye["cekim"] = sonuc["cekim"]
        uye["diger_yazimlar"] = sonuc["diger_yazimlar"]
        uye["cekim_kaynagi"] = sonuc["kaynak"]

    # Kök önce, sonra alfabetik: raporda okunaklı dursun.
    uyeler.sort(key=lambda u: (u["word"] != kok, u["word"], u["type"]))
    return _taslak(kok, uyeler, ayiklanan, sorunlar, "tamam")


def _taslak(kok, uyeler, ayiklanan, sorunlar, durum):
    return {
        "kok": kok,
        "uyeler": uyeler,
        "ayiklanan": ayiklanan,
        "sorunlar": [asdict(s) for s in sorunlar],
        "durum": durum,
    }


def sorun_metni(sorun):
    """Depodaki sözlük biçimindeki sorunu tek satıra çevirir."""
    return str(Sorun(**sorun))


# Tekilinden sık kullanılsa da AYRI kelime sayılmayan düzensiz çoğullar
# (25 Eylül: "children" ayrı kelime olarak yazılmıştı). "people" bilerek
# yok: "halk, insanlar" anlamıyla kendi başına öğretilir.
DUZENSIZ_COGUL_AT = {"children", "women", "men", "feet", "teeth", "mice", "geese",
                     "oxen", "lice"}
