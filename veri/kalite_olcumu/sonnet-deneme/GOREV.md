# Sonnet taraması: koordinatör görevi

Sen bu işin **koordinatörüsün**. Kendin hiçbir anlamı puanlamazsın; alt ajanlar yapar. Girdi/çıktı dosyalarının içeriğini okuma. Veritabanına (`db.sqlite3`) ve proje koduna dokunma. Dosya silme. Efe ile Türkçe konuş, kısa yaz.

## Adımlar
1. **Eksikleri bul** (proje kökünden):
   `python3 araclar/sonnet_tarama_kontrol.py && cat veri/kalite_olcumu/sonnet-deneme/eksik.txt`
   Liste boşsa 4. adıma geç.
2. **Grupla:** Listeyi verilen sırayla 8'erli kümelere böl (sıralama önemli: önce hiç taranmamış gruplar gelir).
3. **Dağıt:** Her küme için Agent aracıyla bir alt ajan başlat: `subagent_type: general-purpose`, `model: sonnet`, `effort: medium`, arka planda. Aynı anda **en çok 3** ajan; biri bitince sıradakini başlat. İstem aynen şu (grup listesini değiştir):
   ```
   Proje kökündeki `.claude/agents/sozluk-denetci.md` dosyasını oku; görev tanımı, kurallar, puanlama ve çıktı biçimi aynen geçerli. TEK FARK: her grubun çıktısını `veri/kalite_olcumu/sonnet-deneme/<grup>.tsv` dosyasına yaz.
   Gruplar, sırayla: bNNNN, bNNNN, ... Girdi: `veri/kalite_olcumu/haiku-tarama/girdi/<grup>.txt`.
   Önceki sonuçları (haiku-tarama/cikti/, pilot-high/, sonuc.tsv) okuma, veritabanına dokunma. Her grubun satır sayısını wc -l ile doğrula. Bitince tek satır: `b0001 OK (n işaretli), ...`.
   ```
   - Her 3 küme bitince: `git add veri/kalite_olcumu/sonnet-deneme && git commit -m "Sonnet taraması: ara sonuç"` (iş kaybolmasın).
   - **Kullanım limiti / rate limit hatası** alırsan yeni ajan başlatma, çalışanların bitmesini bekle, commit'le, "Limit doldu, N grup kaldı" de ve dur. Efe sonraki pencerede aynı istemi verince 1. adımdan devam edersin.
4. **Doğrula:** `python3 araclar/sonnet_tarama_kontrol.py`. Bozuk grup varsa 1. adıma dön (en çok 2 tur; bozuk dosyaların üzerine yeniden yazılır, silme).
5. **Bitiş:** Commit'le, kontrol aracının özetini aynen göster ve şunu yaz: "Sonnet taraması bitti. Opus oturumuna 'Sonnet taraması bitti' yaz."
