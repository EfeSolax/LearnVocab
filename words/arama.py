"""
Sözlük araması (ürün raporu 4.1 ve 4.2).

Akış (words.sozluk_views.sozluk kullanır):

    sonuc = ara(user, "aim")
      sonuc.kartlar       İngilizce tam eşleşme: her tür ayrı kart (yaygın tür önce)
      sonuc.cekim_notlari went -> go: kök kelimenin kartları + "went, go kelimesinin geçmiş hâli"
      sonuc.ifadeler      ifade tam eşleşmesi ("on the other hand")
      sonuc.digerleri     "Diğer sonuçlar" (≤8): bu harflerle başlayanlar, sonra içinde geçen ifadeler
      sonuc.turkce        Türkçe sorgu: bu anlama sahip kelimeler (yaygından nadire)
      sonuc.oneriler      "Bunu mu demek istediniz?" (yazım hatası, 3–5)
      sonuc.bulunamadi    hiçbir şey yok: "Henüz sözlüğümüzde yok."

Anlık öneri (autocomplete): otomatik_oneri(q) — veritabanına gitmeden,
süreç içi dizinden (yalnızca dizinin güncel olup olmadığını soran iki
küçük sorgu). Dizin ortak sözlüğü (kur + herkese açık) tutar; Türkçe
anlam sözcüklerini hem Türkçe harfleriyle hem katlanmış (ı->i, ş->s …)
hâliyle bilir: Türkçe klavyesi olmayan "dusunmek" yazsa da bulur.

Türkçe küçük harf: I -> ı, İ -> i (tr_normal). İngilizce sorguda ise
Türkçe klavyenin büyük harf tuzağı düzeltilir: "Interest"/"İnterest" -> interest.
"""

import bisect
import difflib
import re
import time
from dataclasses import dataclass, field

from django.db.models import (
    Case, Count, IntegerField, Max, Q, Value, When,
)
from django.db.models.functions import Length
from django.db.models.signals import post_delete, post_save
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from users.seviye import kullanici_seviyesi  # noqa: F401  (arama.kullanici_seviyesi)

from .models import (
    CEFR_LEVELS, BulunamayanArama, Expression, FormKind, Meaning,
    PartOfSpeech, Word, WordForm,
)


# ----------------------------------------------------------------------
# Normalleştirme
# ----------------------------------------------------------------------

_KATLAMA = str.maketrans("çğıöşüâîû", "cgiosuaiu")
# Yalnızca Türkçeye özgü harfler. "İ" sayılmaz: Türkçe klavyede büyük harfle
# yazılan İngilizce kelimede de çıkar ("İDEA").
_TURKCE_HARFLER = set("çğıöşüÇĞÖŞÜ")
_BOSLUK = re.compile(r"\s+")
_KENAR = " \t\"'“”‘’.,;:!?()[]{}<>"


def tr_normal(metin):
    """Türkçe küçük harf: I -> ı, İ -> i; boşluklar teke iner."""
    metin = (metin or "").replace("I", "ı").replace("İ", "i").lower()
    return _BOSLUK.sub(" ", metin).strip(_KENAR)


def en_normal(metin):
    """İngilizce küçük harf; Türkçe klavyeden gelen ı/İ -> i."""
    metin = (metin or "").replace("İ", "i").replace("ı", "i").lower()
    return _BOSLUK.sub(" ", metin).strip(_KENAR)


def katla(metin):
    """Türkçe harfleri ASCII'ye katlar (aramada 'isik' = 'ışık')."""
    return tr_normal(metin).translate(_KATLAMA)


def turkce_harfli(metin):
    return any(h in _TURKCE_HARFLER for h in metin or "")


def _sozcukler(metin):
    return [s for s in re.split(r"[^\w]+", metin) if s]


# Yaygından nadire: CEFR sırası; seviyesiz en sonda.
CEFR_SIRASI = {seviye: i for i, seviye in enumerate(CEFR_LEVELS)}
_SEVIYESIZ_SIRA = len(CEFR_LEVELS)
_TUR_SIRASI = {kod: i for i, (kod, _) in enumerate(PartOfSpeech.choices)}


def cefr_sirasi(cefr):
    return CEFR_SIRASI.get(cefr, _SEVIYESIZ_SIRA)


def cefr_sira_ifadesi(alan="cefr"):
    """Veritabanında sıralamak için: A1=0 … C2=5, seviyesiz=6."""
    return Case(*[When(**{alan: s}, then=Value(i)) for s, i in CEFR_SIRASI.items()],
                default=Value(_SEVIYESIZ_SIRA), output_field=IntegerField())


