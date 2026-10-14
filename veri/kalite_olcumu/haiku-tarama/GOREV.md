# Haiku taraması: koordinatör görevi

Sen bu işin **koordinatörüsün**. Kendin hiçbir anlamı puanlamazsın; bunu `sozluk-denetci` alt ajanları yapar. Sen yalnızca işi dağıtır, ilerlemeyi izler ve sonunda özetlersin. **Girdi ya da çıktı dosyalarının içeriğini kendin okuma** (bağlamını şişirir). Veritabanına (`db.sqlite3`) ve proje kodlarına dokunma.

Çalışma klasörü: proje kökü. Dosyalar `veri/kalite_olcumu/haiku-tarama/` altında:
- `girdi/bNNNN.txt` — 181 dosya, her biri 100 anlam kaydı
- `cikti/bNNNN.tsv` — alt ajanların yazdığı sonuçlar (başta boş)

## Adımlar
1. **Eksik grupları bul** (Bash):
   ```
   cd veri/kalite_olcumu/haiku-tarama && comm -23 <(ls girdi | sed 's/\.txt$//') <(ls cikti | sed 's/\.tsv$//')
   ```
   Çıktı boşsa 4. adıma geç.
2. **Grupla:** Eksikleri 5'erli kümelere ayır (b0001–b0005 gibi sıralı; son küme daha kısa olabilir).
3. **Dağıt:** Her küme için `sozluk-denetci` alt ajanını **arka planda** başlat; istemi yalnızca şudur: `Şu grupları işle: b0001, b0002, b0003, b0004, b0005`. Aynı anda **en çok 4** alt ajan çalıştır; biri bitince sıradaki kümeyi başlat. Her alt ajanın tek satırlık özetini topla (OK / BOZUK). Bütün kümeler bitene kadar devam et.
   - Kullanım limiti / rate limit hatası alırsan **dur**, hangi kümelerin bittiğini söyle ve çık. Kullanıcı aynı istemi tekrar verince işe kaldığın yerden devam edersin (1. adım eksikleri bulur).
4. **Doğrula:** `python3 araclar/haiku_tarama_kontrol.py` çalıştır. Bozuk ya da eksik grup varsa `python3 araclar/haiku_tarama_kontrol.py --bozuk-sil` çalıştır ve **1. adıma dön** (en çok 2 tur; sonra kalanları raporla).
5. **Bitiş:** Kontrol aracının yazdırdığı özeti olduğu gibi göster, ek yorum ekleme. Şunu söyle: "Tarama bitti. Sonuçlar `veri/kalite_olcumu/haiku-tarama/isaretlenen.tsv` içinde. Claude'a (Sonnet/Opus) bunu gözden geçirmesini söyle."

## Kurallar
- Alt ajanlara başka görev verme; onların istemini değiştirme.
- Bir alt ajan "BOZUK" derse hemen yeniden deneme; 4. adımdaki tur mantığına bırak.
- Dosyaları silme (yalnızca `--bozuk-sil`'in sildiklerini).
