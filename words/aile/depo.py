"""
Ara depo — 1. ve 2. aşamanın çıktıları veritabanına değil buraya yazılır.

Neden veritabanı değil:
  - Bozuk bir prompt yüzlerce bozuk aile üretirse veritabanı kirlenmez;
    depoyu silip yeniden çalıştırmak yeter.
  - Birleştirme bütün taslaklara birlikte bakmak zorunda; taslaklar
    tek tek veritabanına yazılsaydı ilk gelen aile "doğru" sayılırdı.
  - Dosyalar düz metin: gözle okunur, git diff'i alınır, elle düzeltilir.

Klasör (varsayılan: proje kökünde ara-depo/):

    taslaklar.jsonl         1. aşama. Her satır bir model cevabı (denetimden
                            geçmiş hâli + ham cevap). SADECE EKLENİR: aynı
                            kelime yeniden sorulursa yeni satır yazılır ve
                            okurken SONUNCUSU geçerli sayılır. Geçmiş
                            silinmediği için "prompt'u değiştirdim, sonuç
                            nasıl değişti" sorusu cevaplanabilir.
    kararlar.json           Efe'nin elle verdiği kararlar (bkz. KARAR_SABLONU).
                            Birleştirme her çalıştığında bunları uygular.
    aileler.json            2. aşamanın çıktısı: birleşmiş aileler.
    birlestirme-raporu.txt  Aynısının okunacak hâli; incelenecekler başta.
    anlamlar.jsonl          3. aşama. Her satır bir kelimenin anlam cevabı
                            (ham + denetim + yazıldı mı). Aynı kelime için
                            SONUNCUSU geçerli. --dry-run cevapları da buraya
                            yazılır: gerçek çalıştırma onları tekrar sormaz.
"""

import json
import threading
from datetime import datetime
from pathlib import Path

from django.conf import settings

TASLAKLAR = "taslaklar.jsonl"
KARARLAR = "kararlar.json"
AILELER = "aileler.json"
RAPOR = "birlestirme-raporu.txt"
ANLAMLAR = "anlamlar.jsonl"

# kararlar.json ilk kez oluşturulurken yazılan boş şablon. Anahtarların
# anlamı dosyanın içinde de yazıyor, çünkü bu dosyayı elle düzenleyen kişi
# bu modülü açmayacak.
KARAR_SABLONU = {
    "_aciklama": {
        "kok_esle": "Iki koku ayni aile say. {\"analysis\": \"analyse\"} -> "
                    "kok 'analysis' yazan taslaklar 'analyse' ailesine girer.",
        "ayri_tut": "Ortak kelimeleri olsa bile bu kokleri BIRLESTIRME. "
                    "[[\"conscience\", \"conscious\"]]",
        "cikar": "Bir aileden kelime cikar. {\"consent\": [\"consensus\"]}",
        "uye_ata": "Iki ailede birden gecen kelimenin sahibi. "
                   "{\"consensus\": \"consensus\"}",
        "onayla": "Incelenecek durumundaki aileyi oldugu gibi kabul et. "
                  "[\"analyse\"]",
    },
    "kok_esle": {},
    "ayri_tut": [],
    "cikar": {},
    "uye_ata": {},
    "onayla": [],
}


_YAZMA_KILIDI = threading.Lock()

