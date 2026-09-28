"""
D2 — Bağlaç/ifade cümle havuzunu yükler (rapor 6.2, 13.3).

Havuz yapay zekâyla üretilip denetlenecek; bu komut YALNIZCA hazır dosyayı
okur, hiçbir API çağırmaz. Önce --dry-run ile bakılır (rapor 12.8).

    python manage.py baglac_havuzu_yukle havuz.json --dry-run
    python manage.py baglac_havuzu_yukle havuz.json

Dosya: JSON dizi ya da satır başına bir JSON (jsonl). Her kayıt:

    {
      "cumle": "It was raining. ___, we went for a walk.",   # tam olarak bir "___"
      "dogru": "However",
      "celdiriciler": ["Therefore", "For example", "As a result"],  # en az 3
      "cefr": "B1",                                          # A1…C2
      "aciklama": "However: yine de — beklenenin tersi",     # isteğe bağlı, tek satır Türkçe
      "ifade": "however",                                    # isteğe bağlı, Expression.text
      "denetlendi": true,                                    # yalnızca true olanlar soruya girer
      "kaynak": "gemini-2.5-flash + Efe"                     # isteğe bağlı
    }

Kural: şıklardan YALNIZCA biri anlamı doğru verir; noktalama inceliği
sorulmaz. Aynı (cumle, dogru) ikinci kez gelirse güncellenir.
"""

import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from egzersizler.models import BaglacCumlesi
from words.models import CEFR_LEVELS, Expression


def kayitlari_oku(yol):
    with open(yol, encoding="utf-8") as f:
        metin = f.read().strip()
    if not metin:
        return []
    if metin.startswith("["):
        return json.loads(metin)
    return [json.loads(satir) for satir in metin.splitlines() if satir.strip()]


def dogrula(kayit):
    """Hata listesi (boşsa kayıt geçerli)."""
    hatalar = []
    cumle = (kayit.get("cumle") or "").strip()
    dogru = (kayit.get("dogru") or "").strip()
    celdiriciler = [str(c).strip() for c in kayit.get("celdiriciler") or [] if str(c).strip()]
    if cumle.count(BaglacCumlesi.BOSLUK) != 1:
        hatalar.append('cümlede tam olarak bir "___" olmalı')
    if not dogru:
        hatalar.append("doğru cevap boş")
    farkli = {c.lower() for c in celdiriciler} - {dogru.lower()}
    if len(farkli) < 3:
        hatalar.append("doğrudan farklı en az 3 çeldirici gerekli")
    if kayit.get("cefr") not in CEFR_LEVELS:
        hatalar.append("cefr A1…C2 olmalı")
    return hatalar


class Command(BaseCommand):
    help = "D2 bağlaç/ifade cümle havuzunu JSON/JSONL dosyasından yükler."

    def add_arguments(self, parser):
        parser.add_argument("dosya")
        parser.add_argument("--dry-run", action="store_true", help="Yazmadan yalnızca denetle.")

    def handle(self, *args, dosya, dry_run=False, **opts):
        try:
            kayitlar = kayitlari_oku(dosya)
        except (OSError, ValueError) as e:
            raise CommandError(f"Dosya okunamadı: {e}")

        gecerli, hatali = [], 0
        for i, k in enumerate(kayitlar, start=1):
            hatalar = dogrula(k)
            if hatalar:
                hatali += 1
                self.stdout.write(self.style.WARNING(f"{i}. kayıt atlandı: {'; '.join(hatalar)}"))
            else:
                gecerli.append(k)

        self.stdout.write(f"{len(kayitlar)} kayıt: {len(gecerli)} geçerli, {hatali} hatalı.")
        if dry_run:
            self.stdout.write("Deneme (--dry-run): hiçbir şey yazılmadı.")
            return

        yeni = guncel = 0
        with transaction.atomic():
            for k in gecerli:
                ifade = None
                if k.get("ifade"):
                    ifade = Expression.objects.filter(text__iexact=k["ifade"].strip()).first()
                _, olustu = BaglacCumlesi.objects.update_or_create(
                    cumle=k["cumle"].strip(), dogru=k["dogru"].strip(),
                    defaults={
                        "celdiriciler": [str(c).strip() for c in k["celdiriciler"] if str(c).strip()],
                        "cefr": k["cefr"],
                        "aciklama": (k.get("aciklama") or "").strip()[:200],
                        "ifade": ifade,
                        "denetlendi": bool(k.get("denetlendi", False)),
                        "kaynak": (k.get("kaynak") or "").strip()[:80],
                    },
                )
                yeni += olustu
                guncel += not olustu
        self.stdout.write(self.style.SUCCESS(f"{yeni} yeni, {guncel} güncellendi."))
