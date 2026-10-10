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
9. Yazılar
10. Bildirimler
11. Chrome eklentisi (v1'de)
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
| Aktif üretim: kelimeyi kullanmak | Yazılar |

**Tasarım ilkeleri:**
- **Az seçenek, güçlü altyapı.** Kullanıcı ekranda az karar verir; kalite arka planda.
- **Net görsel hiyerarşi.** En önemli şey en büyük ve en üstte, detay bir dokunuş uzakta.
- **Cesaretlendirici.** Hiçbir ekran cezalandırıcı hissettirmez. Yanlış cevap öğretir, puan kırmaz.
- **Serbestlik.** Tek zorunlu akış yok. Bütün bölümler her zaman açık, isteyen istediği kadar çalışır. Ana Sayfa bir merkezdir, kapı değildir.
- **Çoğu kullanıcı özelliklerin çoğunu kullanmaz.** Bu yüzden en çok kullanılacak yollar (Learn & Pass, Kısa Sınav, okurken dokun-anlamını-gör) kusursuz olmalı.

---

## 2. Bilgi mimarisi

### 2.1 Menü
Beş bölüm, bu sırayla:

```
Sözlük · Çalışmalar · Ana Sayfa · Okumalar · Yazılar
```

- **Ana Sayfa** menünün ortasındadır.
- Eski "Metinler" bölümünün adı **Yazılar**. Adres ve ad dile göre (Efe'nin kararı, 1 Ekim): Türkçe **`/yazilar/` · Yazılar**, İngilizce **`/en/writings/` · Writings** (çeviri `locale/en/LC_MESSAGES/django.po`). İngilizce yayına alınana kadar `/writings/` Türkçe sayfaya yönlenir. Kodda uygulama adı `texts` olarak kaldı.
- "Hakkında" menüde yer almaz. Yardım bağlantısı Ana Sayfa'dadır.
- Sağ üstte kullanıcının **profil fotoğrafı** durur; dokununca **Hesap** açılır, **Ayarlar**'a oradan gidilir (18.26). Misafirde aynı yerde "Giriş Yap" vardır.

### 2.2 Mobil ve masaüstü
- **Mobil:** menü ekranın altında sabit bir sekme çubuğudur.
- **Masaüstü:** aynı menü üste taşınır. Geri kalan her şey mobil ile aynıdır: aynı kartlar, aynı sıra, aynı bileşenler. Masaüstü için ayrı düzen tasarlanmaz, içerik ortada makul bir genişlikte durur.

### 2.3 Giriş yapmamış ziyaretçi (18.3, uygulandı)
**Kural:** Giriş gerektiren öğeler misafire **gösterilmez**. Bölümün içinde tek bir giriş davet bağlantısı olur.

| Bölüm | Misafir ne görür |
|---|---|
| Ana Sayfa | Kısa tanıtım, "Learn & Pass'e başla", Sözlük arama kutusu, günün kelimesi ve günün ifadesi (düğmesiz), hesap açma daveti. |
| Sözlük | Sekme çubuğu yok, sayfa doğrudan Keşfet. En üstte "Kelimelerini kaydetmek için giriş yap". "Listeme ekle" yok. |
| Çalışmalar | Yalnızca Learn & Pass; sekme çubuğu yok, seviye seçici yok. Kelimeler %60 B1 · %20 B2 · %20 C1. Altta "Kişisel egzersiz çözebilmek için giriş yap". Hiçbir şey kaydedilmez. |
| Okumalar | Açık, yalnızca kütüphane metinleri. "PDF yükle" basılınca giriş sayfasına yönlendirir. |
| Yazılar | Açık, yalnızca **diyalog egzersizi** (hedef kelime %60 B1 · %20 B2 · %20 C1; cevap kaydedilmez, seriye sayılmaz). Serbest yazma yok; yerine "Metin yazıp yapay zekâ ile değerlendirilmesini istiyorsan hemen şimdi giriş yapabilirsin". |

---

## 3. Ana Sayfa (giriş yapmış kullanıcı)


- **Seri (streak):** sayı ve kapibara; dokununca takvimli kutu açılır (18.9).
- **Listemdeki kelime sayısı:** tek sayısal gösterge budur. "Öğrenilen kelime" kavramı yoktur (bkz. Bölüm 17).
- **"Bugünün çalışmasına başla":** büyük düğme, Learn & Pass'e gider.
- **Günün kelimesi ve günün ifadesi:** iki ayrı kart, Sözlük › Keşfet'tekilerle aynı (18.8).
- **Yardım bağlantısı:** "Yardım ve hakkında" sayfasına gider (`/hakkinda/`, 18.33).

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
- **Günün kelimesi ve ifadesi:** 18.8.
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
- **Paylaşılabilir adres:** Her kelimenin kalıcı adresi vardır: `/sozluk/aim/`. `/sozluk/?q=aim` araması tam eşleşmede bu adrese yönlenir (18.15). Arayüz aynıdır; değişen yalnızca adres.

### 4.3 Kelime kartı (en önemli bileşen)
> **→ 18.4:** Telaffuz düğmeleri (Amerikan / İngiliz) eklenecek. **→ 18.5:** Liste düğmesi her yerde aynı "Listeme ekle" olacak. **→ 18.6:** "Daha basit" satırına seviye kuralı gelecek.

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
     - **Kalıp gösterimi (Efe'nin kararı, 7 Ekim):** öğrenci sözlüklerindeki gibi `depend on sb/sth`, `suggest doing sth`, `decide to do sth`, `insist that …`. "+" işareti ve "noun", "gerund" gibi dilbilgisi terimleri kullanılmaz. Listenin altında küçük bir açıklama satırı durur: **"sb: birisi · sth: bir şey"** (`data-kalip-aciklamasi`, İngilizce ve Almanca çevirisiyle). Kural `words/kalip_bicimi.py`'de.
  5. **O anlama özel** eş, zıt ve basit anlamlılar çip satırları olarak: `Benzer: … · Daha basit: … · Zıt: …`
     - Her satırda en fazla 3–4 çip olur. Boş satır hiç gösterilmez.
     - Çipe dokununca o kelimenin kartı açılır.
- **Kartın en altında, bir kez:** **Aile** (see also), yani aynı kelime ailesindeki diğer kelimeler.
- **Örnek cümlede çift tıklama (Efe'nin kararı, 30 Eylül; yapıldı):** Karttaki bir örnek cümlede (ilk örnek, "Daha fazla örnek", kalıp örnekleri, ifade kartı) bir kelimeye **çift tıklanınca o kelime Sözlük'te aranır** ve sayfasına gidilir. Çekimli hâller köke bağlanır ("withdrew" → withdraw). Kod: `base/_kelimeKartiJs.html`, `data-cift-tikla-ara`.
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
  - Sonraki sürüm için: seçilenlerle **"Bunlarla çalış"** (Kısa Sınav başlatır).

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
   - Kapibara balonun yanında durur, arada bir göz kırpar (18.33).
4. Bir kaydırma daha yapılınca sonraki kelimeye geçilir.

**Kurallar:**
- **"Biliyorum" doğrulanmaz.** Kontrol sorusu sorulmaz; kullanıcı gelişmek için geliyor.
- **Her kaydırma anında kaydedilir.** Oturum yarıda bırakılsa bile hiçbir şey kaybolmaz.
- **Bilinmeyen kelimeler listeye otomatik eklenmez.** Oturum sonunda "Bilmediğin N kelimeyi listene ekleyelim mi?" diye sorulur. Oturum yarıda bırakıldıysa bir sonraki girişte "Geçen sefer bilmediğin N kelime" kartı çıkar.
- **Giriş yapmamış ziyaretçi** yalnızca kaydırır; hiçbir şey kaydedilmez (bkz. 2.3).

### 6.2 Egzersizler
Açılışta **iki büyük seçenek** vardır:

| | **Kısa Sınav** | **Deneme Sınavı** |
|---|---|---|
| Kime | Çoğu kullanıcı | Daha çok çalışmak isteyen |
| Soru sayısı | **Tam 10**, sorulmaz | "Kaç soru?" 5 / 10 / 15 / 20 / 25 (varsayılan 10, ayarlardan değişir) |
| Soru tipi | **Yalnızca anlam**, TR→EN ve EN→TR karışık | Aşağıdaki bütün tipler, karışık ya da tek tipe odaklı |
| Kaynak | **Yalnızca kullanıcının listesi** | Tipe göre (tabloya bak) |
| Ayar | Yok, bas ve başla | Tip seçimi ve soru sayısı |

- Liste 10 kelimeden kısaysa Kısa Sınav listedeki kadar soru sorar ve "Listene kelime ekle" daveti gösterir.

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
- **Sınırlar, saklama, bölüm bölüm okuma ve çöp kutusu:** 18.24.
- Kelime sorgulama **API olarak** yazılır; Chrome eklentisi aynı API'yi kullanacaktır.

---

## 9. Yazılar

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

**İzin zamanı:** kapibaralı ön ekranla, kullanıcı birkaç şey yaptıktan sonra (18.29). Reddedilen izin bir daha sorulamaz, bu yüzden zamanlama önemlidir.

**Kullanım:** günde en çok iki bildirim, 12.00 (günün kelimesiyle) ve 23.45, yerel saatle; gün tamamlandıysa ya da seri 0 ise gitmez (18.9).
- Günlük L&P hatırlatması.
- "Yazın değerlendirildi" bildirimi.
- Bildirimler **az ve anlamlı** tutulur.

**Barındırma:** Veridyen Senior cron (en sık 15 dakika) ve HTTPS'i destekliyor (18.32).

---

## 11. Chrome eklentisi (v1'de; Efe'nin kararı, 10 Ekim) — **yazıldı, yayın bekliyor**
- **İşlev:** Herhangi bir sitede İngilizce bir kelimeye **çift tıklayınca** anlam **bizim veritabanımızdan** gelir. Baloncuk Okumalar'dakinin aynısı: kök, numaralı anlamlar, phrasal verb, "Henüz sözlüğümüzde yok".
  - **Hareket çift tıklama** (Efe'nin kararı): Chrome zaten çift tıklamada kelimeyi seçiyor; tek tıklama sitelerin bağlantılarını ve düğmelerini bozardı. Yazı kutularında açılmaz.
  - **Kapanma:** baloncuğun dışında herhangi bir yere (kelimenin kendisi dahil) bir kez tıklayınca, Esc ile ya da kelime ekrandan çıkınca. Aynı anda tek baloncuk.
  - **"Listeme ekle +"** girişliyse; değilse "Giriş yap, listene ekle" sitenin giriş sayfasını yeni sekmede açar.
  - **"Oxford'da ara"** (Efe'nin isteği): Oxford Learner's Dictionaries'te o kelimeyi **aynı sekmede** açar (yeni sekme değil). Kelime bizde yoksa da görünür.
  - **Herkese açık, günlük ya da saatlik sınır yok** (Efe'nin kararı). Yalnızca botlara karşı adres başına dakikada 300 (okul ve yurt ağları için 120'den çıkarıldı).
- **Giriş (Claude'un önerisi, Efe onayladı):** ayrı bir giriş yok. Sitede girişliyse eklentide de girişli: istekler eklentinin arka plan betiğinden atılır; siteye erişim izni olduğu için Chrome CORS uygulamaz ve oturum çerezini gönderir. "+" ucu `POST/DELETE /api/eklenti/listem/<id>/` CSRF jetonu yerine isteğin kaynağına bakar: yalnızca `EKLENTI_KIMLIKLERI`'ndeki eklenti (Origin taklit edilemez, başka site listeye kelime ekletemez).
- **Kod:** `chrome-eklentisi/` (Manifest V3, Türkçe ve İngilizce; baloncuk kapalı Shadow DOM'da, sitenin CSS'iyle karışmaz). Sunucu: `readings/api.py` (`kelime` cevabında `girisli`, `eklenti_listem`). Yerelde deneme ve yayın adımları `chrome-eklentisi/README.md`'de.
- **Ana sayfa:** "Defterin her sitede yanında" bölümü (Okumalar'dan sonra, misafir ve girişli). `EKLENTI_ADRESI` boşsa "Chrome Web Store'da çok yakında", doluysa "Chrome'a ekle".
- **Aydınlatma metni:** eklentinin yalnızca çift tıklanan kelimeyi ve yanındaki en çok beş kelimeyi gönderdiği, sayfa adresini göndermediği yazıldı (18.19).
- **Gereksinimler ve sınırlar:**
  - Yeni sürümün yayında olması: `learnvocab.com.tr`'de şu an eski sürüm var; kelime API'si ve "+" ucu yeni sürümle gelir (geçiş, 18.30).
  - Chrome Web Store'a bir kerelik 5 $ ücret (Efe ödeyecek). Kurulumda "tüm sitelerdeki verileri okuyabilir" uyarısı çıkar; çift tıklamayı her sitede yakalamak için gerekiyor.
  - Chrome'un kendi PDF görüntüleyicisinde ve `chrome://` sayfalarında çalışmaz.
- **Telefon (Efe'nin isteği, 10 Ekim):** telefonda Chrome ve Google uygulaması eklenti desteklemiyor. Yerine **Android paylaş menüsü**: site ana ekrana eklenince (PWA, rapor 10) metni seçip "Paylaş → LearnVocab" denebilir; manifest'teki `share_target` → `GET /paylas/` (`LearnVocab/paylas.py`). En çok 4 kelimeyse sözlük araması, daha uzunsa "Kendi metinlerim"e yapıştırılmış gelir (metin oturumda, adreste değil). Uygulamaların eklediği adres ve tırnaklar atılır. Ana sayfanın eklenti bölümünde anlatılıyor.
  - **Sonraki adımlar (sıra Claude'un önerisi):** seçim menüsünün kendisinde "LearnVocab" satırı için Play Store'da siteyi saran küçük bir Android uygulaması (TWA; bir kerelik 25 $); Firefox eklentisi (bilgisayar ve Android; Listeme ekle için anahtar yöntemi gerekir, Firefox her kurulumda rastgele kimlik veriyor); iPhone ve Safari (yılda 99 $, App Store) talep olursa.

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
6. **Giriş gerektiren öğeler misafire gösterilmez**; bölümde tek bir giriş davet bağlantısı olur (2.3, 18.3). Adresi doğrudan açılan korumalı sayfa "önce giriş yapın" ekranını gösterir.
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
| **D7** | Hazır listeler | ODTÜ, Bilkent, Cambridge vb. listeleri veritabanındaki kelimelerle eşleştirilecek. Eşleşmeyenler raporlanacak. **Bilkent yapıldı (10 Ekim):** ELPP 2025-26'nın beş seviyesi beş liste: Bilkent Elementary 817 · Pre-Intermediate 516 · Intermediate 746 · Upper-Intermediate 660 · Pre-Faculty 695 kelime. Yalnızca başlık kelimeleri alındı (eş dizim sütunu Bilkent'in içeriği, alınmadı); tür PDF'in sütunlarından, İngiliz yazımı Amerikan karşılığına bağlandı. Aynı kelime birden çok seviyede olabilir (Efe'nin kararı). Sözlükte olmayan 64 madde `veri/hazir_listeler/bilkent-sozlukte-yok.txt`'de (give up, find out gibi phrasal verb'ler, credit card gibi birleşik isimler, both / yet gibi temel kelimeler → 18.36). Betik `araclar/bilkent_listesi.py`, dosyalar `veri/hazir_listeler/`. ODTÜ, Cambridge… sonra. **ODTÜ (10 Ekim; 101–501 grupları; 101'in Span 2–4'ü ve 501'in Span 3–4'ü Efe'den gelecek):** her span bir liste: ODTÜ 101 Span 1 (380; OLR 0.5'te hedef altı çizili, RHO'lar kalın, ikisi hafta hafta tek listede) · ODTÜ 501 Span 1 (321) · 501 Span 2 (151) · ODTÜ 201 Span 1 (345) · 201 Span 2 (261) · 202 Span 3 (435) · 202 Span 4 (504) · ODTÜ 301 Span 1 (302) · 301 Span 2 (400) · 302 Span 3 (511) · 302 Span 4 (397) · 401 Span 1 (400) · 401 Span 2 (444) · 402 Span 3 (370) · 402 Span 4 (232 kelime). Bahar döneminde grup adı x02. Sıra kura göre (201'ler 21–24, 301'ler 31–34, 401'ler 41–44, 501'ler 51–). **Speakout A0–A1** (101'in kitabı, Lead-in ve Unit 1–8, 417 kelime; ülke tablosundaki Polish/Turkey/China başka anlamlara bağlanmadı). **High Note 5** (Efe'nin kararı: adı "High Note 5", ünite ünite): 501'de okutulan Pearson ders kitabının listesi; Unit 1–7 bölüm, türü yazan tek kelimeler (474), İngiliz yazımı Amerikan karşılığına bağlandı; fonetik alınmadı; `araclar/odtu_listeleri/high_note.py`. **201'de kalın yok, maddeler kalıp** ("to grow flowers (v phr)"): kalıptaki bütün içerik kelimeleri alınır, be/have/do/get atlanır (Efe'nin kararı: A). **Kelimeler belgedeki kalın yazılardan** alınır (Efe'nin uyarısı: ilk 401 yüklemesi kalıptan tahminle yapılmıştı, bazı kelimeler kaymıştı, ör. "distribution of **wealth**"; aynı gün kalından yeniden yapıldı). Hoca kalın yazmayı unuttuysa Claude'un elle kararı; kalın kalıpta altı çizili ya da B1+ kelimeler; "phrasal verb" etiketli fiil + edat fiile bağlanır (depend on → depend), anlamı ayrılanlar 18.38'e. Kalıplar, tanımlar, örnekler alınmaz. Betikler `araclar/odtu_listeleri/`. **Bölümler** (Efe'nin kararı: metin metin değil hafta hafta): `HazirListeKelimesi.bolum` (`words/0027`), dosyada `## 1`; haftası olmayan kısımlar kendi adıyla (RHO 1, Handout 8, Unit 6, More to Read II), sayfada başlık ve üstte bölüm düğmeleri (`?bolum=`). Bir kelime span içinde ilk geçtiği bölümde durur. Sözlükte olmayanlar `veri/hazir_listeler/odtu-401-sozlukte-yok.txt`, `odtu-301-sozlukte-yok.txt` (çoğu phrasal verb → 18.38). **Liste içi arama** (Efe'nin isteği): liste sayfasında "Bu listede ara"; yazdıkça süzülür (Enter gerekmez), yalnızca o listenin kelimeleri, İngilizcede ya da Türkçe anlamda, baştan eşleşenler önce (`?ara=`). |
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
932 test geçiyor (1 Ekim). Her değişiklikten sonra çalıştırılır.

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
7. **Egzersizler:** Kısa Sınav, ardından Deneme Sınavı (tipler; D2, D3).
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
- **Hazır listeyi topluca listeme ekleme (Efe tekrar konuşmak istiyor, 10 Ekim):** Bölüm 17'de "kullanıcıyı boğar" diye vazgeçilmişti, yerine "Bu listeyle çalış" geldi. Konuşulacak seçenekler: hepsini tek tıkla ekleme (ör. 817 kelime; Listem ve günün tekrarı bir anda dolar); sayfa sayfa ("bu 40'ı listeme ekle"); "bilmediklerimi ekle" (bildiklerini işaretler, gerisi eklenir); tümünü eklerken uyarı. Karar verilene kadar uygulanmaz.
- **Tekrar algoritması (L&P):** (→ 18.2: 29 Eylül'de karar verildi: Efe'nin 1-3-7-21 kuralı) "biliyorum" ve "bilmiyorum" denen kelimeler ne zaman tekrar gelir, birikme nasıl yönetilir.
- **Seri (streak):** → 18.9'da 29 Eylül'de kararlaştırıldı.
- **Ayarlar sayfası:** raporda ayarlara yapılan bütün göndermeler (oran kaydırıcısı, varsayılan soru sayısı, yazma sertliği, seviye, bildirimler, hesap) geçerli ama sayfa henüz tasarlanmadı. Mevcut kullanıcı verisinin taşınması da bu sırada ele alınacak.
- **Kapibara:** çizim tamam (18.33). Video için hareketli hâlleri sonra.
- **Hakkında / yardım içeriği:** ilk sürüm yazıldı (18.33); Efe okuyup düzeltecek.
- **KVKK / gizlilik metni:** ilk sürüm yazıldı (10 Ekim, 18.19). Açık kalanlar orada.

**Claude'un varsayımları** (Efe itiraz etmedi, değişebilir):
- Giriş yapmamış biri "+" düğmesine basarsa girişe yönlendirilir.
- Giriş yapmamış ziyaretçiye L&P ve günün kelimesi B1 civarından gelir. L&P'de kaydedilmeyen bir "seviyeni seç" seçeneği vardır.
- Yazma sertliği yalnızca hata listesini etkiler, puanı etkilemez.

**Efe'nin 28 Eylül kararları:**
- Veri havuzları (D2–D6) için **hiç LLM harcaması yapılmaz**. Yükleme komutları ve biçimler hazır; havuzlar boş, ilgili arayüzler boş hâli gösterir ("Yakında" / "hazırlanıyor").
- `reading-texts/` metinlerine dokunulmaz, kütüphaneye yeni metin eklenmez.
- Hazır liste verisi (ODTÜ, Bilkent, Cambridge…) şimdilik eklenmez; altyapı ve `hazir_liste_yukle` komutu hazır. *(10 Ekim'de değişti: Bilkent listeleri eklendi, D7.)*
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

### 18.3 Misafir (giriş yapmamış) kuralları (Efe'nin kararı) — **YAPILDI (1 Ekim)**
Kurallar 2.3'teki tabloda. Kod:
- Sözlük: `pages/sozluk.html` (misafirde sekme çubuğu yerine `data-misafir-daveti`).
- Çalışmalar: `base/_exerciseTabs.html` misafirde hiç çizilmez; L&P açılışında "Kişisel egzersiz çözebilmek için giriş yap" (`data-egzersiz-daveti`). Misafir L&P dağılımı `learnpass.tekrar.misafir_kelimeleri`.
- Yazılar: menüde giriş işareti kalktı (`LearnVocab/navigation.py`). `texts.views.yazmaSayfasi` misafire diyalog kartı + davet gösterir; `diyalogSayfasi` ve `diyalogCevap` misafire açık (`texts.diyalog.misafir_siradaki`, cevap kaydedilmez). Diyalog havuzu (D6) henüz boş; dolunca kendiliğinden çalışır.

### 18.4 Telaffuz: Amerikan ve İngiliz düğmeleri (Efe'nin kararı) — **YAPILDI (1 Ekim: bütün sözlüğün Kokoro sesleri üretildi)**
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

### 18.7 Veritabanı taraması: yanlışlar silinir ya da düzeltilir (Efe'nin kararı) — **A aşaması YAPILDI (30 Eylül); B aşamasının ilişki kısmı YAPILDI (6 Ekim); tanım, kalıp ve örnek kısmı YAPILDI (7 Ekim)**
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
>
> **B aşaması — eş / zıt / daha basit bağları: YAPILDI (6 Ekim).** Claude bütün bağları elle okudu (API yok). Efe'nin kararı: zayıf ama savunulabilir bağ **silinmez**, `ozetler/zayif-baglar.tsv`'ye yazılır; Efe sonra inceler ya da siler.
> - Kod ve kararlar: `words/duzeltmeler/d_2026_10_06.py`, `veri/iliski_denetimi/*.tsv`. Kararlar kimlikle değil kalıcı anahtarla (tür, kaynak, anlam, hedef) tutulur; `uygula()` hepsini baştan uygular, tekrar çalıştırmak güvenli.
> - **18.6 yeniden uygulandı:** genişletme partileri (18.35) kuralı uygulamadan "daha basit" bağı eklemişti; 1.601 bağ silindi (`kural-1-daha-basit.tsv`).
> - **Tür uyuşmazlığı** (`kural-2-tur.tsv`): kaynakla hedefin türü farklı olan 5.088 bağ silindi (wasteful → spend, thankful → thank), 230'u hedefin aynı yazımlı doğru türüne taşındı.
> - **Elle okuma:** önce öncelikli 24 parti (A1–B1 ve sık kelimeler), sonra kalan 48 parti (~16.800 anlam, B2–C2). Silinenler: eş diye bağlanmış kardeş kavramlar (coffee/tea, sherry/port), üst kavram (sculptor = artist), başka anlama ait bağ, anlamsız zıtlar (viola ≠ …, sermon ≠ silence), "= karşıtı" hataları (unsatisfied = content, unreliable = dependable), aynı kelimenin hem = hem ≈ satırında tekrarı. Cinsiyet çiftleri (stallion ≠ mare) kaldı.
> - **Toplam:** 65.932 bağdan **14.390 silindi**, 51.542 kaldı. Eş 30.358 → 27.108, zıt 20.973 → 15.393, daha basit 14.469 → 8.903. **Zayıf olarak işaretlenen 11.820 bağ** (tekilleştirilmiş) dokunulmadan duruyor.
> - Doğrulama: yedeğe baştan uygulanınca çalışma kopyasıyla birebir aynı sonuç; ana veritabanında ilişki dışında hiçbir tablo değişmedi. 979 test geçiyor.
> - **Okurken görülen anlam hataları** (`anlamlari_duzelt()`): interpret ve occur'da asıl anlam başa alındı; load (fiil), junior, conductor, staggered tanımları düzeltildi; küçük harfli china "Çin" ve guinea "Gine" anlamları ile cheese "para", skinny "parasız" silindi (china B2'ye, guinea B2'ye indi).
> - Yedek: `~/LearnVocab-yedekler/db.sqlite3.yedek-20261006-iliski-temizligi-oncesi`.
>
> **Sıradaki:** Efe `zayif-baglar.tsv`'yi inceler. B aşamasının geri kalanı (seviye etiketleri) açık.
>
> **B aşaması — tanımlar, kalıplar ve kalıp örnekleri: YAPILDI (7 Ekim).** Claude bütün kalıpları anlam anlam elle okudu (API yok). Kod `words/duzeltmeler/d_2026_10_07.py`, gösterim kuralı `words/kalip_bicimi.py`.
> - **Tür hataları (tanım):** sıfat tanımı "to be X", zarf tanımı "to do something in a X manner", isim tanımı fiil gibi yazılmıştı. 840 aday okundu, **667 tanım** düzeltildi (`veri/tanim_denetimi/tur-hatalari.tsv`).
> - **Mekanik biçimleme:** 44.537 kalıbın **21.337'si** yeni gösterime çevrildi (`+ noun` → `sth`, `verb-ing` → `doing sth`); bilgi taşımayan ya da sb/sth ile yazılamayan **7.577 kalıp** silindi (`veri/kalip_denetimi/mekanik-silinen.tsv`).
> - **Elle okuma:** 84 parti (`veri/kalip_denetimi/elle-001…084.tsv`). Silinenler: isim/sıfat anlamına yazılmış fiil kalıbı, başka anlamın kalıbı, yalnızca "nesne alır" diyen kalıp ("repair sth"), bozuk dilbilgisi, şiddet / uyuşturucu / cinsel içerikli kalıp ve örnekler. Düzeltilenler: doğal eş dizime çevrildi ("a horde of sth", "be in limbo", "take sth up a notch"), çoğuna yeni kısa örnek yazıldı. **16.822 kalıp silindi, 9.888 kalıp düzeltildi**; 101 örnek cümle yeniden yazıldı (10'u `**` yıldız temizliği, `elle-ornek-yildiz.tsv`).
> - **Toplam:** 44.537 kalıptan **20.138** kaldı (17.037 anlamda). Efe'nin kararı: zayıf ama doğru kalıp silinmez; **430 kalıp** `ozetler/zayif-kaliplar.tsv`'ye yazıldı.
> - **Bağlayıcı ifadeler:** `Expression.pattern` (293 ifade) yeni gösterime çevrildi: "Cümle. However, cümle." → "… However, …", "despite + isim / -ing" → "despite sth/doing sth". Kaynak `words/ifadeler/veri.py` de güncellendi; yükleyici aynı sonucu üretir.
> - **Hat:** yeni kelimelerin kalıpları `words/enrich/checks.py`'de `bicimle()` ile denetlenir (aile hattı da bundan geçer); uymayan biçimlenir, yazılamayan atılır. Prompt'a gösterim kuralı yazıldı.
> - **Hassas anlamlar:** kalıbı silinen ama anlamı duran hassas kelimeler `ozetler/hassas-anlamlar.txt`'de (Efe karar verecek: kalsın / "kaba" işaretlensin / silinsin).
> - Doğrulama: yedeğe (`~/LearnVocab-yedekler/db.sqlite3.yedek-20261007-tanim-kalip-oncesi`) baştan uygulanınca çalışma kopyasıyla birebir aynı sonuç; ana veritabanında kalıp, örnek, anlam ve ifade dışında hiçbir tablo değişmedi. 980 test geçiyor.
>
> **Sıradaki:** Efe `zayif-kaliplar.tsv` ve `hassas-anlamlar.txt`'yi inceler. Eş dizimler (Collocation) aynı gözle henüz okunmadı.

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

### 18.8 Günün kelimesi ve günün ifadesi (Efe'nin kararı, 29 Eylül) — **YAPILDI (1 Ekim)**
**Uygulama (1 Ekim):**
- Kod: `words/gunun.py`, kartlar `templates/pages/gunun/` (Ana Sayfa ve Keşfet'te aynı kartlar), uç `/api/gunun-kelimesi/cevap/`.
- Giriş yapmış kullanıcının kelimesi `GununKelimesi` tablosuna yazılır (gün boyu değişmesin diye). Gün, kullanıcının yerel günüdür. Misafirin kelimesi saklanmaz; tarihten hesaplanır, önbellekte tutulur.
- **"Google'a açık ve resmî kaynaklı" koşulu kademeli gevşer:** Şu an Google'a yalnızca A1–B1 Oxford kelimeleri açık (18.15). B2 ve üstü kullanıcıya da kelime gelebilsin diye sıra: (1) Google'a açık + Oxford/Cambridge, (2) Google'a açık, (3) Oxford/Cambridge, (4) diğer uygun kelimeler. Partiler açıldıkça kendiliğinden (1)'e döner.
- Aday sayıları (1 Ekim): A1 744, B1 785, B2 1.346, C1 1.045, C2 29.
- **"Bilmiyordum" denince** kart açık kalır, düğmeler gider, "Tekrarlarına eklendi" notu çıkar. Karta bir kez cevap verilir.
- **İfade bilinirliği işaretlendi** (elle, API yok; `words/ifadeler/bilinirlik.py`, `manage.py ifade_bilinirligi`): A1–A2'nin hepsi ve B1–B2'nin sık bağlaçları **yaygın (146)**; geri kalanı **az bilinen (149)**. Günün ifadesi 149 ifadelik döngüden gelir.
- İfade sayfası Google'a ancak Türkçe anlamı ve **en az 2 örneği** varsa açılır (`words/dizine_alma.uygun_ifadeler`).

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
> - Ana Sayfa kutusu ve takvim: `pages/anasayfa/_seriKutusu.html`. Kapibara simgesi yalnızca baş (`base/_kapibara.html`, `poz='bas'`).
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
- Seri kutusunda gün sayısı ve yanında **kapibara simgesi** durur. Simge kapibaranın başıdır (18.33).
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
  - Kapibara balonun yanında göz kırpar; oturum sonunda el sallar (kart yoksa uyur).
- Ayrıntılar tasarım oturumunda netleşir.

### 18.11 L&P açıklama kutusu (Efe'nin kararı)
- "Learn & Pass" adı ne yaptığını anlatmıyor. L&P açılış ekranına, L&P'nin ne olduğunu ve nasıl oynandığını anlatan **belirgin bir açıklama kutusu** eklenir.
- Aynı eylemin üç adı var: "Bugünün çalışmasına başla", "Learn & Pass'e başla" ve "Hemen Başla". Adlar tasarım oturumunda tekleştirilir.

### 18.12 Genel tasarım (Efe'nin kararı; ayrıntılar tasarım oturumunda)
- **Tema:** Mevcut indigo-mor-pembe geçişli tema bırakılır, **temiz beyaz bir temaya** geçilir.
- **Yazı boyutu:** **Önemli bilgiler küçük yazıyla yazılmaz.** Efe'nin gözlemi: sayfalar kullanıcı dostu değil. Bütün sayfalar bu gözle yeniden elden geçirilecek.
- **Seçilen tema (Efe'nin kararı, 1 Ekim): A · Mürekkep.**
  - Renkler: saf beyaz zemin, mürekkep mavisi tek ana renk, sarı "fosforlu kalem" vurgu.
  - Yazı tipleri: kelime başlıkları Source Serif 4, geri kalan Inter.
  - Örnek dosyalar: `ozetler/tasarim-ornekleri/temalar.html` (A ve B yan yana; yazı ölçüleri tablosu) ve `anasayfa.html`.
  - Yazı ölçüleri önerisi (telefon): 46 L&P kelimesi · 34 kelime başlığı · 20 kalın Türkçe anlam · 17 gövde/düğme/örnek · 16 İngilizce tanım · 15 yardımcı bilgi · 13 yalnızca rozet; okuma metni 19.
- **Misafir ana sayfası tanıtım sayfası olur** (Efe'nin kararı, 1 Ekim): ilk kez gelen kişi için daha dolu, görselli.
  - Örnek: `ozetler/tasarim-ornekleri/anasayfa.html`. Görseller sitenin kendi bileşenlerinden çizilmiş ürün görselleri, kapibara geçici taslak.
  - Bölümler: giriş (başlık, "Hemen dene", "Seviyemi öğren", arama) · rakamlar · Sözlük · Learn & Pass · Okumalar · Yazılar · seviye testi · günün kelimesi/ifadesi · hesap çağrısı · alt bilgi.
  - **Beğenilmedi (1 Ekim):** Efe'nin arkadaşları "çok klasik, yapay zekâ ile yapıldığı belli" dedi. Hazır şablon kalıpları (renkli hap etiketler, lekeli kolaj, rakam şeridi, tikli zikzak bölümler) kullanılmaz.
  - Yerine iki konsept (uygulanmadı, Efe seçecek): `konsept-defter.html` (kareli kelime defteri; katlanan sütunla kendini sınama, el yazısı notlar, çizgi kapibara) ve `konsept-oyna.html` (sayfa ziyaretçiye hemen kelime sorar; site ancak 7 kelimeden sonra kendini anlatır).
- **Seçilen yön: Defter (Efe'nin kararı, 2 Ekim).** Site kareli bir kelime defteri gibi görünür. Örnekler `ozetler/tasarim-ornekleri/defter/` altında:
  - Ortak stil `defter.css`, ortak menü ve tema düğmesi `defter.js`.
  - Sayfalar: `index.html` (ana sayfa), `kelime.html` (bank), `learnpass.html`, `okuma.html`, `yazilar.html`.
  - Ana sayfa bölümleri: katlanan defter tablosu, bugünün kelimesi ve ifadesi (yapışkan notlar), seri takvimi, "Defterin yapamadığı dört şey", okuma kupürleri, A1–C2 seviye sekmeleri, hazır liste, sık sorulanlar.
  - **Kural:** El yazısı (Caveat) yalnızca süs ve kısa notlar içindir. Anlam, tanım ve düğme hep düz yazıdır (Inter). Başlıklar Fraunces, okuma ve örnek cümleler Source Serif 4, L&P kelimesi Fredoka.
  - L&P kartı çizgili bir fiş kartıdır; ilerleme çentikle (çetele) gösterilir. Yazılar'da puan öğretmenin kırmızı daireli notu gibidir.
- **Siteye uygulandı (2 Ekim, adım adım):**
  - **Ortak katman:** `static/css/defter.css` (renk değişkenleri, kâğıt zemin, `.lv-*` bileşenleri), `base/layout.html`.
    - Tailwind'in indigo/violet/purple renkleri mürekkep mavisine, gray kâğıt nötrlerine, slate gece defterine bağlandı. Eski sınıflar da defter renginde görünür.
    - Kök yazı boyutu 17 px (`html { font-size: 106.25% }`): bütün rem ölçüleri birlikte büyüdü.
    - Yazı tipleri: Inter, Fraunces, Source Serif 4, Caveat, Fredoka (Google Fonts).
    - Üst çubuk ve alt menü: kâğıt zemin, seçili bölüm mürekkep dalgasıyla ya da fosforlu kalemle işaretli. Logo görseli aynı kaldı; yanındaki yazı "Learn**Vocab**" (Fraunces, sarı vurgulu).
    - PWA tema rengi kâğıt rengi (`#fbfaf5`).
  - **Ana sayfa:** misafir için örnekteki tanıtım sayfası, gerçek verilerle.
    - Defter tablosunun 5 kelimesi `words.gunun.defter_kelimeleri`: o gün herkese aynı, 2 B1 + 3 B2, günün kelimesiyle aynı ölçüt, günün kelimesi hariç. Hiçbir şey kaydedilmez.
    - Okumalar kütüphaneden ilk üç metin; seviye sekmeleri `sozluk_seviye`'ye, hazır liste yayındaki ilk listeye bağlı. Seri takvimi açıkça "örnek" yazar.
    - Girişli kullanıcı: tarih, selam, büyük "Bugünün çalışmasına başla", seri ve liste sayısı kâğıt kartları, günün kelimesi ve ifadesi yapışkan not.
  - **Günün kelimesi ve ifadesi:** her yerde (Ana Sayfa, Sözlük › Keşfet) sarı ve mavi yapışkan not.
  - **Sözlük:** kelime kartı beyaz kâğıt sayfası; kelime Fraunces, tür el yazısı, seviye el çizimi daire, numaralar ve "Daha fazla örnek / Kalıplar" el yazısı, örnek cümle okuma yazısıyla. Keşfet / Listem defter sekmeleri. Arama kutusu kâğıttaki çizgi gibi.
  - **Learn & Pass:** oturum dikkat dağıtıcısız (18.10): üst çubuk ve alt menü gizli, tek çıkış ✕ (hiç kart görülmediyse geri döner, yoksa özet açılır), "Geri al" küçük. Kart çizgili fiş, kararlar damga gibi, kapibara çizgi çizimi konuşma balonuyla.
  - **Okumalar:** metin deftere bantlanmış beyaz sayfa, Source Serif ile; dokunulan kelime sarı kalemle işaretlenir, anlamı sarı not baloncuğunda.
  - **Yazılar:** değerlendirmede puan öğretmenin kırmızı daireli notu; hatalar kırmızı dalgalı çizgi, "İyi yaptıkların" yeşil, "Hatalar" kırmızı kalem.
  - **Bütün diğer ekranlar** (egzersizler, hesap, ayarlar, giriş/kayıt, seviye testi, bildirim ön ekranı): kartlar kâğıt sayfası (`.lv-sayfa`), ana düğmeler mürekkep düğmesi (`.lv-dugme`), sayfa başlıkları Fraunces, boş durumlar el yazısı notu, seviye rozetleri el çizimi daire.
  - Kapibara: 18.33.
- **Sayfalar örneklerdeki gibi baştan kuruldu (2 Ekim, Efe'nin isteği: yalnızca renk değil, düzen de):**
  - **Kelime sayfası** (`pages/words/_madde.html`, görünüm `_madde_baglami`): dev başlık, her tür açık bir defter maddesi (rapor 4.2'deki "ilki açık, diğerleri kapalı" kuralı arama sonuçlarında sürüyor; kelime sayfasında bütün türler açık), örnek cümlede kelime sarı kalemle (`|isaretle` süzgeci), aile ağacı (üyelerin ilk Türkçe anlamıyla), "tekrar" ve "kullan" notları, sözlükte alfabetik komşular (yalnızca dizine açık kelimeler) ve sayfa numarası.
  - **Okumalar:** kütüphane kupür kartları; okuma ekranında A−/A+ yazı boyutu (cihazda saklanır) ve okuma sonu (Learn & Pass'e geçiş, sıradaki metin).
  - **Yazılar:** tarih + büyük başlık, çizgili kâğıt "serbest yazma" kartı, mavi not içinde diyalog önizlemesi, "Yazılarım" defter satırları ve kırmızı daireli puanlar. Serbest yazmada konu el yazısıyla, "kullanmayı dene" yapışkan notu (metinde geçen kelimenin üstü canlı çizilir), çizgili kâğıt yazı alanı.
  - **Learn & Pass açılışı:** büyük başlık, dört küçük kâğıtta bugünün sayıları, fiş destesi görseli, "Hemen Başla", **"Nasıl oynanır?" üç adım (18.11 açıklama kutusu)**, "Neden işe yarar?" yapışkan notta.
  - **Egzersizler, Sözlük (Keşfet), göz atma:** büyük başlıklar; seviyeler renkli defter ayraçları, harfler sözlük kenarı dizini.
  - **Giriş / kayıt:** "Defterine dön" / "Defterini aç" başlıkları, bantlı kâğıt form, kâğıttaki çizgi gibi girdiler (`.lv-girdi`).
- **Egzersiz adları ve açılışı (Efe'nin kararı, 2 Ekim):** "Hızlı Egzersiz" → **Kısa Sınav**, "Tempolu Egzersiz" → **Deneme Sınavı** (kodda `hizli` / `tempolu` değerleri aynı). Açılış: Kısa Sınav sarı yoklama notu; Deneme Sınavı gerçek bir deneme kâğıdı (soru sayısı daire içine alınır, soru tipleri tikli liste, her tipin yanında minicik örnek: `egzersizler.sorular.TIPLER["ornek"]`).
- **Eş / zıt / daha basit sorusu (Efe, 2 Ekim):** ne istendiği büyük ve renkli bir damgayla gösterilir: yeşil "= EŞ ANLAMLISI", kırmızı "≠ ZIT ANLAMLISI", mavi "≈ DAHA BASİT KARŞILIĞI"; altında "“cube” kelimesinin **zıt anlamlısı** hangisi?" (soru verisinde `iliski`: es / zit / basit).
  - Not: zıt anlam bağlarının bir kısmı zayıf (ör. cube ↔ slice, sphere). Veri B aşamasında gözden geçirilecek; dokunulmadı.
- **Kalanlar (tasarım):** egzersiz soru ve bitiş ekranları, seviye testi ekranları, Hesap / Ayarlar için sayfaya özel düzen; logo; Tailwind derlemesi (18.17, Standalone CLI indirmek için Efe'nin izni gerekir).
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

### 18.14 Boş havuzlara 5'er örnek (Efe'nin kararı) — **YAPILDI (1 Ekim)**
**Uygulama (1 Ekim):** Claude elle yazdı ve yükledi; dosyalar `veri/ornek/` (yükleme komutları oradaki README'de). Hepsinin `kaynak` alanında "örnek" yazar.
- D2 bağlaç: 5 cümle (so, although, unless, on the other hand, as a result).
- D3 eş dizim: 5 eş dizim (make friends, make progress, do a favor, have fun, make an effort), her birinde 3 doğrulanmış çeldirici. Doğal okunabilecek adaylar ("have friends", "take a decision" gibi) çeldirici yapılmadı.
- D4 seviye testi: 5 değil, tam havuz yazıldı (301 soru, 18.27).
- D5 kütüphane: her konuda bir metin (hukuk, psikoloji, sosyoloji, antropoloji, eğitim), B1–B2, özgün.
- D6 diyalog: 5 diyalog (apologize, exhausted, reluctant, borrow, delicious).
- D7 hazır liste: "Örnek liste: Akademik fiiller" (20 fiil, hepsi sözlükte eşleşti). *10 Ekim'de kaldırıldı (Efe'nin kararı; dosya `veri/ornek/d7_akademik_fiiller.txt`'de duruyor, sonra yeniden eklenebilir).*
- **Göze çarpan veri sorunu (B aşamasına):** Örnek listede bazı fiillerin ilk anlamı yanlış sırada: "interpret" → önce "çevirmenlik yapmak", "occur" → önce "aklına gelmek". Asıl anlam ("yorumlamak", "meydana gelmek") başa alınmalı.

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

### 18.15 Adresler (URL) ve SEO (Efe'nin kararı, 29 Eylül) — **YAPILDI (30 Eylül; canlıya geçişte yapılacaklar aşağıda)**

**Temel ilke (Efe):** Google'da çıkmak ürün için kat kat değerli. **SEO bizi kesinlikle cezalandırmamalı.** Her SEO kararında önce ceza riski değerlendirilir; risk varsa temkinli seçenek seçilir.

**SEO güvenlik kuralları (Efe onayladı, 29 Eylül):**
1. **Kademeli dizine alma:** Bir kelime sayfası ancak **açılınca** Google'a görünür; açılmayan sayfa `noindex` kalır ve sitemap'e girmez. Sayfalar partiler hâlinde açılır.
2. **Toplu ince sayfa üretilmez.** Göz atma sayfaları sayfalıdır ve her satırda anlam bulunur.
3. **Aynı içerik tek adreste:** `?q=` aramaları ya kalıcı adrese 301 ile gider ya da `noindex` olur. `www`'suz ve `http` adresler asıl adrese yönlenir.
4. **Görünmez içerik ya da anahtar kelime doldurma yok.** Başlık ve açıklama sayfanın gerçekten gösterdiğini söyler.
5. **Yapılandırılmış veri yalnızca sayfada görünen içeriği** anlatır.
6. **Veri kalitesi SEO işidir:** Denetlenmemiş kelimeler toplu açılmaz.

**Asıl adres: `https://www.learnvocab.com.tr/`** (Efe'nin kararı). Kodda `settings.SITE_ADRESI`; canonical, sitemap ve robots.txt buradan üretilir, istekteki adresten değil.

**Adres şeması (uygulandı).** Biçim: küçük harf, ASCII, Türkçe, sözcükler tireyle, sonda `/`.

| Sayfa | Adres | Google'da |
|---|---|---|
| Ana Sayfa | `/` | açık |
| Sözlük (Keşfet) | `/sozluk/` | açık |
| **Kelime** | **`/sozluk/bank/`** (bütün türleri tek sayfada) | açılan partiler açık, gerisi `noindex` |
| İfade / phrasal verb | `/sozluk/give-up/`, `/sozluk/on-the-other-hand/` | kelime gibi |
| Arama sonucu | `/sozluk/?q=…` | tam eşleşme kalıcı adrese 301; gerisi `noindex` |
| Listem | `/sozluk/?sekme=listem` | `noindex` |
| Göz atma | `/sozluk/seviye/b1/`, `/sozluk/harf/a/` (sayfalı: `?sayfa=2`) | açık |
| Hazır liste | `/listeler/odtu-101/` | açık |
| Seviye testi | `/seviye-testi/` (adımları `noindex`) | giriş ekranı açık |
| Okumalar | `/okumalar/`, `/okumalar/<metin-adi>/` | kütüphane metinleri açık; `/okumalar/metinlerim/…` `noindex` |
| Çalışmalar | `/calismalar/`, `/calismalar/learn-pass/<mod>/`, `/calismalar/egzersizler/` | `noindex` |
| Yazılar | `/yazilar/` (İngilizce `/en/writings/`), `/yazilar/yaz/`, `/yazilar/diyalog/` | `noindex` |
| Hesap | `/giris/`, `/kayit/`, `/cikis/`, `/sifremi-unuttum/`, `/sifre-degistir/`, `/profil/` (Hesap), `/ayarlar/` | `noindex` |
| Hakkında | `/hakkinda/` | açık |
| Uçlar (JSON, kart parçası) | `/api/…` | `robots.txt` ile kapalı |
| Kökte duranlar | `/robots.txt`, `/sitemap.xml`, `/sw.js`, `/manifest.webmanifest`, `/admin/` | — |

**Nasıl çalışıyor (kod):**
- **Beyaz liste** (`LearnVocab/seo.py`, `DIZINE_ACIK`): Yalnızca listedeki sayfalar Google'a açıktır. Listede olmayan her şey ve her hata sayfası kendiliğinden `noindex` alır (hem `X-Robots-Tag` başlığı hem `<meta name="robots">`). Yeni eklenen bir sayfa, listeye yazılmadıkça kapalı kalır.
- **`robots.txt` yalnızca `/admin/` ve `/api/`'yi kapatır.** Hesap, Çalışmalar ve Yazılar sayfaları `robots.txt` ile kapatılmaz; çünkü Google `noindex`'i ancak sayfayı açabilirse görür. (İlk plandaki "hesap sayfaları robots.txt ile kapalı" maddesi bu yüzden `noindex`'e çevrildi.)
- **canonical** ortak başlıkta (`base/layout.html`) üretilir. Sorgu parametreleri atılır; yalnızca `sayfa` kalır.
- **Kelime sayfası** (`words.sozluk_views.sozluk_kelime`): Arayüz Sözlük sayfasının aynısıdır; üstte arama kutusu, altında kartlar. Eklenen tek görünür şey kartların üstündeki küçük konum satırıdır: `Sözlük › A1 kelimeleri › bank`.
  - Başlık: "bank ne demek? Türkçe anlamı ve cümle içinde kullanımı — LearnVocab Sözlük".
  - Açıklama: sayfadaki Türkçe anlamlar ve ilk örnek cümle.
  - Yapılandırılmış veri: `DefinedTerm` ve `BreadcrumbList` (JSON-LD); ikisi de sayfada görünen içerikten üretilir.
  - Adres yazımdan üretilir (`words/adres.py`, `Word.slug` / `Expression.slug`). `/sozluk/Bank/` küçük harfe 301 ile gider. Olmayan kelime 404 döner (benzer kelimeler gösterilir).
  - Çekimli hâl (`?q=went`) ve Türkçe sorgu (`?q=bitir`) yönlenmez; arama sayfasında `noindex` olarak gösterilir.
- **İç bağlantılar** gerçek `<a href="/sozluk/x/">` bağlantılarıdır: eş / zıt / basit çipleri, aile, "Diğer sonuçlar", anlık öneri, günün kelimesi.
- **Göz atma sayfaları** (`words/gozat.py`): Her satırda kelime, tür, Türkçe anlam ve seviye var; 100'er kelime. Sıklığı 2,3'ün altındaki kayıtlar listelenmez. Bağlantıları Keşfet'in boş hâlinin en altında ("Kelimelere göz at").
- **`sitemap.xml`** (`LearnVocab/seo_views.py`): sabit sayfalar, göz atma sayfaları, **açılmış** kelime ve ifade sayfaları, yayındaki hazır listeler, kütüphane metinleri.
- **Eski adresler** (`LearnVocab/eski_adresler.py`): v1.0'ın ve geliştirme sırasındaki İngilizce sayfa adresleri yenilerine 301 ile gider (`/users/login/` → `/giris/`, `/exercises/learn/` → `/calismalar/`, `/texts/` → `/yazilar/`, `/readings/` → `/okumalar/` …). v1.0'daki `/words/word-detail/<id>/` adresleri Sözlük'e gider; o kimlikler yeni veritabanında geçerli değil. POST ile çalışan eski uçlar yönlenmez.
- **`www` ve `https`:** Canlıda `PREPEND_WWW` ve `SECURE_SSL_REDIRECT` açık; `learnvocab.com.tr` ve `http` istekleri asıl adrese 301 ile gider.
- **Diller (18.22):** Bütün sayfalar dil önekli (`i18n_patterns`; Türkçe öneksiz). **Türkçe, İngilizce ve Almanca yayında** (`/en/…`, `/de/…`); her sayfada `hreflang` (tr, en, de, x-default = Türkçe) var. `sitemap.xml` her dilin adresini ayrı yazar ve her birine `xhtml:link` ile diğer dillerin karşılığını ekler. **Çevirisi bitmemiş dil eklenmez**: çevirisiz `/es/` sayfaları Türkçe sayfaların kopyası olur. Bir dil geçici olarak kapatılacaksa `.env`'de `YAYIN_DILLERI=tr` gibi verilir.

**Kademeli dizine alma (uygulandı):**
- Alan: `Word.dizinde` ve `Expression.dizinde` (admin'de "Google'a açık"). Kurallar `words/dizine_alma.py`, komut `manage.py dizine_ac`.
- **Açılabilme koşulu:** ortak sözlükte olmak, Türkçe anlamı + İngilizce açıklaması + en az bir örnek cümlesi olmak, sıklığı 2,3 ve üstü olmak (18.16). Bir sayfada türlerden biri açıksa sayfa açıktır.
- **1. parti açıldı (30 Eylül): A1–B1, seviyesi Oxford'la doğrulanmış 2.476 kayıt = 2.080 sayfa.**
- **Bekleyenler:** B2 Oxford 1.423 · C1 Oxford 1.177 · bizim etiketimizle A1–C2 10.129 · ifadeler 295. Uygun olmayan (seyrek) 903.
- **Önerilen sıra:** B2 Oxford → C1 Oxford → ifadeler → bizim etiketli kelimeler (18.7 B aşamasındaki elle kontrolden sonra, seviye seviye). Partiler arasında Search Console'da "Dizine eklenen sayfalar" ve "Taranan ama dizine eklenmeyen" sayıları izlenir.
- Komut örnekleri: `dizine_ac` (durum), `dizine_ac --seviye B2 --kaynak oxford --dry-run`, `dizine_ac --ifadeler`, `dizine_ac --kapat-hepsi`.

**Henüz yapılmayanlar:**
- **Türkçe → İngilizce sayfalar** (`/sozluk/tr/bitirmek/`): 2. aşama. Yalnızca birden çok sonucu olan gerçek sorgular için açılacak; otomatik binlerce sayfa üretilmeyecek.
- **Hız:** Tailwind derlemesi ve Alpine'in siteden sunulması (18.17).
- **Canlıya geçişte (18.30):**
  - Google Search Console: alan adı doğrulamasını **Efe yapar** (kendi Google hesabıyla, DNS'e TXT kaydı). Sonra `https://www.learnvocab.com.tr/sitemap.xml` gönderilir.
  - `http://learnvocab.com.tr` isteği şu an iki adımda yönleniyor (önce `https`, sonra `www`). Sunucuda (`.htaccess`) tek adıma indirilir.
  - Canlıdaki v1.0 adreslerinden birkaçı elle denenir (301 ve hedef doğru mu).

**Bölüm 17 ile ilişkisi (Efe onayladı, 29 Eylül):** Bölüm 17'de vazgeçilen şey eski, kalabalık `word_detail` sayfasıydı. Burada arayüz değişmedi; değişen yalnızca adres.

**Risk:** Google, toplu üretilmiş ve düşük değerli sayfaları cezalandırabilir. Veri kalitesi (18.7) SEO'nun doğrudan parçasıdır; bu yüzden denetlenmemiş kelimeler kapalı tutuluyor.

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
- **Eksik Oxford kelimeleri eklendi (1 Ekim):** Claude elle yazdı (API yok): **522 kelime** (A1 100 · A2 62 · B1 53 · B2 110 · C1 197). Her birinde Türkçe anlam, İngilizce açıklama ve örnek cümleler var; seviye kaynağı `oxford`. Dosyalar `veri/oxford_eksik/*.jsonl`, yükleme `manage.py elle_kelime_yukle` (var olanı atlar; `be`, `have` gibi kurala uymayan çekimler elle verilir).
  - **Eklenmeyenler (~100):** İngiliz yazım farkları (colour, centre, favourite, analyse, jewellery, judgement… — Amerikan yazımı sözlükte var); zaten ifade kartı olarak bulunan bağlaçlar (and, because, however, although…; bunların bağlaç dışı anlamları — for "için", as "olarak", so "çok", once "bir kez" gibi — kelime olarak eklendi); hassas kelimeler (rape, abortion, sexual, lesbian; "gay" daha önce Efe'nin kararıyla silinmişti); "born" (fiil; sıfatı var) ve PDF'ten yanlış okunan "diplomatic" (isim).
  - Ay ve gün adları büyük harfle yazıldı (April, Monday…); CD, DVD, TV, IT, OK, AIDS da öyle.
  - A1–B1 olanlar kademeli dizine almanın 1. partisine katıldı.
  - Bu kelimelerin telaffuz dosyaları da üretildi (1 Ekim).
- Eksik listesi `manage.py oxford_cefr_yukle --dry-run` ile yeniden üretilebilir (şu an 101; yukarıda sayılan bilinçli olarak eklenmeyenler).
- **Cambridge EVP:** Ücretsiz ama yalnızca sitede arama var, indirilebilir liste yok. ~7.000 kelimeyi almak siteyi otomatik gezmeyi (scraping) gerektirir. Kullanım koşulları doğrulanamadığı için yapılmadı. C2 ve Oxford dışı kelimeler sıklık tutarsızlığı + B aşamasıyla denetlenecek.
- **Özel adlar (30 Eylül):** Yalnızca özel ad olan kayıt bulunamadı; aile hattı bunları zaten almamış. İki tarama yapıldı: örnek cümlelerde hep büyük harfle geçen kelimeler, Türkçe anlamında "soyadı / adı / şehri" geçenler. Bulunanların hepsi gerçek kelime (milliyet, dil, "surname" vb.).
- **Büyük harf düzeltildi (1 Ekim):**
  - Okuma ekranının kelime sorgusu (`readings/kelime_sorgu.py`) artık büyük-küçük harfe duyarsız (küçük harfli `slug` üzerinden).
  - Arab, Arabian, Arabic, Caucasian, Chinese, Guinean büyük harfle yazıldı (`words/duzeltmeler/d_2026_10_01.py`). Tarama: örnek cümlelerde cümle ortasında hep büyük harfle geçen kelimeler; diğer adaylar (Arctic, senate, pope, commonwealth…) küçük harfle de doğru olduğu için değiştirilmedi.
  - "oriental" (isim, "Doğulu kişi"): insanlar için eskimiş ve rahatsız edici; silindi. Sıfatı (eşya, sanat) kaldı.
  - Yedek: `~/LearnVocab-yedekler/db.sqlite3.yedek-20261001-buyuk-harf-oncesi`.

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

### 18.17 Tailwind (Efe'nin kararı, 29 Eylül: A, Standalone CLI) — **YAPILDI (2 Ekim)**
- Play CDN kaldırıldı. CSS yerelde **Tailwind Standalone CLI v3.4.19** ile derlenir; Node gerekmez, sunucuda hiçbir şey çalışmaz.
  - Ayar: `tailwind.config.js` (renk eşlemesi, `darkMode: 'class'`, okuma konularının dinamik renkleri için safelist). Giriş: `static/css/tailwind-giris.css`. Çıktı: `static/css/site.css` (~80 KB, depoda).
  - Derleme: `.venv/bin/tailwindcss -c tailwind.config.js -i static/css/tailwind-giris.css -o static/css/site.css --minify`. CLI dosyası `.venv/bin/` altında, depoya konmaz (resmî SHA256 ile doğrulandı).
  - `site.css` `<head>`'in sonunda yüklenir (eski CDN sırası korunur). Derlenmiş CSS ile CDN on ekranda karşılaştırıldı: fark yok.
  - `LearnVocab/test_tailwind.py`: sayfalardaki her Tailwind sınıfı `site.css`'te olmalı; şablona yeni sınıf eklenip derleme unutulursa test düşer.
- **Alpine:** 3.17.4 sabitlendi, `static/js/alpine-3.17.4.min.js` dosyasından sunulur.
- **Yazı tipleri:** Google Fonts yerine sitenin kendi dosyaları (`static/fonts/`, `static/css/fontlar.css`).

### 18.18 Rapor yalnızca mevcut durumu yazar (Efe'nin kararı)
- Rapor ürünün **şu anki** hâlini anlatır. Kodla ya da kendi içinde çelişen yerler düzeltilir.
- Bölüm 18'deki işler uygulandıkça ilgili bölümler güncellenir, "→ 18.x" notları kaldırılır, madde buradan silinip Değişiklik kaydına yazılır.

### 18.19 KVKK — **ilk sürüm yapıldı (10 Ekim; Efe'nin isteği)**
- **Aydınlatma metni:** `/gizlilik/` (url adı `gizlilik`), `LearnVocab/yasal.py`; metin `templates/pages/yasal/aydinlatma_tr.html` (asıl) ve `aydinlatma_en.html` (çevirisi; biri değişince öteki de, `GUNCELLEME` tarihi de). Hukuki metin olduğu için django.po'ya bölünmedi. Almanca yok (de kapalı).
  - İçerik (KVKK m. 10): veri sorumlusu, işlenen veriler, amaç ve hukuki sebep (m. 5/2-c, ç, f), aktarımlar (Google Gemini API, Gmail, Google ile giriş, Türkiye'deki barındırma), toplama yöntemi, saklama süreleri, çerezler (yalnızca zorunlu), m. 11 hakları ve başvuru.
  - Gemini'nin ücretsiz katmanı açıkça yazıyor: gönderilen metni Google ürün geliştirmede kullanabilir, insanlar inceleyebilir; yazılara kişisel bilgi yazılmaması öneriliyor. PDF dosyasının saklanmadığı, yalnızca metninin kaldığı yazıyor.
  - Veri sorumlusu ve başvuru e-postası `.env`'den: `KVKK_VERI_SORUMLUSU` (varsayılan "Efe Solmaz"), `KVKK_ILETISIM_EPOSTASI` (boşsa `DEFAULT_FROM_EMAIL`).
- **Kayıt:** formda zorunlu "Aydınlatma Metni'ni okudum" kutusu (bağlantı yeni sekmede açılır). Bu açık rıza değil, bilgilendirmenin kaydı: an `User.aydinlatma_okundu`'ya yazılır (`users/0007`). Google düğmesinin altında "Google ile devam edersen Aydınlatma Metni'ni okumuş olursun" notu; Google ile ilk girişte an `users/sinyaller.py`'de yazılır. Eski hesaplarda boş.
- **Efe'nin kararı / kontrolü gereken (Claude avukat değil; metin bir hukukçuya okutulmalı):**
  - Yurt dışına aktarım (Google): metin "m. 9'a uygun olarak" diyor. 2024 değişikliğinden sonra dayanak ya standart sözleşme (imzalandıktan sonra 5 iş günü içinde Kurum'a bildirilir) ya da arızi aktarımda açık rıza. Hangisi kullanılacak, Efe karar verecek; açık rıza seçilirse yazma değerlendirmesinden önce ayrı bir onay gerekir.
  - Duyuru e-postaları (`featuresMail`, `improvementsMail`) varsayılan açık. Ticari ileti sayılırlarsa önceden onay ve İYS kaydı gerekir; varsayılanın kapalı yapılması önerilir.
  - VERBİS: kişi sayısı ve ciro eşiklerinin altında olunduğu sürece kayıt zorunlu görünmüyor; kontrol edilmeli.
  - Barındırma: Veridyen, sunucular Türkiye'de (Efe doğruladı, 10 Ekim).

### 18.21 Google ile giriş (Efe'nin kararı, 29 Eylül) — **YAPILDI (2 Ekim; Efe yerelde denedi, çalışıyor)**
- Giriş ve kayıt sayfalarına **"Google ile giriş yap"** eklenir. Mevcut e-posta/şifre girişi kalır.
- **Altyapı (Claude'un önerisi):** `django-allauth` (Google sağlayıcısı).
  - Aynı e-postayla kayıtlı hesap varsa Google girişi o hesaba bağlanır.
  - Google ile ilk girişte kullanıcı adı otomatik üretilir.
  - Kayıt formundaki zorunlu "kur" seçimi Google girişinde sorulmaz (Bölüm 16'daki açık soruyla birlikte ele alınır).
- **Efe'nin yapması gereken:** Google Cloud Console'da OAuth istemcisi oluşturmak. Yönlendirme adresi `https://www.learnvocab.com.tr/…` olur. İstemci kimliği ve gizli anahtar `.env`'e yazılır, sohbete yazılmaz.
- KVKK metninde Google girişi belirtilir (18.19).
- **Uygulama (2 Ekim):** `django-allauth 65.19.7` (yalnızca Google sağlayıcısı); ayarlar `LearnVocab/settings.py` ("Google ile giriş" bölümü).
  - Anahtarlar `.env`'de: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`. Yoksa düğme hiç görünmez.
  - Google projesi "LearnVocab" (Efe'nin hesabı); onay ekranı External, yayında; izinler yalnızca email/profile/openid.
  - Yönlendirme adresleri: `http://localhost:8000/…`, `http://127.0.0.1:8000/…`, `https://www.learnvocab.com.tr/accounts/google/login/callback/`.
  - "Google ile devam et" düğmesi giriş ve kayıt sayfalarında (`pages/users/_googleGiris.html`); POST ile başlar.
  - Aynı e-postalı hesap varsa ona bağlanır; yoksa hesap kendiliğinden açılır (kullanıcı adı e-postadan, ad/soyad Google'dan) ve ayar satırı eklenir (`users/sinyaller.py`).
  - allauth'un kendi giriş/kayıt/çıkış sayfaları bizimkilere yönlenir (`/accounts/login/` → `/giris/` …).
  - Yerel sunucu sanal ortamla başlatılır: `.venv/bin/python manage.py runserver` (yeni paketler yalnızca `.venv`'de kurulu).

### 18.22 Dil seçeneği (Efe'nin kararı, 29 Eylül) — **YAPILDI (5 Ekim); Almanca 8 Ekim'de kapatıldı, yayında tr ve en**
> **Almanca kapatıldı (Efe'nin kararı, 8 Ekim):** kelime anlamları Türkçe; Almanca arayüzle Türkçe anlam okuyan bir kitle yok. `/de/` sayfaları ana içeriği aynı kopya sayfalar üretiyor, tarama bütçesini harcıyor ve bakım yükünü artırıyordu. `YAYIN_DILLERI` varsayılanı `tr,en`; site haritası ve hreflang Almancayı yazmaz. Eski `/de/…` adresleri aynı sayfanın Türkçesine **301** verir (`LearnVocab.diller.KapaliDilYonlendirme`). Çeviri dosyası `locale/de/` duruyor; açmak için `YAYIN_DILLERI=tr,en,de`. 18.34'teki Almanca görsel ve videolar artık gerekmez. **Sunucuda ortam değişkeni `YAYIN_DILLERI` tanımlıysa oradan da `de` çıkarılmalı.**
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
- **Efe'nin kararları (2 Ekim):**
  - **Dil düğmesi:** sağ üstte profil fotoğrafının yanında (misafirde "Giriş yap"ın yanında) bir düğme; tıklanınca üç satırlık liste açılır (Türkçe · English · Deutsch). Seçince aynı sayfanın o dildeki adresine gidilir; seçim cihazda, girişlide hesapta saklanır.
  - **Otomatik yönlendirme yok** (Claude'un önerisi, SEO): tarayıcı diline göre yönlendirilmez; en çok küçük bir öneri gösterilir. Bir dil, arayüz metinlerinin hepsi çevrilmeden yayına alınmaz.
  - **"Türkçe anlamlar" ayarı (arayüz dilinden bağımsız):** Ayarlar'da, hesaba kaydedilen bir seçenek; varsayılan açık. Kapalıysa kartlarda, L&P'de ve egzersizlerde Türkçe anlam gösterilmez ve sorulmaz; her şey İngilizce açıklama üzerinden yürür.
- **Uygulama (3–5 Ekim):**
  - **Çeviri dosyaları:** `locale/en/` ve `locale/de/` (`django.po` + derlenmiş `django.mo`, ~1.020 metin, hepsi çevrili). Bütün canlı şablonlar ve Python metinleri (`gettext`/`gettext_lazy`, şablonda `{% translate %}`/`{% blocktranslate %}`) çeviriye hazır. Çevrilmeyenler: kullanılmayan `comments.html`, `friends.html` ve admin.
  - **Terimler:** Kısa Sınav = Quick Quiz / Kurztest · Deneme Sınavı = Practice Test / Probetest · Listem = My List / Meine Liste · Yazılar = Writings / Schreiben (adres `/en/writings/`, `/de/schreiben/`) · seri = streak / Serie · dondurma hakkı = streak freeze / Serienschutz.
  - **Dil düğmesi** (`base/_dilDugmesi.html`): üst çubukta profil fotoğrafının yanında küre ve dil kodu (TR/EN/DE); açılan listede üç dil. Seçince `POST /dil/` (`LearnVocab/diller.py`) aynı sayfanın o dildeki adresine gider; seçim çerezde, girişliyse hesapta (`UserSettings.arayuz_dili`) saklanır. Girişte (Google ile giriş dahil) hesap dili varsa o dile geçilir. Yayında tek dil kalırsa düğme görünmez.
  - **Öneri şeridi** (`base/_dilOnerisi.html`): kullanıcı hiç dil seçmemişse ve tarayıcısı yayındaki başka bir dili istiyorsa sayfanın üstünde o dilde küçük bir öneri ("Diese Seite gibt es auch auf Deutsch."). Yönlendirme yok.
  - **Ayarlar'da "Dil"** bölümü (aynı üç seçenek) ve **"Türkçe anlamlar"** anahtarı (`UserSettings.turkce_anlamlar`, varsayılan açık; `usersettings/anlam.py`). Kapalıyken kartlarda, Listem'de, L&P'de, okuma baloncuğunda, arama önerilerinde, günün kelimesinde ve diyalog ipucunda Türkçe anlam yerine İngilizce açıklama görünür; Kısa Sınav açıklama sorar; Deneme Sınavı'nda Türkçe isteyen tipler (anlam, eşleştirme) "Türkçe anlamlar kapalı" notuyla pasif olur. Misafirde her zaman açık.
  - **Yazılarda geri bildirim arayüz dilinde gelir** (Gemini isteminde dil verilir; `texts/degerlendirme.py`).
  - **Bildirimler** (hatırlatma, seri) alıcının hesap dilinde yazılır (`diller.kullanici_dilinde`).
  - **Yüzdeler** sayfanın diline göre yazılır (Türkçe %70, İngilizce 70%, Almanca 70 %; `Intl.NumberFormat`).
  - **Hazır listelerin adı ve açıklaması** sayfanın dilinde gösterilir: `HazirListe.ad_en/ad_de/aciklama_en/aciklama_de` (admin'de doldurulur; boşsa Türkçesi). Yeni liste eklenirken bu dört alan da doldurulmalı.
  - Okuma metinlerinin **kaynak satırı**: bilinen kaynaklar (şimdilik "Örnek metin (LearnVocab, Claude tarafından yazıldı)") `readings.models.KAYNAK_CEVIRILERI` ile sayfanın dilinde yazılır; yeni bir kaynak metni eklenirse buraya da eklenir.
  - **Veritabanı içeriği Türkçe kalır:** kelime anlamları (karar b).
  - Testler: `LearnVocab/test_diller.py`.

### 18.23 Kayıt formu ve günlük hedef (Efe'nin kararı, 29 Eylül) — **YAPILDI (30 Eylül)**
- **Kayıt formu:** **ad, soyad, e-posta, kullanıcı adı, şifre**; hepsi zorunlu.
  - **Şifre tek kez** alınır; "şifreyi tekrar yaz" alanı yok. Alanın içinde **"Göster / Gizle"** düğmesi var.
  - Şifre kuralı değişmedi: en az 8 karakter, bir büyük harf, bir küçük harf, bir rakam.
  - Hata olursa form, yazılanlar silinmeden yeniden gösterilir (şifre hariç).
- **"Kur" kalktı:** Kayıtta seviye sorulmaz; `User.level` alanı silindi. Seviye yalnızca seviye testinden ya da "Seviyemi kendim seçeyim"den gelir (`User.cefr`); belirlenmemişse B1 varsayılır. Bölüm 16'daki "kur → CEFR eşlemesi" kararı düştü.
- **"Günlük hedef" ayarı kalktı** (`UserSettings.dailyGoal` silindi). Seri sabit kurallarla çalışır (18.9). "Günlük hatırlatma e-postası" ayarı duruyor.

### 18.24 Okumalar: sınırlar, saklama ve çöp kutusu (Efe'nin kararı, 29–30 Eylül) — **YAPILDI (30 Eylül; çöp kutusunun görsel tasarımı tasarım oturumunda)**
**Sınırlar:**
- Kullanıcı başına en çok **100 metin**, bunların en çok **15'i PDF**. Çöpteki metinler sayılmaz.
- **PDF başına en çok 400 sayfa ve 50 MB.** 400 sayfayı aşan PDF reddedilir; metni ~1,5 milyon karakteri aşarsa ilk kısmı alınır.
- Yapıştırılan metin en çok 150.000 karakter.

**Saklama:**
- PDF dosyası **saklanmaz**; yalnızca çıkarılan metin tutulur.
- **Metnin gövdesi veritabanında değil, diskte** durur: zlib ile sıkıştırılmış dosya (`readings/depo.py`). Sunucudaki MySQL en çok 1 GB, disk limitsiz (18.32).
  - Veritabanında yalnızca başlık, tür, kelime sayısı ve dosya adı var (`UserText.dosya`).
  - Depo klasörü **`ozel_depo/`** (`settings.OZEL_DEPO`). **Web'den sunulmaz**; `media/` değildir, çünkü bu metinler yalnızca sahibine özeldir. Git'e girmez.
  - Ölçüm: yerelde 296 KB'lık iki metin diskte 108 KB oldu.
  - Metin silinince dosyası da silinir.
- **Okuma ekranı uzun metni bölüm bölüm gösterir:** her bölüm yaklaşık 1.500 kelime, paragraf sınırında biter. Üstte ve altta "Önceki bölüm · Bölüm 2 / 40 · Sonraki bölüm" (`?bolum=2`).

**Çöp kutusu:**
- Silinen metin çöp kutusuna gider (Okumalar sayfasında, "Kendi metinlerim"in altında açılır liste).
- Buradan **geri alınabilir** ya da **kalıcı silinebilir** (kalıcı silme onay sorar; geri alınamaz).
- **1 hafta** sonra kendiliğinden kalıcı olarak silinir; satırda kaç gün kaldığı yazar.
- Görsel tasarımı tasarım oturumunda yapılacak.

**Canlıya geçişte (18.30):** Sunucuda `ozel_depo/` klasörü web kökünün dışında olmalı ve yedeğe dahil edilmeli. 50 MB'lık yüklemeye sunucunun (Apache/Passenger) izin verdiği doğrulanmalı.

### 18.25 Gelir modeli (Efe'nin kararı, 29 Eylül)
- Site **ücretsiz.** **Ücretli üyelik / premium kesinlikle olmayacak.** (Ücretsiz hesap açma elbette kalır.)
- Site beğenilirse **ileride reklam** alınabilir. Bu ileri bir konu, şimdilik tasarımda reklam alanı ayrılmaz.
- Reklam gelirse L&P ve egzersiz gibi çalışma ekranlarına konmaz (odak, 18.10), sayfa hızını bozmayacak biçimde yerleştirilir (SEO, 18.15). (Claude'un önerisi.)

### 18.26 Gezinme: profil fotoğrafı, Hesap ve Ayarlar (Efe'nin kararı, 29–30 Eylül) — **YAPILDI (30 Eylül; görsel tasarım ve eksik ayarlar tasarım oturumunda)**
- Sağ üstteki dişli kalktı; yerinde kullanıcının **profil fotoğrafı** var. Dokununca **Hesap** (`/profil/`) açılır.
- **Hesap sayfası:** fotoğraf, ad, çıkış; hesap bilgileri formu; **Ayarlar** bağlantısı; parola değiştirme.
- **Ayarlar sayfası** (`/ayarlar/`), Hesap'tan gidilir. Sırasıyla:
  1. **Görünüm (tema):** Sistem · Açık · Koyu. En üstte, kolayca görülür.
  1a. **Dil** (18.22) ve hemen altında **Türkçe anlamlar** anahtarı (Efe, 5 Ekim: insanlar görsün diye dilin hemen altında).
  2. **Seviye:** seviyeyi gösterir, seviye testini tekrarlatır.
  3. **Çalışma:**
     - **Learn & Pass tekrar/yeni oranı: kaydırma çubuğu** (Efe'nin kararı, 1 Ekim). Sola çektikçe tekrar, sağa çektikçe yeni kelime artar; yalnızca **%10'luk adımlar** (%0–%100). Altında "Tekrar %70 · Yeni %30" yazar. Varsayılan %30 yeni.
     - **Egzersizde soru sayısı: 5 · 10 · 15 · 20** (Efe'nin kararı). Deneme Sınavı bu sayıyla açılır; açılış ekranındaki seçenekler de aynı dört sayı (25 kalktı).
     - Yazılarda geri bildirim sertliği (Nazik · Normal · Titiz), sesi otomatik oynatma.
  4. **Bildirimler (anlık):** bu cihazda aç / kapat (18.29).
  5. **E-posta bildirimleri.**
  6. **Verilerim** (dışa aktarma).
  7. **Tehlikeli bölge** (listeyi boşalt, hesabı sil; parola sorar).
- **Alttaki menü ve sağ üstteki profil fotoğrafı her sayfada sabittir** (Hesap ve Ayarlar dahil).
- Misafirde profil fotoğrafının yerinde "Giriş Yap" durur.
- **Tema:** Üst çubuktaki tema düğmesi kalktı. **Varsayılan tema cihazın sistem temasıdır**; kullanıcı Ayarlar'dan Açık ya da Koyu seçerse onun seçimi geçerli olur ("Sistem"e dönebilir). Seçim cihazda saklanır.
- Ayarlar'da **Dil** (Görünüm'ün altında) ve hemen altında **Türkçe anlamlar** anahtarı var (18.22). Beyaz tema (18.12) açık temanın yeni hâli olacak.
- **Kaydet düğmesi yok (Efe, 5 Ekim):** her değişiklik o an arka planda kaydedilir (`keepalive` ile; sayfadan nasıl çıkılırsa çıkılsın ayarlar son hâlindedir), altta kısa bir "kaydedildi ✓" görünür. Tema cihazda, dil `/dil/` ile zaten anında kaydedilir.

### 18.27 Seviye testi değişiklikleri (Efe'nin kararları, 29–30 Eylül) — **YAPILDI (30 Eylül; özet soruları 1 Ekim'de yüklendi)**
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
> **Özet soruları (1 Ekim):** Claude elle yazdı (API yok): A1 50 · A2 50 · B1 50 · B2 50 · C1 51 · C2 50 = **301 soru**. Dosyalar `seviye/havuz/ozet_*.jsonl`, yükleme `manage.py seviye_okuma_yukle`. Her soruda 4–5 cümlelik metin, bir doğru özet ve metinle çelişen 3 çeldirici var; hepsi "denetlendi" işaretli. Efe admin'den (Seviye › Okuma soruları) göz atabilir; beğenmediği soru `denetlendi` kaldırılarak testten çıkarılır.

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

### 18.28 Egzersizler: düzensiz fiiller (Efe'nin kararı, 29 Eylül) — **YAPILDI (1 Ekim)**
- 2. ve 3. hâli kendisiyle aynı olan fiiller (cut, put, hit…) **da sorulur.**
- Bu fiillerde gerçek çeldirici yalnızca -ing ve -s hâlidir; soru **3 şıkla** gelir (cut · cutting · cuts). "cutted" gibi uydurma biçim yine kullanılmaz (12.3). Kod: `egzersizler/sorular.fiil_sorusu`.

### 18.29 Bildirim izni akışı (Efe'nin kararı, 29 Eylül) — **YAPILDI (1 Ekim)**
**Uygulama (1 Ekim):**
- Ön ekran `templates/bildirimler/_onEkran.html` (kapibaralı, sayfanın altında küçük pencere). Ölçüt `bildirimler/baglam.py`: en az 3 **bitmiş** egzersiz oturumu ve en az 20 L&P kartı. Ölçüt bir kez sağlanınca oturumda işaretlenir.
- Çıkmadığı yerler: L&P ve egzersiz oturumları, seviye testi, giriş/kayıt sayfaları. Seviye testi daveti gösterilirken de çıkmaz (iki pencere üst üste binmesin).
- Bu cihaz zaten aboneyse, izin tarayıcıda engelliyse ya da desteklenmiyorsa çıkmaz. "Şimdi değil" → 7 gün bu cihazda çıkmaz. iPhone'da site ana ekrana eklenmediyse "Ana ekrana ekle" rehberi çıkar.
- Eski "Yarın hatırlatayım mı?" kartı L&P bitişinden kaldırıldı.
- **Ayarlar › Bildirimler:** bu cihazda Aç / Kapat (abonelik cihaza özel). Ortak kod `templates/bildirimler/_js.html` (`window.lvBildirim`).
- VAPID anahtarı `.env`'de yoksa bildirimle ilgili hiçbir şey görünmez.

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
  - `media/telaffuz/` ses dosyalarının (218 MB, 28.372 dosya) sunucuya yüklenmesi (18.4)
  - `.env`'e `SITE_ADRESI` (varsayılanı zaten `https://www.learnvocab.com.tr`); `http` + `www`'suz isteğin tek adımda yönlenmesi (`.htaccess`)
  - kademeli dizine alma partilerinin takvimi (18.15: 1. parti açık, sırada B2 Oxford)

**Claude'un hazırladığı TASLAK kontrol listesi (1 Ekim; uygulanmadı, Efe ile konuşulacak):**
1. **Önce yerelde:** `.venv/bin/python manage.py test --parallel 4 --noinput` · `manage.py check --deploy` · veritabanı yedeği (`~/LearnVocab-yedekler/`).
2. **Veri boyutu:** Yerel SQLite 44 MB; MySQL'de benzer olur, 1 GB sınırının çok altında. Telaffuz dosyaları 218 MB (28.372 dosya, inode sınırının ~%7'si). `ozel_depo/` şu an 108 KB.
3. **Veritabanı taşıma (önerilen yol):** yerelde `manage.py dumpdata --natural-foreign --exclude contenttypes --exclude auth.permission --exclude sessions > veri.json`; sunucuda boş MySQL'e `migrate` ve `loaddata veri.json`. (v1.0 kullanıcı verisinin ne olacağı Efe'nin kararı: çok az ve önemsiz.)
4. **Kod:** `git pull`; `pip install -r requirements.txt` (sunucu Python 3.10 — kodda 3.11+ özelliği yok, denetlendi; `wordfreq`, `lemminflect`, `spylls` yalnızca veri komutları için, sunucuda şart değil ama `pymupdf` PDF yükleme için ŞART); `migrate`; `collectstatic`.
5. **Dosyalar:** `media/telaffuz/` sunucudaki `media/`'ya (SFTP/rsync). `ozel_depo/` web kökünün DIŞINDA olmalı ve yedeğe girmeli.
6. **`.env`:** `DEBUG=False`, `SITE_ADRESI=https://www.learnvocab.com.tr`, `OZEL_DEPO` (web dışı tam yol), VAPID anahtarları (`manage.py vapid_anahtari_uret`), Gemini anahtarı. Anahtarlar sohbete yazılmaz.
7. **Yönlendirmeler:** `.htaccess` ile `http://` ve `www`'suz isteklerin tek adımda `https://www.` adresine 301'i. Canlıdaki v1.0 adreslerinden örnekleri elle dene (`/users/login/`, `/texts/`, `/readings/` → yeni adresler).
8. **Cron** (`bildirimler/CRON.md`): `yazilari_yeniden_dene` 30 dk, `bildirim_gonder_hatirlatma` 15 dk, `karsilasma_ozetle` her gece, `clearsessions` isteğe bağlı.
9. **PDF yükleme sınırı:** Apache/Passenger'ın 50 MB yüklemeye izin verdiği doğrulanır (gerekirse `LimitRequestBody`).
10. **Google:** Search Console'da alan adı doğrulaması (Efe, DNS TXT), `sitemap.xml` gönderimi; birkaç gün "Dizine eklenen / taranan ama eklenmeyen" sayılarının izlenmesi; sonra kademeli dizine almanın 2. partisi (B2 Oxford).
10a. **Google ile giriş:** sunucuda `pip install -r requirements.txt` (django-allauth, PyJWT) ve `migrate` (account, socialaccount tabloları); `.env`'e `GOOGLE_CLIENT_ID` ve `GOOGLE_CLIENT_SECRET`; Google Cloud'da canlı yönlendirme adresinin kayıtlı olduğu doğrulanır; canlıda bir kez Google ile girilir.
10b. **Yeni migration'lar:** `egzersizler/0002` (Kısa Sınav / Deneme Sınavı adları), allauth tabloları ve `usersettings/0006` (arayüz dili, Türkçe anlamlar).
10d. **Diller (18.22):** `.mo` dosyaları depoda olduğu için sunucuda `compilemessages` (gettext) gerekmez. `YAYIN_DILLERI` varsayılanı `tr,en,de`. Search Console'da `/en/` ve `/de/` adreslerinin `hreflang` ile tanındığı izlenir. Site haritası artık her adresi üç kez yazıyor; 50.000 adrese yaklaşınca site haritası dizinine (parçalara) bölünür.
10c. **Statik dosyaların önbelleği (Claude'un önerisi, Efe ile konuşulacak):** CSS/JS dosya adları değişmediği için güncellemeden sonra tarayıcılar eski `defter.css`/`site.css`'i kullanabilir. Çözüm: `ManifestStaticFilesStorage` (dosya adına içerik özeti eklenir; `collectstatic` ile çalışır, ek paket gerekmez).
11. **Geçiş günü:** kısa bakım ekranı (Passenger `tmp/restart.txt` ile yeniden başlatma), geçişten sonra ana akışların elle denenmesi (kayıt, L&P, egzersiz, okuma, yazı, bildirim).


### 18.31 İstatistik ekranı (admin) (Efe'nin kararı, 29 Eylül) — **YAPILDI (1 Ekim)**
**Uygulama:** `/admin/istatistik/` (yalnızca yönetici; admin ana sayfasında "İstatistikler" bağlantısı). Kod `LearnVocab/istatistik.py`.
- Göstergeler: aktif kullanıcılar (bugün, 7 gün, 30 gün, son 14 gün); tekrar basamağı başına unutma oranı; günün tamamlanma oranı; L&P'de 10 karta ulaşmadan bırakılan günler (L&P turu ayrı kaydedilmediği için yarıda bırakma bu ölçüyle görülür); yarıda bırakılan egzersiz oturumları; seri uzunluğu dağılımı; bildirim ön ekranı ölçütünü sağlayanların bildirimi açma oranı.
- Gizlilik: yalnızca toplu sayı; arkasında 5'ten az kişi olan oran gösterilmez, 1–4 arası sayılar "<5" yazılır.

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
  - **Ayrıntılı karşılaşma kayıtları (`EncounterLog`) 90 gün tutulur**, daha eskileri **kişisiz** günlük özetlere (`KarsilasmaOzeti`: gün, mod, basamak, karar, sayı) çevrilip silinir: `manage.py karsilasma_ozetle`, cron her gece 04.00 (`bildirimler/CRON.md`). **Yapıldı (1 Ekim).** Tekrar kuralı `WordEncounter`'daki güncel durumla, seviye düzeltmesi son 90 günle çalışır; istatistik ekranı ikisini birlikte okur. Böylece veritabanı 1 GB'ın altında kalır.
  - Seri kaçırma bildirimi **23.45** (18.9).
  - Ses dosyaları (18.4, seçilirse) sunucuda durabilir: ~28 bin dosya (~70–110 MB) inode sınırının %7'si.
- **Maliyet ilkesi (Efe):** Bu süreçte ek masraf çıkmamalı. Ücretli servis, API ya da hesap gerektiren çözümler önerilmez; ücretsiz ve yerel çözümler tercih edilir.

### 18.33 Yardım sayfası ve tanıtım videosu (Efe'nin kararları, 2 Ekim)
- **Tema:** asıl tema **defter**. Video da defter sayfalarında geçer; elle çizilmiş, boya kalemi dokulu çizim yalnızca **çizim şekli** olarak kullanılır.
- **Tanıtım videosu:** yaklaşık 1 dakika ya da daha kısa.
  - Defter sayfası sahneleri, boya kalemi dolgusu, sayfa çevirme geçişleri, kenarda karalama gibi duran kapibara (~50 sn senaryo).
  - **Her dil için ayrı video** (kendi altyazısıyla). Sayfa hangi dildeyse o dilin videosu oynar.
- **Kapibara (Efe onayladı, 2 Ekim):** önden bakan, ayakta duran **yetişkin** kapibara; düz tepeli uzun baş, küçük kulaklar, burun ucunda koyu leke, **ağzı açık, iki ön dişi dışarıda** (kunduz gibi), armut gövde. Çizgi defterin mavi mürekkebi, dolgu boya kalemi dokulu.
  - **Koyu tema:** çizgi koyu kahve kalem; karakter açık kenarlı bir çıkartma gibi zeminden ayrılır.
  - Parçalar `templates/base/_kapibaraTanim.html` (layout her sayfada bir kez ekler); çizim `base/_kapibara.html` ile `poz` seçilerek konur: duruyor, merhaba, kirpar, seri (kafasında portakal), uyku, okuyor, yaziyor, zil, uzgun, bas. Renkler `defter.css` (`--kapi-*`).
  - Sitedeki yerleri: ana sayfa "Bugünün sayfası" (okuyor), seri kutusu (baş), L&P balonu (göz kırpar), L&P oturum sonu (merhaba / kart yoksa uyku), bildirim ön ekranı (zil), Hesap fotoğrafsız (merhaba).
  - Örnek sayfa: `ozetler/tasarim-ornekleri/kapibara/index.html`.
- **Yardım sayfası:** kısa genel tanıtım yazısı + işaretli ekran görüntüleriyle "nasıl yapılır" yönergeleri. Konular en az şunlar:
  - Ayarlardan siteyi nasıl özelleştirirsin.
  - Sözlük ve hazır listelerin kullanımı.
  - Egzersiz çeşitleri (Kısa Sınav, Deneme Sınavı ve soru türleri) ve nasıl kullanılacakları.
  - (Learn & Pass, Okumalar, Yazılar, seri gibi diğer konular Efe'nin açıklamasıyla eklenecek.)
- **Ekran görüntüleri elle değil, her sürümde baştan hazırlanır:** her dil ve her tema (açık/koyu) için. Bu iş 18.34'teki listededir; otomasyon aracı kurulmaz.
- **Yardım ve hakkında sayfası — YAPILDI (2 Ekim; Efe okuyup düzeltecek).** Tek sayfa, adres `/hakkinda/` (eski adres korundu; `/about/` buraya yönlenir, site haritasında).
  - İçerik `LearnVocab/yardim.py`, şablon `templates/pages/about.html`, testler `LearnVocab/test_yardim.py`.
  - Bölümler: içindekiler · "LearnVocab nedir?" (tanı / gör / kullan, bir gün nasıl geçer) · 9 rehber: Sözlük, hazır listeler, Listem, Learn & Pass, Egzersizler (soru tipleri tablosu `egzersizler.sorular.TIPLER`'den gelir, kendiliğinden güncel kalır), Okumalar, Yazılar, seri, Ayarlar · "Siteyi kim yaptı?" (Efe'nin eski hakkında yazısından; iletişim: ODTÜ e-postası ve GitHub, Efe gerekirse kaldırır).
  - Her rehberde telefon çerçevesinde ekran görüntüsü, üstünde kırmızı numaralı işaretler; yanında aynı numaralı adımlar. Görüntü temaya göre değişir.
  - **Görüntüler telefon görünümünde (375 px) çekilir**, masaüstünde de telefon çerçevesinde gösterilir; ayrı masaüstü görüntüsü yoktur. 15 ekran × 2 tema × 3 dil = 90 WebP (dil başına ~900 KB), ekrana gelince yüklenir. Yer: `static/img/yardim/<dil>/<ad>-<acik|koyu>.webp`. Sayfa hangi dildeyse o dilin görüntüleri gelir.
  - İşaret konumları `REHBERLER`'de (Türkçe görüntüye göre); yazılar uzayıp düzen kayan dillerin konumları `ISARET_DILLERI`'nde. Ayarlar rehberi üç görüntü: Görünüm + Dil · Türkçe anlamlar + Seviye · L&P oranı, soru sayısı, geri bildirim.
  - Örnek hesapta 13 günlük seri (bir gün dondurulmuş) var; seri penceresi görüntüsü bu yüzden dolu takvim gösterir.
  - Görüntüler deneme veritabanındaki örnek hesapla çekilir (gerçek kullanıcı verisi görünmez).

### 18.34 Her yeni sürümde yapılacaklar (Efe'nin kararı, 2 Ekim)
Yeni sürüm yayına çıkmadan önce bu liste baştan sona yapılır. Yeni sürekli iş çıkarsa buraya eklenir.
1. Testler: `.venv/bin/python manage.py test --parallel 4 --noinput`.
2. Tailwind yeniden derlenir (komut `tailwind.config.js` başında); `LearnVocab.test_tailwind` geçmeli.
3. Yardım sayfasının ekran görüntüleri **her dil ve her tema** (açık/koyu) için telefon görünümünde (375 px) baştan çekilir; deneme veritabanındaki örnek hesapla, varsayılan ayarlarla (Türkçe anlamlar açık). Koyu temada üst çubuktaki renk geçişi bitmeden çekilmez. Görüntü değiştiyse `LearnVocab/yardim.py`'deki işaret konumları (`REHBERLER`, dile özgü olanlar `ISARET_DILLERI`) güncellenir; `LearnVocab.test_yardim` eksik görüntüyü ve yanlış boyu yakalar (18.33).
4. Tanıtım videosu tasarım ya da metin değiştiyse **her dil için** yeniden hazırlanır; altyazılar güncellenir (18.33).
5. Yeni ya da değişen arayüz metinlerinin çevirileri tamamlanır (18.22): `.venv/bin/python manage.py makemessages -l en -l de --ignore=.venv --ignore=node_modules`, `locale/*/LC_MESSAGES/django.po`'daki boş ve `fuzzy` satırlar çevrilir, `.venv/bin/python manage.py compilemessages -l en -l de --ignore=.venv`. Sonra `/en/` ve `/de/` sayfaları çevrilmemiş Türkçe için taranır (özellikle `{{ sayı }} kelime` gibi değişkene yapışık sözcükler).
6. Rapor güncellenir, "Değişiklik kaydı"na sürüm notu eklenir.

### 18.35 Sözlüğü genişletme: wordfreq'ten yeni kelimeler (Efe'nin kararı, 5 Ekim) — **parti 0–4 yapıldı (4.598 kelime)**
- **Amaç:** sözlükte olmayan, sık kullanılan ~3.500 kelimeyi eklemek.
- **Hat:** 25 Eylül'deki hat aynen kullanılır (`ozetler/2026-09-24_0918_kelime-hatti-durum.txt`, `2026-09-25_kelime-hatti-bitti.txt`): `aile_uret --file …` → `aile_birlestir` → `aile_doldur` (üretici `openai/gpt-oss-120b`, kontrolcü `google/gemini-3.8-flash` düşünme low, OpenRouter). Ardından Claude yeni kelimeleri okur ve hataları `words/duzeltmeler/` altında düzeltir.
- **Harcama (Efe, 5 Ekim):** ücretli Gemini kullanılır; üst sınır **5–10 $**. Eski hatta maliyet ~2,1 $ / 1.000 kelimeydi; aile genişletmesi listedeki kelime sayısından fazla kelime getirir. Önce küçük bir parti çalıştırılıp gerçek maliyet ölçülür, sonra kesme eşiği seçilir.
- **Aday listesi:** `listeler/2026-10-05-wordfreq-adaylar.txt` (kelime, zipf). Üretim: wordfreq'in ilk 80.000 kelimesinden zipf ≥ 3; kendisi, kökü ya da çekimli biçimi sözlükte olanlar, özel adlar, sayılar (18.16), İngiliz yazımları (colour; sözlük Amerikan yazımını tutar), argo ve kesme işaretsiz kısaltmalar, müstehcen ve hassas kelimeler ayıklandı; kalan liste Claude tarafından baştan sona okunup elle temizlendi. Sayılar: zipf ≥ 3,0 → 4.026 · ≥ 3,1 → 3.252 · ≥ 3,2 → 2.566 · ≥ 3,5 → 1.124.
- **Akademik liste (Efe onayladı, 5 Ekim):** NAWL 1.2 (Browne & Culligan, newgeneralservicelist.com, 957 kelime) indirildi; dosya proje dışında `~/LearnVocab-kaynaklar/`. 815'i sözlükte zaten vardı; eksik 134 kelime listenin başına alındı. Birleşik liste: `listeler/2026-10-05-eklenecekler.txt` (önce NAWL, sonra wordfreq; NAWL + zipf ≥ 3,1 = 3.273 kelime).
- **Partiler:** önce 200 kelimelik deneme, sonra 600–800 kelimelik partiler (Efe). Ara depo `ara-depo-genisletme/` (git'e girmez). Her partiden önce veritabanı yedeği (`~/LearnVocab-yedekler/…genisletme-parti-N-oncesi`), her partiden sonra Claude yeni kelimelerin hepsini okur ve düzeltmeleri `words/duzeltmeler/` altına yazar.
- **Parti 0 (deneme, 5 Ekim):** 200 tohum → 184 aile → **310 yeni kelime**, 342 anlam (48 kelime reddedildi, 110'u zaten vardı). Gemini 393 anlamdan 46 karşılığı düzeltti, 39 anlamı sildi. **Gerçek maliyet ~0,54 $ (≈ 1,75 $ / 1.000 yeni kelime).** Claude denetimi `words/duzeltmeler/d_2026_10_05.py`: özel adların büyük harfi, 13 zayıf karşılık, 3 silme (argo/aşağılayıcı/gereksiz), 2 uygunsuz örnek cümle (~%5 anlamda düzeltme).
- **Parti 1–3 (5 Ekim, 769'ar tohum):** 1.254 + 1.112 + 1.006 yeni kelime; maliyet ~2,11 + 1,99 + 1,81 $. Dört partinin toplamı **3.682 kelime, ~6,45 $**. Claude denetimi aynı dosyada (`uygula_1/2/3`): sayı kelimeleri (18.16), argo, aşağılayıcı ve cinsel anlamlar, özel adların büyük harfi, zayıf karşılıklar. Kalan: parti 4 (766 tohum) ve "incelenecek" aileler; Efe ile konuşulduktan sonra.
- **Hattın tuzağı:** hat kelimenin sözlükte olup olmadığına büyük-küçük harfe duyarlı bakar; silinen ya da büyük harfe çevrilen kelimeler sonraki partide yeniden üretilir. Çare: `kopyalari_sil()` ve ara deponun `kararlar.json`'ına `cikar`. `cikar` **taslağın kendi kökünde** uygulanır (ailenin son kökünde değil), bu yüzden kelimeyi içeren her taslağın köküne yazılmalı (replicant, "replica" taslağından sızmıştı).
- **Parti 4 (5 Ekim, 766 tohum):** 916 yeni kelime, ~1,7 $ (tahmini; doldurma bilgisayar uykuya geçince takıldı, süreç durdurulup yeniden başlatıldı, yazılmış aileler atlandığı için kayıp olmadı). Beş partinin toplamı **4.598 kelime, ~8,1 $**. Claude denetimi `uygula_4`. Kalan: "incelenecek" aileler (Efe ile).

### 18.36 En temel kelimeler elle eklenecek (Efe'nin kararı, 5 Ekim) — **yayından önce yapılacak (Efe, 10 Ekim; 18.38)**
- Sözlükte bazı en temel kelimeler yok: the, a, an, I, he, we, my, your, they, which, because, although, however, instead, though, would, could, myself, everyone… (tam liste `listeler/2026-10-05-temel-eksikler.txt`, 54 kelime).
- Bunlar çoğunlukla dilbilgisi kelimeleri (zamir, belirteç, bağlaç, kip). Model hattı bunlarda zayıf kalır; **Claude elle yazar** (API yok, eksik Oxford kelimeleri gibi `veri/…/*.jsonl` + `manage.py elle_kelime_yukle`). Anlam ve örnekler öğrencinin gerçekten kullanacağı biçimde (ör. "although = -e rağmen, -diği hâlde").
- Bu kelimelerin kartı ve L&P'deki yeri ayrıca düşünülür (çok sık oldukları için L&P'de ağırlık formülü onları baskın çıkarabilir; 18.16).

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
| 8 | Adresler ve SEO (kademeli dizine alma) — **yapıldı** | 18.15 | yok |
| 9 | 5'er örnek | 18.14 | yok |
| 10 | Tailwind derleme + beyaz tema + yazı boyutları | 18.17, 18.12 | tema tasarımı |
| 11 | Google ile giriş | 18.21 | Efe'nin OAuth istemcisi |

**1 Ekim durumu:** 8. adım (günün kelimesi, misafir, bildirim izni) ve 9. adım (istatistik, özetler) yapıldı.

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

### 18.37 Ağır işler istekten ayrıldı (Efe'nin isteği, 10 Ekim) — **YAPILDI**
- **Kuyruk zaten vardı:** değerlendirilemeyen yazı `bekliyor` durumunda kalır ve `yazilari_yeniden_dene` onu yeniden dener. Yeni bir kuyruk tablosu ya da iş parçacığı havuzu eklenmedi; bu yapı ana yol olarak sağlamlaştırıldı.
- **Cron:** `*/15 * * * *  cd <proje> && <python> manage.py yazilari_yeniden_dene` (barındırmanın izin verdiği en sık aralık). Bir çalıştırmada en çok 5 metin; son 10 dakikada denenmiş metin atlanır; önceki çalıştırma sürüyorsa yenisi çıkar (kilit `sinir` önbelleğinde, 20 dk).
- **Metin değerlendirme** (`texts/views.py`): aynı anda en çok 4 değerlendirme (`ESZAMANLI_DEGERLENDIRME`); fazlası Gemini'ye gitmeden "yoğun" der, metin kaydedilir, cron dener. İş parçacığı 180 sn ses vermezse (süreç öldü) ilerleme çubuğu takılı kalmaz: "servis cevap vermedi" der, metin `bekliyor` kalır.
- **`sleep(13)`:** kullanıcının beklediği değerlendirmede artık uyunmaz (`gemini.generate(bekle=False)`); onların sınırı `texts/limits.py`'deki dakikalık sayaç. Cron ve toplu komutlar eskisi gibi bekler.
- **PDF** (`readings/views.py`): aynı anda en çok 2 PDF okunur (`ESZAMANLI_PDF`), kullanıcı başına saatte 20 PDF (`PDF_SAATTE`). PDF isteğin içinde okunmaya devam ediyor (400 sayfa birkaç saniye); kuyruğa almak kullanıcıyı 15 dakika bekletirdi.
- **"Yer" sınırı** `LearnVocab/sinir.py`'de (`yer_al` / `yer_birak`): her iş zaman damgalı yer alır; süreç ölürse yer süre sonunda kendiliğinden boşalır.
- **Düzeltme:** sabit pencereli sayaçlar dosya önbelleğinde her artışta 1 saate uzuyordu (Django'nun `incr`'i süreyi sıfırlıyor). Sayaç artık pencerenin bitişini kendisi tutuyor.

### 18.38 Yayından önce eklenecekler (Efe'nin kararı, 10 Ekim) — **açık**
Bilkent listeleri eşleştirilirken çıktı (D7, `veri/hazir_listeler/bilkent-sozlukte-yok.txt`). Yayından önce sözlüğe eklenir; eklenince ilgili Bilkent listelerine de eklenir.
- **Phrasal verb'ler:** sözlükte yalnızca 52 tane var, en yaygınların bir kısmı yok: give up, find out, look forward to, come up with, get rid of, end up, point out, try on, get on… ODTÜ 401'den de: carry on, take on, bring up, make up, take place, carry out, turn out, figure out, deal with, put up with, stand for, set up, turn down, miss out… (`veri/hazir_listeler/odtu-401-sozlukte-yok.txt`). Önce en sık kullanılanların bir listesi çıkarılır (sıklık ve kurum listeleri), sonra eklenir.
- **En temel kelimeler (18.36):** both, yet, instead, the, because, although… `listeler/2026-10-05-…` listesi ve Bilkent'te çıkanlar.
- **Deyimler ve kalıplar (Efe'nin kararı, 10 Ekim: şimdilik not):** High Note 5'teki 478 deyim, kalıp ve phrasal verb sözlükte yok (get cold feet, in a nutshell, give sb the cold shoulder, keep an eye on sb, take issue with…): `veri/hazir_listeler/high-note-5-deyimler.txt`, ünite ünite. Sözlüğe **ifade** olarak eklenmeye uygun (Expression; şu an 295); eklenince High Note 5 listesine de bağlanır. Ayrıca türü yazan ama sözlükte olmayan 187 kelime (çoğu birleşik sıfat: laid-back, absent-minded, self-aware…): `high-note-5-sozlukte-yok.txt`.
- **Ülke ve milliyet adları:** sözlükte yok (Argentina/Argentinian, Brazil/Brazilian, Turkish, British…; Speakout Unit 1). Özel isimler sözlüğe nasıl girecek, ayrıca konuşulur: `veri/hazir_listeler/odtu-101-sozlukte-yok.txt`.
- Yöntem (Claude elle mi, Gemini mi) Efe ile kararlaştırılır.

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
- **2026-09-30 (15):** Uygulama 6. adım yapıldı (18.15):
  - Yeni adres şeması (Türkçe, ASCII): `/sozluk/bank/`, `/listeler/…`, `/calismalar/…`, `/okumalar/…`, `/yazma/…`, `/seviye-testi/`, `/giris/`, `/kayit/`, `/profil/`, `/ayarlar/…`, uçlar `/api/…`. Eski adresler 301.
  - Kalıcı kelime sayfaları (başlık, açıklama, canonical, JSON-LD, konum satırı); `?q=` tam eşleşmede 301, gerisi `noindex`.
  - Beyaz listeli `noindex`, `robots.txt`, `sitemap.xml`, göz atma sayfaları, dil öneki altyapısı (yalnızca Türkçe yayında).
  - Kademeli dizine alma: `Word.dizinde`, `manage.py dizine_ac`; 1. parti (A1–B1 Oxford, 2.080 sayfa) açıldı.
  - Plandan sapma: hesap sayfaları `robots.txt` yerine `noindex` ile kapatıldı (Google `noindex`'i ancak sayfayı açabilirse görür).
  - 904 test geçiyor.
- **2026-09-30 (16):** Efe'nin kararları: bölümün adı **Yazılar** (İngilizcesi Writings), adresi `/yazilar/`; örnek cümlede kelimeye çift tıklanınca o kelime aranır (yapıldı).
- **2026-09-30 (17):** Uygulama 7. adım yapıldı:
  - Kayıt formu (ad, soyad, e-posta, kullanıcı adı, tek şifre + göster/gizle); "kur" (`User.level`) ve günlük hedef (`UserSettings.dailyGoal`) silindi (18.23).
  - Okumalar: gövdeler diskte sıkıştırılmış (`readings/depo.py`, `ozel_depo/`), 100 metin / 15 PDF / 400 sayfa / 50 MB, 1 haftalık çöp kutusu, bölüm bölüm okuma (18.24).
  - Gezinme: profil fotoğrafı → Hesap → Ayarlar; tema Ayarlar'da, varsayılan sistem teması (18.26).
  - 909 test geçiyor.
- **2026-10-01 (1):** Efe'nin kararları: Yazılar'ın İngilizce adresi ve adı `/en/writings/` · Writings; Ayarlar'da tekrar/yeni oranı kaydırma çubuğu (%10'luk adımlar) ve egzersiz soru sayısı 5/10/15/20. İkisi de yapıldı.
- **2026-10-01 (2):** Uygulama 8. adım yapıldı: günün kelimesi ve ifadesi (18.8; ifadeler yaygın 146 / az 149 işaretlendi), misafir kuralları (18.3, 2.3, 12.6), bildirim izni ön ekranı ve Ayarlar'da bildirim aç/kapat (18.29). Testler kendi önbelleklerini kullanıyor (gerçek önbellek klasörüne yazmıyor). 932 test geçiyor.
- **2026-10-01 (3):** Uygulama 9. adım yapıldı: admin istatistik ekranı (18.31, yalnızca toplu sayılar, 5 kişi eşiği) ve 90 günden eski karşılaşma kayıtlarının kişisiz günlük özete çevrilmesi (18.32, `karsilasma_ozetle`, gece cron'u).
- **2026-10-01 (4):** 18.28 (cut/put/hit 3 şıkla soruluyor) ve büyük harf düzeltmesi (harf duyarsız okuma sorgusu; 6 kelime büyük harfle; "oriental" isim silindi) yapıldı.
- **2026-10-01 (5):** Seviye testinin özet soruları yazıldı ve yüklendi (301 soru, `seviye/havuz/`).
- **2026-10-01 (6):** Boş havuzlara 5'er örnek yazılıp yüklendi (D2, D3, D5, D6, D7; `veri/ornek/`).
- **2026-10-01 (7):** Eksik Oxford kelimelerinden 522'si elle yazılıp eklendi (`veri/oxford_eksik/`, `elle_kelime_yukle`).
- **2026-10-01 (8):** Veri B aşaması için inceleme listesi hazırlandı (`ozetler/b-asamasi-inceleme.md`; değişiklik uygulanmadı). Seviye testi özet soruları tarayıcıda uçtan uca denendi.
- **2026-10-01 (9):** Telaffuz ses üretimi TAMAMLANDI: sözlükteki her kelime ve ifade için US + UK, 28.372 MP3 (218 MB), 0 hata, eksik yok.
- **2026-10-01 (10):** Tasarım oturumu başladı. Efe tema A'yı (Mürekkep) seçti. Misafir ana sayfasının görselli bir tanıtım sayfası olmasına karar verdi; örnek `ozetler/tasarim-ornekleri/` altında (uygulanmadı).
- **2026-10-01 (11):** Tanıtım ana sayfası taslağı "fazla klasik" bulundu; iki farklı konsept hazırlandı (`konsept-defter.html`, `konsept-oyna.html`; uygulanmadı).
- **2026-10-02 (1):** Efe defter yönünü seçti. Defter teması beş sayfaya uygulanmış örneklerle geliştirildi, ana sayfa zenginleştirildi (`ozetler/tasarim-ornekleri/defter/`; uygulanmadı).
- **2026-10-02 (2):** Defter teması siteye uygulandı: ortak katman (`static/css/defter.css`, Tailwind renk eşlemesi, 17 px kök yazı), yeni misafir ana sayfası (`words.gunun.defter_kelimeleri`), Sözlük kartı, Learn & Pass (dikkat dağıtıcısız, 18.10), Okumalar, yazı değerlendirmesi; diğer ekranlar ortak kalıplarla. 942 test geçiyor.
- **2026-10-02 (3):** Efe: "örneklerdeki sayfaları da yap". Kelime sayfası, Okumalar, okuma ekranı, Yazılar, serbest yazma, Learn & Pass açılışı, Egzersizler, Sözlük ve giriş/kayıt örneklerdeki düzenle baştan kuruldu. Kelime sayfasında bütün türler açık. 942 test geçiyor.
- **2026-10-02 (4):** Bütün sayfalar defter tasarımıyla sıfırdan kuruldu (ana sayfa girişli de zengin; egzersiz, seviye testi, Hesap, Ayarlar, Listem, göz atma, diyalog, metin ekleme). Egzersiz adları Kısa Sınav / Deneme Sınavı oldu; eş/zıt sorusuna renkli damga eklendi. 945 test geçiyor.
- **2026-10-02 (5):** Dil seçeneği kararları (düğmenin yeri, otomatik yönlendirme yok, arayüz dilinden bağımsız "Türkçe anlamlar" ayarı). Google ile giriş başladı: Efe OAuth istemcisini oluşturuyor.
- **2026-10-02 (6):** Alpine 3.17.4 sabitlendi (`static/js/`). Google ile giriş eklendi (django-allauth; yerelde Efe'nin denemesi bekleniyor). 948 test geçiyor.
- **2026-10-02 (7):** Yardım sayfası ve tanıtım videosu kararları (18.33: defter teması, her dile ayrı video, kapibara taslağıyla devam, yardım konuları). "Her yeni sürümde yapılacaklar" listesi açıldı (18.34): ekran görüntüleri her sürümde her dil ve görünüm için baştan hazırlanır.
- **2026-10-02 (8):** Tailwind derlemeye geçti (18.17 YAPILDI): Play CDN kalktı, `static/css/site.css` Standalone CLI ile derleniyor; derleme testi eklendi. 950 test geçiyor.
- **2026-10-02 (9):** Efe Google ile girişi yerelde denedi, çalışıyor (18.21). Kapibara taslaklarına başlandı.
- **2026-10-02 (10):** Kapibara çizimi Efe'nin örneklerine göre baştan yapıldı ve onaylandı (18.33): önden, ayakta, yetişkin, ağzı açık, iki diş; koyu temada çıkartma görünümü. Sitedeki geçici çizimin yerine kondu (9 poz). 950 test geçiyor.
- **2026-10-02 (11):** Yardım ve hakkında sayfası yazıldı (18.33): 9 rehber, 26 ekran görüntüsü (telefon, açık/koyu), Efe hakkında bölümü ve iletişim. Görüntüler yalnızca telefon görünümünde çekilir (18.34 güncellendi). 955 test geçiyor.
- **2026-10-03:** Dil seçeneğinin altyapısı (18.22): şablonlar ve kod çeviriye hazır, dil düğmesi, hesap dili, "Türkçe anlamlar" ayarı, seri penceresi defter temasında. `usersettings/0006` migration'ı ana veritabanına uygulandı (yedek migration'dan sonra alındı: `~/LearnVocab-yedekler/db.sqlite3.yedek-20261003-arayuz-dili-sonrasi`).
- **2026-10-05:** Dil seçeneği bitti, **tr, en ve de yayında** (18.22 YAPILDI). İngilizce ve Almanca çeviriler tamam; site haritası her dilin adresini `hreflang` karşılıklarıyla yazıyor. Yardım sayfasının görüntüleri üç dilde, iki temada yeniden çekildi (90 görüntü; Türkçe olanlar da dil düğmesiyle yenilendi); Ayarlar rehberine "Dil" ve "Türkçe anlamlar" adımları eklendi, seri görüntüsü yeni pencereyle değişti (18.33). Yüzdeler dile göre yazılıyor. 18.34'e çeviri komutları eklendi, 18.30'a dil maddeleri. 975 test geçiyor.
- **2026-10-05 (2):** Dil düğmesi `/en/` ve `/de/` sayfalarından başka dile geçemiyordu; düzeltildi. Hazır listelerin adı ve açıklaması dile göre (`words/0026`, ana veritabanına yedekten sonra uygulandı: `~/LearnVocab-yedekler/db.sqlite3.yedek-20261005-hazir-liste-cevirileri`; örnek listenin çevirileri yazıldı). Ayarlar'da kaydet düğmesi kalktı, her değişiklik anında kaydediliyor; "Türkçe anlamlar" Dil'in hemen altına taşındı (Efe'nin kararları, 18.26). Yardım sayfasının Ayarlar görüntüleri üç dilde yeniden çekildi. 978 test geçiyor.
- **2026-10-05 (3):** Okuma metinlerinin kaynak satırı İngilizce ve Almanca sayfalarda kendi dilinde (Efe'nin isteği). 979 test geçiyor.
- **2026-10-05 (4):** Sözlüğü genişletme kararı (18.35): wordfreq'ten aday listesi çıkarıldı (4.026 kelime, zipf ≥ 3); hat 25 Eylül'deki gibi, ücretli Gemini, bütçe 5–10 $. En temel kelimeler (the, because, although…) elle eklenecek (18.36, sonra).
- **2026-10-05 (5):** NAWL indirildi ve listeye eklendi; genişletmenin deneme partisi çalıştırıldı: 310 yeni kelime, ~0,54 $; Claude denetimi `d_2026_10_05.py` (18.35).
- **2026-10-05 (6):** Genişletme parti 1–3: 3.372 yeni kelime (toplam 3.682, ~6,45 $), Claude denetimi `uygula_1/2/3`; `cikar` kararının taslak kökünde uygulandığı not edildi (18.35). Parti 4 Efe'yi bekliyor.
- **2026-10-05 (7):** Genişletme parti 4: 916 yeni kelime (toplam 4.598, ~8,1 $), Claude denetimi `uygula_4` (18.35).
- **2026-10-06:** 18.7 B aşamasının ilişki kısmı yapıldı: eş/zıt/daha basit bağları Claude tarafından elle okundu (API yok). 18.6 yeniden uygulandı (genişletmenin eklediği 1.601 bağ), tür uyuşmazlığı temizlendi, elle okumayla kalanlar ayıklandı: 65.932 bağdan 14.390'ı silindi, 230'u taşındı. Efe'nin kararı: zayıf bağlar silinmez, `ozetler/zayif-baglar.tsv`'ye yazılır (11.820 bağ, Efe inceleyecek). Okurken görülen 10 anlam hatası düzeltildi. Kod `words/duzeltmeler/d_2026_10_06.py`, kararlar `veri/iliski_denetimi/`. 979 test geçiyor.
- **2026-10-07:** 18.7 B aşamasının tanım, kalıp ve örnek kısmı yapıldı (API yok). Efe'nin kararı: kalıp gösterimi `sb` / `sth` / `doing sth` / `to do sth` / `that …`; "+" ve "noun" gibi terimler yok; arayüzde "sb: birisi · sth: bir şey" açıklaması (Bölüm 4). 667 tanım düzeltildi; 44.537 kalıptan 24.399'u silindi (7.577 mekanik, 16.822 elle), 21.337'si mekanik olarak biçimlendi, 9.888'i elle düzeltildi, 20.138 kaldı; 430 zayıf kalıp `ozetler/zayif-kaliplar.tsv`'ye yazıldı; 101 örnek yeniden yazıldı. Bağlayıcı ifade kalıpları (`veri.py`, 293 ifade) çevrildi. Zenginleştirme hattı kalıpları `bicimle()` ile denetliyor. Kod `words/duzeltmeler/d_2026_10_07.py`, kararlar `veri/kalip_denetimi/`, `veri/tanim_denetimi/`. 980 test geçiyor.
- **2026-10-08:** Almanca arayüz yayından kaldırıldı (Efe'nin kararı; 18.22): yayında tr ve en, eski `/de/` adresleri Türkçesine 301. Güvenlik ve yük: (1) önceden açılmış hesapla ele geçirme incelendi; allauth 65, e-postası doğrulanmamış hesaba Google ile girilince şifreyi siliyor ve saldırganın oturumu düşüyor; kayıt formu e-postayı doğrulanmış saymadığı için korunuyoruz, `users/test_hesap_guvenligi.py` bunu kanıtlıyor. (2) İstek sınırları (`LearnVocab/sinir.py`, ayrı `sinir` önbelleği): `/api/kelime/` adres başına dakikada 120; `BulunamayanArama` yeni satırı adres başına saatte 30, günde 2.000, toplam 50.000 sınırlı; giriş adres başına 15 dakikada 20, hesap başına 10 hatalı deneme; kayıt adres başına saatte 10; şifre sıfırlama kodu adres başına saatte 10. (3) Misafir L&P aday havuzları bir saat önbellekte (açılış 6 → 3 sorgu). 987 test geçiyor.
- **2026-10-10:** 7–8 Ekim işleri commit edildi. Ağır işler (18.37): değerlendirme ve PDF için eşzamanlı iş sınırı, takılan iş çubuğu, kullanıcı beklerken `sleep` yok, cron 15 dakikada bir ve kilitli; istek sınırı sayaçlarının pencere hatası düzeltildi. KVKK aydınlatma metni (18.19): `/gizlilik/` tr ve en, kayıtta zorunlu "okudum" kutusu, Google düğmesinin altında not; `users/0007` ana veritabanına yedekten sonra uygulandı (`~/LearnVocab-yedekler/db.sqlite3.yedek-20261010-aydinlatma-oncesi`). 1000 test geçiyor.
- **2026-10-10 (2):** Efe doğruladı: barındırma Veridyen, sunucular Türkiye'de (18.19).
- **2026-10-10 (3):** Chrome eklentisi v1'e alındı ve yazıldı (Efe'nin kararı; rapor 11): çift tıklama, dışarı tıklayınca kapanma, "Listeme ekle +" sitedeki oturumla, "Oxford'da ara" aynı sekmede; günlük/saatlik sınır yok, dakikalık bot sınırı 300. Ana sayfaya eklenti bölümü, aydınlatma metnine eklenti maddesi. Yayın yeni sürümün yayına alınmasını bekliyor. 1006 test geçiyor.
- **2026-10-10 (4):** Efe eklentiyi yerelde denedi, "Listeme ekle" dahil çalışıyor (yerel kopya 8000 portunda; Google girişi Console'da orada kayıtlı). Telefon için Android paylaş menüsü: `share_target` ve `/paylas/` (rapor 11). 1010 test geçiyor.
- **2026-10-10 (5):** D7: Bilkent ELPP 2025-26'nın beş seviye listesi yüklendi (3.434 kelime; Efe'nin kararları: yalnızca 2025-26 dosyası, seviye başına bir liste, tam seviye adı, seviyeler arası tekrar serbest). Örnek "Akademik fiiller" listesi kaldırıldı. Yedek: `~/LearnVocab-yedekler/db.sqlite3.yedek-20261010-bilkent-oncesi`. 1010 test geçiyor.
- **2026-10-10 (6):** Hazır listelerde "Bu listede ara" (yazdıkça süzülür). 18.38 açıldı: phrasal verb'ler ve en temel kelimeler yayından önce eklenecek (Efe'nin kararı). Bölüm 16'ya "hazır listeyi topluca ekleme" konuşması eklendi. 1015 test geçiyor.
- **2026-10-10 (7):** D7: ODTÜ 401'in dört span listesi (1.426 kelime), hafta hafta; kelimeler Claude'un elle denetimiyle seçildi. Hazır listelere bölüm (hafta) alanı, başlıkları ve hafta düğmeleri (`words/0027`, ana veritabanına yedekten sonra uygulandı: `~/LearnVocab-yedekler/db.sqlite3.yedek-20261010-bolum-oncesi`). 1019 test geçiyor.
- **2026-10-10 (8):** ODTÜ 401 listeleri belgedeki kalın kelimelerden yeniden çıkarıldı (Efe'nin uyarısı); ODTÜ 301'in dört span listesi eklendi (1.610 kelime; bölümler RHO / Handout / Unit / hafta). Liste sayfasında seçili bölüm hatası düzeltildi. Yedek: `~/LearnVocab-yedekler/db.sqlite3.yedek-20261010-odtu301-oncesi`. 1019 test geçiyor.
- **2026-10-10 (9):** ODTÜ 201'in dört span listesi (1.545 kelime, hafta hafta); 201'de hedef kelime kalın olmadığı için kalıplardaki bütün içerik kelimeleri alındı (Efe'nin kararı). Yedek: `~/LearnVocab-yedekler/db.sqlite3.yedek-20261010-odtu201-oncesi`. 1019 test geçiyor.
- **2026-10-10 (10):** ODTÜ 501 Span 1–2 (472 kelime) ve High Note 5 (474 kelime, Unit 1–7) eklendi; High Note'un 478 deyimi 18.38'e not edildi (Efe'nin kararı). Yedek: `~/LearnVocab-yedekler/db.sqlite3.yedek-20261010-odtu501-oncesi`. 1019 test geçiyor.
- **2026-10-10 (11):** ODTÜ 101 Span 1 (380 kelime; OLR 0.5 altı çizili + RHO kalın, hafta hafta) ve Speakout A0–A1 (417 kelime, ünite ünite). Yedek: `~/LearnVocab-yedekler/db.sqlite3.yedek-20261010-odtu101-oncesi`. 22 hazır liste.
