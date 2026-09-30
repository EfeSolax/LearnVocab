# LearnVocab

İngilizce kelime öğrenme platformu. Hazırlık öğrencileri ve İngilizce öğrenmeye çalışan herkes için tasarlandı.

Canlı sürüm: [www.learnvocab.com.tr](https://www.learnvocab.com.tr)

## Özellikler

Menü: Sözlük · Çalışmalar · Ana Sayfa · Okumalar · Yazılar. Ürünün tek doğruluk kaynağı: `ozetler/2026-09-27_urun-raporu.md`.

- **Sözlük** (`/sozluk/`): arama, her kelimenin kalıcı sayfası (`/sozluk/bank/`), kelime kartları (anlam, örnek, eş dizim, aile, US/UK telaffuz), göz atma (`/sozluk/seviye/b1/`, `/sozluk/harf/a/`), hazır listeler, Listem.
- **Çalışmalar** (`/calismalar/`): Learn & Pass (1·3·7·21 günlük tekrar kuralı) ve Egzersizler (Hızlı, Tempolu).
- **Okumalar** (`/okumalar/`): kütüphane ve kendi metinlerin (PDF/yapıştır); kelimeye dokununca anlam.
- **Yazılar** (`/yazilar/`): Gemini ile değerlendirilen serbest yazma ve diyalogda doğru kelime.
- **Ana Sayfa:** seri (streak), günün kelimesi ve ifadesi.
- **Seviye testi** (`/seviye-testi/`), **Hesap** (`/profil/`) ve **Ayarlar** (`/ayarlar/`), Web Push bildirimleri, admin istatistik ekranı (`/admin/istatistik/`).

## Teknoloji

- **Backend:** Python 3.10+, Django 5.2
- **Frontend:** Tailwind CSS, server-side rendered templates
- **Veritabanı:** Production'da MySQL (`mysqlclient`), lokal'de SQLite varsayılanı
- **AI:** Google Gemini API (`google-genai`) — yalnızca yazı değerlendirme
- **Telaffuz:** önceden üretilmiş MP3 (açık kaynak Kokoro, `araclar/telaffuz_uret.py`)
- **Deployment:** Apache + mod_wsgi (Passenger)

## Kurulum

1. Sanal ortam oluştur ve aktive et:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows'ta: .venv\Scripts\activate
   ```

2. Bağımlılıkları yükle:

   ```bash
   pip install -r requirements.txt
   ```

3. `.env.example` dosyasını `.env` olarak kopyala ve değerleri doldur:

   ```bash
   cp .env.example .env
   ```

4. Veritabanı migration'larını uygula:

   ```bash
   python manage.py migrate
   ```

5. Süper kullanıcı oluştur:

   ```bash
   python manage.py createsuperuser
   ```

6. Sunucuyu başlat:

   ```bash
   python manage.py runserver
   ```

7. Testler:

   ```bash
   python manage.py test --parallel 4 --noinput
   ```

## Sık kullanılan komutlar

| Komut | Ne yapar |
|---|---|
| `dizine_ac` | Kelime sayfalarını partiler hâlinde Google'a açar (rapor 18.15) |
| `elle_kelime_yukle` | Elle yazılmış kelimeleri (JSONL) sözlüğe ekler |
| `seviye_okuma_yukle` | Seviye testi özet sorularını yükler (`seviye/havuz/`) |
| `baglac_havuzu_yukle`, `esdizim_celdiricileri`, `diyalog_yukle`, `kutuphane_yukle`, `hazir_liste_yukle` | Veri havuzlarını yükler (`veri/ornek/`) |
| `ifade_bilinirligi` | İfadeleri yaygın / az bilinen olarak işaretler |
| `karsilasma_ozetle` | 90 günden eski karşılaşma kayıtlarını özetler (gece cron'u) |
| `bildirim_gonder_hatirlatma`, `yazilari_yeniden_dene` | Cron işleri (`bildirimler/CRON.md`) |

## Uygulamalar (Django apps)

| App           | Görev |
| ------------- | ----- |
| `users`       | Kullanıcı modeli, kayıt/giriş/şifre, seviye (`users/seviye.py`) |
| `words`       | Sözlük: kelime, anlam, aile, ifade; arama, kalıcı adresler, günün kelimesi, Listem, hazır listeler |
| `learnpass`   | Learn & Pass ve tekrar kuralı (`learnpass/tekrar.py`) |
| `egzersizler` | Hızlı ve Tempolu Egzersiz |
| `readings`    | Okumalar; kendi metinler diskte sıkıştırılmış (`readings/depo.py`) |
| `texts`       | Yazılar: serbest yazma (Gemini) ve diyalog |
| `seviye`      | Seviye testi ve seviyenin kendiliğinden düzelmesi |
| `seri`        | Seri (streak) |
| `bildirimler` | Web Push, PWA, bildirim izni ön ekranı |
| `userprofile` | Hesap sayfası |
| `usersettings`| Ayarlar, dışa aktarma, hesap silme |
| `friends`, `comments` | Arayüzden kaldırıldı; kodları şimdilik duruyor |

## Güvenlik notları

- `.env` dosyasını **asla** git'e commit etme.
- Production'da `DEBUG=False` olduğundan emin ol.
- Gemini API anahtarı veya Gmail App Password tehlikeye girerse hemen iptal edip yenisini üret.
- Tehlikeli işlemler (hesap silme, tüm kelimeleri silme) parolayla onaylanır.

## Lisans

Bu proje kişisel/eğitim amaçlıdır.
