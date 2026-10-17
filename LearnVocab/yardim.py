"""
Yardım ve hakkında sayfası (rapor 18.33). Adres: /hakkinda/ (url adı `about`).

Ekran görüntüleri static/img/yardim/<dil>/<ad>-<acik|koyu>.webp. Telefon görünümünde
(375 px) çekilir, 500 px genişliğe küçültülür; araclar/yardim_goruntuleri.py hepsini
baştan çeker (rapor 18.34). İşaret konumları (x, y: görüntünün yüzdesi) ve görüntü
yükseklikleri elle yazılmaz: araç sahnedeki öğelerden hesaplayıp her dil için
yardim_isaretler.json'a yazar. Yazılar sayfada HTML'dir.

İşaret numarası, rehberdeki adımın sırasıdır. Görüntüler sayfada bir solda bir sağda durur.
"""

import json
from pathlib import Path

from django.conf import settings
from django.shortcuts import render
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from egzersizler.sorular import TIPLER

GORUNTU_DILLERI = {"tr", "en", "de"}   # görüntüsü çekilmiş diller; diğerleri Türkçeyi gösterir

# {dil: {görüntü adı: {"yukseklik": 500 px genişlikteki boy, "isaretler": [[x, y], ...]}}}
ISARETLER = json.loads((Path(__file__).with_name("yardim_isaretler.json")).read_text())

