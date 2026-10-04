"""
Yardım ve hakkında sayfası (rapor 18.33). Adres: /hakkinda/ (url adı `about`).

Ekran görüntüleri static/img/yardim/<dil>/<ad>-<acik|koyu>.webp. Telefon görünümünde
(375 px) çekilir, 500 px genişliğe küçültülür; her sürümde her dil ve tema için
baştan çekilir (rapor 18.34). Görüntü değişince yalnızca aşağıdaki işaret
konumları (x, y: görüntünün yüzdesi) güncellenir; yazılar sayfada HTML'dir.
Bir dilde yazılar uzayıp düzen kayınca o dilin konumları ISARET_DILLERI'ne yazılır.

İşaret numarası, rehberdeki adımın sırasıdır.
"""

from django.shortcuts import render
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from egzersizler.sorular import TIPLER

GORUNTU_DILLERI = {"tr", "en", "de"}   # görüntüsü çekilmiş diller; diğerleri Türkçeyi gösterir

# kimlik, adres (url adı + sorgu), başlık, giriş, görüntüler [(ad, yükseklik, [(x, y), ...])], adımlar.
# Yükseklik 500 px genişlikteki görüntünün yüksekliğidir (sayfa yüklenirken kaymasın diye).
# Bir rehberde birden çok görüntü olabilir; adımlar görüntüler arasında sırayla dağılır.
REHBERLER = [
    {
        "kimlik": "sozluk", "git": _("Sözlük'e git"), "adres": "sozluk", "sorgu": "", "baslik": _("Sözlük'te kelime aramak"),
        "giris": _("Sözlük, kelimelerin durduğu yer. İngilizce de Türkçe de arayabilirsin."),
        "goruntuler": [
            ("arama", 1082, [(50.7, 40.5), (3, 47.9)]),
            ("kelime", 1082, [(3, 60), (3, 48), (94, 48), (10, 84.7)]),
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
        "giris": _("Hazır listeler bir sınava ya da kuruma göre derlenmiş kelime listeleridir. Sözlük'ün ilk sayfasında dururlar."),
        "goruntuler": [("liste", 1082, [(3, 24), (62, 78.2)])],
        "adimlar": [
            _("Bir listeye girince kelimelerini anlamlarıyla birlikte görürsün; tek tek \"Listeme ekle\" diyebilirsin. Hepsini birden ekleme yoktur: yüzlerce kelimeyle boğulma diye."),
            _("\"Bu listeyle çalış\" dersen Learn & Pass yeni kelimeleri seviyenden değil bu listeden getirir. Bilmediklerini listene ekleyip eklememeyi oturum sonunda sen seçersin."),
        ],
    },
    {
        "kimlik": "listem", "git": _("Listem'e git"), "adres": "sozluk", "sorgu": "?sekme=listem", "baslik": _("Listem"),
        "giris": _("Listem, eklediğin kelimelerin cep defteri. Sözlük'ün ikinci sekmesi."),
        "goruntuler": [("listem", 1082, [(3, 36.5), (97, 36.5), (97, 45.6), (97, 57)])],
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
            ("lp-kart", 786, [(50, 62), (4.5, 80.3), (96, 80.3), (47.7, 5)]),
            ("lp-balon", 1033, [(97, 60), (4.5, 94.5), (96, 94.5), (71, 15.5)]),
        ],
        "adimlar": [
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
            ("kisa-sinav", 826, [(6, 34.9), (33, 67.6), (8, 86.9)]),
            ("deneme-sinavi", 1000, [(5, 43.2), (95, 80.7)]),
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
        "goruntuler": [("okuma", 1082, [(3, 60.3), (3, 71), (50, 67.1)])],
        "adimlar": [
            _("Bilmediğin kelimeye dokun; anlamı hemen bir baloncukta çıkar. \"decided\" gibi çekimli hâller köküne bağlanır, \"give up\" gibi öbekler tanınır."),
            _("Birden çok anlamı varsa hepsi numaralı ve kısa; en yaygın olan en üstte."),
            _("\"Listeme ekle\" ile kelimeyi okurken listene al."),
        ],
    },
    {
        "kimlik": "yazilar", "git": _("Yazılar'a git"), "adres": "profile_texts", "sorgu": "", "baslik": _("Yazılar"),
        "giris": _("Bir kelimeyi gerçekten bilmenin yolu onu kullanmak. Burada iki şey yapabilirsin."),
        "goruntuler": [("yazilar", 1082, [(62, 46), (7, 52.8), (6, 68)])],
        "adimlar": [
            _("Serbest yazma: 3–8 cümle yaz. Türkçe geri bildirim gelir: neyi iyi yaptığın ve gerçek hataların (alıntı → doğrusu → kısa neden), 5 üzerinden bir puanla. Üslup tercihi hata sayılmaz."),
            _("Günde yazabileceğin metin sayısı sınırlı; kalan hakkın burada yazar. Değerlendirme o an yapılamazsa metnin kaybolmaz, sonra kendiliğinden değerlendirilir."),
            _("Diyalogda doğru kelime: kısa bir diyalogdaki boşluğa, Türkçe ipucuna bakarak listendeki doğru kelimeyi yaz."),
        ],
    },
    {
        "kimlik": "seri", "git": _("Ana Sayfa'ya git"), "adres": "index", "sorgu": "#seri", "baslik": _("Seri"),
        "giris": _("Her gün biraz çalışınca takviminde bir gün daha işaretlenir."),
        "goruntuler": [("seri", 1000, [(80, 18.7), (76, 42.3), (3, 60.5)])],
        "adimlar": [
            _("Ana Sayfa'daki seri kutusuna dokun. Bir günü tamamlamak için şunlardan biri yeter: 10 Learn & Pass kartı, 10 egzersiz sorusu, 1 metin ya da 1 diyalog."),
            _("Dondurma hakkı: bir günü kaçırırsan hak varsa o gün otomatik dondurulur ve serin bozulmaz. 1 hakla başlarsın, art arda 5 gün çalışınca bir hak daha kazanırsın; en çok 3 hak birikir."),
            _("Takvimde çalıştığın günler turuncu, dondurulan günler mavi görünür. Gün senin saatinle gece 00.00'da biter."),
        ],
    },
    {
        "kimlik": "ayarlar", "git": _("Ayarlar'a git"), "adres": "settings_page", "sorgu": "", "baslik": _("Ayarlar: siteyi kendine göre ayarla"),
        "giris": _("Sağ üstteki profil fotoğrafına dokun, Hesap açılır; Ayarlar oradadır. Yaptığın her değişiklik hemen kaydedilir; kaydet düğmesi yok."),
        "goruntuler": [
            ("ayarlar-gorunum", 1000, [(49.4, 41.3), (21.6, 80.2)]),
            ("ayarlar-calisma", 1000, [(3, 15.8), (3, 54.2)]),
            ("ayarlar-tercihler", 1000, [(5, 32.6), (5, 61.5), (5, 86)]),
        ],
        "adimlar": [
            _("Görünüm: açık, koyu ya da \"sistem\" (cihazının teması). Bu seçim cihazında saklanır."),
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


# Dile özgü işaret konumları (görüntü adı → konumlar); yazılmayanlar REHBERLER'dekini kullanır.
ISARET_DILLERI = {
    "en": {
        "liste": [(3, 24), (69, 78.2)],
        "lp-balon": [(97, 60), (4.5, 87.4), (96, 87.4), (71, 15.5)],
        "kisa-sinav": [(6, 25.6), (23, 63.2), (8, 86.9)],
        "deneme-sinavi": [(5, 47.1), (95, 85)],
        "okuma": [(3, 60.3), (3, 71), (48, 67.1)],
        "yazilar": [(57, 46), (7, 52.8), (6, 68)],
        "ayarlar-gorunum": [(58.8, 41.3), (49.5, 80.2)],
        "ayarlar-calisma": [(3, 15.8), (3, 55.9)],
        "ayarlar-tercihler": [(5, 29.6), (5, 58.5), (5, 83)],
    },
    "de": {
        "kelime": [(3, 65), (3, 47), (60, 53.3), (10, 90)],
        "liste": [(3, 24), (76, 78.2)],
        "lp-balon": [(97, 60), (4.5, 90.6), (96, 90.6), (61, 15.5)],
        "kisa-sinav": [(6, 21.2), (28, 63.3), (8, 86.9)],
        "deneme-sinavi": [(5, 47.1), (95, 85)],
        "okuma": [(3, 60.3), (3, 71), (45.5, 67.1)],
        "yazilar": [(93, 50.2), (7, 57), (6, 72.3)],
        "ayarlar-gorunum": [(58.3, 41.3), (43.2, 80.2)],
        "ayarlar-calisma": [(3, 15.8), (3, 58.9)],
    },
}


def _rehberler(dil):
    """Görüntülere işaret numaralarını ve adres önekini ekler."""
    klasor = f"img/yardim/{dil}/"
    dile_ozgu = ISARET_DILLERI.get(dil, {})
    sonuc = []
    for r in REHBERLER:
        sira, goruntuler = 0, []
        for ad, yukseklik, isaretler in r["goruntuler"]:
            isaretler = dile_ozgu.get(ad, isaretler)
            goruntuler.append({"yukseklik": yukseklik,
                "acik": f"{klasor}{ad}-acik.webp", "koyu": f"{klasor}{ad}-koyu.webp",
                "isaretler": [{"no": sira + i + 1, "x": x, "y": y} for i, (x, y) in enumerate(isaretler)],
                "adimlar": [{"no": sira + i + 1, "metin": r["adimlar"][sira + i]} for i in range(len(isaretler))],
            })
            sira += len(isaretler)
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
