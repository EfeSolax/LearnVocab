"""
Henüz değerlendirilemeyen yazıları yeniden dener (ürün raporu 9.1).

Gemini cevap vermediğinde ya da kota dolduğunda metin kaybolmaz; `bekliyor`
durumunda kalır ve "Yazılarım"da sarı "Henüz değerlendirilmedi" etiketiyle
görünür. Bu komut cron ile ~30 dakikada bir çalışır (cron kurulumu:
uygulama planı adım 11):

    */30 * * * *  cd <proje> && <python> manage.py yazilari_yeniden_dene

Kotaya uyar:
  - Bir çalıştırmada en çok --limit (varsayılan 5) metin denenir.
  - Kota hatası (429) gelince çalıştırma hemen durur; kalanlar sonraki sefere.
  - Son --bekleme dakika içinde denenmiş metin atlanır (varsayılan 25).
  - Eskiden yeniye sırayla; hiç denenmemiş olan önce.

Arka plandaki denemeler kullanıcının günlük hakkından düşmez. Değerlendirme
tamamlanınca `texts.sinyaller.degerlendirildi(yazi, arka_planda=True)`
çağrılır ("Yazın değerlendirildi" bildirimi, adım 11).

Ayrıca bir günden uzun süre önce silinmiş yazıları kalıcı olarak temizler
(silme "Geri al" için yumuşak yapılıyor, bkz. Text.silindi).
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import F
from django.utils import timezone

from texts import degerlendirme as dg
from texts.models import Text, YaziDurumu

VARSAYILAN_LIMIT = 5
VARSAYILAN_BEKLEME_DK = 25
SILINMIS_SAKLAMA = timedelta(days=1)


class Command(BaseCommand):
    help = "Henüz değerlendirilemeyen yazıları kotaya uyarak yeniden dener."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=VARSAYILAN_LIMIT,
                            help="Bir çalıştırmada en çok kaç metin denensin.")
        parser.add_argument("--bekleme", type=int, default=VARSAYILAN_BEKLEME_DK,
                            help="Son kaç dakikada denenmiş metin atlansın.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Yalnızca hangi metinlerin deneneceğini yaz.")

    def handle(self, *args, **opts):
        limit = max(0, opts["limit"])
        esik = timezone.now() - timedelta(minutes=max(0, opts["bekleme"]))

        adaylar = list(
            Text.objects
            .filter(durum=YaziDurumu.BEKLIYOR, silindi__isnull=True)
            .exclude(son_deneme__gte=esik)
            .order_by(F("son_deneme").asc(nulls_first=True), "createdAt")[:limit]
        )

        if opts["dry_run"]:
            for yazi in adaylar:
                self.stdout.write(f"denenecek: #{yazi.pk} ({yazi.owner_id}) deneme={yazi.deneme_sayisi}")
            self.stdout.write(f"{len(adaylar)} metin denenecekti (dry-run).")
            return

        sayac = {}
        for yazi in adaylar:
            sonuc = dg.degerlendir(yazi, arka_planda=True)
            sayac[sonuc] = sayac.get(sonuc, 0) + 1
            if sonuc in (dg.KOTA, dg.YOGUN, dg.YAPILANDIRMA):
                self.stdout.write(f"#{yazi.pk}: {sonuc}; bu çalıştırma durduruldu.")
                break

        _, detay = (Text.objects
                    .filter(silindi__lt=timezone.now() - SILINMIS_SAKLAMA)
                    .delete())
        silinen = detay.get("texts.Text", 0)

        ozet = ", ".join(f"{k}={v}" for k, v in sorted(sayac.items())) or "denenecek metin yok"
        self.stdout.write(f"Yeniden deneme: {ozet}. Temizlenen silinmiş kayıt: {silinen}.")
