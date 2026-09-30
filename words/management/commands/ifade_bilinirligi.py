"""
İfadeleri "yaygın bilinen" / "az bilinen" olarak işaretler (rapor 18.8).
Liste: words/ifadeler/bilinirlik.py. Yeni ifade yüklendikten ya da liste
değiştirildikten sonra çalıştırılır; tekrar çalıştırmak güvenlidir.

    manage.py ifade_bilinirligi
"""

from django.core.management.base import BaseCommand

from words.ifadeler.bilinirlik import AZ, YAYGIN, YAYGIN_IFADELER, bilinirlik
from words.models import Expression


class Command(BaseCommand):
    help = "İfadelerin bilinirliğini (yaygın / az bilinen) listeye göre işaretler."

    def handle(self, *args, **options):
        ifadeler = list(Expression.objects.only("id", "text", "cefr", "bilinirlik"))
        degisen = []
        for ifade in ifadeler:
            yeni = bilinirlik(ifade.text, ifade.cefr)
            if ifade.bilinirlik != yeni:
                ifade.bilinirlik = yeni
                degisen.append(ifade)
        Expression.objects.bulk_update(degisen, ["bilinirlik"], batch_size=500)
        metinler = {i.text.lower() for i in ifadeler}
        olmayan = sorted(YAYGIN_IFADELER - metinler)
        self.stdout.write(f"{len(degisen)} ifade güncellendi. "
                          f"Yaygın: {sum(i.bilinirlik == YAYGIN for i in ifadeler)}, "
                          f"az bilinen: {sum(i.bilinirlik == AZ for i in ifadeler)}.")
        if olmayan:
            self.stdout.write(self.style.WARNING("Listede olup veritabanında olmayan: " + ", ".join(olmayan)))
