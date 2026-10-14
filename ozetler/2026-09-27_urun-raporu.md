# LearnVocab — Ürün Durumu ve Kararlar

**Güncel durum:** 14 Ekim 2026 · **Hazırlayanlar:** Efe + Claude · **Test:** 1034 geçiyor (14 Ekim)

> **Sonraki Claude oturumları için:** Bu dosya ürünün **şu anki** hâlini ve **geçerli kararları** anlatır. Kısa tutulur (~170 satır); baştan sona oku.
> - **Tarihçe ve gerekçeler** `ozetler/arsiv/2026-09-27_urun-raporu-tam.md` dosyasında (eski tam rapor, "Değişiklik kaydı" dahil). Koddaki ve testlerdeki **"rapor 18.8", "rapor 4.2" gibi atıflar o dosyadaki numaralara bakar**; numaralar değiştirilmedi. Aşağıda her konunun sonunda `[arşiv 18.8]` gibi karşılığı yazılı.
> - Bu dosya ile arşiv çelişirse **bu dosya geçerlidir**.
> - **Yeni karar** alınınca: bu dosyada ilgili yeri güncelle (eskiyi silip yenisini yaz, "→ eskiden" notu bırakma) ve arşivin sonundaki "Değişiklik kaydı"na tarihli bir satır ekle.
> - "Vazgeçilen fikirler" (Bölüm 16) geri getirilmez. "Açık işler" (Bölüm 15) Efe ile konuşulmadan uygulanmaz.
> - **Veri kalitesi ölçümü** (14 Ekim): `veri/kalite_olcumu/2026-10-14-sonuc.md`.

---

## 1. Ürün ve ilkeler
- Türk hazırlık öğrencileri ve İngilizce öğrenen herkes için **kelime öğrenme kaynağı**; "bakıp gidilen" sözlük değil. Canlı: learnvocab.com.tr (şu an eski v1.0; yeni sürüm yayına alınmadı → Bölüm 15).
- Üç beceri: **bilgi** (Sözlük + Çalışmalar) · **pasif tekrar** (Okumalar) · **aktif üretim** (Yazılar).
- İlkeler: az seçenek, güçlü altyapı · net hiyerarşi · cesaretlendirici (yanlış cevap öğretir, puan kırmaz) · serbestlik (tek zorunlu akış yok) · en çok kullanılan yollar (Learn & Pass, Kısa Sınav, okurken dokun-anlamı-gör) kusursuz olmalı.
- **Gelir:** site ücretsiz, **premium kesinlikle yok**; ileride reklam olabilir (çalışma ekranlarına konmaz). [arşiv 18.25]
- **Maliyet ilkesi:** ek masraf çıkmasın; ücretli API önerilmez. İstisna: sözlük genişletme 5–10 $ (kullanıldı, ~8 $). Veri havuzu işleri (D2–D6) için LLM harcaması **yok**; Claude elle yazar. [arşiv 18.32, 18.35]

## 2. Gezinme
- Menü (bu sırayla): **Sözlük · Çalışmalar · Ana Sayfa · Okumalar · Yazılar**. Mobilde altta sabit sekme çubuğu, masaüstünde üstte; içerik tek sütun, ortada (`max-w-3xl`).
- Sağ üstte: **tema düğmesi** (açık ↔ koyu), **dil düğmesi**, **profil fotoğrafı** (→ Hesap → Ayarlar). Misafirde fotoğrafın yerinde "Giriş Yap". [arşiv 18.26]
- **Misafir kuralı:** giriş gerektiren öğe gösterilmez; bölümde tek davet bağlantısı olur. [arşiv 2.3, 18.3]
  - Ana Sayfa: tanıtım sayfası (defter teması). Sözlük: Keşfet, "giriş yap" daveti, "Listeme ekle" yok. Çalışmalar: yalnızca Learn & Pass (%60 B1 · %20 B2 · %20 C1), hiçbir şey kaydedilmez. Okumalar: yalnızca kütüphane. Yazılar: yalnızca diyalog.
- Adresler: `/sozluk/`, `/calismalar/`, `/okumalar/`, `/yazilar/` (İngilizce `/en/writings/`), `/profil/`, `/ayarlar/`, `/hakkinda/`, `/gizlilik/`. Türkçe öneksiz, `/en/…` önekli. Eski v1.0 adresleri 301 ile yeniye gider (`LearnVocab/eski_adresler.py`).

## 3. Ana Sayfa
- Girişli: tarih, selam, büyük **"Bugünün çalışmasına başla"** (Learn & Pass), **seri kutusu** (kapibara başı; dokununca açılır pencere), listedeki kelime sayısı (**tek sayısal gösterge**), günün kelimesi + günün ifadesi (yapışkan not), "Defterin her sitede yanında" (Chrome eklentisi), yardım bağlantısı.
- Seviye testi yapılmamışsa her sayfada davet penceresi çıkar (L&P ve egzersiz oturumlarında çıkmaz); "Seviyemi kendim seçeyim" daveti durdurur. [arşiv 18.27]

