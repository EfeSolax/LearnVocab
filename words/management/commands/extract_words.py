"""
Metinlerden öğrenilmeye değer kelimeleri çıkarır.

Zenginleştirme hattının ÖN UCU. Hat şöyle işliyor:

    metinler --> extract_words --> listeler/X.txt --> aile_uret --> ara depo

KULLANIM
--------
    # Bir klasördeki bütün metinler
    python manage.py extract_words --dir reading-texts --out listeler/okuma.txt

    # Tek tek dosyalar, rapor da al
    python manage.py extract_words --file a.txt b.txt \
        --out listeler/yeni.txt --report cikarim.json

    # Veritabanında olanları atla, en fazla 500 kelime
    python manage.py extract_words --dir metinler --skip-existing --limit 500

    # Süzgeci gevşet: ilk 1000 kelimeyi atla, daha teknik kelimeleri de al
    python manage.py extract_words --dir metinler --top-skip 1000 --min-zipf 1.5

ÇIKTI
-----
--out dosyası aile_uret'in beklediği biçimde: her satırda bir kelime,
türü biliniyorsa `kelime:tur`. Phrasal verb'ler de aynı dosyada.

--phrasal-out verilirse phrasal verb ADAYLARI ayrı dosyaya yazılıyor.
Bunlar OTOMATİK KABUL EDİLMEZ; göz gezdirilip seçilecek bir karar
listesidir (bkz. words/extract/phrasal.py).
"""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from words.extract import frequency, pipeline
from words.models import Word


