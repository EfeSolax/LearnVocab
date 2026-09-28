# Diyalog havuzu (D6) — veri biçimi

"Diyalogda doğru kelime" (ürün raporu 9.2) diyalogları canlı üretmez; önceden
üretilmiş ve **denetlenmiş** bir havuzdan gelir. Havuz `texts.Diyalog`
tablosunda durur ve bu komutla yüklenir:

```
python manage.py diyalog_yukle havuz.json --dry-run   # önce kontrol (rapor 12.8)
python manage.py diyalog_yukle havuz.json             # sonra gerçek yazım
```

Dosya bir JSON listesi (`[ {...}, {...} ]`) ya da JSONL (her satırda bir kayıt) olabilir.

## Bir kayıt

```json
{
  "kelime": "postpone",
  "tur": "verb",
  "anlam": "ertelemek",
  "satirlar": [
    {"kisi": "A", "metin": "Are we still meeting on Friday?"},
    {"kisi": "B", "metin": "No, the manager ___ it until next week."},
    {"kisi": "A", "metin": "Oh, why?"},
    {"kisi": "B", "metin": "Half of the team is away at a conference."}
  ],
  "cevap": "postponed",
  "ipucu": "ertelemek",
  "not": "Resmî bir kelime. Arkadaşlar arasında 'put off' daha doğal duyulur.",
  "register": "formal",
  "sentiment": "neutral",
  "cefr": "B2",
  "denetlendi": true,
  "kaynak": "d6-parti-1"
}
```

| Alan | Zorunlu | Açıklama |
|---|---|---|
| `kelime` | evet | Sözlükteki kelime (`Word.text`). Kullanıcının listesindeki kelimelerle eşleşir. |
| `tur` | kelime birden çok türde varsa | `noun`, `verb`, `adjective`, `adverb`, `phrasal_verb` … (`Word.pos`) |
| `anlam` | hayır | Hedeflenen anlamın Türkçesi (`Meaning.meaning_tr`, birebir). Verilirse anlam bağlanır. |
| `satirlar` | evet | **4–6 satır.** Her satır `{"kisi", "metin"}`. Bütün diyalogda **tam olarak bir** `___` (üç alt çizgi) olmalı. |
| `cevap` | evet | Boşluğa gelen yazım. Kelimenin kendisi ya da çekimli bir biçimi olmalı (`postponed`); değilse kayıt atlanır. |
| `ipucu` | evet | Boşluğun altında görünen Türkçe ipucu (`ertelemek`). |
| `not` | hayır | Cevaptan sonra gösterilen kısa Türkçe not: register (resmî/samimi) ya da duygu tonu. Boşsa `register`/`sentiment` etiketlerinden üretilir. |
| `register` | hayır | `neutral` (varsayılan), `formal`, `academic`, `informal`, `slang`, `literary` |
| `sentiment` | hayır | `neutral` (varsayılan), `positive`, `negative` |
| `cefr` | hayır | Boşsa kelimenin seviyesi kullanılır. |
| `denetlendi` | hayır | **Yalnızca `true` olanlar kullanıcıya gösterilir.** Varsayılan `false`. |
| `kaynak` | hayır | Hangi üretim partisinden geldiği. |

## Değerlendirme kuralları (kullanıcının cevabı)

- Büyük/küçük harf, baştaki/sondaki boşluk ve noktalama önemsenmez.
- `cevap` ya da kelimenin herhangi bir çekimli biçimi (`WordForm` + `words.inflect`) **doğru** sayılır; farklıysa "Bu cümlede: postponed" notu çıkar.
- Tek harf farkı (eksik, fazla, yanlış ya da yer değiştirmiş harf) **"Neredeyse! Doğrusu: postponed"**. 4 harften kısa cevaplarda uygulanmaz (do/go).
- Diğer her şey yanlış; doğrusu gösterilir.

## Üretim ve denetim notları

- Aynı kelime + aynı satırlar ikinci kez yüklenirse yeni kayıt açılmaz, güncellenir.
- Hassas ve müstehcen içerik yazılmaz (rapor 12.2).
- Boşluk hedef kelimeden başka bir kelimeyle de doğal biçimde doldurulabiliyorsa diyalog değiştirilmeli: tek doğru cevap olmalı.
- Diyalog kısa ve gündelik olmalı; ipucu hedef anlamı açık etmeli.
