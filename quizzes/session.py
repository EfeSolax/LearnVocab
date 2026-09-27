"""
Oturum motoru — hangi kart, hangi sırayla, cevaptan sonra ne olacak.

OTURUMUN ŞEKLİ
--------------
Kullanıcı tip seçmiyor, soru sayısı seçmiyor. "Çalış" diyor ve sırası
gelen kartlar geliyor. Seçim kaldırıldı çünkü seçim yanlış yapılıyordu:
insan kendini iyi hissettiren tipi seçer (tanıma), zorlandığını seçmez
(üretim) — oysa öğreten ikincisidir. Zorluğu kullanıcıya seçtirmek,
zorluğun faydasını ortadan kaldırır.

KUYRUK NASIL DİZİLİR
--------------------
İki kural birlikte çalışıyor:

  1. Sırası gelenler önce, en gecikmişi en önde.
  2. Aynı kelimenin iki kartı arka arkaya GELMEZ.

İkincisi karıştırma (interleaving) ilkesi. Aynı kelimeyi arka arkaya
sormak öğrenciye o kelimeyi bildiği hissini verir ama kalıcılığı
düşürür: ikinci soruda cevap hâlâ kısa süreli hafızadadır, hatırlama
denemesi gerçekleşmez. Araya başka kelimeler girdiğinde her soru
gerçek bir hatırlama olur.

OTURUM İÇİ TEKRAR
-----------------
Yanlış cevaplanan kart oturumun sonunda değil, ARADA tekrar soruluyor:
önce ~3 soru sonra, hâlâ bilinmiyorsa ~8 soru sonra. Genişleyen
aralıklarla tekrar, sabit aralıkla tekrardan iyi sonuç veriyor ve
oturumu da uzatmıyor.
"""

import random
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from . import aspects, build, questions, scheduler
from .aspects import Aspect
from .models import (
    DailyGoalDefaults, ItemState, ReviewItem, ReviewLog, SessionMode,
    StudySession, due_items, new_items, overdue_count,
)


# Bir oturumda sorulacak en fazla kart. Sınırsız bırakmak, birikmiş
# tekrarı olan kullanıcıya 300 kartlık bir duvar göstermek demek —
# uygulamayı bıraktıran şey tam olarak budur. Kalanlar kaybolmuyor,
# bir sonraki oturumda geliyor.
OTURUM_UST_SINIRI = 40

# Yanlış cevaplanan kartın kuyruğa geri konacağı mesafeler.
TEKRAR_MESAFELERI = (3, 8)


# ----------------------------------------------------------------------
# Kuyruk kurma
# ----------------------------------------------------------------------

def _serpistir(item_ids, word_by_item, mesafe=aspects.AYNI_KELIME_MESAFESI):
    """
    Aynı kelimenin kartlarını birbirinden uzaklaştırır.

    Açgözlü bir yerleştirme: sıradaki kartı koymak son `mesafe` kart
    içinde aynı kelimeyi tekrar ederse, o kart ertelenir ve sonraki
    uygun aday öne alınır. Hiç uygun aday yoksa kural gevşetilir —
    tek kelimeyle çalışan bir kullanıcıda kuyruk boş kalmasın.
    """
    kalan = list(item_ids)
    sonuc = []
    while kalan:
        son_kelimeler = {word_by_item.get(i) for i in sonuc[-mesafe:]}
        secilen_index = None
        for i, item_id in enumerate(kalan):
            if word_by_item.get(item_id) not in son_kelimeler:
                secilen_index = i
                break
        if secilen_index is None:
            # Hiçbir aday kurala uymuyor (kullanıcının az kelimesi var).
            # Kuralı tamamen bırakmak yerine EN ESKİ görülen kelimeyi
            # seçiyoruz: art arda gelmesi kaçınılmazsa bile en az zararlı
            # olan tekrar, aradan en çok soru geçmiş olanıdır.
            son_sira = {}
            for konum, onceki in enumerate(sonuc):
                son_sira[word_by_item.get(onceki)] = konum
            secilen_index = min(
                range(len(kalan)),
                key=lambda i: son_sira.get(word_by_item.get(kalan[i]), -1),
            )
        sonuc.append(kalan.pop(secilen_index))
    return sonuc


