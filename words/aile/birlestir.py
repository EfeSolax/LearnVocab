"""
2. AŞAMA — taslakları aileye indirir.

Listede aynı aileden birden çok kelime olduğunda (analysis, analyst,
analyse) her biri ayrı bir taslak üretir. Bu modül onları tek aileye
indirir ve bunu yaparken modelin KENDİSİYLE TUTARLI olup olmadığını ölçer:
aynı aileye farklı kapılardan girildiğinde aynı aile mi çıkıyor?

Saf fonksiyonlar: veritabanına ve dosyaya dokunmaz, test edilmesi kolay.

AKIŞ
----
1. Kararlar uygulanır (kararlar.json): kök eşleme, çıkarılacak kelimeler.
2. Taslaklar KÖKLERİNE göre gruplanır.
3. Ortak kelimesi olan kök grupları birbirine bağlanır (ayri_tut hariç).
   Bağlı gruplar bir KÜME oluşturur.
4. Her küme için:
     - tek kök          -> tek aile. Taslaklar birbirine ne kadar
                           benziyor (örtüşme) ölçülür.
     - birden çok kök,  -> aynı aile, yalnızca kökte anlaşamamışlar.
       içerik örtüşüyor    Açık çoğunluk varsa onun kökü alınır. Oy
                           berabereyse ve köklerden biri ötekilerin
                           türediği kelimeyse o alınır (reliable, rely'dan
                           türemiş: kök rely).
     - birden çok kök,  -> KÖK ÇATIŞMASI. Otomatik birleştirilmez; her kök
       içerik örtüşmüyor   ayrı aile olarak kalır, "incelenecek" işaretlenir
                           ve iki aileyi birbirine bağlayan köprü kelimeler
                           raporlanır (consent / consensus gibi).
5. Bir kelime birden çok ailede kaldıysa tek bir sahibi seçilir.

ÖRTÜŞME (kapsama katsayısı)
---------------------------
İki taslağın ortak kelime sayısı / KÜÇÜK taslağın kelime sayısı.
decisively -> {decide, decision, decisive, decisively, indecisive}
decision   -> {decide, decision, decisive, decisively}
örtüşme = 4/4 = 1.0: küçük taslak büyüğün içinde, anlaşmazlık yok.

İlk sürümde Jaccard (ortak / toplam) kullanılıyordu ve bu, bir taslağın
ötekinden DAHA EKSİKSİZ olmasını anlaşmazlık sanıyordu: react kökünden
sorulunca reactor, reactivity geldi; overreact'tan sorulunca overreaction
geldi; ikisi de doğru, Jaccard 0.44 dedi. Kapsama katsayısı yalnızca
gerçek ayrışmayı yakalıyor: iki taslak da ötekinde olmayan ÇOK kelime
getirmişse. Eşiğin (varsayılan 0.6) altındaki aile "incelenecek".
"""

from collections import Counter, defaultdict
from itertools import combinations

ORTUSME_ESIGI = 0.6
# 3 ya da daha çok taslağı olan ailede, taslakların yarısından azında
# geçen kelime "zayıf" sayılır: tutulur ama raporda gösterilir.
ZAYIF_DESTEK = 0.5


def _n(metin):
    return (metin or "").strip().lower()


def jaccard(a, b):
    birlesim = a | b
    return len(a & b) / len(birlesim) if birlesim else 1.0


def kapsama(a, b):
    """Ortak / küçük küme. Küçük taslak büyüğün içindeyse 1.0."""
    en_kucuk = min(len(a), len(b))
    return len(a & b) / en_kucuk if en_kucuk else 1.0


def _turetme_koku(kokler):
    """
    Köklerden biri ötekilerin HEPSİNİN türediği kelimeyse onu döndürür:
    [reliable, rely] -> rely (reli-able), [decisive, decide] -> decide.
    Kural denetim._yalin_uye ile aynı (y->i, de->s gövdeleri dahil).
    """
    from words.aile.denetim import _yalin_uye
    for aday in kokler:
        if all(diger == aday or _yalin_uye(diger, {aday}) == aday for diger in kokler):
            return aday
    return None


class _Birlesim:
    """Küçük bir union-find: kök grupları kümelere ayırmak için."""

    def __init__(self):
        self.ata = {}

    def bul(self, x):
        self.ata.setdefault(x, x)
        while self.ata[x] != x:
            self.ata[x] = self.ata[self.ata[x]]
            x = self.ata[x]
        return x

    def birlestir(self, a, b):
        self.ata[self.bul(a)] = self.bul(b)


