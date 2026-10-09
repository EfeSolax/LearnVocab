# -*- coding: utf-8 -*-
"""
6 Ekim — eş / zıt / daha basit bağlarının temizliği (rapor 18.7 B aşaması).

Kararlar veritabanı kimliğiyle değil, kalıcı anahtarla tutulur; dosyalar
veri/iliski_denetimi/*.tsv altında, her satır bir bağ:

    tur  kaynak  kaynak_tur  anlam  hedef  hedef_tur  karar  not

  tur      synonym / antonym / simpler
  anlam    bağın bağlı olduğu anlamın Türkçesi (meaning_tr)
  karar    sil            -> bağ silinir
           zayif          -> DOKUNULMAZ; Efe sonra inceler (ozetler/zayif-baglar.tsv)
           tur:<pos>      -> hedef, aynı yazımın <pos> türündeki kaydına taşınır
           hedef:<yazım>/<pos> -> hedef başka bir kelimeyle değiştirilir

Dosyalar:
  kural-1-daha-basit.tsv  18.6 kuralını bozan "daha basit" bağları (genişletme
                          partileri kuralı yeniden uygulamadan bağ ekledi)
  kural-2-tur.tsv         kaynakla hedefin türü uyuşmayan bağlar: aynı yazımın
                          kaynak türünde kaydı varsa taşınır, yoksa silinir
                          (wasteful -> spend, thankful -> thank, adoring -> like)
  elle-*.tsv              Claude'un elle okuması

Kural dosyaları kural_dosyalarini_yaz() ile üretilir (yalnızca okur).
Çalıştırma:
  python manage.py shell -c "from words.duzeltmeler import d_2026_10_06 as d; d.kural_dosyalarini_yaz()"
  python manage.py shell -c "from words.duzeltmeler import d_2026_10_06 as d; print(d.uygula())"
  python manage.py shell -c "from words.duzeltmeler import d_2026_10_06 as d; print(d.anlamlari_duzelt())"
Tekrar çalıştırmak güvenli: silinmiş ya da taşınmış bağ bir daha bulunmaz.
"""
import csv
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.db import transaction

from words.models import Meaning, Word, WordRelation
from words.arama import cefr_sirasi
from words.veri_kurallari import daha_basit_silinecekler

KLASOR = Path(settings.BASE_DIR) / "veri" / "iliski_denetimi"
ZAYIF_DOSYASI = Path(settings.BASE_DIR) / "ozetler" / "zayif-baglar.tsv"
ALANLAR = ("tur", "kaynak", "kaynak_tur", "anlam", "hedef", "hedef_tur", "karar", "not")
TURLER = ("synonym", "antonym", "simpler")


def satir(r, karar, not_=""):
    return {"tur": r.type, "kaynak": r.from_word.text, "kaynak_tur": r.from_word.pos,
            "anlam": r.meaning.meaning_tr if r.meaning_id else "",
            "hedef": r.to_word.text, "hedef_tur": r.to_word.pos, "karar": karar, "not": not_}


