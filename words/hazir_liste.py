"""
Hazır listeler (ürün raporu 4.1, veri işi D7).

Learn & Pass bağlantısı — L&P'nin okuyacağı tek fonksiyon:

    from words.hazir_liste import aktif_liste
    liste = aktif_liste(request.user)       # HazirListe ya da None
    if liste:
        adaylar = liste.sirali_kelimeler()  # listedeki sırayla Word queryset'i
    else:
        ... seviyeye göre (eski davranış)

"Bu listeyle çalış" basılınca HazirListeSecimi satırı yazılır; "Seviyeme
dön" satırı siler. Girişsiz ziyaretçinin seçimi olmaz (None döner).

Listeyi dosyadan yüklemek: `manage.py hazir_liste_yukle` (bkz. komut). Bu
modüldeki `dosyadan_eslestir` komutun ve testlerin kullandığı saf eşleştirme.
"""

from dataclasses import dataclass, field

from django.db.models import Q

from .models import HazirListe, HazirListeSecimi, PartOfSpeech, Word


def aktif_liste(user):
    """Kullanıcının "Bu listeyle çalış" dediği yayındaki liste; yoksa None."""
    if user is None or not user.is_authenticated:
        return None
    secim = (HazirListeSecimi.objects.filter(user=user, liste__yayinda=True)
             .select_related("liste").first())
    return secim.liste if secim else None


def listeyle_calis(user, liste):
    """Seçimi kaydeder (bir kullanıcıda tek liste: öncekinin yerine geçer)."""
    HazirListeSecimi.objects.update_or_create(user=user, defaults={"liste": liste})


def seviyeye_don(user):
    HazirListeSecimi.objects.filter(user=user).delete()


def yayindaki_listeler():
    return HazirListe.objects.filter(yayinda=True).order_by("sira", "ad")


# ----------------------------------------------------------------------
# Dosyadan eşleştirme (komut: hazir_liste_yukle)
# ----------------------------------------------------------------------

# Satırdaki tür yazımları -> PartOfSpeech. İngilizce, Türkçe ve kısaltmalar.
TUR_YAZIMLARI = {
    "noun": PartOfSpeech.NOUN, "n": PartOfSpeech.NOUN, "isim": PartOfSpeech.NOUN,
    "verb": PartOfSpeech.VERB, "v": PartOfSpeech.VERB, "fiil": PartOfSpeech.VERB,
    "adjective": PartOfSpeech.ADJECTIVE, "adj": PartOfSpeech.ADJECTIVE,
    "sıfat": PartOfSpeech.ADJECTIVE, "sifat": PartOfSpeech.ADJECTIVE,
    "adverb": PartOfSpeech.ADVERB, "adv": PartOfSpeech.ADVERB, "zarf": PartOfSpeech.ADVERB,
    "phrasal_verb": PartOfSpeech.PHRASAL_VERB, "phrasal verb": PartOfSpeech.PHRASAL_VERB,
    "phr": PartOfSpeech.PHRASAL_VERB, "pv": PartOfSpeech.PHRASAL_VERB,
    "preposition": PartOfSpeech.PREPOSITION, "prep": PartOfSpeech.PREPOSITION,
    "edat": PartOfSpeech.PREPOSITION,
    "conjunction": PartOfSpeech.CONJUNCTION, "conj": PartOfSpeech.CONJUNCTION,
    "bağlaç": PartOfSpeech.CONJUNCTION, "baglac": PartOfSpeech.CONJUNCTION,
}

# Tür verilmemiş ve kelimenin birden çok türü varsa hangisi seçilir:
# daha yaygın (düşük CEFR) olan; eşitse bu sıra.
_TUR_SIRASI = [kod for kod, _ in PartOfSpeech.choices]
_CEFR_SIRASI = {"A1": 0, "A2": 1, "B1": 2, "B2": 3, "C1": 4, "C2": 5}


