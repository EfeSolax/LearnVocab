# -*- coding: utf-8 -*-
"""
1. AŞAMA — listedeki her kelimenin ailesini modele çıkartır, ara depoya yazar.

    python manage.py aile_uret --words decisively,analysis,depend
    python manage.py aile_uret --file listeler/aile-deneme.txt
    python manage.py aile_uret --file listeler/okuma-metinleri.txt --limit 200
    python manage.py aile_uret --file X.txt --dry-run      # depoya yazma

Model YALNIZCA kelimeyi ve türünü yazar. Geri kalan her şey kodun işi:
olmayan kelimeleri atmak (wordfreq), çekimi kelime diye yazılmış üyeleri
ayıklamak, kökü düzeltmek ve çekimleri üretmek (words/aile/denetim.py).

VERİTABANINA YAZMAZ. Çıktı ara-depo/taslaklar.jsonl dosyasına eklenir;
sonraki adım `manage.py aile_birlestir`.

KALDIĞI YERDEN DEVAM EDER: depoda cevabı olan kelime tekrar sorulmaz.
Komut yarıda kesilirse aynı komutu tekrar çalıştırmak yeter. Prompt
değiştikten sonra baştan sormak için --yeniden.

Aynı aileden birden çok kelime listede varsa (analysis, analyst, analyse)
HEPSİ ayrı ayrı sorulur — bilerek. Birleştirme aşaması bu cevapları
karşılaştırıp modelin tutarlı olup olmadığını ölçüyor; her kelime yaklaşık
0.03 sent, ölçüm neredeyse bedava. Maliyet kısılmak istenirse
--uyeyse-atla: başka bir taslakta üye olarak geçen kelime sorulmaz.
"""

import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from LearnVocab import llm
from words import inflect
from words.aile import denetim
from words.aile.depo import Depo, liste_oku
from words.aile.schema import AileCevabi
from words.enrich import prompt
from words.enrich.checks import ifade_mi


