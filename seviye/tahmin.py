"""
Seviye tahmini: basit ve açıklanabilir kural (rapor 7).

1. KISIM — KELİME EKRANLARI
    Bir ekranı "geçmek" = gösterilen kelimelerin en az yarısını (GECME_ORANI)
    bilmek. Ekranlar kolaydan zora gider; geçilemeyen ekranda test durur
    (rapor 7: "kolay ekranda çok az kelime bilinirse zor ekran gösterilmez").

        1. ekran (A1–A2) geçilemedi               -> A1
        2. ekran (B1)    geçilemedi               -> A2
        3. ekran (B2–C1) geçilemedi               -> B1
        3. ekran geçildi                          -> B2
        3. ekranın en az %80'i (UST_ORAN) biliniyor -> C1

2. KISIM — OKUMA (havuz doluysa; 3 metin, kolaydan zora)
    Üçü de doğruysa bir seviye yukarı (en çok C1), hiçbiri doğru değilse
    bir seviye aşağı (en az A1); 1–2 doğruda kelime tahmini kalır. Okuma
    yalnızca uçlarda düzeltir: tek bir metin şansla ya da dikkatsizlikle
    yanlış/doğru olabilir.

İLK LİSTE
    Kendi seviyesindeki ekranda DOKUNMADIĞI kelimeler (A1/A2 -> 1. ekran,
    B1 -> 2. ekran, B2/C1 -> 3. ekran). Okuma seviyeyi o ekranın dışına
    taşıdıysa ve o ekran gösterilmediyse, gösterilen en yakın ekran kullanılır.
"""

GECME_ORANI = 0.5
UST_ORAN = 0.8

SEVIYE_SIRASI = ("A1", "A2", "B1", "B2", "C1")

# Ekran geçilemediğinde tahmin (ekran numarası -> seviye).
KALINAN_SEVIYE = {1: "A1", 2: "A2", 3: "B1"}

# Seviye -> ilk listenin geldiği ekran.
SEVIYE_EKRANI = {"A1": 1, "A2": 1, "B1": 2, "B2": 3, "C1": 3}


def oran(sonuc):
    """{"gosterilen": 40, "bilinen": 30} -> 0.75"""
    gosterilen = sonuc.get("gosterilen") or 0
    return (sonuc.get("bilinen") or 0) / gosterilen if gosterilen else 0.0


def gecti_mi(sonuc):
    return oran(sonuc) >= GECME_ORANI


def sonraki_ekran(ekran, sonuc):
    """Bu ekrandan sonra gösterilecek ekran; test bitiyorsa None."""
    if ekran >= 3 or not gecti_mi(sonuc):
        return None
    return ekran + 1


def kelime_tahmini(ekranlar):
    """
    ekranlar: {1: {"gosterilen", "bilinen"}, 2: {...}, …} (anahtar int ya da str).
    Kuralı modülün başında.
    """
    sonuclar = {int(k): v for k, v in ekranlar.items()}
    for ekran in (1, 2, 3):
        sonuc = sonuclar.get(ekran)
        if sonuc is None or not gecti_mi(sonuc):
            return KALINAN_SEVIYE[ekran]
    return "C1" if oran(sonuclar[3]) >= UST_ORAN else "B2"


def okuma_duzeltmesi(seviye, dogru, toplam):
    """Okuma sonucu uçtaysa bir seviye oynatır; 2. kısım atlandıysa (toplam=0) dokunmaz."""
    if not toplam:
        return seviye
    i = SEVIYE_SIRASI.index(seviye)
    if dogru == toplam:
        i = min(i + 1, len(SEVIYE_SIRASI) - 1)
    elif dogru == 0:
        i = max(i - 1, 0)
    return SEVIYE_SIRASI[i]


def ilk_liste_ekrani(seviye, gosterilen_ekranlar):
    """İlk listenin geleceği ekran: seviyenin ekranı, gösterilmediyse en yakını."""
    hedef = SEVIYE_EKRANI[seviye]
    ekranlar = sorted(int(e) for e in gosterilen_ekranlar)
    if not ekranlar:
        return None
    return min(ekranlar, key=lambda e: (abs(e - hedef), -e))


def ilk_liste(seviye, gosterilen, bilinen):
    """
    gosterilen: {ekran: [word_id, …]}, bilinen: {ekran: [word_id, …]}
    -> seviyenin ekranında dokunulmayan kelimeler (gösterim sırasıyla).
    """
    gosterilen = {int(k): v for k, v in gosterilen.items()}
    bilinen = {int(k): set(v) for k, v in bilinen.items()}
    ekran = ilk_liste_ekrani(seviye, gosterilen)
    if ekran is None:
        return []
    return [w for w in gosterilen[ekran] if w not in bilinen.get(ekran, set())]
