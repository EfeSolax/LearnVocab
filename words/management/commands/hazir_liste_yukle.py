"""
Hazır listeyi dosyadan yükler (ürün raporu 4.1, veri işi D7).

Dosya biçimi: bir satıra bir kelime, isteğe bağlı tür ':' ile.

    # ODTÜ 101
    ## 1            <- bölüm (hafta ya da konu); sonraki kelimeler bu bölümde
    aim
    aim:fiil
    decide:verb
    carpet:n

Tür yazımları: noun/n/isim, verb/v/fiil, adjective/adj/sıfat, adverb/adv/zarf,
phrasal_verb/pv, preposition/prep/edat, conjunction/conj/bağlaç.
Eşleşmeyenler, çekimden köke bağlananlar (went -> go) ve tür verilmeyip
birden çok türü olanlar raporlanır.

    python manage.py hazir_liste_yukle listeler/odtu-101.txt --ad "ODTÜ 101" \\
        --slug odtu-101 --kurum ODTÜ --dry-run
    ... --yenile            # aynı slug varsa üyeleri baştan yazar
    ... --eslesmeyenler cikti.txt
    ... --gizli             # yayinda=False: Keşfet'te görünmez, gözden geçirilince açılır
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from words.hazir_liste import dosyadan_eslestir
from words.models import HazirListe, HazirListeKelimesi


class Command(BaseCommand):
    help = "Hazır kelime listesini dosyadan yükler (bir satıra bir kelime[:tür])."

    def add_arguments(self, parser):
        parser.add_argument("dosya")
        parser.add_argument("--ad", required=True, help='Listenin adı: "ODTÜ 101"')
        parser.add_argument("--slug", help="Adres parçası (verilmezse addan üretilir)")
        parser.add_argument("--kurum", default="")
        parser.add_argument("--aciklama", default="")
        parser.add_argument("--sira", type=int, default=0)
        parser.add_argument("--gizli", action="store_true", help="Keşfet'te gösterme")
        parser.add_argument("--yenile", action="store_true",
                            help="Aynı slug'lı liste varsa üyelerini baştan yaz")
        parser.add_argument("--eslesmeyenler", help="Eşleşmeyen satırları bu dosyaya yaz")
        parser.add_argument("--dry-run", action="store_true", help="Hiçbir şey yazma, yalnızca raporla")

    def handle(self, *args, **o):
        try:
            with open(o["dosya"], encoding="utf-8") as f:
                satirlar = f.read().splitlines()
        except OSError as hata:
            raise CommandError(f"Dosya okunamadı: {hata}")

        slug = o["slug"] or slugify(o["ad"].replace("ı", "i"))
        if not slug:
            raise CommandError("Geçerli bir --slug verin.")
        mevcut = HazirListe.objects.filter(slug=slug).first()
        if mevcut and not o["yenile"]:
            raise CommandError(f"'{slug}' zaten var. Üyeleri baştan yazmak için --yenile.")

        sonuc = dosyadan_eslestir(satirlar)
        self._rapor(sonuc)

        if o["eslesmeyenler"] and sonuc.eslesmeyenler:
            with open(o["eslesmeyenler"], "w", encoding="utf-8") as f:
                for no, satir, neden in sonuc.eslesmeyenler:
                    f.write(f"{satir}\t# {no}. satır: {neden}\n")
            self.stdout.write(f"Eşleşmeyenler yazıldı: {o['eslesmeyenler']}")

        if o["dry_run"]:
            self.stdout.write(self.style.WARNING("--dry-run: hiçbir şey yazılmadı."))
            return

        with transaction.atomic():
            alanlar = {"ad": o["ad"], "kurum": o["kurum"], "aciklama": o["aciklama"],
                       "sira": o["sira"], "yayinda": not o["gizli"]}
            if mevcut:
                for k, v in alanlar.items():
                    setattr(mevcut, k, v)
                mevcut.save()
                liste = mevcut
                liste.uyelikler.all().delete()
            else:
                liste = HazirListe.objects.create(slug=slug, **alanlar)
            HazirListeKelimesi.objects.bulk_create([
                HazirListeKelimesi(liste=liste, word=w, sira=i, bolum=b, aile=a)
                for i, (w, b, a) in enumerate(zip(sonuc.kelimeler, sonuc.bolumler, sonuc.aileler), start=1)
            ])
        self.stdout.write(self.style.SUCCESS(
            f"“{liste.ad}” ({slug}): {len(sonuc.kelimeler)} kelime yazıldı."))

    def _rapor(self, sonuc):
        self.stdout.write(f"Eşleşen: {len(sonuc.kelimeler)}")
        if sonuc.kokten:
            self.stdout.write(f"Çekimden köke bağlanan ({len(sonuc.kokten)}):")
            for satir, kok in sonuc.kokten:
                self.stdout.write(f"  {satir} -> {kok}")
        if sonuc.belirsiz:
            self.stdout.write(f"Birden çok türü olan, en yaygını seçilen ({len(sonuc.belirsiz)}):")
            for satir, secilen, digerleri in sonuc.belirsiz:
                self.stdout.write(f"  {satir}: {secilen.get_pos_display()} "
                                  f"(diğerleri: {', '.join(w.get_pos_display() for w in digerleri)})")
        if sonuc.tekrarlar:
            self.stdout.write(f"Tekrar eden satır ({len(sonuc.tekrarlar)}): "
                              + ", ".join(f"{no}. {s}" for no, s in sonuc.tekrarlar))
        if sonuc.eslesmeyenler:
            self.stdout.write(self.style.WARNING(f"Eşleşmeyen ({len(sonuc.eslesmeyenler)}):"))
            for no, satir, neden in sonuc.eslesmeyenler:
                self.stdout.write(f"  {no}. {satir}  ({neden})")
