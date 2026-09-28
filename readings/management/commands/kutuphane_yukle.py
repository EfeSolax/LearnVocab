"""
Okuma kütüphanesine metin yükler (rapor 8, veri işi D5).

reading-texts/ klasöründeki kitap metinleri import_readings ile geliyor.
D5'te üretilecek / derlenecek metinler (telifsiz, akademik, hikâye, yapay
zekâ) ise JSON Lines dosyasından, bu komutla yüklenir. Önce --dry-run ile
bakılır, sonra gerçek yazım yapılır (rapor 12.8).

Dosya biçimi — her satır bir metin:

    {"number": 101, "title": "The Lighthouse Keeper", "topic": "hikaye",
     "cefr": "B1", "source": "Yapay zekâ ile üretildi",
     "paragraphs": ["First paragraph…", "Second paragraph…"]}

  - title ve paragraphs (ya da boş satırla ayrılmış tek "body") zorunlu.
  - number verilmezse aynı başlıklı kayıt güncellenir; yoksa en büyük
    numaranın bir fazlası verilir. Tekrar çalıştırmak güvenli.
  - topic: readings.models.TOPICS'teki anahtarlardan biri olmalı; olmayan
    konu uyarı verir (görünen adı anahtarın kendisi, rengi gri olur).
  - cefr: A1–C2 ya da boş.

    python manage.py kutuphane_yukle metinler.jsonl --dry-run
    python manage.py kutuphane_yukle metinler.jsonl
"""

import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Max

from readings.models import TOPIC_LABELS, ReadingText, paragraflara_bol
from words.models import CEFR_LEVELS


def metni_oku(satir, satir_no):
    """JSON satırını doğrular, ReadingText alanlarına çevirir."""
    try:
        veri = json.loads(satir)
    except json.JSONDecodeError as hata:
        raise CommandError(f"{satir_no}. satır JSON değil: {hata}") from hata
    if not isinstance(veri, dict):
        raise CommandError(f"{satir_no}. satır bir nesne olmalı.")

    baslik = str(veri.get("title") or "").strip()
    if isinstance(veri.get("paragraphs"), list):
        paragraflar = [str(p).strip() for p in veri["paragraphs"] if str(p).strip()]
    else:
        paragraflar = paragraflara_bol(str(veri.get("body") or ""))
    if not baslik or not paragraflar:
        raise CommandError(f"{satir_no}. satırda başlık ya da metin eksik.")

    cefr = str(veri.get("cefr") or "").strip().upper()
    if cefr and cefr not in CEFR_LEVELS:
        raise CommandError(f"{satir_no}. satırda bilinmeyen seviye: {cefr}")

    numara = veri.get("number")
    if numara is not None:
        try:
            numara = int(numara)
        except (TypeError, ValueError) as hata:
            raise CommandError(f"{satir_no}. satırda numara sayı değil: {numara}") from hata

    govde = "\n\n".join(paragraflar)
    return {
        "number": numara,
        "title": baslik[:200],
        "topic": str(veri.get("topic") or "").strip()[:20],
        "body": govde,
        "word_count": len(govde.split()),
        "cefr": cefr,
        "source": str(veri.get("source") or "").strip()[:200],
    }


class Command(BaseCommand):
    help = "Okuma kütüphanesine JSON Lines dosyasından metin yükler (D5)."

    def add_arguments(self, parser):
        parser.add_argument("dosya", help="JSON Lines dosyası (satır başına bir metin).")
        parser.add_argument("--dry-run", action="store_true",
                            help="Hiçbir şey yazma, ne olacağını göster.")

    def handle(self, *args, **secenekler):
        try:
            with open(secenekler["dosya"], encoding="utf-8") as f:
                satirlar = [(i, s) for i, s in enumerate(f, 1) if s.strip()]
        except OSError as hata:
            raise CommandError(f"Dosya okunamadı: {hata}") from hata
        if not satirlar:
            raise CommandError("Dosyada metin yok.")

        metinler = [metni_oku(s, i) for i, s in satirlar]

        numaralar = [m["number"] for m in metinler if m["number"] is not None]
        if len(numaralar) != len(set(numaralar)):
            raise CommandError("Dosyada aynı numara birden çok kez geçiyor.")
        bilinmeyen = {m["topic"] for m in metinler} - set(TOPIC_LABELS)
        if bilinmeyen:
            self.stdout.write(self.style.WARNING(
                "Uyarı: TOPICS listesinde olmayan konu(lar): " + ", ".join(sorted(bilinmeyen))))

        eklenen = guncellenen = degismeyen = 0
        with transaction.atomic():
            siradaki = (ReadingText.objects.aggregate(m=Max("number"))["m"] or 0) + 1
            siradaki = max([siradaki] + [n + 1 for n in numaralar])
            for m in metinler:
                alanlar = {k: v for k, v in m.items() if k != "number"}
                if m["number"] is not None:
                    mevcut = ReadingText.objects.filter(number=m["number"]).first()
                else:
                    mevcut = ReadingText.objects.filter(title__iexact=m["title"]).first()

                if mevcut is None:
                    eklenen += 1
                    numara = m["number"]
                    if numara is None:
                        numara, siradaki = siradaki, siradaki + 1
                    if not secenekler["dry_run"]:
                        ReadingText.objects.create(number=numara, **alanlar)
                elif any(getattr(mevcut, k) != v for k, v in alanlar.items()):
                    guncellenen += 1
                    if not secenekler["dry_run"]:
                        for k, v in alanlar.items():
                            setattr(mevcut, k, v)
                        mevcut.save()
                else:
                    degismeyen += 1

        ozet = (f"{len(metinler)} metin okundu — {eklenen} eklendi, "
                f"{guncellenen} güncellendi, {degismeyen} değişmedi")
        if secenekler["dry_run"]:
            ozet += "  (DENEME: hiçbir şey yazılmadı)"
        self.stdout.write(self.style.SUCCESS(ozet))
