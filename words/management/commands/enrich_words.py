# -*- coding: utf-8 -*-
"""
Kelime listesini ucuz bir modelle zenginleştirip veritabanına yazar.

    python manage.py enrich_words --words courage,decision,notorious
    python manage.py enrich_words --file listeler/hafta1.txt --dry-run
    python manage.py enrich_words --file buyuk.txt --workers 8 --report rapor.json

Dosya biçimi: her satırda bir kelime. Türünü belirtmek istersen iki nokta
üst üste ile: `progress:noun`. Boş satırlar ve `#` ile başlayanlar atlanır.

Akış her kelime için aynı ve tek yönlü:

    DB'ye bak  ->  modele sor  ->  denetle  ->  yaz

Model veritabanını hiç görmez; ne bildiğimizi ona metin olarak veriyoruz.
Denetimden geçmeyen hiçbir şey yazılmaz. --dry-run ile model çağrılır ama
veritabanına dokunulmaz — prompt ayarlarken kullanılacak kip budur.

PARALELLİK: kelimeler öbekler hâlinde işlenir. Öbek içinde YALNIZCA model
çağrıları paralel gider; veritabanı okuma ve yazma her zaman ana iş
parçacığında kalır. Django bağlantılarını iş parçacıklarına dağıtmamak hem
SQLite'ta kilitlenmeyi hem de yarı yazılmış kayıtları baştan imkânsız kılıyor.
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from LearnVocab import llm
from words.enrich import (checks, confusables, context, false_friends, prompt,
                          schema, writer)
from words.models import Word


class Command(BaseCommand):
    help = "Kelime listesini yapay zekâ ile zenginleştirip veritabanına ekler."

    def add_arguments(self, cozumleyici):
        cozumleyici.add_argument("--words", default="",
                                 help="Virgülle ayrılmış kelimeler.")
        cozumleyici.add_argument("--file", default="",
                                 help="Her satırda bir kelime olan dosya.")
        cozumleyici.add_argument("--limit", type=int, default=0,
                                 help="En fazla bu kadar kelime işle.")
        cozumleyici.add_argument("--model", default="",
                                 help="Ayardaki modeli geçersiz kıl.")
        cozumleyici.add_argument("--workers", type=int, default=0,
                                 help="Aynı anda kaç istek (varsayılan: LLM_WORKERS).")
        cozumleyici.add_argument("--dry-run", action="store_true",
                                 help="Modeli çağır ama veritabanına yazma.")
        cozumleyici.add_argument("--skip-existing", action="store_true",
                                 help="Anlamı zaten olan kelimeleri hiç sorma.")
        cozumleyici.add_argument("--report", default="",
                                 help="Ayrıntılı raporu bu JSON dosyasına yaz.")
        cozumleyici.add_argument("--verbose-json", action="store_true",
                                 help="Her kelimenin ham JSON çıktısını bas.")

    # ------------------------------------------------------------------

    def handle(self, *args, **secenekler):
        istekler = self._listeyi_oku(secenekler)
        if not istekler:
            raise CommandError("İşlenecek kelime yok. --words ya da --file ver.")
        if secenekler["limit"]:
            istekler = istekler[: secenekler["limit"]]

        self.kuru = secenekler["dry_run"]
        self.model_adi = secenekler["model"] or getattr(settings, "LLM_MODEL", "?")
        isci = secenekler["workers"] or int(getattr(settings, "LLM_WORKERS", 6))
        isci = max(1, min(isci, 32))

        alanlar = context.alan_listesi()
        toplam = llm.Usage()
        kayitlar = []
        sayac = dict(yazildi=0, atlandi=0, reddedildi=0, hata=0)
        # Üst üste kaç kalıcı hata alındı. Tek bir kelimenin patlaması
        # 10.000 kelimelik bir çalışmayı durdurmamalı; ama anahtar yanlışsa
        # 10.000 isteği boşuna göndermek de olmaz.
        ard_arda_hata = 0
        basladi = time.monotonic()

        self.stdout.write(
            f"{len(istekler)} kelime · model: {self.model_adi} · {isci} paralel istek"
            + ("  (DENEME — yazılmayacak)" if self.kuru else "")
        )
        # Aile kökü denetimi sistem sözlüğüne bağlı; yoksa "herit", "ambigu"
        # gibi uydurma kökler yakalanamaz. Sessizce zayıflamasın diye yazıyoruz.
        sozluk = checks._sozluk()
        self.stdout.write(
            f"Kök denetimi: {len(sozluk):,} kelimelik sistem sözlüğü kullanılıyor."
            if sozluk else
            self.style.WARNING("Kök denetimi: sistem sözlüğü bulunamadı "
                               "(/usr/share/dict/words) — uydurma aile kökleri "
                               "yakalanamayabilir.")
        )
        self.stdout.write("-" * 70)

        sira = 0
        obek_boyu = isci * 3

        for obek in self._obekle(istekler, obek_boyu):
            # --- 1. Hazırlık: veritabanı okuma, ana iş parçacığı ----------
            # Atlananların mesajları burada üretiliyor ama BASILMIYOR: model
            # çağrıları paralel gittiği için çıktı sırası bozulurdu.
            hazir, bekleyen = [], {}
            for metin, pos_ipucu in obek:
                sira += 1
                if checks.ifade_mi(metin, pos_ipucu):
                    bekleyen[sira] = self.style.WARNING(
                        f"[{sira}/{len(istekler)}] {metin}: deyim/bağlayıcı ifade, "
                        f"kelime hattına girmez — atlandı.")
                    kayitlar.append({"kelime": metin, "pos": pos_ipucu,
                                     "durum": "ifade"})
                    sayac["atlandi"] += 1
                    continue

                if secenekler["skip_existing"] and self._zaten_tam(metin, pos_ipucu):
                    bekleyen[sira] = f"[{sira}/{len(istekler)}] {metin}: zaten kayıtlı, atlandı."
                    sayac["atlandi"] += 1
                    continue
                ozet = context.kelime_ozeti(metin)
                metni = prompt.kullanici_metni(
                    metin, pos_ipucu, context.ozeti_metne_cevir(ozet), alanlar,
                )
                hazir.append((sira, metin, pos_ipucu, metni))

            if not hazir:
                continue

            # --- 2. Model çağrıları: paralel, veritabanına dokunmaz -------
            with ThreadPoolExecutor(max_workers=isci) as havuz:
                cevaplar = list(havuz.map(
                    lambda h: self._sor(h[3], secenekler["model"]), hazir
                ))

            # --- 3. Denetim ve yazma: ana iş parçacığı --------------------
            for (no, metin, pos_ipucu, _m), (sonuc, hata) in zip(hazir, cevaplar):
                for bekleyen_no in sorted(k for k in bekleyen if k < no):
                    self.stdout.write(bekleyen.pop(bekleyen_no))
                onek = f"[{no}/{len(istekler)}] {metin}"
                kayit = {"kelime": metin, "pos": pos_ipucu}

                if hata is not None:
                    self.stderr.write(self.style.ERROR(
                        f"{onek}: {type(hata).__name__} — {hata}"))
                    kayit.update(durum="hata", mesaj=str(hata))
                    kayitlar.append(kayit)
                    sayac["hata"] += 1
                    ard_arda_hata += 1

                    if isinstance(hata, llm.LLMUnconfigured) or ard_arda_hata >= 5:
                        self._sonucu_bas(sayac, toplam, basladi)
                        raise CommandError(
                            "Ayar hatası ya da üst üste 5 başarısız istek; "
                            "çalışma durduruldu."
                        ) from hata
                    continue

                ard_arda_hata = 0
                toplam += sonuc.usage
                if secenekler["verbose_json"]:
                    self.stdout.write(sonuc.raw)

                kelime = sonuc.data
                # Aile aramasını modelin önerdiği kökle tekrarla: ilk arama boş
                # dönmüş olabilir ama model "courage" demiş olabilir.
                ozet = context.kelime_ozeti(
                    metin, kelime.family_root if kelime.found else ""
                )
                rapor = checks.denetle(kelime, metin, ozet, alanlar)

                # Model bazen found=true deyip hiç anlam döndürmüyor. Bu
                # kelimenin kusuru değil, isteğin boşa gitmesi — reddetmeden
                # önce bir kez daha soruyoruz. Maliyeti bir istek, kazancı
                # kelimenin tamamı.
                if not rapor.kabul and any(s.kod == "anlam_yok" for s in rapor.hatalar):
                    yeniden, hata2 = self._sor(_m, secenekler["model"])
                    if yeniden is not None:
                        toplam += yeniden.usage
                        sonuc, kelime = yeniden, yeniden.data
                        ozet = context.kelime_ozeti(
                            metin, kelime.family_root if kelime.found else "")
                        rapor = checks.denetle(kelime, metin, ozet, alanlar)
                        rapor.ekle("uyari", "ikinci_deneme",
                                   "İlk cevapta hiç anlam yoktu; istek tekrarlandı.")

                # Yanlış dostlar modelden değil, küratörlü tablodan geliyor.
                # Denetimden SONRA ekleniyor: bu kayıtlar doğrulanmış veri,
                # denetime sokmanın anlamı yok.
                if rapor.kabul:
                    eklenen = false_friends.ekle(kelime)
                    if eklenen:
                        rapor.ekle("uyari", "yanlis_dost_eklendi",
                                   f"{eklenen} yanlış dost küratörlü tablodan eklendi.")
                    cift = confusables.ekle(kelime)
                    if cift:
                        rapor.ekle("uyari", "karistirilan_eklendi",
                                   f"{cift} karıştırılan çift küratörlü tablodan eklendi "
                                   f"(modelinki varsa elendi).")

                kayit["sorunlar"] = [str(s) for s in rapor.sorunlar]

                if not rapor.kabul:
                    # Reddedilen kelimenin ham cevabı rapora girsin ki sebebi
                    # tahmin etmek yerine bakarak anlayalım.
                    kayit["ham_cevap"] = sonuc.raw[:4000]
                    self.stdout.write(self.style.WARNING(f"{onek}: REDDEDİLDİ"))
                    for sorun in rapor.hatalar:
                        self.stdout.write(f"    {sorun}")
                    kayit["durum"] = "reddedildi"
                    sayac["reddedildi"] += 1
                elif not kelime.meanings:
                    self.stdout.write(f"{onek}: eklenecek yeni anlam yok.")
                    kayit["durum"] = "yeni_anlam_yok"
                    sayac["atlandi"] += 1
                elif self.kuru:
                    self._ozeti_bas(onek, kelime, rapor, yazildi=False)
                    kayit["durum"] = "deneme"
                    kayit["veri"] = kelime.model_dump()
                else:
                    writer.yaz(kelime, kaynak=f"AI: {self.model_adi}"[:120],
                               aile=ozet.get("aile"))
                    self._ozeti_bas(onek, kelime, rapor, yazildi=True)
                    kayit["durum"] = "yazildi"
                    sayac["yazildi"] += 1

                kayitlar.append(kayit)

            for bekleyen_no in sorted(bekleyen):
                self.stdout.write(bekleyen[bekleyen_no])

        self._sonucu_bas(sayac, toplam, basladi)

        if secenekler["report"]:
            Path(secenekler["report"]).write_text(
                json.dumps({"ozet": sayac, "kayitlar": kayitlar},
                           ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.stdout.write(f"Ayrıntılı rapor: {secenekler['report']}")

    # ------------------------------------------------------------------

    def _sor(self, kullanici_metni, model):
        """
        Tek bir model çağrısı. İŞ PARÇACIĞINDA çalışır — veritabanına
        dokunmaz, yalnızca ağ bekler. Hata fırlatmaz, döndürür; biri
        patladığında öbeğin geri kalanı sürsün diye.
        """
        try:
            return llm.chat_json(prompt.SISTEM, kullanici_metni,
                                 schema.Word, model=model or None), None
        except llm.LLMInvalidOutput:
            # Şema ihlali çoğunlukla tek seferlik. Sıcaklığı sıfırlayıp bir kez daha.
            try:
                return llm.chat_json(
                    prompt.SISTEM,
                    kullanici_metni + "\n\nUYARI: Bir önceki cevabın şemaya "
                                      "uymadı. Yalnızca şemaya uyan JSON döndür.",
                    schema.Word, model=model or None, temperature=0.0,
                ), None
            except llm.LLMError as hata:
                return None, hata
        except llm.LLMError as hata:
            return None, hata

    @staticmethod
    def _obekle(dizi, boyut):
        for i in range(0, len(dizi), boyut):
            yield dizi[i:i + boyut]

    def _zaten_tam(self, metin, pos_ipucu):
        sorgu = Word.objects.filter(text=metin.lower().strip())
        if pos_ipucu:
            sorgu = sorgu.filter(pos=pos_ipucu)
        return sorgu.filter(meanings__isnull=False).exists()

    def _listeyi_oku(self, secenekler):
        ham = []
        if secenekler["words"]:
            ham += secenekler["words"].split(",")
        if secenekler["file"]:
            yol = Path(secenekler["file"])
            if not yol.exists():
                raise CommandError(f"Dosya bulunamadı: {yol}")
            ham += yol.read_text(encoding="utf-8").splitlines()

        istekler, gorulen = [], set()
        for satir in ham:
            satir = satir.strip()
            if not satir or satir.startswith("#"):
                continue
            if ":" in satir:
                metin, _, pos = satir.partition(":")
                metin, pos = metin.strip().lower(), pos.strip().lower()
            else:
                metin, pos = satir.lower(), ""
            if not metin or (metin, pos) in gorulen:
                continue
            gorulen.add((metin, pos))
            istekler.append((metin, pos))
        return istekler

    # ------------------------------------------------------------------

    def _ozeti_bas(self, onek, kelime, rapor, yazildi):
        anlamlar = " | ".join(a.meaning_tr for a in kelime.meanings)
        cumle = sum(len(a.sentences) for a in kelime.meanings)
        coll = sum(len(a.collocations) for a in kelime.meanings)

        etiket = self.style.SUCCESS("✓") if yazildi else "·"
        self.stdout.write(
            f"{etiket} {onek} ({kelime.pos}, {kelime.cefr}, aile: {kelime.family_root})")
        self.stdout.write(f"    {anlamlar}")
        self.stdout.write(
            f"    {len(kelime.meanings)} anlam · {cumle} cümle · {coll} collocation"
            f" · {len(kelime.false_friends)} yanlış dost · {len(kelime.relations)} bağ")
        for sorun in rapor.uyarilar:
            self.stdout.write(self.style.WARNING(f"    {sorun}"))

    def _sonucu_bas(self, sayac, tuketim, basladi):
        gecen = time.monotonic() - basladi
        self.stdout.write("-" * 70)
        satir = (f"{sayac['yazildi']} yazıldı · {sayac['atlandi']} atlandı · "
                 f"{sayac['reddedildi']} reddedildi · {sayac['hata']} hata")
        if self.kuru:
            satir += "   (DENEME: hiçbir şey yazılmadı)"
        self.stdout.write(self.style.SUCCESS(satir))
        self.stdout.write(f"Tüketim: {tuketim}")

        if tuketim.requests:
            sure = gecen / tuketim.requests
            self.stdout.write(
                f"Kelime başına: {tuketim.total_tokens // tuketim.requests:,} token · "
                f"${tuketim.cost_usd / tuketim.requests:.5f} · {sure:.1f} sn")
            self.stdout.write(
                f"Bu hızla 10.000 kelime: {gecen / tuketim.requests * 10000 / 3600:.1f} saat · "
                f"${tuketim.cost_usd / tuketim.requests * 10000:.2f}")
        self.stdout.write(f"Toplam süre: {gecen:.1f} sn")
