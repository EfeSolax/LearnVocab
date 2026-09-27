# -*- coding: utf-8 -*-
"""
3. AŞAMA — birleşmiş ailelerin kelimelerine anlam doldurur ve VERİTABANINA yazar.

    python manage.py aile_doldur                          # ara-depo/
    python manage.py aile_doldur --depo ara-depo-deneme-3 --dry-run
    python manage.py aile_doldur --aile predict,simple    # yalnızca bu aileler
    python manage.py aile_doldur --limit 50               # ilk 50 aile

Okur:   <depo>/aileler.json (aile_birlestir çıktısı) — yalnızca TEMİZ aileler
Yazar:  veritabanı + <depo>/anlamlar.jsonl

Her kelime için bir istek (word_filling). Kullanıcı mesajında kelimenin
ailesi de var: anlamlar aile içinde tutarlı olsun (destroy "yıkmak" ise
destruction "yıkım"). 1. aşamada "şüpheli katılım" işaretlenen kelimeler
(polluted, weakened) için model açıkça uyarılıyor: fiilden ayrı anlamı
yoksa found=false döner ve kelime veritabanına GİRMEZ.

Her aile tek transaction'da yazılır. Anlamı zaten olan kelime sorulmaz;
aynı komutu tekrar çalıştırmak güvenli. --dry-run cevapları da depoya
yazılır, gerçek çalıştırma onları TEKRAR SORMAZ (para iki kez ödenmez);
yeniden sormak için --yeniden-sor.

Sonda: depodaki bütün bağlar (eş/zıt anlamlı, daha basit) yeniden denenir
ve küratörlü yanlış dost / karıştırılan çift tabloları uygulanır.
"""

import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from LearnVocab import llm
from words.aile import anlam as A
from words.aile import kontrol as K
from words.aile import turkce
from words.aile.depo import Depo
from words.enrich import prompt
from words.models import Word


def _sirala(aileler, liste_yolu):
    """Aileleri, tohumlarından listede EN ÖNCE geçeninin sırasına göre dizer."""
    from pathlib import Path
    sira = {}
    for satir in Path(liste_yolu).read_text(encoding="utf-8").splitlines():
        satir = satir.strip()
        if satir and not satir.startswith("#"):
            sira.setdefault(satir.split(":")[0].lower(), len(sira))
    son = len(sira) + 1

    def anahtar(a):
        adaylar = [sira.get(t.lower(), son) for t in a.get("tohumlar", [])]
        adaylar.append(sira.get(a["kok"].lower(), son))
        return min(adaylar)
    return sorted(aileler, key=anahtar)