class Depo:
    """Ara depo klasörü üzerinde okuma/yazma."""

    def __init__(self, yol=None):
        self.yol = Path(yol) if yol else Path(settings.BASE_DIR) / "ara-depo"

    def _dosya(self, ad):
        return self.yol / ad

    def hazirla(self):
        self.yol.mkdir(parents=True, exist_ok=True)
        kararlar = self._dosya(KARARLAR)
        if not kararlar.exists():
            kararlar.write_text(json.dumps(KARAR_SABLONU, ensure_ascii=False, indent=2),
                                encoding="utf-8")

    # --- taslaklar ------------------------------------------------------

    def taslak_ekle(self, kayit):
        """Tek bir taslağı dosyanın sonuna ekler. Yalnızca ana iş parçacığı."""
        self.hazirla()
        kayit = dict(kayit)
        kayit.setdefault("tarih", datetime.now().isoformat(timespec="seconds"))
        with self._dosya(TASLAKLAR).open("a", encoding="utf-8") as dosya:
            dosya.write(json.dumps(kayit, ensure_ascii=False) + "\n")

    def tum_taslaklar(self):
        """Dosyadaki bütün satırlar, yazıldıkları sırayla (geçmiş dahil)."""
        yol = self._dosya(TASLAKLAR)
        if not yol.exists():
            return []
        satirlar = []
        for no, satir in enumerate(yol.read_text(encoding="utf-8").splitlines(), 1):
            satir = satir.strip()
            if not satir:
                continue
            try:
                satirlar.append(json.loads(satir))
            except json.JSONDecodeError:
                # Yarım yazılmış son satır (komut kesildiyse). Sessizce
                # atlamak yerine işaretle; ama bütün depoyu okunmaz yapma.
                satirlar.append({"tohum": f"<bozuk satır {no}>", "durum": "bozuk"})
        return satirlar

    def guncel_taslaklar(self):
        """
        Her (tohum, tür ipucu) için EN SON taslak.

        Aynı kelime --yeniden ile tekrar sorulduğunda eski cevap geçmişte
        kalır, birleştirmeye yenisi girer.
        """
        son = {}
        for kayit in self.tum_taslaklar():
            son[(kayit.get("tohum"), kayit.get("tur_ipucu", ""))] = kayit
        return list(son.values())

    def sorulmus_mu(self):
        """Depoda cevabı olan (tohum, tür ipucu) çiftleri."""
        return {(k.get("tohum"), k.get("tur_ipucu", ""))
                for k in self.tum_taslaklar() if k.get("durum") != "hata"}

    def uye_metinleri(self):
        """Herhangi bir geçerli taslakta üye olarak geçen bütün kelimeler."""
        metinler = set()
        for kayit in self.guncel_taslaklar():
            if kayit.get("durum") == "tamam":
                metinler |= {u["word"] for u in kayit.get("uyeler", [])}
        return metinler

    # --- kararlar -------------------------------------------------------

    def kararlar(self):
        yol = self._dosya(KARARLAR)
        if not yol.exists():
            return {k: v for k, v in KARAR_SABLONU.items() if not k.startswith("_")}
        veri = json.loads(yol.read_text(encoding="utf-8"))
        sonuc = {}
        for anahtar, bos in KARAR_SABLONU.items():
            if anahtar.startswith("_"):
                continue
            sonuc[anahtar] = veri.get(anahtar, type(bos)())
        return sonuc

    # --- birleşmiş aileler ----------------------------------------------

    def aileleri_yaz(self, aileler, ozet, rapor_metni):
        self.hazirla()
        self._dosya(AILELER).write_text(
            json.dumps({"olusturuldu": datetime.now().isoformat(timespec="seconds"),
                        "ozet": ozet, "aileler": aileler},
                       ensure_ascii=False, indent=2),
            encoding="utf-8")
        self._dosya(RAPOR).write_text(rapor_metni, encoding="utf-8")

    # --- 3. aşama: anlam cevapları ----------------------------------------

    def anlam_ekle(self, kayit):
        self.hazirla()
        kayit = dict(kayit)
        kayit.setdefault("tarih", datetime.now().isoformat(timespec="seconds"))
        satir = json.dumps(kayit, ensure_ascii=False) + "\n"
        # aile_doldur --dry-run aileleri paralel işliyor; satırlar birbirine
        # karışmasın diye tek yazar.
        with _YAZMA_KILIDI, self._dosya(ANLAMLAR).open("a", encoding="utf-8") as dosya:
            dosya.write(satir)

    def anlamlar(self):
        """(kelime, tür) -> en son anlam kaydı."""
        yol = self._dosya(ANLAMLAR)
        son = {}
        if not yol.exists():
            return son
        for satir in yol.read_text(encoding="utf-8").splitlines():
            satir = satir.strip()
            if not satir:
                continue
            try:
                kayit = json.loads(satir)
            except json.JSONDecodeError:
                continue
            son[(kayit.get("word"), kayit.get("type"))] = kayit
        return son

    def aileler(self):
        yol = self._dosya(AILELER)
        if not yol.exists():
            return []
        return json.loads(yol.read_text(encoding="utf-8")).get("aileler", [])


def liste_oku(satirlar):
    """
    Kelime listesi satırlarını (kelime, tür ipucu) çiftlerine çevirir.

    Eski enrich_words'ün biçimiyle aynı: satırda bir kelime, isteğe bağlı
    "kelime:tür", boş satır ve # yorumları atlanır — satır SONUNDAKİ yorum
    dahil ("decisively:adverb   # DB: decide" türe yapışmasın).
    """
    istekler, gorulen = [], set()
    for satir in satirlar:
        satir = satir.strip()
        if "#" in satir:
            satir = satir.split("#", 1)[0].strip()
        if not satir:
            continue
        if ":" in satir:
            metin, _, tur = satir.partition(":")
            metin, tur = metin.strip().lower(), tur.strip().lower()
        else:
            metin, tur = satir.lower(), ""
        if tur == "phrasal verb":
            tur = "phrasal_verb"
        if not metin or (metin, tur) in gorulen:
            continue
        gorulen.add((metin, tur))
        istekler.append((metin, tur))
    return istekler
