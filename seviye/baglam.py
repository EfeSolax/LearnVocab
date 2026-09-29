"""
Seviye testi daveti her sayfada (rapor 18.27).

Kullanıcı testi yapana ya da "Seviyemi kendim seçeyim" diyene kadar her sayfa
açılışında küçük bir davet çıkar (pages/seviye/_davetPenceresi.html; "Kapat"
yalnızca o sayfa için kapatır). L&P ve egzersiz oturumlarında ve seviye testi
sayfalarının kendisinde çıkmaz: odağı bozmasın.
"""

HARIC_SAYFALAR = {
    "learn_pass_run", "egzersiz_oturum",
    "seviye_testi", "seviye_ekran", "seviye_okuma", "seviye_sonuc", "seviye_sec",
}


def davet(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}
    ad = getattr(getattr(request, "resolver_match", None), "url_name", None)
    if ad in HARIC_SAYFALAR:
        return {}
    from users.seviye import seviyesi_belli_mi
    return {"seviye_daveti_goster": not seviyesi_belli_mi(user)}
