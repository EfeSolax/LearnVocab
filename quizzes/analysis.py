"""
Bilgi analizi — hangi kelimeyi biliyor, nerede takılıyor.

Öğren-Geç sinyallerini okuyan yardımcılar burada. Eskiden views.py
içindeydiler; learnpass testleri de oradan alıyordu. Görünüm dosyası
yeniden yazılırken mantık buraya taşındı, views.py bunları yeniden
dışa veriyor (eski içe aktarmalar çalışmaya devam etsin diye).
"""

# wrongRatio bir YÜZDE döndürür (0-100). Eşikler de yüzde cinsindendir.
WRONG_RATIO_HIGH = 50
WRONG_RATIO_MID = 20


def encounter_signals(user):
    """
    Öğren-Geç'ten gelen iki sinyali kelime id'lerine göre döner.

    misjudged: kullanıcının "biliyorum" deyip anlamı görünce yanıldığını
               kabul ettiği kelimeler. Kendi başına ASLA çalışmayacağı
               kelimeler bunlardır — bilmediğini bilmiyor.
    learned:   Öğren-Geç'te doğrulayarak bildiği kelimeler.

    Bu iki sinyal aralıklı tekrarın ölçemediği bir şeyi ölçüyor:
    zamanlayıcı yalnızca CEVAPLARI görür, öğrencinin kendi bilgisi
    hakkındaki YARGISINI görmez. "Biliyorum deyip yanılmak", cevabı
    yanlış vermekten farklı ve daha tehlikeli bir durumdur.
    """
    from learnpass.models import WordEncounter

    kayitlar = WordEncounter.objects.filter(user=user).values_list(
        "word_id", "misjudged_count", "is_learned"
    )
    misjudged, learned = set(), set()
    for word_id, misjudged_count, is_learned in kayitlar:
        if misjudged_count:
            misjudged.add(word_id)
        elif is_learned:
            learned.add(word_id)
    return misjudged, learned


def classify_links_by_priority(links, misjudged_ids=None, learned_ids=None):
    """
    Kelime bağlantılarını üç öncelik grubuna ayırır.

    NOT: Bu fonksiyon artık kart SEÇMİYOR — seçimi zamanlayıcı yapıyor
    (bkz. scheduler.py). Yalnızca analiz sayfasında "hangi kelimelerde
    zorlanıyorsun" tablosunu kurmak için kullanılıyor. Eski quiz
    sisteminde bu üç grup doğrudan soru havuzuydu.
    """
    priority1, priority2, priority3 = [], [], []
    misjudged_ids = misjudged_ids or set()
    learned_ids = learned_ids or set()

    for link in links:
        if link.word_id in misjudged_ids:
            priority1.append(link)
        elif link.word_id in learned_ids:
            priority3.append(link)
        elif link.totalAttempts <= 2:
            priority1.append(link)
        elif link.totalAttempts <= 6:
            if link.wrongRatio >= WRONG_RATIO_HIGH:
                priority1.append(link)
            else:
                priority2.append(link)
        else:
            if link.wrongRatio >= WRONG_RATIO_HIGH:
                priority1.append(link)
            elif link.wrongRatio >= WRONG_RATIO_MID:
                priority2.append(link)
            else:
                priority3.append(link)

    priority1.sort(key=lambda link: (link.totalAttempts, -link.wrongRatio))
    priority2.sort(key=lambda link: link.wrongRatio, reverse=True)
    priority3.sort(key=lambda link: link.wrongRatio, reverse=True)

    return priority1, priority2, priority3


def weak_items(user, limit=20):
    """
    En çok takılınan kartlar.

    Sıralama unutma sayısına göre, doğru/yanlış oranına göre değil:
    bir kelimeyi öğrenip UNUTMAK, hiç öğrenememekten farklı bir
    problemdir ve farklı bir çözüm ister (daha sık tekrar, farklı
    boyut, ya da kelimenin gerçekten gerekli olup olmadığını sorgulamak).
    """
    from .models import ItemState, ReviewItem

    return (ReviewItem.objects
            .filter(user=user)
            .exclude(state=ItemState.NEW)
            .filter(lapses__gt=0)
            .select_related("word", "meaning")
            .order_by("-lapses", "-difficulty")[:limit])


def recent_confident_errors(user, limit=10):
    """
    Son dönemde hızlı ve yanlış cevaplanan kartlar.

    Bunlar öğrencinin "biliyorum" sandığı ama bilmediği yerler.
    Analiz sayfasında ayrı gösterilmelerinin sebebi: sıradan bir
    yanlıştan farklı olarak, bu hatalar öğrencinin kendi kendine
    fark edemeyeceği hatalardır.
    """
    from .models import ReviewLog

    return (ReviewLog.objects
            .filter(user=user, was_confident_error=True)
            .order_by("-answered_at")[:limit])


def declared_stuck(user, limit=10):
    """
    Kullanıcının "bu kadar gördüm, hâlâ öğrenemedim" dediği kelimeler.

    Bu liste diğerlerinden farklı bir şey söylüyor. "En çok unuttukların"
    davranıştan çıkarılmış bir ölçü; bu ise kullanıcının kendi teşhisi ve
    başka hiçbir yerden gelmiyor.

    Bunlara doğru cevap "daha sık sor" DEĞİL. Kullanıcı zaten yeterince
    görmüş ve olmamış; aynı yoldan devam etmek aynı sonucu verir. Doğru
    cevap kelimeyi başka bir yoldan sunmak: farklı örnek cümle, ailesi,
    daha basit karşılığı, kendi cümlesini yazdırmak. Bu liste o
    müdahalenin nereye yapılacağını söylüyor.
    """
    try:
        from learnpass.models import Declaration, WordEncounter
    except Exception:  # pragma: no cover
        return []

    return (WordEncounter.objects
            .filter(user=user, declaration=Declaration.STUCK)
            .select_related("word")
            .order_by("-times_seen")[:limit])


def declaration_summary(user):
    """Beyanların sayısal özeti — ilerleme sayfasının üst şeridi için."""
    try:
        from learnpass.models import Declaration, WordEncounter
    except Exception:  # pragma: no cover
        return {"mastered": 0, "stuck": 0}

    kayitlar = WordEncounter.objects.filter(user=user)
    return {
        "mastered": kayitlar.filter(declaration=Declaration.MASTERED).count(),
        "stuck": kayitlar.filter(declaration=Declaration.STUCK).count(),
    }
