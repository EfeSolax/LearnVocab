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
18. Yapılacaklar (29 Eylül 2026 kararları)

> **29 Eylül notu:** Bölüm 18'deki kararlar uygulanana kadar önceki bölümlerde onlarla çelişen yerler **"→ 18.x"** notuyla işaretlidir. Çelişki olursa **Bölüm 18 geçerlidir.**

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
> **→ 18.3:** Misafir kuralları değişiyor (Sözlük'te sekme ve "Listeme ekle" yok, Çalışmalar'da yalnızca L&P, Yazma'da yalnızca diyalog; giriş gerektiren öğeler gizlenip yerine tek bir davet bağlantısı konur).

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
> **→ 18.8:** Günün kelimesi ve günün ifadesi 29 Eylül'de yeniden kararlaştırıldı. **→ 18.9:** Seri 29 Eylül'de kararlaştırıldı; kutu şu an yalnızca yer tutucu.


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
> **→ 18.4:** Telaffuz düğmeleri (Amerikan / İngiliz) eklenecek. **→ 18.5:** Liste düğmesi her yerde aynı "Listeme ekle" olacak. **→ 18.6:** "Daha basit" satırına seviye kuralı gelecek. **→ 18.15:** Kartın adresi SEO için yeniden tasarlanacak.

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
> **→ 18.1:** Kart akışı değişiyor ("Düşündüğün bu muydu?" kaydırmayla cevaplanacak). **→ 18.2:** Aralıklı tekrar şimdi kararlaştırılacak. **→ 18.10:** L&P ekranı dikkat dağıtıcılardan arındırılarak yeniden tasarlanacak. **→ 18.11:** L&P'nin ne olduğunu anlatan açıklama kutusu eklenecek.

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

**Kullanım:** (→ 18.9: günde iki zaman, 12.00 · 23.45 yerel saatle; gün tamamlandıysa ya da seri 0 ise gitmez)
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
6. **Giriş gerektiren düğmeler gizlenmez.** Basılınca girişe yönlendirir. **→ 18.3:** Bu kural değişiyor: misafire giriş gerektiren öğeler gösterilmez, bölümde tek bir giriş davet bağlantısı olur.
7. **Onay penceresi yerine "Geri al" bildirimi** kullanılır.
8. **Yeni veri üretimi** önce önbelleğe (cache) yazılır, `--dry-run` ile kontrol edilir, sonra gerçek yazım yapılır. Her partiden sonra çıktı gözden geçirilir.

---

## 13. Veri

> **→ 18.7:** Bütün veritabanı taranıp yanlış alanlar silinecek ya da düzeltilecek. **→ 18.16:** CEFR ile sıklık (wordfreq) ilişkisi kararlaştırılacak. **→ 18.14:** Boş havuzlara 5'er örnek yazılacak.

### 13.1 Mevcut durum (27 Eylül 2026; kelime ve aile sayısı 29 Eylül)
| Öğe | Sayı |
|---|---|
| Kelime (`Word`, her tür ayrı kayıt) | 16.109 (29 Eylül: yalnızca sayı anlamı taşıyan 80 kayıt silindi, bkz. 18.16) |
| Kelime ailesi | 4.897 (29 Eylül: boş kalan 27 aile silindi) |
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
Bu komut Claude'un VM'i içindir (`testayar` ve `$HOME/lvenv` yalnızca orada var). Efe'nin Mac'inde: `.venv/bin/python manage.py test --parallel 4 --noinput`.
829 test geçiyor (29 Eylül; silinen eski sayfaların testleri kaldırıldı). Her değişiklikten sonra çalıştırılır.

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
| Diğer eski arayüz parçaları (Tüm Kelimeler, kelime/ifade detayı, Kelimelerim, elle kelime ekleme, kelime klasörleri, yapay zekâ ile kelime ekleme) | **Kodlarıyla birlikte silindi** (29 Eylül, 18.13). |

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

> **29 Eylül:** Karar bekleyen konular Bölüm 18'de; tam liste 18.20'nin sonunda. En yakın konuşmalar: **CEFR (18.16)**, **seri (18.9)** ve **günün kelimesi/ifadesi (18.8)**.

**Efe ile konuşulmadan uygulanmayacaklar:**
- **Tekrar algoritması (L&P):** (→ 18.2: 29 Eylül'de karar verildi: Efe'nin 1-3-7-21 kuralı) "biliyorum" ve "bilmiyorum" denen kelimeler ne zaman tekrar gelir, birikme nasıl yönetilir.
- **Seri (streak):** → 18.9'da 29 Eylül'de kararlaştırıldı.
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
| Her kelimeye ayrı sayfa, "Tüm Kelimeler" sayfası, filtre paneli | Kart bileşeni yerinde açılır. Sayfa kalabalığı gider. **Not (29 Eylül, 18.15):** Bu, ayrı bir sayfa *tasarımından* vazgeçmektir. Her kelimenin SEO için kalıcı bir **adresi** olur (`/sozluk/bank/`); o adreste aynı Sözlük ekranı ve aynı kart görünür. |
| Eş, zıt ve basit anlamlıları kelime düzeyinde göstermek | Yanlış eşleşme (bank → shore). Anlama özel gösterilir. |
| Okurken yapay zekâyla bağlamdan tek anlam seçmek | Maliyet ve gecikme. Tüm anlamlar numaralı gösterilir. |
| Hazır listeyi toplu "hepsini ekle" | Kullanıcıyı boğar. Yerine "Bu listeyle çalış" geldi. |
| Listem'de yolculuk adımı, istatistik, seviye filtresi | Listem aşırı basit kalmalı. |
| Yazmada 10 kriter ve 100 puanlık akademik rubrik | Cesaret kırıcı. Yerine iki liste ve 2–5 bantlı puan geldi. |
| Yazma geri bildiriminde "geliştirilebilir" bölümü | Model her şeyi oraya yığar. |
| Diyalogları canlı üretmek | Yavaş ve denetimsiz. Havuzdan gelir. |

---

## 18. Yapılacaklar (29 Eylül 2026 kararları)

Kaynak: Claude'un 29 Eylül eleştirisi ve Efe'nin cevabı. **Henüz hiçbiri uygulanmadı.**
- **"Efe'nin kararı"** yazan maddeler kesindir.
- **"Karar bekliyor"** yazan maddeler Efe ile konuşulmadan uygulanmaz. Seçenekler ve Claude'un önerisi maddenin altında durur.

### 18.1 L&P kart akışı: "Düşündüğün bu muydu?" kaydırmayla cevaplanır (Efe'nin kararı) — **YAPILDI (30 Eylül)**
> `templates/pages/learnpass/learnPass.html`: durumlar soru → dogrula / bilmiyor. Karar ikinci adımda kesinleşip gönderilir. Düğmeler ve ← → tuşları da aynı iki seçeneği verir. Açıkken "Geri al" yalnızca soruya döner; kesinleşmiş kararı sunucuda geri alır.

**Sorun:** Şu an "Biliyorum" denince anlam ve "Düşündüğün bu muydu?" sorusu çıkıyor, ama tek düğme "Sonraki kelime". `WordEncounter.MISJUDGED` modelde var, arayüz hiç göndermiyor (`learnPass.html`, `verdict` yalnızca `known`/`unknown`). L&P'nin "biliyorum sanıyordum / gerçekten biliyorum" vaadi toplanmıyor.

**Yeni akış:**
1. Kart kelimeyi gösterir. Sağa kaydır = **biliyorum**, sola kaydır = **bilmiyorum**.
2. **"Biliyorum" dediyse:** anlam ve "Düşündüğün bu muydu?" açılır. Bu ekranda ikinci kaydırma cevaptır:
   - **Sağa kaydır = "Evet, eminim"** → `known`
   - **Sola kaydır = "Hayır, yanılmışım"** → `misjudged`
   - Ekranda iki yönün ne anlama geldiği yazar.
3. **"Bilmiyorum" dediyse:** yalnızca anlam gösterilir, altında **"Devam etmek için kaydır"** yazar. Hangi yöne kaydırıldığı önemli değil → `unknown`.
4. Kayıt ikinci adımda yapılır. Karar `known` / `misjudged` / `unknown` olarak gönderilir; misafirde hiçbir şey kaydedilmez.
- **Varsayım (Claude):** Masaüstünde kaydırma zor olduğu için düğmeler ve ok tuşları da aynı iki seçeneği verir ("Evet, eminim" / "Hayır, yanılmışım"). Yeni tasarımda (18.10) netleşir.

### 18.2 Tekrar kuralı (Efe'nin kararı, 29 Eylül: FSRS yerine Efe'nin kuralı) — **YAPILDI (30 Eylül)**
> **Kod:** `learnpass/tekrar.py` (kaydet, tekrar_sirasi, liste_sirasi, yeni_kelime, misafir_kelimeleri). Migration `learnpass/0005_tekrar_kurali`: `is_learned` ve beyan alanları silindi; `basamak`, `son_basarili`, `son_bilinen_at`, `sonraki_tekrar`, `takipte`, `egz_dogru`, `egz_yanlis` alanları ve günlükte `basamak_once` eklendi. Beyan ucu silindi.
> - **Egzersizler:** Cevaplar aynı kurala işlenir (`egzersizler/kayit.py`). Liste kelimeleri aynı öncelik sırasıyla sorulur (`sorular.liste_kelimeleri`). "Tekrar çöz" turları işlenmez.
> - **Zorlandıklarım:** Son sonucu "bilemedi" olanlar (`words/listem.py`).
> - **Birim:** `settings.TEKRAR_BIRIMI_SAAT` (24).
> - **Testler:** `learnpass/test_tekrar.py` (Efe'nin 12.10 / 12.40 örneği dahil).
> - **Efe onayladı (30 Eylül):** Girişli kullanıcıda yeni kelimenin seviyesi %60 kendi seviyesi, %25 bir üstü, %15 bir altı (sıklık ağırlıklı). Seviyesi bilinmeyene misafir dağılımı uygulanır.

**Sorun:**
- Tekrar algoritması yok.
- Listeye eklenmeyen bilinmeyen yeni kelime bir daha hiç gelmiyor.
- Rapor "öğrenildi kavramı yok" diyor (Bölüm 17), ama kodda `WordEncounter.is_learned` ve `Declaration.MASTERED` duruyor ve seçimi etkiliyor.

**Önce FSRS kabul edilmişti; aynı gün Efe'nin aşağıdaki kuralı yerine geçti. FSRS kullanılmaz.**

**1. Toplanan bilgi.** L&P'deki kararlar (`unknown`, `misjudged`, `known`) ve egzersizdeki doğru/yanlış cevaplar kullanıcı+kelime başına tutulur:
- **Son karşılaşma zamanı** (dakika hassasiyetinde). L&P ve egzersizler **aynı** zamanı paylaşır.
- Bilmeme / yanılma / yanlış sayıları ve bunlardan **zorlanma oranı**.
- Bilinen kelimelerde **tekrar basamağı** (aşağıda 4).

**2. Kimler aday olur** (L&P'de ve egzersizlerde):
- **Zorlandığı kelimeler:** son sonucu "bilmiyorum", "yanılmışım" ya da yanlış cevap olanlar. Bunlar her zaman adaydır.
- **Bildiği kelimeler:** yalnızca tekrar aralığı dolmuşsa adaydır.

**3. Sıralama.**
1. **En son karşısına çıkma zamanı en eski olan önce.**
2. Zaman eşitse **zorlanma oranı yüksek olan** önce.
3. Hâlâ eşitse **rastgele.**

> **Örnek (Efe):** A–Z kelimeleri 12.40'taki bir egzersizde soruldu. a–z kelimeleri listede, en son aynı gün 12.10'da görüldü. Yeni bir L&P ya da egzersizde **önce a–z** gelir.

Böylece yeni bir tur açıldığında, sistemde başka aday varsa **az önce çıkan kelimeler değil, çıkmayanlar** gelir.

**4. Bilinen kelimelerde 1-3-7-21 kuralı.**
- Kelime bilindikçe bir sonraki tekrarı giderek uzayan aralıkla gelir: **1 → 3 → 7 → 21.**
- Her doğru bilişte bir basamak ilerlenir.

**5. Sıfırlama.**
- Kelime bu zincirin herhangi bir basamağında bilinemezse ("bilmiyorum", "yanılmışım" ya da yanlış cevap), **bütün ilerleme silinir.**
- Kelime hiç bilinmiyormuş gibi zorlandıkları arasına döner (basamak 0).

**6. Önceki kararlardan geçerli kalanlar:**
- Listem'deki her kelime ve L&P'de `unknown` / `misjudged` denen **her kelime** (listede olmasa bile) takip edilir.
- Yeni bir kelimeye ilk seferde "Evet, eminim" denirse kelime takibe girmez, bilinen sayılır.
- **Egzersizler:**
  - Yanlış cevap her zaman "bilemedi" sayılır (sıfırlar).
  - Doğru cevap basamağı yalnızca kelimenin aralığı dolmuşsa ilerletir.
- **Oturum:**
  - 20 kart. Mevcut oran kuralı korunur: varsayılan %70 tekrar / %30 yeni.
  - Günde en çok 15 yeni kelime.
- **"Zorlandıklarım"** filtresi = son sonucu "bilemedi" olan kelimeler.
- **`is_learned` / `MASTERED` kaldırılır.**

**7. Vazgeçilenler:**
- **FSRS.**
- **Mevcut listelerin ilk tekrarlarını 2–4 haftaya yaymak.** Kullanıcı tekrar sayısını görmüyor; sıralama zaten en eskiyi öne alıyor.

**Efe'nin cevapları (29 Eylül):**
- (b) **Aralığın başlangıcı:** Kelimenin çalışmada (L&P ya da egzersiz) **en son görülüp bilindiği andan** itibaren sayılır.
- (c) **21'den sonra:** Kelime **21 günde bir** gelmeye devam eder.
- (e) **Sıfırlama:** Sayaçlar **silinmez**, bilgi korunur. Yalnızca basamak başa döner.

- (a) **Birim: 1 gün** (Efe'nin kararı, 29 Eylül). Aralıklar 1 · 3 · 7 · 21 gündür.
  - Birim ve basamaklar tek bir ayar sabitinde tutulur.
  - Birkaç hafta sonra `EncounterLog` ile basamak başına unutma oranı ölçülüp gerekirse ayarlanır.
- (d) **Listede olup hiç görülmemiş kelimeler EN BÜYÜK önceliktir** (Efe'nin kararı). Bütün sıralamanın önüne geçer, sonra 3'teki sıralama işler.

### 18.3 Misafir (giriş yapmamış) kuralları (Efe'nin kararı)
Genel kural değişir: **giriş gerektiren öğeler misafire gösterilmez.** Gerekli yerlerde bölümün içinde tek bir giriş davet bağlantısı olur. Bölüm 2.3 ve 12.6 bu maddeye göre güncellenecek.

- **Sözlük:**
  - Keşfet | Listem sekme çubuğu misafirde **tamamen kalkar**, sayfa doğrudan Keşfet olur.
  - Keşfet aynen çalışır. Tek fark: **"Listeme ekle" düğmesi görünmez.**
  - Sayfanın **en üstünde** bir giriş davet mesajı durur ("Kelimelerini kaydetmek için giriş yap" gibi).
- **Çalışmalar:**
  - Misafirde yalnızca **Learn & Pass** vardır. Egzersizler sekmesi ve üstteki sekme çubuğu **kalkar**.
  - **Seviye seçici yoktur.**
  - Kelime dağılımı sabittir: **%60 B1 · %20 B2 · %20 C1.** Mesaj şu olmalı: "bir şeyler biliyorsun, bir şeyler de öğreneceksin".
  - Bu dağılım ancak CEFR etiketleri doğrulandıktan (18.16) sonra anlamlı olur.
  - Sayfada bir bağlantı durur: **"Kişisel egzersiz çözebilmek için giriş yap"**.
- **Ana Sayfa:** Görünür (değişiklik yok).
- **Okumalar:** Misafire açık (değişiklik yok).
- **Yazma:**
  - Menüde misafire açılır. **Serbest metin yazma misafirde yoktur, yalnızca diyalog egzersizi vardır.**
  - Şu anlamda bir davet yazısı durur: "Metin yazıp yapay zekâ ile değerlendirilmesini istiyorsan hemen şimdi giriş yapabilirsin".
  - Menüdeki `giris_gerekli` işareti Yazma'dan kalkar.

- **Misafirin diyalogları:** L&P ile aynı dağılım (%60 B1 · %20 B2 · %20 C1). Giriş yapmış kullanıcıda hedef kelime yine listeden gelir (9.2).
- **Kısmen yapıldı (30 Eylül):** L&P'de misafirin seviye seçicisi kalktı; dağılım %60/20/20, sıklık ağırlıklı, nadir tür yok (`tekrar.misafir_kelimeleri`). Sözlük, Çalışmalar sekmeleri ve Yazma kuralları 8. adımda yapılacak.

### 18.4 Telaffuz: Amerikan ve İngiliz düğmeleri (Efe'nin kararı) — **YAPILDI ama kalitesi yetersiz (30 Eylül)**
> **Sorun (Efe, 30 Eylül):**
> - Mac'te US düğmesi "Albert" adlı şaka sesini seçiyordu ("sincap gibi"). Düzeltildi: şaka ve eski sentez sesleri dışlandı, artık Samantha seçiliyor.
> - UK için Mac'teki tek düzgün ses Daniel, o da "scatter"ı yanlış okudu.
> - **Tarayıcı sesi cihazdan cihaza değişiyor ve yanlış okuyabiliyor.** Kalıcı çözüm karar bekliyor:
>   - (A) Tarayıcı sesiyle kalmak.
>   - (B) Wikimedia Commons'taki gerçek insan kayıtları (ücretsiz, CC BY-SA, kaynak gösterilmeli, her kelime yok).
>   - (C) Açık kaynak bir yapay zekâ ses modeliyle (ör. Kokoro, ücretsiz, Mac'te çalışır) bütün kelimelerin US/UK seslerini bir kez üretip dosya olarak saklamak.
>   - (D) Google Cloud TTS'nin ücretsiz kotası (faturalandırma hesabı ister; "harcama yok" kararıyla çelişebilir).
>   - Claude'un önerisi: B + C (önce insan kaydı, yoksa üretilmiş ses). İlk olarak C'yi 20 kelimede deneyip Efe'nin dinlemesi.
>
> **Deneme (30 Eylül):**
> - Kokoro (kokoro-onnx, açık kaynak, ücretsiz, yerel) ile 20 kelime × 4 ses üretildi (`~/LearnVocab-ses-deneme/`, proje dışında).
> - Fonetik kontrol doğru: scatter US skæɾɚ / UK skatə, schedule US skɛdʒuːl / UK ʃɛdjuːl.
> - Dosya başına ~5 KB (Opus), 80 dosya 71 saniyede üretildi.
> - **Efe'nin değerlendirmesi:** bm_george neredeyse bütün kelimelerde çok kötü, diğerleri iyi.
> - **Seçilen sesler: US `af_heart`, UK `bf_emma`** (ikisi de kadın; Claude'un önerisi, Efe US'de erkek sesi isterse `am_michael`).
> - **Efe'nin kararı (30 Eylül):** Yalnızca C (Kokoro). İnsan kayıtları (B) ve erkek sesler **yok**. US `af_heart`, UK `bf_emma`, **MP3** (her cihazda çalışsın diye).
> - **Uygulama:**
>   - Ortak dosya adı kuralı `words/telaffuz.py` (Django'suz): `give-up_us.mp3`.
>   - Üretim betiği `araclar/telaffuz_uret.py`. Kokoro'nun ayrı ortamında çalışır: `~/LearnVocab-ses-deneme/.venv/bin/python araclar/telaffuz_uret.py --model ~/LearnVocab-ses-deneme --paralel 4`. Veritabanını salt okur, var olan dosyayı atlar (yarıda kalırsa devam eder).
>   - Çıktı `media/telaffuz/` (git'e girmez). 13.806 metin × 2 = 27.572 dosya, dakikada ~105 dosya, ~4,5 saat. İlk üretim 30 Eylül'de başlatıldı.
>   - Kart: `{% telaffuz_adresi %}` (words/templatetags/kelime.py) dosya varsa `data-ses` basar. Düğme dosyayı çalar; dosya yoksa ya da çalınamazsa tarayıcı sesine döner.
>   - Canlıda `/media` Apache tarafından sunuluyor (`.htaccess`). Dosyaların sunucuya yüklenmesi geçiş planında (18.30).
>   - **Yeni kelime eklenince** betik yeniden çalıştırılır; yalnızca eksik dosyaları üretir.

> Uygulama: `templates/base/_telaffuz.html` (kartta tür ve seviyenin yanında "US" / "UK" düğmeleri). Ses algılama ve okuma kodu `base/_kelimeKartiJs.html`'de. Cihazda o aksanın sesi yoksa `<html>`'e `ses-us` / `ses-uk` sınıfı eklenmez ve düğme görünmez (CSS: `base/layout.html`). Hız 0,9. Günün kelimesi kartına 18.8 ile eklenecek.

- Kelime kartına (başlıkta, kelimenin yanında) **iki ses düğmesi:** 🇺🇸 Amerikan · 🇬🇧 İngiliz.
- **Altyapı:** Tarayıcının `speechSynthesis` özelliği (`en-US` ve `en-GB` sesleri). Ücretsiz, API yok, dosya saklanmaz.
- **Sınır:** Ses kalitesi ve varlığı cihaza bağlı.
  - iPhone, Mac, Android Chrome ve Windows'ta genelde iki aksan da var.
  - Bazı cihazlarda (özellikle Linux, bazı eski Android'ler) İngiliz sesi olmayabilir. O aksanın sesi yoksa düğmesi gizlenir; hiç İngilizce ses yoksa ikisi de gizlenir.
- Daha sonra düşünülebilir: IPA gösterimi (açık veri, ör. CMUdict ABD telaffuzu). Bu ayrı bir karardır.

### 18.5 Liste düğmesi her yerde aynı (Efe'nin kararı) — **YAPILDI (30 Eylül)**
> Uygulama: `base/_kartListeDugmesi.html` tek biçim (kompakt "+" kalktı). Okuma baloncuğu aynı yazıyı JS ile çiziyor. Misafirde düğme hiç basılmıyor. Listem'deki "Listemden çıkar" Bölüm 5 gereği aynen kaldı.

- Giriş yapmış kullanıcıda kelimenin listeye eklendiği her yerde **aynı "Listeme ekle +" düğmesi** kullanılır. Listedeyse "Listemde ✓" yazar.
- Kare "+" düğmesi kalkar: Türkçe sorgudaki kompakt kartlar, kapalı kart satırları, okuma baloncuğu dahil.
- Misafirde düğme görünmez (18.3).

### 18.6 "Daha basit" kuralı (Efe'nin kararı) — **YAPILDI (30 Eylül)**
> `manage.py veri_tara` (kural: `words/veri_kurallari.py`). Oxford kalibrasyonundan sonra uygulandı. 15.918 ilişkiden **5.989'u silindi** (hedef B2+ ise 4.012; hedef kaynaktan alt seviyede değilse 1.977), 9.929'u kaldı. Kalanlarda anlamca tuhaf olanlar (accompaniment → add gibi) B aşamasında elle taranacak.

Bir "daha basit" ilişkisi yalnızca **iki koşul birden** sağlanırsa kalır:
1. Hedef kelimenin seviyesi **A1, A2 ya da B1**.
2. Hedef, kaynaktan **kesinlikle daha alt** bir seviyede. Aynı seviye de yetmez.

Koşullardan biri sağlanmazsa ilişki **veritabanından tamamen silinir.**
- Sonuç: A1 kelimelerin "daha basit" satırı hiç olmaz. `go (A1) → leave (A2)` silinir.
- **Varsayım (Claude):** Kaynağın seviyesi ilişkinin bağlı olduğu **anlamın** CEFR'idir (anlamda yoksa kelimenin). Hedefin seviyesi hedef kelimenin CEFR'idir.
- **Sıra:** Kural CEFR etiketlerine dayanıyor. Bu yüzden 18.16 (CEFR doğrulaması) **bittikten sonra** uygulanır. Etiketler sonradan değişirse silinen ilişkiler ancak yedekten ya da ham önbellekten (`ara-depo-tam`) geri gelir.

### 18.7 Veritabanı taraması: yanlışlar silinir ya da düzeltilir (Efe'nin kararı) — **A aşaması YAPILDI (30 Eylül)**
> **Sonuçlar:**
> - Kendine bağlanan ilişki, aynı yazımın başka türüne ilişki, yinelenen ilişki / anlam / örnek / eş dizim, boş anlam ya da tanım, anlamsız kelime, örneksiz anlam: **hiç yok (0)**.
> - Kelimesi geçmeyen örnek cümle: 91.106 cümlede **0**. Bulunan 23 şüphelinin hepsi iyelik ekli ("owl's") çıktı.
> - Eş/zıt çakışması: 1 (despairing → hopeless); zıt kaydı silindi.
> - Hassas filtre: anlamlarda 0. Örneklerde 16 eşleşme var, hepsi akademik ya da nötr kullanım ("vulgar words", "sex of each respondent"); dokunulmadı.
> - "papist" (aşağılayıcı, 12.2) silindi.
> - Tek tek düzeltmeler: `words/duzeltmeler/d_2026_09_30.py`. Yedek: `~/LearnVocab-yedekler/db.sqlite3.yedek-20260930-veri-tara-oncesi`.
> - Türkçe yazım denetimi (spylls) bu turda çalıştırılmadı; sözlük dosyası kurulu değil, B aşamasına bırakıldı.
>
> **Sıradaki:** B aşaması (Claude + Efe, elle). Öncelik: ilişkiler ve `learnvocab` etiketli seviyeler.

**Yöntem (Efe'nin kararı, 29 Eylül):**
1. Önce **A**: kural tabanlı kontrollerle mevcut veritabanı ayıklanır.
2. Geri kalanı sonra Efe ile birlikte **B** ile taranır (Claude oturumlarda parça parça okur).
3. **C (LLM API) yapılmayacak.** Harcama yok.

- **Kapsam:** Kelime, anlam, örnek cümle, eş dizim, ilişki (eş/zıt/basit), aile ve ifade verisi.
- **Ne yapılacak:** Yanlış olan alan ya da kayıt silinir. Doğrusu biliniyorsa düzeltilir.
- **Kurallar:**
  - Önce `db.sqlite3.yedek-…` yedeği alınır; yeri 18.13'e göre proje dışıdır.
  - Çalışma `yazayar` kopyasında yapılır.
  - Her partiden sonra özet rapor çıkarılır.
- **Kural tabanlı ve ücretsiz kontroller:**
  - 18.6 kuralı.
  - Kendisine bağlanan ilişkiler.
  - Aynı kelimenin hem eş hem zıt anlamlısı olması.
  - Örnek cümlede kelimenin (ya da çekimli biçiminin) geçmemesi.
  - Boş ya da yinelenen alanlar.
  - Türkçe yazım denetimi (`spylls`).
  - Hassas filtreler.
  - Sıklığı çok düşük aile üyeleri (ör. `goer`).
- **Anlam hataları kuralla yakalanamaz** (bank → Zıt: borrower gibi). Bunlar B aşamasında elle taranır. Öncelik: ilişkiler ve seviye etiketleri (~56 bin ilişki, ~20 bin anlam, ~91 bin cümle).
- 18.6'daki "daha basit" silme kuralı, CEFR doğrulamasından (18.16) sonra uygulanır.

### 18.8 Günün kelimesi ve günün ifadesi (Efe'nin kararı, 29 Eylül)
**Nerede:**
- İki **ayrı** kart: Günün Kelimesi ve Günün İfadesi.
- İkisi de **Ana Sayfa'da** ve **Sözlük › Keşfet'in boş hâlinde** durur.
- Ana Sayfa'da "Bugünün çalışmasına başla" düğmesinin altında, ikinci planda yer alırlar.

**Günün kelimesi nasıl seçilir:**
- Kullanıcının seviyesinde olur. Misafire B1 gelir.
- Kullanıcı onu henüz görmemiş olmalıdır: listesinde olmamalı, L&P'de ya da egzersizde karşısına çıkmamış olmalı.
- Sıklık ağırlığıyla seçilir (18.16). "heath" ya da "humbler" gibi kelimeler gelmez.
- Yalnızca Google'a açık (`noindex` olmayan) kelimelerden seçilir.
- Verisi zengin olmalı: en az 2 örnek cümle ve eş dizim. Seviyesi resmî kaynakla doğrulanmış (`cefr_kaynak` = oxford/cambridge) kelimeler tercih edilir.
- Nadir türler gelmez (18.16/7).
- **Misafirlere** o gün herkese aynı kelime gelir (paylaşılabilir, önbelleğe alınabilir). **Giriş yapmış kullanıcıya** kişiye özel kelime gelir.

**Günün kelimesi kartı:**
- Kelime, seviye rozeti, telaffuz düğmeleri (18.4), tek anlam ve bir örnek cümle.
- Giriş yapmış kullanıcı için "Listeme ekle" düğmesi (18.5).
- **"Biliyordum / Bilmiyordum" düğmeleri.** Cevap L&P verisine yazılır ve son karşılaşma zamanını günceller:
  - "Bilmiyordum" denirse kelime tekrar takibine girer (18.2).
  - "Biliyordum" denirse bilinen sayılır (yeni kelimede ilk "eminim" kuralı).
- Karta dokununca Sözlük'teki tam kart açılır (`/sozluk/<kelime>/`).
- **Kullanıcı kelimeyi listesine ekler ya da "Biliyordum" derse, o gün o kelime bir daha gösterilmez.**

**Günün ifadesi:**
- Claude, 295 ifadeyi **"yaygın bilinen"** ve **"az bilinen"** olarak işaretler (elle, API yok). Modele bir alan eklenir.
- **Herkese aynı ifade** gösterilir (misafir ve giriş yapmış kullanıcı): az bilinenlerden, sırası bir kez rastgele karıştırılmış döngüyle. Az bilinen ifade sayısı N ise döngü N günde bir başa döner.
- Kart: ifade, seviye, Türkçe anlamı, bir örnek. Giriş yapmış kullanıcı için "Listeme ekle".
- Listeye eklenirse o gün bir daha gösterilmez.
- Daha sonra ifade havuzu büyütülecek (Efe).
- **SEO:**
  - İfadelerin de kalıcı adresi olur (`/sozluk/<ifade>/`, 18.15). Kart bu adrese bağlanır.
  - Aynı kurallar geçerli: yalnızca anlamı ve en az 2 örneği olan ifade sayfaları Google'a açılır.
  - "X ne demek" aramaları ifadeler için de gerçek aramalardır. İçeriği dolu sayfalar ceza riski taşımaz.

**Bildirim:** 12.00 bildiriminde günün kelimesi yazar (18.9). Örnek: "Günün kelimesi: resilient · Bugünün çalışması seni bekliyor."

**Efe'nin kararları (29 Eylül):**
- (a) **Kart gizlenince:** Kelime kartının yerinde **"Bugünün kelimesi tamam ✓, yarın yenisi gelecek."** mesajı görünür. Yerine başka kelime gelmez. İfade kartı da listeye eklenince aynı biçimde kapanır ("Bugünün ifadesi tamam ✓").
- (b) **İfadelerde "Biliyordum / Bilmiyordum" yoktur** ve ifadeler için bilme kaydı tutulmaz. İfade kartında yalnızca "Listeme ekle" vardır.

### 18.9 Seri (streak) (Efe'nin kararı, 29 Eylül) — **YAPILDI (30 Eylül)**
> **Kod:**
> - `seri` uygulaması: `GunlukCalisma`, `SeriDurumu`; kural `seri/hesap.py`; yerel saat `seri/zaman.py`; uçlar `/seri/durum/` ve `/seri/saat-dilimi/`.
> - Ana Sayfa kutusu ve takvim: `pages/anasayfa/_seriKutusu.html`. Kapibara simgesi geçici (`base/_kapibara.html`).
> - Alevli çubuk: `base/_alev.html` (L&P ve egzersiz).
> - Metin kontrolü: `texts/gecerlilik.py`.
> - Bildirimler: `bildirim_gonder_hatirlatma` 15 dakikada bir (`bildirimler/CRON.md`).
> - Tarayıcı saat dilimini bir kez gönderir (`base/layout.html`).
> - Testler: `seri/tests.py`, `bildirimler/tests.py`.
>
> **Varsayımlar (Efe onayladı, 30 Eylül):**
> - (1) Serisi 0 olan kullanıcının kaçırdığı gün dondurma hakkı harcatmaz.
> - (2) L&P'de "Geri al" günün sayacını bir azaltır, ama tamamlanmış günü geri almaz.
> - (3) Alev, çubukta günün tamamlanacağı kart hizasında durur. Gün zaten tamamlandıysa çubuğun sonunda yanık durur.

**Seriyi ne devam ettirir** (bir gün "tamamlandı" sayılır):
- **10 L&P kartı**, **ya da**
- **10 egzersiz sorusu**, **ya da**
- **1 metin yazmak** (Yazma), **ya da**
- **1 diyalog yapmak.**
- **Başka hiçbir şey seriyi devam ettirmez:** okuma, kelimeye dokunma, listeye ekleme, günün kelimesi sayılmaz.
- Misafirde seri yoktur.

**Günün sınırı:**
- Gün **tam 00.00'da** biter, **kullanıcının yerel saatiyle.** Geç saat esnekliği yoktur; bu ayrı bir heyecan katıyor (Efe).
- Yerel saat için kullanıcının saat dilimi tarayıcıdan alınıp kaydedilir.

**Çalışma ekranındaki alev (L&P ve egzersizler):**
- Üstteki ilerleme çubuğu normalde **sönük gri** durur. 10. soru hizasında **gri bir alev simgesi** vardır.
- O gün 10 soru sınırına ulaşılınca alev **animasyonla, yanıyormuş gibi tatlı bir şekilde** **sarı-turuncu** tonlara boyanır. Çubuk da bu renge döner.
- L&P ve egzersiz **ayrı sayılır, toplanmaz**; ikisinden **biri** 10'a ulaşınca gün tamamlanır. Çubuk o ekranın kendi sayısını gösterir, ama gün zaten tamamlandıysa alev baştan yanık görünür.

**Dondurma hakkı:**
- Herkes **1 hakla** başlar.
- **Art arda 5 gün** tamamlanınca 1 hak kazanılır.
- En fazla **3 hak** birikir.
- Kaçırılan gün, hak varsa **otomatik** dondurulur ve seri bozulmaz. Birden çok gün kaçırılırsa her güne bir hak harcanır. Haklar biterse seri bozulur.
- **Dondurulan gün seri sayısını artırmaz.** Seri sayısı yalnızca tamamlanan günleri sayar.
- **Hak kazanma:** Ardışık tamamlanan gün sayacı tutulur. Sayaç 5 olunca +1 hak verilir ve sayaç sıfırlanır. Dondurulan (atlanan) gün sayacı sıfırlar.
  - Efe'nin örneği: 1–6. günler yapıldı → 5. günde +1. 7. gün atlandı (donduruldu), sayaç sıfır. 8. günden itibaren yeniden sayılır.
  - 8, 9, 10, 11 ve 12. günler yapılınca **12. gün** +1 hak verilir (Efe onayladı).

**Seri bozulunca:** "Yeni seri başlatmak için hemen alıştırma yap" gibi cesaretlendirici bir dil kullanılır. "Serini kaybettin" denmez.

**Ana Sayfa'daki seri:**
- Seri kutusunda gün sayısı ve yanında **kapibara simgesi** durur. Kapibara çizimi gelene kadar geçici bir simge kullanılır (Bölüm 16).
- **Seriye dokununca** küçük bir **açılır kutu** çıkar. Diğer içeriğin **üzerine biner**; aşağı doğru genişleyen bir alan **değildir**. Kutuda:
  - **Mevcut seri** (gün sayısı)
  - **Dondurma hakkı** sayısı (bu bilgi yalnızca burada görünür)
  - **En uzun seri** rekoru
  - **Takvim:** Günlerin renkleri
    - **Tamamlanan:** sarı-turuncu
    - **Dondurulan:** mavi
    - **Diğerleri:** gri

**Bildirimler** (Bölüm 10'daki "günde tek, 19:00" kararının yerine geçer):
- **Günde iki zaman: 12.00 ve 23.45** (kullanıcının yerel saatiyle). 23.45 bildirimi seriyi kaçırma uyarısıdır. (Önce 23.50'ydi; sunucuda cron en sık 15 dakikada bir çalıştığı için 23.45'e alındı, Efe onayladı 30 Eylül.)
- **Kullanıcı o günü tamamladıysa sonraki bildirim gitmez.**
- **Serisi 0 olan kullanıcıya bildirim gitmez.**
- 12.00 bildiriminde günün kelimesi yer alır (18.8).
- Dondurma hakkı varsa 23.45 bildirimi şöyle der: **"Bugün çalışmazsan 1 dondurma hakkın kullanılacak."**
- Dil cesaretlendiricidir.

**Efe'nin cevapları (29 Eylül):**
- (a) **Sayım:** L&P ve egzersiz toplanmaz; biri tek başına 10 olmalı.
- (b) **L&P:** Kaydırılan her kelime 1 sayılır, bilinen ya da bilinmeyen fark etmez. **Egzersiz:** Cevaplanan her soru 1 sayılır; "yanlışları tekrar çöz" gerekmez. Claude'un varsayımı: tekrar çözülen sorular sayıma girmez.
- (c) **Metin:** Gönderildiği an sayılır, **ama yalnızca geçerli bir metinse** (aşağıya bak).
- (d) **Diyalog:** Cevaplanan 1 diyalog yeter; doğru ya da yanlış önemli değil.
- (e)–(g) Yukarıdaki dondurma kurallarına yazıldı.
- (h) **Takvim:** Önceki aylara oklarla geçilir.
- (i) **Saat:** Kullanıcının yerel saati kullanılır.
- (j) **Seri 0 iken:** Bildirim gitmez.
- (k) **Dondurma uyarısı:** gece uyarısının metni onaylandı (saat 23.45, 18.32).

**Metin geçerlilik kontrolü (Efe'nin kararı, ölçütler Efe onayladı):**
Rastgele yazı yazıp günü tamamlamak engellenir. Metin, seriye sayılmak için gönderildiği anda şu kontrollerden geçmeli. Kontroller Gemini'siz, anında ve ücretsizdir:
1. **Uzunluk:** En az **5 cümle** ve **50 kelime** olmalı.
2. **Gerçek İngilizce:** Kelimelerin en az **%90'ı** gerçek İngilizce kelime olmalı. Ölçüt wordfreq'te sıklığının olması ya da sözlüğümüzde bulunması.
3. **Tekrar yok:** Aynı kelime ya da cümlenin kopyalanıp çoğaltıldığı metinler geçersizdir. Ölçüt: farklı kelime oranı düşükse ya da aynı cümle tekrarlanıyorsa.
4. **Anlamsız harf dizileri yok** ("asdfgh", "aaaaaa").
5. **Aynı metin iki kez sayılmaz:** Kullanıcının önceki bir metninin kopyası sayılmaz.
- Geçmeyen metin yine gönderilebilir ve değerlendirilebilir, ama **seriye sayılmaz.** Kullanıcıya nazikçe nedeni söylenir.
- Gemini değerlendirmesi sonradan metni "değerlendirilemez" bulursa bu bilgi ileride kullanılabilir. Seri anında hesaplandığı için şimdilik yalnızca yukarıdaki kontroller geçerlidir.

### 18.10 L&P ekranı sıfırdan, dikkat dağıtıcısız tasarlanır (Efe'nin kararı)
- **Şu an oturum sırasında ekranda olanlar:** üst çubuk, alt menü, seviye seçici, "Geri al", "Bitir" ve ✕. "Bitir" ile ✕ aynı işi yapan iki çıkış.
- **Hedef:** Oturum sırasında ekranda yalnızca kart, ilerleme ve tek çıkış kalsın.
- **Claude'un önerisi:**
  - Oturumda üst çubuk ve alt menü gizlenir.
  - Tek çıkış ✕ olur.
  - "Geri al" küçük ve ikincil kalır.
  - Seviye seçici oturum ekranından çıkar.
  - Kapibara yer tutucusu çizim gelene kadar gösterilmez.
- Ayrıntılar tasarım oturumunda netleşir.

### 18.11 L&P açıklama kutusu (Efe'nin kararı)
- "Learn & Pass" adı ne yaptığını anlatmıyor. L&P açılış ekranına, L&P'nin ne olduğunu ve nasıl oynandığını anlatan **belirgin bir açıklama kutusu** eklenir.
- Aynı eylemin üç adı var: "Bugünün çalışmasına başla", "Learn & Pass'e başla" ve "Hemen Başla". Adlar tasarım oturumunda tekleştirilir.

### 18.12 Genel tasarım (Efe'nin kararı; ayrıntılar tasarım oturumunda)
- **Tema:** Mevcut indigo-mor-pembe geçişli tema bırakılır, **temiz beyaz bir temaya** geçilir.
- **Yazı boyutu:** **Önemli bilgiler küçük yazıyla yazılmaz.** Efe'nin gözlemi: sayfalar kullanıcı dostu değil. Bütün sayfalar bu gözle yeniden elden geçirilecek.
- **Logo:** Şimdilik dokunulmaz, sonra ele alınacak.
- **Dil:** `<html lang="en">` → **`lang="tr"`**. **YAPILDI (30 Eylül):** `lang` seçili dilden geliyor (`get_current_language`, 18.22'ye hazır). Kelime kartındaki ve okuma baloncuğundaki İngilizce metinler `lang="en"` taşıyor. "BİLMİYORUM" artık doğru görünüyor.
  - Şu an Türkçe büyük harf bozuk: "BİLMİYORUM" ekranda "BILMIYORUM" çıkıyor.
  - Ekran okuyucular ve Google sayfayı İngilizce sanıyor.

### 18.13 Temizlik (Efe'nin kararı)
**Kod:**
- Eski yollar ve ölü kod **tamamen silinir**. Örnekler: `/words/all-words/`, `word-detail`, `add-all-words`, `add-selected-to-my-list`, `add-family-to-my-list`, eski ifade sayfaları, eski profil kelime sayfası ve bunların şablonları.
- **`ai-add` özellikle silinir:** `words/views.py` içindeki uçlar, `words/ai_import.py`, `aiAddWords.html` ve testleri. Veritabanında kullanıcının eklediği (`owner` dolu) kelime yok (29 Eylül: 0), yani veri kaybı olmaz.
- Silmeden önce yeni bileşenlerin kullandığı uçlar taranır; kullanılan bir uç (ör. kartın "Listeme ekle" isteği) silinmez.
- **Kod temizliği yapıldı (29 Eylül):**
  - **Silinen sayfalar ve yollar:** Tüm Kelimeler, kelime detayı, ifade detayı, toplu/seçili/aile ekleme, `ai-add` (4 uç), eski Kelimelerim, elle kelime ekleme/düzenleme/silme, kelime klasörleri (6 uç), toplu kelime silme, eski `profile/myaccount`, `profile/settings`, `profile/texts` yönlendirmeleri ve kullanılmayan `save_mybio`.
  - **Silinen modüller ve şablonlar:** `words/ai_import.py`, `words/addWeeks/`, `LearnVocab/pagination.py`, 19 eski şablon ve `quizzes/` kalıntısı.
  - **Kalanlar:**
    - `words/views.py` artık yalnızca liste ekle/çıkar uçlarını tutuyor (kelime ve ifade; fetch ile JSON döner).
    - `userprofile` yalnızca Profilim ve arkadaşlık için profil görüntülemeyi tutuyor.
    - `comments` ve `friends` kaldı.
  - **Testler:** Silinen özelliklerin testleri kaldırıldı. Eski adreslerin 404 döndüğünü doğrulayan test eklendi (`OldPagesRemovedTests`). 829 test geçiyor.
  - **`encrypted.data`:** `pywebpush`'un test modunda diske yazdığı şifreli Web Push yüküydü (28 Eylül 07:26, bildirim geliştirmesi sırasında). İçinde işe yarar sır yoktu. Silindi, `.gitignore`'a eklendi.
- **Ölü tablolar silindi (29 Eylül, Efe'nin kararı):**
  - `WordList` (kelime klasörleri), `UserMeaning`, `UserWordNote`, `UserExampleSentence`. Migration: `words/0022_olu_kullanici_tablolari`.
  - Yerelde yalnızca 1 klasör kaydı vardı. Yedek: `~/LearnVocab-yedekler/db.sqlite3.yedek-20260929-olu-tablolar-oncesi`.
  - 826 test geçiyor.
  - Not: `Word.owner` / `visibility` / `isBaseWord` alanları görünürlük kuralında hâlâ kullanılıyor. Kullanıcı artık kelime ekleyemediği için ileride sadeleştirilebilir.
- **`comments` ve `friends` kalır.**
- Bölüm 17 ile çelişen kod kalkar (`is_learned`, `MASTERED`; 18.2 ile birlikte).

**Proje klasörü:**
- Proje kökünde ~1,5 GB veri var: 20 veritabanı yedeği, `ara-depo-*` klasörleri ve `pdfler`.
**Efe'nin kararı (29 Eylül):**

| Ne | Karar |
|---|---|
| `pdfler/`, `_arsiv/` | **Kalır.** |
| `ara-depo-tam/`, `ara-depo-pdf-1/` | Efe proje dışına kopyaladı. **Projeden silinir.** |
| `ara-depo-deneme-4…11`, `ara-depo-kontrol-*` | Silinir. |
| `db.sqlite3.yedek-*` (20 dosya) | Silinir. |
| `tmp/` | Silinir. |
| `encrypted.data` | Efe de bilmiyor (büyük olasılıkla başka bir Claude oturumu üretti). **Claude'a inceleme izni verildi.** İncelenip Efe'ye raporlanır; ne olduğu anlaşılmadan silinmez. |

- **Silme Efe'nin Mac'inde yapılır.** CLAUDE.md'deki "bağlı klasörde dosya silinmez" kuralı Claude'un VM'i içindir; burada Efe açıkça izin verdi.
- **Yapıldı (29 Eylül):**
  - Deneme ve kontrol depoları, 20 `db.sqlite3.yedek-*` dosyası ve `tmp/django-cache` silindi (~450 MB).
  - `tmp/restart.txt` (Passenger yeniden başlatma dosyası) bırakıldı.
  - `ara-depo-tam` ve `ara-depo-pdf-1`'i Efe proje dışına taşıdı ve kopyayı doğruladı.
  - **Projede artık `db.sqlite3` dışında veritabanı kopyası yok.** Veri işlerinden (18.6, 18.7) önce proje dışına yedek alınmalı.
- Kalan kalıntı: `quizzes/` klasöründe yalnızca `.DS_Store` ve `__pycache__` var; ölü kod temizliğinde kaldırılır.
- **Silmeden önceki kontrol notu (tarihçe):**
  - Efe'nin aldığı `ara-depo-tam` kopyasının yeri ve boyutu doğrulanır (`anlamlar.jsonl` ~548 MB).
  - Veri işlerinden (18.6, 18.7) önce **proje dışında** tek bir güncel `db.sqlite3` yedeği alınır. Projedeki 20 eski yedek silinince elde başka kopya kalmaz.
- **Dış depo yolu:** `iliskileri_anlama_bagla` ve `kelime_listesi` komutlarının varsayılan `--depo ara-depo-tam` değeri artık çalışmaz. Dış yol `.env`'e (ör. `ARA_DEPO_DIZINI`) ya da belgeye yazılır.

### 18.14 Boş havuzlara 5'er örnek (Efe'nin kararı)
- Boş görünmesinler diye her boş havuza **5 örnek**, Claude tarafından **elle** yazılır. API harcaması olmaz.
- **Havuzlar:**
  - D2 bağlaç/ifade cümleleri
  - D3 eş dizim çeldiricileri
  - D4 seviye testi okuma metinleri
  - D5 okuma kütüphanesi
  - D6 diyaloglar
- Örnekler "örnek" olarak işaretlenir; gerçek havuz gelince değiştirilir.
- Bu karar, 28 Eylül'deki "kütüphaneye yeni metin eklenmez" kararını **yalnızca bu 5'er örnek için** değiştirir.
- **D7 hazır listeler de kapsamda** (Efe'nin kararı, 29 Eylül).
  - Örnek listeler bir kurumun gerçek listesiymiş gibi adlandırılmaz. Örneğin "ODTÜ 101" yerine "Örnek liste: Akademik fiiller" gibi bir ad kullanılır.
  - Kelimeler veritabanındaki mevcut kelimelerden seçilir.

### 18.15 Adresler (URL) ve SEO (Efe'nin kararı, 29 Eylül: kalıcı kelime adresleri onaylandı)

**Temel ilke (Efe):** Google'da çıkmak ürün için kat kat değerli. **SEO bizi kesinlikle cezalandırmamalı.** Her SEO kararında önce ceza riski değerlendirilir; risk varsa temkinli seçenek seçilir.

**SEO güvenlik kuralları (Efe onayladı, 29 Eylül; kademeli dizine alma dahil):**
1. **Kademeli dizine alma:**
   - Sitemap'e ve dizine önce yalnızca **denetimden geçmiş** kelime sayfaları girer: 18.7 A aşamasından temiz çıkan, en az bir anlamı ve örneği olanlar.
   - Denetlenmeyen ya da zayıf sayfalar `noindex` kalır ve denetlendikçe açılır.
   - 16 bin sayfa tek günde açılmaz; partiler hâlinde (ör. önce A1–B1 sık kelimeler) açılır.
2. **Toplu ince sayfa üretilmez:**
   - Türkçe → İngilizce sayfalar (`/sozluk/tr/…`) yalnızca birden çok sonucu ve gerçek içeriği olan sorgular için açılır, otomatik binlerce sayfa üretilmez.
   - Göz atma sayfaları sayfalı olur ve her satırda anlam bulunur; yalnızca bağlantı listesi olmaz.
3. **Aynı içerik tek adreste:**
   - `?q=` adresleri ya kalıcı adrese 301 ile yönlenir ya da `noindex` olur.
   - `www` / `www`'suz ve `http` / `https`'den yalnızca biri yaşar.
4. **Görünmez içerik ya da anahtar kelime doldurma yok.** Başlık ve açıklama sayfanın gerçekten gösterdiğini söyler.
5. **Yapılandırılmış veri yalnızca sayfada görünen içeriği** anlatır.
6. **Veri kalitesi SEO işidir:** 18.7 ve 18.16 bitmeden toplu dizine alma yapılmaz.

**Şu anki sorunlar:**
- Adresler karışık: Çalışmalar `/exercises/learn/` altında, Egzersizler `/egzersizler/`, Yazma `/texts/`, Okumalar `/readings/`, Sözlük `/sozluk/`. `/exercises/` ise 404.
- `robots.txt` ve `sitemap.xml` yok.
- Kelime sonuçları `/sozluk/?q=bank` adresinde duruyor. Google site içi arama sonuç sayfalarını dizine almamayı öneriyor.
- `canonical` adresi istekten üretiliyor (canlıda `http` olarak çıkma riski var).
- Kelime kartlarındaki bağlantılar `?q=` adreslerine gidiyor.

**Claude'un önerdiği adres şeması:**

| Sayfa | Adres | Google'da |
|---|---|---|
| Ana Sayfa | `/` | dizine alınır |
| Sözlük arama | `/sozluk/` | dizine alınır |
| **Kelime** | **`/sozluk/bank/`** (bütün türleri tek sayfada) | **dizine alınır, sitemap'te** |
| İfade / phrasal verb | `/sozluk/give-up/` | dizine alınır |
| Türkçe → İngilizce | `/sozluk/tr/bitirmek/` (2. aşama) | dizine alınır |
| Hazır liste | `/listeler/odtu-101/` | dizine alınır |
| Seviye testi | `/seviye-testi/` | dizine alınır |
| Okumalar | `/okumalar/`, `/okumalar/<metin-adi>/` | kütüphane metinleri dizine alınır |
| Çalışmalar | `/calismalar/`, `/calismalar/egzersizler/` | `noindex` |
| Yazma | `/yazma/`, `/yazma/diyalog/` | `noindex` |
| Hesap | `/giris/`, `/kayit/`, `/ayarlar/`, `/profil/` | `noindex` |
| API | `/api/…` | `robots.txt` ile kapalı |

- **Biçim:** küçük harf, ASCII (`sozluk`, `sözlük` değil), kelimeler tireyle ayrılır, sonda `/` olur.
- **Eski adresler** yeni adreslere **301** ile yönlenir; canlıda dizine girmiş sayfalar kaybolmaz.
- `/sozluk/?q=bank` tam eşleşmede `/sozluk/bank/` adresine yönlenir. Eşleşmeyen aramalar `noindex` olur.

**Bölüm 17 ile ilişkisi (Efe onayladı, 29 Eylül):**
- Bölüm 17'de "her kelimeye ayrı sayfa" fikrinden vazgeçildi. Oradaki sorun eski, kalabalık `word_detail` sayfasıydı.
- Burada **arayüz hiç değişmez**: aynı Sözlük sayfası, üstte arama kutusu, aynı kart bileşeni yerinde açılır. Değişen yalnızca **adres** (`?q=bank` yerine `/sozluk/bank/`).
- Bölüm 17'deki satıra bu açıklama eklendi.

**Yapılacak diğer SEO işleri (Efe'nin kararı: hepsi yapılacaklar listesinde):**
- `sitemap.xml` (Django sitemaps): bütün kelime, ifade, liste ve kütüphane metni sayfaları.
- `robots.txt`: `/api/`, `/admin/` ve hesap sayfaları kapalı; sitemap satırı eklenir.
- `canonical` sabit `https://learnvocab.com.tr/...` olarak üretilir. `www` ve `www`'suz adreslerden biri seçilip diğeri 301 ile ona yönlenir.
- Başlık kalıbı korunur ve genişletilir: "bank ne demek? Türkçe anlamı ve cümle içinde kullanımı".
- Yapılandırılmış veri: schema.org `DefinedTerm` ve `BreadcrumbList` (JSON-LD).
- İç bağlantılar gerçek `<a href="/sozluk/x/">` olur: eş/zıt çipleri, aile, "diğer sonuçlar".
- Taranabilir göz atma sayfaları eklenir: `/sozluk/seviye/b1/`, `/sozluk/harf/a/`.
- Hız (Core Web Vitals sıralamayı etkiler): 18.17 (Tailwind) ve Alpine'in sürümünü sabitleyip siteden sunmak.
- Google Search Console kurulur, sitemap gönderilir. Alan adı doğrulamasını **Efe yapar** (kendi Google hesabıyla, DNS kaydı); Claude adımları hazırlar.
- **Asıl adres: `https://www.learnvocab.com.tr/`** (Efe'nin kararı, 29 Eylül).
  - v1.0 bu adreste yayında ve Google'da bu adresle biliniyor. SEO açısından iki seçenek eşit, yerleşik adresi korumak en güvenlisi.
  - `learnvocab.com.tr` ve `http` istekleri 301 ile buraya yönlenir.
- **Risk:** Google, toplu üretilmiş ve düşük değerli sayfaları cezalandırabilir. Veri kalitesi (18.7) SEO'nun doğrudan parçasıdır. İçeriği çok zayıf kelime sayfalarına `noindex` konması değerlendirilir.

### 18.16 CEFR ve sıklık (wordfreq) (29 Eylül'de konuşuldu; kararlar aşağıda)
**Efe'nin kararları (29 Eylül):**
1. **Etiket düzeltme izni:** Claude yanlış bulduğu CEFR etiketlerini düzeltebilir (ör. "justice C1", "literally C1").
2. **Sayılar silinir.** **Yapıldı (29 Eylül):**
   - Anlamı yalnızca sayı olan 80 kayıt silindi: sayılar, sıra sayıları (seventieth…), kesirler (fourth = dörtte bir), katlar (tenfold). Bağlı anlam, örnek, ilişki ve eş dizimlerle birlikte 1.320 satır.
   - Boş kalan 27 aile de silindi; aralarında daha önce kelimeleri hassas filtreyle silinmiş gay, negro ve shit aileleri vardı.
   - Yedek: `~/LearnVocab-yedekler/db.sqlite3.yedek-20260929-sayilar-oncesi`.
   - **Sayı dışında önemli anlamı olduğu için kalanlar:** first (ilk), second (saniye, ikincil, desteklemek), zero (fiil: odaklanmak), score, teen, fortnight, centenarian, dozen ("dozens of").
3. **Sıklığa göre L&P'de çıkma olasılığı:**
   - Yeni kelime seçiminde her kelimenin çıkma olasılığı sıklığıyla orantılıdır: sık kullanılan sık, az kullanılan az çıkar.
   - Claude'un belirlediği ilk formül: **ağırlık = (max(zipf, 1,5) − 1)²**. Örnekler: zipf 5 → 16 · 4 → 9 · 3 → 4 · 2 → 1. Çok sık bir kelime, çok seyrek bir kelimeden ~60 kat fazla çıkar.
   - Formül ayar sabitinde tutulur, gerekirse değiştirilir.
   - Bu ağırlık yalnızca **yeni** kelime seçimini etkiler. Tekrarlar 18.2'deki kurala göre gelir.
4. **Google'dan gizleme:**
   - Sıklığı çok düşük kelimelerin sayfaları `noindex` olur ve sitemap'e girmez. İlk eşik: **zipf < 2,3**.
   - İçeriği zayıf ya da SEO'ya zarar verebilecek her sayfa da gizlenir (18.15).
5. **İşe yaramaz kayıtlar silinmez:** doorknob, humbler gibi kelimeler kalır. Yalnızca gizlenir ve L&P'de nadir çıkar.
6. **Özel adlar:**
   - Yalnızca özel ad olarak anlam taşıyan ve öğrenci için önem taşımayan kayıtlar Claude tarafından silinebilir.
   - Okurken **kelime anlamıyla** karşılaşılabilecekler (ör. heath = fundalık) silinmez.
   - Özel adlar sıklık hesabından da düşülür.
7. **Nadir türler:**
   - Tanım: kelimenin temel türü A1–B1 iken kendisi C1–C2 olan tür. Örnekler: dog (fiil), tree (fiil), husband (fiil), traffic (fiil).
   - Bu türler Sözlük'te kalır, ama L&P'ye **yalnızca seviyesi C1–C2 olan kullanıcılar** için girer. Diğer kullanıcılarda dolaşıma girmez.
   - Kelimenin temel türleri herkese çıkmaya devam eder.
8. **Resmî kaynakla kalibrasyon:** Oxford 3000/5000 ve Cambridge (English Vocabulary Profile) seviyeleri veritabanıyla karşılaştırılır.
   - `Word` modeline yeni bir alan eklenir: **`cefr_kaynak`** (`oxford` / `cambridge` / `learnvocab`).
   - Resmî kaynakta seviyesi olan kelimeler o seviyeyi alır ve **bir daha incelenmez.**
   - Resmî kaynakta olmayanlar "`learnvocab`" (bizim etiketimiz) olarak işaretlenir. Sonraki CEFR denetimleri yalnızca bunlara bakar.
   - **Sınırlar:**
     - Oxford listeleri ~5.000 kelimeyi kapsar, A1–C1 arasıdır (C2 yok).
     - Cambridge EVP'ye erişim üyelik gerektirebilir; uygulamada erişilebilirliği kontrol edilecek.
     - Veritabanına yalnızca seviye etiketi ve kaynağı yazılır, listelerin kendisi projeye konmaz.

9. **Sıklık ekranda hiç görünmez** (Efe onayladı). Kullanıcı yalnızca CEFR rozetini (B1 gibi) görür. Sıklık yalnızca arka planda kullanılır: L&P olasılığı, şüpheli etiket bulma, Google'dan gizleme.

**Uygulama durumu (30 Eylül):**
- `Word.siklik` (Zipf), `Word.cefr_kaynak` (varsayılan `learnvocab`) ve `Word.nadir_tur` alanları eklendi (`words/0023`).
- `manage.py siklik_hesapla` çalıştırıldı:
  - 16.109 kelime.
  - Sıklık dağılımı: <2,3: 904 · 2,3–3,5: 6.464 · 3,5–5: 7.565 · ≥5: 1.176.
  - **81 nadir tür** (second/dog/bed/tree/window fiil…).
- Kod: `words/siklik.py` (`siklik_puani`, `lp_agirligi`, `nadir_tur_idleri`).
- **Oxford kalibrasyonu yapıldı (30 Eylül):**
  - `pdfler/` altına Oxford'un resmî sitesinden iki PDF indirildi (Efe onayladı; git'e girmez, listeler projeye konmaz).
  - `manage.py oxford_cefr_yukle` (okuyucu `words/oxford.py`) çalıştırıldı:
    - Oxford'da 5.687 (kelime, tür) çifti var; 5.076'sı bizde eşleşti. **3.217'sinin seviyesi değişti (%63)**. En sık kaymalar: B1→B2 686, B2→C1 656, A2→A1 393, B1→C1 391.
    - Bu 5.076 kelime artık `cefr_kaynak = oxford`, bir daha incelenmez.
    - Kalan 11.033 kelime `learnvocab` (bizim etiketimiz); C2'lerin hepsi bunların içinde.
  - Seviyeler değişince nadir tür yeniden hesaplandı: **146**.
  - Yedek: `~/LearnVocab-yedekler/db.sqlite3.yedek-20260930-oxford-oncesi`.
- **Bulgu, sözlükteki boşluk:** Oxford'daki 611 (kelime, tür) çifti bizde yok. Bir kısmı yalnızca tür farkı (above bizde edat var, zarf yok), ama banana, bathroom, because, be gibi **temel A1 kelimeleri eksik**. **Efe'nin kararı (30 Eylül):** Eksik ~600 kelimeyi **Claude elle yazacak** (anlam, açıklama, örnekler; API yok), A1–A2'den başlayarak. **Şimdilik ertelendi**, veri adımından sonra yapılacak. Liste `manage.py oxford_cefr_yukle --dry-run` çıktısından yeniden üretilebilir.
- **Cambridge EVP:** Ücretsiz ama yalnızca sitede arama var, indirilebilir liste yok. ~7.000 kelimeyi almak siteyi otomatik gezmeyi (scraping) gerektirir. Kullanım koşulları doğrulanamadığı için yapılmadı. C2 ve Oxford dışı kelimeler sıklık tutarsızlığı + B aşamasıyla denetlenecek.
- **Özel adlar (30 Eylül):** Yalnızca özel ad olan kayıt bulunamadı; aile hattı bunları zaten almamış. İki tarama yapıldı: örnek cümlelerde hep büyük harfle geçen kelimeler, Türkçe anlamında "soyadı / adı / şehri" geçenler. Bulunanların hepsi gerçek kelime (milliyet, dil, "surname" vb.).
- **Bulgu, büyük harf:** Arab, Arabic, Chinese, Caucasian, Guinean gibi hep büyük harfle yazılan kelimeler veritabanında küçük harfle duruyor.
  - Düzeltmek için önce okuma ekranının kelime sorgusunun (`readings/kelime_sorgu.py`, `text__in`) büyük-küçük harfe duyarsız hâle getirilmesi gerekiyor. Yoksa "Arabic"e dokunan kullanıcı "sözlükte yok" görür.
  - Ertelendi; 18.13 kod işleriyle birlikte yapılır.
  - "oriental" (insanlar için kullanımı eskimiş ve rahatsız edici) de o sırada gözden geçirilecek.

**Önceki not (tarihçe):**
- **Öncelik yüksek.** Şunlar bu karara bağlı: misafir L&P dağılımı (18.3), "daha basit" silme kuralı (18.6), kademeli dizine alma (18.15), yeni kelime seçimi.
- **Bulgular (29 Eylül, salt okunur analiz):**
  - Seviyelerin ortanca sıklığı (Zipf) düzenli azalıyor: A1 4,95 · A2 4,58 · B1 3,86 · B2 3,35 · C1 2,92. Etiketler **genel olarak** tutarlı.
  - C2 (84 kelime) ortancası 3,28, yani C1'den yüksek. Bu kelimelerin çoğu sık kelimelerin nadir türleri.
  - **Sıklık türü (isim/fiil) ayırmıyor:** "dog (fiil) C1", "tree (fiil) C2", "second (fiil) C1" etiketleri **doğru**, ama sıklıkları çok yüksek görünüyor. Sıklık CEFR'in yerine konsaydı bunlar A1 olurdu.
  - **Gerçek etiket hatası örnekleri:** "justice C1", "literally C1" (ikisi de B1–B2 olmalı).
  - **Asıl sorun işe yaramaz kayıtlar:** "handwrite, spectate, humbler, rooter, dully, pillared" gibi sıklığı çok düşük türetilmiş kelimeler B1 etiketli. "gramme, seventieth, bedsheet" ise A1–A2. Bunlar hem öğrenmeye hem SEO'ya zarar verir.
  - Özel adlar sıklığı şişiriyor: "heath" 3,76 çıkıyor (Heath soyadı yüzünden).
- **Claude'un görüşü:** CEFR'i sıklıkla **değiştirmemek**; ikisini birlikte kullanmak.
- **Sıklık zorluk demek değildir:**
  - "however", "despite" çok sık geçer ama B1–B2'dir.
  - "cat", "government"tan seyrek geçer ama çok daha kolaydır.
  - wordfreq kelime biçimini sayar; tür ve anlam ayırmaz ("bank" isim ve fiil aynı sayılır).
  - Film altyazısı ve web ağırlıklı bir kaynaktır.
- **Önerilen yol:**
  1. **CEFR etiket olarak kalır.** Öğrenci ve hazırlık okulları bu dili konuşuyor.
  2. **Sıklık, L&P'de yeni kelime seçiminde sıralama ölçütü olur** (aynı seviyede önce sık kelimeler). "heath" sorunu ve alfabetik kayma böyle çözülür.
  3. **Sıklık tutarsızlık bulucu olarak kullanılır:** çok sık ama C1 etiketli, ya da çok seyrek ama A1–B1 etiketli kelimeler listelenir ve 18.7'deki denetimle düzeltilir.
- Şu anki dağılım şüpheli: C2 yalnızca 84, B2 7.120. Kalibrasyon için kamuya açık kaynaklarla karşılaştırma yapılabilir.

### 18.17 Tailwind (Efe'nin kararı, 29 Eylül: A, Standalone CLI)
- **Sorun Tailwind'in kendisi değil, Play CDN** (`cdn.tailwindcss.com`, `templates/base/layout.html`).
  - Bu betik her sayfa açılışında telefonda sayfayı tarayıp CSS'i **tarayıcıda** üretiyor. Tailwind bunu canlıda kullanılmamak üzere işaretliyor.
  - Büyük bir JavaScript indiriliyor; ilk açılışta stil gecikebiliyor. Bu hem kullanıcıya hem Google'ın hız ölçümüne yansıyor.
  - Başka birinin sunucusuna bağımlılık yaratıyor.
- **Seçenekler:**
  - (A) **Tailwind Standalone CLI** (Node gerekmez, tek dosya). CSS yerelde derlenir; `static/css/site.css` (~15–30 KB) üretilir ve depoya konur. Sunucuda hiçbir şey çalışmaz.
  - (B) `django-tailwind` paketi. Node gerektirir.
  - (C) Tailwind'i bırakıp düz CSS yazmak. ~8.600 satırlık şablonun baştan yazılması demek.
- **Öneri: A.** Beyaz tema (18.12) de aynı derleme adımında kurulur.
- **Alpine:** `unpkg …@3.x.x` sürümü sabitlenmeden çekiliyor. Sürüm sabitlenip dosya `static/` altından sunulur.

### 18.18 Rapor yalnızca mevcut durumu yazar (Efe'nin kararı)
- Rapor ürünün **şu anki** hâlini anlatır. Kodla ya da kendi içinde çelişen yerler düzeltilir.
- Bölüm 18'deki işler uygulandıkça ilgili bölümler güncellenir, "→ 18.x" notları kaldırılır, madde buradan silinip Değişiklik kaydına yazılır.

### 18.19 KVKK
- Efe ayarlayacak. Bölüm 16'daki not geçerli.

### 18.21 Google ile giriş (Efe'nin kararı, 29 Eylül)
- Giriş ve kayıt sayfalarına **"Google ile giriş yap"** eklenir. Mevcut e-posta/şifre girişi kalır.
- **Altyapı (Claude'un önerisi):** `django-allauth` (Google sağlayıcısı).
  - Aynı e-postayla kayıtlı hesap varsa Google girişi o hesaba bağlanır.
  - Google ile ilk girişte kullanıcı adı otomatik üretilir.
  - Kayıt formundaki zorunlu "kur" seçimi Google girişinde sorulmaz (Bölüm 16'daki açık soruyla birlikte ele alınır).
- **Efe'nin yapması gereken:** Google Cloud Console'da OAuth istemcisi oluşturmak. Yönlendirme adresi `https://www.learnvocab.com.tr/…` olur. İstemci kimliği ve gizli anahtar `.env`'e yazılır, sohbete yazılmaz.
- KVKK metninde Google girişi belirtilir (18.19).

### 18.22 Dil seçeneği (Efe'nin kararı, 29 Eylül)
- Siteye **dil seçeneği** eklenecek.
- Bu yüzden arayüz metinleri şablonlara ve koda gömülü kalmaz. Seçili dile göre metinlerin çekileceği **dil dosyaları** hazırlanır.
  - **Claude'un önerisi:** Django'nun kendi çeviri sistemi (`gettext`: `{% translate %}`, `.po`/`.mo` dosyaları, `LocaleMiddleware`).
  - Bundan sonra yazılan her yeni arayüz metni baştan çeviriye hazır yazılır.
  - Mevcut metinler adım adım dönüştürülür.
- **Bağlantılar:**
  - `<html lang>` seçili dile göre gelir (18.12).
  - SEO için her dilin kendi adres öneki ve `hreflang` etiketleri olur (18.15).
- **Efe'nin kararları (29 Eylül):**
  - (a) **Diller:** Hedef **tr · en · de · es · fr**. **Şimdilik tr, en ve de.** es ve fr sonra eklenir.
  - (b) **Kapsam:** **Şimdilik yalnızca arayüz** çevrilir. Kelime anlamları Türkçe kalır.
  - (c) **Adres biçimi:** Türkçe öneksiz kalır, diğer diller önekli olur (`/en/…`, `/de/…`). Her sayfada `hreflang` etiketleri bulunur (Efe onayladı: SEO'da yerleşik adresler bozulmaz, ceza riski yok).

### 18.23 Kayıt formu ve Profilim (Efe'nin kararı, 29 Eylül)
- **Kayıt formunda alınacaklar:** **ad, soyad, e-posta, kullanıcı adı, şifre.**
  - **Şifre tek kez** alınır; "şifreyi tekrar yaz" alanı olmaz. Kullanıcı yanlış yazmasın diye **"göster / gizle"** düğmesi olur.
  - Eski zorunlu **"kur" seçimi kaldırılır.** Seviye, seviye testinden ya da "Seviyemi kendim seçeyim"den gelir (Bölüm 7).
  - Bölüm 16'daki "kur → CEFR eşlemesi" ara kararı bununla birlikte düşer.
- **Profilim'deki "günlük hedef" ayarı** (0/5/10/15/20) **kaldırılır.** Seri sabit kurallarla çalışır (18.9).

### 18.24 Okumalar: sınırlar, saklama ve çöp kutusu (Efe'nin kararı, 29 Eylül)
**Sınırlar:**
- Kullanıcı başına en çok **100 metin**, bunların en çok **15'i PDF**.
- **PDF başına en çok 400 sayfa** (önceden 60).

**Saklama:**
- PDF dosyası zaten **saklanmıyor**; yalnızca çıkarılan metin veritabanına yazılıyor (`UserText.body`).
- **Metinler diskte saklanır (Efe'nin kararı, 30 Eylül):** Sunucudaki MySQL veritabanı en çok 1 GB. Kullanıcı metinleri veritabanına değil, **sıkıştırılmış dosya olarak diske** yazılır (disk limitsiz). Veritabanında yalnızca başlık, dosya adı ve bilgiler durur.
- **Sıkıştırma (Efe onayladı, 29 Eylül):**
  - Metin veritabanına **zlib ile sıkıştırılmış** olarak yazılır. Düz İngilizce metin genelde 3–4 kat küçülür.
  - 400 sayfalık bir kitap (~1 MB metin) ~250–300 KB olur.
  - Okurken metin açılır; kullanıcı farkı görmez.
  - Okuma ekranı uzun metni **bölüm bölüm** gösterir, 400 sayfa tek seferde yüklenmez.
- **PDF dosya boyutu sınırı: 50 MB** (Efe'nin kararı; önceden 10 MB).

**Çöp kutusu (Efe'nin kararı: tasarlanacak):**
- Silinen metinler çöp kutusuna gider. Kullanıcı buradan geri alabilir ya da kalıcı olarak silebilir.
- **Çöpte kalma süresi: 1 hafta.** Sonra kendiliğinden kalıcı olarak silinir (Efe'nin kararı).
- **Çöpteki metinler 100 metin sınırına sayılmaz** (Efe'nin kararı).
- Tasarımı tasarım oturumunda yapılır.

### 18.25 Gelir modeli (Efe'nin kararı, 29 Eylül)
- Site **ücretsiz.** **Ücretli üyelik / premium kesinlikle olmayacak.** (Ücretsiz hesap açma elbette kalır.)
- Site beğenilirse **ileride reklam** alınabilir. Bu ileri bir konu, şimdilik tasarımda reklam alanı ayrılmaz.
- Reklam gelirse L&P ve egzersiz gibi çalışma ekranlarına konmaz (odak, 18.10), sayfa hızını bozmayacak biçimde yerleştirilir (SEO, 18.15). (Claude'un önerisi.)

### 18.26 Gezinme: profil fotoğrafı, Hesap ve Ayarlar (Efe'nin kararı, 29 Eylül)
- Sağ üstteki **dişli (ayarlar) simgesi kalkar.** Yerine kullanıcının **profil fotoğrafı** gelir.
- Profil fotoğrafına dokununca **Hesap** sayfası açılır. **Ayarlar** sayfasına Hesap sayfasından gidilir.
- **Alttaki menü ve sağ üstteki profil fotoğrafı her sayfada sabittir.** Ayarlar ve Hesap sayfaları da dahil, hiçbir sayfada değişmez ya da kaybolmaz.
- Misafirde profil fotoğrafının yerinde "Giriş Yap" durur.
- **Ayarlar sayfasının içeriği** (raporda şimdiye kadar geçen ayarlar):
  - tekrar/yeni oranı
  - egzersizde varsayılan soru sayısı
  - yazma sertliği
  - seviye ve seviye testini tekrarlama
  - bildirimleri açma/kapama
  - dil
  - hesap işlemleri
  - Tasarımı tasarım oturumunda yapılır.
- **Tema düğmesi (Efe'nin kararı, 30 Eylül):**
  - Üst çubuktan kalkar, **Ayarlar'a taşınır**. Ayarlar'da **kolayca görülen** bir yerde durur.
  - **Varsayılan tema cihazın sistem temasıdır** (açık ya da koyu). Kullanıcı Ayarlar'dan değiştirirse onun seçimi geçerli olur.
  - Beyaz tema (18.12) açık temanın yeni hâlidir; koyu tema da korunur.

### 18.27 Seviye testi değişiklikleri (Efe'nin kararları, 29–30 Eylül) — **YAPILDI (30 Eylül; özet soruları havuzu henüz boş)**
> **Kod:**
> - Kural: `seviye/tahmin.py`. Ekran seçimi: `seviye/secim.py`. Özet soruları: `seviye/okuma.py`.
> - Seviyenin kendiliğinden düzelmesi: `seviye/duzeltme.py` + `SeviyeDuzeltmesi` modeli (L&P açılışında ve egzersiz bitişinde çalışır).
> - Davet: `seviye/baglam.py` + `pages/seviye/_davetPenceresi.html`, her sayfada. "Şimdi değil" ve Ana Sayfa'daki eski davet kartı silindi.
> - Migration `seviye/0002`: OkumaSorusu'nun `zorluk` alanı silindi, soru artık `cefr` ile seçiliyor. C2 seçilebilir seviyeler arasına eklendi.
>
> **Kelime havuzu yeniden seçildi (`seviye_kelimeleri_sec`):**
> - A1 · A2 · B1 · B2 60'ar, C1 90, C2 yuvası 30.
> - Kelimeler önce Oxford'la doğrulanmışlardan seçiliyor.
> - C2 yuvası: seviyesi Oxford'la doğrulanmış en zor C1'ler (Zipf >= 2,8). Örnekler: deteriorate, embody, ensue, deprive.
> - İlk denemede eşik 2,3'tü; "concentrator, interfacial" gibi tanınmaz teknik kelimeler geldiği için 2,8'e çıkarıldı.
>
> **Kendi seviyesini seçen kullanıcıya not:** Seçim sayfasında tek satırlık küçük bir not var; kayıttan sonra aynı cümle başarı mesajında görünür. Ayarlar sayfası gelene kadar not Profilim'e bağlanıyor.
>
> **Sıradaki içerik işi:** A1–C2 her seviyeye 50 özet sorusu (Claude elle yazacak, `seviye_okuma_yukle`). Havuz boşken okuma kısmı atlanır ve sonuç kelime ekranlarından belirlenir.

**Davet:**
- Kullanıcı testi yapana kadar **her sayfa açılışında** seviye testi daveti çıkar. Önceki "Şimdi değil → 30 gün" ara kararının yerine geçer.
- **L&P ve egzersiz oturumları sırasında davet çıkmaz.**
- **"Seviyemi kendim seçeyim"** diyen kullanıcıda davet durur. İsterse testi Ayarlar'dan yapar. Seviyesini sistem arka planda kendisi düzeltir (aşağıda).
  - Seviye seçildikten sonra **çok küçük bir not** gösterilir: "Seviyeni istediğin zaman Ayarlar'dan değiştirebilirsin." Not Ayarlar'a bağlanır. Ayrı bir kutu ya da kart değildir, tek satırlık küçük bir yazıdır.

**1. kısım: kelime ekranları** (Bölüm 7'deki ekran düzeninin ve D8'deki "ekran başına 120 kelimelik havuz" ara kararının yerine geçer):

| Ekran | Kelimeler | Sonraki ekran ne zaman açılır |
|---|---|---|
| 1 | 40 kelime: **20 A1 + 20 A2** | İşaretlenen oran **%60'ın üstündeyse** |
| 2 | 40 kelime: **20 B1 + 20 B2** | İşaretlenen oran **%60'ın üstündeyse** |
| 3 | 40 kelime: **30 C1 + 10 C2** | Son ekran |

- %60'ı geçemeyen kullanıcıya sonraki ekran açılmaz.
- Kelimeler sık kullanılan ve seviyesi resmî kaynakla doğrulanmış (18.16) kelimelerden seçilir.
- **C2 yedeği (Efe onayladı):** Veritabanında şu an C2 kelime çok az (84'ten azı, çoğu nadir tür). C2 havuzu resmî kaynakla (Cambridge EVP, 18.16) genişletilene kadar 3. ekrandaki 10 C2 kelimenin yerine **en zor C1 kelimeleri** (sıklığı en düşük, ama Google'a açık ve nadir tür olmayanlar) kullanılır.

**2. kısım: özet soruları** ("Bu 4 cümlelik paragrafı en iyi özetleyen cümle hangisi?"):
- **En çok 3 soru** sorulur. Hangi seviyelerden sorulacağı kelime ekranlarının sonucuna göre belirlenir.
- **Kural:**
  - Geçilen her ekranın **üst** seviyesinden 1 soru.
  - Geçilemeyen ilk ekranın **alt** seviyesinden 1 soru.
  - İstisna: 1. ekran geçilemezse A1 ve A2'den birer soru sorulur, çünkü tek soru yetersiz kalır.

| Kelime ekranlarının sonucu | Sorulan özet soruları |
|---|---|
| 1. ekran geçilemedi | A1 · A2 |
| 1 geçildi, 2 geçilemedi | A2 · B1 |
| 1 ve 2 geçildi, 3 geçilemedi | A2 · B2 · C1 |
| Üçü de geçildi | A2 · B2 · C2 |

- **Havuz:** A1, A2, B1, B2, C1 ve C2 için **50'şer soru** (toplam 300), **Claude tarafından elle yazılır** (API yok). Test sırasında rastgele seçilir. Bu, 18.14'teki "D4'e 5 örnek" maddesinin yerine geçer.

**Sonuç seviyesi (Efe onayladı, 30 Eylül):**
- Kelime ekranlarından bir **başlangıç tahmini** çıkar: son geçilen ekranın üst seviyesi (A2 / B2 / C2). Hiç geçilemediyse A1.
- Özet soruları bu tahmini düzeltir: **doğru cevaplanan en yüksek seviye** sonuç olur.
  - Örnek: 1 geçildi, 2 geçilemedi, A2 ve B1 soruları doğru → **B1**. Yalnızca A2 doğru → **A2**. İkisi de yanlış → **A1**.
- Hiçbir özet sorusu doğru değilse sonuç, sorulan en düşük seviyedir.
- **Özet sorularının doğru cevabı kullanıcıya gösterilmez** (Efe'nin kararı: demoralize etmemek için). Doğru/yanlış işareti de yoktur, test sonuç ekranına geçer.

**Seviyenin kendiliğinden düzelmesi** (Efe'nin kararı; matematik Claude'un önerisi, Efe onayladı):
- Kullanıcının L&P ve egzersizlerde karşılaştığı kelimelerden her seviye için **bilme oranı** hesaplanır.
  - **Bilindi sayılanlar:** L&P'de "Evet, eminim" ve egzersizde doğru cevap.
  - **Bilinmedi sayılanlar:** "bilmiyorum", "yanılmışım" ve yanlış cevap.
- **Seviye başına kural (Efe):**
  - Bilme oranı **%75'in üstünde** → o seviye bitmiştir, gösterdiği seviye bir üsttür.
  - **%35–75** → o seviyededir.
  - **%35'in altında** → bir alt seviyededir.
- **Ağırlıklı ortalama:** Her seviyenin gösterdiği seviye, o seviyede görülen kelime sayısıyla ağırlıklandırılıp ortalanır. Sonuç en yakın seviyeye yuvarlanır. Çok kelime görülen seviyenin sözü daha çok geçer.
- **Kararlılık önlemleri (Claude'un önerisi):**
  - Bir seviye hesaba girmek için en az 20 kelime görülmüş olmalı. Toplam en az 50 kelime yoksa seviye değişmez.
  - Oranlar az veride zıplamasın diye yumuşatılır: (bilinen + 1) / (görülen + 2).
  - Seviye haftada en çok bir basamak değişir.
- **Herkese uygulanır** (Efe onayladı, 30 Eylül): seviyesini kendisi seçenlere de testi yapanlara da. `seviye/duzeltme.py`'deki boş kanca bununla dolar.

### 18.28 Egzersizler: düzensiz fiiller (Efe'nin kararı, 29 Eylül)
- 2. ve 3. hâli kendisiyle aynı olan fiiller (cut, put, hit…) **da sorulur.** Önceki "sorulmuyor" ara kararının yerine geçer.

### 18.29 Bildirim izni akışı (Efe'nin kararı, 29 Eylül)
- **Zamanlama:** Tarayıcının izin penceresinden **önce** küçük bir **ön ekran** çıkar.
  - Bildirimin neden önemli olduğunu kısaca anlatır (seri hatırlatması, günün kelimesi).
  - Üzerinde **kapibara** vardır (kabul oranını artırmak için).
  - Kullanıcı kabul ederse tarayıcının kendi izin penceresi açılır.
- **Ne zaman çıkar:** Kullanıcı birkaç şey yaptıktan sonra: **en az 3–4 egzersiz** çözmüş ve **biraz L&P** yapmış olmalı. Önceki "yalnızca L&P turu bitince" ara kararının yerine geçer.
- **Ayarlar'dan** bildirimler açılıp kapatılabilir.
- **Ölçüt (Efe onayladı, 30 Eylül):** En az **3 tamamlanmış egzersiz oturumu** ve en az **20 L&P kartı.**

### 18.30 Yeni sisteme geçiş planı (konuşulacak; unutulmayacak)
- Efe'nin kararı: **Önce bütün değişiklikler yapılır, her şey bitince** geçiş konuşulur.
- Konuşulacaklar:
  - sözlük verisinin yereldeki SQLite'tan canlıdaki MySQL'e taşınması
  - canlıdaki v1.0 kullanıcı verisinin ne olacağı (Efe: çok az ve önemsiz)
  - geçiş günü ve bakım ekranı
  - eski adreslerin 301 yönlendirmeleri
  - Search Console
  - `www` yönlendirmesi
  - kademeli dizine alma (18.15)
  - `media/telaffuz/` ses dosyalarının (~140 MB, ~27.600 dosya) sunucuya yüklenmesi (18.4)

### 18.31 İstatistik ekranı (admin) (Efe'nin kararı, 29 Eylül)
- **Admin panelinde** bir istatistik ekranı olur.
- **Amaç:** Tekrar biriminin (1 gün, 18.2) ve genel kullanımın doğru çalışıp çalışmadığını anlamak.
- **Gizlilik önceliklidir:**
  - Ekranda **yalnızca toplu sayılar** vardır. Kullanıcı adı, e-posta, yazılan metin ya da kişi bazında kayıt gösterilmez.
  - Çok küçük gruplar (ör. 5 kişiden az) kişiyi belli edebileceği için gösterilmez. (Claude'un önerisi.)
- **Claude'un önerdiği göstergeler:**
  - Tekrar basamağı başına (1-3-7-21) unutma oranı
  - L&P turlarının yarıda bırakılma oranı
  - Günlük/haftalık aktif kullanıcı sayısı
  - Seri uzunluğu dağılımı
  - Bildirim izni kabul oranı
  - Günün tamamlanma oranı

### 18.32 Barındırma sınırları ve sonuçları (Efe'nin kararları, 30 Eylül)
- **Paket:** Veridyen **Senior**.
  - Disk ve trafik limitsiz. **Inode 400.000.** **MySQL veritabanı başına en çok 1 GB** (MariaDB 10.6+).
  - 4 çekirdek, 4 GB RAM. **Cron en sık 15 dakikada bir.**
  - Python sürümü seçilebilir; SSH, Git ve Let's Encrypt var.
- **Sonuçları:**
  - Okuma metinleri diskte sıkıştırılmış dosya (18.24).
  - **Ayrıntılı karşılaşma kayıtları (`EncounterLog`) 90 gün tutulur**, daha eskileri günlük özetlere çevrilir. (Henüz yapılmadı; istatistik ekranıyla birlikte, 18.31.) Tekrar kuralı (18.2) ve istatistik ekranı (18.31) bu özetlerle çalışır. Böylece veritabanı 1 GB'ın altında kalır.
  - Seri kaçırma bildirimi **23.45** (18.9).
  - Ses dosyaları (18.4, seçilirse) sunucuda durabilir: ~28 bin dosya (~70–110 MB) inode sınırının %7'si.
- **Maliyet ilkesi (Efe):** Bu süreçte ek masraf çıkmamalı. Ücretli servis, API ya da hesap gerektiren çözümler önerilmez; ücretsiz ve yerel çözümler tercih edilir.

### 18.20 Önerilen uygulama sırası (Claude'un önerisi)
Her adım ayrı commit, her adımdan sonra testler.

| # | İş | Maddeler | Bekleyen karar |
|---|---|---|---|
| 1 | Dosya temizliği, `encrypted.data` incelemesi, dış yedek | 18.13 | yok |
| 2 | Ölü kod ve eski yollar, `ai-add`, `is_learned` / `MASTERED` | 18.13, 18.2 | yok |
| 3 | `lang="tr"`, liste düğmesi, telaffuz | 18.12, 18.5, 18.4 | yok |
| 4 | **CEFR konuşması** | 18.16 | **Efe ile konuşma** |
| 5 | Veri taraması A + "daha basit" kuralı | 18.7, 18.6 | 4'e bağlı |
| 6 | Tekrar kuralı + yeni L&P akışı + dikkat dağıtıcısız L&P ekranı + açıklama kutusu | 18.2, 18.1, 18.10, 18.11 | ekran tasarımı Efe'ye gösterilir |
| 7 | Misafir kuralları | 18.3 | 4'e bağlı (dağılım) |
| 8 | Adresler ve SEO (kademeli dizine alma) | 18.15 | `www` seçimi; dizine alma 5'ten sonra |
| 9 | 5'er örnek | 18.14 | yok |
| 10 | Tailwind derleme + beyaz tema + yazı boyutları | 18.17, 18.12 | tema tasarımı |
| 11 | Google ile giriş | 18.21 | Efe'nin OAuth istemcisi |

- 1–3 hemen yapılabilir.
- 6'da L&P aynı ekranda hem akış hem tasarım değiştirdiği için tek seferde yapılır.

**Hâlâ açık kararlar:**
- Tema tasarımı (18.12)
- Yeni sisteme geçiş planı (18.30, her şey bitince)

**Kullanıcı verisi notu (Efe, 29 Eylül):**
- Canlıdaki v1.0'da çok az kullanıcı verisi var (çoğu Efe'nin arkadaşlarının kaydı). Sistem baştan değişecek.
- Eski verinin taşınması ve tekrar kuralı için geçmişten tohumlama önemsizdir.
- Eski adreslerin 301 yönlendirmesi yine yapılır, çünkü Google'da dizine girmiş olabilirler.

---

## Değişiklik kaydı
- **2026-09-27:** İlk sürüm. Kaynak: `ozetler/2026-09-26_urun-kararlari.md` (26–27 Eylül konuşmaları).
- **2026-09-28:** D1 yapıldı (migration `words/0020_iliski_anlam`, komut `iliskileri_anlama_bagla`). 56.187 bağ anlama atandı, 512'si birden çok anlamda geçtiği için çoğaltıldı. Silinmiş anlamlardan gelen 44 bağ boş kaldı (kartta görünmez). `confused_with` kelime düzeyinde kaldı. `aile_doldur` artık bağları doğrudan anlama yazıyor; silinmiş anlamın bağını geri kurmuyor.
- **2026-09-28:** Adım 3 (İskelet) yapıldı. Menü `LearnVocab/navigation.py` (Sözlük · Çalışmalar · Ana Sayfa · Okumalar · Yazma; mobilde altta, masaüstünde üstte; içerik `max-w-3xl`). Sözlük iskeleti `/sozluk/` (Keşfet | Listem; şimdilik yalnızca İngilizce tam eşleşme). Ortak kelime kartı `templates/base/_kelimeKarti.html` + veri `words/kart.py` (`kart_verisi`, sabit 8 sorgu). Düzensiz fiil: `inflect.duzensiz_fiil_mi` (veritabanında düzenli fiillerin de v2/v3'ü dolu olduğu için kural çıktısıyla karşılaştırılıyor). Giriş gerekli: `data-giris-gerekli="<neden>"` + `/users/login/?next=…&neden=…` (girişte `next`'e dönülüyor). "Geri al" bildirimi: `window.geriAl.goster(mesaj, fn)`. Ara durum: L&P açılış sayfası girişsiz açık ama misafir kaydırma akışı 6. adımda; o zamana kadar mod düğmeleri girişe yönlendiriyor. Dişli simgesi ayarlar sayfası tasarlanana kadar Profilim'e gidiyor.
- **2026-09-28:** Adım 4–9 yapıldı (her biri ayrı commit). Sözlük ve Listem (`words/arama.py`, `words/listem.py`, `words/hazir_liste.py`, `words/sozluk_views.py`); Learn & Pass (misafir modu, oturum sonu soru, "geçen sefer" kartı); Egzersizler (yeni `egzersizler` uygulaması, `/egzersizler/`); Okumalar (kendi metinlerim, dokun-anlam baloncuğu, `GET /api/kelime/`); Yazma (JSON geri bildirim, sertlik, `yazilari_yeniden_dene`, diyaloglar). `quizzes` uygulaması kaldırıldı (`learnpass/0003`). Efe'nin 28 Eylül kararları ve açık sorular Bölüm 16'da.
- **2026-09-28:** Adım 10–11 yapıldı. Seviye testi (`seviye` uygulaması, `User.cefr`, tek kaynak `users.seviye.kullanici_seviyesi`), yeni Ana Sayfa (`LearnVocab/anasayfa.py`), Bildirimler ve PWA (`bildirimler` uygulaması; kurulum ve cron: `bildirimler/CRON.md`). Uygulama planının 11 adımı tamamlandı; D2–D6 havuzları Efe'nin kararıyla boş, D7 liste verisi yüklenmedi.
- **2026-09-29:** Claude'un eleştirisi ve Efe'nin cevabı sonucunda Bölüm 18 (Yapılacaklar) eklendi; etkilenen bölümlere "→ 18.x" notları kondu. Henüz hiçbir madde uygulanmadı. Bölüm 14'teki test bilgisi düzeltildi (1017 test; Mac komutu eklendi).
- **2026-09-29 (2):** Efe'nin cevapları işlendi:
  - 18.2 FSRS önerisi olduğu gibi kabul edildi.
  - 18.3 misafir L&P ve diyalog dağılımı %60 B1 · %20 B2 · %20 C1; seviye seçici yok; Sözlük'te üstte giriş daveti.
  - 18.6 "daha basit" için ikinci koşul (hedef kaynaktan kesinlikle alt seviye) eklendi.
  - 18.7 yöntem: önce A, sonra B, C yok.
  - 18.9 seri kutusu şimdilik kalıyor.
  - 18.13 dosya kararları.
  - 18.14 D7 dahil.
  - 18.15 kalıcı kelime adresleri onaylandı, SEO güvenlik kuralları eklendi, Bölüm 17'ye açıklama notu kondu.
  - 18.20 uygulama sırası eklendi.
  - Henüz hiçbir madde uygulanmadı.
- **2026-09-29 (3):**
  - 18.2'de FSRS'nin yerini Efe'nin kuralı aldı: en eski görülen önce, sonra zorlanma oranı, sonra rastgele; bilinenlerde 1-3-7-21; bilemezse sıfırlama.
  - 18.13'teki silme yapıldı.
- **2026-09-29 (4):**
  - 18.2'ye Efe'nin (b)(c)(e) cevapları yazıldı; (a) birim ve (d) açık.
  - 18.16 CEFR kararları yazıldı.
  - Sayı kayıtları (80) ve boş aileler (27) veritabanından silindi, 13.1 güncellendi.
  - Yedek proje dışında: `~/LearnVocab-yedekler/`.
- **2026-09-29 (5):**
  - 18.2: birim 1 gün; hiç görülmemiş liste kelimesi en büyük öncelik.
  - 18.15: asıl adres `https://www.learnvocab.com.tr/`; kademeli dizine alma onaylandı.
  - 18.16: sıklık ekranda görünmez.
  - 18.17: Tailwind Standalone CLI onaylandı.
  - 18.21 (Google ile giriş) eklendi.
- **2026-09-29 (6):** 18.8 Günün kelimesi ve ifadesi kararlaştırıldı: seçim kuralları, kart, iki ayrı kart (Ana Sayfa ve Keşfet), herkese aynı az bilinen ifade döngüsü, 19:00 bildirimi.
- **2026-09-29 (7):** 18.8 a–b kararlaştırıldı: tamamlanan kartın yerine "Bugünün kelimesi tamam ✓" mesajı gelir; ifadelerde bilme düğmesi ve kaydı yoktur.
- **2026-09-29 (8):** 18.22 Dil seçeneği eklendi (dil dosyaları, gettext önerisi, açık sorular).
- **2026-09-29 (9):** 18.13 kod temizliği yapıldı (eski yollar, `ai-add`, eski şablonlar, sayfalama, `quizzes` kalıntısı); `encrypted.data` incelendi ve silindi; 829 test geçiyor. Ölü modeller için karar bekleniyor.
- **2026-09-29 (10):** 18.9 Seri kararlaştırıldı: 10 soru / 1 metin / 1 diyalog, 00.00 sınırı, alevli ilerleme çubuğu, dondurma hakları (başlangıç 1, 5 günde 1, en çok 3), takvimli açılır kutu, 12.00 · 19.00 · 23.50 bildirimleri.
- **2026-09-29 (11):** 18.9 ayrıntıları kesinleşti: L&P ya da egzersizden biri tek başına 10, yerel saat, dondurulan gün sayıyı artırmaz, ardışık 5 günde +1 hak, bildirimler 12.00 ve 23.50 (seri 0 ise yok), metin geçerlilik kontrolü eklendi.
- **2026-09-29 (12):** 18.9 hak günü (12) ve metin ölçütleri (5 cümle, 50 kelime, %90) kesinleşti; 18.22 diller (tr, en, de; yalnızca arayüz); 18.23 kayıt formu ve günlük hedefin kaldırılması; 18.24 okuma sınırları, sıkıştırma önerisi, çöp kutusu eklendi.
- **2026-09-29 (13):** Ölü tablolar silindi (`words/0022`, 826 test). 18.24 sıkıştırma, 50 MB, çöp 1 hafta ve sınıra sayılmaz; 18.22 dil adres biçimi onaylandı. Yeni: 18.25 gelir modeli, 18.26 gezinme (profil fotoğrafı → Hesap → Ayarlar), 18.27 seviye testi (%60, her sayfada davet, 6 seviye × 50 okuma sorusu), 18.28 düzensiz fiiller, 18.29 bildirim izni ön ekranı, 18.30 geçiş planı (sonra), 18.31 admin istatistik ekranı.
- **2026-09-30:** 18.26 tema düğmesi Ayarlar'a, varsayılan sistem teması. 18.27 seviye testi yeniden yazıldı: 3 kelime ekranı (20 A1+20 A2 / 20 B1+20 B2 / 30 C1+10 C2, %60 eşiği), en çok 3 özet sorusu (seçim kuralı ve tablo), kendi seçenlerin seviyesinin L&P ve egzersiz verisinden düzeltilmesi. 18.29 bildirim izni ölçütü onaylandı.
- **2026-09-30 (2):** 18.27 kesinleşti: sonuç = doğru cevaplanan en yüksek seviye, özet cevapları gösterilmez, seviye düzeltmesi herkese, C2 yerine en zor C1 yedeği, kendi seçenlere küçük Ayarlar notu.
- **2026-09-30 (3):** Uygulama 1. adım yapıldı: `lang="tr"`, telaffuz düğmeleri (18.4), tek biçim liste düğmesi (18.5). 829 test geçiyor.
- **2026-09-30 (4):** Telaffuz ses seçimi düzeltildi (şaka sesleri dışlandı); tarayıcı sesinin kalitesi yetersiz, kalıcı çözüm 18.4'te karar bekliyor.
- **2026-09-30 (5):** 18.32 barındırma sınırları: metinler diskte, EncounterLog 90 gün + özet, seri uyarısı 23.45. Maliyet ilkesi yazıldı.
- **2026-09-30 (6):** Telaffuz denemesi: Kokoro sesleri iyi, bm_george kötü. Seçim: US af_heart, UK bf_emma.
- **2026-09-30 (7):** Telaffuz: Kokoro ile bütün sözlüğün US/UK MP3'leri üretiliyor (araclar/telaffuz_uret.py); kart önce dosyayı çalıyor, yoksa tarayıcı sesi.
- **2026-09-30 (8):** Veri adımı başladı: siklik / cefr_kaynak / nadir_tur alanları ve siklik_hesapla komutu (81 nadir tür, 904 kelime <2,3).
- **2026-09-30 (9):** Oxford 3000/5000 kalibrasyonu: 5.076 kelime oxford kaynaklı, 3.217 seviye değişti; 611 Oxford kelimesi bizde yok (A1'ler dahil). Cambridge EVP indirilebilir değil, scraping yapılmadı.
- **2026-09-30 (10):** Eksik ~600 Oxford kelimesini Claude elle ekleyecek (ertelendi).
- **2026-09-30 (11):** Veri A aşaması: 'daha basit' kuralı uygulandı (5.989 silindi), veri yapısal olarak temiz, özel ad yok, papist ve 1 eş/zıt çakışması silindi. Büyük harf bulgusu ertelendi.
- **2026-09-30 (12):** Uygulama 3. ve 4. adım yapıldı:
  - Tekrar kuralı (`learnpass/tekrar.py`, `learnpass/0005`); yeni L&P akışı (18.1); egzersiz ve Zorlandıklarım bağlantısı; misafir dağılımı.
  - Seri uygulaması: günlük sayım, yerel saat, dondurma, takvimli Ana Sayfa kutusu, alevli çubuk, metin geçerlilik kontrolü, 12.00 / 23.45 bildirimleri.
  - 865 test geçiyor. Tarayıcıda veritabanı kopyasıyla uçtan uca denendi.
- **2026-09-30 (13):** 18.2 ve 18.9'daki dört varsayım Efe tarafından onaylandı.
- **2026-09-30 (14):** Uygulama 5. adım yapıldı: yeni seviye testi (3 ekran, %60 üstü, özet sorusu seviyeleri, en yüksek doğru), her sayfada davet, seviyenin kendiliğinden düzelmesi, C2 yuvası için Oxford'lu en zor C1'ler. 875 test geçiyor.
