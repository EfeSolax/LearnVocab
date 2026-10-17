"""
Yardım sayfasının ekran görüntülerini çeker ve işaret konumlarını hesaplar (rapor 18.33–18.34).

    .venv/bin/python araclar/yardim_goruntuleri.py --adres http://localhost:8781 --oturum <sessionid>
    .venv/bin/python araclar/yardim_goruntuleri.py ... --sadece seri,listem --dil tr --tema acik

Örnek hesapla giriş yapılmış bir sunucuya bağlanır (deneme veritabanı; gerçek veritabanı değil:
Learn & Pass sahnesi bir kart kaydeder). Her sahne telefon görünümünde (375 px, görüntü 500 px
genişlikte), her dil (tr, en, de) ve tema (açık, koyu) için çekilir:

    static/img/yardim/<dil>/<ad>-<acik|koyu>.webp

İşaretlerin yeri elle tahmin edilmez: sahnedeki öğenin sayfadaki konumundan hesaplanır ve
LearnVocab/yardim_isaretler.json'a yazılır ({dil: {ad: {"yukseklik", "isaretler": [[x%, y%], …]}}});
yardım sayfası konumları oradan okur. İşaret sırası, rehberdeki adımların sırasıdır.
Chrome gerekir (araclar/cdp.py).
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cdp import GENISLIK, YUKSEKLIK, Tarayici  # noqa: E402

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "static" / "img" / "yardim"
ISARET_DOSYASI = KOK / "LearnVocab" / "yardim_isaretler.json"
DILLER = {"tr": "", "en": "/en", "de": "/de"}

# Sayfaya eklenen yardımcılar (window.LVY; sitenin kendi adlarıyla çakışmasın). n(öğe, yer): işaretin noktası (CSS px, görünen alana göre).
# yer: "sol" = sol kenar boşluğu, "sag" = sağ kenar boşluğu, "orta", "solkenar", "sagkenar".
YARDIMCI = r"""
window.LVY = {
  el(s, i = 0) { const a = [...document.querySelectorAll(s)].filter(e => e.getClientRects().length);
                 const e = a[i < 0 ? a.length + i : i]; if (!e) throw new Error('öğe yok: ' + s + ' #' + i); return e; },
  n(e, yer = 'sol', dy = 0) {
    const r = e.getBoundingClientRect();
    const x = yer === 'sol' ? 11 : yer === 'sag' ? 364 : yer === 'solkenar' ? r.left
            : yer === 'sagkenar' ? r.right : r.left + r.width / 2;
    return [x, r.top + r.height / 2 + dy];
  },
  ust(e, bosluk = 110) { window.scrollTo(0, e.getBoundingClientRect().top + window.scrollY - bosluk); },
  bekle(ms) { return new Promise(r => setTimeout(r, ms)); },
  kelime(kapsam, kelime) {   // metin içindeki bir kelimenin ortası (tıklamak için)
    const w = document.createTreeWalker(kapsam, NodeFilter.SHOW_TEXT);
    for (let d; (d = w.nextNode());) {
      const i = d.data.search(new RegExp('\\b' + kelime + '\\b'));
      if (i >= 0) { const r = document.createRange(); r.setStart(d, i); r.setEnd(d, i + kelime.length);
                    const k = r.getBoundingClientRect(); return [k.left + k.width / 2, k.top + k.height / 2]; }
    }
    throw new Error('kelime yok: ' + kelime);
  },
};
true
"""


def sahne_arama(t, s):
    t.git(s + "/sozluk/")
    t.js("LVY.el('#sozluk-ara').focus(); true")
    t.komut("Input.insertText", text="deci")
    time.sleep(1.5)
    return t.js("[LVY.n(LVY.el('#sozluk-ara'), 'orta'), LVY.n(LVY.el('#sozluk-ara-oneriler li'), 'sol')]")


def sahne_kelime(t, s):
    t.git(s + "/sozluk/bank/")
    return t.js("""[LVY.n(LVY.el('[data-anlam] p'), 'sol'), LVY.n(LVY.el('[data-telaffuz="en-US"]'), 'sol'),
                    LVY.n(LVY.el('[data-kelime-liste]'), 'sag'), LVY.n(LVY.el('[data-anlam] button'), 'solkenar')]""")


def sahne_liste(t, s):
    t.git(s + "/listeler/cambridge-b1-preliminary/")
    return t.js("""[LVY.n(LVY.el('h1'), 'sol'),
                    LVY.n(LVY.el('form[action*="calis"] button'), 'orta')]""")


def sahne_listem(t, s):
    t.git(s + "/sozluk/?sekme=listem")
    return t.js("""[LVY.n(LVY.el('[data-listem] input[type=search]'), 'sol'), LVY.n(LVY.el('[data-filtre-dugmesi]'), 'sag'),
                    LVY.n(LVY.el('[data-sec-dugmesi]'), 'sag'), LVY.n(LVY.el('[data-listem-satiri] [data-kelime-liste]'), 'sag')]""")


def sahne_lp_secim(t, s):
    # Liste seçili çekilir: oran çubuğu ("Kelimeler nereden gelsin?") görünsün
    t.git(s + "/calismalar/learn-pass/sec/")
    t.js("document.querySelector('[data-liste-id] input').click(); LVY.bekle(500).then(() => true)")
    return t.js("""[LVY.n(LVY.el('[data-kaynak="listem"]'), 'sol'), LVY.n(LVY.el('[data-liste-id]'), 'sol'),
                    LVY.n(LVY.el('[data-liste-sil]'), 'sag'), LVY.n(LVY.el('[data-liste-orani]'), 'sol')]""")


def sahne_lp_kart(t, s):
    t.git(s + "/calismalar/learn-pass/karma/", bekleme=1.2)
    return t.js("""[LVY.n(LVY.el('#lp-kart'), 'orta'), LVY.n(LVY.el('[data-karar="-1"]'), 'sol'),
                    LVY.n(LVY.el('[data-karar="1"]'), 'sag'), LVY.n(LVY.el('#lp-alev'), 'orta')]""")


def sahne_lp_balon(t, s):
    # Anlam balonu uzun olabilir: görünen alan, "Evet, eminim" düğmesinin altına kadar uzatılır
    t.git(s + "/calismalar/learn-pass/karma/", bekleme=1.2)
    t.js("LVY.el('[data-karar=\"1\"]').click(); LVY.bekle(1200).then(() => true)")
    boy = t.js("window.scrollTo(0, 0); Math.ceil(LVY.el('[data-dogrula=\"1\"]').getBoundingClientRect().bottom + 24)")
    t.telefon(tema=t.tema, yukseklik=max(YUKSEKLIK, boy))
    time.sleep(0.5)
    t.js("window.scrollTo(0, 0); true")
    noktalar = t.js("""[LVY.n(LVY.el('#lp-acilim'), 'sag'), LVY.n(LVY.el('[data-dogrula="-1"]'), 'sol'),
                        LVY.n(LVY.el('[data-dogrula="1"]'), 'sag'), LVY.n(LVY.el('#lp-geri-al'), 'orta')]""")
    return {"noktalar": noktalar, "yukseklik": max(YUKSEKLIK, boy)}


def sahne_kisa_sinav(t, s):
    t.git(s + "/calismalar/egzersizler/")
    t.js("LVY.ust(LVY.el('#kisa-sinav'), 130); true")
    time.sleep(0.4)
    k = "section[aria-labelledby=kisa-sinav]"
    return t.js(f"""[LVY.n(LVY.el('#kisa-sinav'), 'sol'), LVY.n(LVY.el('{k} > div:nth-child(2) > p'), 'orta'),
                     LVY.n(LVY.el('{k} button[type=submit]'), 'sol')]""")


def sahne_deneme_sinavi(t, s):
    t.git(s + "/calismalar/egzersizler/")
    t.js("LVY.ust(LVY.el('#deneme-sinavi'), 110); true")
    time.sleep(0.4)
    f = "section:has(#deneme-sinavi) fieldset"
    return t.js(f"""[LVY.n(LVY.el('{f}', 0), 'sol'), LVY.n(LVY.el('{f} legend', 1), 'sag')]""")


def sahne_okuma(t, s):
    t.git(s + "/okumalar/the-tichborne-case/")
    t.js("LVY.ust(LVY.el('[data-okuma-metni]'), 150); true")
    time.sleep(0.4)
    x, y = t.js("LVY.kelime(LVY.el('[data-okuma-metni]'), 'proposed')")
    t.tikla(x, y)
    time.sleep(1.5)
    return t.js(f"""[[11, {y}], LVY.n(LVY.el('[data-kelime-baloncugu] li, [data-kelime-baloncugu] p'), 'sol'),
                    LVY.n(LVY.el('[data-kelime-baloncugu] [data-kelime-liste]'), 'orta'),
                    LVY.n(LVY.el('[data-isaret-koy]'), 'orta')]""")


def sahne_yazilar(t, s):
    # Yazılar'ın adresi dile göre çevrilir (/yazilar/, /en/writing/ …): alt menüdeki bağlantıdan alınır
    t.git(s + "/")
    t.git(t.js("[...document.querySelectorAll('nav a[href]')].filter(a => a.getClientRects().length).at(-1).href"))
    return t.js("""[LVY.n(LVY.el('[data-yazmaya-basla]'), 'orta'), LVY.n(LVY.el('[data-yazmaya-basla] + p, [data-yazmaya-basla] ~ p'), 'sol')]""")


def sahne_seri(t, s):
    t.git(s + "/")
    t.js("LVY.ust(LVY.el('#seri'), 80); LVY.el('[data-seri-kutusu] button').click(); LVY.bekle(1200).then(() => true)")
    return t.js("""[LVY.n(LVY.el('[data-seri-kutusu] button'), 'sag'),
                    LVY.n(LVY.el('[data-seri-kutusu] [role=dialog] p', 2), 'sag'),
                    LVY.n(LVY.el('[data-seri-kutusu] [role=dialog] .grid', 1), 'sol')]""")


def sahne_ayarlar_gorunum(t, s):
    t.git(s + "/ayarlar/")
    return t.js("""[LVY.n(LVY.el('[data-tema-ayari]'), 'orta'), LVY.n(LVY.el('[data-dil-ayari]'), 'sol')]""")


def sahne_ayarlar_calisma(t, s):
    t.git(s + "/ayarlar/")
    t.js("LVY.ust(LVY.el('[data-turkce-anlamlar-ayari]'), 120); true")
    time.sleep(0.4)
    return t.js("""[LVY.n(LVY.el('[data-turkce-anlamlar-ayari]'), 'sol'), LVY.n(LVY.el('[data-seviye-ayari]'), 'sol')]""")


def sahne_ayarlar_tercihler(t, s):
    t.git(s + "/ayarlar/")
    t.js("LVY.ust(LVY.el('[data-oran-ayari]'), 120); true")
    time.sleep(0.4)
    return t.js("""[LVY.n(LVY.el('[data-oran-ayari]'), 'sol'), LVY.n(LVY.el('[data-soru-sayisi-ayari]'), 'sol'),
                    LVY.n(LVY.el('[data-sertlik-ayari]'), 'sol')]""")


SAHNELER = {
    "arama": sahne_arama, "kelime": sahne_kelime, "liste": sahne_liste, "listem": sahne_listem,
    "lp-secim": sahne_lp_secim, "lp-kart": sahne_lp_kart, "lp-balon": sahne_lp_balon,
    "kisa-sinav": sahne_kisa_sinav, "deneme-sinavi": sahne_deneme_sinavi, "okuma": sahne_okuma,
    "yazilar": sahne_yazilar, "seri": sahne_seri, "ayarlar-gorunum": sahne_ayarlar_gorunum,
    "ayarlar-calisma": sahne_ayarlar_calisma, "ayarlar-tercihler": sahne_ayarlar_tercihler,
}


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--adres", default="http://localhost:8781")
    a.add_argument("--oturum", required=True, help="örnek hesabın sessionid çerezi")
    a.add_argument("--sadece", default="", help="virgülle sahne adları")
    a.add_argument("--dil", default="tr,en,de")
    a.add_argument("--tema", default="acik,koyu")
    a.add_argument("--cikti", default=str(CIKTI), help="görüntü klasörü (deneme için başka bir yer)")
    a.add_argument("--isaret-yazma", action="store_true", help="yardim_isaretler.json'a yazma")
    g = a.parse_args()

    sahneler = [s for s in g.sadece.split(",") if s] or list(SAHNELER)
    isaretler = json.loads(ISARET_DOSYASI.read_text()) if ISARET_DOSYASI.exists() else {}
    with Tarayici() as t:
        t.cerez("sessionid", g.oturum, g.adres)
        t.komut("Emulation.setFocusEmulationEnabled", enabled=True)
        t.komut("Page.addScriptToEvaluateOnNewDocument", source=YARDIMCI)
        for dil in g.dil.split(","):
            t.cerez("django_language", dil, g.adres)   # "Bu sayfanın Türkçesi de var" kutusu çıkmasın
            for tema in g.tema.split(","):
                t.tema = tema
                for ad in sahneler:
                    t.telefon(tema=tema)
                    sonuc = SAHNELER[ad](t, g.adres + DILLER[dil])
                    noktalar, boy = (sonuc["noktalar"], sonuc["yukseklik"]) if isinstance(sonuc, dict) else (sonuc, YUKSEKLIK)
                    time.sleep(0.5 if tema == "koyu" else 0.2)   # koyu temada üst çubuğun renk geçişi bitsin
                    yol = Path(g.cikti) / dil / f"{ad}-{tema}.webp"
                    t.kaydet(str(yol), yukseklik=boy)
                    yuzde = [[round(x / GENISLIK * 100, 1), round(y / boy * 100, 1)] for x, y in noktalar]
                    if tema == "acik":
                        from PIL import Image
                        with Image.open(yol) as im:
                            yukseklik = im.size[1]
                        isaretler.setdefault(dil, {})[ad] = {"yukseklik": yukseklik, "isaretler": yuzde}
                    print(f"{dil} {tema} {ad}: {yuzde}", flush=True)
    if not g.isaret_yazma:
        ISARET_DOSYASI.write_text(json.dumps(isaretler, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
