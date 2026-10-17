"""
Üst çubuktaki küçük seri rozeti (Efe, 17 Ekim): girişli kullanıcıda alev +
mevcut seri. Bugün tamamlandıysa alev turuncu, değilse gri.

    {% load seri %}{% ust_seri as s %}  ->  {"mevcut": 5, "bugun_tamam": True} ya da None
"""

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def ust_seri(context):
    request = context.get("request")
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return None
    from seri import hesap
    d = hesap.durum(user)
    return {"mevcut": d["mevcut"], "bugun_tamam": d["bugun_tamam"]}
