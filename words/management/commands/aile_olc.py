# -*- coding: utf-8 -*-
"""
Aile hattında MODELİN KALİTESİNİ ölçer (beklentili 40 kelimelik liste).

    python manage.py aile_olc --write                     # listeyi yaz
    python manage.py aile_uret --file listeler/aile-deneme.txt --depo ara-depo-deneme-2
    python manage.py aile_birlestir --depo ara-depo-deneme-2
    python manage.py aile_olc --depo ara-depo-deneme-2      # puanla
    python manage.py aile_olc --depo ara-depo-deneme-2 --only-fail

Beklentiler: words/aile/deneme.py

İKİ TÜR ÖLÇÜ
------------
DOĞRULUK   Beklentisi olan her kelime için: kök doğru mu, olması gereken
           kelimeler var mı, olmaması gerekenler yok mu. A grubunda ayrıca:
           aynı aileden gelen kelimeler birleştirmede TEK aileye düştü mü.

DAVRANIŞ   Beklenti gerektirmeyen, bütün taslaklardan sayılan oranlar.
           Asıl liste (binlerce kelime) çalışırken de aynı sayılar
           izlenebilsin diye ayrı tutuluyor:
             uydurma oranı   modelin yazdığı üyelerin yüzde kaçı
                             İngilizcede yok (olmayan_kelime)
             çekim ihlali    -ed/-ing çekimini kelime diye yazma oranı
             kök düzeltme    kökü kodun düzeltmek zorunda kaldığı taslaklar
             örtüşme         aynı aileden gelen taslakların benzerliği

TOPLAM PUAN BİR NOT DEĞİL. Prompt değiştikçe sayıların hangi yöne
gittiğine bakılır. Karşılaştırmak için her denemeyi ayrı bir depoya yaz
(--depo ara-depo-deneme-2) ya da eski depoyu sil.
"""

from collections import Counter, defaultdict
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from words.aile.deneme import GRUP_ADLARI, SON_SURUM, SURUMLER, liste_metni
from words.aile.depo import Depo

VARSAYILAN_LISTE = "listeler/aile-deneme-{surum}.txt"


