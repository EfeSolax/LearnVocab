# Kural taraması özeti

Veritabanı: `db.sqlite3`; 26392 anlam, 22286 kelime tarandı.

| Kural | Bulgu | Not |
|---|---|---|
| `r01_seviye` | 4099 | kelime düzeyinde; `learnvocab` etiketli, Zipf ile çelişen seviye |
| `r02_yalniz_parcacikli_fiil` | 48 | fiil anlamının tüm örnekleri 'X up/for…' |
| `r03_tur_uyumsuzlugu` | 0 | karşılığın -mak/-mek biçimi ile kelime türü uyuşmuyor |
| `r04_karsilik_bicimi` | 23 | q/w/x, yinelenen, çok uzun, boş parantez… |
| `r05_tanim_turu` | 24 | tanımın biçimi kelimenin türüne uymuyor |
| `r06_ornek_kalitesi` | 312 | çok kısa, şablon, 'textbook explains' örüntüsü |
| `r07_hassas_siddet` | 59 | mevcut hassas filtre + şiddet sözcükleri (örneklerde) |
| `r08_supheli_turkce` | 17 | altın etiketten tohumlanmış kötü karşılıklar listesi |
| `r09_yinelenen_anlam` | 4 | aynı kelimenin anlamları çakışıyor |
| `r10_anlam_sirasi` | 15 | 1. anlam sonrakilerden 2+ CEFR yüksek (sıra şüphesi) |

Birleşik: **4546** farklı anlam en az bir kural tarafından işaretlendi (17.2%).

## Altın etiket (14 Ekim, 16 bulgu) hangi kuralla yakalandı

| Kimlik | Kayıt | Yakalayan kurallar |
|---|---|---|
| 23938 | bathe H | r01, r08 |
| 7386 | moderate H | r08 |
| 7544 | deterministic H | — |
| 24894 | uptown H | — |
| 7597 | sickened H | r01 |
| 12432 | dummy H(sıra) | — |
| 21684 | fluff Z | r08 |
| 7144 | doom Z | r08 |
| 13201 | gagged Z(içerik) | r01, r07 |
| 18548 | sum Z | r02 |
| 19992 | team Z | — |
| 19779 | compressibility Z | r06 |
| 16987 | branded Z | — |
| 13538 | excavator Z | r01, r08 |
| 6195 | pat Z | r08 |
| 7569 | dip S(seviye) | — |

Bağımsız yakalanan (r08 altından tohumlandığı, r01 çok geniş olduğu için ikisi sayılmaz): **3/16**
