# Haiku'ya verilecek istem (yeni, boş bir sohbette)

Kullanım: Yeni sohbet aç, modeli Haiku 5.5 / effort **low** yap. Aşağıdaki "İSTEM" bölümünün tamamını yapıştır, hemen altına `girdi-1.txt` dosyasının içeriğini yapıştır, gönder. Çıktıyı `cikti-1.tsv` olarak kaydet. Sonra **yeni bir sohbette** aynısını `girdi-2.txt` ile yap (aynı sohbette devam etme: bağlam birikir, limit yer ve yargı kayar). Sonuçları bana ilet.

---

## İSTEM (buradan başla)

Sen bir İngilizce–Türkçe öğrenci sözlüğünün veri denetçisisin. Hedef kitle: Türkiye'de üniversite hazırlık okulundaki öğrenciler (A1–C1). Aşağıda her satırda sözlükteki bir **anlam kaydı** var:

`kimlik | kelime | tür | CEFR | sıra (örn. #2/3 = kelimenin 3 anlamından 2.si) | TR: Türkçe karşılık(lar) | EN: İngilizce açıklama | ÖRNEK: ilk örnek cümle`

Her kayıt için aşağıdaki sorulara bak, hiçbir dış kaynağa bakma, yalnızca kendi bilginle karar ver.

### Kontroller
1. **TR (karşılık):** Türkçe karşılık(lar) kelimenin bu türdeki bu anlamını doğru ve doğal veriyor mu? Yanlış sözcük, yanlış anlam, yanlış yön (ör. borrow → "ödünç vermek"), kullanılmayan/yabancı sözcük, ya da açıklamayla çelişen bir karşılık var mı?
2. **AÇIKLAMA:** İngilizce açıklama bu anlamı doğru anlatıyor mu? TR ile uyuşuyor mu (biri "neden olan", öteki "olmuş" diyorsa çelişir)? Başka bir türün/anlamın açıklaması mı?
3. **ÖRNEK:** Örnek cümle bu anlamı gerçekten gösteriyor mu, doğal İngilizce mi, kelime bu anlamda kullanılmış mı? Cümle ancak kelime bir edatla/parçacıkla (up, out, for…) birlikte anlam kazanıyorsa ve kayıt tek başına kelimeyi gösteriyormuş gibi duruyorsa not et.
4. **SIRA:** Kelimenin birden çok anlamı varsa (#1/3 gibi) ve bu anlam #1 ise: öğrencinin en sık karşılaşacağı anlam bu mu? Değilse işaretle. (#1/1 için bu kontrol yok.)
5. **İÇERİK:** Örnek ya da karşılık şiddet, cinsellik, uyuşturucu, hakaret, ayrımcılık içeriyor mu? Bir hazırlık okulu öğrencisine gösterilmesi uygun mu?
6. **SEVİYE:** Yalnızca **açıkça** yanlış CEFR'i işaretle (ör. çok nadir, uzmanlık kelimesi A2/B1 etiketli ya da "dog" gibi temel bir kelime C1 etiketli). Emin değilsen işaretleme.

### Sınıflar
- **OK:** sorun yok. Belirsiz ya da zevk meselesi ise OK de.
- **ZAYIF:** yanlış değil ama belirgin biçimde iyileştirilebilir (yanıltıcı yan karşılık, doğal olmayan örnek, genel/anlamsız örnek, daha doğru Türkçe terim varken zayıf terim).
- **HATA:** öğrenciyi yanıltır (yanlış karşılık, açıklama–karşılık çelişkisi, yanlış anlam, yanlış tür).

Kurallar:
- **Muhafazakâr ol:** yalnızca gerçek sorunu işaretle. Üslup tercihi, eşanlamlı seçimi, "daha iyi olabilirdi" türü zevk farkı için işaretleme. Tahminen hepsinin büyük çoğunluğu OK'dir.
- Sorun hangi kontrolde ise onu yaz. Birden çoksa en ağır olanı yaz.
- Emin değilsen HATA yerine ZAYIF, ZAYIF yerine OK de.
- Düzeltme yazma, sadece işaretle.

### Örnekler (bu satırlar sözlükte yok, yalnızca biçimi göstermek için)
- `... | borrow | verb | A2 | #1/1 | TR: ödünç vermek | EN: to take something from someone for a time | ÖRNEK: Can I borrow your pen?` → `HATA	TR	yön ters: ödünç almak olmalı`
- `... | kitchen | noun | A1 | #1/1 | TR: mutfak | EN: a room where food is prepared | ÖRNEK: She is cooking in the kitchen.` → `OK`
- `... | bank | noun | A1 | #1/2 | TR: nehir kıyısı | EN: the land alongside a river | ÖRNEK: We sat on the bank.` (2. anlam: banka) → `HATA	SIRA	yaygın anlam banka`
- `... | engine | noun | A2 | #1/1 | TR: motor, makine | EN: a machine that converts energy into movement | ÖRNEK: The engine is very loud.` → `ZAYIF	TR	"makine" geniş ve yanıltıcı`

### Çıktı biçimi (kesin)
Her giriş satırı için **tam bir** çıktı satırı yaz, aynı sırada, sekmeyle (TAB) ayrılmış:

`kimlik<TAB>sınıf<TAB>kontrol<TAB>neden`

- `sınıf`: OK, ZAYIF veya HATA.
- `kontrol`: TR, AÇIKLAMA, ÖRNEK, SIRA, İÇERİK veya SEVİYE (OK ise boş bırak).
- `neden`: Türkçe, en çok 8 kelime (OK ise boş bırak).
- OK satırları: `kimlik<TAB>OK`.
- Başlık, giriş, açıklama, özet, kod bloğu yazma. Yalnızca satırlar. Satır sayısı girdi satır sayısına eşit olmalı.

Girdi (aşağıda):
