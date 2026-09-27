# -*- coding: utf-8 -*-
"""
2. AŞAMA — ara depodaki taslakları aileye indirir ve raporlar.

    python manage.py aile_birlestir
    python manage.py aile_birlestir --esik 0.6      # örtüşme eşiği
    python manage.py aile_birlestir --goster analyse

Okur:   ara-depo/taslaklar.jsonl, ara-depo/kararlar.json
Yazar:  ara-depo/aileler.json, ara-depo/birlestirme-raporu.txt

VERİTABANINA YAZMAZ, yalnızca okur: birleşen ailelerin kelimeleri
veritabanında BAŞKA bir ailede kayıtlıysa raporda "db_farkli_aile" olarak
gösterilir. Bu bir hata değil; eski hattın kurduğu aileler yenisiyle
çelişiyor olabilir ve 3. aşama yazmadan önce bunun görülmesi gerekiyor.

Her çalıştırma sıfırdan hesaplar; bu yüzden kararlar.json'a karar ekleyip
tekrar çalıştırmak güvenli. Tipik döngü:

    aile_birlestir  ->  raporda İNCELENECEK'lere bak  ->  kararlar.json
    ->  aile_birlestir  ->  ...
"""

from django.core.management.base import BaseCommand

from words.aile import birlestir
from words.aile.depo import AILELER, KARARLAR, RAPOR, Depo
from words.models import Word


class Command(BaseCommand):
    help = "2. aşama: aile taslaklarını birleştirir, örtüşmeyenleri raporlar."

    def add_arguments(self, cozumleyici):
        cozumleyici.add_argument("--depo", default="", help="Ara depo klasörü.")
        cozumleyici.add_argument("--esik", type=float, default=birlestir.ORTUSME_ESIGI,
                                 help="Bunun altındaki örtüşme 'incelenecek' sayılır.")
        cozumleyici.add_argument("--goster", default="",
                                 help="Yalnızca bu kökün ailesini ayrıntılı bas.")

    def handle(self, *args, **secenekler):
        depo = Depo(secenekler["depo"] or None)
        taslaklar = depo.guncel_taslaklar()
        if not taslaklar:
            self.stdout.write(f"Depoda taslak yok ({depo.yol}). Önce: manage.py aile_uret")
            return

        kararlar = depo.kararlar()
        aileler, disarida = birlestir.birlestir(taslaklar, kararlar, secenekler["esik"])
        self._veritabani_ile_karsilastir(aileler)
        ozet = birlestir.ozet(aileler, disarida)

        rapor = rapor_metni(aileler, disarida, ozet, secenekler["esik"])
        depo.aileleri_yaz(aileler, ozet, rapor)

        if secenekler["goster"]:
            hedef = [a for a in aileler if a["kok"] == secenekler["goster"].lower()]
            if not hedef:
                self.stdout.write(f"'{secenekler['goster']}' köklü aile yok.")
            for aile in hedef:
                self.stdout.write(aile_metni(aile, ayrintili=True))
            return

        self.stdout.write(f"{len(taslaklar)} taslak → {ozet['aile']} aile, "
                          f"{ozet['kelime']} kelime")
        self.stdout.write(self.style.SUCCESS(f"  temiz        {ozet['temiz']}"))
        stil = self.style.WARNING if ozet["incelenecek"] else self.style.SUCCESS
        self.stdout.write(stil(f"  incelenecek  {ozet['incelenecek']}"))
        self.stdout.write(f"  tek taslaklı {ozet['tek_taslakli']} "
                          f"(karşılaştırılacak ikinci cevap yok)")
        if ozet["ortalama_ortusme"] is not None:
            self.stdout.write(f"  ortalama örtüşme ({ozet['cok_taslakli']} çok taslaklı "
                              f"ailede): {ozet['ortalama_ortusme']}")
        for durum, adet in ozet["disarida"].items():
            self.stdout.write(self.style.WARNING(f"  birleştirmeye girmeyen taslak: "
                                                 f"{adet} {durum}"))
        if ozet["sorun_kodlari"]:
            self.stdout.write("Bulgular:")
            for kod, adet in ozet["sorun_kodlari"].items():
                self.stdout.write(f"  {adet:>4}  {kod}")

        for aile in [a for a in aileler if a["durum"] == "incelenecek"][:10]:
            self.stdout.write("")
            self.stdout.write(aile_metni(aile, ayrintili=True))
        if ozet["incelenecek"] > 10:
            self.stdout.write(f"\n… ve {ozet['incelenecek'] - 10} tane daha (rapora bak).")

        self.stdout.write("")
        self.stdout.write(f"Rapor:    {depo.yol / RAPOR}")
        self.stdout.write(f"Aileler:  {depo.yol / AILELER}")
        self.stdout.write(f"Kararlar: {depo.yol / KARARLAR}")

    def _veritabani_ile_karsilastir(self, aileler):
        """Yalnızca okur: üyeler veritabanında başka bir aileye mi kayıtlı?"""
        for aile in aileler:
            metinler = [u["word"] for u in aile["uyeler"]]
            farkli = {}
            for kelime in (Word.objects.filter(text__in=metinler, isBaseWord=True)
                           .select_related("family")):
                if kelime.family.root != aile["kok"]:
                    farkli.setdefault(kelime.family.root, []).append(kelime.text)
            if farkli:
                aile["sorunlar"].append({
                    "kod": "db_farkli_aile",
                    "mesaj": "Veritabanında başka aileye kayıtlı: " + "; ".join(
                        f"{', '.join(sorted(set(k)))} → '{kok}'" for kok, k in farkli.items())})