@dataclass
class EslesmeSonucu:
    kelimeler: list = field(default_factory=list)       # sıralı Word listesi
    bolumler: list = field(default_factory=list)        # kelimelerle aynı sırada bölüm adı ("" olabilir)
    aileler: list = field(default_factory=list)         # kelimelerle aynı sırada kaynağın ailesi (liste)
    eslesmeyenler: list = field(default_factory=list)   # (satır no, satır, neden)
    kokten: list = field(default_factory=list)          # (satır, kök) went -> go
    belirsiz: list = field(default_factory=list)        # (satır, seçilen, diğer türler)
    tekrarlar: list = field(default_factory=list)       # (satır no, satır)


def satiri_coz(satir):
    """'aim:fiil' -> ('aim', 'verb'); 'aim' -> ('aim', None); tür bilinmiyorsa ValueError."""
    metin, _, tur = satir.partition(":")
    metin = " ".join(metin.split())
    tur = tur.strip().lower()
    if not tur:
        return metin, None
    if tur not in TUR_YAZIMLARI:
        raise ValueError(f"bilinmeyen tür: {tur}")
    return metin, TUR_YAZIMLARI[tur]


def _yaygin_once(kelimeler):
    return sorted(kelimeler, key=lambda w: (_CEFR_SIRASI.get(w.cefr, 9),
                                            _TUR_SIRASI.index(w.pos) if w.pos in _TUR_SIRASI else 99,
                                            w.id))


def dosyadan_eslestir(satirlar):
    """
    Bir satıra bir kelime[:tür]. Boş satırlar ve # ile başlayanlar atlanır.
    "## 1" ya da "## Food" satırı bölüm başlatır: sonraki kelimeler o bölümdedir.
    "abandon | abandoned, abandoning": "|" sonrası kaynağın kelime ailesidir (kartta gösterilir).
    Yalnızca ortak sözlükteki (kur ya da herkese açık) kelimelerle eşleşir.

      - Tür verilmişse o tür; yoksa kelimenin en yaygın türü (ötekiler raporlanır).
      - Kelime yoksa çekimli hâl köküne bağlanır (went -> go) ve raporlanır.
      - Hiçbiri tutmazsa eşleşmeyenlere yazılır.
    """
    sonuc = EslesmeSonucu()
    gorulen = set()
    ortak = Q(isBaseWord=True) | Q(visibility="public")
    bolum = ""
    for no, ham in enumerate(satirlar, start=1):
        satir = ham.strip()
        if satir.startswith("## "):
            bolum = satir[3:].strip()[:80]
            continue
        if not satir or satir.startswith("#"):
            continue
        satir, _, aile_metni = satir.partition("|")
        satir = satir.strip()
        aile = [a.strip() for a in aile_metni.split(",") if a.strip()]
        try:
            metin, tur = satiri_coz(satir)
        except ValueError as hata:
            sonuc.eslesmeyenler.append((no, satir, str(hata)))
            continue
        if not metin:
            continue

        adaylar = list(Word.objects.filter(ortak, text__iexact=metin))
        if not adaylar:
            koklar = list(Word.objects.filter(ortak, forms__surface__iexact=metin).distinct())
            if koklar:
                sonuc.kokten.append((satir, ", ".join(sorted({w.text for w in koklar}))))
                adaylar = koklar
        if tur:
            adaylar = [w for w in adaylar if w.pos == tur]
        if not adaylar:
            sonuc.eslesmeyenler.append((no, satir, "sözlükte yok" if not tur else "bu türde yok"))
            continue

        adaylar = _yaygin_once(adaylar)
        secilen = adaylar[0]
        if not tur and len(adaylar) > 1:
            sonuc.belirsiz.append((satir, secilen, adaylar[1:]))
        if secilen.id in gorulen:
            sonuc.tekrarlar.append((no, satir))
            continue
        gorulen.add(secilen.id)
        sonuc.kelimeler.append(secilen)
        sonuc.bolumler.append(bolum)
        sonuc.aileler.append(aile)
    return sonuc