def _kararlari_hazirla(kararlar):
    esle = {_n(k): _n(v) for k, v in (kararlar.get("kok_esle") or {}).items()}

    def kanonik(kok):
        gorulen = set()
        while kok in esle and kok not in gorulen:
            gorulen.add(kok)
            kok = esle[kok]
        return kok

    ayri = {frozenset((_n(a), _n(b)))
            for cift in (kararlar.get("ayri_tut") or []) if len(cift) == 2
            for a, b in [cift]}
    cikar = defaultdict(set)
    for kok, kelimeler in (kararlar.get("cikar") or {}).items():
        cikar[kanonik(_n(kok))] |= {_n(k) for k in kelimeler}
    uye_ata = {_n(k): kanonik(_n(v)) for k, v in (kararlar.get("uye_ata") or {}).items()}
    onayla = {kanonik(_n(k)) for k in (kararlar.get("onayla") or [])}
    return kanonik, ayri, cikar, uye_ata, onayla


def birlestir(taslaklar, kararlar=None, esik=ORTUSME_ESIGI):
    """
    Döner: (aileler, disarida)
      aileler  : birleşmiş aile sözlükleri (bkz. _aile_kur)
      disarida : birleştirmeye giremeyen taslaklar (kusurlu, bulunamadı, hata)
    """
    kanonik, ayri, cikar, uye_ata, onayla = _kararlari_hazirla(kararlar or {})

    # --- 1-2. Kararlar + kök grupları ---------------------------------
    gruplar = defaultdict(list)
    disarida = []
    for taslak in taslaklar:
        if taslak.get("durum") != "tamam" or not taslak.get("uyeler"):
            disarida.append(taslak)
            continue
        kok = kanonik(_n(taslak["kok"]))
        uyeler = [u for u in taslak["uyeler"] if u["word"] not in cikar[kok]]
        gruplar[kok].append({
            **taslak, "kok": kok, "kok_ilk": taslak["kok"], "uyeler": uyeler,
            "_metinler": {u["word"] for u in uyeler},
        })

    # --- 3. Kümeler ---------------------------------------------------
    birlesim = _Birlesim()
    dizin = defaultdict(set)          # kelime -> içinde geçtiği kök grupları
    for kok, grup in gruplar.items():
        birlesim.bul(kok)
        for taslak in grup:
            for metin in taslak["_metinler"] | {kok}:
                dizin[metin].add(kok)

    for metin, kokler in dizin.items():
        if metin in uye_ata:
            continue    # sahibi elle belirlenmiş kelime köprü olamaz
        for a, b in combinations(sorted(kokler), 2):
            if frozenset((a, b)) not in ayri:
                birlesim.birlestir(a, b)

    kumeler = defaultdict(list)
    for kok in gruplar:
        kumeler[birlesim.bul(kok)].append(kok)

    # --- 4. Aileler ---------------------------------------------------
    aileler = []
    for kokler in kumeler.values():
        kokler.sort()
        if len(kokler) == 1:
            aileler.append(_aile_kur(kokler[0], gruplar[kokler[0]], esik))
            continue

        grup_kumeleri = {k: set().union(*(t["_metinler"] for t in gruplar[k])) | {k}
                         for k in kokler}
        ciftler = [(a, b, kapsama(grup_kumeleri[a], grup_kumeleri[b]))
                   for a, b in combinations(kokler, 2)]
        tum_taslaklar = [t for k in kokler for t in gruplar[k]]
        oylar = Counter(t["kok"] for t in tum_taslaklar)
        (kazanan, kazanan_oy), = oylar.most_common(1)
        gerekce = "çoğunluğun kökü"
        if kazanan_oy * 2 <= len(tum_taslaklar):
            # Açık çoğunluk yok (2. denemede rely 2 - reliable 2). Köklerden
            # biri ötekilerin türediği kelimeyse o kazanır.
            kazanan = _turetme_koku(kokler)
            gerekce = "öteki kökler ondan türediği için"

        if kazanan and all(o >= esik for _a, _b, o in ciftler):
            aile = _aile_kur(kazanan, tum_taslaklar, esik)
            dagilim = ", ".join(f"{k}: {n}" for k, n in oylar.most_common())
            aile["sorunlar"].insert(0, {
                "kod": "kok_oylamasi",
                "mesaj": f"Taslaklar kökte anlaşamadı ({dagilim}); içerik örtüştüğü "
                         f"için kök '{kazanan}' alındı ({gerekce})."})
            aileler.append(aile)
            continue

        # Kök çatışması: her kök ayrı aile, hepsi incelenecek.
        for kok in kokler:
            aile = _aile_kur(kok, gruplar[kok], esik)
            digerleri = []
            for diger in kokler:
                if diger == kok:
                    continue
                kopru = sorted(grup_kumeleri[kok] & grup_kumeleri[diger])
                if kopru:
                    digerleri.append(f"'{diger}' (ortak: {', '.join(kopru)})")
            aile["sorunlar"].insert(0, {
                "kod": "kok_catismasi",
                "mesaj": "Başka köklü taslaklarla ortak kelimesi var ama içerikleri "
                         "örtüşmüyor: " + "; ".join(digerleri) + ". Aynı aileyse "
                         "kararlar.json › kok_esle, ayrıysa › ayri_tut."})
            aile["durum"] = "incelenecek"
            aileler.append(aile)

    # --- 5. Bir kelimenin tek sahibi ----------------------------------
    _sahipleri_belirle(aileler, uye_ata)

    for aile in aileler:
        if aile["kok"] in onayla and aile["durum"] == "incelenecek":
            aile["durum"] = "temiz"
            aile["sorunlar"].append({"kod": "elle_onaylandi",
                                     "mesaj": "kararlar.json › onayla ile kabul edildi."})

    aileler.sort(key=lambda a: (a["durum"] != "incelenecek", a["kok"]))
    return aileler, disarida


