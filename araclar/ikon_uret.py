"""
Site simgelerini mor kitap logosundan (static/images/favicon.jpg) üretir (20 Ekim, Efe'nin seçimi).

    .venv/bin/python araclar/ikon_uret.py

favicon.jpg kare değil (733×708) ve dairenin dışı beyaz. Daire kare kesilir, dışı saydam yapılır:
  - static/images/favicon.ico      16/32/48 px (sekme; kökteki /favicon.ico da bunu sunar)
  - static/pwa/ikon-192.png, ikon-512.png   saydam köşeli (manifest, Google arama simgesi)
  - static/pwa/ikon-maskable-512.png        Android maskesi: daire %80 güvenli alanın içinde
  - static/pwa/apple-touch-icon.png         180 px, saydamlık yok (iOS saydamı siyah boyar)
Logo değişirse KAYNAK ve DAIRE yeniden ölçülür.
"""
from pathlib import Path

from PIL import Image, ImageDraw

KOK = Path(__file__).resolve().parent.parent
KAYNAK = KOK / "static/images/favicon.jpg"
# Mor halkanın dış sınırı (ölçüldü: x 22–703, y 6–685): merkez ve yarıçap
DAIRE = (362.5, 345.5, 341)
ZEMIN = (251, 250, 245, 255)       # defter kâğıdı (#fbfaf5, manifest'teki tema rengi)
MASKE_ZEMINI = (197, 186, 228, 255)  # dairenin iç rengi; maske kırpınca kenar görünmesin


def daire_logo():
    """Daireyi kare keser, dışını yumuşak kenarla saydam yapar."""
    cx, cy, r = DAIRE
    kare = Image.open(KAYNAK).convert("RGBA").crop((round(cx - r), round(cy - r),
                                                    round(cx + r), round(cy + r)))
    boy = kare.size[0]
    buyuk = 4  # kenar yumuşatma için maske dört kat büyük çizilip küçültülür
    maske = Image.new("L", (boy * buyuk, boy * buyuk), 0)
    ImageDraw.Draw(maske).ellipse((0, 0, boy * buyuk - 1, boy * buyuk - 1), fill=255)
    kare.putalpha(maske.resize((boy, boy), Image.LANCZOS))
    return kare


def zeminli(logo, boy, zemin, oran):
    """Logoyu `zemin` renkli kareye, kenarın `oran` kadarını kaplayacak biçimde ortalar."""
    tuval = Image.new("RGBA", (boy, boy), zemin)
    ic = round(boy * oran)
    kucuk = logo.resize((ic, ic), Image.LANCZOS)
    tuval.alpha_composite(kucuk, ((boy - ic) // 2, (boy - ic) // 2))
    return tuval


def main():
    logo = daire_logo()
    logo.save(KOK / "static/images/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    for boy in (192, 512):
        logo.resize((boy, boy), Image.LANCZOS).save(KOK / f"static/pwa/ikon-{boy}.png", optimize=True)
    zeminli(logo, 512, MASKE_ZEMINI, 0.8).save(KOK / "static/pwa/ikon-maskable-512.png", optimize=True)
    zeminli(logo, 180, ZEMIN, 0.9).convert("RGB").save(KOK / "static/pwa/apple-touch-icon.png", optimize=True)
    print("Simgeler yazıldı.")


if __name__ == "__main__":
    main()