def ortak_sozluk(onek=""):
    """Herkesin görebildiği kelimeler: kur (base) ya da herkese açık."""
    return Q(**{f"{onek}isBaseWord": True}) | Q(**{f"{onek}visibility": "public"})


def gorunur_kelimeler(user):
    """words.views.visible_words_qs ile aynı kural (arkadaş görünürlüğü yok)."""
    if user is None or not user.is_authenticated:
        return Word.objects.filter(ortak_sozluk())
    return Word.objects.filter(ortak_sozluk() | Q(owner=user) | Q(saved_by=user)).distinct()


def yaygin_sirala(kelimeler):
    """Word listesi: yaygın seviye önce, sonra tür sırası (isim, fiil, sıfat …)."""
    return sorted(kelimeler, key=lambda w: (cefr_sirasi(w.cefr), _TUR_SIRASI.get(w.pos, 99), w.id))


# ----------------------------------------------------------------------
# Süreç içi dizin (anlık öneri, Türkçe sorgu, yazım hatası)
# ----------------------------------------------------------------------

class _Dizin:
    """
    Ortak sözlüğün aramaya yarayan küçük özeti (16 bin kelime, 20 bin anlam:
    birkaç MB, kurulumu ~0,3 sn). Kelime/anlam eklenince, silinince ya da
    15 dakika geçince yeniden kurulur.
    """

    def __init__(self):
        kelimeler = list(Word.objects.filter(ortak_sozluk())
                         .values_list("id", "text", "pos", "cefr"))
        anlamlar = list(Meaning.objects.filter(ortak_sozluk("word__"))
                        .order_by("word_id", "sort_order", "id")
                        .values_list("word_id", "meaning_tr", "sort_order"))

        self.kelime = {}          # id -> (text, pos, cefr sırası)
        ilk_anlam = {}            # id -> ilk Türkçe anlam
        for wid, anlam, _ in anlamlar:
            ilk_anlam.setdefault(wid, anlam)

        # Yazım (küçük harf) -> en yaygın türün bilgisi: (cefr sırası, gösterim, anlam, cefr)
        self.metin = {}
        for wid, text, pos, cefr in yaygin_sirala_ham(kelimeler):
            self.kelime[wid] = (text, pos, cefr_sirasi(cefr))
            anahtar = en_normal(text)
            if anahtar not in self.metin:
                self.metin[anahtar] = (cefr_sirasi(cefr), text, ilk_anlam.get(wid, ""),
                                       cefr if cefr in CEFR_SIRASI else "")
        self.metinler = sorted(self.metin)                    # önek araması (bisect)
        self.uzunluga_gore = {}                               # yazım hatası adayları
        for m in self.metinler:
            self.uzunluga_gore.setdefault(len(m), []).append(m)

        # Türkçe anlamlar: katlanmış sözcük -> [(kelime id, anlam, sort_order, özgün sözcük)]
        self.anlamlar = []                                    # (wid, anlam, sira, katlanmış anlam)
        self.sozcuk = {}
        for wid, anlam, sira in anlamlar:
            if wid not in self.kelime or not anlam:
                continue
            normal = tr_normal(anlam)
            katli = normal.translate(_KATLAMA)
            no = len(self.anlamlar)
            self.anlamlar.append((wid, anlam, sira, katli))
            for s in set(_sozcukler(katli)):
                self.sozcuk.setdefault(s, []).append(no)
        self.sozcukler = sorted(self.sozcuk)

    # --- İngilizce önek ---------------------------------------------------

    def onek(self, en, en_cok=8):
        """Bu harflerle başlayan yazımlar: tam eşleşme önce, sonra yaygın, kısa."""
        bas = bisect.bisect_left(self.metinler, en)
        son = bisect.bisect_left(self.metinler, en + "￿")
        adaylar = self.metinler[bas:son]
        adaylar.sort(key=lambda m: (m != en, self.metin[m][0], len(m), m))
        return adaylar[:en_cok]

    # --- Türkçe anlam -----------------------------------------------------

    def turkce(self, sorgu, en_cok=30):
        """
        Türkçe anlamı sorguyla eşleşen kelimeler: [(kelime id, eşleşen anlam)].
        Anlamdaki bir sözcük sorguyla BAŞLAMALI ("bitir" -> "bitirmek"; "abitir" değil).
        Sıra: sözcük tam aynıysa (ya da -mek/-mak eklisiyse) önce, sonra ilk
        anlamda geçen, sonra yaygın seviye, sonra kısa kelime.
        """
        q = katla(sorgu)
        if len(q) < 2:
            return []
        tam = {q, q + "mek", q + "mak"}
        bulunan = {}   # wid -> (puan, anlam)

        def ekle(no, tam_mi):
            wid, anlam, sira, _ = self.anlamlar[no]
            text, _, cefr = self.kelime[wid]
            puan = (0 if tam_mi else 1, min(sira, 3), cefr, len(text), text)
            if wid not in bulunan or puan < bulunan[wid][0]:
                bulunan[wid] = (puan, anlam)

        if " " in q:
            desen = re.compile(r"(?<!\w)" + re.escape(q))
            for no, (_, _, _, katli) in enumerate(self.anlamlar):
                m = desen.search(katli)
                if m:
                    ekle(no, katli[m.end():m.end() + 1] in ("", ",", ";", " ", "("))
        else:
            bas = bisect.bisect_left(self.sozcukler, q)
            son = bisect.bisect_left(self.sozcukler, q + "￿")
            for s in self.sozcukler[bas:son][:400]:
                for no in self.sozcuk[s]:
                    ekle(no, s in tam)
        sirali = sorted(bulunan.items(), key=lambda kv: kv[1][0])
        return [(wid, anlam) for wid, (_, anlam) in sirali[:en_cok]]

    # --- Yazım hatası -----------------------------------------------------

    def benzer_yazimlar(self, en, en_cok=5):
        """16 bin yazımda: yalnızca uzunluğu ±2 olanlara difflib (hızlı)."""
        adaylar = [m for n in range(max(1, len(en) - 2), len(en) + 3)
                   for m in self.uzunluga_gore.get(n, ())]
        benzer = difflib.get_close_matches(en, adaylar, n=en_cok * 2, cutoff=0.75)
        # Aynı benzerlikte yaygın olan önce
        benzer.sort(key=lambda m: (-round(difflib.SequenceMatcher(None, en, m).ratio(), 2),
                                   self.metin[m][0]))
        return benzer[:en_cok]

    def benzer_turkce(self, sorgu, en_cok=5):
        q = katla(sorgu)
        adaylar = [s for s in self.sozcukler if abs(len(s) - len(q)) <= 2]
        sozcukler = difflib.get_close_matches(q, adaylar, n=3, cutoff=0.8)
        sonuc = []
        for s in sozcukler:
            for wid, anlam in self.turkce(s, en_cok=en_cok):
                if wid not in [w for w, _ in sonuc]:
                    sonuc.append((wid, anlam))
        return sonuc[:en_cok]