## 4. Sözlük
**Keşfet** (varsayılan) | **Listem** (yalnızca girişli). [arşiv 4, 5]
- **Boş hâl:** arama kutusu → **konulara göz at** (34 konu, renkli kutucuk; ilk 8, "daha fazla göster") → günün kelimesi → günün ifadesi → hazır listeler → "Kelimelere göz at" (seviye/harf).
- **Arama:** anlık öneri (`carpet · halı`); İngilizce tam eşleşme kalıcı adrese 301 (`/sozluk/aim/`), her tür ayrı kart (ilki açık); Türkçe sorgu kapalı kompakt kartlar; çekimli hâl → kök (`went` → go); yazım hatasında "Bunu mu demek istediniz?"; bulunamayanlar kaydedilir. [arşiv 4.2, 18.15]
- **Kelime kartı** (her yerde aynı bileşen; `words/kart.py`, `base/_kelimeKarti.html`): kelime, Türkçe tür etiketi (yalnızca Sözlük'te), CEFR, **US/UK ses düğmeleri** (Kokoro MP3), düzensiz fiillerde V2/V3, "Listeme ekle +" / "Listemde ✓". Her anlam açık; anlamda: Türkçe (kalın) · İngilizce açıklama · **1 örnek** ("Daha fazla örnek" kapalı) · **konu kutucuğu** · "Kalıplar" (kapalı; `depend on sb/sth` biçimi, altında "sb: birisi · sth: bir şey") · **anlama özel** Benzer / Daha basit / Zıt çipleri. En altta **Aile**. Örnek cümlede çift tıklama kelimeyi Sözlük'te arar. [arşiv 4.3, 18.4, 18.5, 18.39]
- **"Daha basit" kuralı:** hedef A1–B1 ve kaynaktan kesinlikle alt seviye; aksi hâlde bağ silinir. [arşiv 18.6]
- **Listem:** satır = kelime + numaralı Türkçe anlamlar + "Listemden çıkar" (onay yok, "Geri al" bildirimi); arama, filtre (En yeni/En eski/A→Z; Tümü/1 hafta/1 ay; **Zorlandıklarım**), toplu seçim. İstatistik/ilerleme/seviye filtresi **yok**. [arşiv 5]
- **Hazır listeler** (`/listeler/<ad>/`, 30 adet): **Bilkent** (5 seviye) · **ODTÜ** (101–502, span span, hafta hafta bölümlü) · **Speakout A0–A1** · **High Note 5** · **More to Read II · AWL** (kitabın kelime aileleriyle) · **Cambridge** (Pre A1 Starters, A1 Movers, A2 Key, B1 Preliminary) · **Phrasal Verbs** (715, seviye bölümlü). "Bu listeyle çalış" L&P'nin yeni kelime kaynağını listeye çevirir; **toplu "hepsini ekle" yok**. Sayfada bölüm düğmeleri (`?bolum=`) ve "Bu listede ara". Kurum adları kullanılır (kelime derlemesi telife konu değil — Efe). [arşiv 4.1, 13.3 D7]
- **Konu sayfası** `/sozluk/konu/<slug>/`: kolaydan zora 40'ar kelime, "Bu listede ara"; Google'a kapalı. Konular elle işaretli (2.964 anlam + 17 ifade); kelime hattı artık kategori yazmaz. [arşiv 18.39]
- **Anlam sırası:** çok anlamlı 4.077 kelime elle okundu, 321'inin sırası düzeltildi; 439 gereksiz anlam satırı birleştirildi (örnekler 5'ten fazla kalabilir). [arşiv 18.40]
- **Günün kelimesi/ifadesi:** kullanıcının seviyesinde, görmediği, sık, Google'a açık, zengin verili kelime (misafire herkese aynı). Kart gün boyu açık; **Biliyordum/Bilmiyordum** düğmeleri (fikir değiştirilebilir, L&P verisine yazılır). İfade: 149 "az bilinen" ifadelik döngü; ifadede bilme kaydı yok, yalnızca "Listeme ekle". [arşiv 18.8]

## 5. Çalışmalar
Sekmeler: **Learn & Pass** (varsayılan) | **Egzersizler** (misafirde sekme yok). [arşiv 6]