def yaz(ad, satirlar):
    KLASOR.mkdir(parents=True, exist_ok=True)
    with open(KLASOR / ad, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ALANLAR, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(satirlar)
    return len(satirlar)


def oku(yol):
    with open(yol, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


# Türü uyuşmayan ama anlamca yerinde bağlar (Claude elle okudu): silinmez, zayıf işaretlenir.
TUR_ISTISNALARI = {
    ("onshore", "ashore"), ("nigh", "nearly"), ("nigh", "almost"), ("halfway", "midway"),
    ("near", "adjacent"), ("near", "close"), ("near", "far"), ("while", "during"),
    ("besides", "also"), ("circa", "approximately"), ("circa", "exactly"), ("forward", "ahead"),
    ("onward", "ahead"), ("far", "distant"), ("flat", "level"), ("opposed", "against"),
    ("regardless", "despite"),
}


# Kural 2'de taşınacak bağlar elle okundu (356). Taşındıktan sonra da yanlış kalanlar
# silinir (division -> divide (isim: ayrım çizgisi), printer -> print (isim), sharpness ->
# sharp (isim: diyez)…); anlamca zayıf kalanlar işaretlenir. (kaynak, hedef) çiftleri.
TASIMA_SIL = {
    ("division", "divide"), ("divisor", "divide"), ("partition", "divide"), ("interface", "divide"),
    ("multiplier", "divide"), ("slash", "divide"), ("cement", "divide"), ("separation", "divide"),
    ("segmentation", "divide"), ("pagination", "divide"), ("hunt", "preserve"),
    ("idealization", "ideal"), ("printer", "print"), ("rager", "calm"), ("seizure", "calm"),
    ("bolt", "calm"), ("twister", "calm"), ("shudder", "calm"), ("explosion", "calm"),
    ("relaxant", "calm"), ("lightning", "calm"), ("blow", "calm"), ("stirring", "calm"),
    ("haunting", "calm"), ("vibration", "calm"), ("buzz", "calm"), ("tornado", "calm"),
    ("hurricane", "calm"), ("typhoon", "calm"), ("quake", "calm"), ("eruption", "calm"),
    ("thunderbolt", "calm"), ("surf", "calm"), ("wave", "calm"), ("wake", "calm"),
    ("adrenaline", "calm"), ("spasm", "calm"), ("fit", "calm"), ("riot", "calm"),
    ("madness", "calm"), ("warpath", "calm"), ("provocation", "calm"), ("tranquilizer", "calm"),
    ("sharpness", "sharp"), ("swoop", "retreat"), ("adhesion", "adhesive"), ("belly", "top"),
    ("buzz", "text"), ("west", "western"), ("successor", "next"), ("lioness", "male"),
    ("bloody", "very"), ("drone", "male"), ("lastly", "then"), ("silverback", "male"),
    ("initial", "first"), ("topper", "first"), ("steadfastness", "faithful"), ("why", "since"),
    ("northwards", "up"), ("brown", "white"), ("coffeehouse", "bar"), ("rootless", "home"),
    ("doer", "act"), ("explicit", "state"), ("adoration", "like"), ("modeling", "act"),
    ("likability", "like"), ("likeness", "like"), ("precedence", "first"), ("theist", "faithful"),
    ("hang over", "stay"), ("waiver", "forfeit"),
}
TASIMA_ZAYIF = {
    ("idealism", "ideal"), ("gust", "calm"), ("hysteria", "calm"), ("fright", "calm"),
    ("terror", "calm"), ("shock", "calm"), ("temper", "calm"), ("blowup", "calm"),
    ("irritation", "calm"), ("outburst", "calm"), ("exasperation", "calm"), ("wrath", "calm"),
    ("worry", "calm"), ("patch up", "break"), ("camp", "retreat"), ("diametrically", "opposite"),
    ("mouth off", "respect"), ("mouth off", "talk"), ("chill out", "stress"), ("sole", "top"),
    ("clam up", "silence"), ("blotter", "log"), ("synonym", "equivalent"), ("par", "equivalent"),
    ("halfway", "complete"), ("outwardly", "inside"), ("inwardly", "inside"),
    ("ancestral", "family"), ("underwater", "under"), ("lineal", "family"), ("maternal", "family"),
    ("through", "across"), ("least", "little"), ("cash in", "exchange"), ("masculinity", "male"),
    ("democrat", "liberal"), ("behavior", "act"), ("hate", "like"), ("exploit", "act"),
    ("public", "state"), ("national", "state"), ("bill", "act"), ("former", "first"),
    ("inland", "inside"), ("intersect", "parallel"), ("resin", "adhesive"), ("pay off", "benefit"),
    ("round up", "increase"),
}


def _fiilce(pos):
    """Phrasal verb tür denetiminde fiil sayılır: give up -> abandon doğru bir eş anlamlıdır."""
    return "verb" if pos == "phrasal_verb" else pos


def _iliskiler():
    return WordRelation.objects.select_related("from_word", "to_word", "meaning")


def kural_dosyalarini_yaz(ez=False):
    """
    Kural 1 ve 2'nin karar dosyalarını üretir; veritabanını değiştirmez.
    Uygulamadan SONRA çalıştırılırsa dosyalar boşalır; bu yüzden var olan
    dosyalar ez=True verilmedikçe ezilmez.
    """
    if not ez and (KLASOR / "kural-1-daha-basit.tsv").exists():
        raise FileExistsError("Kural dosyaları zaten var; yeniden üretmek için ez=True.")
    nedenler = dict(daha_basit_silinecekler())
    bir = [satir(r, "sil", nedenler[r.id]) for r in _iliskiler().filter(id__in=nedenler)]

    turler = {(t, p) for t, p in Word.objects.values_list("text", "pos")}
    iki = []
    for r in _iliskiler().filter(type__in=TURLER).exclude(id__in=nedenler):
        kaynak, hedef = _fiilce(r.from_word.pos), _fiilce(r.to_word.pos)
        if kaynak == hedef:
            continue
        if (r.from_word.text, r.to_word.text) in TUR_ISTISNALARI:
            iki.append(satir(r, "zayif", f"tür farklı ({r.from_word.pos} → {r.to_word.pos}), anlam yakın"))
        elif (r.to_word.text, kaynak) in turler:
            cift = (r.from_word.text, r.to_word.text)
            if cift in TASIMA_SIL:
                iki.append(satir(r, "sil", f"doğru türe taşınsa da yanlış ({kaynak})"))
            elif cift in TASIMA_ZAYIF:
                iki.append(satir(r, "zayif", f"doğru türü {kaynak}; taşınmadı, anlam zayıf"))
            else:
                iki.append(satir(r, f"tur:{kaynak}", "aynı yazımın kaynak türündeki kaydı"))
        else:
            iki.append(satir(r, "sil", f"tür uyuşmuyor ({r.from_word.pos} → {r.to_word.pos})"))
    return {"kural-1-daha-basit.tsv": yaz("kural-1-daha-basit.tsv", bir),
            "kural-2-tur.tsv": yaz("kural-2-tur.tsv", iki)}


def _bul(k):
    qs = WordRelation.objects.filter(
        type=k["tur"], from_word__text=k["kaynak"], from_word__pos=k["kaynak_tur"],
        to_word__text=k["hedef"], to_word__pos=k["hedef_tur"])
    return qs.filter(meaning__meaning_tr=k["anlam"]) if k["anlam"] else qs.filter(meaning__isnull=True)


def _tasi(r, hedef):
    """Bağı yeni hedefe taşır; aynı bağ zaten varsa eskisini siler."""
    ayni = WordRelation.objects.filter(from_word_id=r.from_word_id, to_word=hedef,
                                       type=r.type, meaning_id=r.meaning_id)
    if hedef.id == r.from_word_id or ayni.exists():
        r.delete()
        return "silindi"
    r.to_word = hedef
    r.save(update_fields=["to_word"])
    return "taşındı"


def uygula(dosyalar=None):
    """Karar dosyalarını uygular; zayıfları ozetler/zayif-baglar.tsv'ye toplar."""
    # Kural dosyaları önce: elle kararların bir kısmı kural 2'nin doğru türe taşıdığı bağları anar.
    yollar = ([KLASOR / d for d in dosyalar] if dosyalar else
              sorted(KLASOR.glob("*.tsv"), key=lambda y: (not y.name.startswith("kural-"), y.name)))
    sayac, zayiflar = Counter(), []
    with transaction.atomic():
        for yol in yollar:
            for k in oku(yol):
                karar = k["karar"]
                if karar == "zayif":
                    zayiflar.append(k)
                    continue
                for r in _bul(k):
                    if karar == "sil":
                        r.delete()
                        sayac["silindi"] += 1
                        continue
                    if karar.startswith("tur:"):
                        yazim, pos = k["hedef"], karar[4:]
                    elif karar.startswith("hedef:"):
                        yazim, pos = karar[6:].rsplit("/", 1)
                    else:
                        raise ValueError(f"{yol.name}: bilinmeyen karar {karar!r}")
                    hedef = Word.objects.filter(text=yazim, pos=pos).first()
                    sayac[_tasi(r, hedef) if hedef else "hedef yok"] += 1
    sayac["zayıf (dokunulmadı)"] = len(zayiflar)
    sayac["zayıf dosyası"] = zayif_dosyasini_yaz()
    return dict(sayac)


def zayif_dosyasini_yaz():
    """Bütün karar dosyalarındaki zayıf bağları tek dosyada toplar (Efe inceler)."""
    zayiflar, gorulen = [], set()
    for yol in sorted(KLASOR.glob("*.tsv")):
        for k in oku(yol):
            anahtar = tuple(k[a] for a in ALANLAR[:6])
            if k["karar"] == "zayif" and anahtar not in gorulen:
                gorulen.add(anahtar)
                zayiflar.append(k)
    with open(ZAYIF_DOSYASI, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ALANLAR, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(zayiflar)
    return len(zayiflar)


# ---------------------------------------------------------------------------
# Okuma sırasında görülen anlam hataları. Anahtar: (kelime, tür, Türkçe karşılık).

# Asıl anlam başa: (kelime, tür) -> sıradaki Türkçe karşılıklar
SIRA = {
    ("interpret", "verb"): ["açıklamak, yorumlamak", "çevirmenlik yapmak, sözlü çeviri yapmak"],
    ("occur", "verb"): ["gerçekleşmek, meydana gelmek", "aklına gelmek, hatırlanmak"],
}

# Yanlış İngilizce tanım: (kelime, tür, karşılık) -> yeni tanım
TANIM = {
    ("load", "verb", "doldurmak"): "to put ammunition into a gun or weapon",
    ("junior", "noun", "üçüncü sınıf öğrencisi"):
        "a student in the third year of a four-year high school or college program",
    ("conductor", "noun", "kondüktör, biletçi"):
        "a person who checks passengers' tickets on a train or bus",
    ("staggered", "adjective", "şoke olmuş, çok şaşırmış, hayrete düşmüş"):
        "very surprised or shocked by something unexpected",
}

# Silinen anlamlar: küçük harfli china/guinea ülke adı değildir (özel ad sözlükte
# yok); cheese "para" ve skinny "parasız" yerleşik anlamlar değil.
ANLAM_SIL = [
    ("china", "noun", "Çin"), ("guinea", "noun", "gine"),
    ("cheese", "noun", "para"), ("skinny", "adjective", "kıt, yetersiz"),
]


def anlamlari_duzelt():
    sayac = Counter()
    with transaction.atomic():
        for (kelime, tur), sira in SIRA.items():
            for i, tr in enumerate(sira):
                sayac["sıra"] += Meaning.objects.filter(
                    word__text=kelime, word__pos=tur, meaning_tr=tr).update(sort_order=i)
        for (kelime, tur, tr), tanim in TANIM.items():
            sayac["tanım"] += Meaning.objects.filter(
                word__text=kelime, word__pos=tur, meaning_tr=tr).update(definition=tanim)
        for kelime, tur, tr in ANLAM_SIL:
            n, _ = Meaning.objects.filter(word__text=kelime, word__pos=tur, meaning_tr=tr).delete()
            sayac["silinen anlam"] += bool(n)
        # Kalan anlamlar 0'dan sıralansın (porselen, İngiliz altını ilk anlam olur);
        # Word.cefr en kolay anlamın seviyesidir (china A1 -> B2).
        for kelime, tur, _ in ANLAM_SIL:
            anlamlar = list(Meaning.objects.filter(word__text=kelime, word__pos=tur))
            for i, m in enumerate(anlamlar):
                if m.sort_order != i:
                    m.sort_order = i
                    m.save(update_fields=["sort_order"])
            w = Word.objects.get(text=kelime, pos=tur)
            en_kolay = min((m.cefr for m in anlamlar), key=cefr_sirasi)
            if w.cefr_kaynak == "learnvocab" and w.cefr != en_kolay:
                w.cefr = en_kolay
                w.save(update_fields=["cefr"])
                sayac["kelime seviyesi"] += 1
    return dict(sayac)