def yaygin_sirala_ham(satirlar):
    """(id, text, pos, cefr) satırları: yaygın seviye, tür sırası."""
    return sorted(satirlar, key=lambda r: (cefr_sirasi(r[3]), _TUR_SIRASI.get(r[2], 99), r[0]))


_dizin = None
_dizin_anahtari = None
_dizin_zamani = 0.0
_nesil = 0
_DIZIN_OMRU = 15 * 60


def _nesli_artir(**kwargs):
    global _nesil
    _nesil += 1


# Aynı süreçteki değişiklikler (admin, testler, betikler) dizini hemen eskitir.
# Başka süreçlerdeki değişiklikleri sayılar ve en büyük id yakalar; metni
# yerinde düzeltilen kelime en geç 15 dakikada yansır.
for _model in (Word, Meaning):
    post_save.connect(_nesli_artir, sender=_model, dispatch_uid=f"arama-dizini-{_model.__name__}")
    post_delete.connect(_nesli_artir, sender=_model, dispatch_uid=f"arama-dizini-sil-{_model.__name__}")


def dizin():
    """Güncel dizin (gerekirse yeniden kurulur). 2 küçük sorgu."""
    global _dizin, _dizin_anahtari, _dizin_zamani
    k = Word.objects.aggregate(n=Count("id"), m=Max("id"))
    a = Meaning.objects.aggregate(n=Count("id"), m=Max("id"))
    anahtar = (_nesil, k["n"], k["m"], a["n"], a["m"])
    if (_dizin is None or anahtar != _dizin_anahtari
            or time.monotonic() - _dizin_zamani > _DIZIN_OMRU):
        _dizin = _Dizin()
        _dizin_anahtari = anahtar
        _dizin_zamani = time.monotonic()
    return _dizin