class Command(BaseCommand):
    help = "1. aşama: kelime listesinden aile taslakları üretir (ara depoya)."

    def add_arguments(self, cozumleyici):
        cozumleyici.add_argument("--words", default="", help="Virgülle ayrılmış kelimeler.")
        cozumleyici.add_argument("--file", default="", help="Her satırda bir kelime.")
        cozumleyici.add_argument("--limit", type=int, default=0,
                                 help="Bu çalıştırmada en fazla bu kadar YENİ kelime sor.")
        cozumleyici.add_argument("--model", default="", help="Ayardaki modeli geçersiz kıl.")
        cozumleyici.add_argument("--workers", type=int, default=0,
                                 help="Aynı anda kaç istek (varsayılan: LLM_WORKERS).")
        cozumleyici.add_argument("--yeniden", action="store_true",
                                 help="Depoda cevabı olan kelimeleri de tekrar sor.")
        cozumleyici.add_argument("--uyeyse-atla", action="store_true",
                                 help="Başka bir taslakta üye olarak geçen kelimeyi sorma.")
        cozumleyici.add_argument("--dry-run", action="store_true",
                                 help="Modeli çağır, sonucu göster ama depoya yazma.")
        cozumleyici.add_argument("--depo", default="",
                                 help="Ara depo klasörü (varsayılan: ara-depo/).")
        cozumleyici.add_argument("--ham", action="store_true",
                                 help="Her kelimenin ham JSON cevabını da bas.")
        cozumleyici.add_argument("--yeniden-denetle", action="store_true",
                                 help="Model ÇAĞIRMADAN depodaki ham cevapları güncel "
                                      "denetimden tekrar geçir (denetim değişince).")
        cozumleyici.add_argument("--kok-sorma", action="store_true",
                                 help="Aile köklerini ayrıca sorma (kök sorgusu kapalı).")

    # ------------------------------------------------------------------

    def handle(self, *args, **secenekler):
        self.kuru = secenekler["dry_run"]
        self.model_adi = secenekler["model"] or getattr(settings, "LLM_MODEL", "?")
        self.secenekler = secenekler
        depo = Depo(secenekler["depo"] or None)

        # --yeniden-denetle tek başına verilirse yalnızca depodaki cevaplar
        # denetlenir; ardından (yeni köklere) kök sorgusu yine çalışır.
        if secenekler["yeniden_denetle"]:
            self._yeniden_denetle(depo)
        yalniz_denetim = secenekler["yeniden_denetle"] and not (
            secenekler["words"] or secenekler["file"])
        istekler = [] if yalniz_denetim else self._istekler(secenekler, depo)

        isci = secenekler["workers"] or int(getattr(settings, "LLM_WORKERS", 6))
        self.isci = max(1, min(isci, 32))

        self.toplam = llm.Usage()
        self.sayac = Counter()
        self.kodlar = Counter()
        self.ard_arda_hata = 0
        self.basladi = time.monotonic()
        self._baslik_basildi = False

        uretilen = []
        if istekler:
            self._baslik(depo, f"{len(istekler)} kelime")
            uretilen = self._isle(istekler, depo, "liste")

        # KÖK SORGUSU. İlk gerçek çalıştırmada 29 ailenin 21'i tek bir
        # cevaba dayanıyordu: karşılaştıracak ikinci cevap yoktu. Her
        # ailenin KÖKÜ de (sorulmadıysa) bir kez sorulunca her aile en az
        # iki cevapla birleştirmeye giriyor. Kök, ailenin en doğal kapısı:
        # model oradan bakınca aileyi en eksiksiz kuruyor. Maliyet yaklaşık
        # %30 fazla istek. Depodaki BÜTÜN taslaklara bakılıyor, yani komut
        # yarıda kesilip yeniden çalıştırıldığında eksik kalan kökler de
        # tamamlanıyor.
        if not secenekler["kok_sorma"]:
            kokler = self._sorulacak_kokler(depo, uretilen)
            if kokler:
                self._baslik(depo, None)
                self.stdout.write(f"--- Kök sorgusu: {len(kokler)} kök kendisi sorulmamış, "
                                  f"soruluyor ---")
                self._isle([(k, "") for k in kokler], depo, "kok_sorgusu")

        if not self._baslik_basildi:
            self.stdout.write("Sorulacak yeni kelime yok (hepsi depoda). "
                              "Tekrar sormak için --yeniden.")
            return
        self._sonucu_bas(depo)

    def _yeniden_denetle(self, depo):
        """
        Denetim kodu değiştiğinde modeli yeniden çağırmak gereksiz: ham
        cevaplar depoda duruyor. Her birini güncel denetimden geçirip yeni
        satır olarak ekler (eskisi geçmişte kalır). Maliyeti sıfır.
        """
        from words.aile.schema import AileCevabi
        sayac, kodlar = Counter(), Counter()
        for eski in depo.guncel_taslaklar():
            if not eski.get("ham"):
                continue
            try:
                cevap = AileCevabi.model_validate_json(eski["ham"])
            except Exception:
                continue
            taslak = denetim.denetle(cevap, eski["tohum"], eski.get("tur_ipucu", ""))
            yeni = {k: v for k, v in eski.items() if k not in ("tarih",)}
            yeni.update(taslak)
            yeni["yeniden_denetlendi"] = True
            sayac[taslak["durum"]] += 1
            for s in taslak["sorunlar"]:
                kodlar[s["kod"]] += 1
            if not self.kuru:
                depo.taslak_ekle(yeni)
        self.stdout.write(f"Yeniden denetlendi (model çağrılmadı): "
                          + " · ".join(f"{v} {k}" for k, v in sayac.items()))
        for kod, adet in kodlar.most_common():
            self.stdout.write(f"  {adet:>4}  {kod}")

    def _baslik(self, depo, ne):
        if self._baslik_basildi:
            return
        self._baslik_basildi = True
        self.stdout.write(
            f"{ne or 'Yalnızca kök sorgusu'} · model: {self.model_adi} · "
            f"{self.isci} paralel istek"
            + ("  (DENEME — depoya yazılmayacak)" if self.kuru else f" · depo: {depo.yol}"))
        self._kaynaklari_bas()
        self.stdout.write("-" * 70)

    def _sorulacak_kokler(self, depo, uretilen):
        """Kendisi hiç sorulmamış aile kökleri (tamam durumdaki taslaklardan)."""
        taslaklar = (uretilen if self.kuru else []) + depo.guncel_taslaklar()
        sorulan = {denetim.normalize(t.get("tohum", "")) for t in taslaklar}
        sorulan |= {t.get("tohum", "") for t in taslaklar}
        kokler = []
        for t in taslaklar:
            kok = t.get("kok")
            if t.get("durum") == "tamam" and kok and kok not in sorulan:
                sorulan.add(kok)
                kokler.append(kok)
        return kokler

    def _isle(self, istekler, depo, kaynak):
        """İstekleri öbek öbek sorar, denetler, depoya yazar. Taslakları döndürür."""
        secenekler = self.secenekler
        uretilen = []
        sira = 0
        for obek in self._obekle(istekler, self.isci * 3):
            with ThreadPoolExecutor(max_workers=self.isci) as havuz:
                cevaplar = list(havuz.map(
                    lambda istek: self._sor(istek[0], istek[1], secenekler["model"]),
                    obek))

            # Denetim ve yazma ana iş parçacığında: dosyaya tek elden yazılır.
            for (tohum, ipucu), (sonuc, hata) in zip(obek, cevaplar):
                sira += 1
                onek = f"[{sira}/{len(istekler)}] {tohum}"
                kayit = {"tohum": tohum, "tur_ipucu": ipucu, "model": self.model_adi,
                         "kaynak": kaynak}

                if hata is not None:
                    self.stderr.write(self.style.ERROR(f"{onek}: {type(hata).__name__} — {hata}"))
                    self.sayac["hata"] += 1
                    self.ard_arda_hata += 1
                    kayit.update(durum="hata", mesaj=str(hata)[:500])
                    if not self.kuru:
                        depo.taslak_ekle(kayit)
                    if isinstance(hata, llm.LLMUnconfigured) or self.ard_arda_hata >= 5:
                        self._sonucu_bas(depo)
                        raise CommandError("Ayar hatası ya da üst üste 5 başarısız istek; "
                                           "çalışma durduruldu.") from hata
                    continue

                self.ard_arda_hata = 0
                self.toplam += sonuc.usage
                taslak = denetim.denetle(sonuc.data, tohum, ipucu)

                # Model anlamı koparan bir öneki soyup başka kelimenin
                # ailesini kurduysa (withdraw -> draw) bir kez, açık bir
                # uyarıyla tekrar sor. Bu hata kararlı değil: aynı model
                # uyarı görünce çoğunlukla düzeltiyor. Maliyeti tek istek.
                koparan = next((s for s in taslak["sorunlar"]
                                if s["kod"] == "koparan_onek" and s["seviye"] == "hata"), None)
                if koparan:
                    ek = (f"\n\nDİKKAT: '{tohum}' kelimesindeki ön ek anlamı KORUYAN bir ön "
                          f"ek DEĞİL. '{tohum}' başka bir kelimenin ailesine girmez, KENDİ "
                          f"ailesini kurar ve root_word '{tohum}' olmalıdır.")
                    yeniden, hata2 = self._sor(tohum, ipucu, secenekler["model"], ek)
                    if yeniden is not None:
                        self.toplam += yeniden.usage
                        sonuc = yeniden
                        taslak = denetim.denetle(sonuc.data, tohum, ipucu)
                        taslak["sorunlar"].insert(0, {
                            "seviye": "uyari", "kod": "ikinci_deneme",
                            "mesaj": f"İlk cevapta kök yanlış önekle bulunmuştu "
                                     f"({koparan['mesaj'][:80]}…); uyarıyla tekrar soruldu."})

                kayit.update(taslak)
                kayit["ham"] = sonuc.raw[:4000]
                kayit["token"] = {"girdi": sonuc.usage.prompt_tokens,
                                  "cikti": sonuc.usage.completion_tokens}
                self.sayac[taslak["durum"]] += 1
                for s in taslak["sorunlar"]:
                    self.kodlar[s["kod"]] += 1

                if secenekler["ham"]:
                    self.stdout.write(sonuc.raw)
                self._taslagi_bas(onek, taslak)
                if not self.kuru:
                    depo.taslak_ekle(kayit)
                uretilen.append(kayit)
        return uretilen

    # ------------------------------------------------------------------

    def _istekler(self, secenekler, depo):
        ham = []
        if secenekler["words"]:
            ham += secenekler["words"].split(",")
        if secenekler["file"]:
            yol = Path(secenekler["file"])
            if not yol.exists():
                raise CommandError(f"Dosya bulunamadı: {yol}")
            ham += yol.read_text(encoding="utf-8").splitlines()
        istekler = liste_oku(ham)
        if not istekler and not (secenekler["words"] or secenekler["file"]):
            raise CommandError("İşlenecek kelime yok. --words ya da --file ver.")

        atlanan = Counter()
        sorulmus = set() if secenekler["yeniden"] else depo.sorulmus_mu()
        uyeler = depo.uye_metinleri() if secenekler["uyeyse_atla"] else set()

        secilen = []
        for metin, ipucu in istekler:
            if ifade_mi(metin, ipucu):
                atlanan["deyim / bağlayıcı ifade (kelime hattına girmez)"] += 1
                continue
            if (metin, ipucu) in sorulmus:
                atlanan["depoda zaten var"] += 1
                continue
            if metin in uyeler:
                atlanan["başka bir taslakta üye (--uyeyse-atla)"] += 1
                continue
            secilen.append((metin, ipucu))

        for sebep, adet in atlanan.items():
            self.stdout.write(f"Atlandı: {adet} kelime — {sebep}")
        if secenekler["limit"]:
            secilen = secilen[: secenekler["limit"]]
        return secilen

    def _kaynaklari_bas(self):
        """Denetimin gücü kurulu paketlere bağlı; sessizce zayıflamasın."""
        kaynak = denetim.varlik_kaynagi()
        if kaynak == "wordfreq":
            self.stdout.write("Varlık denetimi: wordfreq (olmayan ve çok nadir kelimeler atılır).")
        elif kaynak == "sozluk":
            self.stdout.write(self.style.WARNING(
                "Varlık denetimi: YALNIZCA sistem sözlüğü — olmayan kelimeler ATILMAZ, "
                "sadece uyarılır. Kur:  pip install wordfreq"))
        else:
            self.stdout.write(self.style.WARNING(
                "Varlık denetimi YAPILAMIYOR. Kur:  pip install wordfreq"))
        if inflect.lemminflect_var_mi():
            self.stdout.write("Çekimler: lemminflect sözlüğü + kurallar.")
        else:
            self.stdout.write(self.style.WARNING(
                "Çekimler: yalnızca kurallar (çok heceli fiillerde yanılabilir). "
                "Kur:  pip install lemminflect"))

    def _sor(self, tohum, ipucu, model, ek=""):
        """Tek bir model çağrısı. İş parçacığında çalışır; hata döndürür, fırlatmaz."""
        metin = prompt.aile_kullanici_metni(tohum, ipucu) + ek
        try:
            return llm.chat_json(prompt.AILE_SISTEM, metin, AileCevabi,
                                 model=model or None), None
        except llm.LLMInvalidOutput:
            try:
                return llm.chat_json(
                    prompt.AILE_SISTEM,
                    metin + "\n\nUYARI: Bir önceki cevabın şemaya uymadı. "
                            "Yalnızca şemaya uyan JSON döndür.",
                    AileCevabi, model=model or None, temperature=0.0), None
            except llm.LLMError as hata:
                return None, hata
        except llm.LLMError as hata:
            return None, hata

    @staticmethod
    def _obekle(dizi, boyut):
        for i in range(0, len(dizi), boyut):
            yield dizi[i:i + boyut]

    # ------------------------------------------------------------------

    def _taslagi_bas(self, onek, taslak):
        if taslak["durum"] == "bulunamadi":
            self.stdout.write(self.style.WARNING(f"· {onek}: model kelimeyi tanımadı."))
            return
        uyeler = ", ".join(f"{u['word']} ({u['type'][:4]})" for u in taslak["uyeler"])
        if taslak["durum"] == "kusurlu":
            self.stdout.write(self.style.ERROR(f"X {onek}: KUSURLU → {taslak['kok'] or '?'}"))
        else:
            self.stdout.write(f"{self.style.SUCCESS('✓')} {onek} → {taslak['kok']}")
        self.stdout.write(f"    {uyeler}")
        for sorun in taslak["sorunlar"]:
            if sorun.get("seviye") != "bilgi":
                self.stdout.write(self.style.WARNING(f"    {denetim.sorun_metni(sorun)}"))

    def _sonucu_bas(self, depo):
        sayac, kodlar, tuketim = self.sayac, self.kodlar, self.toplam
        gecen = time.monotonic() - self.basladi
        self.stdout.write("-" * 70)
        self.stdout.write(self.style.SUCCESS(
            f"{sayac['tamam']} tamam · {sayac['kusurlu']} kusurlu · "
            f"{sayac['bulunamadi']} bulunamadı · {sayac['hata']} hata"
            + ("   (DENEME: depoya yazılmadı)" if self.kuru else "")))
        if kodlar:
            self.stdout.write("Denetim bulguları (· = bilgi, ekrana basılmadı):")
            bilgi = {"katilim_sifati", "bagimsiz_cogul"}
            for kod, adet in kodlar.most_common():
                self.stdout.write(f"  {adet:>4}  {'· ' if kod in bilgi else ''}{kod}")
        self.stdout.write(f"Tüketim: {tuketim}")
        if tuketim.requests:
            self.stdout.write(
                f"Kelime başına: {tuketim.total_tokens // tuketim.requests:,} token · "
                f"${tuketim.cost_usd / tuketim.requests:.5f} · "
                f"{gecen / tuketim.requests:.1f} sn")
        self.stdout.write(f"Toplam süre: {gecen:.1f} sn")
        if not self.kuru and (sayac["tamam"] or sayac["kusurlu"]):
            self.stdout.write(f"Sonraki adım:  python manage.py aile_birlestir"
                              + (f" --depo {depo.yol}" if depo.yol.name != "ara-depo" else ""))
