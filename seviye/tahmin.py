"""
Seviye tahmini (rapor 7, 18.27). Basit ve açıklanabilir.

1. KISIM — KELİME EKRANLARI
    1. ekran A1–A2 (20 + 20) · 2. ekran B1–B2 (20 + 20) · 3. ekran C1–C2 (30 + 10)
    İşaretlenen oran %60'ın ÜSTÜNDEYSE ekran geçilmiş sayılır ve sonraki
    ekran açılır; değilse kelime kısmı biter.

2. KISIM — ÖZET SORULARI (en çok 3)
    Geçilen her ekranın ÜST seviyesinden bir soru + geçilemeyen ilk ekranın
    ALT seviyesinden bir soru. İstisna: 1. ekran geçilemezse A1 ve A2.
        1 geçilemedi           -> A1 · A2
        1 geçti, 2 geçilemedi  -> A2 · B1
        1, 2 geçti, 3 geçilemedi -> A2 · B2 · C1
        üçü de geçti           -> A2 · B2 · C2

SONUÇ
    Doğru cevaplanan EN YÜKSEK seviye. Hiçbiri doğru değilse sorulan en düşük
    seviye. Soru sorulamadıysa (havuz boş) kelime ekranlarının tahmini: son
    geçilen ekranın üst seviyesi (A2 / B2 / C2), hiç geçilemediyse A1.
    Doğru cevaplar kullanıcıya gösterilmez (demoralize etmemek için).

İLK LİSTE
    Kendi seviyesindeki ekranda DOKUNMADIĞI kelimeler (A1/A2 -> 1. ekran,
    B1/B2 -> 2. ekran, C1/C2 -> 3. ekran). O ekran gösterilmediyse gösterilen
    en yakın ekran.
"""

GECME_ORANI = 0.6   # bu oranın ÜSTÜ gerekir

SEVIYE_SIRASI = ("A1", "A2", "B1", "B2", "C1", "C2")
EKRAN_SEVIYELERI = {1: ("A1", "A2"), 2: ("B1", "B2"), 3: ("C1", "C2")}
SEVIYE_EKRANI = {s: e for e, ss in EKRAN_SEVIYELERI.items() for s in ss}


def oran(sonuc):
    """{"gosterilen": 40, "bilinen": 30} -> 0.75"""
    gosterilen = sonuc.get("gosterilen") or 0
    return (sonuc.get("bilinen") or 0) / gosterilen if gosterilen else 0.0


def gecti_mi(sonuc):
    return oran(sonuc) > GECME_ORANI


def sonraki_ekran(ekran, sonuc):
    """Bu ekrandan sonra gösterilecek ekran; kelime kısmı bitiyorsa None."""
    if ekran >= 3 or not gecti_mi(sonuc):
        return None
    return ekran + 1


def gecilen_ekranlar(ekranlar):
    """Sırayla geçilen ekranlar: [1, 2] gibi (geçilemeyende durur)."""
    sonuclar = {int(k): v for k, v in ekranlar.items()}
    gecilen = []
    for ekran in (1, 2, 3):
        if ekran in sonuclar and gecti_mi(sonuclar[ekran]):
            gecilen.append(ekran)
        else:
            break
    return gecilen


def kelime_tahmini(ekranlar):
    gecilen = gecilen_ekranlar(ekranlar)
    return EKRAN_SEVIYELERI[gecilen[-1]][1] if gecilen else "A1"


def sorulacak_seviyeler(ekranlar):
    """Özet sorularının seviyeleri (kural modülün başında)."""
    gecilen = gecilen_ekranlar(ekranlar)
    if not gecilen:
        return ["A1", "A2"]
    seviyeler = [EKRAN_SEVIYELERI[e][1] for e in gecilen]
    if gecilen[-1] < 3:
        seviyeler.append(EKRAN_SEVIYELERI[gecilen[-1] + 1][0])
    return seviyeler


def sonuc_seviyesi(kelime_seviyesi, sorulan, dogru_bilinen):
    """
    sorulan: sorulan seviyeler; dogru_bilinen: doğru cevaplananların seviyeleri.
    Soru sorulamadıysa kelime tahmini döner.
    """
    if not sorulan:
        return kelime_seviyesi
    if dogru_bilinen:
        return max(dogru_bilinen, key=SEVIYE_SIRASI.index)
    return min(sorulan, key=SEVIYE_SIRASI.index)


def ilk_liste_ekrani(seviye, gosterilen_ekranlar):
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
