# LearnVocab Chrome eklentisi (rapor 11)

Herhangi bir sitede İngilizce bir kelimeye **çift tıklayınca** anlamı LearnVocab
sözlüğünden gelir. Baloncuk Okumalar'dakinin aynısıdır: kök, numaralı anlamlar,
phrasal verb, "Listeme ekle +", "Henüz sözlüğümüzde yok". Altta "Oxford'da ara"
aynı sekmede Oxford Learner's Dictionaries'e gider. Baloncuğun dışına (kelimenin
kendisi dahil) tıklayınca, Esc'ye basınca ya da kelime ekrandan çıkınca kapanır.

| Dosya | Ne yapar |
|---|---|
| `manifest.json` | Manifest V3. Siteye erişim izni yalnızca `https://www.learnvocab.com.tr/*`. |
| `icerik.js` | Her sayfada çalışır; çift tıklanan kelimeyi bulur, baloncuğu kapalı Shadow DOM'da çizer. |
| `arkaplan.js` | Siteye giden bütün istekler (anlam, listeme ekle, giriş sayfası). |
| `pencere.html/js` | Araç çubuğu simgesine tıklayınca çıkan kısa bilgi. |
| `_locales/tr`, `_locales/en` | Yazılar; tarayıcının diline göre. |

**Giriş:** ayrı bir giriş yok. Kullanıcı sitede girişliyse arka plan betiği
oturum çerezini gönderir. Değilse "Giriş yap, listene ekle" sitenin giriş
sayfasını açar.

**Sunucu tarafı:** `GET /api/kelime/` (sınır: adres başına dakikada 300, günlük
ya da saatlik sınır yok) ve `POST/DELETE /api/eklenti/listem/<id>/`
(`readings/api.py`). Ekleme ucu yalnızca `EKLENTI_KIMLIKLERI`'ndeki eklentiden
gelen isteği kabul eder.

## Yerelde denemek
1. `.venv/bin/python araclar/eklenti_paketle.py --yerel` → `tmp/eklenti-yerel/`
   (yerel sunucuya, `http://localhost:8765`, bağlanan kopya; kaynak dosyalar değişmez).
2. Chrome → `chrome://extensions` → sağ üstte "Geliştirici modu" → "Paketlenmemiş
   öğe yükle" → `tmp/eklenti-yerel`.
3. Kartta görünen kimliği (32 harf) yerel `.env`'e yaz: `EKLENTI_KIMLIKLERI=<kimlik>`,
   sunucuyu yeniden başlat. Bu olmadan "Listeme ekle" 403 alır; anlamlar yine gelir.

## Yayına göndermek
1. Önce sunucu kodu yayına alınır (ekleme ucu ve `girisli` alanı yoksa "+" çalışmaz).
2. Paket: `.venv/bin/python araclar/eklenti_paketle.py` → `tmp/learnvocab-eklenti-<sürüm>.zip`.
3. https://chrome.google.com/webstore/devconsole → geliştirici hesabı (bir kerelik 5 $)
   → "Yeni öğe" → zip'i yükle.
4. Mağaza sayfası: kategori "Eğitim", dil Türkçe; en az bir ekran görüntüsü
   (1280×800); 128 px simge paketin içinde.
5. "Gizlilik" sekmesi:
   - Tek amaç: "Sayfadaki İngilizce bir kelimenin Türkçe anlamını göstermek ve kullanıcının LearnVocab listesine eklemek."
   - Siteye erişim izni (`learnvocab.com.tr`): anlamı sözlükten almak ve listeye eklemek için.
   - Bütün sitelerde çalışan içerik betiği: kullanıcının çift tıkladığı kelimeyi bulmak için. Sayfa okunmaz, kaydedilmez.
   - Toplanan veri: "Web sitesi içeriği" (yalnızca çift tıklanan kelime ve yanındaki birkaç kelime). Satılmaz, başka amaçla kullanılmaz.
   - Gizlilik politikası: `https://www.learnvocab.com.tr/gizlilik/`
6. Yüklemeden sonra öğe kimliği görünür. Sunucunun `.env`'ine
   `EKLENTI_KIMLIKLERI=<kimlik>` yazılır, uygulama yeniden başlatılır.
7. Onaylanınca mağaza adresi `.env`'e `EKLENTI_ADRESI=<adres>` olarak yazılır; ana
   sayfadaki "Chrome Web Store'da çok yakında" yazısı "Chrome'a ekle" düğmesine döner.

Chrome kurulumda "tüm sitelerdeki verilerinizi okuyabilir" uyarısı gösterir: çift
tıklamayı her sitede yakalamak için gerekiyor. İnceleme bu yüzden birkaç gün sürebilir.

Yeni sürümde `manifest.json`'daki `version` artırılır.