### Learn & Pass (L&P)
- Oturum 20 kart, dikkat dağıtıcısız (üst çubuk/alt menü gizli; tek çıkış ✕; küçük "Geri al"). Kart yalnızca kelime; **sağa = biliyorum, sola = bilmiyorum**. "Biliyorum" ise anlam açılır ve "Düşündüğün bu muydu?": sağ = **eminim** (`known`), sol = **yanılmışım** (`misjudged`). "Bilmiyorum" ise anlam gösterilir (`unknown`). Düğmeler ve ← → tuşları aynı işi yapar. Her karar anında kaydedilir. [arşiv 6.1, 18.1, 18.10, 18.11]
- Oturum sonunda "Bilmediğin N kelimeyi listene ekleyelim mi?"; yarım kalırsa sonraki girişte "geçen sefer" kartı. Açılışta "Nasıl oynanır?" kutusu. Kapibara balonda göz kırpar. Oran: ayarlardaki kaydırıcı, varsayılan %70 tekrar / %30 yeni (tekrar birikirse yeni oran düşer).
- **Yeni kelime seçimi:** girişlide %60 kendi seviyesi · %25 bir üst · %15 bir alt; kelime ağırlığı `(max(zipf,1,5)−1)²` (sık kelime sık çıkar); **nadir türler** (dog fiili gibi) yalnızca C1–C2 kullanıcıya girer; dilbilgisi türleri (zamir, belirleyici, yardımcı fiil, ünlem) yeni kelime havuzuna girmez. [arşiv 18.16, 18.36]
- **Tekrar kuralı (Efe'nin 1-3-7-21'i; FSRS yok):** `learnpass/tekrar.py`, birim `TEKRAR_BIRIMI_SAAT` = 24. Adaylar: zorlandıkları (son sonuç bilemedi) her zaman; bildikleri yalnızca aralıkları (1→3→7→21, sonra 21 günde bir) dolunca. **Listede olup hiç görülmemiş kelime en büyük öncelik.** Sıra: en eski son görülme → yüksek zorlanma oranı → rastgele. Bilinemezse basamak 0'a döner (sayaçlar silinmez). Egzersiz cevapları aynı kurala işler (yanlış her zaman sıfırlar). Günde en çok 15 yeni kelime. `is_learned`/`MASTERED` yok. [arşiv 18.2]
- **Seviye kendiliğinden düzelir** (`seviye/duzeltme.py`): seviye başına bilme oranı >%75 bitmiş, %35–75 o seviyede, <%35 alt; ağırlıklı ortalama; seviye başına ≥20, toplam ≥50 kelime; haftada en çok 1 basamak. [arşiv 18.27]

### Egzersizler
- **Kısa Sınav:** tam 10 soru, yalnızca anlam (TR↔EN karışık), yalnızca kullanıcının listesinden, ayarsız. **Deneme Sınavı:** 5/10/15/20 soru (ayardan), tip seçilebilir. [arşiv 6.2, 18.12]
- Tipler: kelime↔anlam · kelime↔İngilizce açıklama · eşleştirme · düzensiz fiil 2./3. hâl (~189; cut/put/hit 3 şıkla) · kelime biçimi · eş/zıt/daha basit (büyük renkli damga) · bağlaç/ifade (D2) · hafif fiilli eş dizim (D3). **Gramer kuralı anlatılmaz, tür etiketi gösterilmez**; yanlışta tek satır açıklama (kelime biçiminde tüm biçimler anlamlarıyla). Bitişte skor + "Yanlışları tekrar çöz · Yeni tur · Bitir". [arşiv 6.2, 18.28]
- Türkçe anlamlar ayarı kapalıysa Kısa Sınav açıklama sorar; Türkçe isteyen Deneme tipleri pasif olur.