class Command(BaseCommand):
    help = "Aile hattının model kalitesini beklentili deneme listesiyle ölçer."

    def add_arguments(self, cozumleyici):
        cozumleyici.add_argument("--write", action="store_true",
                                 help="Deneme listesini listeler/aile-deneme-<sürüm>.txt'ye yaz.")
        cozumleyici.add_argument("--surum", default=SON_SURUM, choices=sorted(SURUMLER),
                                 help=f"Hangi beklenti listesi (varsayılan: {SON_SURUM}).")
        cozumleyici.add_argument("--depo", default="",
                                 help="Ölçülecek ara depo (varsayılan: ara-depo-deneme-<sürüm>).")
        cozumleyici.add_argument("--only-fail", action="store_true",
                                 help="Yalnızca beklentiyi tutturamayanları bas.")

    def handle(self, *args, **secenekler):
        surum = secenekler["surum"]
        self.beklentiler = SURUMLER[surum]
        if secenekler["write"]:
            ad = VARSAYILAN_LISTE.format(surum=surum)
            (Path(settings.BASE_DIR) / ad).write_text(liste_metni(surum), encoding="utf-8")
            self.stdout.write(f"{len(self.beklentiler)} kelime yazıldı: {ad}")
            return

        depo_yolu = Path(secenekler["depo"] or f"ara-depo-deneme-{surum}")
        if not depo_yolu.is_absolute():
            depo_yolu = Path(settings.BASE_DIR) / depo_yolu
        depo = Depo(depo_yolu)
        taslaklar = {t["tohum"]: t for t in depo.guncel_taslaklar()}
        if not taslaklar:
            self.stdout.write(f"Depo boş: {depo.yol}. Önce aile_uret çalıştır.")
            return
        aileler = depo.aileler()
        aile_bul = {}
        for aile in aileler:
            for tohum in aile["tohumlar"]:
                aile_bul.setdefault(tohum, aile["kok"])
        for aile in aileler:
            for uye in aile["uyeler"]:
                aile_bul.setdefault(uye["word"], aile["kok"])

        self._dogruluk(taslaklar, aile_bul, bool(aileler), secenekler["only_fail"], aileler)
        self._davranis(list(taslaklar.values()), aileler)

    # ------------------------------------------------------------------

    def _dogruluk(self, taslaklar, aile_bul, birlesti, yalniz_hata, aileler=()):
        """
        Beklentiler BİRLEŞİK AİLE üzerinden ölçülüyor: veritabanına giren
        şey o. (3. denemeye kadar tek tek cevaplar üzerinden ölçülüyordu;
        prediction'ın cevabında predictable yoktu ama birleşik ailede vardı
        ve bu, hatanın olmadığı yerde hata gösteriyordu.) Tek cevapların
        kök doğruluğu ayrı bir satır olarak basılıyor: modelin kendisinin
        ne kadar isabetli olduğunu o söylüyor.
        """
        self.stdout.write("DOĞRULUK (beklentili liste · birleşik aile üzerinden)"
                          if birlesti else "DOĞRULUK (beklentili liste · TEK CEVAPLAR)")
        self.stdout.write("=" * 70)
        if not birlesti:
            self.stdout.write(self.style.WARNING(
                "Birleştirme çalıştırılmamış; tek cevaplar ölçülüyor. "
                "Önce: manage.py aile_birlestir --depo <aynı depo>"))
        uyeler_of = {a["kok"]: {u["word"] for u in a["uyeler"]} for a in aileler}
        puan = defaultdict(lambda: [0, 0])      # grup -> [geçen, toplam]
        tek_dogru = tek_toplam = 0
        eksik = []

        for b in self.beklentiler:
            t = taslaklar.get(b["tohum"])
            if t is None:
                eksik.append(b["tohum"])
                continue
            if t.get("durum") == "tamam":
                tek_toplam += 1
                tek_dogru += int(t["kok"] in b["kok"])

            hatalar = []
            if birlesti:
                kok = aile_bul.get(b["tohum"])
                metinler = uyeler_of.get(kok, set())
                if kok is None:
                    hatalar.append(f"birleşik ailelerde yok (taslak {t.get('durum')})")
            else:
                kok = t.get("kok")
                metinler = {u["word"] for u in t.get("uyeler", [])}
                if t.get("durum") != "tamam":
                    hatalar.append(f"taslak {t.get('durum')}")
            if kok is not None and not hatalar:
                if kok not in b["kok"]:
                    hatalar.append(f"kök '{kok}' (beklenen: {'/'.join(b['kok'])})")
                for k in b.get("icermeli", []):
                    if k not in metinler:
                        hatalar.append(f"'{k}' yok")
                for k in b.get("icermemeli", []):
                    if k in metinler:
                        hatalar.append(f"'{k}' OLMAMALIYDI")

            grup = puan[b["grup"]]
            grup[1] += 1
            if not hatalar:
                grup[0] += 1
            if hatalar or not yalniz_hata:
                isaret = self.style.SUCCESS("✓") if not hatalar else self.style.ERROR("X")
                satir = f"{isaret} [{b['grup']}] {b['tohum']:<17} → {kok or '?'}"
                if hatalar:
                    satir += "   " + "; ".join(hatalar)
                self.stdout.write(satir)

        # A grubu: aynı etiketli tohumlar tek birleşik aileye düştü mü?
        self.stdout.write("")
        if birlesti:
            self.stdout.write("Tutarlılık (birleştirme sonrası tek aile mi):")
            etiketler = defaultdict(list)
            beklenen_kok = defaultdict(set)
            for b in self.beklentiler:
                if b.get("aile"):
                    etiketler[b["aile"]].append(b["tohum"])
                    beklenen_kok[b["aile"]] |= set(b["kok"])
            tek = 0
            for etiket, tohumlar in etiketler.items():
                vardiklari = {aile_bul.get(t, "?") for t in tohumlar}
                if len(vardiklari) == 1 and vardiklari <= beklenen_kok[etiket]:
                    tek += 1
                    if not yalniz_hata:
                        self.stdout.write(f"  ✓ {etiket}: {', '.join(tohumlar)}")
                else:
                    ayrinti = ", ".join(f"{t}→{aile_bul.get(t, '?')}" for t in tohumlar)
                    ayrinti += f"  (beklenen kök: {'/'.join(sorted(beklenen_kok[etiket]))})"
                    self.stdout.write(self.style.ERROR(f"  X {etiket}: {ayrinti}"))
            puan["A-birleşik"] = [tek, len(etiketler)]

        self.stdout.write("")
        toplam_gecen = toplam = 0
        for grup, (gecen, adet) in sorted(puan.items()):
            ad = GRUP_ADLARI.get(grup, "aynı aileye düşenler")
            self.stdout.write(f"  {grup:<11} {ad:<22} {gecen}/{adet}")
            toplam_gecen += gecen
            toplam += adet
        self.stdout.write(self.style.SUCCESS(f"  TOPLAM      {toplam_gecen}/{toplam}"))
        if tek_toplam:
            self.stdout.write(f"  (tek cevapların kök doğruluğu: {tek_dogru}/{tek_toplam} — "
                              f"modelin kendi isabeti, birleştirmeden önce)")
        if eksik:
            self.stdout.write(self.style.WARNING(
                f"  Depoda cevabı olmayan: {', '.join(eksik)}"))

    def _davranis(self, taslaklar, aileler):
        self.stdout.write("")
        self.stdout.write("DAVRANIŞ (bütün taslaklar)")
        self.stdout.write("=" * 70)
        durum = Counter(t.get("durum") for t in taslaklar)
        gecerli = [t for t in taslaklar if t.get("durum") in ("tamam", "kusurlu")]

        yazilan = sum(len(t.get("uyeler", [])) + len(t.get("ayiklanan", [])) for t in gecerli)
        sebepler = Counter(a["sebep"] for t in gecerli for a in t.get("ayiklanan", []))
        kodlar = Counter(s["kod"] for t in gecerli for s in t.get("sorunlar", []))
        kok_duzeltilen = sum(1 for t in gecerli if any(
            s["kod"] in ("onekli_kok_duzeltildi", "zarf_kok_duzeltildi")
            for s in t.get("sorunlar", [])))

        def oran(pay, payda):
            return f"{pay}/{payda} (%{100 * pay / payda:.1f})" if payda else "—"

        self.stdout.write(f"  taslak                 {len(taslaklar)}  "
                          + " · ".join(f"{k}: {v}" for k, v in durum.items()))
        self.stdout.write(f"  modelin yazdığı üye    {yazilan}  "
                          f"(ortalama aile: {yazilan / max(len(gecerli), 1):.1f})")
        self.stdout.write(f"  uydurma kelime         {oran(sebepler['olmayan_kelime'], yazilan)}")
        self.stdout.write(f"  çok nadir (atılan)     {oran(sebepler['cok_nadir'], yazilan)}")
        self.stdout.write(f"  çekimi kelime sanma    {oran(sebepler['cekim_uyesi'], yazilan)}")
        self.stdout.write(f"  katılım sıfatı (bilgi) {kodlar['katilim_sifati']}")
        self.stdout.write(f"  uydurma tür (atılan)   {oran(sebepler['supheli_tur'], yazilan)}")
        self.stdout.write(f"  şüpheli katılım        {kodlar['supheli_katilim']}  (3. aşama karar verecek)")
        self.stdout.write(f"  İngiliz yazımı düzelt. {kodlar['amerikan_yazimi']}")
        kok_sorgusu = sum(1 for t in taslaklar if t.get("kaynak") == "kok_sorgusu")
        self.stdout.write(f"  kök sorgusu taslağı    {kok_sorgusu}")
        self.stdout.write(f"  kök düzeltilen taslak  {oran(kok_duzeltilen, len(gecerli))}")
        self.stdout.write(f"  kök listede yok        {oran(kodlar['kok_listede_yok'], len(gecerli))}")
        self.stdout.write(f"  sorulan ailede yok     {oran(kodlar['tohum_ailede_yok'], len(gecerli))}")

        if aileler:
            coklu = [a["ortusme"]["ortalama"] for a in aileler if a.get("ortusme")]
            incelenecek = sum(1 for a in aileler if a["durum"] == "incelenecek")
            self.stdout.write(f"  birleşik aile          {len(aileler)}  "
                              f"(incelenecek: {incelenecek})")
            if coklu:
                self.stdout.write(f"  ortalama örtüşme       {sum(coklu) / len(coklu):.2f}  "
                                  f"(en düşük: {min(coklu):.2f}, {len(coklu)} çok taslaklı aile)")

        girdi = sum(t.get("token", {}).get("girdi", 0) for t in taslaklar)
        cikti = sum(t.get("token", {}).get("cikti", 0) for t in taslaklar)
        istek = sum(1 for t in taslaklar if t.get("token"))
        if istek:
            fiyat_g = float(getattr(settings, "LLM_PRICE_INPUT", 0) or 0)
            fiyat_c = float(getattr(settings, "LLM_PRICE_OUTPUT", 0) or 0)
            maliyet = girdi / 1e6 * fiyat_g + cikti / 1e6 * fiyat_c
            self.stdout.write(f"  token                  {girdi:,} girdi + {cikti:,} çıktı · "
                              f"${maliyet:.4f} · kelime başı ${maliyet / istek:.5f}")
            self.stdout.write(f"  10.000 kelime          ≈ ${maliyet / istek * 10000:.2f}")
