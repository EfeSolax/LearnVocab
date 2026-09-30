"""
Kelime sayfalarını partiler hâlinde arama motorlarına açar (rapor 18.15).

    manage.py dizine_ac                              # durum: kaç sayfa açık, kaçı bekliyor
    manage.py dizine_ac --seviye A1 A2 B1 --kaynak oxford --dry-run
    manage.py dizine_ac --seviye A1 A2 B1 --kaynak oxford
    manage.py dizine_ac --seviye B2 --en-cok 1500    # en sık 1500 kelime
    manage.py dizine_ac --ifadeler                   # ifade sayfaları
    manage.py dizine_ac --kapat-hepsi                # hepsini yeniden kapat

Kurallar words/dizine_alma.py'de. Bir kez açılan sayfa kendiliğinden
kapanmaz; veri sonradan bozulursa admin'den "Google'a açık" işareti kaldırılır.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count

from words import dizine_alma
from words.models import CEFR_LEVELS, Expression, Word


class Command(BaseCommand):
    help = "Kelime sayfalarını partiler hâlinde arama motorlarına açar."

    def add_arguments(self, parser):
        parser.add_argument("--seviye", nargs="+", choices=CEFR_LEVELS, help="Yalnızca bu seviyeler.")
        parser.add_argument("--kaynak", choices=["oxford", "cambridge", "learnvocab"],
                            help="Yalnızca seviyesi bu kaynaktan gelenler.")
        parser.add_argument("--en-az-siklik", type=float, help="Zipf alt sınırı (varsayılan 2,3).")
        parser.add_argument("--en-cok", type=int, help="En çok bu kadar kelime açılır (sık olan önce).")
        parser.add_argument("--ifadeler", action="store_true", help="İfade sayfalarını aç.")
        parser.add_argument("--kapat-hepsi", action="store_true", help="Bütün sayfaları kapat.")
        parser.add_argument("--dry-run", action="store_true", help="Yazmadan yalnızca say.")

    def handle(self, *args, **o):
        if o["kapat_hepsi"]:
            if not o["dry_run"]:
                Word.objects.filter(dizinde=True).update(dizinde=False)
                Expression.objects.filter(dizinde=True).update(dizinde=False)
            self.stdout.write("Bütün kelime ve ifade sayfaları kapatıldı.")
            return self._durum()

        secim_var = o["ifadeler"] or o["seviye"] or o["kaynak"] or o["en_cok"] or o["en_az_siklik"]
        if not secim_var:
            return self._durum()

        if o["ifadeler"]:
            ifadeler = dizine_alma.uygun_ifadeler().filter(dizinde=False)
            sayi = ifadeler.count()
            if not o["dry_run"]:
                ifadeler.update(dizinde=True)
            self.stdout.write(f"İfade: {sayi} sayfa {'açılacak' if o['dry_run'] else 'açıldı'}.")

        if o["seviye"] or o["kaynak"] or o["en_cok"] or o["en_az_siklik"]:
            sirali = dizine_alma.siradaki_kelimeler(o["seviye"], o["kaynak"], o["en_az_siklik"])
            idler = list(sirali.values_list("id", flat=True)[:o["en_cok"]] if o["en_cok"]
                         else sirali.values_list("id", flat=True))
            secilen = Word.objects.filter(id__in=idler)
            sayfa = secilen.values("slug").distinct().count()
            ornek = ", ".join(secilen.order_by("-siklik").values_list("text", flat=True)[:8])
            if not o["dry_run"]:
                secilen.update(dizinde=True)
            self.stdout.write(f"Kelime: {len(idler)} kayıt, {sayfa} sayfa "
                              f"{'açılacak' if o['dry_run'] else 'açıldı'}. Örnek: {ornek}")
        self._durum()

    def _durum(self):
        acik = Word.objects.filter(dizinde=True)
        self.stdout.write(f"\nAçık kelime sayfası: {acik.values('slug').distinct().count()} "
                          f"(ifade: {Expression.objects.filter(dizinde=True).count()})")
        bekleyen = (dizine_alma.uygun_kelimeler().filter(dizinde=False)
                    .values("cefr", "cefr_kaynak").annotate(n=Count("id")).order_by("cefr", "cefr_kaynak"))
        self.stdout.write("Uygun ama kapalı (seviye / kaynak / kayıt):")
        for satir in bekleyen:
            self.stdout.write(f"  {satir['cefr']:<14} {satir['cefr_kaynak']:<11} {satir['n']}")
        uygunsuz = Word.objects.count() - dizine_alma.uygun_kelimeler().count()
        self.stdout.write(f"Uygun olmayan (seyrek ya da eksik içerik): {uygunsuz}")
