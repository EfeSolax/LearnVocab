"""
Kelime sorgulama (rapor 8 ve 11): okurken dokunulan kelimenin anlamı.

Okuma ekranındaki baloncuk ve ileride Chrome eklentisi aynı sonucu kullanır
(api.py bunu JSON olarak verir). Kullanıcıdan BAĞIMSIZDIR: kimin sorduğu
fark etmez, bu yüzden sunucu önbelleğine yazılabilir. "Listemde mi?"
bilgisi ayrı, üstüne eklenir (api.listede_ekle).

Sıra:
  1. Yazım temizlenir: "Decided," -> decided, "government's" -> government.
  2. Kök: `WordForm` (decided -> decide, went -> go, children -> child).
     Çekimden gelen kök önce gelir; yazımın kendisi de bir sözlük maddesiyse
     (decided · sıfat) o da `digerleri`nde döner.
     WordForm'da yoksa küçük bir kural denemesi (-s, -ed, -ing …) yapılır.
  3. Aynı yazımın bütün türleri tek listede: bank · isim + bank · fiil.
     Anlamlar kısa ve numaralı gösterilir, en yaygın üstte (sort_order).
     Yapay zekâyla bağlamdan anlam SEÇİLMEZ (rapor 17).
  4. Phrasal verb: dokunulan kelimenin çevresindeki birkaç kelime (once /
     sonra) verilirse "gave it up" -> give up yakalanır. Araya en çok bir
     kelime girebilir (words/extract/phrasal.py ile aynı kural).

Sorgu sayısı sabit: çekimler 1, kelimeler + anlamlar 2, phrasal + anlamlar
2 (yalnızca aday varsa). Sayfadaki kelimeler tek tek SORGULANMAZ; yalnızca
dokunulan kelime.
"""

import hashlib
import re

from django.core.cache import cache
from django.db.models import Prefetch, Q

from words.extract.phrasal import PARCACIKLAR
from words.models import FormKind, Meaning, PartOfSpeech, Word, WordForm


# Sonuçlar sunucu önbelleğinde bu kadar kalır. Sözlük sık değişmiyor;
# değişse bile en kötü ihtimalle bir gün eski anlam görünür.
ONBELLEK_SURESI = 60 * 60 * 24
ONBELLEK_SURUMU = 1          # sonuç biçimi değişirse artır

# Baloncuk küçük kalsın: bir kelimede en çok bu kadar anlam.
EN_COK_ANLAM = 8

# Dokunulan kelimenin önünden / arkasından en çok kaç kelime dikkate alınır.
BAGLAM_ONCE = 2
BAGLAM_SONRA = 3

_PARCACIK = frozenset(PARCACIKLAR)

# Tek kelimelik yazım: harf, arada kesme ya da tire ("don't", "well-known").
_KELIME = re.compile(r"[a-z]+(?:['\-][a-z]+)*")

# Çekimden gelen yazımda hangi tür önce gösterilir.
_TUR_IPUCU = {
    FormKind.PLURAL: PartOfSpeech.NOUN,
    FormKind.THIRD_PERSON: PartOfSpeech.VERB,
    FormKind.PAST: PartOfSpeech.VERB,
    FormKind.PAST_PARTICIPLE: PartOfSpeech.VERB,
    FormKind.PRESENT_PARTICIPLE: PartOfSpeech.VERB,
    FormKind.COMPARATIVE: PartOfSpeech.ADJECTIVE,
    FormKind.SUPERLATIVE: PartOfSpeech.ADJECTIVE,
}

# İpucu yoksa türlerin sırası (en yaygından).
_TUR_SIRASI = [PartOfSpeech.NOUN, PartOfSpeech.VERB, PartOfSpeech.ADJECTIVE,
               PartOfSpeech.ADVERB, PartOfSpeech.PHRASAL_VERB,
               PartOfSpeech.PREPOSITION, PartOfSpeech.CONJUNCTION]


def _ortak_sozluk():
    """Herkesin görebildiği kelimeler (words.kart ile aynı kural)."""
    return Q(isBaseWord=True) | Q(visibility="public")


def temizle(yazim):
    """
    Dokunulan yazımı sözlük biçimine getirir; kelime değilse "" döner.

        "Decided,"      -> "decided"
        "government’s"  -> "government"
        "“Hello”"       -> "hello"
    """
    if not yazim:
        return ""
    s = str(yazim).strip().lower()[:60]
    s = s.replace("’", "'").replace("‘", "'").replace("‐", "-").replace("‑", "-")
    eslesme = _KELIME.search(s)
    if not eslesme:
        return ""
    s = eslesme.group(0)
    # İyelik eki: government's -> government, students' zaten kesmesiz kalır.
    if s.endswith("'s") and len(s) > 3:
        s = s[:-2]
    return s


def baglam_kelimeleri(metin, en_cok):
    """ "it up." -> ["it", "up"] (en çok `en_cok` tane)."""
    if not metin:
        return []
    kelimeler = []
    for parca in str(metin)[:200].split():
        t = temizle(parca)
        if t:
            kelimeler.append(t)
        if len(kelimeler) >= en_cok:
            break
    return kelimeler


