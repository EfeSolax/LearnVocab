# -*- coding: utf-8 -*-
"""
D1 — eş, zıt ve basit anlamlıları ANLAMA bağlar (WordRelation.meaning).

    python manage.py iliskileri_anlama_bagla --dry-run     # önce bu (rapor 12.8)
    python manage.py iliskileri_anlama_bagla
    python manage.py iliskileri_anlama_bagla --kelime bank,aim --dry-run -v 2

Neden: kelime kartı eş/zıt/basit anlamlıları anlam başına gösteriyor
(rapor 4.3): "bank" için "shore" yalnızca "nehir kıyısı" anlamının altında.
Model bağları zaten anlam başına üretmişti (ara-depo-tam/anlamlar.jsonl,
cevap.meanings[i].relations); yükleyici (bag_tamamla) eskiden bunları
kelime düzeyinde birleştiriyordu. Bu komut depodaki cevabı okuyup her
bağı doğru Meaning'e bağlar. Para harcamaz, model çağırmaz.

Kurallar:
  - Cevap anlamı -> Meaning eşlemesi: words.aile.anlam.anlam_eslemesi
    (meaning_tr, normalleştirilmiş meaning_tr, açıklama).
  - Bir (hedef, tür) birden çok anlamda geçiyorsa satır çoğaltılır: her
    (anlam, hedef, tür) bir satır.
  - Depoda karşılığı olmayan bağ (seed, kullanıcı formu…) kelimenin TEK
    anlamı varsa o anlama verilir.
  - Yalnızca silinmiş/değişmiş bir anlamdan gelen bağ boş kalır (silinen
    anlamın bağı başka anlama yapışmasın). Depoda da olmayan çok anlamlı
    kelimelerin bağları da boş kalır; kaç tane oldukları yazdırılır.
  - confused_with dokunulmaz: karışıklık biçimden gelir (affect/effect),
    bir anlamdan değil; küratörlü tablodan kelime çifti olarak yazılır.

İdempotent: ikinci çalıştırma hiçbir şey değiştirmez. Zaten bağlı
satırlara dokunulmaz; bütün hedefleri bağlanmış bir bağın artık gereksiz
boş satırı silinir (aynı bağ hem boş hem dolu durmasın).
"""

from collections import Counter, defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from words.aile.anlam import anlam_eslemesi
from words.aile.depo import Depo
from words.models import Meaning, RelationType, WordRelation

NEDENLER = {
    "silinen_anlam": "yalnızca veritabanında olmayan (silinmiş/değişmiş) bir anlamdan geliyor",
    "depoda_yok": "kelimenin depoda cevabı var ama bu bağ cevapta yok (çok anlamlı kelime)",
    "kelime_depoda_yok": "kelimenin depoda cevabı yok (elle/seed/eski hat; çok anlamlı)",
    "anlami_yok": "kelimenin hiç anlamı yok",
}


class _Kuru(Exception):
    """--dry-run: transaction'ı geri almak için."""