class Command(BaseCommand):
    help = "Metinlerden öğrenilmeye değer kelimeleri çıkarır."

    def add_arguments(self, parser):
        parser.add_argument("--dir", help="Metin klasörü (.txt ve .pdf dosyaları)")
        parser.add_argument("--file", nargs="+", help="Tek tek metin ya da PDF dosyaları")
        parser.add_argument("--glob", default="",
                            help="--dir ile kullanılan desen (varsayılan: .txt ve .pdf)")

        parser.add_argument("--out", default="listeler/cikarim.txt",
                            help="Kelime listesi çıktısı")
        parser.add_argument("--report", help="Ayrıntılı JSON rapor")
        parser.add_argument("--phrasal-out",
                            help="Phrasal verb adaylarının yazılacağı dosya")

        parser.add_argument("--top-skip", type=int, default=2000,
                            help="En sık kaç kelime atlansın (varsayılan 2000)")
        parser.add_argument("--min-zipf", type=float,
                            default=frequency.VARSAYILAN_MIN_ZIPF,
                            help="Bu sıklığın altındakiler aşırı teknik sayılır")
        parser.add_argument("--min-count", type=int, default=1,
                            help="Kelime metinde en az kaç kez geçmeli")
        parser.add_argument("--limit", type=int, help="En fazla kaç kelime yazılsın")

        parser.add_argument("--skip-existing", action="store_true",
                            help="Veritabanında olan kelimeleri atla")
        parser.add_argument("--no-pos", action="store_true",
                            help="Tür tahmini yazma (yalnızca kelime)")
        parser.add_argument("--no-phrasal", action="store_true",
                            help="Phrasal verb arama")
        parser.add_argument("--dry-run", action="store_true",
                            help="Dosyaya yazma, yalnızca özet göster")

    # ------------------------------------------------------------------

    def handle(self, *args, **secenekler):
        yollar = self._yollari_topla(secenekler)
        if not yollar:
            raise CommandError("Metin bulunamadı. --dir ya da --file ver.")

        if not frequency.wordfreq_var_mi():
            self.stdout.write(self.style.WARNING(
                "UYARI: `wordfreq` kurulu değil. Sabit liste (5000 kelime) "
                "kullanılıyor; kök bulma ve teknik terim eleme belirgin "
                "biçimde zayıf çalışır.\n"
                "        pip install wordfreq\n"
            ))

        mevcut = set()
        if secenekler["skip_existing"]:
            mevcut = set(Word.objects.values_list("text", flat=True))

        self.stdout.write(f"{len(yollar)} dosya okunuyor…")

        sonuc = pipeline.calistir(
            yollar,
            top_skip=secenekler["top_skip"],
            min_zipf=secenekler["min_zipf"],
            min_count=secenekler["min_count"],
            mevcut_kelimeler=mevcut,
            limit=secenekler["limit"],
            phrasal_dahil=not secenekler["no_phrasal"],
        )

        self._ozet_yaz(sonuc, secenekler)

        if secenekler["dry_run"]:
            self.stdout.write(self.style.WARNING(
                "\nKURU ÇALIŞTIRMA — hiçbir dosya yazılmadı."))
            self._ornek_yaz(sonuc)
            return

        self._liste_yaz(sonuc, secenekler)
        self._phrasal_yaz(sonuc, secenekler)
        self._rapor_yaz(sonuc, secenekler)
        self._ornek_yaz(sonuc)

    # ------------------------------------------------------------------

    def _yollari_topla(self, secenekler):
        yollar = []
        if secenekler.get("dir"):
            klasor = Path(secenekler["dir"])
            if not klasor.is_dir():
                raise CommandError(f"Klasör yok: {klasor}")
            if secenekler["glob"]:
                yollar += sorted(klasor.glob(secenekler["glob"]))
            else:   # varsayılan: .txt ve .pdf (büyük/küçük harf fark etmez)
                yollar += sorted(p for p in klasor.iterdir()
                                 if p.is_file() and p.suffix.lower() in (".txt", ".pdf"))
        for dosya in secenekler.get("file") or []:
            yol = Path(dosya)
            if not yol.is_file():
                raise CommandError(f"Dosya yok: {yol}")
            yollar.append(yol)
        return yollar

    def _ozet_yaz(self, sonuc, secenekler):
        istatistik = sonuc["stats"]
        self.stdout.write("")
        self.stdout.write(
            f"  {istatistik['distinct_lemmas']:>6} farklı kök bulundu")
        self.stdout.write(
            f"  {istatistik['proper_nouns']:>6} özel isim ayıklandı")
        self.stdout.write("")

        for sebep, kelimeler in sorted(sonuc["dropped"].items(),
                                       key=lambda x: -len(x[1])):
            self.stdout.write(f"  {len(kelimeler):>6} elendi — {sebep}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"  {istatistik['kept']:>6} kelime KALDI"))
        if sonuc["phrasal"]:
            self.stdout.write(self.style.SUCCESS(
                f"  {len(sonuc['phrasal']):>6} phrasal verb bulundu"))
        if sonuc["phrasal_candidates"]:
            self.stdout.write(
                f"  {len(sonuc['phrasal_candidates']):>6} phrasal verb ADAYI "
                f"(elle gözden geçirilecek)")

        for yol, hata in istatistik["read_errors"]:
            self.stdout.write(self.style.ERROR(f"  okunamadı: {yol} — {hata}"))

    def _liste_yaz(self, sonuc, secenekler):
        hedef = Path(secenekler["out"])
        hedef.parent.mkdir(parents=True, exist_ok=True)

        satirlar = [
            "# extract_words çıktısı — aile_uret ile okunur.",
            "# Biçim: kelime[:tur]   (tur: noun/verb/adjective/adverb/phrasal_verb)",
            f"# Süzgeç: ilk {secenekler['top_skip']} kelime atlandı, "
            f"min zipf {secenekler['min_zipf']}",
            "",
        ]
        for kayit in sonuc["words"]:
            if kayit["pos"] and not secenekler["no_pos"]:
                satirlar.append(f"{kayit['word']}:{kayit['pos']}")
            else:
                satirlar.append(kayit["word"])

        if sonuc["phrasal"]:
            satirlar += ["", "# --- phrasal verb'ler ---"]
            for kayit in sonuc["phrasal"]:
                satirlar.append(f"{kayit['phrase']}:phrasal_verb")

        hedef.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
        self.stdout.write(f"\nListe yazıldı: {hedef}")

    def _phrasal_yaz(self, sonuc, secenekler):
        if not secenekler.get("phrasal_out") or not sonuc["phrasal_candidates"]:
            return
        hedef = Path(secenekler["phrasal_out"])
        hedef.parent.mkdir(parents=True, exist_ok=True)
        satirlar = [
            "# PHRASAL VERB ADAYLARI — otomatik kabul EDİLMEDİ.",
            "# Bu bir KARAR LİSTESİDİR: anlamı parçalarından çıkmayanları",
            "# seçip words/extract/phrasal.py içindeki KURATORLU kümesine ekle.",
            "",
        ]
        for kayit in sonuc["phrasal_candidates"]:
            satirlar.append(f"{kayit['phrase']}   # {kayit['count']} kez")
        hedef.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
        self.stdout.write(f"Phrasal adayları: {hedef}")

    def _rapor_yaz(self, sonuc, secenekler):
        if not secenekler.get("report"):
            return
        import json

        hedef = Path(secenekler["report"])
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2),
                         encoding="utf-8")
        self.stdout.write(f"Rapor: {hedef}")

    def _ornek_yaz(self, sonuc):
        """İlk 15 kelimeyi ekrana basar — süzgecin çalıştığı görülsün."""
        if not sonuc["words"]:
            return
        self.stdout.write("\n  En çok geçenlerden ilk 15:")
        for kayit in sonuc["words"][:15]:
            tur = f":{kayit['pos']}" if kayit["pos"] else ""
            self.stdout.write(
                f"    {kayit['word'] + tur:<28} {kayit['count']:>3} kez  "
                f"zipf {kayit['zipf']}")
        if sonuc["phrasal"]:
            self.stdout.write("\n  Bulunan phrasal verb'ler:")
            for kayit in sonuc["phrasal"][:10]:
                self.stdout.write(
                    f"    {kayit['phrase']:<28} {kayit['count']:>3} kez")
