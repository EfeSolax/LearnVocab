# LearnVocab — Ürün ve Tasarım Raporu (v1)

**Tarih:** 27 Eylül 2026
**Hazırlayanlar:** Efe + Claude
**Durum:** Kararlar kesinleşti. Uygulamaya bu rapora göre başlanacak.

> **Sonraki Claude oturumları için:** Bu belge ürünün TEK doğruluk kaynağıdır. İşe başlamadan önce baştan sona oku.
> - Kararların nasıl alındığını görmek istersen tarihçe `ozetler/2026-09-26_urun-kararlari.md` dosyasında. O dosyadaki eski notlar bu raporla çelişirse **bu rapor geçerlidir**.
> - Bölüm 17'deki "Vazgeçilen fikirler"i geri getirme.
> - Bölüm 16'daki konular Efe ile konuşulmadan uygulanmaz.
> - Yeni bir karar alındığında bu raporu güncelle ve değişikliği en alttaki "Değişiklik kaydı"na yaz.

---

## İçindekiler
1. Ürün özeti ve ilkeler
2. Bilgi mimarisi (menü, giriş yapmamış ziyaretçi, mobil/masaüstü)
3. Ana Sayfa
4. Sözlük (Keşfet, arama, kelime kartı)
5. Listem
6. Çalışmalar (Learn & Pass, Egzersizler)
7. Seviye testi
8. Okumalar
9. Yazma
10. Bildirimler
11. Chrome eklentisi (v1 sonrası)
12. Site geneli kurallar
13. Veri: mevcut durum ve yapılacak veri işleri
14. Teknik bağlam ve çalışma kuralları
15. Uygulama planı
16. Sonra konuşulacaklar ve varsayımlar
17. Vazgeçilen fikirler

---

## 1. Ürün özeti ve ilkeler

**Ne:**
- Türk üniversite hazırlık öğrencileri ve İngilizce öğrenen herkes için bir **kelime öğrenme kaynağı**.
- "Bakıp gidilen" bir sözlük değil.
- Canlı adres: learnvocab.com.tr

**Üç beceri, üç bölüm:**
| Beceri | Bölüm |
|---|---|
| Bilgi: kelimeyi tanımak ve hatırlamak | Sözlük + Çalışmalar |
| Pasif tekrar: kelimeyi bağlamda görmek | Okumalar |
| Aktif üretim: kelimeyi kullanmak | Yazma |

**Tasarım ilkeleri:**
- **Az seçenek, güçlü altyapı.** Kullanıcı ekranda az karar verir; kalite arka planda.
- **Net görsel hiyerarşi.** En önemli şey en büyük ve en üstte, detay bir dokunuş uzakta.
- **Cesaretlendirici.** Hiçbir ekran cezalandırıcı hissettirmez. Yanlış cevap öğretir, puan kırmaz.
- **Serbestlik.** Tek zorunlu akış yok. Bütün bölümler her zaman açık, isteyen istediği kadar çalışır. Ana Sayfa bir merkezdir, kapı değildir.
- **Çoğu kullanıcı özelliklerin çoğunu kullanmaz.** Bu yüzden en çok kullanılacak yollar (Learn & Pass, Hızlı Egzersiz, okurken dokun-anlamını-gör) kusursuz olmalı.

---

## 2. Bilgi mimarisi

### 2.1 Menü
Beş bölüm, bu sırayla:

```
Sözlük · Çalışmalar · Ana Sayfa · Okumalar · Yazma
```

- **Ana Sayfa** menünün ortasındadır.
- Eski "Metinler" bölümünün yeni adı **Yazma**.
- "Hakkında" menüde yer almaz. Yardım bağlantısı Ana Sayfa'dadır.
- Ayarlar sağ üstteki dişli simgesindedir.

### 2.2 Mobil ve masaüstü
- **Mobil:** menü ekranın altında sabit bir sekme çubuğudur.
- **Masaüstü:** aynı menü üste taşınır. Geri kalan her şey mobil ile aynıdır: aynı kartlar, aynı sıra, aynı bileşenler. Masaüstü için ayrı düzen tasarlanmaz, içerik ortada makul bir genişlikte durur.

### 2.3 Giriş yapmamış ziyaretçi
| Bölüm | Giriş yapmamış ziyaretçi ne görür |
|---|---|
| Sözlük | Yalnızca **Keşfet**: arama, kartlar, günün kelimesi/ifadesi, hazır listeler. **Listem sekmesi yoktur.** |
| Çalışmalar › Learn & Pass | **Açık.** Yalnızca kaydırma: hiçbir şey kaydedilmez ve listeye eklenmez. |
| Çalışmalar › Egzersizler | Kapalı. Tıklanınca giriş yönlendirmesi yapılır. |
| Okumalar | **Açık**, yalnızca varsayılan (kütüphane) metinler. "PDF yükle" düğmesi görünür; basılınca "Önce giriş yapmalısın" denip giriş sayfasına yönlendirilir. |
| Yazma | Kapalı. Tıklanınca giriş yönlendirmesi yapılır. |

- **Genel kural:** Giriş gerektiren düğmeler gizlenmez; basılınca kısa bir açıklamayla girişe yönlendirir. Bu, "+ Listeme ekle" düğmeleri için de geçerlidir.
- **Varsayım:** Giriş yapmamış ziyaretçinin seviyesi bilinmediği için L&P ve günün kelimesi B1 civarından gelir. L&P'de üstte küçük bir "seviyeni seç" seçeneği bulunur; seçim kaydedilmez.

---

## 3. Ana Sayfa (giriş yapmış kullanıcı)

- **Seri (streak):** yeri ayrılır. Nasıl sayılacağı **sonra konuşulacak** (bkz. Bölüm 16).
- **Listemdeki kelime sayısı:** tek sayısal gösterge budur. "Öğrenilen kelime" kavramı yoktur (bkz. Bölüm 17).
- **"Bugünün çalışmasına başla":** büyük düğme, Learn & Pass'e gider.
- **Günün kelimesi ve günün ifadesi:** Sözlük'teki kartların küçük hâli. Tıklanınca Sözlük'te ilgili kart açılır; içerik iki ayrı yerde tutulmaz.
- **Yardım bağlantısı:** içeriği en son yazılacak.

---

## 4. Sözlük

**Zihinsel model:** Sözlük, kelimelerin durduğu yerdir (ara, göz at, topla). Çalışmalar ise kelimelerle bir şey yapılan yerdir.

Üstte iki sekme vardır: **Keşfet | Listem**. Listem yalnızca giriş yapmış kullanıcılara görünür.

