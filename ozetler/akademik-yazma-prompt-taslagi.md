# Akademik yazma değerlendirmesi — prompt taslağı (17 Ekim 2026, Claude)

Kaynak: Forefront, *Avoiding Plagiarism* + *Writing Focus: Features of Academic Writing* (s. 10–35, 26 sayfa, taranmış PDF; metin macOS Vision ile yerelde OCR'landı). Gemini'nin özeti: `veri/kalite_olcumu/akademik-yazma-degerlendirme-kriterleri.md`. Bu dosya taslaktır; uygulanmadı.

## 1. Gemini'nin özeti kaynağa göre nasıl?

Genel olarak sadık ve kullanışlı. Kitapta OLMAYAN ya da yoruma dayanan yerler:

| Gemini'de | Kitapta |
|---|---|
| 8 intihal senaryosunun "karar"ları (Senaryo 6 ihlal, 8 kabul…) | Kitap yalnızca soruyor, cevap vermiyor. Kararlar Gemini'nin yorumu (çoğu makul; kitap s. 10'da yapay zekâ kullanımının "teknik olarak intihal sayılmayabileceğini ama kopya sayıldığını" da söylüyor). |
| `not much → little`, `not many → few` | Kitapta yok; kitap yalnızca `There is not any evidence → no` diyor. |
| Task 8 ve mantık hataları tablosundaki "doğrusu" yeniden yazımları | Kitap alıştırma olarak bırakıyor; yeniden yazımlar Gemini'nin. |
| 8 öğrenci ↔ geri bildirim eşleştirmesi | Kitapta cevap yok. Gemini'nin eşleştirmesinde bir hata var: C ("none of these young people stand a chance") Öğrenci 5'e, E ("no improvement in the last 50 years") Öğrenci 3'e uyuyor; Gemini 3'e ikisini verip 5'e A demiş (A, Öğrenci 7'nin: "kids", "they're", "the saddest thing"). |
| `good → beneficial/harmful` (Bölüm 7) | Tabloda `good → valuable/positive/useful`, `bad → negative/harmful`. |
| `I think → It can be argued that` | Kitap "I think …" cümlesini uygunsuz örnek olarak veriyor ama karşılık önermiyor; öneri Gemini'nin (makul). |

## 2. Kitabın hangi kuralları bizim kısa yazma alıştırmamızda denetlenebilir?

Öğrenci 1–3 paragraf yazıyor, kaynak okumuyor, kaynakça eklemiyor. Bu yüzden:

- **Denetlenir (metinden alıntılanabilir, cümle düzeyinde):** kısaltmalar · gündelik kelime/ifade ve tek kelimelik karşılığı olan phrasal verb'ler · okuyucuya hitap (`you`, retorik soru, ünlem, emoji, `...`) · dayanaksız kişisel görüş (`I think`) · cinsiyetçi dil · gereksiz uzatma · belirsiz ifade · kanıtsız mutlak ifade (hedging eksikliği) · kişisel anekdotu kanıt sayma · duygusal dil · 8 mantık hatası · konudan sapma geçişleri (`by the way, turning to…`).
- **Denetlenmez:** intihal ve yapay zekâ kullanımı (tespit edilemez), atıf biçimi ve kaynakça, başlık/alt başlık, türün tam yapısı (lab raporu vb.), "araştırmaya dayan" kuralının kendisi (öğrenciden kaynak istenmiyor; yalnızca anekdot/duygu kanıt yerine konunca hata).
- **Dikkat (aşırı düzeltme riski):** `I` her zaman hata değil (`I argue that`, `I will first discuss`, `I agree with X's view` uygundur; kitap s. 19–21). `get, good, big, thing, keep, stay, happen` gibi kelimeleri her geçtiği yerde işaretlemek metni boğar; yalnızca açıkça gündelik ya da belirsizse. Zaten ihtiyatlı olan ifadeye ve kanıtlanmış genel gerçeğe hedging istenmez.

## 3. Önerilen yapı (karar Efe'nin)

