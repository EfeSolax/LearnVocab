"""
Listem (ürün raporu 5): kullanıcının "+" ile eklediği kelimelerin cep defteri.

Aşırı basit: satırda kelime (+ renkli seviye etiketi), numaralı Türkçe
anlamlar ve "Listemden çıkar".
İstatistik, durum, seviye filtresi YOK (rapor 17).

Süzgeçler (tek "Filtre" düğmesinin içinde):
    sira  : yeni (varsayılan) · eski · az
    zaman : tumu (varsayılan) · hafta · ay
    zor   : 1 -> Zorlandıklarım: L&P'de "bilmiyorum" dediği / bildiğini sanıp
            yanıldığı ya da egzersizde yanlış yaptığı; son sonuç (learnpass.WordEncounter)
            ya da egzersizde yanlış yaptığı (UserWordLink.wrongCount > 0).
    ara   : listede ara (İngilizce yazım ya da Türkçe anlam)

Sayfalama: 50'şer satır; "Daha fazla göster" sonraki parçayı getirir.
"Tümünü seç" o anki süzgece uyan BÜTÜN kelimeleri seçer (yüklenmemiş
sayfalar dahil) — sayfaya bunların id'leri gömülür.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db.models import Case, Count, Exists, OuterRef, Prefetch, Q, Value, When
from django.db.models import DateTimeField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .arama import en_normal, gorunur_kelimeler, tr_normal
from usersettings.anlam import turkce_acik

from .kart import tur_etiketi
from .models import Meaning, UserWordLink

SIRALAR = {"yeni": _("En yeni"), "eski": _("En eski"), "az": "A→Z"}
ZAMANLAR = {"tumu": _("Tümü"), "hafta": _("Son 1 hafta"), "ay": _("Son 1 ay")}
_ZAMAN_GUN = {"hafta": 7, "ay": 30}
SAYFA_BOYU = 50
TOPLU_EN_COK = 2000


@dataclass
class ListemDurumu:
    ara: str = ""
    sira: str = "yeni"
    zaman: str = "tumu"
    zor: bool = False
    sayfa: int = 1

    @property
    def filtre_var(self):
        """Filtre düğmesindeki nokta: varsayılandan farklı bir seçim var mı."""
        return self.sira != "yeni" or self.zaman != "tumu" or self.zor

    def parametreler(self, **degisen):
        """Adres parametreleri (varsayılanlar yazılmaz)."""
        d = {"ara": self.ara, "sira": self.sira, "zaman": self.zaman,
             "zor": "1" if self.zor else "", "sayfa": self.sayfa}
        d.update(degisen)
        cikti = {"sekme": "listem"}
        for k, v in d.items():
            if v in ("", None, False) or (k, v) in (("sira", "yeni"), ("zaman", "tumu"), ("sayfa", 1)):
                continue
            cikti[k] = v
        return cikti


def durum(get):
    """request.GET -> ListemDurumu (geçersiz değerler varsayılana döner)."""
    try:
        sayfa = max(1, int(get.get("sayfa") or 1))
    except ValueError:
        sayfa = 1
    sira = get.get("sira")
    zaman = get.get("zaman")
    return ListemDurumu(
        ara=(get.get("ara") or "").strip()[:80],
        sira=sira if sira in SIRALAR else "yeni",
        zaman=zaman if zaman in ZAMANLAR else "tumu",
        zor=get.get("zor") == "1",
        sayfa=sayfa,
    )


def zorlandiklarim_q(user):
    """
    Zorlandıklarım (rapor 18.2): son sonucu "bilemedi" olan kelimeler — L&P'de
    bilmiyorum / yanılmışım ya da egzersizde yanlış; sonra bilinirse çıkar.
    """
    from learnpass.models import WordEncounter
    zor = WordEncounter.objects.filter(user=user, word=OuterRef("word"),
                                       son_basarili=False, times_seen__gt=0)
    return Q(Exists(zor))


def baglar(user, d):
    """Süzgeçlenmiş ve sıralanmış UserWordLink queryset'i."""
    qs = UserWordLink.objects.filter(user=user)
    if d.zaman in _ZAMAN_GUN:
        qs = qs.filter(dateAdded__gte=timezone.now() - timedelta(days=_ZAMAN_GUN[d.zaman]))
    if d.zor:
        qs = qs.filter(zorlandiklarim_q(user))
    if d.ara:
        en, tr = en_normal(d.ara), tr_normal(d.ara)
        eslesen = (UserWordLink.objects.filter(user=user)
                   .filter(Q(word__text__icontains=en) | Q(word__meanings__meaning_tr__icontains=tr))
                   .values("id"))
        qs = qs.filter(id__in=eslesen)
    if d.sira == "eski":
        return qs.order_by("dateAdded", "id")
    if d.sira == "az":
        return qs.order_by("word__text", "word__pos", "id")
    return qs.order_by("-dateAdded", "-id")


