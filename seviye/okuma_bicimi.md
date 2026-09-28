# Seviye testi okuma havuzu (D4) — veri biçimi

Seviye testinin 2. kısmı (ürün raporu 7) canlı üretilmez; önceden üretilmiş ve
**denetlenmiş** bir havuzdan gelir (~100 metin). Havuz `seviye.OkumaSorusu`
tablosunda durur ve bu komutla yüklenir:

```
python manage.py seviye_okuma_yukle havuz.json --dry-run   # önce kontrol (rapor 12.8)
python manage.py seviye_okuma_yukle havuz.json             # sonra gerçek yazım
```

Dosya bir JSON listesi (`[ {...}, {...} ]`) ya da JSONL (her satırda bir kayıt) olabilir.

**Havuz boşken** (ya da üç zorluğun birinde hiç denetlenmiş soru yokken) 2. kısım
bütünüyle atlanır ve seviye yalnızca kelime ekranlarından tahmin edilir.

## Bir kayıt

```json
{
  "zorluk": 1,
  "cefr": "A2",
  "metin": "Tom works in a small bakery. He starts work at five in the morning. He makes bread and cakes for the people in his town. In the afternoon he goes home and sleeps.",
  "dogru": "Tom is a baker who starts his day very early.",
  "celdiriciler": [
    "Tom buys bread from a small shop every morning.",
    "Tom does not like his job at the bakery.",
    "Tom sleeps in the bakery in the afternoon."
  ],
  "denetlendi": true,
  "kaynak": "d4-parti-1"
}
```

| Alan | Zorunlu | Açıklama |
|---|---|---|
| `zorluk` | evet | `1` kolay · `2` orta · `3` zor. Testte her zorluktan bir metin, kolaydan zora. |
| `cefr` | hayır | Metnin hedef seviyesi (A1–C2). Yalnızca denetim içindir. |
| `metin` | evet | 4–5 cümlelik kısa İngilizce metin (yükleyici 3–6 cümleyi kabul eder). |
| `dogru` | evet | Metni en iyi özetleyen cümle. |
| `celdiriciler` | evet | 2–4 çeldirici. Metinle ilgili görünmeli ama özeti **yanlış** ya da **eksik** vermeli; birden çok doğru şık olmamalı. |
| `denetlendi` | hayır | **Yalnızca `true` olanlar teste girer.** Varsayılan `false`. |
| `kaynak` | hayır | Parti adı vb. |

Aynı `metin` ikinci kez yüklenirse yeni kayıt açılmaz, diğer alanlar güncellenir.
