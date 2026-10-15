# Doğrulama: koordinatör görevi

Sen bu işin **koordinatörüsün**. Kendin karar vermezsin; alt ajanlar yapar. Girdi/çıktı dosyalarının içeriğini okuma. Veritabanına (`db.sqlite3`) ve proje koduna dokunma. Dosya silme. Efe ile Türkçe konuş, kısa yaz.

## Adımlar
1. **Eksikleri bul** (proje kökünden):
   `python3 araclar/dogrulama_kontrol.py && cat veri/kalite_olcumu/dogrulama/eksik.txt`
   Liste boşsa 4. adıma geç.
2. **Grupla:** Listeyi sırayla 4'erli kümelere böl (her dosya 50 kayıt).
3. **Dağıt:** Her küme için Agent aracıyla alt ajan başlat: `subagent_type: general-purpose`, `model: sonnet`, `effort: medium`, arka planda. Aynı anda **en çok 3** ajan; biri bitince sıradakini başlat. İstem aynen şu (dosya listesini değiştir):
   ```
   Proje kökündeki `veri/kalite_olcumu/dogrulama/KURALLAR.md` dosyasını oku ve kurallara aynen uy.
   Dosyalar, sırayla: d001, d002, d003, d004. Her biri için `veri/kalite_olcumu/dogrulama/girdi/<ad>.txt` dosyasını Read ile oku, her kaydı değerlendir, sonucu `veri/kalite_olcumu/dogrulama/cikti/<ad>.tsv` dosyasına Write ile yaz.
   Başka dosya okuma, veritabanına dokunma. Bitince tek satır: `d001 OK (n DUZELT, n BIRAK, n EFE), ...`.
   ```
   - Her 3 küme bitince: `git add veri/kalite_olcumu/dogrulama && git commit -m "Doğrulama: ara sonuç"`.
   - **Kullanım limiti / rate limit hatası** alırsan yeni ajan başlatma, çalışanları bekle, commit'le, "Limit doldu, N dosya kaldı" de ve dur. Efe aynı istemi tekrar verince 1. adımdan devam edersin.
4. **Doğrula:** `python3 araclar/dogrulama_kontrol.py`. Bozuk dosya varsa 1. adıma dön (en çok 2 tur; bozuk dosyaların üzerine yeniden yazılır).
5. **Bitiş:** Commit'le, kontrol aracının özetini aynen göster ve şunu yaz: "Doğrulama bitti. Opus oturumuna 'Doğrulama bitti' yaz."