# ----------------------------------------------------------------------
# Anlık öneri (autocomplete)
# ----------------------------------------------------------------------

def otomatik_oneri(sorgu, en_cok=8):
    """
    Yazarken açılan satırlar: [{"metin": "carpet", "anlam": "halı"}].
    Önce bu harflerle başlayan İngilizce kelimeler (yaygından nadire), yer
    kalırsa Türkçe anlamı bu harflerle başlayanlar ("bitir" -> finish · bitirmek).
    Her yazım bir kez; satıra dokununca /sozluk/<kelime>/ o kelimenin kartlarını açar.
    """
    en = en_normal(sorgu)
    if not en:
        return []
    d = dizin()
    satirlar = []
    if not turkce_harfli(sorgu):
        for m in d.onek(en, en_cok):
            _, text, anlam, cefr = d.metin[m]
            satirlar.append({"metin": text, "anlam": anlam, "cefr": cefr})
    if len(satirlar) < en_cok and len(en) >= 2:
        gorulen = {s["metin"].lower() for s in satirlar}
        for wid, anlam in d.turkce(sorgu, en_cok * 3):
            text = d.kelime[wid][0]
            if text.lower() in gorulen:
                continue
            gorulen.add(text.lower())
            satirlar.append({"metin": text, "anlam": anlam,
                             "cefr": d.metin[en_normal(text)][3], "turkce": True})
            if len(satirlar) >= en_cok:
                break
    return satirlar


# ----------------------------------------------------------------------
# Tam arama
# ----------------------------------------------------------------------

# "went, go kelimesinin geçmiş hâli" — çekim türüne göre
CEKIM_ADLARI = {
    FormKind.PAST: gettext_lazy("geçmiş hâli"),
    FormKind.PAST_PARTICIPLE: gettext_lazy("3. hâli"),
    FormKind.PRESENT_PARTICIPLE: gettext_lazy("-ing hâli"),
    FormKind.PLURAL: gettext_lazy("çoğulu"),
    FormKind.THIRD_PERSON: gettext_lazy("-s almış hâli"),
    FormKind.COMPARATIVE: gettext_lazy("karşılaştırma hâli (-er)"),
    FormKind.SUPERLATIVE: gettext_lazy("en üstünlük hâli (-est)"),
    FormKind.OTHER: gettext_lazy("bir biçimi"),
}

DIGER_EN_COK = 8


@dataclass
class AramaSonucu:
    sorgu: str
    kelimeler: list = field(default_factory=list)       # tam eşleşme ya da çekimden kök (Word)
    cekim_notlari: list = field(default_factory=list)   # ["went, go kelimesinin geçmiş hâli"]
    ifadeler: list = field(default_factory=list)        # ifade tam eşleşmesi (Expression)
    digerleri: list = field(default_factory=list)       # satır sözlükleri (bkz. _satir)
    turkce: list = field(default_factory=list)          # [(kelime id, eşleşen anlam)]
    oneriler: list = field(default_factory=list)        # satır sözlükleri

    @property
    def bulundu(self):
        return bool(self.kelimeler or self.ifadeler or self.turkce)

    @property
    def bulunamadi(self):
        return not (self.bulundu or self.digerleri or self.oneriler)


def _ilk_anlam(word):
    anlamlar = list(word.meanings.all())
    return anlamlar[0].meaning_tr if anlamlar else ""


def _satir(word=None, ifade=None):
    """'carpet · isim · halı · B1' satırı. Kelimeye dokununca kartı yerinde açılır."""
    from .kart import tur_etiketi
    if ifade is not None:
        return {"metin": ifade.text, "tur": "ifade", "anlam": ifade.meaning_tr,
                "cefr": ifade.cefr if ifade.cefr in CEFR_SIRASI else "", "id": None}
    return {"metin": word.text, "tur": tur_etiketi(word.pos), "anlam": _ilk_anlam(word),
            "cefr": word.cefr if word.cefr in CEFR_SIRASI else "", "id": word.id}


def _kelime_gecen(alan, en):
    """Çok sözcüklü metinde en bir sözcük olarak geçiyor: 'aim at', 'take aim'."""
    return (Q(**{f"{alan}__istartswith": en + " "}) | Q(**{f"{alan}__icontains": " " + en + " "})
            | Q(**{f"{alan}__iendswith": " " + en}))


