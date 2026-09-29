# Zamanlanmış işler (cron) — Veridyen / cPanel

LearnVocab'ın iki düzenli işi var (rapor 9.1 ve 10):

| Komut | Ne yapar | Ne sıklıkla |
|---|---|---|
| `yazilari_yeniden_dene` | Gemini'nin cevap veremediği ("Henüz değerlendirilmedi") yazıları kotaya uyarak yeniden dener; arka planda değerlendirilen yazı için "Yazın değerlendirildi" bildirimi gider. Bir günden eski silinmiş yazıları da temizler. | 30 dakikada bir |
| `bildirim_gonder_hatirlatma` | Seri hatırlatmaları (rapor 18.9): kullanıcının **yerel** saatiyle 12.00'de "Günün kelimesi" ve 23.45'te seriyi kaçırma uyarısı. Günü tamamlayana ya da serisi 0 olana gitmez; aynı bildirim aynı gün iki kez gitmez. | **15 dakikada bir** |
| `clearsessions` | Süresi dolmuş oturum kayıtlarını siler (Django'nun kendi komutu). İsteğe bağlı. | Günde bir, gece |

## 1. Yolları bul

cPanel → **Setup Python App** ekranında uygulamanın üstünde şuna benzer bir satır yazar:

```
source /home/KULLANICI/virtualenv/PROJE_KLASORU/3.10/bin/activate && cd /home/KULLANICI/PROJE_KLASORU
```

Aşağıdaki satırlarda `KULLANICI`, `PROJE_KLASORU` ve `3.10` yerine oradaki değerleri yaz.
Sanal ortamın python'unu doğrudan çağırmak etkinleştirmekle aynı işi görür:
`/home/KULLANICI/virtualenv/PROJE_KLASORU/3.10/bin/python`.

`.env` dosyası `settings.py` tarafından proje klasöründen okunur; cron'da ayrıca ortam değişkeni vermek gerekmez.
Log klasörünü bir kez oluştur: `mkdir -p /home/KULLANICI/logs`

## 2. Cron satırları

cPanel → **Cron Jobs** → her satır için "Add New Cron Job" (saat alanlarını "Common Settings" yerine elle gir):

```cron
# Yazıları yeniden dene — 30 dakikada bir
*/30 * * * * cd /home/KULLANICI/PROJE_KLASORU && /home/KULLANICI/virtualenv/PROJE_KLASORU/3.10/bin/python manage.py yazilari_yeniden_dene >> /home/KULLANICI/logs/yazilari_yeniden_dene.log 2>&1

# Seri hatırlatmaları (yerel 12.00 ve 23.45) — 15 dakikada bir
*/15 * * * * cd /home/KULLANICI/PROJE_KLASORU && /home/KULLANICI/virtualenv/PROJE_KLASORU/3.10/bin/python manage.py bildirim_gonder_hatirlatma >> /home/KULLANICI/logs/hatirlatma.log 2>&1

# Eski oturumları temizle — her gece 04:15 (isteğe bağlı)
15 4 * * * cd /home/KULLANICI/PROJE_KLASORU && /home/KULLANICI/virtualenv/PROJE_KLASORU/3.10/bin/python manage.py clearsessions >> /home/KULLANICI/logs/clearsessions.log 2>&1
```

Etkinleştirmeyi tercih edersen aynı iş şöyle de yazılabilir:

```cron
*/30 * * * * source /home/KULLANICI/virtualenv/PROJE_KLASORU/3.10/bin/activate && cd /home/KULLANICI/PROJE_KLASORU && python manage.py yazilari_yeniden_dene >> /home/KULLANICI/logs/yazilari_yeniden_dene.log 2>&1
```

**Saat dilimi:** Cron sunucunun saatiyle çalışır. Sunucu UTC'deyse 19:00 Türkiye saati `0 16 * * *` olur
(`date` komutuyla sunucu saatini kontrol et). Komut kendi içinde Türkiye saatine bakar; yanlış saatte çalışırsa göndermez, zarar vermez.

**Kontrol:** Satırı eklemeden önce aynı komutu SSH/Terminal'de elle çalıştır; `--dry-run` ikisinde de var:

```bash
cd /home/KULLANICI/PROJE_KLASORU
/home/KULLANICI/virtualenv/PROJE_KLASORU/3.10/bin/python manage.py yazilari_yeniden_dene --dry-run
/home/KULLANICI/virtualenv/PROJE_KLASORU/3.10/bin/python manage.py bildirim_gonder_hatirlatma --dry-run
```

cPanel cron çıktısını e-postayla da gönderebilir; `>> ... 2>&1` yönlendirmesi olduğu için e-posta gelmez, çıktı log dosyasına gider.
Log dosyaları zamanla büyür; arada bir boşaltmak yeterli.

## 3. Canlıya çıkarken yapılacaklar

SSH/Terminal'de, sanal ortam etkinken ve proje klasöründeyken:

```bash
source /home/KULLANICI/virtualenv/PROJE_KLASORU/3.10/bin/activate
cd /home/KULLANICI/PROJE_KLASORU

pip install -r requirements.txt          # yeni: pywebpush (+ py-vapid, http-ece, aiohttp), pymupdf
python manage.py migrate                 # yeni tablolar: bildirimler (abonelikler, hatırlatma kayıtları) ve diğerleri
python manage.py collectstatic --noinput # yeni: static/pwa/ (ikonlar, service worker)
python manage.py vapid_anahtari_uret --eposta ADRESIN@ornek.com
touch tmp/restart.txt                    # Passenger'ı yeniden başlat (.env yeniden okunsun)
```

- `vapid_anahtari_uret` anahtarları **ekrana basmadan** doğrudan `.env`'e yazar. `.env`'de dolu bir anahtar varsa hiçbir şeye dokunmaz:
  anahtar değişirse kullanıcıların bütün bildirim abonelikleri geçersiz olur. Yerelde ve canlıda **ayrı** anahtar olması sorun değil;
  aynı anahtarı kullanmak da sorun değil. Anahtarı sohbete/mesaja yapıştırma.
- Anahtar yoksa bildirimler kendiliğinden kapalıdır (izin kartı görünmez, gönderim atlanır); site normal çalışır.
- Push yalnızca **HTTPS** üzerinde çalışır (yerelde `localhost` istisna). `/sw.js` ve `/manifest.webmanifest` Django tarafından kökten sunulur; Apache'de ayrıca bir şey yapmak gerekmez.
- Sonra cron satırlarını (bölüm 2) ekle.

## 4. Yerelde denemek

```bash
.venv/bin/python manage.py vapid_anahtari_uret --eposta ADRESIN@ornek.com   # yerel .env'e yazar
.venv/bin/python manage.py runserver
```

`http://localhost:8000` üzerinden bir L&P oturumu bitir → "Yarın hatırlatayım mı?" → **Evet**.
Sonra `.venv/bin/python manage.py bildirim_gonder_hatirlatma --saat-kontrolu-yok` bugün kaydırma yapmadıysan bildirimi gönderir
(yaptıysan göndermez — bu doğru davranış). Tarayıcının bildirimleri bu site için kapalıysa (sistem ayarları dahil) bildirim görünmez.