def _aile_kur(kok, taslaklar, esik):
    """Aynı aileye ait taslaklardan tek aile kurar ve ölçer."""
    n = len(taslaklar)
    oy = Counter()
    bilgi = {}
    for taslak in taslaklar:
        for uye in taslak["uyeler"]:
            anahtar = (uye["word"], uye["type"])
            oy[anahtar] += 1
            bilgi.setdefault(anahtar, uye)

    uyeler = []
    for (metin, tur), adet in oy.items():
        uye = {k: v for k, v in bilgi[(metin, tur)].items()}
        uye["oy"] = adet
        uye["destek"] = round(adet / n, 2)
        uyeler.append(uye)
    uyeler.sort(key=lambda u: (u["word"] != kok, u["word"], u["type"]))

    sorunlar = []
    durum = "temiz"

    ortusme = None
    if n >= 2:
        degerler = [(a["tohum"], b["tohum"], kapsama(a["_metinler"], b["_metinler"]))
                    for a, b in combinations(taslaklar, 2)]
        ortalama = sum(o for *_x, o in degerler) / len(degerler)
        en_dusuk = min(degerler, key=lambda d: d[2])
        ortusme = {"ortalama": round(ortalama, 2), "en_dusuk": round(en_dusuk[2], 2),
                   "en_dusuk_cift": [en_dusuk[0], en_dusuk[1]]}
        if ortalama < esik:
            durum = "incelenecek"
            sorunlar.append({
                "kod": "dusuk_ortusme",
                "mesaj": f"Aynı köke çıkan {n} taslak büyük oranda örtüşmüyor "
                         f"(ortalama {ortalama:.2f} < {esik}). Model aileyi farklı "
                         f"kelimelerden farklı kurmuş; hangi üyelerin doğru olduğuna bak."})

    metinler = {u["word"] for u in uyeler}
    if kok not in metinler:
        durum = "incelenecek"
        sorunlar.append({"kod": "kok_listede_yok",
                         "mesaj": f"Kök '{kok}' hiçbir taslakta üye olarak yazılmamış."})

    if n >= 3:
        zayif = [f"{u['word']} ({u['type']}, {u['oy']}/{n})"
                 for u in uyeler if u["destek"] < ZAYIF_DESTEK]
        if zayif:
            sorunlar.append({"kod": "zayif_uye",
                             "mesaj": "Taslakların yarısından azında geçiyor: "
                                      + ", ".join(zayif)})

    # Taslaklarda tek başına kalan kelimeler: incelemede "kim neyi eklemiş"
    # sorusunun cevabı. Yalnızca birden çok taslak varsa anlamlı.
    taslak_ozeti = []
    for taslak in taslaklar:
        digerleri = set().union(*(t["_metinler"] for t in taslaklar if t is not taslak)) \
            if n >= 2 else set()
        taslak_ozeti.append({
            "tohum": taslak["tohum"],
            "kok": taslak.get("kok_ilk", taslak["kok"]),
            "uyeler": sorted(taslak["_metinler"]),
            "yalniz_bunda": sorted(taslak["_metinler"] - digerleri) if n >= 2 else [],
        })

    # Taslak düzeyindeki uyarılar tekrarsız toplanır (nadir, atılan kelime…).
    # "bilgi" seviyesindekiler (katılım sıfatı, Amerikan yazımı) rapora
    # girmiyor: gürültü yapıyordu, depoda duruyorlar.
    taslak_uyarilari = []
    for taslak in taslaklar:
        for sorun in taslak.get("sorunlar", []):
            if sorun.get("seviye") == "bilgi":
                continue
            satir = f"[{sorun['kod']}] {sorun['mesaj']}"
            if satir not in taslak_uyarilari:
                taslak_uyarilari.append(satir)

    return {
        "kok": kok,
        "durum": durum,
        "taslak_sayisi": n,
        "tohumlar": sorted({t["tohum"] for t in taslaklar}),
        "ortusme": ortusme,
        "uyeler": uyeler,
        "sorunlar": sorunlar,
        "taslak_uyarilari": taslak_uyarilari,
        "taslaklar": taslak_ozeti,
    }


