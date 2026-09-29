# LearnVocab

İngilizce kelime öğrenme platformu. Hazırlık öğrencileri ve İngilizce öğrenmeye çalışan herkes için tasarlandı.

Canlı sürüm: [learnvocab.com.tr](https://learnvocab.com.tr)

## Özellikler

Site dört bölümden oluşur (ayrıntı: `ozetler/2026-09-27_urun-raporu.md`):

- **Sözlük:** Kelime arama, anlamları, örnek cümleleri, eş dizimleri ve kelime ailesiyle birlikte kelime kartları. Kullanıcı beğendiği kelimeleri kendi listesine ekler (Listem).
- **Çalışmalar:**
  - **Learn & Pass (Öğren-Geç):** Kelimeyi gör, bildiğini düşünüyor musun karar ver, anlamını kontrol et. Hızlıdır ve her an bırakılabilir. Bilinmeyen kelimeler listeye eklenebilir.
  - **Egzersizler:** Kullanıcının listesinden Hızlı Egzersiz ve daha fazla soru tipi sunan Tempolu Egzersiz (yapım aşamasında).
- **Okumalar:** Seviyeye uygun okuma metinleri; okurken kelimeye dokunup anlamını görme (yapım aşamasında).
- **Yazma:** Yapay zekâ (Gemini) destekli metin değerlendirme: kullanıcı bir metin yazar, geri bildirim ve puan alır.

Ayrıca: kullanıcı profili, ayarlar ve veri dışa aktarma.

## Teknoloji

- **Backend:** Python 3.10+, Django 5.2
- **Frontend:** Tailwind CSS, server-side rendered templates
- **Veritabanı:** Production'da MySQL (`mysqlclient`), lokal'de SQLite varsayılanı
- **AI:** Google Gemini API (`google-generativeai`)
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

## Uygulamalar (Django apps)

| App           | Görev                                                     |
| ------------- | --------------------------------------------------------- |
| `users`       | Kullanıcı modeli (AbstractUser), kayıt/giriş/şifre işlemleri |
| `words`       | Kelime, anlam, kelime ailesi ve ifade modelleri; kullanıcı listesi |
| `learnpass`   | Learn & Pass (Öğren-Geç) ve Egzersizler sekmesi           |
| `readings`    | Okumalar                                                  |
| `texts`       | Yazma: kullanıcı metinleri ve Gemini ile değerlendirme    |
| `userprofile` | Profilim sayfası (kullanıcının listesi Sözlük › Listem'de) |
| `usersettings`| Kullanıcı ayarları, hesap silme/dışa aktarma              |
| `friends`, `comments` | Arayüzden kaldırıldı; kodları şimdilik duruyor    |

## Güvenlik notları

- `.env` dosyasını **asla** git'e commit etme.
- Production'da `DEBUG=False` olduğundan emin ol.
- Gemini API anahtarı veya Gmail App Password tehlikeye girerse hemen iptal edip yenisini üret.
- Tehlikeli işlemler (hesap silme, tüm kelimeleri silme) parolayla onaylanır.

## Lisans

Bu proje kişisel/eğitim amaçlıdır.