# kimlik, adres (url adı + sorgu), başlık, giriş, görüntüler (adlar), adımlar.
# Bir rehberde birden çok görüntü olabilir; adımlar görüntüler arasında işaret sayısına göre sırayla dağılır.
REHBERLER = [
    {
        "kimlik": "sozluk", "git": _("Sözlük'e git"), "adres": "sozluk", "sorgu": "", "baslik": _("Sözlük'te kelime aramak"),
        "giris": _("Sözlük, kelimelerin durduğu yer. İngilizce de Türkçe de arayabilirsin."),
        "goruntuler": [
            "arama",
            "kelime",
        ],
        "adimlar": [
            _("Arama kutusuna İngilizce bir kelime ya da Türkçe bir anlam yaz (\"karar\" yazınca decide, decision gelir)."),
            _("Yazarken açılan önerilerden birine dokun; kelimeyi sonuna kadar yazman gerekmez. Yanlış yazdıysan \"Bunu mu demek istediniz?\" çıkar; \"went\" yazarsan go'ya gider."),
            _("Kelime sayfasında her anlam ayrı: kalın Türkçe anlam, gri İngilizce tanım ve kelimenin sarıyla işaretlendiği bir örnek cümle."),
            _("US ve UK düğmeleri Amerikan ve İngiliz telaffuzunu çalar."),
            _("\"Listeme ekle\" kelimeyi listene koyar; Learn & Pass onu sana belli aralıklarla yeniden sorar."),
            _("\"örnek daha\" ve \"Kalıplar\" yerinde açılır. Örnek cümledeki bir kelimeye çift dokunursan o kelimenin sayfasına gidersin."),
        ],
    },
    {
        "kimlik": "hazir-listeler", "git": _("Hazır listelere git"), "adres": "hazir_listeler", "sorgu": "", "baslik": _("Hazır listelerle çalışmak"),
        "giris": _("Hazır listeler bir sınava ya da kuruma göre derlenmiş kelime listeleridir. Sözlük'ün ilk sayfasında kurumlara göre gruplanmış dururlar (Bilkent, ODTÜ, Cambridge ve diğerleri)."),
        "goruntuler": ["liste"],
        "adimlar": [
            _("Bir listeye girince kelimelerini anlamlarıyla birlikte görürsün; tek tek \"Listeme ekle\" diyebilirsin. Hepsini birden ekleme yoktur: yüzlerce kelimeyle boğulma diye."),
            _("\"Bu listeyle çalış\" dersen liste, Learn & Pass'e başlarken seçebileceğin listelere eklenir; haftalara bölünmüş listelerde bir haftayı seçip \"Bu kelimelerle çalış\" diyebilirsin."),
        ],
    },
    {
        "kimlik": "listem", "git": _("Listem'e git"), "adres": "sozluk", "sorgu": "?sekme=listem", "baslik": _("Listem"),
        "giris": _("Listem, eklediğin kelimelerin cep defteri. Sözlük'ün ikinci sekmesi."),
        "goruntuler": ["listem"],
        "adimlar": [
            _("Listende İngilizce ya da Türkçe ara (\"hedef\" yazınca aim çıkar)."),
            _("Filtre: en yeni, en eski ya da A→Z sırala; son bir hafta ya da ay; \"Zorlandıklarım\" bilmediğin ya da egzersizde yanlış yaptığın kelimeleri gösterir."),
            _("\"Seç\" ile birden çok kelimeyi işaretleyip birlikte çıkarabilirsin."),
            _("\"çıkar\" kelimeyi listeden alır. Yanlışlıkla çıkardıysan birkaç saniye \"Geri al\" görünür."),
        ],
    },
    {
        "kimlik": "learn-pass", "git": _("Learn & Pass'e git"), "adres": "learn_pass_page", "sorgu": "", "baslik": _("Learn & Pass"),
        "giris": _("Sitenin kalbi: kelimeyi görürsün, bilip bilmediğine karar verirsin. Birkaç dakika yeter, istediğin an bırakabilirsin; her cevap anında kaydedilir."),
        "goruntuler": [
            "lp-secim",
            "lp-kart",
            "lp-balon",
        ],
        "adimlar": [
            _("Learn & Pass'te \"Hemen kaydırmaya başla\"ya basınca önce kelimelerin nereden geleceğini seçersin. \"Listem\": listendeki kelimeler ve seviyene göre yeni kelimeler."),
            _("Hazır listelerde \"Bu listeyle çalış\" dediğin listeler de burada durur; haftalık listelerde hangi hafta olduğu yazar."),
            _("Çöp kutusu listeyi bu ekrandan kaldırır."),
            _("Bir liste seçince kelimelerin ne kadarının Listem'den, ne kadarının o listeden geleceğini çubukla ayarlarsın. Sonra \"Başla\"."),
            _("Kartta yalnızca kelime var. Anlamını aklından geçir."),
            _("Bilmiyorsan sola kaydır ya da \"Bilmiyorum\"a bas; anlamı görünür."),
            _("Biliyorsan sağa kaydır ya da \"Biliyorum\"a bas."),
            _("Üstteki çubukta alev var: o gün 10 karta ulaşınca yanar ve günün serisi tamamlanır."),
            _("\"Biliyorum\" dedikten sonra kapibara anlamı gösterir: \"Düşündüğün bu muydu?\""),
            _("Düşündüğün değilse \"Hayır, yanılmışım\" de; kelime tekrar sırasına girer."),
            _("Doğruysa \"Evet, eminim\". Kimse seni sınamaz; dürüst olman yeter."),
            _("Yanlış bir şeye bastıysan \"Geri al\"."),
        ],
        "not": _("Listene eklediğin kelimeleri 1, 3, 7 ve 21 gün sonra yeniden sorarız. Tekrar ile yeni kelime oranını Ayarlar'dan değiştirebilirsin."),
    },
    {
        "kimlik": "egzersizler", "git": _("Egzersizlere git"), "adres": "exercises_page", "sorgu": "", "baslik": _("Egzersizler: Kısa Sınav ve Deneme Sınavı"),
        "giris": _("Çalışmalar'ın ikinci sekmesi. İki çeşit var; puan ya da not yok, yanlış cevap yalnızca öğretir."),
        "goruntuler": [
            "kisa-sinav",
            "deneme-sinavi",
        ],
        "adimlar": [
            _("Kısa Sınav çoğu gün yeter: listendeki kelimelerin anlamları, iki yönlü (İngilizce→Türkçe ve tersi). Ayar yok."),
            _("10 soru sorar; listende daha az kelime varsa o kadar."),
            _("\"Başla\"ya bas. Her sorudan sonra doğrusu tek satırla görünür; sonunda yanlışlarını yeniden çözebilirsin."),
            _("Deneme Sınavı daha çok çalışmak istediğin günler için: önce kaç soru (5, 10, 15, 20) seç."),
            _("Sonra soru tipini seç: \"Karışık\" hepsinden sorar, istersen tek bir tipe odaklanırsın. Tipler aşağıda."),
        ],
        "tipler": True,
    },
    {
        "kimlik": "okumalar", "git": _("Okumalar'a git"), "adres": "readings", "sorgu": "", "baslik": _("Okumalar"),
        "giris": _("Kelimeyi metnin içinde görmek için. Kütüphanedeki metinleri okuyabilir ya da kendi metnini (PDF ya da yapıştırarak) ekleyebilirsin; kendi metinlerini yalnızca sen görürsün."),
        "goruntuler": ["okuma"],
        "adimlar": [
            _("Bilmediğin kelimeye dokun; anlamı hemen bir baloncukta çıkar. \"decided\" gibi çekimli hâller köküne bağlanır, \"give up\" gibi öbekler tanınır."),
            _("Birden çok anlamı varsa hepsi numaralı ve kısa; en yaygın olan en üstte."),
            _("\"Listeme ekle\" ile kelimeyi okurken listene al. Aynı kelimeye yeniden dokununca baloncuk kapanır."),
            _("\"işaret koy\"a basıp bir kelimeye dokunursan orası kaldığın yer olur; metne döndüğünde \"işarete git\" seni oraya götürür. İşaret bu cihazda saklanır."),
        ],
    },
    {
        "kimlik": "yazilar", "git": _("Yazılar'a git"), "adres": "profile_texts", "sorgu": "", "baslik": _("Yazılar"),
        "giris": _("Bir kelimeyi gerçekten bilmenin yolu onu kullanmak. Burada iki şey yapabilirsin."),
        "goruntuler": ["yazilar"],
        "adimlar": [
            _("Serbest yazma: önce türü seç: Günlük (3–8 cümle) ya da Akademik (1–3 paragraf; resmî dil, ihtiyatlı dil ve mantık da denetlenir). Türkçe geri bildirim gelir: neyi iyi yaptığın ve gerçek hataların (alıntı → doğrusu → kısa neden), 5 üzerinden bir puanla. Üslup tercihi hata sayılmaz."),
            _("Günde yazabileceğin metin sayısı sınırlı; kalan hakkın burada yazar. Değerlendirme o an yapılamazsa metnin kaybolmaz, sonra kendiliğinden değerlendirilir."),
            _("Diyalogda doğru kelime: kısa bir diyalogdaki boşluğa, Türkçe ipucuna bakarak listendeki doğru kelimeyi yaz."),
        ],
    },
    {
        "kimlik": "seri", "git": _("Ana Sayfa'ya git"), "adres": "index", "sorgu": "#seri", "baslik": _("Seri"),
        "giris": _("Her gün biraz çalışınca takviminde bir gün daha işaretlenir."),
        "goruntuler": ["seri"],
        "adimlar": [
            _("Ana Sayfa'daki seri kartında \"takvim ›\"a dokun. Bir günü tamamlamak için şunlardan biri yeter: 10 Learn & Pass kartı, 10 egzersiz sorusu, 1 metin ya da 1 diyalog."),
            _("Dondurma hakkı: bir günü kaçırırsan hak varsa o gün otomatik dondurulur ve serin bozulmaz. 1 hakla başlarsın, art arda 5 gün çalışınca bir hak daha kazanırsın; en çok 3 hak birikir."),
            _("Takvimde çalıştığın günler turuncu, dondurulan günler mavi görünür. Gün senin saatinle gece 00.00'da biter."),
        ],
    },
    {
        "kimlik": "ayarlar", "git": _("Ayarlar'a git"), "adres": "settings_page", "sorgu": "", "baslik": _("Ayarlar: siteyi kendine göre ayarla"),
        "giris": _("Sağ üstteki profil fotoğrafına dokun, Hesap açılır; Ayarlar oradadır. Yaptığın her değişiklik hemen kaydedilir; kaydet düğmesi yok."),
        "goruntuler": [
            "ayarlar-gorunum",
            "ayarlar-calisma",
            "ayarlar-tercihler",
        ],
        "adimlar": [
            _("Görünüm: açık, koyu ya da \"sistem\" (cihazının teması). Üstteki ay/güneş düğmesiyle de değiştirebilirsin. Bu seçim cihazında saklanır."),
            _("Dil: sitenin dili (Türkçe, English, Deutsch). Üstteki küre düğmesinden de değiştirebilirsin; giriş yaptıysan seçimin hesabında saklanır."),
            _("Türkçe anlamlar: kapatırsan Türkçe anlamlar ne gösterilir ne sorulur; kartlarda, okurken ve egzersizlerde İngilizce açıklamalar kullanılır. Sitenin dilinden bağımsızdır."),
            _("Seviye: seviye testini yeniden çözebilirsin. Günün kelimesi ve egzersizler seviyene göre gelir; çalıştıkça seviyen kendiliğinden düzeltilir."),
            _("Learn & Pass'te tekrar ve yeni kelime oranı: sola çektikçe listendeki kelimeleri daha çok tekrar edersin, sağa çektikçe daha çok yeni kelime görürsün."),
            _("Egzersizde soru sayısı: Deneme Sınavı bu sayıyla açılır."),
            _("Yazılarda geri bildirim: hataların ne kadar ayrıntılı gösterileceği (nazik, normal, titiz)."),
        ],
        "not": _("Aşağıda testlerde sesin kendiliğinden çalması, bildirim tercihleri, verilerini dosya olarak indirme ve geri alınamaz işlemler (listeyi boşaltma, hesabı silme) de vardır."),
    },
]