- **Yazı türü:** Günlük / Akademik. Varsayılanı Ayarlar'da (Çalışma › Yazma), her metinde yazma ekranında değiştirilebilir. Sertlik (Nazik/Normal/Titiz) iki türde de kalır: akademikte en çok 4 / 8 / 12 hata.
- **Uzunluk:** akademikte en çok ~3.000 karakter, yönlendirme "1–3 paragraf". Günlük değişmez (1.500).
- **Puan:** tek 1–5 puan (rubrik/kırılım yok — rapor Bölüm 16). Akademikte üslup ve mantık sorunları puanı düşürür; puanın yanında "akademik" etiketi.
- **Konu önerileri:** akademikte tartışma konuları (kitabın kendi soruları gibi: "Should English be compulsory in schools?", "Has social media weakened offline relationships?" …).
- **Zaman aşımı:** akademik çağrıda 60 sn (çağrı başına verilebiliyor).
- **İsteğe bağlı:** her hataya kısa bir tür etiketi (`resmî dil`, `ihtiyatlı dil`, `nesnellik`, `mantık`, `dilbilgisi`) — öğrenci hangi kuralı çiğnediğini görür; şemaya bir alan eklenir.
- **Açık soru:** metnin bütününe dair yapı sorunları (tez cümlesi yok, paragraf tek fikre odaklanmıyor) metinden alıntılanamaz. Ya hiç yazılmaz (önerim) ya da tek cümlelik bir "yapı notu" alanı açılır — bu, vazgeçilen "Geliştirilebilir" bölümüne yaklaşır.

## 4. Prompt taslağı (akademik bölümü)

Günlük prompt'taki giriş paragrafı, kural 3'ün "üslup hata değildir" satırı ve kural 5 akademik türde şununla değişir. Diğer kurallar (dil, JSON, alıntı, kullanılan kelimeler, markdown yok) aynen kalır.

```
Sen İngilizce öğrenen Türk üniversite öğrencilerine akademik yazmayı öğreten, sıcak ama titiz bir öğretmensin.
Öğrenci kısa bir AKADEMİK İngilizce metin yazdı (1–3 paragraf). Kaynak okuması ya da kaynakça eklemesi
BEKLENMİYOR; atıf biçimi, başlıklar ve intihal DENETLENMEZ. Metni hem dilbilgisi hem de aşağıdaki akademik
yazım kurallarına göre değerlendir.

AKADEMİK HATALAR (her biri "hatalar" listesine ayrı madde olur; "dogrusu" akademik karşılıktır):
A. Resmî dil
  A1. Kısaltmalar: don't, can't, it's, they're, haven't → do not, cannot, it is, they are, have not.
  A2. Gündelik kelime ve ifadeler — YALNIZCA açıkça konuşma diliyse: kids, stuff, lots of, a lot of, kind of,
      gonna/wanna, like (= such as), etc., by the way, on top of that, after all (geçiş olarak) → children,
      materials, many/numerous, partly, going to/want to, such as, and so on, furthermore/in addition.
      Tek kelimelik akademik karşılığı olan phrasal verb'ler: look at → examine, look into → investigate,
      find out → discover/conclude, go up → increase/rise, build up → accumulate, get rid of → eliminate.
      get / good / big / thing / happen gibi kelimeleri yalnızca belirsizlik ya da açık gündelik ton yaratıyorsa yaz.
  A3. Okuyucuya hitap: you/your, retorik soru, ünlem, emoji, yarım bırakılan cümle (...) →
      edilgen çatı ("It can be observed that"), üçüncü şahıs ("students ... they") ya da "one".
  A4. Dayanaksız kişisel görüş: "I think", "I feel", "In my opinion" → "It can be argued that", "This suggests that".
      DİKKAT: "I argue that", "I will first discuss", "I agree with X's view that" HATA DEĞİLDİR.
  A5. Cinsiyetçi dil: mankind, freshman, "every student ... he/she" → humanity, first-year students, "students ... they".
  A6. Gereksiz uzatma: due to the fact that → because; inside of → inside; in spite of the fact that → although.
  A7. Belirsiz ifade: "around 1000", "many people", "some reasons", "things" → daha kesin bir ifade
      ("approximately 1,000", "a majority of the participants", reasons adlarıyla).
B. İhtiyatlı dil (hedging)
  B1. Kanıtsız mutlak ya da buyurgan ifade: always, never, all/everyone, definitely, certainly, obviously,
      impossible, will (kesin tahmin), must/should (buyurgan) → often, rarely, many/most, likely to, may, can,
      tend to, suggest. Kanıtlanmış genel gerçeklere ve zaten ihtiyatlı ifadelere DOKUNMA.
C. Nesnellik ve mantık
  C1. Kişisel anekdotu kanıt olarak sunma (my neighbour, my friend, in my family) → genel ve kişisiz ifade.
  C2. Duygusal dil (the saddest thing, it makes me sad, terrible) → nötr ifade.
  C3. Mantık hataları: aceleci genelleme, aşırı basitleştirme, kaygan zemin, sahte ikilem, konuyu saptırma,
      çoğunluğa başvurma, duygu sömürüsü, varsayımı olgu gibi sunma. "neden"de hatanın Türkçe adını söyle
      ve tek cümleyle açıkla; "dogrusu" dengeli bir yeniden yazım olsun.
  C4. Konudan sapma geçişleri ("By the way, turning to the previous issue") → paragrafı tek fikre bağlayan bir geçiş.

ALINTI: Her zaman metinden HARFİ HARFİNE, 2–10 kelimelik kesintisiz bir parça seç; tek kelime alıntılama
("you" değil "you can see"). Aynı sorun birkaç yerde varsa her yer ayrı madde; sınır dolacaksa en önemlilerini
seç. "dogrusu" ASLA boş ya da alıntıyla aynı olmasın.
ÖNCELİK: anlamı bozan dilbilgisi > mantık ve nesnellik (C) > ihtiyatlı dil (B) > resmî dil (A).
"iyi": akademik güçlü yanları öv (ihtiyatlı dil, resmî kelime, edilgen çatı, açık konu cümlesi, bağlaçlar).

PUAN (akademik): 5 = dilbilgisi sağlam, resmî ve ihtiyatlı, kişisel/duygusal dil yok · 4–4.5 = birkaç üslup
kusuru · 3.5 = belirgin gündelik dil ya da kanıtsız genellemeler · 3 = metnin çoğu sohbet dilinde ya da mantık
hataları var · 2 = akademik metin özelliği neredeyse yok ya da dilbilgisi anlamı bozuyor.
```