class Command(BaseCommand):
    help = "D1: WordRelation satırlarını ara depodaki anlam başına bağlarla Meaning'e bağlar."

    def add_arguments(self, c):
        c.add_argument("--depo", default="ara-depo-tam",
                       help="anlamlar.jsonl'ün olduğu ara depo klasörü (varsayılan: ara-depo-tam).")
        c.add_argument("--dry-run", action="store_true",
                       help="Hesapla ve özetle; veritabanına yazma.")
        c.add_argument("--kelime", default="",
                       help="Virgülle ayrılmış kelimeler; yalnızca bunlar (kontrol için).")

    def handle(self, *args, **s):
        depo = Depo(s["depo"])
        if not (depo.yol / "anlamlar.jsonl").exists():
            raise CommandError(f"{depo.yol}/anlamlar.jsonl yok.")
        self.v = s["verbosity"]
        kuru = s["dry_run"]
        kelimeler = {k.strip() for k in s["kelime"].split(",") if k.strip()}

        self.stdout.write(f"Depo okunuyor: {depo.yol}/anlamlar.jsonl …")
        kayitlar = depo.anlamlar()

        try:
            with transaction.atomic():
                sayac, nedenler = self._bagla(kayitlar, kelimeler)
                if kuru:
                    raise _Kuru
        except _Kuru:
            pass
        self._ozet(sayac, nedenler, kuru)

    # ------------------------------------------------------------------

    def _bagla(self, kayitlar, kelimeler):
        sayac = Counter()
        nedenler = Counter()

        satirlar = (WordRelation.objects.exclude(type=RelationType.CONFUSED_WITH)
                    .select_related("from_word", "to_word").order_by("id"))
        if kelimeler:
            satirlar = satirlar.filter(from_word__text__in=kelimeler)
        sayac["karistirilan_atlandi"] = WordRelation.objects.filter(
            type=RelationType.CONFUSED_WITH).count()

        kelime_satirlari = defaultdict(list)
        for r in satirlar:
            kelime_satirlari[r.from_word_id].append(r)

        anlamlar = defaultdict(list)
        for m in Meaning.objects.filter(word_id__in=kelime_satirlari).order_by("sort_order", "id"):
            anlamlar[m.word_id].append(m)

        guncellenecek, olusturulacak, silinecek = [], [], []
        for word_id, rows in kelime_satirlari.items():
            kelime = rows[0].from_word
            db_anlamlari = anlamlar.get(word_id, [])
            kayit = kayitlar.get((kelime.text, kelime.pos)) or {}
            cevap = kayit.get("cevap") or {}
            depoda = kayit.get("durum") == "yazildi" and bool(cevap.get("found"))

            # (hedef metni, tür) -> bu bağın geçtiği Meaning'ler (cevaptaki sırayla)
            istenen = defaultdict(list)
            kopuk = set()   # yalnızca eşleşmeyen cevap anlamlarında geçen bağlar
            if depoda:
                cevap_anlamlari = cevap.get("meanings", [])
                for anlam, m in zip(cevap_anlamlari, anlam_eslemesi(db_anlamlari, cevap_anlamlari)):
                    for bag in anlam.get("relations", []):
                        anahtar = ((bag.get("to_word") or "").strip().lower(), bag.get("type"))
                        if m is None:
                            kopuk.add(anahtar)
                        elif m not in istenen[anahtar]:
                            istenen[anahtar].append(m)

            gruplar = defaultdict(list)
            for r in rows:
                gruplar[(r.to_word_id, r.type)].append(r)

            for (_hedef_id, tur), grup in gruplar.items():
                anahtar = (grup[0].to_word.text.strip().lower(), tur)
                hedefler = istenen.get(anahtar, [])
                tek_anlam = False
                if not hedefler and len(db_anlamlari) == 1 and anahtar not in kopuk:
                    hedefler, tek_anlam = [db_anlamlari[0]], True

                bos = [r for r in grup if r.meaning_id is None]
                if not hedefler:
                    if bos:
                        if not db_anlamlari:
                            neden = "anlami_yok"
                        elif anahtar in kopuk:
                            neden = "silinen_anlam"
                        elif depoda:
                            neden = "depoda_yok"
                        else:
                            neden = "kelime_depoda_yok"
                        nedenler[neden] += len(bos)
                        sayac["eslesmeyen"] += len(bos)
                        if self.v >= 2:
                            self.stdout.write(f"  - boş kaldı ({neden}): {grup[0]}")
                    sayac["zaten_bagli"] += len(grup) - len(bos)
                    continue

                var = {r.meaning_id for r in grup if r.meaning_id is not None}
                sayac["zaten_bagli"] += len(var)
                for m in hedefler:
                    if m.pk in var:
                        continue
                    if bos:
                        r = bos.pop(0)
                        r.meaning = m
                        guncellenecek.append(r)
                        sayac["atanan"] += 1
                        sayac["atanan_tek_anlam"] += int(tek_anlam)
                    else:
                        ornek = grup[0]
                        olusturulacak.append(WordRelation(
                            from_word_id=ornek.from_word_id, to_word_id=ornek.to_word_id,
                            type=tur, note=ornek.note, meaning=m))
                        sayac["cogaltilan"] += 1
                    if self.v >= 2:
                        self.stdout.write(f"  + {grup[0]}  [{m.meaning_tr}]")
                # Bütün hedefler bağlı: kalan boş satır aynı bağın gereksiz kopyası.
                silinecek += [r.pk for r in bos]
                sayac["fazla_bos_silinen"] += len(bos)

        WordRelation.objects.bulk_update(guncellenecek, ["meaning"], batch_size=2000)
        WordRelation.objects.bulk_create(olusturulacak, batch_size=2000)
        if silinecek:
            for i in range(0, len(silinecek), 2000):
                WordRelation.objects.filter(pk__in=silinecek[i:i + 2000]).delete()
        sayac["kelime"] = len(kelime_satirlari)
        sayac["satir"] = sum(len(r) for r in kelime_satirlari.values())
        return sayac, nedenler

    def _ozet(self, sayac, nedenler, kuru):
        baslik = "KURU ÇALIŞTIRMA (veritabanına yazılmadı)" if kuru else "YAZILDI"
        self.stdout.write(self.style.SUCCESS(f"\n{baslik}"))
        self.stdout.write(f"İncelenen: {sayac['satir']} bağ satırı, {sayac['kelime']} kelime "
                          f"(confused_with hariç; {sayac['karistirilan_atlandi']} karıştırılan "
                          f"kelime düzeyinde kaldı)")
        self.stdout.write(f"  Zaten bağlıydı:          {sayac['zaten_bagli']}")
        self.stdout.write(f"  Anlama atanan:           {sayac['atanan']} "
                          f"(tek anlamlı kelime kuralıyla: {sayac['atanan_tek_anlam']})")
        self.stdout.write(f"  Çoğaltılan (yeni satır): {sayac['cogaltilan']}")
        self.stdout.write(f"  Fazla boş satır silinen: {sayac['fazla_bos_silinen']}")
        self.stdout.write(f"  Eşleşmeyen (boş kaldı):  {sayac['eslesmeyen']}")
        for neden, n in nedenler.most_common():
            self.stdout.write(f"      {n:>6}  {NEDENLER[neden]}")
