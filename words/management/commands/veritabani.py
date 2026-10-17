"""
Canlı veritabanı <-> SQLite dosyası (ayrıntı: LearnVocab/veritabani_esitleme.py).

  python manage.py veritabani indir canli.sqlite3
      Canlı veritabanının (MySQL) tam kopyası yeni bir SQLite dosyasına.

  python manage.py veritabani yukle canli.sqlite3              # kuru deneme: yalnızca rapor
  python manage.py veritabani yukle canli.sqlite3 --uygula     # içerik tablolarını yazar (önce tam yedek)
  python manage.py veritabani yukle ilk.sqlite3 --hepsi --uygula
      İlk taşıma: canlıdaki BÜTÜN tablolar boşaltılıp dosyadan doldurulur (onay sorar).

Yerelde dosyayla çalışmak:  DB_NAME=canli.sqlite3 python manage.py runserver
"""

import os

from django.core.management.base import BaseCommand, CommandError

from LearnVocab import veritabani_esitleme as ve


class Command(BaseCommand):
    help = "Canlı veritabanını SQLite dosyasına indirir ya da dosyadaki içeriği canlıya yükler."

    def add_arguments(self, parser):
        parser.add_argument("islem", choices=["indir", "yukle"])
        parser.add_argument("dosya", help="SQLite dosyasının yolu")
        parser.add_argument("--uygula", action="store_true", help="yukle: gerçekten yaz (yoksa kuru deneme)")
        parser.add_argument("--hepsi", action="store_true",
                            help="yukle: BÜTÜN tabloları dosyadakiyle değiştir (ilk taşıma)")
        parser.add_argument("--zorla", action="store_true",
                            help="yukle: dosya indirildikten sonra canlıda değişen içerik tablolarını da ez")
        parser.add_argument("--yedek-klasoru", default=os.path.expanduser("~/veritabani-yedekleri"),
                            help="yukle --uygula öncesi tam yedeğin yazılacağı klasör")
        parser.add_argument("--evet", action="store_true", help="--hepsi onayını sormadan geç")

    def handle(self, islem, dosya, uygula, hepsi, zorla, yedek_klasoru, evet, **_):
        rapor = self.stdout.write
        try:
            if islem == "indir":
                ve.indir(dosya, rapor=rapor)
                return
            if hepsi and uygula and not evet:
                cevap = input("Canlıdaki BÜTÜN veriler (kullanıcılar dahil) silinip dosyadakiyle değiştirilecek. "
                              "Devam etmek için EVET yaz: ")
                if cevap.strip() != "EVET":
                    raise CommandError("Vazgeçildi.")
            sonuc = ve.yukle(dosya, uygula=uygula, hepsi=hepsi, zorla=zorla,
                             yedek_klasoru=yedek_klasoru, rapor=rapor)
        except ve.EsitlemeHatasi as hata:
            raise CommandError(str(hata)) from hata

        if not hepsi:
            rapor("\nTablo                               eklenen  güncellenen  silinen")
            for tablo, (e, g, s) in sorted(sonuc["ozet"].items()):
                if e or g or s:
                    rapor(f"{tablo:<36}{e:>7}{g:>13}{s:>9}")
            icerik = {m._meta.label for t, m in ve.modeller().items() if t in ve.ICERIK}
            bagli = {k: n for k, n in sonuc["etkiler"].items() if k not in icerik and n}
            if bagli:
                rapor("\nSilinen içeriğe bağlı olduğu için birlikte silinecek kullanıcı kayıtları:")
                for etiket, n in sorted(bagli.items()):
                    rapor(f"  {etiket}: {n}")
        if uygula:
            rapor(self.style.SUCCESS("\nYazıldı. Önbellek temizlendi; uygulamayı yeniden başlat "
                                     "(Passenger: touch tmp/restart.txt)."))
        else:
            rapor(self.style.WARNING("\nKURU DENEME: hiçbir şey yazılmadı. Yazmak için --uygula ekle."))