## 5. Doğrulama önerisi

Kitabın 8 öğrenci alıntısı (s. 15–16) ve mantık hatası örnekleri (s. 35) hazır bir **altın test seti**: her birinde neyin yakalanması gerektiği belli (Öğrenci 1: certainly/obviously · 2: you, retorik soru · 3: no improvement, do not have a chance · 4: on top of that, by the way · 5: genelleme · 6: komşu anekdotu, open new doors · 7: kids, they're, haven't, the saddest thing · 8: sahte ikilem). Prompt bu 8 + 8 metinde çalıştırılıp beklenen maddelerin yakalanıp yakalanmadığı ve yanlış alarm sayısı ölçülür (Gemini ücretsiz katman, ~16 çağrı).

## 6. Deneme sonucu (17 Ekim, gerçek Gemini, sertlik Normal)

16 örnekten 14'ü sonuçlandı (O7 dakikalık, M8 günlük kotaya takıldı). Betik ve ham çıktı scratchpad'de (`akademik_deneme.py`, `akademik_sonuc.json`); öğrenci alıntılarının yarım cümleli baş/sonlarına kısa nötr tamamlamalar eklendi.

- **Beklenen ifadeyi yakalama:** 17/20 (%85). Öğrenci alıntıları 10/13: certainly/obviously, you/retorik soru, on top of that/by the way, komşu anekdotu hep yakalandı. Kaçanlar: O3 "no improvement" (üstelik "iyi" diye övüldü), O6 "open new doors" (mecaz), O8 sahte ikilem. Mantık hatası örnekleri 7/7 yakalandı **ama hatanın adı yalnızca 1'inde (M5) söylendi**; diğerleri yalnızca "ihtiyatlı dil" diye düzeltildi (M7 retorik soru olarak).
- **Yanlış/sorunlu maddeler:** O8 "After all" → "In addition" (anlam değişti); O8 "is therefore only likely to" (zaten ihtiyatlı) işaretlendi; M2 "memorizing → memorization" (gereksiz); M1'de aynı alıntı hem "iyi" hem "hata" (iki kez); M2'de mantık hatası taşıyan cümle "iyi" diye övüldü.
- **Puan:** 14 metnin 10'u 3,5; ayırt ediciliği düşük. Mantık hatası örneği M2 4,5 aldı.
- **Süre:** 9–45 sn (503'te yeniden deneme dahil); 60 sn yetiyor.
- **Kota:** gemini-3.6-flash ücretsiz katmanı proje başına **dakikada 5, günde 20 istek**. 429'da kod yedek modele geçmiyor (yalnızca 503'te geçiyor).

**Önerilen prompt düzeltmeleri:** (1) Mantık hatasında "neden" alanı hatanın adıyla başlasın ("Mantık hatası (sahte ikilem): …"); önce C kuralları taransın. (2) B1 listesine olumsuz mutlaklar: no, none, nothing, any, "do not have a chance". (3) A2'ye mecaz/deyim (open new doors, a way out). (4) "dogrusu" anlamı korusun (after all → ultimately/indeed). (5) Zaten ihtiyatlı ifadeler (likely, may, often, tend to) işaretlenmez. (6) Puan için sayıya dayalı çapa (mantık hatası varsa en çok 3,5; birden çoksa 3). **Kod:** "iyi" alıntısı bir hata alıntısıyla çakışıyorsa at.
