"""
D3 — Hafif fiilli eş dizimlerde çeldirici doğrulama (rapor 6.2, 13.3).

İki adım; ikisi de hiçbir API çağırmaz:

1) Adayları dosyaya yaz (doğrulama için yapay zekâya verilecek iş listesi):

       python manage.py esdizim_celdiricileri --adaylari-yaz adaylar.jsonl

   Her hafif fiilli eş dizim (make/take/do/give/have + …) için diğer dört
   hafif fiil birer aday. Henüz doğrulanmış kaydı olanlar yazılmaz.
   Satır biçimi:
       {"collocation_id": 12, "pattern": "make a decision", "celdirici": "do",
        "meaning_tr": "karar vermek", "ornek": "She made a decision …"}

2) Doğrulama sonucunu yükle:

       python manage.py esdizim_celdiricileri --yukle sonuc.jsonl --dry-run
       python manage.py esdizim_celdiricileri --yukle sonuc.jsonl

   Satır biçimi (aday satırına iki alan eklenmiş hâli):
       {"collocation_id": 12, "celdirici": "do",
        "gercekten_yanlis": true,            # "do a decision" gerçekten yanlış mı?
        "kaynak": "gemini-2.5-flash", "not": "…"}

   gercekten_yanlis=false olan (ör. İngiliz İngilizcesinde "take a
   decision") ASLA çeldirici olmaz. Bir eş dizim en az 3 doğrulanmış
   çeldiricisi olunca soru havuzuna girer.
"""

import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from egzersizler.models import EsdizimCeldiricisi
from egzersizler.sorular import HAFIF_FIILLER, hafif_fiilli_esdizimler


class Command(BaseCommand):
    help = "D3: hafif fiilli eş dizim çeldiricilerinin adaylarını yazar / doğrulamalarını yükler."

    def add_arguments(self, parser):
        grup = parser.add_mutually_exclusive_group(required=True)
        grup.add_argument("--adaylari-yaz", metavar="DOSYA")
        grup.add_argument("--yukle", metavar="DOSYA")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, adaylari_yaz=None, yukle=None, dry_run=False, **opts):
        if adaylari_yaz:
            return self._adaylar(adaylari_yaz)
        return self._yukle(yukle, dry_run)

    def _adaylar(self, yol):
        dogrulanmis = set(EsdizimCeldiricisi.objects.exclude(gercekten_yanlis__isnull=True)
                          .values_list("collocation_id", "celdirici"))
        sayi = 0
        with open(yol, "w", encoding="utf-8") as f:
            for e in hafif_fiilli_esdizimler().select_related("meaning").order_by("id"):
                fiil = e.pattern.split(" ", 1)[0].lower()
                for aday in HAFIF_FIILLER:
                    if aday == fiil or (e.id, aday) in dogrulanmis:
                        continue
                    f.write(json.dumps({
                        "collocation_id": e.id, "pattern": e.pattern, "celdirici": aday,
                        "meaning_tr": e.meaning_tr or e.meaning.meaning_tr,
                        "ornek": e.example or "",
                    }, ensure_ascii=False) + "\n")
                    sayi += 1
        self.stdout.write(self.style.SUCCESS(f"{sayi} aday yazıldı: {yol}"))

    def _yukle(self, yol, dry_run):
        try:
            with open(yol, encoding="utf-8") as f:
                metin = f.read().strip()
            kayitlar = json.loads(metin) if metin.startswith("[") else \
                [json.loads(s) for s in metin.splitlines() if s.strip()]
        except (OSError, ValueError) as e:
            raise CommandError(f"Dosya okunamadı: {e}")

        esdizimler = {e.id: e for e in hafif_fiilli_esdizimler()}
        gecerli, atlanan = [], 0
        for i, k in enumerate(kayitlar, start=1):
            e = esdizimler.get(k.get("collocation_id"))
            aday = str(k.get("celdirici") or "").strip().lower()
            sonuc = k.get("gercekten_yanlis")
            if e is None or aday not in HAFIF_FIILLER or not isinstance(sonuc, bool) \
                    or aday == e.pattern.split(" ", 1)[0].lower():
                atlanan += 1
                self.stdout.write(self.style.WARNING(f"{i}. kayıt atlandı: {k}"))
                continue
            gecerli.append((e, aday, sonuc, k))

        self.stdout.write(f"{len(kayitlar)} kayıt: {len(gecerli)} geçerli, {atlanan} atlandı, "
                          f"{sum(1 for g in gecerli if g[2])} çeldirici onaylı.")
        if dry_run:
            self.stdout.write("Deneme (--dry-run): hiçbir şey yazılmadı.")
            return
        simdi = timezone.now()
        with transaction.atomic():
            for e, aday, sonuc, k in gecerli:
                EsdizimCeldiricisi.objects.update_or_create(
                    collocation=e, celdirici=aday,
                    defaults={"gercekten_yanlis": sonuc,
                              "kaynak": str(k.get("kaynak") or "")[:80],
                              "not_metni": str(k.get("not") or "")[:300],
                              "dogrulama_tarihi": simdi})
        self.stdout.write(self.style.SUCCESS(f"{len(gecerli)} doğrulama yazıldı."))
