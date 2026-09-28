"""
"Seviye zamanla çalışma sonuçlarına göre sessizce düzeltilir" (rapor 7).

Algoritma raporda TANIMLI DEĞİL; Efe ile konuşulacak (tekrar algoritmasıyla
birlikte ele alınması doğal: aynı L&P ve egzersiz kayıtlarını okuyacaklar).
Bu fonksiyon bilerek hiçbir şey yapmıyor ve henüz hiçbir yerden
çağrılmıyor. Karar verilince:

  - Çağıran: L&P oturum sonu ve egzersiz bitişi (ya da günlük bir cron).
  - Girdi: kullanıcının son N kaydırması / cevabı, kelimelerin seviyeleri.
  - Çıktı: User.cefr'i bir adım oynatmak ya da dokunmamak. Kullanıcıya
    bildirilmez ("sessizce"); seviye testi sonucu ile karışmasın diye
    SeviyeTestiSonucu'na yazılmaz.
"""


def seviyeyi_sessizce_duzelt(user, olay=None):
    """Kanca: şimdilik hiçbir şey yapmaz, seviyeyi değiştirmediği için None döner."""
    return None