def _kural_adaylari(t):
    """
    WordForm'da olmayan yazımlar için kaba kök adayları. Sözlükte karşılığı
    olan ilk aday seçilir; olmayanlar zararsızdır (sorgu boş döner).
    """
    adaylar = []
    if t.endswith("ies") and len(t) > 4:
        adaylar.append(t[:-3] + "y")
    if t.endswith("es") and len(t) > 3:
        adaylar.append(t[:-2])
    if t.endswith("s") and not t.endswith("ss") and len(t) > 3:
        adaylar.append(t[:-1])
    if t.endswith("ied") and len(t) > 4:
        adaylar.append(t[:-3] + "y")
    if t.endswith("ed") and len(t) > 4:
        adaylar += [t[:-2], t[:-1]]
        if len(t) > 5 and t[-3] == t[-4]:
            adaylar.append(t[:-3])           # stopped -> stop
    if t.endswith("ing") and len(t) > 5:
        adaylar += [t[:-3], t[:-3] + "e"]
        if len(t) > 6 and t[-4] == t[-5]:
            adaylar.append(t[:-4])           # running -> run
    if t.endswith("ly") and len(t) > 4:
        adaylar.append(t[:-2])
    return [a for a in dict.fromkeys(adaylar) if a != t]


def _anlam_prefetch():
    return Prefetch("meanings", queryset=Meaning.objects.order_by("sort_order", "id")
                    .only("id", "word_id", "meaning_tr", "definition", "sort_order"))


def _anlamlar(kelimeler):
    """Birden çok Word'ün anlamları, verilen sırayla, numaralanmaya hazır."""
    sonuc = []
    for kelime in kelimeler:
        for anlam in kelime.meanings.all():
            sonuc.append({"tr": anlam.meaning_tr, "tanim": anlam.definition or "",
                          "word_id": kelime.id})
    return sonuc[:EN_COK_ANLAM]


def _madde(yazim, kelimeler, ipucu=None):
    """
    Aynı yazımın türleri -> tek sözlük maddesi:
    {kok, word_id, anlamlar, word_ids}. word_id "+" ile eklenecek olan
    (ipucu verilen tür, yoksa en yaygın tür).
    """
    def sira(k):
        tur = k.pos
        birinci = 0 if (ipucu and tur == ipucu) else 1
        ikinci = _TUR_SIRASI.index(tur) if tur in _TUR_SIRASI else len(_TUR_SIRASI)
        return (birinci, ikinci, k.id)

    kelimeler = sorted((k for k in kelimeler if k.meanings.all()), key=sira)
    if not kelimeler:
        return None
    return {
        "kok": yazim,
        "word_id": kelimeler[0].id,
        "word_ids": [k.id for k in kelimeler],
        "anlamlar": _anlamlar(kelimeler),
    }


def _phrasal_adaylari(pencere, dokunulan, kokler):
    """
    Pencere: [önceki kelimeler…, dokunulan, sonraki kelimeler…]
    kokler: her pencere kelimesi için olası kökler (kendisi dahil).

    Fiil dokunulan kelime ya da ondan önceki olabilir (parçacığa dokunulmuş
    olabilir: "gave it UP"). Fiille parçacık arasına en çok bir kelime girer.
    Üç parçalı olanlar da denenir: "come up with", "look forward to".
    Aday, dokunulan kelimeyi kapsamalı.
    """
    adaylar = []
    n = len(pencere)
    for i in range(0, dokunulan + 1):
        for mesafe in (1, 2):
            j = i + mesafe
            if j >= n or pencere[j] not in _PARCACIK:
                continue
            # Araya giren kelimeye dokunulduysa phrasal gösterilmez:
            # "gave IT up" -> "it" kendi anlamıyla kalır.
            if mesafe == 2 and dokunulan == i + 1:
                continue
            uzantilar = [[pencere[j]]]
            if j + 1 < n and pencere[j + 1] in _PARCACIK:
                uzantilar.append([pencere[j], pencere[j + 1]])
            for ek in uzantilar:
                if not (i <= dokunulan <= j + len(ek) - 1):
                    continue
                for kok in kokler[i]:
                    adaylar.append(" ".join([kok] + ek))
    return list(dict.fromkeys(adaylar))


def _onbellek_anahtari(t, once, sonra):
    ham = f"{ONBELLEK_SURUMU}|{t}|{' '.join(once)}|{' '.join(sonra)}"
    return "kelime-sorgu:" + hashlib.sha1(ham.encode("utf-8")).hexdigest()


