"""
Seviye testi okuma havuzunu (D4) bir JSON / JSONL dosyasından yükler.

Biçim: seviye/okuma_bicimi.md

    python manage.py seviye_okuma_yukle havuz.json --dry-run   # önce kontrol
    python manage.py seviye_okuma_yukle havuz.json             # sonra yaz

Aynı metin ikinci kez yüklenirse yeni satır açılmaz, alanları güncellenir.
Hatalı kayıtlar atlanır ve nedeni yazılır; dosyanın geri kalanı yüklenir.
Bu komut hiçbir yapay zekâ çağrısı yapmaz: yalnızca hazır dosyayı okur.
"""

import hashlib
import json
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from seviye.models import OkumaSorusu
from users.seviye import SEVIYELER

EN_AZ_CUMLE = 3
EN_COK_CUMLE = 6
EN_AZ_CELDIRICI = 2
EN_COK_CELDIRICI = 4

_CUMLE_SONU = re.compile(r"[.!?]+(?=\s|$)")


class KayitHatasi(ValueError):
    pass


def dosyayi_oku(yol):
    metin = Path(yol).read_text(encoding="utf-8").strip()
    if not metin:
        return []
    if metin.startswith("["):
        veri = json.loads(metin)
        if not isinstance(veri, list):
            raise CommandError("JSON dosyası bir liste olmalı.")
        return veri
    return [json.loads(satir) for satir in metin.splitlines() if satir.strip()]


def cumle_sayisi(metin):
    return len(_CUMLE_SONU.findall(metin.strip()))


def kaydi_coz(kayit):
    """Bir kaydı doğrular; OkumaSorusu alanları sözlüğünü döner ya da KayitHatasi."""
    if not isinstance(kayit, dict):
        raise KayitHatasi("kayıt bir nesne değil")

    cefr = str(kayit.get("cefr") or "").strip().upper()
    if cefr not in SEVIYELER:
        raise KayitHatasi("'cefr' A1, A2, B1, B2, C1 ya da C2 olmalı")

    metin = " ".join(str(kayit.get("metin") or "").split())
    if not metin:
        raise KayitHatasi("'metin' boş")
    n = cumle_sayisi(metin)
    if not (EN_AZ_CUMLE <= n <= EN_COK_CUMLE):
        raise KayitHatasi(f"metin {EN_AZ_CUMLE}–{EN_COK_CUMLE} cümle olmalı, {n} var")

    dogru = str(kayit.get("dogru") or "").strip()
    if not dogru:
        raise KayitHatasi("'dogru' boş")
    celdiriciler = kayit.get("celdiriciler")
    if not isinstance(celdiriciler, list):
        raise KayitHatasi("'celdiriciler' bir liste olmalı")
    celdiriciler = [str(c).strip() for c in celdiriciler if str(c).strip()]
    if not (EN_AZ_CELDIRICI <= len(celdiriciler) <= EN_COK_CELDIRICI):
        raise KayitHatasi(f"{EN_AZ_CELDIRICI}–{EN_COK_CELDIRICI} çeldirici olmalı")
    siklar = [s.casefold() for s in [dogru, *celdiriciler]]
    if len(set(siklar)) != len(siklar):
        raise KayitHatasi("şıklar birbirinden farklı olmalı")
    if any(len(s) > 400 for s in [dogru, *celdiriciler]):
        raise KayitHatasi("bir şık 400 karakterden uzun")

    return {
        "cefr": cefr,
        "metin": metin,
        "dogru": dogru,
        "celdiriciler": celdiriciler,
        "denetlendi": bool(kayit.get("denetlendi", False)),
        "kaynak": str(kayit.get("kaynak") or "").strip()[:120],
        "anahtar": hashlib.sha1(metin.encode("utf-8")).hexdigest(),
    }


class Command(BaseCommand):
    help = "Seviye testi okuma havuzunu (D4) JSON/JSONL dosyasından yükler. Biçim: seviye/okuma_bicimi.md"

    def add_arguments(self, parser):
        parser.add_argument("dosya", help="JSON listesi ya da JSONL dosyası")
        parser.add_argument("--dry-run", action="store_true", help="Hiçbir şey yazmadan kontrol et.")

    def handle(self, *args, **opts):
        try:
            kayitlar = dosyayi_oku(opts["dosya"])
        except (OSError, ValueError) as exc:
            raise CommandError(f"Dosya okunamadı: {exc}")

        eklenen = guncellenen = atlanan = 0
        with transaction.atomic():
            for sira, kayit in enumerate(kayitlar, start=1):
                try:
                    alanlar = kaydi_coz(kayit)
                except KayitHatasi as exc:
                    atlanan += 1
                    self.stdout.write(f"  atlandı #{sira}: {exc}")
                    continue
                anahtar = alanlar.pop("anahtar")
                var = OkumaSorusu.objects.filter(anahtar=anahtar).exists()
                if not opts["dry_run"]:
                    OkumaSorusu.objects.update_or_create(anahtar=anahtar, defaults=alanlar)
                if var:
                    guncellenen += 1
                else:
                    eklenen += 1

        onek = "(dry-run) " if opts["dry_run"] else ""
        self.stdout.write(f"{onek}{len(kayitlar)} kayıt: {eklenen} yeni, "
                          f"{guncellenen} güncellendi, {atlanan} atlandı.")