### 4.1 Keşfet: boş hâl (arama yapılmamışken)
```
┌──────────────────────────────┐
│ [ Keşfet ] |   Listem        │
│ ┌──────────────────────── 🔍┐│
│ │ İngilizce veya Türkçe ara  ││
│ └───────────────────────────┘│
│ ┌ Günün Kelimesi ───────────┐│
│ │ …                         ││
│ └───────────────────────────┘│
│ ┌ Günün İfadesi ────────────┐│
│ │ …                         ││
│ └───────────────────────────┘│
│ Hazır Listeler               │
│  › ODTÜ 101                  │
│  › Cambridge B2 …            │
└──────────────────────────────┘
```
- **Günün kelimesi kişiye özeldir**, kullanıcının seviyesine göre seçilir.
- **Hazır listeler:** ODTÜ hazırlık (101…), Bilkent (upp-int…), Cambridge (B2…) vb.
  - Kurum adları kullanılabilir; kelime derlemeleri telife konu değildir (Efe'nin kararı).
  - Liste sayfasında **"Bu listeyle çalış"** düğmesi vardır. Basılınca L&P'nin yeni kelime kaynağı seviye yerine bu liste olur. "Bilmiyorum" denen kelimeler Listem'e girer.
  - **Listenin hepsini toplu ekleme yoktur**; 800 kelimeyle kullanıcıyı boğmayız.

### 4.2 Arama
- **Anlık öneri kutusu (autocomplete):**
  - Kullanıcı yazarken altta öneri satırları açılır: `carpet · halı`, `career · kariyer`.
  - Satıra dokununca doğrudan o kelimenin kartları gelir. Böylece kullanıcı kelimeyi sonuna kadar yazmak zorunda kalmaz ve aranan kelimenin tam olarak istenen kelime olduğu garanti edilir.
- **İngilizce tam eşleşme ("aim"):**
  - Önce o kelimenin **her türü için ayrı kart** gelir (aim · isim, aim · fiil). Bu, veritabanındaki `Word` yapısına birebir uyar: her tür ayrı bir kayıttır.
  - **İlk kart açık** gelir. Diğerleri kapalıdır ve tek satır görünür: `aim · fiil · hedeflemek · B1 · [+]`.
  - Kartların altında **"Diğer sonuçlar"** listesi bulunur, en fazla ~8 satır. Her satır: `carpet · isim · halı · B1`.
    - Önce bu harflerle başlayan kelimeler gelir, yaygından nadire (CEFR'e göre). Ardından içinde bu kelime geçen ifadeler.
    - Satıra dokununca o kelimenin kartları açılır.
- **Türkçe sorgu ("bitir"):**
  - Bu Türkçe anlama sahip İngilizce kelimeler **kapalı kompakt kartlar** olarak gelir: end, finish, complete, terminate…
  - Sıra yaygından nadiredir.
  - Her kartta kelime, seviye, eşleşen Türkçe anlam (vurgulu), tek satırlık tanım ve "+" bulunur. Dokununca tam kart açılır.
- **Bulunamayan arama, sırayla şu adımlar denenir:**
  1. **Çekimli hâl → kök:** `went` → **go** kartı, üstte "went, go'nun geçmiş hâli". `children` → **child** kartı. Veri: `WordForm`.
  2. **Yazım hatası:** `recieve` → "Bunu mu demek istediniz?" altında 3–5 tek satırlık öneri. 16 bin kelimede benzerlik araması yeterince hızlıdır.
  3. **Hiçbir şey yoksa** (`gskjengkwng`): "Henüz sözlüğümüzde yok."
  - Bulunamayan aramalar **kaydedilir**. Hangi kelimelerin ekleneceğine bu kayıttan karar verilir.
- **Paylaşılabilir adres:** Arama sonucu `/sozluk?q=aim` gibi bir adreste durur. Hem paylaşılabilir, hem Google tarafından görülebilir (SEO).

### 4.3 Kelime kartı (en önemli bileşen)
Aynı bileşen **her yerde** kullanılır: Keşfet, Listem, günün kelimesi. **Hiçbir kelimenin ayrı bir sayfası yoktur.** Kart bulunduğu yerde açılır ve kapanır.

```
┌───────────────────────────────────────────┐
│ aim                       [Listeme ekle +]│
│ isim                                  B1  │
│───────────────────────────────────────────│
│ 1. amaç, hedef                            │
│    the purpose of doing sth, what sb is   │
│    trying to achieve                      │
│    "Our main aim is to reduce costs."     │
│    › Daha fazla örnek    › Kalıplar       │
│    Benzer: goal · purpose                 │
│    Daha basit: goal                       │
│───────────────────────────────────────────│  ← anlamlar arası ince çizgi (hr)
│ 2. nişan                                  │
│    …                                      │
│    › Daha fazla örnek    › Kalıplar       │
│    Benzer: target                         │
│═══════════════════════════════════════════│
│ Aile: aimless · aimlessly                 │  ← see also
└───────────────────────────────────────────┘
```

**Kural listesi:**
- **Başlık:**
  - Solda kelime, sağda "Listeme ekle +" (listedeyse "Listemde ✓").
  - Altında **Türkçe tür etiketi** (isim, fiil, sıfat, zarf) küçük ve gri yazılır, sağında seviye rozeti durur.
- **Düzensiz fiiller:** Kelimenin yanında gri, küçük yazıyla V2/V3 gösterilir: **go** · *went · gone*. Düzenli fiillerde gösterilmez.
- **Anlamların hepsi açık** gelir ve aralarında ince çizgi olur. Ortalama anlam sayısı 1,2 olduğundan kartlar genelde kısadır.
- **Her anlam bloğunda** (verideki `Meaning`'e bağlı):
  1. Türkçe anlam (kalın)
  2. İngilizce açıklama (gri)
  3. **1 örnek cümle**. Diğerleri "› Daha fazla örnek" altında kapalıdır.
  4. **"› Kalıplar"** (kapalı): collocation'lar ve kalıplar birlikte, her biri Türkçe anlamı ve örneğiyle.
  5. **O anlama özel** eş, zıt ve basit anlamlılar çip satırları olarak: `Benzer: … · Daha basit: … · Zıt: …`
     - Her satırda en fazla 3–4 çip olur. Boş satır hiç gösterilmez.
     - Çipe dokununca o kelimenin kartı açılır.
- **Kartın en altında, bir kez:** **Aile** (see also), yani aynı kelime ailesindeki diğer kelimeler.
- **Eş, zıt ve basit anlamlılar anlama özeldir, kelimeye değil.** Örneğin "bank" için "shore" yalnızca "nehir kıyısı" anlamının altında görünür. Bu kesin bir karardır (bkz. Bölüm 13.3, veri işi D1).

---

## 5. Listem

**Amaç:** Kullanıcının "+" ile eklediği kelimelerin cep defteri. **Aşırı basit tutulur.**

```
┌──────────────────────────────────────┐
│   Keşfet   | [ Listem ]              │
│ ┌──────────────────────── 🔍┐ [Filtre]│
│ │ Listende ara               │ [Seç]  │
│ └───────────────────────────┘        │
│ aim                     [Listemden çıkar]│
│   1. amaç, hedef                     │
│   2. nişan                           │
│ ──────────────────────────────────── │
│ decide                  [Listemden çıkar]│
│   1. karar vermek                    │
└──────────────────────────────────────┘
```
- **Satırlar:** Kelime, altında numaralı Türkçe anlamları, yanında "Listemden çıkar". **Başka hiçbir şey yoktur**: istatistik, durum ya da ilerleme gösterilmez.
- **Dokununca** kelime yerinde açılır ve Sözlük'teki kartın aynısı görünür (aynı bileşen).
- **Sıralama:** varsayılan olarak **en son eklenen en üstte**.
- **Aynı kelimenin iki türü eklendiyse** iki ayrı satır olur, küçük gri tür etiketiyle (aim · isim / aim · fiil).
- **Listemden çıkar:** Onay penceresi açılmaz. Birkaç saniyelik **"Geri al"** bildirimi çıkar.
- **Boş liste:** "Listen boş. Sözlük'te + ile ya da Learn & Pass'te kelime ekleyebilirsin."
- **Arama kutusu ve anlık öneri** yalnızca listedeki kelimelerden sonuç getirir. İngilizce ile de, Türkçe anlamla da aranabilir ("hedef" → aim).
- **Filtre düğmesi** (tek düğme, açılınca üç satır):
  - Sırala: **En yeni** (varsayılan) · En eski · A→Z
  - Zaman: Tümü · Son 1 hafta · Son 1 ay
  - **Zorlandıklarım:** L&P'de "bilmiyorum" dediği ya da egzersizde yanlış yaptığı kelimeler.
  - Seviye filtresi **yoktur**.
- **Toplu işlem ("Seç" düğmesi):**
  - Satırlarda onay kutuları belirir. Üstte çubuk: `N seçili · Tümünü seç · Çıkar · İptal`.
  - "Tümünü seç" **o anki filtreye** uygulanır. Örnek: Son 1 hafta → Tümünü seç → Çıkar.
  - Toplu çıkarmada da "12 kelime çıkarıldı · Geri al" bildirimi çıkar.
  - Sonraki sürüm için: seçilenlerle **"Bunlarla çalış"** (Hızlı Egzersiz başlatır).

---

## 6. Çalışmalar

Üstte iki sekme: **Learn & Pass** (varsayılan açılan) | **Egzersizler**.

### 6.1 Learn & Pass (L&P): ürünün kalbi
**Neden değerli:**
- Hızlıdır ve her an bırakılabilir.
- Hatırlatır, yeni kelime keşfettirir.
- "Biliyorum sanıyordum" ile "gerçekten biliyorum" arasındaki farkı gösterir.

**Açılış ekranı:**
- İstatistik şeridi. İçeriği tekrar algoritması konuşulunca netleşecek; seri de burada görünür.
- Kısa slogan ve büyük **"Hemen Başla"** düğmesi.
- Teşvik edici kısa bir oran notu, yanında ayarlara bağlantı.
- "Neden işe yarar": 3 kısa madde.

**Yeni/tekrar oranı:**
- Her seferinde sorulmaz. Ayarlarda kaydırıcıyla değiştirilir, varsayılan ~%70 tekrar / %30 yeni.
- Tekrar birikirse yeni kelime oranı otomatik azalır.
- Tekrar algoritmasının kendisi **sonra konuşulacak**.

**Kart akışı:**
1. Kart ekranda yalnızca **kelimeyi** gösterir: okunaklı, yuvarlak ve sevimli bir yazı tipiyle. Tür etiketi yoktur.
2. **Sağa kaydır = biliyorum**, **sola kaydır = bilmiyorum**.
3. Kaydırınca aşağı doğru açılan bir animasyon gelir:
   - **Kapibara maskotu** göz kırpar.
   - Konuşma balonunda anlam yazar ("Düşündüğün bu muydu?").
   - Altında küçük ve silik bir İngilizce örnek cümle olur.
   - **Kapibara şimdilik boş bir yer tutucu kutudur.** Çizimi ve animasyonu sonra Claude ile birlikte yapılacak.
4. Bir kaydırma daha yapılınca sonraki kelimeye geçilir.

**Kurallar:**
- **"Biliyorum" doğrulanmaz.** Kontrol sorusu sorulmaz; kullanıcı gelişmek için geliyor.
- **Her kaydırma anında kaydedilir.** Oturum yarıda bırakılsa bile hiçbir şey kaybolmaz.
- **Bilinmeyen kelimeler listeye otomatik eklenmez.** Oturum sonunda "Bilmediğin N kelimeyi listene ekleyelim mi?" diye sorulur. Oturum yarıda bırakıldıysa bir sonraki girişte "Geçen sefer bilmediğin N kelime" kartı çıkar.
- **Giriş yapmamış ziyaretçi** yalnızca kaydırır; hiçbir şey kaydedilmez (bkz. 2.3).

### 6.2 Egzersizler
Açılışta **iki büyük seçenek** vardır:

| | **Hızlı Egzersiz** | **Tempolu Egzersiz** |
|---|---|---|
| Kime | Çoğu kullanıcı | Daha çok çalışmak isteyen |
| Soru sayısı | **Tam 10**, sorulmaz | "Kaç soru?" 5 / 10 / 15 / 20 / 25 (varsayılan 10, ayarlardan değişir) |
| Soru tipi | **Yalnızca anlam**, TR→EN ve EN→TR karışık | Aşağıdaki bütün tipler, karışık ya da tek tipe odaklı |
| Kaynak | **Yalnızca kullanıcının listesi** | Tipe göre (tabloya bak) |
| Ayar | Yok, bas ve başla | Tip seçimi ve soru sayısı |

- Liste 10 kelimeden kısaysa Hızlı Egzersiz listedeki kadar soru sorar ve "Listene kelime ekle" daveti gösterir.

**Soru tipleri ve kelime kaynakları (Tempolu):**
| Soru tipi | Kaynak | Not |
|---|---|---|
| Kelime ↔ anlam (TR↔EN) | Kullanıcının listesi | İki yönlü |
| Kelime ↔ İngilizce açıklama | Kullanıcının listesi | |
| Eşleştirme (kelime–anlam) | Kullanıcının listesi | |
| Fiilin 2./3. hâli | **Tüm düzensiz fiiller** (~189), listeden bağımsız | |
| Kelime biçimi ("hangi versiyonu gelir?") | Kullanıcının seviyesindeki her kelime (aile verisi) | Yanlış cevapta **şıklardaki tüm biçimler anlamlarıyla** gösterilir. **Gramer kuralı açıklanmaz**; amaç hissettirmek. |
| Eş / zıt / daha basit anlamlı | **Listede olmayan** kelimeler: ~%80 kendi seviyesi, ~%20 bir üst seviye | Veri anlama özel olacak (D1) |
| Bağlaç / ifade | Liste yok, kullanıcının seviyesinde cümleler | Cümle havuzu üretilecek (D2). Şıklardan **yalnızca biri** anlamı doğru verir. Noktalama inceliği sorulmaz. |
| Eş dizim (collocation) | Mümkünse listeden, yetmezse seviyeden | **v1'de yalnızca hafif fiiller** (make/take/do/give/have…, ~650 adet). Çeldiriciler "mantıklı görünen ama yanlış" olur (do/make a mistake) ve her biri yapay zekâyla önceden doğrulanır (D3). Sıfat+isim sonra. |

- "Türkçe anlama göre doğru İngilizce kelimeyi yaz", register ve diyalog soruları **Yazma** bölümündedir (Bölüm 9).

**Ekranlar:**
1. **Soru:**
   - Üstte ilerleme çubuğu ve ✕ (çık).
   - Küçük gri **soru tipi** etiketi ("Anlamını seç" gibi; gramer etiketi değil).
   - Büyük soru metni, **4 büyük şık**. Masaüstünde 1–4 tuşlarıyla seçilir.
2. **Cevaptan sonra:** Doğruysa yeşil, yanlışsa kırmızı. **Tek satır açıklama**, ardından "Devam".
3. **Bitiş:**
   - Skor (ör. 8/10) ve yanlışların listesi.
   - Üç seçenek: **Yanlışları tekrar çöz** · **Yeni tur** · **Bitir**.

---

## 7. Seviye testi (ilk giriş)

**1. kısım: kelime bilgisi.**
- 3 ekran, her ekranda 40 kelime. Kullanıcı yalnızca **bildiklerine dokunur**.
  - Ekran 1: A1–A2
  - Ekran 2: B1–B1+
  - Ekran 3: B2–C1
- Kolay ekranda çok az kelime bilinirse zor ekran gösterilmez.
- **Uydurma (sahte) kelime kullanılmaz.** Kullanıcı fark ederse güven kaybolur. Dokunulanlara güvenilir.

**2. kısım: okuduğunu anlama.**
- 3 kısa metin, her biri 4–5 cümle, kolaydan zora.
- Her metinde "metni en iyi özetleyen cümle" sorulur, çeldirici şıklarla.
- Sorular ~100 soruluk bir havuzdan rastgele seçilir. Havuz bir kere üretilir ve denetlenir (D4).

**Sonuç:**
- Seviye tahmini yapılır.
- **İlk liste**, kendi seviyesindeki ekranda **dokunmadığı** kelimelerden oluşur.

**Diğer:**
- "Seviyemi kendim seçeyim" kaçış yolu vardır.
- Test ayarlardan tekrarlanabilir.
- Seviye zamanla çalışma sonuçlarına göre sessizce düzeltilir.

---

## 8. Okumalar

**Tek işi: odaklanıp okumak.**

**Okumalar ana sayfası:**
- **Kütüphane:** telifsiz metinler, kısa akademik yazılar, edebi kelimeler içeren kısa hikâyeler, yapay zekâyla üretilmiş metinler (D5).
- **Kendi metinlerim:** PDF yükleme ya da kopyala-yapıştır. **Yalnızca o kullanıcıya özeldir**, böylece telif riski yoktur. Giriş gerektirir.

**Okuma ekranı:**
- Bir kelimeye dokununca anlamı **anında** küçük bir baloncukta görünür. Yanında küçük bir **"+"** ile kelime listeye eklenir. **Başka bir şey yoktur.**
- **Çok anlamlı kelimede tüm anlamlar kısa ve numaralı** gösterilir: "1. banka 2. nehir kıyısı". En yaygın anlam en üsttedir. Yapay zekâyla bağlamdan anlam seçilmez (maliyet ve gecikme yüzünden).
- **Çekimli biçimler köke bağlanır** (decided → decide; `WordForm` verisi).
- **Phrasal verb'ler algılanır** (give up, look after).
- Veritabanında olmayan kelime için "Henüz sözlüğümüzde yok" yazar. Bu da kaydedilir.
- **v1'de OCR yoktur.** Taranmış (resim) PDF'ler desteklenmez.
- Kelime sorgulama **API olarak** yazılır; Chrome eklentisi aynı API'yi kullanacaktır.

---

## 9. Yazma

**Eski sistemin sorunları** (`texts/send_gemini.py`):
- 10 kriter ve 100 puan var. Akademik yapı bekleniyor (topic, major, minor, summary), formal dil, özne tutarlılığı, hedging.
- Sonuç cesaret kırıcı: puanlar düşük geliyor.
- Kriterler fazla ve gereksiz.
- Cevap uzun ve düz; neyin neden yanlış olduğu açıklanmıyor.
- **Bu prompt tamamen değiştirilecek.**

### 9.1 Serbest yazma
- **Görev:**
  - Kısa, **3–8 cümle**. Akademik yazı beklenmez.
  - Konu önerilerinden biri seçilir ya da serbest yazılır.
  - Listeden 3–5 **"kullanmayı dene"** kelimesi önerilir. Kullanmak zorunlu değildir.
- **Değerlendirici:** Gemini'nin ücretsiz katmanı. Yedek model mantığı `LearnVocab/gemini.py`'de zaten var.
- **Geri bildirim dili:** Türkçe.
- **Çıktı yalnızca iki listedir** (ve bir puan):
  - **İyi yapılanlar:** her madde **tek cümle**, neyin iyi olduğunu ve **neden** iyi olduğunu söyler. Metinden somut bir alıntıya dayanır, boş övgü olmaz. En az 1, en çok 3–4 madde.
  - **Hatalar:** her madde **tek bir şeye** değinir. Biçim: `alıntı → doğrusu → tek cümlelik neden`.
    > ~~he go to school~~ → **he goes to school** · Tekil öznede fiile -s eklenir.
  - **"Geliştirilebilir" bölümü YOKTUR.** Olursa model her şeyi oraya yığar.
- **Metin görünümü:** Hatalı parçaların altı metinde çizilidir. Dokununca ilgili hata maddesi açılır.
- **Hata tanımı:** Yalnızca gerçek hatalar sayılır: dilbilgisi, yanlış kelime, anlamı bozan kullanım. **Üslup tercihi hata değildir.**
- **Model JSON döndürür**, listeleri arayüz çizer. Önerilen şema:
  ```json
  {
    "puan": 3.5,
    "iyi": [{"alinti": "...", "aciklama": "..."}],
    "hatalar": [{"alinti": "...", "dogrusu": "...", "neden": "..."}],
    "kullanilan_kelimeler": ["aim", "decide"]
  }
  ```
- **Puan:** 5 üzerinden, yarım puan adımlı. Pratikte aralık 2–5.
  | Puan | Ne zaman |
  |---|---|
  | 1 | Yalnızca çok çok kötü (neredeyse hiç) |
  | 2 | Çok kötü |
  | 3 | Kötü |
  | 3.5 | Ortalama |
  | 4 | Azıcık iyi |
  | 4.5–5 | Çok iyi |
- **Sertlik** (ayarlardan):
  - **Nazik:** yalnızca anlamı bozan hatalar, en çok 3.
  - **Normal (varsayılan):** dilbilgisi ve kelime hataları, en çok 6.
  - **Titiz:** noktalama, büyük harf ve resmiyet de dahil.
  - **Varsayım:** Sertlik yalnızca hata listesini etkiler, puan bantları her sertlikte aynıdır.
- **Değerlendirilemeyen metin:**
  - Gemini cevap vermezse ya da kota dolarsa metin kaybolmaz. **Yazılarım** listesinde **sarı "Henüz değerlendirilmedi"** etiketiyle görünür.
  - Sistem bu metinleri arka planda aralıklarla (ör. 30 dakikada bir, kotaya uyarak) **kendisi yeniden dener**.
  - Değerlendirme tamamlanınca etiket kalkar. Kullanıcı bildirimleri açtıysa "Yazın değerlendirildi" bildirimi gider.
- **Sınırlar:**
  - Kullanıcı başına günlük değerlendirme limiti olur (`texts/limits.py` var).
  - Yoğunlukta "Biraz sonra tekrar dene" mesajı gösterilir.

### 9.2 Diyalogda doğru kelime
- 4–6 satırlık hazır bir diyalog ve **1 boşluk**. Boşluğun altında Türkçe ipucu olur (*ertelemek*). Kullanıcı İngilizce kelimeyi **yazar**.
- Hedef kelime kullanıcının listesinden gelir.
- **Değerlendirme:**
  - Çekimli hâl kabul edilir (postpone / postponed).
  - Tek harf hatasında "Neredeyse! Doğrusu: postponed" denir.
- "İlk harfi göster" ipucu vardır.
- Resmî/samimi kelime seçimi (register) ve duygu tonu (sentiment) burada öğretilir.
- Diyaloglar **önceden üretilmiş ve denetlenmiş bir havuzdan** gelir, canlı üretilmez (D6).

---

## 10. Bildirimler (Web Push)

**Mümkün mü:**
- **Android (Chrome vb.):** Kullanıcı izin verince çalışır.
- **iPhone (iOS 16.4+):** Yalnızca site **"Ana Ekrana Ekle"** ile uygulama gibi kurulursa (PWA) ve kullanıcı izin verirse çalışır. Safari sekmesinden çalışmaz. Bu yüzden iPhone kullanıcıları için küçük bir "Ana ekrana ekle" rehberi gerekir.

**Gereksinimler:**
- HTTPS
- Service worker
- Web app manifest
- VAPID anahtarı
- `pywebpush` / `django-webpush`
- Sunucuda **cron**. Yazma yeniden denemesi de aynı cron'u kullanır.

**İzin zamanı:**
- Sayfa açılır açılmaz **sorulmaz**. Anlamlı bir anda sorulur; örneğin L&P bitince: "Yarın hatırlatayım mı?"
- Reddedilen izin bir daha sorulamaz, bu yüzden zamanlama önemlidir.

**Kullanım:**
- Günlük L&P hatırlatması.
- "Yazın değerlendirildi" bildirimi.
- Bildirimler **az ve anlamlı** tutulur.

**Kontrol edilecek:** Mevcut barındırma (Apache + Passenger, learnvocab.com.tr) cron ve HTTPS'i destekliyor mu? Bu adıma gelince Efe'ye sorulacak.

---

## 11. Chrome eklentisi (v1'den sonra)
- **İşlev:** Herhangi bir sitede kelimeye tıklayınca anlam **bizim veritabanımızdan** gelir. "+" ile listeye eklenir.
- **Altyapı:** Okumalar'daki kelime sorgulama API'sini kullanır.
- **Gereksinimler ve sınırlar:**
  - HTTPS'li sunucu.
  - Chrome Web Store'a bir kerelik 5 $ ücret.
  - Chrome'un kendi PDF görüntüleyicisinde çalışmaz.

---

## 12. Site geneli kurallar

1. **Gramer etiketleri:**
   - **Yalnızca Sözlük kartında** gösterilir, Türkçe olarak: isim, fiil, sıfat, zarf.
   - L&P kartlarında, egzersiz sorularında ve açıklamalarda **asla gösterilmez**.
   - Egzersizlerde kural anlatılmaz; seçenekler anlamlarıyla gösterilerek hissettirilir.
2. **Hassas ve müstehcen anlamlar yazılmaz.** Bu site onun için geliştirilmedi. (Veri hattında `_HASSAS_TR` / `_HASSAS_EN` filtreleri var.)
3. **Uydurma kelime kullanılmaz** (seviye testi dahil).
4. **Cesaretlendirici dil.** Hiçbir ekran cezalandırmaz, hata mesajları öğretir.
5. **Ayrı kelime sayfası yoktur.** Kelime her zaman kart bileşeni olarak, bulunduğu yerde açılır.
6. **Giriş gerektiren düğmeler gizlenmez.** Basılınca girişe yönlendirir.
7. **Onay penceresi yerine "Geri al" bildirimi** kullanılır.
8. **Yeni veri üretimi** önce önbelleğe (cache) yazılır, `--dry-run` ile kontrol edilir, sonra gerçek yazım yapılır. Her partiden sonra çıktı gözden geçirilir.

---

## 13. Veri

### 13.1 Mevcut durum (27 Eylül 2026)
| Öğe | Sayı |
|---|---|
| Kelime (`Word`, her tür ayrı kayıt) | 16.189 |
| Kelime ailesi | 4.924 |
| Anlam (`Meaning`) | 19.828 (çok anlamlı kelime: 3.288) |
| Örnek cümle | 91.480 |
| Eş dizim (`Collocation`) | 35.687 (fiil+isim 12.498 · sıfat+isim 13.104 · hafif fiilli ~650) |
| İlişki (`WordRelation`) | 56.347 (eş: 14.016 kelimede · zıt: 13.357 · basit: 13.600) |
| İfade / ifade grubu | 295 / 21 |
| Düzensiz fiil | ~189 |

- **CEFR dağılımı:** A1 557 · A2 1.591 · B1 4.929 · B2 7.120 · C1 1.908 · C2 84
- **Toplam veri maliyeti:** ~30 $

### 13.2 Modeller (özet)
- **`Word`:** text, pos, cefr, v2Form, v3Form, family
- **`Meaning`:** meaning_tr, definition, cefr, sort_order
  - `examples` → `ExampleSentence`
  - `collocations` → `Collocation` (pattern, kind, meaning_tr, example)
- **`WordRelation`:** from_word, to_word, type (synonym / antonym / simpler / confused_with), note, **meaning** (D1, 28 Eylül). Eş/zıt/basit anlama bağlı: her (anlam, hedef, tür) bir satır. `confused_with` kelime düzeyinde kalır (meaning boş): karışıklık biçimden gelir, anlamdan değil. Kart için `Meaning.iliski_satirlari()` (Benzer / Daha basit / Zıt, satır başına en çok 4).
- **Diğer:** `WordForm` (çekimli biçim → kök), `Expression` / `ExpressionGroup`, `UserWordLink` / `UserExpressionLink` (kullanıcı listesi), `FalseFriend`.

### 13.3 Yapılacak veri işleri
| Kod | İş | Not / maliyet |
|---|---|---|
| **D1** | `WordRelation`'a boş bırakılabilir `meaning` FK ekle, önbellekten geri doldur | **Yapıldı (28 Eylül), bkz. Değişiklik kaydı.** Ham önbellekte (`ara-depo-tam/anlamlar.jsonl`) ilişkiler **zaten anlam başına** üretilmiş: 4.371 çok anlamlı kaydın 4.366'sında anlamlara göre farklı. Yükleyici bunları kelime düzeyinde birleştirmiş. Tek anlamlı kelimelerde atama otomatik. Elle eklenen anlamlarda (`words/duzeltmeler/d_2026_09_25.py`) ilişki boş kalabilir, kontrol edilecek. **0 $.** |
| **D2** | Bağlaç/ifade cümle havuzu (seviyelere göre) | Şıklardan yalnızca biri doğru olmalı. Üretilip denetlenecek. |
| **D3** | Hafif fiilli eş dizimler için çeldirici doğrulama | ~650 eş dizim. Her çeldirici yapay zekâyla "gerçekten yanlış mı" diye kontrol edilecek. |
| **D4** | Seviye testi okuma havuzu (~100 metin + soru) | 3 zorluk düzeyi, özet cümlesi ve çeldiriciler. |
| **D5** | Okuma kütüphanesi | Telifsiz, akademik, hikâye ve yapay zekâ metinleri. |
| **D6** | Diyalog havuzu (Yazma) | Kelime başına diyalog, Türkçe ipucu ve register notu. |
| **D7** | Hazır listeler | ODTÜ, Bilkent, Cambridge vb. listeleri veritabanındaki kelimelerle eşleştirilecek. Eşleşmeyenler raporlanacak. |
| **D8** | Seviye testi kelime ekranları | 3 × 40 kelime. Yaygın ve tanınır kelimelerden, seviyeye göre seçilecek. |

---

## 14. Teknik bağlam ve çalışma kuralları

**Yığın:**
- Django 5.2, sunucu tarafında şablonlar, Tailwind CSS.
- Canlıda MySQL, yerelde SQLite.
- Gemini API.
- Apache + Passenger (`passenger_wsgi.py`).

**Yollar:**
- Efe'nin Mac'indeki proje: `/Users/efesolmaz/Desktop/Programlama/Projects/Python Projects/LearnVocab Latest wClaude`, sanal ortam `.venv`.
- Claude'un VM'inde proje `$HOME/mnt/LearnVocab Latest wClaude` altında bağlı. Python: `$HOME/lvenv/bin/python`.

**Ayar modülleri:**
- `testayar`: testler için.
- `yazayar`: `$HOME/db-calisma.sqlite3` kopyasına yazar. Bağlı klasördeki SQLite'a doğrudan yazmak başarısız olur. **Kopyada çalışılır, sonra kopya geri `cp` edilir.**

**Testler:**
```
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$HOME timeout 170 $HOME/lvenv/bin/python manage.py test --settings=testayar --parallel 4
```
776 test geçiyor. Her değişiklikten sonra çalıştırılır.

**Betik çalıştırma:** `yazayar` ile çalışırken `PYTHONPATH=$HOME:.` gerekir.

**VM kısıtları:**
- Her komut en fazla ~180 saniye sürebilir; uzun işler parçalara bölünür.
- Bağlı klasörde **dosya silinemez** (`rm` yasak). Silinmesi gereken dosyalar Efe'ye söylenir ya da izin istenir.

**Kelime hattı:**
- Sıra: `aile_uret` → `aile_birlestir` → `aile_doldur`. Önce `--dry-run`, sonra önbellekten gerçek yazım.
- Bayraklar: `--sira listeler/tum-tohumlar.txt`, `--limit`, `--reddedilenler`.
- Kararlar `kararlar.json` dosyasında: `cikar`, `onayla`, `uye_ata`, `kok_esle`, `ayri_tut`.
- Bir kelimenin yeniden yazılmasını engellemek: `anlamlar.jsonl`'e `"durum":"reddedildi"` kaydı ekle ya da `kararlar.json`'da `cikar` kullan.
- `kelime_listesi` komutu `listeler/tum-kelimeler.txt` dosyasını üretir.

**Elle düzeltmeler:**
- Yeri: `words/duzeltmeler/d_2026_09_25.py`. Fonksiyonlar idempotenttir.
- Çalıştırma:
  ```
  python manage.py shell -c "from words.duzeltmeler import d_2026_09_25 as d; d.uygula_7()"
  ```

**Güvenlik:**
- OpenRouter anahtarı `.env` içinde `LLM_API_KEY` olarak durur. **Sohbete asla yapıştırılmaz.**
- Gemini anahtarı ve ayarları `.env` / `settings`'tedir.

**Yedek:** Büyük veri değişikliklerinden önce `db.sqlite3.yedek-<açıklama>` adıyla yedek alınır.

**Uygulamalar:**
| Uygulama | Durum |
|---|---|
| `words`, `users`, `userprofile`, `usersettings`, `learnpass`, `readings`, `texts` | Aktif |
| `quizzes` | **Tamamen silinecek** (Efe'nin kararı). Önce başka modellerden gelen bağımlılıklar ve FK'ler kontrol edilir, tablolar migration ile kaldırılır. |
| `comments`, `friends` | Arayüzden kaldırıldı, **kodları kalıyor**. |
| Diğer eski arayüz parçaları (Tüm Kelimeler sayfası, filtre paneli, eski egzersiz sayfaları) | **Arayüzden kaldırılır**, kod gerekmedikçe silinmez. |

---

## 15. Uygulama planı

Her adım kendi içinde test edilir ve Efe'ye gösterilir. Veri havuzları (D2–D8) ilgili adıma gelince hazırlanır.

1. **Temizlik:**
   - `quizzes` silinir.
   - Eski sayfalar ve bağlantılar arayüzden kaldırılır.
   - README'deki eski özellik listesi güncellenir.
2. **Veri: D1.** Eş, zıt ve basit anlamlılar anlamlara bağlanır, testler eklenir.
3. **İskelet:**
   - Yeni menü (mobilde altta, masaüstünde üstte).
   - Ortak kelime kartı bileşeni.
   - Giriş yapmamış ziyaretçi kuralları ve "girişe yönlendir" davranışı.
   - "Geri al" bildirim bileşeni.
4. **Sözlük:**
   - Keşfet'in boş hâli.
   - Arama: anlık öneri, İngilizce ve Türkçe sorgu, diğer sonuçlar, bulunamayan akışı, arama kaydı.
   - Kelime kartı.
   - Hazır listeler (D7) ve "Bu listeyle çalış".
5. **Listem:** liste, arama, filtre, toplu seçim.
6. **Learn & Pass:**
   - Açılış ekranı.
   - Kaydırmalı kart akışı (kapibara yeri boş kutu).
   - Oturum sonu ekleme ve "geçen sefer" kartı.
   - Tekrar algoritması konuşulana kadar mevcut seçim mantığı (`learnpass/selection.py`) korunur.
7. **Egzersizler:** Hızlı Egzersiz, ardından Tempolu Egzersiz (tipler; D2, D3).
8. **Okumalar:** kütüphane (D5), kendi metinlerim (PDF ve yapıştır), dokun-anlam baloncuğu, kelime sorgulama API'si.
9. **Yazma:**
   - Yeni prompt ve JSON çıktısı.
   - Puan bantları ve sertlik.
   - Altı çizili hata görünümü.
   - Sarı etiket ve otomatik yeniden deneme.
   - Diyalog egzersizi (D6).
10. **Seviye testi** (D4, D8) ve **Ana Sayfa**.
11. **Bildirimler ve PWA:** manifest, service worker, izin akışı, cron. Önce barındırma kontrol edilir.

---

## 16. Sonra konuşulacaklar ve varsayımlar

**Efe ile konuşulmadan uygulanmayacaklar:**
- **Tekrar algoritması (L&P):** "biliyorum" ve "bilmiyorum" denen kelimeler ne zaman tekrar gelir, birikme nasıl yönetilir.
- **Seri (streak):** nasıl sayılır, kaçırılan gün affı. Efe'nin fikirleri var.
- **Ayarlar sayfası:** raporda ayarlara yapılan bütün göndermeler (oran kaydırıcısı, varsayılan soru sayısı, yazma sertliği, seviye, bildirimler, hesap) geçerli ama sayfa henüz tasarlanmadı. Mevcut kullanıcı verisinin taşınması da bu sırada ele alınacak.
- **Kapibara:** çizim ve animasyon Claude tarafından yapılacak, Efe ile birlikte. Şimdilik boş yer tutucu.
- **Hakkında / yardım içeriği:** her şey bittikten sonra.
- **KVKK / gizlilik metni:** işler geliştikçe. Not: PDF yüklemeleri ve Gemini'nin ücretsiz katmanı (gönderilen metinler Google'ın ürün geliştirmesinde kullanılabilir) bu metinde belirtilmeli.

**Claude'un varsayımları** (Efe itiraz etmedi, değişebilir):
- Giriş yapmamış biri "+" düğmesine basarsa girişe yönlendirilir.
- Giriş yapmamış ziyaretçiye L&P ve günün kelimesi B1 civarından gelir. L&P'de kaydedilmeyen bir "seviyeni seç" seçeneği vardır.
- Yazma sertliği yalnızca hata listesini etkiler, puanı etkilemez.

**Efe'nin 28 Eylül kararları:**
- Veri havuzları (D2–D6) için **hiç LLM harcaması yapılmaz**. Yükleme komutları ve biçimler hazır; havuzlar boş, ilgili arayüzler boş hâli gösterir ("Yakında" / "hazırlanıyor").
- `reading-texts/` metinlerine dokunulmaz, kütüphaneye yeni metin eklenmez.
- Hazır liste verisi (ODTÜ, Bilkent, Cambridge…) şimdilik eklenmez; altyapı ve `hazir_liste_yukle` komutu hazır.
- Barındırma Veridyen: cron ve HTTPS var.

**Uygulama sırasında Claude'un verdiği, Efe'ye sorulacak ara kararlar** (değişebilir):
- Kur → CEFR eşlemesi (seviye alanı boşken): 101→A1, 201→A2, 301→B1, 401→B2, 501→C1; bilinmiyorsa B1.
- L&P turu 20 kart. Bekleyen tekrar 40'ı aşınca yeni oranı 0,30 × 40 / bekleyen (en az 0,10).
- L&P'de listeye eklenmeyen bilinmeyen yeni kelime bir daha gelmiyor (eski seçim kuralı; tekrar algoritmasıyla birlikte konuşulacak). Yeni kelime seçimi her seviyede ilk 2000 kayıttan yapıldığı için alfabetik başa kayıyor, düzeltilmeli.
- Egzersizler: üç hâli aynı düzensiz fiiller (cut/put/hit) sorulmuyor; eşleştirme tek soru sayılıyor.
- Yazma: günlük değerlendirme sınırı 3 (`TEXT_DAILY_LIMIT`), site genelinde dakikada en çok 4. Titiz sertlikte en çok 10 hata. Metin 20–1500 karakter. Diyalog cevapları Zorlandıklarım'a yazılmıyor.
- Okumalar: kendi metni silinince 1 gün çöpte kalır; kullanıcı başına en çok 100 metin; PDF en çok 10 MB / 60 sayfa, dosya saklanmaz.
- Hazır liste dosyasında türü verilmemiş çok türlü kelimenin yalnızca en yaygın türü eklenir.
- Seviye testi zorunlu değil: seviyesi boş kullanıcıya Ana Sayfa'da davet kartı ("Teste başla · Seviyemi kendim seçeyim · Şimdi değil"; "Şimdi değil" cihazda 30 gün). Tahmin: bir ekranı geçmek için %50; 3. ekranda %80+ → C1; okuma (havuz dolunca) yalnızca 3/3 ya da 0/3'te ±1 seviye. D8 havuzu `seviye_kelimeleri_sec` ile 360 kelime (ekran başına 120, her testte rastgele 40); "sixth", "ether" gibi sınırdaki kelimeler admin'den temizlenebilir.
- "Seviye zamanla sessizce düzeltilir" için algoritma yok; `seviye/duzeltme.py` boş kanca, tekrar algoritmasıyla konuşulacak.
- Kayıt formundaki eski "kur" seçimi duruyor (zorunlu); kaldırılsın mı, CEFR'e mi eşlensin?
- Bildirimler: hatırlatma 19:00, günde tek; izin kartı yalnızca L&P turu bitince, "Şimdi değil" 7 gün. Bildirimleri kapatma düğmesi ayarlar sayfası tasarlanınca eklenecek.

---

## 17. Vazgeçilen fikirler (geri getirme)

| Fikir | Neden vazgeçildi |
|---|---|
| Kelime yolculuğu (Tanıdım → Hatırladım → Metinde gördüm → Kullandım) ve "öğrenildi" durumu | Efe kaldırdı. Tek gösterge listedeki kelime sayısı. (Zorlandıklarım için bilmiyorum ve yanlış kayıtları yine tutulur.) |
| Tek zorunlu günlük akış ("10 dakikalık görev") | Kullanıcıyı kısıtlar, bütün bölümler açık kalmalı. |
| L&P'de "biliyorum" dediği kelimeyi kontrol sorusuyla sınamak | Kullanıcı gelişmek için geliyor, güvenilir. |
| Seviye testinde uydurma kelime | Fark edilirse güven kaybı. |
| Egzersizlerde her seferinde yeni/eski oranı sormak | Ayarlardaki kaydırıcıya taşındı. |
| Egzersizlerde gramer kuralı anlatmak ya da tür etiketi göstermek | Amaç hissettirmek. Etiket yalnızca Sözlük'te ve Türkçe. |
| Her kelimeye ayrı sayfa, "Tüm Kelimeler" sayfası, filtre paneli | Kart bileşeni yerinde açılır. Sayfa kalabalığı gider. |
| Eş, zıt ve basit anlamlıları kelime düzeyinde göstermek | Yanlış eşleşme (bank → shore). Anlama özel gösterilir. |
| Okurken yapay zekâyla bağlamdan tek anlam seçmek | Maliyet ve gecikme. Tüm anlamlar numaralı gösterilir. |
| Hazır listeyi toplu "hepsini ekle" | Kullanıcıyı boğar. Yerine "Bu listeyle çalış" geldi. |
| Listem'de yolculuk adımı, istatistik, seviye filtresi | Listem aşırı basit kalmalı. |
| Yazmada 10 kriter ve 100 puanlık akademik rubrik | Cesaret kırıcı. Yerine iki liste ve 2–5 bantlı puan geldi. |
| Yazma geri bildiriminde "geliştirilebilir" bölümü | Model her şeyi oraya yığar. |
| Diyalogları canlı üretmek | Yavaş ve denetimsiz. Havuzdan gelir. |

---

## Değişiklik kaydı
- **2026-09-27:** İlk sürüm. Kaynak: `ozetler/2026-09-26_urun-kararlari.md` (26–27 Eylül konuşmaları).
- **2026-09-28:** D1 yapıldı (migration `words/0020_iliski_anlam`, komut `iliskileri_anlama_bagla`). 56.187 bağ anlama atandı, 512'si birden çok anlamda geçtiği için çoğaltıldı. Silinmiş anlamlardan gelen 44 bağ boş kaldı (kartta görünmez). `confused_with` kelime düzeyinde kaldı. `aile_doldur` artık bağları doğrudan anlama yazıyor; silinmiş anlamın bağını geri kurmuyor.
- **2026-09-28:** Adım 3 (İskelet) yapıldı. Menü `LearnVocab/navigation.py` (Sözlük · Çalışmalar · Ana Sayfa · Okumalar · Yazma; mobilde altta, masaüstünde üstte; içerik `max-w-3xl`). Sözlük iskeleti `/sozluk/` (Keşfet | Listem; şimdilik yalnızca İngilizce tam eşleşme). Ortak kelime kartı `templates/base/_kelimeKarti.html` + veri `words/kart.py` (`kart_verisi`, sabit 8 sorgu). Düzensiz fiil: `inflect.duzensiz_fiil_mi` (veritabanında düzenli fiillerin de v2/v3'ü dolu olduğu için kural çıktısıyla karşılaştırılıyor). Giriş gerekli: `data-giris-gerekli="<neden>"` + `/users/login/?next=…&neden=…` (girişte `next`'e dönülüyor). "Geri al" bildirimi: `window.geriAl.goster(mesaj, fn)`. Ara durum: L&P açılış sayfası girişsiz açık ama misafir kaydırma akışı 6. adımda; o zamana kadar mod düğmeleri girişe yönlendiriyor. Dişli simgesi ayarlar sayfası tasarlanana kadar Profilim'e gidiyor.
- **2026-09-28:** Adım 4–9 yapıldı (her biri ayrı commit). Sözlük ve Listem (`words/arama.py`, `words/listem.py`, `words/hazir_liste.py`, `words/sozluk_views.py`); Learn & Pass (misafir modu, oturum sonu soru, "geçen sefer" kartı); Egzersizler (yeni `egzersizler` uygulaması, `/egzersizler/`); Okumalar (kendi metinlerim, dokun-anlam baloncuğu, `GET /api/kelime/`); Yazma (JSON geri bildirim, sertlik, `yazilari_yeniden_dene`, diyaloglar). `quizzes` uygulaması kaldırıldı (`learnpass/0003`). Efe'nin 28 Eylül kararları ve açık sorular Bölüm 16'da.
- **2026-09-28:** Adım 10–11 yapıldı. Seviye testi (`seviye` uygulaması, `User.cefr`, tek kaynak `users.seviye.kullanici_seviyesi`), yeni Ana Sayfa (`LearnVocab/anasayfa.py`), Bildirimler ve PWA (`bildirimler` uygulaması; kurulum ve cron: `bildirimler/CRON.md`). Uygulama planının 11 adımı tamamlandı; D2–D6 havuzları Efe'nin kararıyla boş, D7 liste verisi yüklenmedi.
