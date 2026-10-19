"""
Kelime kartının verisi (ürün raporu 4.3 — sitenin en önemli bileşeni).

Aynı kart her yerde kullanılıyor: Sözlük (Keşfet), Listem, günün kelimesi.
Şablon: templates/base/_kelimeKarti.html. Bu modül kartı veritabanından
SABİT sayıda sorguyla hazırlar; kart sayısı arttıkça sorgu sayısı artmaz
(N+1 yok). Şablon ek sorgu yapmaz: her şey burada hazırlanır.

    from words.kart import kart_verisi
    kartlar = kart_verisi(kelimeler, request.user)
    {% for kart in kartlar %}{% include 'base/_kelimeKarti.html' %}{% endfor %}

`kelimeler`: Word nesneleri, id'ler ya da bir queryset. Sıra korunur,
tekrarlar atılır. Görünürlük (başkasının gizli kelimesi) ÇAĞIRANIN işi:
kart_verisi'ne yalnızca kullanıcının görebileceği kelimeler verilmeli
(bkz. words.views.visible_words_qs). Kartın kendi içinde gösterdiği diğer
kelimeler (ilişki çipleri, aile) yalnızca ortak sözlükten gelir.
"""

from dataclasses import dataclass, field

from django.db.models import Prefetch, Q
from django.utils.translation import gettext_lazy as _

from usersettings.anlam import turkce_acik

from . import inflect
from .konular import konu_bilgisi
from .models import (
    Collocation, ExampleSentence, Meaning, PartOfSpeech, UsagePattern, UserWordLink,
    Word, WordRelation,
)


# Tür etiketleri (rapor 12.1: gramer etiketleri YALNIZCA Sözlük kartında).
# Arayüz diline göre çevrilir (rapor 18.22); PartOfSpeech'in kendi etiketleri
# yönetim paneli içindir.
TUR_ETIKETLERI = {
    PartOfSpeech.NOUN: _("isim"), PartOfSpeech.VERB: _("fiil"), PartOfSpeech.ADJECTIVE: _("sıfat"),
    PartOfSpeech.ADVERB: _("zarf"), PartOfSpeech.PHRASAL_VERB: _("phrasal verb"),
    PartOfSpeech.PREPOSITION: _("edat"), PartOfSpeech.CONJUNCTION: _("bağlaç"),
    PartOfSpeech.PRONOUN: _("zamir"), PartOfSpeech.DETERMINER: _("belirleyici"),
    PartOfSpeech.MODAL_VERB: _("yardımcı fiil"), PartOfSpeech.EXCLAMATION: _("ünlem"),
}

# Kartta seviye rozeti gösterilmeyen değer.
_SEVIYESIZ = "Belirtilmemiş"


def tur_etiketi(pos):
    """noun -> isim, verb -> fiil … Bilinmeyen değer olduğu gibi döner."""
    return TUR_ETIKETLERI.get(pos, pos or "")


def _ortak_sozluk(onek=""):
    """Herkesin görebildiği kelimeler: kur (base) ya da herkese açık."""
    return Q(**{f"{onek}isBaseWord": True}) | Q(**{f"{onek}visibility": "public"})


@dataclass
class KartAnlami:
    anlam: Meaning
    meaning_tr: str
    definition: str
    ornek: str                                   # kartta görünen tek örnek
    diger_ornekler: list = field(default_factory=list)   # "› Daha fazla örnek"
    kaliplar: list = field(default_factory=list)          # "› Kalıplar": {metin, anlam, ornek}
    iliski_satirlari: list = field(default_factory=list)  # [("Benzer", [Word…]), …]
    konular: list = field(default_factory=list)           # anlamın konuları (rapor 18.39): words.konular.konu_bilgisi


@dataclass
class Kart:
    kelime: Word
    id: int
    text: str
    pos: str
    tur: str                  # Türkçe tür etiketi
    cefr: str                 # boş olabilir
    v2: str                   # yalnızca düzensiz fiilde dolu
    v3: str
    listede: bool
    anlamlar: list
    aile: list                # aynı ailedeki diğer kelimeler (Word), yazımı farklı olanlar
    # Türkçe sorguda ("bitir") kapalı kartta vurgulanan anlam; o anlamın
    # açıklaması da tek satır olarak altında görünür (rapor 4.2).
    eslesen: str = ""
    # Kapalı kartın özetinde ilk anlam yerine gösterilecek anlam (konu sayfası: o konuya bağlı
    # anlam — lap Spor'da "tur, çevrim"; Efe, 17 Ekim). 0 ise ilk anlam.
    ozet_anlam_id: int = 0
    # Az kullanılan kelime (Word.az_kullanilan): seviye rozeti yok, açık kartta "az kullanılan" yazar
    az_kullanilan: bool = False

    @property
    def eslesen_tanim(self):
        """Eşleşen Türkçe anlamın İngilizce açıklaması (yoksa ilk anlamınki)."""
        for a in self.anlamlar:
            if a.meaning_tr == self.eslesen:
                return a.definition
        return self.anlamlar[0].definition if self.anlamlar else ""

    @property
    def ozet(self):
        """Kapalı kartın tek satırı için ilk anlam (ya da ozet_anlam_id'deki): 'aim · fiil · hedeflemek · B1'
        (Türkçe kapalıysa açıklama)."""
        if not self.anlamlar:
            return ""
        a = next((a for a in self.anlamlar if a.anlam.id == self.ozet_anlam_id), self.anlamlar[0])
        return a.meaning_tr or a.definition

    @property
    def duzensiz(self):
        return bool(self.v2 or self.v3)


