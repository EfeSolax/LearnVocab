"""
Sayfalama yardımcıları.

"Kelimelerim" sayfasındaki esnek sayfalama (ilk/son, sayfa numaraları, sayfa
başına adet, doğrudan sayfaya atlama) tek bir şablon parçasından besleniyor.
Bu modül o parçanın ihtiyaç duyduğu bağlamı üretiyor; böylece aynı arayüz
birden fazla listede tekrar yazılmadan kullanılabiliyor.
"""

from urllib.parse import urlencode


def build_page_window(current, total, side=3):
    """
    Sayfa numarası listesi üretir; boşluklar None (ellipsis) ile gösterilir.

    Örn: current=10, total=20, side=3 -> [1, None, 7,8,9,10,11,12,13, None, 20]
    """
    if total <= 1:
        return [1] if total == 1 else []

    start = max(2, current - side)
    end = min(total - 1, current + side)

    pages = [1]
    if start > 2:
        pages.append(None)
    pages.extend(range(start, end + 1))
    if end < total - 1:
        pages.append(None)
    pages.append(total)

    # Tekilleştir: 1 veya son sayfa komşulukta tekrar etmesin
    seen = set()
    cleaned = []
    for page in pages:
        if page is None:
            if cleaned and cleaned[-1] is None:
                continue
            cleaned.append(None)
            continue
        if page in seen:
            continue
        seen.add(page)
        cleaned.append(page)

    return cleaned


def resolve_per_page(request, options, default):
    """?per_page= değerini doğrular; geçersizse varsayılana döner."""
    try:
        value = int(request.GET.get("per_page", default))
    except (TypeError, ValueError):
        return default
    return value if value in options else default


def pagination_context(page_obj, paginator, *, params, per_page, per_page_options,
                       default_per_page, side=3):
    """
    Sayfalama şablon parçası için bağlam üretir.

    params: [(ad, deger), ...] — sayfa bağlantılarında korunacak filtreler.
            Boş, None ve "all" değerleri atılır.
    """
    kept = [
        (name, str(value))
        for name, value in params
        if value not in (None, "", "all")
    ]

    query_pairs = list(kept)
    if per_page != default_per_page:
        query_pairs.append(("per_page", str(per_page)))

    return {
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "page_window": build_page_window(page_obj.number, paginator.num_pages, side=side),
        # Sayfa bağlantılarına eklenecek sorgu dizesi ("page" hariç)
        "base_qs": urlencode(query_pairs),
        "per_page": per_page,
        "per_page_options": list(per_page_options),
        "default_per_page": default_per_page,
        # Şablondaki küçük GET formlarının gizli alanları
        "pagination_params": [{"name": name, "value": value} for name, value in kept],
    }
