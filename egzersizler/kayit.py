"""
Cevapların kaydı ve "Zorlandıklarım" (rapor 5).

Üç yere yazılıyor:
  - EgzersizCevabi: her cevap, kelime başına bir satır (listede olsun olmasın).
  - UserWordLink.correctCount / wrongCount: kelime listedeyse eski sayaçlar.
  - Tekrar kuralı (learnpass/tekrar.py, rapor 18.2): yanlış her zaman
    sıfırlar, doğru yalnızca kelime adayken basamağı ilerletir. L&P ile
    egzersizler aynı "son karşılaşma" zamanını paylaşır.
Ayrıca her soru günün serisine 1 sayılır (seri/hesap.py, rapor 18.9).
"Yanlışları tekrar çöz" turları (oturum.kaynak dolu) ne tekrar kuralına ne
seriye sayılır: aynı soru hemen yeniden soruluyor.
"""

from datetime import timedelta

from django.db.models import F
from django.utils import timezone

from words.models import UserWordLink, Word

from .models import EgzersizCevabi


def cevaplari_kaydet(user, oturum, soru_tipi, sonuclar):
    """
    sonuclar: [(word_id | None, dogru_mu), …]
    Döner: seri bilgisi (alevli çubuk için) ya da tekrar turunda None.
    """
    EgzersizCevabi.objects.bulk_create([
        EgzersizCevabi(user=user, word_id=wid, oturum=oturum, soru_tipi=soru_tipi, dogru=dogru)
        for wid, dogru in sonuclar
    ])
    for wid, dogru in sonuclar:
        if wid is None:
            continue
        alan = "correctCount" if dogru else "wrongCount"
        UserWordLink.objects.filter(user=user, word_id=wid).update(**{alan: F(alan) + 1})

    if oturum.kaynak_id is not None:
        return None
    from learnpass import tekrar
    from learnpass.models import WordEncounter
    from seri import hesap as seri_hesap
    kelimeler = Word.objects.in_bulk([wid for wid, _ in sonuclar if wid is not None])
    for wid, dogru in sonuclar:
        if wid in kelimeler:
            tekrar.kaydet(user, kelimeler[wid], WordEncounter.DOGRU if dogru else WordEncounter.YANLIS,
                          WordEncounter.MODE_EGZERSIZ)
    return seri_hesap.say(user, seri_hesap.EGZERSIZ)


def zorlanilan_kelime_idleri(user, gun=None):
    qs = EgzersizCevabi.objects.filter(user=user, dogru=False, word__isnull=False)
    if gun:
        qs = qs.filter(tarih__gte=timezone.now() - timedelta(days=gun))
    return qs.values_list("word_id", flat=True).distinct()


def zorlanilanlar(user, gun=None):
    """
    Kullanıcının egzersizde en az bir kez yanlış yaptığı kelimeler.
    Listem bunu kendi listesiyle kesiştirir (listede olmayan kelimeler de
    burada olabilir: fiil, kelime biçimi, eş/zıt soruları listeden bağımsız).
    `gun` verilirse yalnızca son N gündeki yanlışlar.
    """
    if not user or not user.is_authenticated:
        return Word.objects.none()
    return Word.objects.filter(id__in=zorlanilan_kelime_idleri(user, gun=gun))