def _digerleri(user, en):
    """≤8 satır: bu harflerle başlayanlar (yaygından nadire), sonra içinde geçen ifadeler."""
    if len(en) < 2:
        return []
    kelimeler = gorunur_kelimeler(user)
    onekli = list(kelimeler.filter(text__istartswith=en).exclude(text__iexact=en)
                  .exclude(text__contains=" ")
                  .annotate(_sira=cefr_sira_ifadesi(), _uzunluk=Length("text"))
                  .order_by("_sira", "_uzunluk", "text", "pos")
                  .prefetch_related("meanings")[:DIGER_EN_COK])
    ifadeler = []
    if " " not in en:
        ifadeler = [_satir(word=w) for w in kelimeler.filter(text__contains=" ")
                    .filter(_kelime_gecen("text", en))
                    .annotate(_sira=cefr_sira_ifadesi())
                    .order_by("_sira", "text").prefetch_related("meanings")[:DIGER_EN_COK]]
        ifadeler += [_satir(ifade=e) for e in Expression.objects.filter(visibility="public")
                     .filter(Q(text__iexact=en) | _kelime_gecen("text", en))
                     .exclude(text__iexact=en)
                     .annotate(_sira=cefr_sira_ifadesi()).order_by("_sira", "text")[:DIGER_EN_COK]]
    # İfadeler de görünsün: önekliler en çok 6 yer alır, boş kalan yer doldurulur.
    ifade_payi = min(len(ifadeler), 2)
    satirlar = [_satir(word=w) for w in onekli[:DIGER_EN_COK - ifade_payi]]
    satirlar += ifadeler[:DIGER_EN_COK - len(satirlar)]
    return satirlar


def ara(user, sorgu):
    """Arama sayfasının bütün dalları; bkz. modül açıklaması."""
    en = en_normal(sorgu)
    sonuc = AramaSonucu(sorgu=sorgu)
    if not en:
        return sonuc
    kelimeler = gorunur_kelimeler(user)
    turkce_mi = turkce_harfli(sorgu)

    # 1) İngilizce tam eşleşme: her tür ayrı kart
    if not turkce_mi:
        sonuc.kelimeler = yaygin_sirala(kelimeler.filter(text__iexact=en))
        sonuc.ifadeler = [ifade_hazirla(e) for e in Expression.objects
                          .filter(visibility="public", text__iexact=en).prefetch_related("examples")]

    # 2) Çekimli hâl -> kök (went -> go, children -> child)
    if not turkce_mi and not sonuc.kelimeler and not sonuc.ifadeler:
        bicimler = list(WordForm.objects.filter(surface__iexact=en)
                        .exclude(word__text__iexact=en)
                        .filter(word__in=kelimeler).select_related("word"))
        kokler = yaygin_sirala({b.word for b in bicimler})
        sonuc.kelimeler = kokler
        turler = {}
        for b in bicimler:
            turler.setdefault(b.word.text, [])
            ad = CEKIM_ADLARI.get(b.kind, CEKIM_ADLARI[FormKind.OTHER])
            if ad not in turler[b.word.text]:
                turler[b.word.text].append(ad)
        yazim = sorgu.strip()
        sonuc.cekim_notlari = [_("%(yazim)s, %(kok)s kelimesinin %(adlar)s") % {
                                   "yazim": yazim, "kok": kok, "adlar": " / ".join(str(a) for a in adlar)}
                               for kok, adlar in turler.items()]

    # 3) Türkçe sorgu: bu anlama sahip kelimeler
    if (turkce_mi or not (sonuc.kelimeler or sonuc.ifadeler)) and len(en) >= 2:
        sonuc.turkce = dizin().turkce(sorgu, en_cok=30)

    # 4) Diğer sonuçlar (İngilizce sorguda)
    if not turkce_mi:
        sonuc.digerleri = _digerleri(user, en)

    # 5) Hiçbiri yoksa: yazım hatası önerileri
    if not (sonuc.bulundu or sonuc.digerleri):
        sonuc.oneriler = yazim_onerileri(sorgu)
    return sonuc


def kelime_sayfasi(user, slug):
    """
    /sozluk/<slug>/ sayfasının içeriği (rapor 18.15): o yazımın bütün türleri
    (her biri ayrı kart), aynı adresteki ifadeler ve "Diğer sonuçlar".
    Böyle bir kelime de ifade de yoksa None.
    """
    kelimeler = yaygin_sirala(gorunur_kelimeler(user).filter(slug=slug))
    ifadeler = [ifade_hazirla(e) for e in Expression.objects
                .filter(visibility="public", slug=slug).prefetch_related("examples")]
    if not kelimeler and not ifadeler:
        return None
    metin = kelimeler[0].text if kelimeler else ifadeler[0].text
    sonuc = AramaSonucu(sorgu=metin, kelimeler=kelimeler, ifadeler=ifadeler)
    sonuc.digerleri = _digerleri(user, en_normal(metin))
    return sonuc