@dataclass
class ListemSatiri:
    bag: UserWordLink
    id: int                 # kelime id
    text: str
    tur: str                # yalnızca aynı yazımın iki türü listedeyse dolu
    anlamlar: list          # Türkçe anlamlar (numaralı gösterilir)
    cefr: str = ""          # renkli seviye etiketi


def satirlar(user, d):
    """(satırlar, toplam, sonraki sayfa var mı). Sorgu sayısı sabit: 4."""
    qs = baglar(user, d)
    toplam = qs.count()
    bas = (d.sayfa - 1) * SAYFA_BOYU
    sayfa = list(qs.select_related("word").prefetch_related(
        Prefetch("word__meanings", queryset=Meaning.objects.order_by("sort_order", "id")
                 .only("id", "word_id", "meaning_tr", "definition", "sort_order")))[bas:bas + SAYFA_BOYU])
    turkce = turkce_acik(user)
    iki_turlu = set()
    if sayfa:
        iki_turlu = set(UserWordLink.objects.filter(user=user)
                        .values("word__text").annotate(n=Count("id")).filter(n__gt=1)
                        .values_list("word__text", flat=True))
    sonuc = [ListemSatiri(bag=b, id=b.word_id, text=b.word.text,
                          tur=tur_etiketi(b.word.pos) if b.word.text in iki_turlu else "",
                          anlamlar=_anlamlar(b.word, turkce),
                          cefr="" if b.word.az_kullanilan else (b.word.cefr or ""))
             for b in sayfa]
    return sonuc, toplam, bas + len(sayfa) < toplam


def _anlamlar(word, turkce=True):
    """Satırdaki numaralı anlamlar: Türkçe; "Türkçe anlamlar" kapalıysa İngilizce açıklama."""
    if turkce:
        return [m.meaning_tr for m in word.meanings.all() if m.meaning_tr]
    return [m.definition for m in word.meanings.all() if m.definition]


def tum_kelime_idleri(user, d):
    """"Tümünü seç" için: o anki süzgece uyan bütün kelimeler (sayfa sınırı yok)."""
    return list(baglar(user, d).values_list("word_id", flat=True)[:TOPLU_EN_COK])


def oneri(user, sorgu, en_cok=8):
    """Listem'in anlık önerisi: YALNIZCA listedeki kelimelerden, İngilizce ya da Türkçe anlamla."""
    en, tr = en_normal(sorgu), tr_normal(sorgu)
    if not en:
        return []
    qs = (UserWordLink.objects.filter(user=user)
          .filter(Q(word__text__icontains=en) | Q(word__meanings__meaning_tr__icontains=tr))
          .select_related("word").prefetch_related("word__meanings").distinct()
          .annotate(_bas=Case(When(word__text__istartswith=en, then=Value(0)), default=Value(1)))
          .order_by("_bas", "word__text")[:en_cok * 2])
    satirlar_, gorulen = [], set()
    for bag in qs:
        w = bag.word
        if w.text.lower() in gorulen:
            continue
        gorulen.add(w.text.lower())
        anlamlar = [m.meaning_tr for m in w.meanings.all() if m.meaning_tr]
        eslesen = next((a for a in anlamlar if tr in tr_normal(a)), None)
        if not turkce_acik(user):
            tanimlar = _anlamlar(w, False)
            eslesen, anlamlar = None, [t[:60] for t in tanimlar]
        satirlar_.append({"metin": w.text, "anlam": eslesen or (anlamlar[0] if anlamlar else "")})
        if len(satirlar_) >= en_cok:
            break
    return satirlar_


