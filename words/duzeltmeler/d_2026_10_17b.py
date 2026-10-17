# -*- coding: utf-8 -*-
"""
17 Ekim — Gemini'nin tüm veritabanı taramasından (veri/kalite_olcumu/gemini-tum-veritabani-duzeltmeleri.tsv)
Claude'un kabul ettiği 193 öneri. Karar dosyaları veri/kalite_olcumu/duzeltme/gemini3-kabul.tsv ve
gemini3-ret.tsv (ret gerekçeleriyle). Efe: "iyi gördüklerini uygula; edat gerçekten sık kullanılıyorsa
anlamın başına (… ile) eklenebilir."

Uygulananlar: Türkçe anlam (56; 32'si edat etiketi), phrasal verb'lerin ana fiil bağı (49), kalıplarda
Amerikan yazımı (31), boş aileler (16), silinmiş hassas anlamlardan kalan sahipsiz eş/zıt/basit bağları
(30, yedeği silinen-baglar.tsv), eksik çekimler, İngilizce kalmış 2 eş dizim karşılığı, fall (isim)
örneği, level off'un Phrasal Verbs listesine eklenmesi. Eş dizim/kalıp silme önerileri uygulanmadı.

Çalıştırma (önce kuru deneme; yedek: ~/LearnVocab-yedekler/db.sqlite3.yedek-20261017-gemini3-oncesi):
  python manage.py shell -c "from words.duzeltmeler import d_2026_10_17b as d; print(d.gemini3(kuru=True))"
  python manage.py shell -c "from words.duzeltmeler import d_2026_10_17b as d; print(d.gemini3())"
Tekrar çalıştırmak güvenli: mevcut değeri tutmayan satır atlanır.
"""
import csv
import re
from collections import Counter

from words.duzeltmeler.d_2026_10_14b import KLASOR, _calistir
from words.models import (
    Collocation, ExampleSentence, HazirListeKelimesi, Meaning, UsagePattern, Word, WordFamily, WordForm,
    WordRelation,
)

KABUL = KLASOR / "gemini3-kabul.tsv"
BAG_YEDEK = KLASOR / "silinen-baglar.tsv"
PHRASAL_LISTE = 29


def _satirlar():
    with KABUL.open(encoding="utf-8") as f:
        yield from csv.DictReader((s for s in f if not s.startswith("#")), delimiter="\t")


def gemini3(kuru=False):
    def is_():
        sayac, bag_yedek = Counter(), []
        for x in _satirlar():
            islem, kid, eski, yeni = x["alan_veya_islem"], int(x["kayit_id"]), x["mevcut_deger"], x["onerilen_deger"]
            tamam = False
            if islem == "UPDATE meaning_tr":
                tamam = Meaning.objects.filter(pk=kid, meaning_tr=eski).update(meaning_tr=yeni)
            elif islem == "meaning_tr":                              # eş dizimin Türkçesi İngilizce kalmış
                tamam = Collocation.objects.filter(pk=kid, pattern=eski, meaning_tr=eski).update(meaning_tr=yeni)
            elif islem.startswith("UPDATE pattern"):
                tamam = UsagePattern.objects.filter(pk=kid, pattern=eski).update(pattern=yeni)
            elif islem == "UPDATE text":
                ornek = ExampleSentence.objects.filter(pk=kid).first()
                if ornek and ornek.text.startswith(eski.rstrip(".… ")[:60]):
                    ornek.text = yeni
                    ornek.save(update_fields=["text"])
                    tamam = True
            elif islem == "UPDATE base_verb_id":
                hedef = int(re.match(r"\d+", yeni).group())
                if Word.objects.filter(pk=hedef, pos="verb").exists():
                    tamam = Word.objects.filter(pk=kid, base_verb__isnull=True).update(base_verb_id=hedef)
            elif islem == "DELETE boş aile":
                aile = WordFamily.objects.filter(pk=kid).first()
                if aile and not aile.words.exists():
                    aile.delete()
                    tamam = True
            elif islem.startswith("DELETE ("):                       # sahipsiz bağ (meaning_id NULL)
                bag = WordRelation.objects.filter(pk=kid, meaning__isnull=True).select_related("from_word", "to_word").first()
                if bag:
                    bag_yedek.append("\t".join([str(bag.pk), bag.type, bag.from_word.text, bag.from_word.pos,
                                                bag.to_word.text, x["neden"]]))
                    bag.delete()
                    tamam = True
            elif islem == "INSERT WordForm":
                kelime = Word.objects.filter(pk=kid).first()
                for yazim, tur in re.findall(r"(\S+) \((\w+)\)", yeni):
                    if kelime and not kelime.forms.filter(surface=yazim).exists():
                        WordForm.objects.create(word=kelime, surface=yazim, kind=tur)
                        tamam = True
            elif islem == "INSERT (phrasal-verbs listesi)":
                if not HazirListeKelimesi.objects.filter(liste_id=PHRASAL_LISTE, word_id=kid).exists():
                    son = (HazirListeKelimesi.objects.filter(liste_id=PHRASAL_LISTE)
                           .order_by("-sira").values_list("sira", flat=True).first() or 0)
                    HazirListeKelimesi.objects.create(liste_id=PHRASAL_LISTE, word_id=kid, sira=son + 1, bolum="C1")
                    tamam = True
            sayac[f"{islem}: {'uygulandı' if tamam else 'atlandı'}"] += 1
        if bag_yedek and not kuru:
            with BAG_YEDEK.open("a", encoding="utf-8") as f:
                f.write("\n".join(bag_yedek) + "\n")
        return sayac
    return _calistir(is_, kuru)