def tam_eslesme_slug(sonuc):
    """Arama tam bir kelimeyi ya da ifadeyi bulduysa onun adresi (slug); yoksa ''."""
    if sonuc.cekim_notlari:
        return ""          # went -> go: sayfa go'nun, adres went'in değil
    if sonuc.kelimeler:
        return sonuc.kelimeler[0].slug
    if sonuc.ifadeler:
        return sonuc.ifadeler[0].slug
    return ""


def yazim_onerileri(sorgu, en_cok=5):
    """'recieve' -> receive … Önce İngilizce yazımlar, yoksa Türkçe anlamlar."""
    d = dizin()
    satirlar = []
    if not turkce_harfli(sorgu):
        for m in d.benzer_yazimlar(en_normal(sorgu), en_cok):
            _, text, anlam, cefr = d.metin[m]
            satirlar.append({"metin": text, "anlam": anlam, "cefr": cefr, "tur": "", "id": None})
    if not satirlar:
        for wid, anlam in d.benzer_turkce(sorgu, en_cok):
            text = d.kelime[wid][0]
            satirlar.append({"metin": text, "anlam": anlam, "cefr": d.metin[en_normal(text)][3],
                             "tur": "", "id": None})
    return satirlar[:en_cok]


# ----------------------------------------------------------------------
# Bulunamayan aramaların kaydı
# ----------------------------------------------------------------------

# Tablo sınırsız büyümesin (8 Ekim): girişsiz bir döngü her yeni sorguda satır açabiliyordu.
BULUNAMAYAN_ADRES_SAATTE = 30      # bir adresin saatte açabileceği YENİ satır
BULUNAMAYAN_GUNDE = 2000           # bütün site, günde yeni satır
BULUNAMAYAN_EN_COK = 50000         # tablo bu boyutu geçince yeni satır açılmaz


def _yeni_satir_acilabilir(istemci):
    from django.core.cache import cache
    from LearnVocab import sinir
    toplam = cache.get_or_set("bulunamayan:toplam", BulunamayanArama.objects.count, 600)
    if toplam >= BULUNAMAYAN_EN_COK:
        return False
    if istemci and sinir.asildi(f"bulunamayan:{istemci}", BULUNAMAYAN_ADRES_SAATTE, 3600):
        return False
    return not sinir.asildi("bulunamayan:gun", BULUNAMAYAN_GUNDE, 24 * 3600)


def bulunamayan_kaydet(sorgu, kaynak=BulunamayanArama.KAYNAK_SOZLUK, oneri_vardi=False, istemci=None):
    """
    Aynı sorgu (küçük harf) tek satır, sayaç artar. Harf içermeyen ya da çok
    uzun sorgular yazılmaz. Okumalar da kullanabilir: kaynak="okuma".
    YENİ satır adres başına, günlük ve toplam sınırla açılır (yukarıdaki sabitler);
    var olan satırın sayacı her zaman artar.
    """
    from django.db.models import F
    anahtar = tr_normal(sorgu) if turkce_harfli(sorgu) else en_normal(sorgu)
    if not anahtar or len(anahtar) > 60 or not re.search(r"[^\W\d_]", anahtar):
        return
    guncellenen = (BulunamayanArama.objects.filter(sorgu=anahtar, kaynak=kaynak)
                   .update(sayi=F("sayi") + 1, son=timezone.now(), oneri_vardi=oneri_vardi))
    if not guncellenen and _yeni_satir_acilabilir(istemci):
        BulunamayanArama.objects.get_or_create(sorgu=anahtar, kaynak=kaynak,
                                               defaults={"oneri_vardi": oneri_vardi})


# Günün kelimesi ve günün ifadesi: words/gunun.py (rapor 18.8).
# Kullanıcının seviyesi tek kaynaktan: users.seviye.kullanici_seviyesi
# (User.cefr, yoksa B1). Yukarıda import edildi.


def ifade_hazirla(ifade):
    """İfade kartı için: ilk örnek cümle (doğru/yanlış noktalama örnekleri değil)."""
    from .models import ExampleKind
    ifade.ilk_ornek = next((o.text for o in ifade.examples.all()
                            if o.kind == ExampleKind.EXAMPLE), "")
    return ifade