def _yeni_kart_butcesi(user, now=None):
    """
    Bugün kaç yeni kart açılabilir?

    Kullanıcının günlük hedefi (UserSettings.dailyGoal) taban; ama
    birikmiş tekrar eşiği aşarsa yeni kart hiç açılmıyor. Borç varken
    yeni borç açmamak, aralıklı tekrar uygulamalarında bırakmanın
    bir numaralı sebebini (birikmiş yığın) ortadan kaldırıyor.
    """
    from .models import new_items_introduced_today

    try:
        hedef = user.mysettings.dailyGoal
    except Exception:
        hedef = DailyGoalDefaults.NEW_ITEMS_FALLBACK

    if hedef is None:
        hedef = DailyGoalDefaults.NEW_ITEMS_FALLBACK
    if hedef <= 0:
        return 0

    if overdue_count(user, now) > DailyGoalDefaults.BACKLOG_BLOCK_THRESHOLD:
        return 0

    kalan = hedef - new_items_introduced_today(user, now)
    return max(kalan, 0)


def _beyana_gore_sirala(user, kartlar):
    """
    Öğren-Geç beyanlarını sıralamaya uygular.

    "Hâlâ öğrenemedim" denen kelimelerin kartları öne, "artık öğrendim"
    denenler arkaya alınıyor. Grup içindeki sıra (en gecikmiş önce)
    korunuyor.

    DİKKAT — BEYAN YALNIZCA SIRALAMAYI DEĞİŞTİRİR, ZAMANLAMAYI DEĞİL.
    Kartın kararlılığı, zorluğu ve bir sonraki tekrar günü kullanıcının
    CEVAPLARINDAN hesaplanıyor (scheduler.py) ve kendi hakkındaki yargısı
    o hesaba girmiyor. Girseydi kullanıcı, farkında olmadan sistemin
    kendisini yanıltmasına izin vermiş olurdu: "öğrendim" diyerek
    aralıkları şişirmek, unutmanın en kısa yolu.

    Aynı gün sırası gelmiş kartlar arasında sıra değiştirmek ise zararsız
    ve faydalı: takıldığı kelime, oturumun dikkati en açık olduğu başına
    denk geliyor.
    """
    try:
        from learnpass.models import Declaration, WordEncounter
    except Exception:  # pragma: no cover — learnpass yoksa sıra bozulmasın
        return kartlar

    beyanlar = dict(
        WordEncounter.objects
        .filter(user=user, word_id__in=[k.word_id for k in kartlar])
        .exclude(declaration=Declaration.NONE)
        .values_list("word_id", "declaration")
    )
    if not beyanlar:
        return kartlar

    def oncelik(kart):
        beyan = beyanlar.get(kart.word_id)
        if beyan == Declaration.STUCK:
            return 0
        if beyan == Declaration.MASTERED:
            return 2
        return 1

    return sorted(kartlar, key=oncelik)


def _yeni_kart_sirasi(user, adet):
    """
    Açılacak yeni kartları MERDİVEN sırasına göre seçer.

    İlk sürümde bu satır `order_by("aspect", "id")` idi ve gerçek veride
    şu çıktı: yirmi kartlık oturumun yirmisi de "eş dizim" oldu. Sebebi
    aptalca ama sessizdi — alfabetik sıralamada `collocation`,
    `recognize`ın önüne geçiyor. Yani sistem öğrenciye hiç tanımadığı
    kelimelerin eş dizimlerini soruyordu.

    Doğru sıra alfabe değil KADEME: önce tanıma, sonra üretim, sonra
    kullanım. Kademe içinde boyutun ağırlığı belirliyor, en sonda kart
    id'si (eski kelimeler önce).
    """
    kartlar = list(new_items(user).select_related("word")[:adet * 20])
    kartlar.sort(key=lambda k: (
        _kademe_sirasi(k.aspect),
        -aspects.ASPECTS[k.aspect].weight,
        k.id,
    ))
    return kartlar[:adet]


def _kademe_sirasi(aspect):
    """
    Kademenin açılma sırası.

    Ayırt etme boyutları (kademe 0) tanımadan hemen sonra geliyor:
    kelimeyi tanıdıktan sonra "ama şununla karıştırma" demek için doğru
    an burasıdır — üretmeyi beklemek, yanlışın yerleşmesine zaman tanır.
    """
    kademe = aspects.stage_of(aspect)
    return {aspects.STAGE_ENTRY: 0,
            aspects.STAGE_GUARD: 1,
            aspects.STAGE_PRODUCTION: 2,
            aspects.STAGE_USE: 3}.get(kademe, 4)


def _mod_havuzu(user, mode, list_id=None, now=None):
    """Moda göre kartların geldiği taban sorgu."""
    now = now or timezone.now()

    if mode == SessionMode.WEAK:
        # Zorlandıkları: en az bir kez unutulmuş ya da zorluğu yüksek
        # kartlar. Sırası gelmemiş olsalar bile sorulabilirler — bu
        # kullanıcının bilinçli olarak programın dışına çıktığı moddur.
        return (ReviewItem.objects
                .filter(user=user)
                .exclude(state=ItemState.NEW)
                .filter(lapses__gt=0)
                .order_by("-lapses", "-difficulty"))

    if mode == SessionMode.LIST and list_id:
        return (ReviewItem.objects
                .filter(user=user, word__in_user_lists__id=list_id)
                .order_by("due_at", "id"))

    return due_items(user, now).order_by("due_at", "id")


