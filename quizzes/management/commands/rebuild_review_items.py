"""
Çalışma kartlarını toptan tamamlar.

Ne zaman gerekir:
  - Zenginleştirme hattı çalıştıktan sonra. Yeni eş dizimler, kalıplar,
    yanlış dostlar geldiğinde kartları da açılsın diye.
  - Kelime listesine toplu ekleme yapıldığında.
  - Yeni bir boyut eklendiğinde (geriye dönük kart açmak için).

Normalde buna gerek yok: kullanıcı çalışma sayfasını açtığında giriş
kartları kendiliğinden tamamlanıyor (views.studyHome -> ensure_all_entry_items).
Bu komut aynı işi bütün kullanıcılar için ve üst kademeleri de kapsayarak
yapıyor.

Kullanımı:
    python manage.py rebuild_review_items              # herkes
    python manage.py rebuild_review_items --user efe   # tek kullanıcı
    python manage.py rebuild_review_items --dry-run    # yalnızca say
"""

from django.core.management.base import BaseCommand

from users.models import User

from ... import build
from ...models import ReviewItem


class Command(BaseCommand):
    help = "Kullanıcıların çalışma kartlarını eksiksiz hâle getirir."

    def add_arguments(self, parser):
        parser.add_argument("--user", help="Yalnızca bu kullanıcı adı için")
        parser.add_argument("--dry-run", action="store_true",
                            help="Hiçbir şey yazma, yalnızca durumu göster")

    def handle(self, *args, **secenekler):
        kullanicilar = User.objects.all()
        if secenekler.get("user"):
            kullanicilar = kullanicilar.filter(username=secenekler["user"])
            if not kullanicilar.exists():
                self.stderr.write(f"Kullanıcı bulunamadı: {secenekler['user']}")
                return

        kuru = secenekler.get("dry_run")
        toplam_acilan = 0

        for kullanici in kullanicilar:
            onceki = ReviewItem.objects.filter(user=kullanici).count()
            kelime_sayisi = build.user_words(kullanici).count()

            if kuru:
                self.stdout.write(
                    f"{kullanici.username:<20} {kelime_sayisi:>5} kelime · "
                    f"{onceki:>5} kart (kuru çalıştırma)"
                )
                continue

            acilan = build.ensure_all_entry_items(kullanici)

            # Üst kademeler: kararlılığı eşiği geçmiş kartların üstünü aç.
            # Bu, boyut tanımları değiştiğinde geriye dönük düzeltme yapar.
            for kart in ReviewItem.objects.filter(user=kullanici).exclude(stability=None):
                acilan += build.unlock_after_review(kart)

            toplam_acilan += acilan
            sonraki = ReviewItem.objects.filter(user=kullanici).count()
            self.stdout.write(
                f"{kullanici.username:<20} {kelime_sayisi:>5} kelime · "
                f"{onceki:>5} -> {sonraki:>5} kart (+{acilan})"
            )

        if not kuru:
            self.stdout.write(self.style.SUCCESS(
                f"\nToplam {toplam_acilan} yeni kart açıldı."
            ))
