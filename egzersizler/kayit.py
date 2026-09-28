"""
Cevapların kaydı ve "Zorlandıklarım" (rapor 5).

İki yere yazılıyor:
  - EgzersizCevabi: her cevap, kelime başına bir satır (listede olsun
    olmasın). "Zorlandıklarım" buradan okunur: zorlanilanlar(user).
  - UserWordLink.correctCount / wrongCount: kelime kullanıcının listesindeyse
    eski sayaçlar da artırılır; Learn & Pass'in zorlanma puanı
    (learnpass/selection.py, "eski egzersiz sayaçları") bunları kullanıyor.
"""

from datetime import timedelta

from django.db.models import F
from django.utils import timezone

from words.models import UserWordLink, Word

from .models import EgzersizCevabi


def cevaplari_kaydet(user, oturum, soru_tipi, sonuclar):
    """sonuclar: [(word_id | None, dogru_mu), …]"""
    EgzersizCevabi.objects.bulk_create([
        EgzersizCevabi(user=user, word_id=wid, oturum=oturum, soru_tipi=soru_tipi, dogru=dogru)
        for wid, dogru in sonuclar
    ])
    for wid, dogru in sonuclar:
        if wid is None:
            continue
        alan = "correctCount" if dogru else "wrongCount"
        UserWordLink.objects.filter(user=user, word_id=wid).update(**{alan: F(alan) + 1})


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
