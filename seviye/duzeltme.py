"""
Seviyenin kendiliğinden düzelmesi (rapor 7, 18.27). Herkese uygulanır.

Veri: son 90 günün L&P ve egzersiz karşılaşmaları (learnpass.EncounterLog).
  bilindi   : L&P "Evet, eminim" (known) ve egzersizde doğru
  bilinmedi : "bilmiyorum", "yanılmışım" ve egzersizde yanlış

Her seviye L için (Efe'nin kuralı):
  p_L = (bilinen + 1) / (görülen + 2)      # az veride zıplamasın diye yumuşatılır
  p_L > %75        -> L bitmiş, gösterdiği seviye L+1
  %35 <= p_L <= %75 -> L
  p_L < %35        -> L-1
Gösterilen seviyeler, o seviyede görülen karşılaşma sayısıyla ağırlıklandırılıp
ortalanır ve en yakın seviyeye yuvarlanır (hedef).

Kararlılık:
  - Bir seviye hesaba girmek için en az 20 karşılaşma; toplam 50 yoksa dokunulmaz.
  - Seviye haftada en çok BİR basamak, hedefe doğru oynar.
  - Seviyesi hiç belirlenmemiş kullanıcıya dokunulmaz (seviye testi daveti
    sürsün diye).
Kullanıcıya bildirilmez ("sessizce"); her değişiklik SeviyeDuzeltmesi'ne yazılır.
Çağıranlar: L&P açılış ekranı ve egzersiz bitişi.
"""

from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

SEVIYELER = ("A1", "A2", "B1", "B2", "C1", "C2")
UST_ESIK = 0.75
ALT_ESIK = 0.35
EN_AZ_SEVIYE_BASINA = 20
EN_AZ_TOPLAM = 50
PENCERE_GUN = 90
BEKLEME = timedelta(days=7)

BILINDI = ("known", "dogru")
BILINMEDI = ("unknown", "misjudged", "yanlis")


def gosterdigi_seviye(seviye, bilinen, gorulen):
    """Tek seviyenin işaret ettiği seviye (sıra numarası)."""
    i = SEVIYELER.index(seviye)
    p = (bilinen + 1) / (gorulen + 2)
    if p > UST_ESIK:
        return min(i + 1, len(SEVIYELER) - 1)
    if p < ALT_ESIK:
        return max(i - 1, 0)
    return i


def hedef_seviye(ozet):
    """
    ozet: {"B1": {"gorulen": 40, "bilinen": 31}, …} -> hedef seviye ya da None
    (veri yetersizse).
    """
    sayilanlar = {s: v for s, v in ozet.items()
                  if s in SEVIYELER and v["gorulen"] >= EN_AZ_SEVIYE_BASINA}
    toplam = sum(v["gorulen"] for v in sayilanlar.values())
    if toplam < EN_AZ_TOPLAM:
        return None
    ortalama = sum(gosterdigi_seviye(s, v["bilinen"], v["gorulen"]) * v["gorulen"]
                   for s, v in sayilanlar.items()) / toplam
    return SEVIYELER[int(ortalama + 0.5)]


def ozet_cikar(user, simdi=None):
    from learnpass.models import EncounterLog
    baslangic = (simdi or timezone.now()) - timedelta(days=PENCERE_GUN)
    satirlar = (EncounterLog.objects
                .filter(user=user, created_at__gte=baslangic, word__isnull=False,
                        verdict__in=BILINDI + BILINMEDI)
                .values("word__cefr")
                .annotate(gorulen=Count("id"), bilinen=Count("id", filter=Q(verdict__in=BILINDI))))
    return {r["word__cefr"]: {"gorulen": r["gorulen"], "bilinen": r["bilinen"]}
            for r in satirlar if r["word__cefr"] in SEVIYELER}


def seviyeyi_sessizce_duzelt(user, simdi=None):
    """Seviyeyi hedefe doğru en çok bir basamak oynatır; değiştiyse yeni seviyeyi döner."""
    from users.seviye import seviyesi_belli_mi

    from .models import SeviyeDuzeltmesi

    if user is None or not getattr(user, "is_authenticated", False) or not seviyesi_belli_mi(user):
        return None
    simdi = simdi or timezone.now()
    if SeviyeDuzeltmesi.objects.filter(user=user, olusturuldu__gt=simdi - BEKLEME).exists():
        return None
    ozet = ozet_cikar(user, simdi)
    hedef = hedef_seviye(ozet)
    if hedef is None or hedef == user.cefr:
        return None
    i, j = SEVIYELER.index(user.cefr), SEVIYELER.index(hedef)
    yeni = SEVIYELER[i + (1 if j > i else -1)]
    SeviyeDuzeltmesi.objects.create(user=user, eski=user.cefr, yeni=yeni,
                                    ozet=dict(ozet, hedef=hedef))
    user.cefr = yeni
    user.save(update_fields=["cefr"])
    return yeni