@transaction.atomic
def start(user, mode=SessionMode.DUE, list_id=None, now=None) -> StudySession:
    """
    Yeni bir çalışma oturumu kurar ve kuyruğunu doldurur.

    Giriş kartları burada tamamlanıyor: kullanıcı kelime eklemiş ama
    henüz çalışmamışsa, kartları oturuma girdiği anda açılıyor. Kelime
    ekleme akışına dokunmadan çalışmasının sebebi bu.
    """
    now = now or timezone.now()

    build.ensure_all_entry_items(user)

    # Önce gereğinden fazla çekilip beyana göre sıralanıyor, sonra
    # kesiliyor: kesme önce yapılsaydı "hâlâ öğrenemedim" denen kelimeler
    # sınırın dışında kalabilirdi.
    havuz = list(_mod_havuzu(user, mode, list_id, now)[:OTURUM_UST_SINIRI * 2])
    havuz = _beyana_gore_sirala(user, havuz)[:OTURUM_UST_SINIRI]

    # Yeni kartlar yalnızca normal modda ve bütçe elverdiğinde.
    if mode == SessionMode.DUE:
        butce = _yeni_kart_butcesi(user, now)
        yer = max(OTURUM_UST_SINIRI - len(havuz), 0)
        if butce and yer:
            havuz.extend(_yeni_kart_sirasi(user, min(butce, yer)))

    word_by_item = {i.id: i.word_id for i in havuz}
    sira = _serpistir([i.id for i in havuz], word_by_item)

    return StudySession.objects.create(
        user=user, mode=mode, queue=sira, planned_count=len(sira),
    )


# ----------------------------------------------------------------------
# Soru akışı
# ----------------------------------------------------------------------

def next_question(session, rng=None):
    """
    Kuyruğun başındaki karttan soru üretir.

    Soru üretilemeyen kart (verisi eksik) kuyruktan SESSİZCE düşürülüyor
    ve bir sonrakine geçiliyor. Kullanıcıya "bu kelime için soru
    üretilemedi" demenin bir faydası yok; onun için bu kart hiç var
    olmadı.
    """
    rng = rng or random

    while session.queue:
        item_id = session.queue[0]
        item = (ReviewItem.objects
                .filter(id=item_id, user=session.user)
                .select_related("word", "meaning", "word__family")
                .first())

        if item is None:
            session.queue.pop(0)
            session.save(update_fields=["queue"])
            continue

        soru = questions.build(item)
        if soru is None:
            session.queue.pop(0)
            # Üretilemeyen kart bir daha denenmesin diye ileri atılıyor:
            # veri sonradan gelebilir (zenginleştirme hattı çalışınca),
            # ama bugün tekrar denemenin anlamı yok.
            if item.state == ItemState.NEW:
                item.due_at = timezone.now() + timedelta(days=1)
                item.save(update_fields=["due_at"])
            session.save(update_fields=["queue"])
            continue

        return item, soru

    return None, None


