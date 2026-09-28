"""
Diyalog havuzunu (D6) bir JSON / JSONL dosyasından yükler.

Biçim: texts/diyalog_bicimi.md

    python manage.py diyalog_yukle havuz.json --dry-run   # önce kontrol
    python manage.py diyalog_yukle havuz.json             # sonra yaz

Kurallar (rapor 12.8): önce --dry-run ile çıktı gözden geçirilir, sonra
gerçek yazım yapılır. Aynı diyalog (kelime + satırlar) ikinci kez yüklenirse
yeni satır açılmaz, alanları güncellenir. Hatalı kayıtlar atlanır ve nedeni
yazılır; dosyanın geri kalanı yüklenir.
"""

import hashlib
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from texts.diyalog import kabul_edilen_bicimler, normalle
from texts.models import Diyalog
from words.models import Meaning, Register, Sentiment, Word

EN_AZ_SATIR = 4
EN_COK_SATIR = 6


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
    # JSONL: her satır bir kayıt
    return [json.loads(satir) for satir in metin.splitlines() if satir.strip()]


def anahtar_uret(kelime, satirlar):
    govde = json.dumps([kelime.pk, satirlar], ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(govde.encode("utf-8")).hexdigest()


def kaydi_coz(kayit):
    """Bir kaydı doğrular; Diyalog alanları sözlüğünü döner ya da KayitHatasi."""
    if not isinstance(kayit, dict):
        raise KayitHatasi("kayıt bir nesne değil")

    ad = str(kayit.get("kelime") or "").strip()
    if not ad:
        raise KayitHatasi("'kelime' boş")
    kelimeler = Word.objects.filter(text__iexact=ad)
    if kayit.get("tur"):
        kelimeler = kelimeler.filter(pos=kayit["tur"])
    kelimeler = list(kelimeler[:2])
    if not kelimeler:
        raise KayitHatasi(f"'{ad}' sözlükte yok")
    if len(kelimeler) > 1:
        raise KayitHatasi(f"'{ad}' birden çok türde var; 'tur' alanını yaz")
    kelime = kelimeler[0]

    satirlar = kayit.get("satirlar")
    if not isinstance(satirlar, list) or not (EN_AZ_SATIR <= len(satirlar) <= EN_COK_SATIR):
        raise KayitHatasi(f"'satirlar' {EN_AZ_SATIR}–{EN_COK_SATIR} satırlık bir liste olmalı")
    temiz = []
    for satir in satirlar:
        if not isinstance(satir, dict) or not str(satir.get("metin") or "").strip():
            raise KayitHatasi("her satırda 'metin' olmalı")
        temiz.append({"kisi": str(satir.get("kisi") or "").strip()[:20],
                      "metin": str(satir["metin"]).strip()})
    bosluk_sayisi = sum(s["metin"].count(Diyalog.BOSLUK) for s in temiz)
    if bosluk_sayisi != 1:
        raise KayitHatasi(f"tam olarak bir boşluk ({Diyalog.BOSLUK}) olmalı, {bosluk_sayisi} var")

    cevap = str(kayit.get("cevap") or "").strip()
    ipucu = str(kayit.get("ipucu") or "").strip()
    if not cevap or not ipucu:
        raise KayitHatasi("'cevap' ve 'ipucu' dolu olmalı")

    register = kayit.get("register") or Register.NEUTRAL
    sentiment = kayit.get("sentiment") or Sentiment.NEUTRAL
    if register not in Register.values:
        raise KayitHatasi(f"bilinmeyen register: {register}")
    if sentiment not in Sentiment.values:
        raise KayitHatasi(f"bilinmeyen sentiment: {sentiment}")

    anlam = None
    if kayit.get("anlam"):
        anlam = Meaning.objects.filter(word=kelime, meaning_tr__iexact=str(kayit["anlam"]).strip()).first()
        if anlam is None:
            raise KayitHatasi(f"'{ad}' için '{kayit['anlam']}' anlamı yok")

    alanlar = {
        "word": kelime,
        "meaning": anlam,
        "satirlar": temiz,
        "cevap": cevap,
        "ipucu": ipucu,
        "not_metni": str(kayit.get("not") or "").strip()[:400],
        "register": register,
        "sentiment": sentiment,
        "cefr": str(kayit.get("cefr") or kelime.cefr or "").strip()[:15],
        "denetlendi": bool(kayit.get("denetlendi", False)),
        "kaynak": str(kayit.get("kaynak") or "").strip()[:120],
    }

    # Cevap kelimenin bir biçimi olmalı (postpone -> postponed); değilse
    # kullanıcının doğru cevabı "yanlış" sayılır.
    bicimler = kabul_edilen_bicimler(Diyalog(word=kelime, cevap=kelime.text))
    if normalle(cevap) not in bicimler:
        raise KayitHatasi(f"'{cevap}', '{kelime.text}' kelimesinin bilinen bir biçimi değil")

    alanlar["anahtar"] = anahtar_uret(kelime, temiz)
    return alanlar


class Command(BaseCommand):
    help = "Diyalog havuzunu (D6) JSON/JSONL dosyasından yükler. Biçim: texts/diyalog_bicimi.md"

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
                var = Diyalog.objects.filter(anahtar=anahtar).exists()
                if not opts["dry_run"]:
                    Diyalog.objects.update_or_create(anahtar=anahtar, defaults=alanlar)
                if var:
                    guncellenen += 1
                else:
                    eklenen += 1

        onek = "(dry-run) " if opts["dry_run"] else ""
        self.stdout.write(f"{onek}{len(kayitlar)} kayıt: {eklenen} yeni, "
                          f"{guncellenen} güncellendi, {atlanan} atlandı.")