# ----------------------------------------------------------------------
# Toplu çıkar ve "Geri al"
# ----------------------------------------------------------------------

def _idler(ham):
    idler = []
    for v in ham or []:
        try:
            idler.append(int(v))
        except (TypeError, ValueError):
            continue
    return list(dict.fromkeys(idler))[:TOPLU_EN_COK]


def toplu_cikar(user, kelime_idleri):
    """Seçilenleri çıkarır; "Geri al" için eklenme tarihi ve sayaçları döner."""
    qs = UserWordLink.objects.filter(user=user, word_id__in=_idler(kelime_idleri))
    geri = [{"word": b.word_id, "dateAdded": b.dateAdded.isoformat(),
             "correctCount": b.correctCount, "wrongCount": b.wrongCount} for b in qs]
    qs.delete()
    # Çıkarılan kelime L&P tekrarından da çıkar (Efe, 20 Ekim)
    from learnpass.tekrar import takipten_cikar
    takipten_cikar(user, [g["word"] for g in geri])
    return geri


def toplu_geri_yukle(user, geri):
    """
    Toplu çıkarmanın "Geri al"ı: bağlar eklenme tarihleri ve sayaçlarıyla geri
    konur (yoksa "en yeni" sırası ve Zorlandıklarım bozulurdu). Gelecekten
    tarih, saat dilimsiz tarih ve kullanıcının göremediği kelime kabul edilmez.
    Sorgu sayısı sabit: 4.
    """
    simdi = timezone.now()
    kayitlar = {}
    for oge in (geri or [])[:TOPLU_EN_COK]:
        try:
            wid = int(oge["word"])
            tarih = datetime.fromisoformat(oge["dateAdded"])
            dogru = max(0, int(oge.get("correctCount", 0)))
            yanlis = max(0, int(oge.get("wrongCount", 0)))
        except (TypeError, ValueError, KeyError, AttributeError):
            continue
        if timezone.is_naive(tarih):
            continue
        kayitlar[wid] = (min(tarih, simdi), dogru, yanlis)
    if not kayitlar:
        return 0
    gorunur = set(gorunur_kelimeler(user).filter(id__in=kayitlar).values_list("id", flat=True))
    mevcut = set(UserWordLink.objects.filter(user=user, word_id__in=gorunur)
                 .values_list("word_id", flat=True))
    yeni = [wid for wid in kayitlar if wid in gorunur and wid not in mevcut]
    if not yeni:
        return 0
    UserWordLink.objects.bulk_create([UserWordLink(user=user, word_id=w) for w in yeni],
                                     ignore_conflicts=True)
    # auto_now_add oluştururken tarihi ezer; tek UPDATE ile geri yazılır
    # (çok seçimde 300'lük parçalar: SQL parametre sınırı).
    for i in range(0, len(yeni), 300):
        parca = yeni[i:i + 300]
        UserWordLink.objects.filter(user=user, word_id__in=parca).update(
            dateAdded=Case(*[When(word_id=w, then=Value(kayitlar[w][0])) for w in parca],
                           output_field=DateTimeField()),
            correctCount=Case(*[When(word_id=w, then=Value(kayitlar[w][1])) for w in parca]),
            wrongCount=Case(*[When(word_id=w, then=Value(kayitlar[w][2])) for w in parca]),
        )
    return len(yeni)


def json_govdesi(request):
    """fetch ile gelen JSON gövdesi (bozuksa boş sözlük)."""
    try:
        return json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        return {}