@transaction.atomic
def answer(session, item, user_input, seconds=None, used_hint=False,
           rng=None, now=None):
    """
    Bir cevabı işler: değerlendirir, zamanlar, kaydeder, kuyruğu günceller.

    Dönen sözlük geri bildirim ekranını besliyor.
    """
    rng = rng or random
    now = now or timezone.now()

    soru = questions.build(item)
    if soru is None:
        # Soru arada bozulduysa cevabı yok say ve kartı kuyruktan çıkar.
        _kuyruktan_cikar(session, item.id)
        return {"ok": False}

    dogru = soru.check(user_input)
    beklenen = soru.expected_seconds
    uretim_mi = soru.is_production

    nota = scheduler.not_uret(dogru, seconds, beklenen, used_hint, uretim_mi)
    guvenli_hata = scheduler.yuksek_guvenli_hata(dogru, seconds, beklenen)

    gecen_gun = item.elapsed_days
    onceki = item.memory()
    yeni = scheduler.guncelle(onceki, nota, gecen_gun)
    gun = scheduler.sonraki_aralik(yeni, rng=rng)

    # --- durum geçişleri ---
    if nota == scheduler.YENIDEN:
        item.lapses += 1
        item.state = (ItemState.RELEARNING if item.state == ItemState.REVIEW
                      else ItemState.LEARNING)
    else:
        item.state = ItemState.REVIEW

    item.reps += 1
    item.stability = yeni.kararlilik
    item.difficulty = yeni.zorluk
    item.last_reviewed_at = now
    item.last_interval_days = gun

    sira_gunu = now + timedelta(days=gun)

    # Yüksek güvenli hata: bir hafta içinde mutlaka tekrar sorulsun.
    #
    # DİKKAT — burada bir kez sonsuz döngü vardı: işaret konuyordu ama
    # HİÇBİR ZAMAN kalkmıyordu. Zorunlu tarih geçtikten sonra da sıra
    # günü ona sabitleniyor, kart geçmiş bir tarihe kilitleniyor ve
    # sonsuza kadar "sırası gelmiş" görünüyordu. Kod hata vermiyordu;
    # kullanıcı yalnızca aynı kartı durmadan görüyordu.
    #
    # Doğru kural: işaret bir SONRAKİ tekrarda kalkar. Hafta içindeki
    # herhangi bir tekrar zorunlu kontrolü karşılar — amaç belirli bir
    # günde sormak değil, hafta geçmeden bir kez daha sormak.
    if guvenli_hata:
        item.recheck_by = now + timedelta(days=7)
    elif item.recheck_by:
        item.recheck_by = None

    # Zamanlayıcı daha uzak bir gün hesapladıysa zorunlu tarihe çekiliyor.
    if item.recheck_by and item.recheck_by < sira_gunu:
        sira_gunu = item.recheck_by

    item.due_at = sira_gunu
    item.save()

    # --- kayıt ---
    ReviewLog.objects.create(
        user=session.user, item=item, session=session,
        word_text=soru.word_text or item.word.text,
        aspect=item.aspect, format=soru.format,
        is_correct=dogru, grade=nota, seconds=seconds,
        used_hint=used_hint, was_confident_error=guvenli_hata,
        elapsed_days=gecen_gun,
        stability_before=(onceki.kararlilik if onceki else None),
        difficulty_before=(onceki.zorluk if onceki else None),
        stability_after=yeni.kararlilik, difficulty_after=yeni.zorluk,
        scheduled_days=gun,
    )

    # --- üst kademeyi açmayı dene ---
    acilan = build.unlock_after_review(item)

    # --- kuyruk ---
    _kuyruktan_cikar(session, item.id)
    if not dogru:
        _oturum_ici_tekrar(session, item.id)
        if item.id not in session.missed:
            session.missed.append(item.id)

    session.answered_count += 1
    if dogru:
        session.correct_count += 1
    session.save(update_fields=["queue", "missed", "answered_count",
                                "correct_count"])

    return {
        "ok": True,
        "correct": dogru,
        "question": soru,
        "grade": nota,
        "grade_label": scheduler.NOT_ADLARI[nota],
        "confident_error": guvenli_hata,
        "next_days": gun,
        "unlocked": acilan,
        "remaining": len(session.queue),
    }


def _kuyruktan_cikar(session, item_id):
    session.queue = [i for i in session.queue if i != item_id]


def _oturum_ici_tekrar(session, item_id):
    """
    Yanlış bilinen kartı kuyruğa geri koyar.

    Mesafe, kartın bu oturumda kaçıncı kez yanlış bilindiğine göre
    büyüyor: ilk hatada 3 kart sonra, ikinci hatada 8 kart sonra.
    Genişleyen aralık, sabit aralıktan daha iyi tutuyor çünkü her
    denemede hatırlama biraz daha zor — ama hâlâ mümkün.
    """
    kacinci = session.missed.count(item_id)
    mesafe = TEKRAR_MESAFELERI[min(kacinci, len(TEKRAR_MESAFELERI) - 1)]
    konum = min(mesafe, len(session.queue))
    session.queue.insert(konum, item_id)


def finish(session):
    """Oturumu kapatır ve özet verisini döner."""
    session.finish()

    kartlar = (ReviewItem.objects
               .filter(id__in=session.missed)
               .select_related("word"))

    return {
        "session": session,
        "missed_words": [k.word for k in kartlar],
        "accuracy": session.accuracy,
    }


def summary_for(user, now=None):
    """Çalışma sayfasının üst kısmındaki durum özeti."""
    from .models import knowledge_score, study_streak

    now = now or timezone.now()
    return {
        "due": due_items(user, now).count(),
        "new_budget": _yeni_kart_butcesi(user, now),
        "new_available": new_items(user).count(),
        "knowledge": knowledge_score(user),
        "streak": study_streak(user, now),
        "total_items": ReviewItem.objects.filter(user=user).count(),
    }
