# Devir notu — 20 Ekim 2026

Önceki sohbet uzadığı için yeni sohbete geçildi. Bu not o sohbetin sonundaki durumu özetler.
Ürünün tek doğruluk kaynağı yine `ozetler/2026-09-27_urun-raporu.md`; bu not yalnızca yayın ve
son işlerin durumunu tutar. Ayrıntılı tarih: arşivin "Değişiklik kaydı" (17 Ekim 13–18. maddeler).

## Yayın durumu

- **Site yayında:** https://www.learnvocab.com.tr (Veridyen, cPanel; kullanıcı `learnvoc`).
- **Kod:** sunucuda `~/LearnVocab`, dal `kelime-modeli`, GitHub `EfeSolax/LearnVocab`.
  Son commit `04f6e1e`. Her şey GitHub'a gönderildi; yerelde commit'lenmemiş iş yok.
- **Güncelleme akışı:** yerelde değiştir → test → commit → `git push` → sunucuda
  `cd ~/LearnVocab && git pull -q && touch tmp/restart.txt`
  (stil/statik değiştiyse araya `python manage.py collectstatic --noinput`).
  Sunucudaki dosyalar elle düzenlenmez (git pull çakışır); `.env` istisna.
- **Sunucu ortamı:** önce `source /home/learnvoc/virtualenv/LearnVocab/3.10/bin/activate && cd ~/LearnVocab`.
  `pip` dosyası çalışmıyor: `python -m pip install -r requirements.txt` kullanılır.
- **Veritabanı:** MySQL `learnvoc_learnvocab` (utf8mb4_general_ci: harf büyüklüğü ve aksan
  ayırt etmez; büyük/küçük harfle ayrılan kelime çifti eklenmemeli). Sürücü PyMySQL (mysqlclient
  sunucuda derlenmiyor). İçerik `veritabani yukle --zorla` ile yerelden aktarıldı; kullanıcı
  tabloları taşınmadı. Yönetici hesabı: `EfeSolax`.
- **Statik ve medya:** `~/learnvocab.com.tr/static -> ~/LearnVocab/staticfiles_root`,
  `~/learnvocab.com.tr/media -> ~/LearnVocab/media` (sembolik bağ). Medya (varsayılan profil
  fotoğrafı + 38.470 telaffuz MP3) git'te değil; yükleme adımları KOMUTLAR.txt'de.