# ----------------------------------------------------------------------
# Konular: Gemini'nin kategori önerileri (veri/kalite_olcumu/gemini-kategori-onerileri.tsv), Efe'nin
# kararıyla aynen: 4.086 ekleme, 32 "doğru anlama bağla", 11 kırık ipucu düzeltmesi. Kaynak
# veri/kategoriler/*.txt olduğu için öneriler dosyalara yazılır, sonra konular baştan kurulur:
#
#   python manage.py shell -c "from words.duzeltmeler import d_2026_10_17b as d; print(d.gemini_konular(kuru=True))"
#   python manage.py shell -c "from words.duzeltmeler import d_2026_10_17b as d; print(d.gemini_konular())"
#   python manage.py shell -c "from words.duzeltmeler import d_2026_10_11 as d; d.konulari_kur()"
#
# Her madde önerinin meaning_id'sine bağlanıyor mu diye denenir; ipucu başka anlama düşüyorsa (ya da
# dosya biçimini bozan virgül varsa) hedef anlamın virgülsüz bir parçası ipucu yapılır.
# ----------------------------------------------------------------------
KONU_ONERI = KLASOR.parent / "gemini-kategori-onerileri.tsv"


def _madde_bul(yazim, tur, hedef):
    """Gemini'nin kodu hedef anlama bağlanmıyorsa işe yarayan bir madde arar."""
    from words.duzeltmeler.d_2026_10_11 import _bagla
    kisa = {v: k for k, v in {"n": "noun", "v": "verb", "adj": "adjective", "adv": "adverb",
                              "pv": "phrasal_verb"}.items()}
    anlam = Meaning.objects.select_related("word").get(pk=hedef)
    bas = f"{yazim}:{kisa.get(anlam.word.pos, anlam.word.pos)}"
    parcalar = [p.strip() for p in re.split(r"[,;]", anlam.meaning_tr) if p.strip()]
    for aday in [f"{bas}={p}" for p in parcalar] + [f"{bas}=^{parcalar[0]}"] if parcalar else []:
        anlamlar, _, _ = _bagla(aday)
        if [m.id for m in anlamlar] == [hedef]:
            return aday
    return None


