"""
Bildirim izni ön ekranının ne zaman çıkacağı (rapor 18.29).

Kullanıcı "birkaç şey yaptıktan sonra": en az 3 BİTMİŞ egzersiz oturumu ve
en az 20 L&P kartı. Ölçüt bir kez sağlanınca oturumda işaretlenir; her
sayfada yeniden sayılmaz. L&P ve egzersiz oturumlarında ve seviye testinde
çıkmaz; seviye testi daveti gösteriliyorsa da çıkmaz (iki pencere üst üste
binmesin). Cihaz aboneliği, izin durumu ve "Şimdi değil" erteleme tarayıcıda
denetlenir (templates/bildirimler/_onEkran.html).
"""

from django.db.models import F, Sum

from . import ayar

EN_AZ_EGZERSIZ = 3
EN_AZ_LP_KARTI = 20
_OTURUM_ANAHTARI = "bildirim_olcutu_tamam"

HARIC_SAYFALAR = {
    "learn_pass_run", "egzersiz_oturum",
    "seviye_testi", "seviye_ekran", "seviye_okuma", "seviye_sonuc", "seviye_sec",
    "login", "register",
}


def olcut_saglandi_mi(user):
    from egzersizler.models import EgzersizOturumu
    from learnpass.models import WordEncounter

    biten = EgzersizOturumu.objects.filter(user=user, durum=EgzersizOturumu.DURUM_BITTI).count()
    if biten < EN_AZ_EGZERSIZ:
        return False
    kart = WordEncounter.objects.filter(user=user).aggregate(
        n=Sum(F("known_count") + F("unknown_count") + F("misjudged_count")))["n"] or 0
    return kart >= EN_AZ_LP_KARTI


def on_ekran(request):
    """Context processor: `bildirim_on_ekrani_goster`."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated or not ayar.acik():
        return {}
    ad = getattr(getattr(request, "resolver_match", None), "url_name", None)
    if ad in HARIC_SAYFALAR:
        return {}
    from users.seviye import seviyesi_belli_mi
    if not seviyesi_belli_mi(user):          # önce seviye testi daveti
        return {}
    tamam = request.session.get(_OTURUM_ANAHTARI)
    if not tamam and olcut_saglandi_mi(user):
        request.session[_OTURUM_ANAHTARI] = tamam = True
    return {"bildirim_on_ekrani_goster": bool(tamam)}