## 6. Seviye testi (`seviye/`)
- **Kelime ekranları:** 1) 20 A1 + 20 A2 · 2) 20 B1 + 20 B2 · 3) 30 C1 + 10 "C2" (C2 yerine en zor C1'ler). Bir sonraki ekran yalnızca işaretlenen oran **%60'ı geçerse** açılır. Sahte kelime yok. Havuz 360 kelime (`seviye_kelimeleri_sec`).
- **Özet soruları** (en çok 3; hangi seviyeden sorulacağı ekran sonucuna göre) ve sonuç: doğru cevaplanan en yüksek seviye; doğru cevap kullanıcıya gösterilmez. Havuz **301 soru** (A1–C2, elle, `seviye_okuma_yukle`). [arşiv 18.27]
- "Seviyemi kendim seçeyim" kaçış yolu; Ayarlar'dan tekrarlanır. Kayıt formunda seviye/kur sorulmaz; belirsizse B1.

## 7. Okumalar
- **Kütüphane:** 45 metin: 40 **More to Read II** (ODTÜ kitabından; **izin henüz alınmadı**, → Bölüm 15) + 5 örnek (101–105). **Kendi metinlerim:** PDF ya da yapıştır; yalnızca sahibine özel; giriş gerekir. [arşiv 8, 18.24]
- Okuma ekranı: kelimeye dokununca **anında baloncuk** (kök, numaralı tüm anlamlar, phrasal verb algısı, "Listeme ekle +", yoksa "Henüz sözlüğümüzde yok" — kaydedilir). Yapay zekâyla bağlamdan anlam seçilmez. A−/A+ yazı boyutu. Uzun metin ~1.500 kelimelik bölümlere ayrılır.
- **Sınırlar:** kullanıcı başına 100 metin (en çok 15 PDF); PDF ≤ 400 sayfa / 50 MB (OCR yok, dosya saklanmaz); yapıştırma ≤ 150.000 karakter. Metin gövdesi **diskte** (`ozel_depo/`, sıkıştırılmış, web'den sunulmaz). Silinen metin 1 hafta çöpte kalır, geri alınabilir. Aynı anda en çok 2 PDF, kullanıcı başı saatte 20.
- Kelime sorgusu **API** olarak yazılı (`GET /api/kelime/`); Chrome eklentisi aynısını kullanır.

## 8. Yazılar
- **Serbest yazma** (girişli): 3–8 cümle, 3–5 "kullanmayı dene" kelimesi. **Gemini** (ücretsiz katman, yedek model `LearnVocab/gemini.py`) JSON döndürür: `puan` (5 üzerinden, yarım adım; pratikte 2–5), `iyi` (alıntı + neden), `hatalar` (`~~yanlış~~ → doğrusu · tek cümle neden`), `kullanilan_kelimeler`. "Geliştirilebilir" bölümü **yok**. Hatalı parçanın altı çizili. **Sertlik** ayarı: Nazik (≤3 hata) · Normal (≤6) · Titiz (≤10; noktalama/resmiyet dahil); puan bantları aynı. Geri bildirim arayüz dilinde. [arşiv 9, 18.22]
- Değerlendirilemeyen metin "Henüz değerlendirilmedi" etiketiyle kalır; cron `yazilari_yeniden_dene` (15 dk) yeniden dener. Günde 3 değerlendirme, site genelinde dakikada 4, aynı anda 4. Metin 20–1500 karakter. [arşiv 18.37]
- **Diyalogda doğru kelime:** 4–6 satırlık hazır diyalog, 1 boşluk + Türkçe ipucu; çekimli hâl kabul, tek harf hatasında "Neredeyse!"; "ilk harfi göster". **Önceden üretilmiş havuzdan** (D6); cevaplar Zorlandıklarım'a yazılmaz.

## 9. Seri (streak) [arşiv 18.9]
- Gün sayılır: **10 L&P kartı** ya da **10 egzersiz sorusu** (toplanmaz) ya da **1 geçerli metin** ya da **1 diyalog**. Okuma/listeye ekleme/günün kelimesi sayılmaz. Gün **kullanıcının yerel saatiyle 00.00'da** biter.
- **Geçerli metin:** ≥5 cümle ve ≥50 kelime, kelimelerin ≥%90'ı gerçek İngilizce, tekrar/anlamsız dizi yok, önceki metnin kopyası değil. Geçmezse değerlendirilir ama seriye sayılmaz.
- **Dondurma hakkı:** 1 ile başlar; art arda 5 gün → +1; en çok 3. Kaçırılan gün hak varsa otomatik dondurulur (seri sayısını artırmaz, ardışık sayacı sıfırlar).
- Çalışma ekranında ilerleme çubuğu 10. kart hizasında gri alev; gün tamamlanınca sarı-turuncuya döner. Seri kutusu: seri, dondurma hakkı, en uzun seri, takvim (tamamlanan sarı-turuncu · dondurulan mavi · diğerleri gri). Bozulunca "Yeni seri başlatmak için…" dili; "kaybettin" denmez.

## 10. Bildirimler ve PWA [arşiv 10, 18.29]
- Web Push (VAPID anahtarı `.env`'de yoksa hiçbir şey görünmez). Günde en çok 2: **12.00** (günün kelimesiyle) ve **23.45** (seri uyarısı; dondurma hakkı varsa "…1 hakkın kullanılacak"). Gün tamamlandıysa ya da seri 0 ise gitmez. Metinler hesap dilinde.
- **İzin ön ekranı** (kapibaralı): ≥3 bitmiş egzersiz oturumu **ve** ≥20 L&P kartı sonrası; "Şimdi değil" 7 gün; iPhone'da site ana ekrana eklenmediyse rehber. Ayarlar'dan cihaza özel aç/kapat.
- Cron (`bildirimler/CRON.md`): `bildirim_gonder_hatirlatma` 15 dk · `yazilari_yeniden_dene` 15 dk · `karsilasma_ozetle` her gece 04.00. Barındırma en sık 15 dk destekler.

## 11. Chrome eklentisi (yazıldı, **yayın bekliyor**) [arşiv 11]
- Herhangi sitede kelimeye **çift tıklayınca** anlam (bizim veritabanımızdan; Okumalar'daki baloncuk). "Listeme ekle" (girişliyse; ayrı giriş yok, site oturumu), "Oxford'da ara" (aynı sekme). Herkese açık; yalnızca adres başına dakikada 300. Kod `chrome-eklentisi/`, sunucu `readings/api.py`.
- Telefon: Android paylaş menüsü (PWA `share_target` → `/paylas/`). Chrome Web Store 5 $ (Efe öder). Sonra: TWA (25 $), Firefox, Safari (talep olursa).

## 12. Hesap, Ayarlar, dil, giriş, KVKK
- **Kayıt:** ad, soyad, e-posta, kullanıcı adı, tek şifre (≥8, büyük, küçük, rakam) + "Aydınlatma Metni'ni okudum". **Google ile giriş** (django-allauth; `.env`'de `GOOGLE_CLIENT_ID/SECRET`, yoksa düğme yok). [arşiv 18.21, 18.23]
- **Ayarlar** (`/ayarlar/`, kaydet düğmesi yok, değişiklik anında kaydedilir): Görünüm (Sistem/Açık/Koyu) · **Dil** + **Türkçe anlamlar** anahtarı · Seviye · Çalışma (L&P tekrar/yeni kaydırıcısı %10 adım, egzersiz soru sayısı 5/10/15/20, yazma sertliği, ses) · Bildirimler · E-posta · Verilerim · Tehlikeli bölge. [arşiv 18.26]
- **Diller:** yayında **tr + en** (Almanca 8 Ekim'de kapatıldı; `/de/` → 301; `locale/de/` duruyor, açmak için `YAYIN_DILLERI=tr,en,de`). es/fr sonra. Yalnızca arayüz çevrilir, kelime anlamları Türkçe. Otomatik yönlendirme yok (SEO). Çevirisi bitmemiş dil yayına alınmaz. [arşiv 18.22]
- **KVKK:** `/gizlilik/` (tr asıl, en çeviri), kayıtta okundu kaydı. **Hukukçuya okutulmadı**; açık sorular Bölüm 15'te. [arşiv 18.19]
- **Yardım ve hakkında** (`/hakkinda/`, `LearnVocab/yardim.py`): 9 rehber, telefon çerçeveli işaretli ekran görüntüleri (15 ekran × 2 tema × dil, WebP). [arşiv 18.33]
- **Admin istatistik** (`/admin/istatistik/`): yalnızca toplu sayı; 5'ten küçük gruplar gösterilmez. [arşiv 18.31]

## 13. Site geneli kurallar
1. Gramer etiketi yalnızca Sözlük kartında, Türkçe; L&P/egzersiz/açıklamada asla.
2. **Hassas ve müstehcen anlam/örnek yazılmaz** (`_HASSAS_*` filtreleri; kararsız olanlar `ozetler/hassas-anlamlar.txt`'de).
3. Uydurma kelime yok (seviye testi dahil). 4. Cesaretlendirici dil. 5. **Kelimenin ayrı sayfa tasarımı yok** (kart yerinde açılır); SEO için kalıcı **adres** var.
6. Giriş gerektiren öğe misafire gösterilmez. 7. Onay penceresi yerine "Geri al". 8. Yeni veri önce önbelleğe, `--dry-run`, sonra yazım; her partiyi gözden geçir.
9. Önemli bilgi küçük yazıyla yazılmaz; kök yazı 17 px. **Tema: Defter** (kareli kâğıt, mürekkep mavisi, sarı kalem; Fraunces/Source Serif/Inter/Caveat/Fredoka), koyu tema var. **Kapibara** (yetişkin, önden, iki ön dişi dışarıda) maskot. [arşiv 18.12, 18.33]
10. `<html lang>` seçili dile göre. Tailwind **Standalone CLI** ile yerelde derlenir (`site.css` depoda); Alpine 3.17.4 ve yazı tipleri siteden sunulur. [arşiv 18.17]

## 14. SEO ve adresler [arşiv 18.15]
- **İlke:** Google'da çıkmak çok değerli; **SEO bizi cezalandırmamalı**. Asıl adres `https://www.learnvocab.com.tr/` (`SITE_ADRESI`).
- **Beyaz liste** (`LearnVocab/seo.py` `DIZINE_ACIK`): listede olmayan her sayfa `noindex`. `robots.txt` yalnızca `/admin/` ve `/api/`'yi kapatır.
- **Kelime sayfası** `/sozluk/bank/` yalnızca `dizinde` açıksa Google'a görünür (kademeli dizine alma; kural `words/dizine_alma.py`, komut `dizine_ac`: Türkçe anlam + açıklama + ≥1 örnek + Zipf ≥ 2,3). **Açık: 2.691 kelime** (A1–B1 Oxford'lu 1. parti); sırada B2 Oxford → C1 Oxford → ifadeler → `learnvocab` etiketli kelimeler (elle denetimden sonra). Cambridge kaynaklı A1–B1 henüz açılmadı.
- `sitemap.xml` her dil adresini `hreflang` ile yazar; `?q=` aramaları `noindex`; göz atma sayfaları sayfalı.
- Henüz yok: Türkçe→İngilizce sayfalar (`/sozluk/tr/…`, 2. aşama).

## 15. Açık işler ve karar bekleyenler
**Yayın (yeni sürümün canlıya geçişi; "her şey bitince" — Efe) [arşiv 18.30 taslak kontrol listesi]**
- Taslak liste: yerel testler + `check --deploy` + yedek · veri MySQL'e taşıma (`dumpdata`/`loaddata`; v1.0 kullanıcı verisi önemsiz) · `git pull`, `pip install`, `migrate`, `collectstatic` · `media/telaffuz/` yükleme (sayı arttı, ~37 bin dosya (28.372 + 9.202); inode sınırı 400 bin) · `ozel_depo/` web kökü dışında · `.env` (`DEBUG=False`, `SITE_ADRESI`, VAPID, Gemini, Google) · `.htaccess` tek adım 301 · cron'lar · 50 MB yükleme sınırı · Search Console (Efe, DNS TXT) · geçiş günü bakım ekranı · sunucuda `YAYIN_DILLERI`'nde `de` yok.
- **Yayın kriterleri tanımsız:** liste uzadıkça "bitti" çizgisi kayıyor (14 Ekim eleştirisi). Claude'un önerisi (Efe onaylamadı): 8–10 maddelik kapalı bir kriter listesi yazıp geri kalanı yayın sonrasına bırakmak.
- Statik dosya önbelleği: `ManifestStaticFilesStorage` önerisi (Efe ile konuşulacak) [arşiv 18.30 10c].

**Hukuk / izin**
- **More to Read II (40 metin) izni:** Efe ODTÜ hazırlığıyla konuşacak; şu an kütüphanede, **Google'a açık ve site haritasında**. Claude'un önerisi (karar bekliyor): izin gelene kadar `noindex`. Reddedilirse: `ReadingText.objects.filter(source="More to Read II").delete()`.
- KVKK: yurt dışı aktarım dayanağı (standart sözleşme mi, açık rıza mı), duyuru e-postalarının varsayılan açık olması (ticari ileti/İYS), VERBİS; metin bir hukukçuya okutulmalı. [arşiv 18.19]

**Veri**
- **Kalite ölçümü (14 Ekim) bulguları** (`veri/kalite_olcumu/2026-10-14-sonuc.md`): 200 rastgele anlamda **%3 hata** (6), %4,5 zayıf; ölçüm bağımsız değil (aynı model ailesi). 16 işaretli anlam **düzeltilmedi**. **Yapısal bulgu:** `learnvocab` etiketli B1'in %22'si, B2'nin %34,5'i Zipf < 3,0 (Oxford'lu olanlarda ~%0); 3.755 kelime için seviye kararı (yükselt / "az kullanılan" işaretle / L&P'den çıkar) Efe'nin. "Yalnızca phrasal biçimde geçen fiil" (sum up, team up) örüntüsü taranmalı. Kalıp ve bağ hata oranı henüz ölçülmedi.
- **Kural taraması (14 Ekim, ücretsiz, `araclar/veri_kural_taramasi.py`, çıktı `veri/kalite_olcumu/kural-taramasi/`):** 10 kural; seviye (r01), yalnızca parçacıkla geçen fiil (r02), şablon örnek (r06), şiddet/hassas (r07) yararlı çıktı. Türkçe karşılık kalitesi kuralla bulunamaz (altın 16 bulgudan yalnızca 3'ü bağımsız yakalandı). **Uygulandı** (`words/duzeltmeler/d_2026_10_14b.py`, yedek `~/LearnVocab-yedekler/db.sqlite3.yedek-20261014-r02-r06-r07-oncesi`): 8 yinelenen fiil anlamı silindi (yedek `veri/kalite_olcumu/duzeltme/silinen-anlamlar.tsv`), 32 anlamın karşılığına parçacık etiketi yazıldı ("(off ile) savuşturmak"), 308 anlamda genel kalıp örnek yerine iyi örnek öne alındı, 2 şiddetli örnek değişti. **Açık:** etiketli 32+6 anlamın ayrı phrasal verb kaydına dönüştürülmesi (içerik yazma işi, Efe karar verecek); r07'de brain/drug fiilleri, shiv, sadist, prostitution, obscene, vulgar kararı Efe'nin.
- **Haiku 5.5 ön eleme (14 Ekim kalibrasyonu):** İstem 2 (`veri/kalite_olcumu/haiku/istem-2.md`) kapsamdaki hataların %80'ini yakaladı, %25 işaretledi; öneri: yüksek riskli katmanlarda (`learnvocab` 18.038 + phrasal 1.024 anlam) Haiku → işaretlenenleri Sonnet inceler. Henüz başlamadı. Opus tam taraması haftalık limitin ~%40'ı (Efe).
- Efe'nin incelemesi bekleyen dosyalar: `ozetler/zayif-baglar.tsv` (11.820 bağ), `zayif-kaliplar.tsv` (430), `hassas-anlamlar.txt` (kalsın / "kaba" / silinsin). **Eş dizimler (Collocation) henüz elle okunmadı.**
- Cambridge A1'e indirme: `learnvocab` etiketli 28 kelime A1 olurdu; Efe'ye soruldu, uygulanmadı.
- Sözlükte olmayanlar: ülke/milliyet adları (özel isim nasıl girecek?), High Note 5'in 478 deyimi + 187 birleşik sıfat (ifade olarak eklenebilir), ODTÜ/High Note/More to Read listelerinin phrasal verb'lerle yeniden bağlanması. İfade havuzu (295) büyütülecek. [arşiv 18.38]
- **Hazır listeyi topluca listeme ekleme** (Efe tekrar konuşmak istiyor): hepsini tek tıkla / sayfa sayfa / "bilmediklerimi ekle" / uyarılı. Konuşulana kadar uygulanmaz. Konu sayfalarının "Bu listeyle çalış"a bağlanması da sonra.
- D2 (bağlaç cümleleri), D3 (eş dizim çeldiricileri), D4 (kütüphane/okuma), D6 (diyaloglar): havuzlar **5'er örnekle** dolu, gerçek havuz yok. D8 hazır.
- Telaffuz: yeni kelimeler (phrasal, temel, birleşik, konu eksikleri) için `araclar/telaffuz_uret.py` yeniden çalıştırılmalı (11 Ekim'de başlatıldı; bitti mi doğrula).
- `Word.owner/visibility/isBaseWord` artık sadeleştirilebilir (kullanıcı kelime ekleyemiyor).

**Ürün / tasarım**
- Tanıtım videosu (her dil), logo, yardım ekran görüntülerinin her sürümde yenilenmesi [arşiv 18.33–18.34 sürüm listesi]. Kapibara hareketli hâlleri.
- 1-3-7-21 biriminin ayarı: birkaç hafta gerçek veri sonrası `EncounterLog` ile (istatistik ekranı). Seri, seviye düzeltme ve tekrar kuralı gerçek kullanıcıyla sınanmadı.
- Test: `words.test_gunun.test_listeye_eklenince_kapanir` paralel çalışırken kararsız olabiliyor (11 Ekim notu).
- Chrome eklentisi yayını (Web Store, `EKLENTI_ADRESI`).

## 16. Vazgeçilen fikirler (geri getirme) [arşiv 17]
Kelime yolculuğu / "öğrenildi" durumu · tek zorunlu günlük akış · L&P'de "biliyorum"u sınama · seviye testinde uydurma kelime · egzersizde her seferinde yeni/eski oranı sormak · egzersizde gramer kuralı/tür etiketi · her kelimeye ayrı sayfa tasarımı ("Tüm Kelimeler", filtre paneli) · kelime düzeyinde eş/zıt/basit · okurken yapay zekâyla tek anlam seçmek · hazır listede toplu "hepsini ekle" (**yeniden konuşulacak**, Bölüm 15) · Listem'de yolculuk/istatistik/seviye filtresi · 10 kriterli 100 puanlık yazma rubriği · "geliştirilebilir" bölümü · canlı diyalog üretimi · **FSRS** · ücretli üyelik · Almanca (şimdilik) · "günlük hedef" ayarı · kayıtta "kur" seçimi.

## 17. Veri: bugünkü durum (14 Ekim 2026)
| Öğe | Sayı |
|---|---|
| Kelime (`Word`, her tür ayrı; ortak sözlük) | **22.286** (phrasal verb 715) |
| Aile | 7.771 |
| Anlam | 26.384 (birleştirme ve 14 Ekim düzeltmeleri sonrası) |
| Örnek cümle | 119.069 |
| Eş dizim (`Collocation`) / kullanım kalıbı (`UsagePattern`) | 45.001 / 19.661 |
| İlişki (`WordRelation`; eş/zıt/basit anlama bağlı) | 40.545 (+ zayıf işaretli bağlar duruyor) |
| İfade | 295 (21 grup) |
| Hazır liste / okuma metni / konu | 30 / 45 / 34 |
| CEFR | A1 1.059 · A2 1.694 · B1 5.056 · B2 9.883 · C1 4.441 · C2 153 |
| CEFR kaynağı | oxford 5.597 · cambridge 577 · **learnvocab 16.112** |
| Google'a açık (`dizinde`) | 2.691 |

- **Modeller:** `Word` (text, pos, cefr, cefr_kaynak, siklik, nadir_tur, dizinde, slug, family, base_verb, v2/v3) · `Meaning` (meaning_tr, definition, sort_order, register, sentiment, cefr; → `ExampleSentence`, `Collocation`, `UsagePattern`, `Category` bağı) · `WordRelation` (anlama bağlı; `confused_with` kelime düzeyinde) · `WordForm` · `Expression`/`ExpressionGroup` · `UserWordLink`/`UserExpressionLink` · `FalseFriend` · `HazirListe`/`HazirListeKelimesi` (bölüm, aile).
- **Türler:** isim, fiil, sıfat, zarf, phrasal verb + dilbilgisi türleri (zamir, belirleyici, yardımcı fiil, ünlem; `words/0029`). Dilbilgisi kelimeleri (the, I, can, because…) ve 100 birleşik isim elle eklendi.
- **Kaynak ve harcama:** ham veri ~30 $ + genişletme ~8 $; sonraki bütün düzeltme ve eklemeler Claude'un elle okumasıyla (API yok). Seviyeler: Oxford 3000/5000 ve Cambridge sınav listeleriyle kalibre; `cefr_kaynak=learnvocab` olanlar yalnızca bizim etiketimiz.
- **Düzeltme kodları:** `words/duzeltmeler/d_YYYY_MM_DD.py` (idempotent; kararlar `veri/**` altındaki TSV/TXT dosyalarında). Yeniden çalıştırmak güvenli; önce **proje dışına yedek** (`~/LearnVocab-yedekler/`).

## 18. Teknik bağlam ve çalışma kuralları
- **Yığın:** Django 5.2 (şablonlar), Tailwind (yerel derleme), SQLite (yerel) / MySQL (canlı), Gemini (yalnızca yazı değerlendirme), Kokoro (önceden üretilmiş MP3), Apache + Passenger. Uygulamalar: `words, users, userprofile, usersettings, learnpass, egzersizler, readings, texts, seviye, seri, bildirimler` aktif; `comments`, `friends` kodda duruyor ama arayüzde yok.
- **Mac'te (Efe, güncel):** sanal ortam `.venv`.
  - Test: `.venv/bin/python manage.py test --parallel 4 --noinput`
  - Tailwind: komut `tailwind.config.js` başında; `LearnVocab.test_tailwind` şablona eklenen yeni sınıfı yakalar.
  - Sunucu: `.venv/bin/python manage.py runserver`
- **Claude VM'inde (eski kurulum):** `--settings=testayar`; `yazayar` = `$HOME/db-calisma.sqlite3` kopyası (bağlı klasörde SQLite'a yazma başarısız); kopyada çalış, sonra geri `cp`; bağlı klasörde dosya silinmez. CLAUDE.md bu kuralları taşır.
- **Veri hattı (yeni kelime):** `aile_uret` → `aile_birlestir` → `aile_doldur` (önce `--dry-run`); kararlar `kararlar.json`; ara depo `ara-depo-genisletme/` ve `ara-depo-tam` (proje dışı, `ARA_DEPO_DIZINI`). Hattın tuzağı: büyük-küçük harfe duyarlı kelime kontrolü (silinen kelime yeniden üretilebilir → `kopyalari_sil()`, `cikar`). Elle ekleme: `veri/**/*.jsonl` + `elle_kelime_yukle`.
- **Güvenlik:** API anahtarları `.env`'de, **sohbete yazılmaz**. Üretimde `DEBUG=False`, HSTS/güvenli çerez ayarları `settings.py`'de.
- **Yedek:** `db.sqlite3` git'te değil (`.gitignore`). Büyük veri işinden önce yedek **proje dışına** alınır. **Yedekler tek makinede**: Mac dışı kopya henüz yok (14 Ekim eleştirisi; Efe'nin işi).
- **Her yeni sürümden önce:** testler · Tailwind derle · yardım ekran görüntüleri (her dil/tema) · tanıtım videosu · çeviriler (`makemessages` + `compilemessages`, `fuzzy`/boş satır kalmasın) · bu dosyayı güncelle. [arşiv 18.34]
- **Barındırma:** Veridyen Senior; disk limitsiz, inode 400.000, MySQL ≤ 1 GB/veritabanı, cron ≥ 15 dk. Bu yüzden `EncounterLog` 90 gün tutulur, eskisi kişisiz `KarsilasmaOzeti`'ne çevrilir. [arşiv 18.32]
