# -*- coding: utf-8 -*-
"""
Aile hattının veritabanına yazdığı aileleri siler (test ve yeniden doldurma için).

    python manage.py aile_sil --depo ara-depo-deneme-3          # ne silineceğini göster
    python manage.py aile_sil --depo ara-depo-deneme-3 --evet   # gerçekten sil
    python manage.py aile_sil --hepsi --evet                    # BÜTÜN aileler

Silinen: depodaki aileler.json'da geçen köklerin WordFamily kayıtları ve
onlara bağlı her şey (kelimeler, anlamlar, cümleler, eş dizimler, kalıplar,
çekim biçimleri, bağlar, kullanıcıların bu kelimelere bağlı çalışma
kartları ve listeleri). Artık hiçbir anlamı kalmayan alanlar (Category) da
silinir.

--evet verilmeden hiçbir şey silinmez: yalnızca sayılar basılır. Geri
dönüşü yok; önce bir kez --evet'siz çalıştırıp sayılara bak.

Depodaki cevaplar (anlamlar.jsonl) SİLİNMEZ: aile_doldur sonradan onları
modeli çağırmadan yeniden yazabilir. Yeni cevap istemek için
aile_doldur --yeniden-sor.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.deletion import Collector

from words.aile.depo import Depo
from words.models import Category, WordFamily


class Command(BaseCommand):
    help = "Aile hattının yazdığı aileleri veritabanından siler (--evet ile)."

    def add_arguments(self, c):
        c.add_argument("--depo", default="", help="Bu depodaki ailelerin kökleri silinir.")
        c.add_argument("--hepsi", action="store_true", help="Bütün aileleri sil.")
        c.add_argument("--evet", action="store_true", help="Gerçekten sil.")

    def handle(self, *args, **s):
        if s["hepsi"]:
            aileler = WordFamily.objects.all()
            kapsam = "BÜTÜN aileler"
        else:
            if not s["depo"]:
                raise CommandError("--depo ya da --hepsi ver.")
            kokler = [a["kok"] for a in Depo(s["depo"]).aileler()]
            if not kokler:
                raise CommandError(f"{s['depo']}/aileler.json yok ya da boş.")
            aileler = WordFamily.objects.filter(root__in=kokler)
            kapsam = f"{s['depo']} deposundaki {len(kokler)} kökün aileleri"

        toplayici = Collector(using="default")
        toplayici.collect(list(aileler))
        sayilar = {m._meta.label: len(o) for m, o in toplayici.data.items()}
        for qs in toplayici.fast_deletes:
            adet = qs.count()
            if adet:
                sayilar[qs.model._meta.label] = sayilar.get(qs.model._meta.label, 0) + adet

        self.stdout.write(f"Kapsam: {kapsam}")
        if not sayilar:
            self.stdout.write("Veritabanında silinecek bir şey yok.")
            return
        for etiket, adet in sorted(sayilar.items(), key=lambda x: -x[1]):
            self.stdout.write(f"  {adet:>6}  {etiket}")

        if not s["evet"]:
            self.stdout.write(self.style.WARNING("Hiçbir şey silinmedi. Silmek için: --evet"))
            return

        with transaction.atomic():
            aileler.delete()
            bos_alan, _ = Category.objects.filter(meanings__isnull=True).delete()
        self.stdout.write(self.style.SUCCESS(
            f"Silindi. ({bos_alan} boş alan kaydı da temizlendi.)"))
