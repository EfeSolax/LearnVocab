# LearnVocab

İngilizce kelime öğrenme platformu. Hazırlık öğrencileri ve İngilizce öğrenmeye çalışan herkes için tasarlandı.

Canlı sürüm: [learnvocab.com.tr](https://learnvocab.com.tr)

## Özellikler

- Kullanıcılar kendi kelimelerini ekleyebilir (İngilizce, Türkçe, V2/V3 fiil halleri, açıklama, örnek cümleler).
- Eklenen kelimeler için görünürlük seçenekleri: **Herkese Açık**, **Arkadaşlara Açık**, **Gizli**.
- 101–501 arası hazır kur seviyesi kelime listeleri.
- Quiz sistemi: çoktan seçmeli, eşleştirme, yazma ve karma. Algoritma, kullanıcının zayıf olduğu kelimeleri öncelikli sorar.
- Yapay zeka destekli (Gemini) metin değerlendirme: kullanıcı haftanın kelimeleriyle bir metin yazar, AI puanlar.
- Arkadaşlık sistemi (istek gönderme/kabul etme), arkadaşların kelime listesine erişim.
- Kullanıcı yorumları, like/dislike sistemi.
- Kullanıcı profili, ayarlar (günlük hedef, mail bildirimleri), veri dışa aktarma.

## Teknoloji

- **Backend:** Python 3.10+, Django 5.2
- **Frontend:** Tailwind CSS, server-side rendered templates
- **Veritabanı:** Production'da MySQL (`mysqlclient`), lokal'de SQLite varsayılanı
- **AI:** Google Gemini API (`google-generativeai`)
- **Deployment:** Apache + mod_wsgi (Passenger)

## Kurulum

1. Sanal ortam oluştur ve aktive et:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows'ta: venv\Scripts\activate
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

## Uygulamalar (Django apps)

| App           | Görev                                                     |
| ------------- | --------------------------------------------------------- |
| `users`       | Kullanıcı modeli (AbstractUser), kayıt/giriş/şifre işlemleri |
| `words`       | Kelime modeli, kelime listesi yönetimi                    |
| `quizzes`     | Quiz oluşturma, soru üretici, attempt takibi              |
| `texts`       | Kullanıcı metinleri ve Gemini ile değerlendirme           |
| `friends`     | Arkadaşlık istekleri ve listesi                           |
| `comments`    | Site yorumları, like/dislike                              |
| `userprofile` | Profil sayfası ve sekmeleri                               |
| `usersettings`| Kullanıcı ayarları, hesap silme/dışa aktarma              |

## Güvenlik notları

- `.env` dosyasını **asla** git'e commit etme.
- Production'da `DEBUG=False` olduğundan emin ol.
- Gemini API anahtarı veya Gmail App Password tehlikeye girerse hemen iptal edip yenisini üret.
- Tehlikeli işlemler (hesap silme, tüm kelimeleri silme) parolayla onaylanır.

## Lisans

Bu proje kişisel/eğitim amaçlıdır.
