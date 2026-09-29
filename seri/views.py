"""Seri uçları (rapor 18.9): açılır kutunun verisi ve saat dilimi kaydı."""

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from . import hesap
from .models import SeriDurumu
from .zaman import gecerli_saat_dilimi_mi, yerel_simdi


@login_required
@require_GET
def durum(request):
    """Seri özeti + istenen ayın takvimi (?yil=2026&ay=9; yoksa bu ay)."""
    simdi = yerel_simdi(request.user)
    try:
        yil = int(request.GET.get("yil") or simdi.year)
        ay = int(request.GET.get("ay") or simdi.month)
        if not 1 <= ay <= 12 or not 2000 <= yil <= 2100:
            raise ValueError
    except ValueError:
        yil, ay = simdi.year, simdi.month
    veri = hesap.durum(request.user)
    veri.update({"yil": yil, "ay": ay, "bugun": simdi.date().isoformat(),
                 "gunler": hesap.takvim(request.user, yil, ay)})
    return JsonResponse(veri)


@login_required
@require_POST
def saat_dilimi(request):
    """Tarayıcının saat dilimini kaydeder (gün yerel 00.00'da biter)."""
    try:
        ad = json.loads(request.body or b"{}").get("saat_dilimi")
    except ValueError:
        ad = None
    if not ad or not gecerli_saat_dilimi_mi(ad):
        return JsonResponse({"ok": False}, status=400)
    SeriDurumu.objects.update_or_create(user=request.user, defaults={"saat_dilimi": ad})
    return JsonResponse({"ok": True})