# ----------------------------------------------------------------------
# Rapor
# ----------------------------------------------------------------------

def _uye_satiri(uye, n):
    tur = uye["type"].replace("_", " ")
    destek = f" {uye['oy']}/{n}" if n > 1 else ""
    return f"{uye['word']} ({tur}{destek})"


def aile_metni(aile, ayrintili=False):
    n = aile["taslak_sayisi"]
    satirlar = [f"■ {aile['kok']}  [{aile['durum'].upper()}]  "
                f"{n} taslak · tohumlar: {', '.join(aile['tohumlar'])}"
                + (f" · örtüşme {aile['ortusme']['ortalama']}" if aile["ortusme"] else "")]
    satirlar.append("   " + ", ".join(_uye_satiri(u, n) for u in aile["uyeler"]))
    for sorun in aile["sorunlar"]:
        satirlar.append(f"   ! [{sorun['kod']}] {sorun['mesaj']}")
    if ayrintili and n > 1:
        for t in aile["taslaklar"]:
            ek = f"  · yalnız bunda: {', '.join(t['yalniz_bunda'])}" if t["yalniz_bunda"] else ""
            satirlar.append(f"     {t['tohum']:>18} → {t['kok']}: {', '.join(t['uyeler'])}{ek}")
    if ayrintili and aile["taslak_uyarilari"]:
        for uyari in aile["taslak_uyarilari"]:
            satirlar.append(f"     · {uyari}")
    return "\n".join(satirlar)


def rapor_metni(aileler, disarida, ozet, esik):
    s = []
    s.append("LEARNVOCAB — AİLE BİRLEŞTİRME RAPORU")
    s.append("=" * 70)
    s.append(f"{ozet['aile']} aile · {ozet['kelime']} kelime · "
             f"{ozet['temiz']} temiz · {ozet['incelenecek']} incelenecek")
    s.append(f"Tek taslaklı aile: {ozet['tek_taslakli']} · örtüşme eşiği: {esik}"
             + (f" · ortalama örtüşme: {ozet['ortalama_ortusme']}"
                if ozet["ortalama_ortusme"] is not None else ""))
    if ozet["sorun_kodlari"]:
        s.append("Bulgular: " + ", ".join(f"{k} {v}" for k, v in ozet["sorun_kodlari"].items()))
    s.append("")
    s.append("KARAR VERMEK İÇİN: ara-depo/kararlar.json")
    s.append("  kok_esle  iki kökü aynı aile say        {\"analysis\": \"analyse\"}")
    s.append("  ayri_tut  ortak kelimesi olsa da ayır    [[\"consent\", \"consensus\"]]")
    s.append("  cikar     aileden kelime çıkar          {\"consent\": [\"consensus\"]}")
    s.append("  uye_ata   paylaşılan kelimenin sahibi    {\"consensus\": \"consensus\"}")
    s.append("  onayla    incelenecek aileyi kabul et    [\"analyse\"]")
    s.append("Sonra tekrar:  python manage.py aile_birlestir")

    incelenecek = [a for a in aileler if a["durum"] == "incelenecek"]
    if incelenecek:
        s.append("")
        s.append("=" * 70)
        s.append(f"İNCELENECEK ({len(incelenecek)})")
        s.append("=" * 70)
        for aile in incelenecek:
            s.append(aile_metni(aile, ayrintili=True))
            s.append("")

    temiz = [a for a in aileler if a["durum"] == "temiz"]
    if temiz:
        s.append("=" * 70)
        s.append(f"TEMİZ ({len(temiz)})")
        s.append("=" * 70)
        for aile in temiz:
            s.append(aile_metni(aile))

    if disarida:
        s.append("")
        s.append("=" * 70)
        s.append(f"BİRLEŞTİRMEYE GİRMEYEN TASLAKLAR ({len(disarida)})")
        s.append("=" * 70)
        for t in disarida:
            neden = "; ".join(f"[{x['kod']}] {x['mesaj']}" for x in t.get("sorunlar", [])
                              if x.get("seviye") == "hata") or t.get("mesaj", "")
            s.append(f"  {t.get('tohum')}: {t.get('durum')} — {neden}")
    return "\n".join(s) + "\n"