def sorgula(yazim, once="", sonra="", onbellek=True):
    """
    Dokunulan kelimenin sözlük sonucu (kullanıcıdan bağımsız):

        {
          "q": "decided",           # temizlenmiş yazım
          "bulundu": True,
          "kok": "decide",          # gösterilecek madde
          "word_id": 12,            # "+" ile eklenecek kelime
          "anlamlar": [{"tr": "karar vermek", "tanim": "...", "word_id": 12}],
          "digerleri": [ {kok, word_id, anlamlar} ],  # decided · sıfat gibi
          "phrasal": {kok: "give up", word_id, anlamlar} | None,
        }

    Bulunamazsa bulundu=False, kok=q, anlamlar=[] (phrasal yine dolu olabilir).
    """
    t = temizle(yazim)
    once_k = baglam_kelimeleri(once, 10)[-BAGLAM_ONCE:]
    sonra_k = baglam_kelimeleri(sonra, BAGLAM_SONRA)

    anahtar = _onbellek_anahtari(t, once_k, sonra_k)
    if onbellek:
        kayitli = cache.get(anahtar)
        if kayitli is not None:
            return kayitli

    sonuc = _hesapla(t, once_k, sonra_k)
    if onbellek:
        cache.set(anahtar, sonuc, ONBELLEK_SURESI)
    return sonuc


def _hesapla(t, once_k, sonra_k):
    bos = {"q": t, "bulundu": False, "kok": t, "word_id": None, "anlamlar": [],
           "digerleri": [], "phrasal": None}
    if not t:
        return bos

    pencere = once_k + [t] + sonra_k
    dokunulan = len(once_k)
    # Phrasal ancak pencerede (ilk kelimeden sonra) bir parçacık varsa olabilir;
    # yoksa bağlam kelimelerinin köklerine hiç bakılmaz.
    phrasal_olabilir = any(k in _PARCACIK for k in pencere[1:])

    # 1) Çekimler — dokunulan kelime ve (gerekirse) pencere tek sorguda.
    arananlar = set(pencere) if phrasal_olabilir else {t}
    formlar = {}                               # yazım -> [(kök, tür ipucu, çekim mi)]
    for yuzey, kok, tur in (WordForm.objects
                            .filter(surface__in=arananlar)
                            .filter(Q(word__isBaseWord=True) | Q(word__visibility="public"))
                            .values_list("surface", "word__text", "kind")):
        formlar.setdefault(yuzey, []).append((kok, tur))

    # Dokunulan kelimenin kök sırası: çekimden gelen kök önce, sonra yazımın kendisi.
    cekim_kokleri, ipuclari = [], {}
    for kok, tur in formlar.get(t, []):
        if kok != t and tur != FormKind.OTHER:
            if kok not in cekim_kokleri:
                cekim_kokleri.append(kok)
                ipuclari[kok] = _TUR_IPUCU.get(tur)
    yazimlar = cekim_kokleri + [t]
    kural = [] if cekim_kokleri else _kural_adaylari(t)

    # 2) Kelimeler + anlamlar (2 sorgu).
    kelimeler = {}
    for kelime in (Word.objects.filter(_ortak_sozluk(), text__in=yazimlar + kural)
                   .only("id", "text", "pos").prefetch_related(_anlam_prefetch())):
        kelimeler.setdefault(kelime.text, []).append(kelime)

    if not kelimeler.get(t) and not cekim_kokleri:
        # Kural adaylarından sözlükte olan ilki kök sayılır.
        for aday in kural:
            if kelimeler.get(aday):
                yazimlar = [aday, t]
                break

    maddeler = []
    for yazim in yazimlar:
        madde = _madde(yazim, kelimeler.get(yazim, []), ipuclari.get(yazim))
        if madde:
            maddeler.append(madde)

    sonuc = dict(bos)
    if maddeler:
        ana = maddeler[0]
        sonuc.update(bulundu=True, kok=ana["kok"], word_id=ana["word_id"],
                     anlamlar=ana["anlamlar"],
                     digerleri=[{k: m[k] for k in ("kok", "word_id", "anlamlar")}
                                for m in maddeler[1:]])

    # 3) Phrasal verb (2 sorgu, yalnızca aday varsa).
    if phrasal_olabilir:
        kokler = []
        for i, kelime in enumerate(pencere):
            olasi = [kelime] + [k for k, _ in formlar.get(kelime, []) if k != kelime]
            if i == dokunulan:
                olasi = list(dict.fromkeys(yazimlar + olasi))
            kokler.append(olasi)
        adaylar = _phrasal_adaylari(pencere, dokunulan, kokler)
        if adaylar:
            bulunan = list(Word.objects.filter(_ortak_sozluk(), text__in=adaylar,
                                               pos=PartOfSpeech.PHRASAL_VERB)
                           .only("id", "text", "pos").prefetch_related(_anlam_prefetch()))
            # En uzun eşleşme kazanır: "come up with" > "come up".
            bulunan.sort(key=lambda k: (-len(k.text.split()), adaylar.index(k.text)))
            for kelime in bulunan:
                madde = _madde(kelime.text, [kelime])
                if madde:
                    sonuc["phrasal"] = {k: madde[k] for k in ("kok", "word_id", "anlamlar")}
                    break

    return sonuc


def tum_word_idleri(sonuc):
    """Sonuçta "+" düğmesi çıkacak bütün kelimeler (listede bilgisi için)."""
    idler = [sonuc.get("word_id")]
    idler += [m["word_id"] for m in sonuc.get("digerleri", [])]
    if sonuc.get("phrasal"):
        idler.append(sonuc["phrasal"]["word_id"])
    return [i for i in idler if i]