class Command(BaseCommand):
    help = "3. aşama: birleşmiş ailelere anlam doldurur ve veritabanına yazar."

    def add_arguments(self, c):
        c.add_argument("--depo", default="", help="Ara depo klasörü (varsayılan: ara-depo/).")
        c.add_argument("--aile", default="", help="Virgülle ayrılmış kökler; yalnızca bunlar.")
        c.add_argument("--limit", type=int, default=0,
                       help="En fazla bu kadar aile (tamamı veritabanında olan aileler sayılmaz).")
        c.add_argument("--reddedilenler", action="store_true",
                       help="Yalnızca daha önce REDDEDİLEN kelimesi olan aileler: depodaki "
                            "cevaplar güncel kurallarla yeniden denetlenir (üretici tekrar "
                            "sorulmaz; kabul edilene yalnızca kontrol ücreti).")
        c.add_argument("--sira", default="",
                       help="Tohum listesi (ör. listeler/tum-tohumlar.txt): aileler bu listedeki "
                            "sıraya göre işlenir — bütçe önce en sık kelimelere gider.")
        c.add_argument("--incelenecek-dahil", action="store_true",
                       help="'incelenecek' durumundaki aileleri de doldur (önerilmez).")
        c.add_argument("--model", default="", help="Ayardaki modeli geçersiz kıl.")
        c.add_argument("--workers", type=int, default=0, help="Aynı anda kaç istek.")
        c.add_argument("--dry-run", action="store_true",
                       help="Modeli çağır, denetle, depoya yaz; VERİTABANINA yazma.")
        c.add_argument("--yeniden-sor", action="store_true",
                       help="Depoda cevabı olan kelimeleri de modele tekrar sor.")
        c.add_argument("--kontrol-yok", action="store_true",
                       help="Kontrol modelini çalıştırma (LLM_KONTROL_MODEL ayarlı olsa bile).")
        c.add_argument("--yeniden-kontrol", action="store_true",
                       help="Daha önce kontrol edilmiş cevapları da kontrolcüye tekrar sor.")
        # Model kıyaslaması için: .env'yi değiştirmeden kontrolcüyü seçmek.
        c.add_argument("--kontrol-model", default="",
                       help="Kontrol modeli (LLM_KONTROL_MODEL yerine).")
        c.add_argument("--kontrol-fiyat", default="",
                       help="Kontrol modelinin 1M token fiyatı, 'girdi,çıktı': 0.75,3.75")
        c.add_argument("--kontrol-dusunme", default="",
                       help="Kontrol modelinin düşünme derinliği: low / medium / high.")
        c.add_argument("--hepsi", action="store_true",
                       help="Yalnızca --dry-run ile: veritabanında anlamı olan kelimeleri de "
                            "işle (kıyaslama/ölçüm için).")

    # ------------------------------------------------------------------

    def handle(self, *args, **s):
        # --kontrol-* seçenekleri ayarları bu çalıştırma için değiştiriyor;
        # süreç içinde kalıcı olmasın (testler aynı süreçte koşuyor).
        adlar = ("LLM_KONTROL_MODEL", "LLM_KONTROL_PRICE_INPUT",
                 "LLM_KONTROL_PRICE_OUTPUT", "LLM_KONTROL_REASONING_EFFORT")
        eski = {ad: getattr(settings, ad, None) for ad in adlar}
        try:
            self._handle(s)
        finally:
            for ad, deger in eski.items():
                setattr(settings, ad, deger)

    def _handle(self, s):
        self.s = s
        self.kuru = s["dry_run"]
        if s["hepsi"] and not self.kuru:
            raise CommandError("--hepsi yalnızca --dry-run ile kullanılabilir.")
        if s["kontrol_model"]:
            settings.LLM_KONTROL_MODEL = s["kontrol_model"]
        if s["kontrol_fiyat"]:
            try:
                girdi, cikti = (float(x) for x in s["kontrol_fiyat"].split(","))
            except ValueError as hata:
                raise CommandError("--kontrol-fiyat biçimi: girdi,çıktı (ör. 0.75,3.75)") from hata
            settings.LLM_KONTROL_PRICE_INPUT, settings.LLM_KONTROL_PRICE_OUTPUT = girdi, cikti
        if s["kontrol_dusunme"]:
            settings.LLM_KONTROL_REASONING_EFFORT = s["kontrol_dusunme"]
        self.kontrol_ard_hata = 0
        self.model_adi = s["model"] or getattr(settings, "LLM_MODEL", "?")
        depo = Depo(s["depo"] or None)
        aileler = depo.aileler()
        if not aileler:
            raise CommandError(f"{depo.yol}/aileler.json yok. Önce: manage.py aile_birlestir")

        secilen = [a for a in aileler
                   if a["durum"] == "temiz" or s["incelenecek_dahil"]]
        atlanan_incelenecek = len(aileler) - len(secilen)
        if s["aile"]:
            istenen = {k.strip().lower() for k in s["aile"].split(",") if k.strip()}
            secilen = [a for a in secilen if a["kok"] in istenen]
        if s["sira"]:
            secilen = _sirala(secilen, s["sira"])
        if s["reddedilenler"] or s["limit"]:
            dbde = set(Word.objects.values_list("text", "pos"))
            kayitlar = depo.anlamlar()
        if s["reddedilenler"]:
            secilen = [a for a in secilen if any(
                (u["word"], u["type"]) not in dbde
                and (kayitlar.get((u["word"], u["type"])) or {}).get("durum") == "reddedildi"
                for u in a["uyeler"])]
        elif s["limit"]:
            # Limit BEKLEYEN işi sayar: veritabanında olmayan ve REDDEDİLMEMİŞ
            # kelimesi olan aileler. Kuru denemeden sonraki gerçek yazım aynı
            # aileleri seçer; yalnızca reddedilmiş kelimesi kalan eski aileler
            # her partide baştan seçilip limiti yemez (onlar: --reddedilenler).
            secilen = [a for a in secilen if any(
                (u["word"], u["type"]) not in dbde
                and (kayitlar.get((u["word"], u["type"])) or {}).get("durum") != "reddedildi"
                for u in a["uyeler"])]
        if s["limit"]:
            secilen = secilen[: s["limit"]]

        isci = max(1, min(s["workers"] or int(getattr(settings, "LLM_WORKERS", 6)), 32))
        onbellek = depo.anlamlar()

        self.stdout.write(
            f"{len(secilen)} aile · model: {self.model_adi} · {isci} paralel istek"
            + ("  (DENEME — veritabanına yazılmayacak)" if self.kuru else ""))
        if atlanan_incelenecek:
            self.stdout.write(self.style.WARNING(
                f"{atlanan_incelenecek} 'incelenecek' aile atlandı (kararlar.json'la çöz "
                f"ya da --incelenecek-dahil)."))
        self.stdout.write("-" * 70)

        self.toplam = llm.Usage()
        self.kontrol_tuketim = llm.Usage()
        self.kontrol_sayac = Counter()
        self.isci = isci
        self.kontrol = K.ayarli_mi() and not s["kontrol_yok"]
        hazir, aciklama = turkce.durum()
        self.stdout.write(f"Türkçe yazım denetimi: {aciklama}" if hazir else self.style.WARNING(
            f"Türkçe yazım denetimi YAPILAMIYOR: {aciklama}"))
        if self.kontrol:
            self.stdout.write(f"Kontrol modeli: {K.model_adi()} · düşünme: {K.dusunme()}")
        else:
            self.stdout.write(self.style.WARNING(
                "Kontrol modeli KAPALI (" + ("--kontrol-yok" if s["kontrol_yok"]
                                             else ".env › LLM_KONTROL_MODEL boş")
                + "): anlamlar yalnızca kodla denetleniyor."))
        self.sayac = Counter()
        self.kodlar = Counter()
        basladi = time.monotonic()
        ard_arda_hata = 0

        # --dry-run HIZLI YOL: grup (öbek) bariyeri yok. Her aile kendi
        # kelimelerini sorar, kaydeder ve denetler; `isci` kadar aile aynı anda
        # işlenir. Öbek yolunda her öbek en yavaş isteği bekliyordu ve 300
        # tohumluk ilk PDF partisi (1.124 kelime) ~2 saat sürecekti.
        # Veritabanına yazılmadığı için güvenli; gerçek yazım (önbellekten,
        # hızlı) aşağıdaki sıralı yoldan yapılır.
        if self.kuru and isci > 1:
            self._var_onbellegi = {(u["word"], u["type"]): self._anlami_var(u["word"], u["type"])
                                   for a in secilen for u in a["uyeler"]}
            with ThreadPoolExecutor(max_workers=isci) as havuz:
                list(havuz.map(lambda a: self._aile_tam(a, onbellek, depo, s), secilen))
            secilen = []          # aşağıdaki öbek döngüsü atlanır

        for obek in [secilen[i:i + isci] for i in range(0, len(secilen), isci)]:
            # Her ailenin sorulacak kelimeleri
            isler = []
            for aile in obek:
                uyeler = [(u["word"], u["type"]) for u in aile["uyeler"]]
                for uye in aile["uyeler"]:
                    anahtar = (uye["word"], uye["type"])
                    if self._anlami_var(*anahtar):
                        continue
                    if not s["yeniden_sor"] and anahtar in onbellek and onbellek[anahtar].get("ham"):
                        continue
                    isler.append((aile["kok"], uye, uyeler))

            # Her cevap GELDİĞİ ANDA depoya yazılıyor: süreç yarıda kesilirse
            # (Claude'un ortamında komut başına süre sınırı var) parası ödenmiş
            # cevaplar kaybolmasın, sonraki çalıştırma onları tekrar sormasın.
            with ThreadPoolExecutor(max_workers=isci) as havuz:
                gelecekler = {havuz.submit(self._sor, *is_): is_ for is_ in isler}
                cevaplar = []
                for gelecek in as_completed(gelecekler):
                    is_, sonuc_hata = gelecekler[gelecek], gelecek.result()
                    cevaplar.append((is_, sonuc_hata))
                    sonuc, _hata = sonuc_hata
                    if sonuc is not None:
                        kok_, uye_, _ = is_
                        depo.anlam_ekle({"word": uye_["word"], "type": uye_["type"],
                                         "aile": kok_, "ham": sonuc.raw, "model": self.model_adi,
                                         "token": {"girdi": sonuc.usage.prompt_tokens,
                                                   "cikti": sonuc.usage.completion_tokens}})

            for (kok, uye, _u), (sonuc, hata) in cevaplar:
                anahtar = (uye["word"], uye["type"])
                if hata is not None:
                    self.stderr.write(self.style.ERROR(
                        f"  {uye['word']} ({uye['type']}): {type(hata).__name__} — {hata}"))
                    self.sayac["hata"] += 1
                    ard_arda_hata += 1
                    if isinstance(hata, llm.LLMUnconfigured) or ard_arda_hata >= 5:
                        self._ozet(depo, basladi)
                        raise CommandError("Ayar hatası ya da üst üste 5 başarısız istek.") from hata
                    continue
                ard_arda_hata = 0
                self.toplam += sonuc.usage
                onbellek[anahtar] = {"word": uye["word"], "type": uye["type"], "aile": kok,
                                     "ham": sonuc.raw, "model": self.model_adi,
                                     "token": {"girdi": sonuc.usage.prompt_tokens,
                                               "cikti": sonuc.usage.completion_tokens}}

            # Aile aile denetle ve yaz. --dry-run'da veritabanına yazılmadığı
            # için aileler PARALEL işleniyor: ikinci deneme, kontrolcü ve yeniden
            # üretim aile başına sırayla bekleniyordu ve 1.124 kelimelik ilk PDF
            # partisi ~2 saat sürecekti. (İstatistik sayaçları iş parçacıkları
            # arasında paylaşılıyor; nadiren bir iki eksik sayabilir. Gerçek
            # fatura OpenRouter'da.) Gerçek yazımda sıra korunuyor.
            if self.kuru and isci > 1:
                # Veritabanı okuması iş parçacıklarına girmesin (SQLite kilidi):
                # "anlamı var mı" cevapları burada, ana iş parçacığında alınıyor.
                self._var_onbellegi = {(u["word"], u["type"]): self._anlami_var(u["word"], u["type"])
                                       for a in obek for u in a["uyeler"]}
                with ThreadPoolExecutor(max_workers=isci) as havuz:
                    list(havuz.map(lambda a: self._aileyi_isle(a, onbellek, depo), obek))
                self._var_onbellegi = {}
            else:
                for aile in obek:
                    self._aileyi_isle(aile, onbellek, depo)

        # Bağlar ve küratörlü tablolar
        if not self.kuru:
            baglar = A.bag_tamamla(list(depo.anlamlar().values()))
            self.sayac["bag"] = baglar["kurulan"]
            self.sayac["bekleyen_bag"] = baglar["bekleyen"]
            for komut in ("seed_false_friends", "seed_confusables"):
                try:
                    call_command(komut, stdout=StringIO())
                except Exception as hata:   # tablo komutu hatası dolumu bozmasın
                    self.stderr.write(f"{komut}: {hata}")
        self._ozet(depo, basladi)

    # ------------------------------------------------------------------

    def _anlami_var(self, metin, tur):
        if self.s.get("hepsi"):
            return False
        return Word.objects.filter(text=metin, pos=tur, meanings__isnull=False).exists()

    def _sor(self, kok, uye, aile_uyeleri, ek=""):
        """Tek model çağrısı (iş parçacığında). Hata döndürür, fırlatmaz."""
        metin = prompt.kelime_kullanici_metni(
            uye["word"], uye["type"], aile_uyeleri, uye.get("supheli_katilim", False)) + ek
        try:
            return llm.chat_json(prompt.KELIME_SISTEM, metin, A.KelimeCevabi,
                                 model=self.s["model"] or None), None
        except llm.LLMInvalidOutput:
            try:
                return llm.chat_json(
                    prompt.KELIME_SISTEM,
                    metin + "\n\nUYARI: Bir önceki cevabın şemaya uymadı. "
                            "Yalnızca şemaya uyan JSON döndür.",
                    A.KelimeCevabi, model=self.s["model"] or None, temperature=0.0), None
            except llm.LLMError as hata:
                return None, hata
        except llm.LLMError as hata:
            return None, hata

    def _aile_tam(self, aile, onbellek, depo, s):
        """Hızlı yol: bir ailenin eksik kelimelerini sor, anında kaydet, denetle."""
        uyeler = [(u["word"], u["type"]) for u in aile["uyeler"]]
        for uye in aile["uyeler"]:
            anahtar = (uye["word"], uye["type"])
            if self._var_onbellegi.get(anahtar):
                continue
            if not s["yeniden_sor"] and anahtar in onbellek and onbellek[anahtar].get("ham"):
                continue
            sonuc, hata = self._sor(aile["kok"], uye, uyeler)
            if hata is not None:
                if isinstance(hata, llm.LLMUnconfigured):
                    raise CommandError(f"Ayar hatası: {hata}") from hata
                self.stderr.write(self.style.ERROR(
                    f"  {uye['word']} ({uye['type']}): {type(hata).__name__} — {hata}"))
                self.sayac["hata"] += 1
                continue
            self.toplam += sonuc.usage
            kayit = {"word": uye["word"], "type": uye["type"], "aile": aile["kok"],
                     "ham": sonuc.raw, "model": self.model_adi,
                     "token": {"girdi": sonuc.usage.prompt_tokens,
                               "cikti": sonuc.usage.completion_tokens}}
            onbellek[anahtar] = kayit
            depo.anlam_ekle(kayit)
        self._aileyi_isle(aile, onbellek, depo)

    def _aileyi_isle(self, aile, onbellek, depo):
        yazilacak, satirlar, girdiler = [], [], []
        for uye in aile["uyeler"]:
            anahtar = (uye["word"], uye["type"])
            etiket = f"{uye['word']} ({uye['type']})"
            var_mi = getattr(self, "_var_onbellegi", {})
            if (var_mi[anahtar] if anahtar in var_mi else self._anlami_var(*anahtar)):
                self.sayac["zaten_var"] += 1
                continue
            kayit = onbellek.get(anahtar)
            if not kayit or not kayit.get("ham"):
                continue
            try:
                cevap = A.KelimeCevabi.model_validate_json(kayit["ham"])
            except Exception as hata:
                satirlar.append(self.style.ERROR(f"  X {etiket}: bozuk cevap — {hata}"))
                self.sayac["bozuk"] += 1
                continue
            supheli = uye.get("supheli_katilim", False)
            rapor = A.denetle(cevap, uye["word"], uye["type"], uye.get("cekim"), supheli)

            # Türkçe ya da anlam sorunu varsa sorunların METNİYLE bir kez
            # daha sor (2. denemede "fortunately = ne yazık ki" uyarıyla
            # yazılmıştı). İki cevaptan iyisi kalır. Kayıt işaretlenir ki
            # sonraki çalıştırmalar aynı kelimeyi tekrar tekrar sormasın.
            sorunlar = A.yeniden_sorulmali(rapor)
            if sorunlar and not kayit.get("ikinci_deneme"):
                kayit["ikinci_deneme"] = True
                ek = ("\n\nDİKKAT: Bu kelime için önceki cevabında şu sorunlar vardı:\n"
                      + "\n".join(f"- {s.mesaj}" for s in sorunlar)
                      + "\nBu sorunları düzelterek cevabı BAŞTAN ver. Türkçe karşılık kısa, "
                        "doğru ve kelimenin türünde olsun.")
                yeni, hata = self._sor(aile["kok"], uye,
                                       [(u["word"], u["type"]) for u in aile["uyeler"]], ek)
                if yeni is not None:
                    self.toplam += yeni.usage
                    self.sayac["ikinci_deneme"] += 1
                    yeni_cevap = yeni.data
                    yeni_rapor = A.denetle(yeni_cevap, uye["word"], uye["type"],
                                           uye.get("cekim"), supheli)
                    if A.puan(yeni_rapor, yeni_cevap) > A.puan(rapor, cevap):
                        cevap, rapor = yeni_cevap, yeni_rapor
                        kayit["ham"] = yeni.raw
                        self.sayac["ikinci_deneme_iyi"] += 1
                    rapor.ekle("uyari", "ikinci_deneme",
                               f"Sorunlar yüzünden tekrar soruldu: "
                               f"{', '.join(sorted({s.kod for s in sorunlar}))}.")

            girdiler.append({"uye": uye, "kayit": kayit, "cevap": cevap, "rapor": rapor,
                             "etiket": etiket, "supheli": supheli})

        # --- Kontrol modeli -------------------------------------------------
        if self.kontrol:
            self._kontrol_et(aile, [g for g in girdiler if g["rapor"].kabul])

        # --- Sonuç ------------------------------------------------------------
        for g in girdiler:
            kayit, cevap, rapor, etiket, uye = (g["kayit"], g["cevap"], g["rapor"],
                                                g["etiket"], g["uye"])
            for sorun in rapor.sorunlar:
                self.kodlar[sorun.kod] += 1
            kayit.update(aile=aile["kok"], sorunlar=[str(x) for x in rapor.sorunlar],
                         cevap=cevap.model_dump() if rapor.kabul else None)

            if not rapor.kabul:
                neden = "; ".join(str(x) for x in rapor.hatalar)
                satirlar.append(self.style.WARNING(f"  · {etiket}: YAZILMADI — {neden}"))
                kayit["durum"] = "reddedildi"
                self.sayac["reddedildi"] += 1
            else:
                kayit["durum"] = "deneme" if self.kuru else "yazildi"
                yazilacak.append({"cevap": cevap, "cekim": uye.get("cekim"),
                                  "diger_yazimlar": uye.get("diger_yazimlar")})
                anlamlar = " | ".join(f"{a.meaning_tr} ({a.cefr})" for a in cevap.meanings)
                satirlar.append(f"  ✓ {etiket}: {anlamlar}")
                for sorun in rapor.uyarilar:
                    satirlar.append(self.style.WARNING(f"      {sorun}"))
            depo.anlam_ekle(kayit)

        if not yazilacak and not satirlar:
            return
        if yazilacak and not self.kuru:
            sonuc = A.aileyi_yaz(aile["kok"], yazilacak, f"AI: {self.model_adi}")
            for k, v in sonuc.items():
                self.sayac[k] += v
            self.sayac["aile"] += 1
        elif yazilacak:
            self.sayac["kelime"] += len(yazilacak)
            self.sayac["anlam"] += sum(len(o["cevap"].meanings) for o in yazilacak)
        self.stdout.write(f"■ {aile['kok']}")
        for satir in satirlar:
            self.stdout.write(satir)

    def _kontrol_et(self, aile, girdiler):
        """
        Kod denetiminden geçen kelimeleri kontrol modeline sorar ve kararı
        uygular. Aynı üretim cevabı daha önce kontrol edildiyse (depoda)
        kontrolcü tekrar çağrılmaz. Kontrol edilemeyen kelime YAZILMAZ:
        denetlenmemiş veri veritabanına girmesin; sonraki çalıştırmada
        yeniden denenir.
        """
        aile_uyeleri = [(u["word"], u["type"]) for u in aile["uyeler"]]
        # Önbellek yalnızca AYNI cevabı AYNI model kontrol ettiyse geçerli:
        # model kıyaslarken bir modelin kararı ötekinin yerine geçmesin.
        bekleyen = [g for g in girdiler if self.s["yeniden_kontrol"]
                    or g["kayit"].get("kontrol_icin") != g["kayit"].get("ham")
                    or g["kayit"].get("kontrol_model") != K.kimlik()
                    or not g["kayit"].get("kontrol_ham")]
        with ThreadPoolExecutor(max_workers=self.isci) as havuz:
            sonuclar = list(havuz.map(
                lambda g: K.sor(g["uye"]["word"], g["uye"]["type"], aile_uyeleri,
                                g["cevap"].meanings), bekleyen))
        yeni = {id(g): s for g, s in zip(bekleyen, sonuclar)}

        for g in girdiler:
            kayit, uye = g["kayit"], g["uye"]
            if id(g) in yeni:
                sonuc, hata = yeni[id(g)]
                if hata is not None:
                    g["rapor"].ekle("hata", "kontrol_edilemedi",
                                    f"Kontrol modeli cevap vermedi: {type(hata).__name__} — "
                                    f"{str(hata)[:120]}")
                    self.kontrol_sayac["hata"] += 1
                    self.kontrol_ard_hata += 1
                    # Bakiye bitti (402), anahtar yanlış, model adı yanlış: bütün
                    # listeyi boşuna denemeden dur.
                    if isinstance(hata, llm.LLMFatal) or self.kontrol_ard_hata >= 5:
                        raise CommandError(
                            f"Kontrol modeli üst üste {self.kontrol_ard_hata} kez hata verdi "
                            f"(son: {str(hata)[:200]}). Bakiye, model adı ve anahtarı kontrol et. "
                            f"O ana kadarki cevaplar depoda; aynı komut kaldığı yerden sürer.")
                    continue
                self.kontrol_ard_hata = 0
                self.kontrol_tuketim += sonuc.usage
                karar, ham = sonuc.data, sonuc.raw
                kayit["kontrol_token"] = {"girdi": sonuc.usage.prompt_tokens,
                                          "cikti": sonuc.usage.completion_tokens}
            else:
                karar = K.KontrolCevabi.model_validate_json(kayit["kontrol_ham"])
                ham = kayit["kontrol_ham"]
                self.kontrol_sayac["onbellek"] += 1
            kayit["kontrol_icin"], kayit["kontrol_ham"] = kayit["ham"], ham
            kayit["kontrol_model"] = K.kimlik()
            # İlk kontrol ayrıca saklanıyor: yeniden üretim olursa kontrol_ham
            # değişiyor ama model kıyası (kontrol_kiyasla) İLK kararlara bakar,
            # çünkü iki model yalnızca orada birebir aynı girdiyi gördü.
            if kayit.get("ilk_kontrol_icin") != kayit["ham"] or id(g) in yeni:
                kayit["ilk_kontrol_icin"] = kayit["ham"]
                kayit["ilk_kontrol_ham"] = ham
                kayit["ilk_kontrol_anlamlar"] = [
                    {"meaning_tr": a.meaning_tr, "cefr": a.cefr, "definition": a.definition,
                     "sentences": a.sentences,
                     "collocations": [e.pattern for e in a.collocations]}
                    for a in g["cevap"].meanings]

            istatistik = K.uygula(g["cevap"], karar, uye["type"], g["rapor"])
            self._kontrol_say(istatistik)

            # Hiç anlam kalmadıysa (ve kelime geçerliyse) gerekçelerle bir kez
            # daha üret ve yeniden kontrol et.
            if (not g["cevap"].meanings
                    and (karar.word_valid or istatistik["sozlukte_var"])
                    and not kayit.get("kontrol_yeniden")):
                kayit["kontrol_yeniden"] = True
                self._yeniden_uret(aile, g, aile_uyeleri,
                                   K.yeniden_uretim_notu(istatistik["gerekceler"]),
                                   "Kontrolcü bütün anlamları sildi; gerekçeleriyle yeniden üretildi.")
            # Temel anlam eksikse bir kez, eksik anlamı söyleyerek yeniden üret.
            # Yeni cevap da kontrol edilir; yine eksikse yalnızca raporlanır.
            elif ((istatistik["eksik"] or istatistik["cumlesiz"])
                    and (karar.word_valid or istatistik["sozlukte_var"])
                    and not kayit.get("eksik_yeniden")):
                kayit["eksik_yeniden"] = True
                self.kontrol_sayac["eksik_yeniden"] += 1
                neden = []
                if istatistik["eksik"]:
                    neden.append(f"temel anlam eksikti ('{istatistik['eksik']}')")
                if istatistik["cumlesiz"]:
                    neden.append("cümleleri hatalı anlam: "
                                 + ", ".join(f"'{a}'" for a in istatistik["cumlesiz"]))
                self._yeniden_uret(aile, g, aile_uyeleri,
                                   K.eksik_anlam_notu(istatistik["eksik"],
                                                      istatistik["cumlesiz"]),
                                   "; ".join(neden).capitalize() + "; yeniden üretildi.")

    def _yeniden_uret(self, aile, g, aile_uyeleri, not_metni, mesaj):
        uye, kayit = g["uye"], g["kayit"]
        uretim, hata = self._sor(aile["kok"], uye, aile_uyeleri, not_metni)
        if uretim is None:
            return
        self.toplam += uretim.usage
        self.kontrol_sayac["yeniden_uretim"] += 1
        cevap = uretim.data
        rapor = A.denetle(cevap, uye["word"], uye["type"], uye.get("cekim"), g["supheli"])
        if rapor.kabul:
            sonuc, hata = K.sor(uye["word"], uye["type"], aile_uyeleri, cevap.meanings)
            if sonuc is None:
                rapor.ekle("hata", "kontrol_edilemedi", f"Kontrol modeli cevap vermedi: {hata}")
            else:
                self.kontrol_tuketim += sonuc.usage
                kayit["kontrol_ham"] = sonuc.raw
                self._kontrol_say(K.uygula(cevap, sonuc.data, uye["type"], rapor))
        rapor.ekle("uyari", "kontrol_yeniden_uretim", mesaj)
        kayit["ham"] = uretim.raw
        kayit["kontrol_icin"] = uretim.raw
        g["cevap"], g["rapor"] = cevap, rapor

    def _kontrol_say(self, istatistik):
        for anahtar, deger in istatistik.items():
            if anahtar not in ("gerekceler", "eksik", "cumlesiz", "sozlukte_var"):
                self.kontrol_sayac[anahtar] += deger
        self.kontrol_sayac["kelime"] += 1

    def _ozet(self, depo, basladi):
        s, t = self.sayac, self.toplam
        gecen = time.monotonic() - basladi
        self.stdout.write("-" * 70)
        self.stdout.write(self.style.SUCCESS(
            f"{s['kelime']} kelime {'hazır (DENEME)' if self.kuru else 'yazıldı'} · "
            f"{s['reddedildi']} reddedildi · {s['hata']} hata · {s['zaten_var']} zaten vardı"))
        if s["ikinci_deneme"]:
            self.stdout.write(f"{s['ikinci_deneme']} kelime sorunları yüzünden tekrar soruldu, "
                              f"{s['ikinci_deneme_iyi']} tanesinde ikinci cevap daha iyiydi.")
        if not self.kuru:
            self.stdout.write(f"{s['aile']} aile · {s['anlam']} anlam · {s['cumle']} cümle · "
                              f"{s['collocation']} eş dizim · {s['kalip']} kalıp · "
                              f"{s['bicim']} çekim biçimi · {s['bag']} yeni bağ "
                              f"({s['bekleyen_bag']} bağın hedefi henüz yok)")
        if self.kodlar:
            self.stdout.write("Denetim bulguları:")
            for kod, adet in self.kodlar.most_common():
                self.stdout.write(f"  {adet:>4}  {kod}")
        if self.kontrol and self.kontrol_sayac["kelime"]:
            k = self.kontrol_sayac
            toplam_anlam = k["kontrol_anlam"]
            hatali = k["karsilik_duzeltildi"] + k["anlam_silindi"]
            oran = 100 * hatali / toplam_anlam if toplam_anlam else 0
            self.stdout.write(self.style.SUCCESS(
                f"Kontrol ({K.model_adi()}): {k['kelime']} kontrol · {toplam_anlam} anlamdan "
                f"{k['dogru']} doğru, {k['karsilik_duzeltildi']} karşılık düzeltildi, "
                f"{k['anlam_silindi']} anlam silindi"))
            self.stdout.write(self.style.SUCCESS(
                f"  ÜRETİCİ HATA ORANI (kontrolcüye göre): {hatali}/{toplam_anlam} = %{oran:.1f}"))
            self.stdout.write(
                f"  {k['cumle_silindi']} cümle · {k['esdizim_silindi']} eş dizim silindi · "
                f"{k['cefr_degisti']} seviye değişti · {k['yeniden_uretim']} yeniden üretim · "
                f"{k['hata']} kontrol hatası · {k['onbellek']} önbellekten")
            self.stdout.write(
                f"  Temel anlam eksik: {k['eksik_anlam']} kez · {k['eksik_yeniden']} kelime "
                f"eksik anlam yüzünden yeniden üretildi")
            if self.kontrol_tuketim.real_cost:
                kg = self.kontrol_tuketim
                self.stdout.write(self.style.WARNING(
                    f"  Kontrol GERÇEK fatura: ${kg.real_cost:.4f} · 10.000 kelime ≈ "
                    f"${kg.real_cost / max(kg.requests, 1) * 10000:.2f} · önbellek: "
                    f"{kg.cached_tokens:,}/{kg.prompt_tokens:,} girdi "
                    f"(%{100 * kg.cached_tokens / max(kg.prompt_tokens, 1):.0f})"))
            ks = self.kontrol_tuketim
            if ks.requests:
                self.stdout.write(f"  Kontrol tüketimi: {ks.requests} istek · "
                                  f"{ks.prompt_tokens:,} girdi + {ks.completion_tokens:,} çıktı · "
                                  f"${K.maliyet(ks):.4f} · 10.000 kelime ≈ "
                                  f"${K.maliyet(ks) / ks.requests * 10000:.2f}")
        self.stdout.write(f"Tüketim: {t}")
        if t.requests:
            self.stdout.write(
                f"Kelime başına: {t.total_tokens // t.requests:,} token · "
                f"${t.cost_usd / t.requests:.5f} · {gecen / t.requests:.1f} sn")
            self.stdout.write(f"Bu hızla 10.000 kelime: ${t.cost_usd / t.requests * 10000:.2f}")
            if t.real_cost:
                self.stdout.write(self.style.WARNING(
                    f"Üretici GERÇEK fatura: ${t.real_cost:.4f} · 10.000 kelime ≈ "
                    f"${t.real_cost / t.requests * 10000:.2f}"))
        self.stdout.write(f"Toplam süre: {gecen:.1f} sn · cevaplar: {depo.yol}/anlamlar.jsonl")