# Diyalog kapalıyken (settings.DIYALOG_ACIK) yardımda ondan söz edilmez: Yazılar'ın
# diyalog adımı (son adım) düşer, giriş ve seri adımı diyalogsuz yazılır.
DIYALOGSUZ = {
    "yazilar_giris": _("Bir kelimeyi gerçekten bilmenin yolu onu kullanmak. Burada serbest yazma yapabilirsin."),
    "seri_adim": _("Ana Sayfa'daki seri kartında \"takvim ›\"a dokun. Bir günü tamamlamak için şunlardan biri yeter: 10 Learn & Pass kartı, 10 egzersiz sorusu ya da 1 metin."),
}


def _diyalogsuz(r):
    if settings.DIYALOG_ACIK:
        return r
    if r["kimlik"] == "yazilar":
        return {**r, "giris": DIYALOGSUZ["yazilar_giris"], "adimlar": r["adimlar"][:-1]}
    if r["kimlik"] == "seri":
        return {**r, "adimlar": [DIYALOGSUZ["seri_adim"], *r["adimlar"][1:]]}
    return r


def _rehberler(dil):
    """Görüntülere işaret numaralarını, konumlarını ve yanını (bir sol bir sağ) ekler."""
    klasor = f"img/yardim/{dil}/"
    sonuc, kacinci = [], 0
    for r in map(_diyalogsuz, REHBERLER):
        sira, goruntuler = 0, []
        for ad in r["goruntuler"]:
            bilgi = ISARETLER[dil][ad]
            isaretler = bilgi["isaretler"][:len(r["adimlar"]) - sira]
            goruntuler.append({"ad": ad, "yukseklik": bilgi["yukseklik"], "sag": kacinci % 2 == 1,
                "acik": f"{klasor}{ad}-acik.webp", "koyu": f"{klasor}{ad}-koyu.webp",
                "isaretler": [{"no": sira + i + 1, "x": x, "y": y} for i, (x, y) in enumerate(isaretler)],
                "adimlar": [{"no": sira + i + 1, "metin": r["adimlar"][sira + i]} for i in range(len(isaretler))],
            })
            sira += len(isaretler)
            kacinci += 1
        sonuc.append({**r, "goruntuler": goruntuler, "kalan_adimlar": r["adimlar"][sira:]})
    return sonuc


def yardim_sayfasi(request):
    dil = (get_language() or "tr")[:2]
    return render(request, "pages/about.html", {
        "rehberler": _rehberler(dil if dil in GORUNTU_DILLERI else "tr"),
        "soru_tipleri": TIPLER.values(),
        "meta_aciklama": _("LearnVocab nasıl kullanılır: Sözlük, hazır listeler, Learn & Pass, "
                           "egzersizler, okumalar, yazılar, seri ve ayarlar. Siteyi kim yaptı, nasıl ulaşılır."),
    })
