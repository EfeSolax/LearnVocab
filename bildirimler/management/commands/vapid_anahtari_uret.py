"""
VAPID anahtar çifti üretip DOĞRUDAN `.env` dosyasına yazar (rapor 10).

    python manage.py vapid_anahtari_uret --eposta efe@ornek.com

Anahtarlar ekrana BASILMAZ. `.env`'de dolu bir VAPID anahtarı zaten varsa
hiçbir şeye dokunmaz: anahtar değişirse bütün abonelikler geçersiz olur.
Boş satırlar (`VAPID_PUBLIC_KEY=`) doldurulur, eksikler dosyanın sonuna eklenir.
Yazdıktan sonra sunucuyu yeniden başlatmak gerekir (Passenger: tmp/restart.txt).
"""

import base64
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

ANAHTARLAR = ("VAPID_PUBLIC_KEY", "VAPID_PRIVATE_KEY")


def _b64(veri):
    return base64.urlsafe_b64encode(veri).rstrip(b"=").decode("ascii")


def anahtar_cifti_uret():
    """(genel, özel): ikisi de base64url. Genel anahtar tarayıcının
    applicationServerKey'i (65 baytlık sıkıştırılmamış nokta), özel anahtar
    pywebpush'un kabul ettiği 32 baytlık ham değer."""
    ozel = ec.generate_private_key(ec.SECP256R1())
    genel = ozel.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    ham = ozel.private_numbers().private_value.to_bytes(32, "big")
    return _b64(genel), _b64(ham)


def _satirlari_oku(yol):
    return yol.read_text(encoding="utf-8").splitlines() if yol.exists() else []


def _deger(satirlar, ad):
    """`AD=deger` satırının değeri; satır yoksa None."""
    for satir in satirlar:
        s = satir.strip()
        if s.startswith("#") or "=" not in s:
            continue
        anahtar, _, deger = s.partition("=")
        if anahtar.strip().removeprefix("export ").strip() == ad:
            return deger.strip().strip('"').strip("'")
    return None


def _yaz(satirlar, ad, deger):
    for i, satir in enumerate(satirlar):
        s = satir.strip()
        if not s.startswith("#") and "=" in s and s.partition("=")[0].strip() == ad:
            satirlar[i] = f"{ad}={deger}"
            return
    satirlar.append(f"{ad}={deger}")


class Command(BaseCommand):
    help = "VAPID anahtarlarını üretip .env dosyasına yazar (ekrana basmaz)."

    def add_arguments(self, parser):
        parser.add_argument("--env-dosyasi", default=str(Path(settings.BASE_DIR) / ".env"),
                            help="Yazılacak .env dosyası (varsayılan: proje kökündeki .env).")
        parser.add_argument("--eposta", default="",
                            help="VAPID_ADMIN_EMAIL (push servisinin ulaşacağı adres). "
                                 "Doluysa dokunulmaz.")

    def handle(self, *args, **opts):
        yol = Path(opts["env_dosyasi"])
        satirlar = _satirlari_oku(yol)

        dolu = [ad for ad in ANAHTARLAR if _deger(satirlar, ad)]
        if dolu:
            raise CommandError(
                f"{yol} içinde zaten {', '.join(dolu)} var; hiçbir şey değiştirilmedi. "
                "Anahtar değişirse bütün bildirim abonelikleri geçersiz olur. "
                "Gerçekten yenilemek istiyorsan önce o satırları elle sil.")

        genel, ozel = anahtar_cifti_uret()
        if not any(s.strip().startswith("VAPID_") for s in satirlar) and satirlar:
            satirlar += ["", "# Web Push (manage.py vapid_anahtari_uret ile üretildi)"]
        _yaz(satirlar, "VAPID_PUBLIC_KEY", genel)
        _yaz(satirlar, "VAPID_PRIVATE_KEY", ozel)
        if opts["eposta"] and not _deger(satirlar, "VAPID_ADMIN_EMAIL"):
            _yaz(satirlar, "VAPID_ADMIN_EMAIL", opts["eposta"])
        elif _deger(satirlar, "VAPID_ADMIN_EMAIL") is None:
            _yaz(satirlar, "VAPID_ADMIN_EMAIL", "")

        yol.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(
            f"VAPID anahtarları {yol} dosyasına yazıldı (ekrana basılmadı). "
            "Sunucuyu yeniden başlatınca bildirimler açılır."))
        if not _deger(satirlar, "VAPID_ADMIN_EMAIL"):
            self.stdout.write("Not: VAPID_ADMIN_EMAIL boş; DEFAULT_FROM_EMAIL kullanılacak.")