def _kelime_sorgusu(idler):
    """Kart için gereken her şey tek seferde: 1 + 7 sorgu."""
    iliski_turleri = [tur for tur, _ in Meaning.ILISKI_SATIRLARI]
    anlamlar = Meaning.objects.order_by("sort_order", "id").prefetch_related(
        Prefetch("examples", queryset=ExampleSentence.objects.order_by("sort_order", "id")),
        Prefetch("collocations", queryset=Collocation.objects.order_by("sort_order", "id")),
        Prefetch("patterns", queryset=UsagePattern.objects.order_by("sort_order", "id")),
        "categories",                                     # konular (rapor 18.39)
        # Meaning.iliski_satirlari() self.relations.all() üzerinden grupluyor;
        # bu önbellek onu besliyor. Yalnızca kartta görünen üç tür ve ortak
        # sözlükteki hedefler.
        Prefetch("relations", queryset=(
            WordRelation.objects
            .filter(type__in=iliski_turleri)
            .filter(_ortak_sozluk("to_word__"))
            .select_related("to_word")
            .order_by("id")
        )),
    )
    aile = (Word.objects.filter(_ortak_sozluk())
            .only("id", "text", "pos", "family_id").order_by("text", "pos"))
    return (Word.objects.filter(pk__in=idler)
            .select_related("family")
            .prefetch_related(
                Prefetch("meanings", queryset=anlamlar),
                Prefetch("family__words", queryset=aile, to_attr="kart_aile"),
            ))


def _kaliplar(anlam):
    """Collocation'lar ve kullanım kalıpları birlikte (rapor 4.3, madde 4)."""
    kaliplar = [{"metin": c.pattern, "anlam": c.meaning_tr or "", "ornek": c.example or ""}
                for c in anlam.collocations.all()]
    kaliplar += [{"metin": k.pattern, "anlam": "", "ornek": k.example or ""}
                 for k in anlam.patterns.all()]
    return kaliplar


def _kart_anlami(anlam):
    ornekler = [o.text for o in anlam.examples.all()]
    return KartAnlami(
        anlam=anlam,
        meaning_tr=anlam.meaning_tr,
        definition=anlam.definition or "",
        ornek=ornekler[0] if ornekler else "",
        diger_ornekler=ornekler[1:],
        kaliplar=_kaliplar(anlam),
        iliski_satirlari=anlam.iliski_satirlari(),
        konular=sorted((konu_bilgisi(k) for k in anlam.categories.all()), key=lambda k: k["ad"]),
    )


def _aile(kelime):
    """Ailedeki diğer kelimeler: aynı yazımlı olanlar (aim isim/fiil) hariç, tekrarsız, kök önce."""
    aile = getattr(kelime.family, "kart_aile", None) or []
    kok = kelime.family.root.lower()
    gorulen = {kelime.text.lower()}
    uyeler = []
    for uye in sorted(aile, key=lambda w: (w.text.lower() != kok, w.text.lower())):
        anahtar = uye.text.lower()
        if anahtar not in gorulen:
            gorulen.add(anahtar)
            uyeler.append(uye)
    return uyeler


def kart_verisi(kelimeler, user=None):
    """
    Kelimelerden kart listesi (list[Kart]) üretir, verilen sırayla.

    Sorgu sayısı sabit: kelimeler + anlamlar + örnekler + collocation'lar +
    kalıplar + ilişkiler + konular + aile (+ girişliyse liste durumu) = en çok 9.
    Queryset verilirse onu değerlendirmek için +1.
    """
    idler = list(dict.fromkeys(k.pk if isinstance(k, Word) else int(k) for k in kelimeler))
    if not idler:
        return []

    kelime_by_id = {w.pk: w for w in _kelime_sorgusu(idler)}

    listede = set()
    if user is not None and user.is_authenticated:
        listede = set(UserWordLink.objects.filter(user=user, word_id__in=idler)
                      .values_list("word_id", flat=True))

    kartlar = []
    for pk in idler:
        kelime = kelime_by_id.get(pk)
        if kelime is None:
            continue
        duzensiz = (kelime.pos in (PartOfSpeech.VERB, PartOfSpeech.PHRASAL_VERB)
                    and inflect.duzensiz_fiil_mi(kelime.text, kelime.v2Form, kelime.v3Form))
        kartlar.append(Kart(
            kelime=kelime,
            id=kelime.pk,
            text=kelime.text,
            pos=kelime.pos,
            tur=tur_etiketi(kelime.pos),
            cefr="" if kelime.cefr in ("", None, _SEVIYESIZ) or kelime.az_kullanilan else kelime.cefr,
            az_kullanilan=kelime.az_kullanilan,
            v2=(kelime.v2Form or "") if duzensiz else "",
            v3=(kelime.v3Form or "") if duzensiz else "",
            listede=pk in listede,
            anlamlar=[_kart_anlami(a) for a in kelime.meanings.all()],
            aile=_aile(kelime),
        ))
    if user is not None and not turkce_acik(user):
        # "Türkçe anlamlar" kapalı (rapor 18.22): Türkçe boşalır, şablonlar İngilizce açıklamaya düşer.
        for kart in kartlar:
            kart.eslesen = ""
            for a in kart.anlamlar:
                a.meaning_tr = ""
                for k in a.kaliplar:
                    k["anlam"] = ""
    return kartlar