- **SSL:** AutoSSL, learnvocab.com.tr ve www (11 Aralık 2026'ya kadar, kendisi yenilenir).
- **Cron:** 4 iş kurulu (yazilari_yeniden_dene 30 dk, bildirim_gonder_hatirlatma 15 dk,
  karsilasma_ozetle 04.00, clearsessions 04.15); loglar `~/logs/`.
- **Google Search Console:** URL ön eki mülkü doğrulandı (dosya `~/learnvocab.com.tr/google072d9de2b33e5c4f.html`,
  silinmemeli), site haritası gönderildi, ana sayfa için dizine ekleme istendi.

## Açık işler (Efe ile konuşulacak / bekleyen)

1. **iOS 17 Learn & Pass balonu:** `04f6e1e` ile düzeldi (Efe gerçek cihazda doğruladı, 20 Ekim).
2. **Alt menü ve sekmeler arası kaydırma** (`templates/base/_mobileTabBar.html`, stiller `defter.css` `lv-alt-*`; 20 Ekim):
   alt menü WhatsApp'taki gibi yüzen yuvarlak çubuk; açık sekmenin arkasındaki kapsül dokununca kayar (yeni sayfada
   kaldığı yerden tamamlar), parmakla kaydırırken parmağı izler. Kaydırma hataları (Efe'nin ekran kaydı): önizleme artık
   sayfa açılınca hazırlanır (2 dk sessionStorage önbelleği); yeni sayfa ikinci kez kayarak girmez (sona doğru "yeniden
   kayma" buydu); 900 ms sonra eski sayfayı geri getiren zamanlayıcı kalktı. **iPhone'da doğrulanmadı.**
3. **Gemini ücretli katman:** Google ödemesi `OR_BACR2_31` ile reddedildi (Yapı Kredi kartı;
   adres bankadakiyle eşitlendi, yine olmadı). Bankayla konuşulacak. O zamana kadar ücretsiz
   kota (model başına ~20/gün, 3 model), kota hatasında yedek modele geçiliyor. Ücretli olunca
   sunucu `.env`'de `GEMINI_MIN_SECONDS_BETWEEN_REQUESTS=0`.
4. **Chrome eklentisi:** Web Store incelemesinde (kimlik `ahddbpdmnbpjcnekkamakdepdhihcgng`).
   Sunucu `.env`'e `EKLENTI_KIMLIKLERI=<kimlik>` eklenmeli (eklendi mi doğrulanmadı).
   Onaylanınca `EKLENTI_ADRESI=<mağaza adresi>` + restart.
5. **Mobil uygulama:** PWA hazır; "uygulama olarak ekle" rehberi Yardım sayfasında (`/hakkinda/#uygulama`),
   ana sayfada yönlendirme kutusu var. Sonraki adım önerisi: Google Play (TWA, PWABuilder) +
   `/.well-known/assetlinks.json`. App Store sonra.
6. **Sunucuda eski dosyalar:** `~/env-eski` (eski şifreler, önce silinmeli), `~/LearnVocab-eski`,
   `~/eski-static`, `~/eski-media`, `~/htaccess-eski`. Site bir süre sorunsuz çalışınca silinebilir.
7. **Güvenlik:** Sohbete yazılan Gmail uygulama şifresi (`EMAIL_HOST_PASSWORD`) yenilenmeli; yenilendiği doğrulanmadı.
8. Önceki sohbetten Efe'ye sorulmuş, cevaplanmamış: akademik yazma prompt düzeltmelerinin uygulanması
   (`ozetler/akademik-yazma-prompt-taslagi.md`), olası ODTÜ alt gruplaması.

## Son oturumda yapılanlar (17–20 Ekim, hepsi yayında)

- Yardım sayfası son hâli: yeni ekran görüntüleri (tr/en/de × açık/koyu), görseller bir sol bir sağ;
  işaret konumları `araclar/yardim_goruntuleri.py` ile `LearnVocab/yardim_isaretler.json`'a yazılır.
- Learn & Pass: telefonda sayfa kaymaz (ekrana sabit), çapraz çekiş de sağa/sola sayılır, kaydırma
  eşiği 40 px (hızlı fiske 20 px), kartta kırmızı çizgi yok, balon içi kaymaz (sığmazsa örnek cümle,
  sonra kunduz gizlenir).
- Kelime satırları telefonda: seviye rozeti anlam satırında, düğmeye taşmaz.
- Seviye testi okuma soruları boş bırakılabilir.
- Hız: HTML GZip, Chrome'da bağlantıları önceden yükleme (çıkış/admin/sil hariç), Sözlük seviye/harf
  sekme sorgusu düzeltildi + 1 saat önbellek (canlıda sayfa başına ~0,5 sn kazanç).
- Kütüphane: arama (başlık + metin) ve 10'ar metinle sayfalama (aşağı kaydırınca yüklenir).
- Yazı değerlendirme: Gemini beklendikten sonra veritabanı bağlantısı yenilenir ("MySQL server has gone away").
- iPhone uygulama görünümünde alt menü ekranın alt çubuğunun üstünde (`viewport-fit=cover`).

## Çalışma notları

- Testler (Mac): `.venv/bin/python manage.py test --parallel 4 --noinput`; paralelde "cannot pickle
  traceback" çıkarsa `--parallel` olmadan çalıştırıp gerçek hatayı gör.
- Şablonda çok satırlı `{# #}` yorumu yasak (test yakalar). Betik içinde `class="` metni yazma
  (Tailwind testi sınıf sanıyor).
- Yeni Tailwind sınıfından sonra: `.venv/bin/tailwindcss -c tailwind.config.js -i static/css/tailwind-giris.css -o static/css/site.css --minify`.
- Yeni çeviri: `locale/{en,de}/LC_MESSAGES/django.po` sonuna ekle, `manage.py compilemessages -l en -l de`.
- Yerel deneme sunucusu: `.claude/launch.json` → `learnvocab-yardim` (8781, kopya veritabanı, örnek hesap).