def _sahipleri_belirle(aileler, uye_ata):
    """
    Birden çok ailede geçen kelimeye tek sahip seçer; diğerlerinden çıkarır.

    Sıra: (1) kararlar.json › uye_ata, (2) kelimenin KENDİSİ sorulduğunda
    modelin koyduğu aile, (3) daha çok taslakta geçtiği aile. Hiçbiri
    ayırmıyorsa kelime ilk ailede kalır ve "sahip_belirsiz" yazılır.
    """
    nerede = defaultdict(list)
    for aile in aileler:
        for metin in {u["word"] for u in aile["uyeler"]}:
            nerede[metin].append(aile)

    for metin, sahipler in nerede.items():
        if len(sahipler) < 2:
            continue

        secilen, sebep = None, ""
        if metin in uye_ata:
            secilen = next((a for a in sahipler if a["kok"] == uye_ata[metin]), None)
            sebep = "kararlar.json › uye_ata"
        if secilen is None:
            kendisi = [a for a in sahipler if metin in a["tohumlar"]]
            if len(kendisi) == 1:
                secilen, sebep = kendisi[0], "kelimenin kendisi sorulduğunda bu aile çıktı"
        if secilen is None:
            oylar = sorted(((sum(u["oy"] for u in a["uyeler"] if u["word"] == metin), a)
                            for a in sahipler), key=lambda x: -x[0])
            if oylar[0][0] > oylar[1][0]:
                secilen, sebep = oylar[0][1], "daha çok taslakta geçti"
        if secilen is None:
            secilen = sahipler[0]
            secilen["durum"] = "incelenecek"
            secilen["sorunlar"].append({
                "kod": "sahip_belirsiz",
                "mesaj": f"'{metin}' şu ailelerde de var: "
                         + ", ".join(a["kok"] for a in sahipler if a is not secilen)
                         + ". kararlar.json › uye_ata ile sahibini belirle."})
            sebep = "belirsiz"

        for aile in sahipler:
            if aile is secilen:
                continue
            aile["uyeler"] = [u for u in aile["uyeler"] if u["word"] != metin]
            aile["sorunlar"].append({
                "kod": "baska_aileye_verildi",
                "mesaj": f"'{metin}' '{secilen['kok']}' ailesine verildi ({sebep})."})
            if metin == aile["kok"]:
                aile["durum"] = "incelenecek"


def ozet(aileler, disarida):
    """Sayılar: raporun başı ve komutun son satırları."""
    durum = Counter(a["durum"] for a in aileler)
    kodlar = Counter(s["kod"] for a in aileler for s in a["sorunlar"])
    cok_taslakli = [a["ortusme"]["ortalama"] for a in aileler if a["ortusme"]]
    return {
        "aile": len(aileler),
        "temiz": durum["temiz"],
        "incelenecek": durum["incelenecek"],
        "kelime": sum(len(a["uyeler"]) for a in aileler),
        "tek_taslakli": sum(1 for a in aileler if a["taslak_sayisi"] == 1),
        "cok_taslakli": len(cok_taslakli),
        "ortalama_ortusme": round(sum(cok_taslakli) / len(cok_taslakli), 2)
        if cok_taslakli else None,
        "disarida": Counter(t.get("durum", "?") for t in disarida),
        "sorun_kodlari": dict(kodlar.most_common()),
    }