def gemini_konular(kuru=False):
    from words.duzeltmeler.d_2026_10_11 import KONU_DOSYALARI, _bagla, _madde_coz
    sayac, sorun = Counter(), []
    with KONU_ONERI.open(encoding="utf-8") as f:
        oneriler = list(csv.DictReader(f, delimiter="\t"))

    # Önerileri dosyaya yazılacak maddeye çevir (hedef anlama bağlandığı doğrulanmış)
    yazilacak = []           # (slug, islem, kelime, tür, madde)
    for x in oneriler:
        kod, hedef = x["dosya_madde_kodu"].strip(), int(x["meaning_id"])
        tutuyor = "," not in kod and [m.id for m in _bagla(kod)[0]] == [hedef]
        if not tutuyor:
            yazim = _madde_coz(kod)[0] if "," not in kod else kod.split(":")[0].split("=")[0]
            kod = _madde_bul(yazim, x["tur"], hedef)
            sayac["ipucu yeniden yazıldı" if kod else "bağlanamadı"] += 1
            if not kod:
                sorun.append(f"{x['kategori_slug']}\t{x['dosya_madde_kodu']}\t{hedef}")
                continue
        yazilacak.append((x["kategori_slug"], x["islem"], x["kelime"], x["tur"], kod))

    # Dosyalara uygula: DUZELT_* eski maddeyi değiştirir, EKLE bölüm sonuna yeni satır olarak eklenir
    for yol in KONU_DOSYALARI:
        satirlar = yol.read_text(encoding="utf-8").split("\n")
        bolumler = {}        # slug -> [başlık satırı no, son madde satırı no]
        slug = None
        for i, s in enumerate(satirlar):
            if s.startswith("## "):
                slug = s[3:].split("|")[0].strip()
                bolumler[slug] = [i, i]
            elif slug and s.strip() and not s.startswith("#"):
                bolumler[slug][1] = i
        ekler = {}
        for kslug, islem, kelime, tur, kod in yazilacak:
            if kslug not in bolumler:
                continue
            bas, son = bolumler[kslug]
            if islem.startswith("DUZELT"):
                degisti = False
                for i in range(bas + 1, son + 1):
                    if satirlar[i].startswith("#"):
                        continue
                    maddeler = [m.strip() for m in satirlar[i].split(",")]
                    for j, m in enumerate(maddeler):
                        if not m:
                            continue
                        y, t, _ = _madde_coz(m)
                        if y.lower() == kelime.lower() and (t is None or t == tur):
                            maddeler[j] = kod
                            degisti = True
                            break
                    if degisti:
                        satirlar[i] = ", ".join(maddeler)
                        break
                sayac[f"{islem}: {'değişti' if degisti else 'eklendi (eski madde yok)'}"] += 1
                if degisti:
                    continue
            ekler.setdefault(kslug, []).append(kod)
            if islem == "EKLE":
                sayac["EKLE"] += 1
        # Eklemeleri bölüm sonlarına, sondan başa doğru yerleştir (satır numaraları kaymasın)
        for kslug in sorted(ekler, key=lambda s: -bolumler[s][1]):
            son = bolumler[kslug][1]
            satirlar[son + 1:son + 1] = ["# Gemini önerisi, 17 Ekim 2026 (Efe onayı)",
                                         ", ".join(dict.fromkeys(ekler[kslug]))]
        if not kuru:
            yol.write_text("\n".join(satirlar), encoding="utf-8")
    sayac["sorun"] = len(sorun)
    if sorun:
        (KLASOR / "gemini-konu-baglanamayan.tsv").write_text("\n".join(sorun) + "\n", encoding="utf-8")
    return sayac


# Konular baştan kurulunca ipucusuz 14 madde, anlam sırası önceki turlarda değiştiği için başka
# anlama kaydı (appeal hukukta "çekicilik", party siyasette "eğlence" …). Eski doğru anlamlar dosyaya
# açık ipucuyla yazılır; temperature (hava durumu: sıcaklık), gas (gaz) ve classical (klasik,
# geleneksel) yeni hâlleriyle daha doğru olduğu için bırakıldı.
ESKI_DOGRU = [  # (konu, dosyadaki madde, doğru anlam id)
    ("gorunus-beden", "dark:adj", 670), ("neden-sonuc-degisim", "sharp:adj", 1430), ("doga", "earth", 4428),
    ("neden-sonuc-degisim", "drop:n", 11213), ("siyaset-toplum", "party:n=parti", 15368),
    ("giyim-moda", "trainer", 16537), ("ev-esyalar", "floor", 16597), ("hukuk-suc", "appeal:n", 17625),
    ("saglik", "temperature", 17764), ("doga", "space", 20066), ("ekonomi-is-dunyasi", "loss", 20124),
]


def eski_konu_baglari(kuru=False):
    from words.duzeltmeler.d_2026_10_11 import KONU_DOSYALARI
    sayac = Counter()
    for yol in KONU_DOSYALARI:
        satirlar, slug = yol.read_text(encoding="utf-8").split("\n"), None
        for i, s in enumerate(satirlar):
            if s.startswith("## "):
                slug = s[3:].split("|")[0].strip()
                continue
            if not s.strip() or s.startswith("#"):
                continue
            maddeler = [m.strip() for m in s.split(",")]
            for konu, madde, hedef in ESKI_DOGRU:
                if konu == slug and madde in maddeler:
                    kod = _madde_bul(madde.split(":")[0].split("=")[0], None, hedef)
                    if kod:
                        maddeler[maddeler.index(madde)] = kod
                        sayac["düzeltildi"] += 1
                    else:
                        sayac[f"bulunamadı: {konu} {madde}"] += 1
            satirlar[i] = ", ".join(maddeler)
        if not kuru:
            yol.write_text("\n".join(satirlar), encoding="utf-8")
    return sayac
