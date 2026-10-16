# Opus düzeltme turu: koordinatör görevi

Sen bu işin **koordinatörüsün**. Kayıtları kendin okumaz, kendin düzeltmezsin; Opus alt ajanları yapar. Girdi/çıktı dosyalarının içeriğini okuma (bağlamın şişer, limit boşa gider). Proje koduna dokunma. Dosya silme. Efe ile Türkçe konuş, kısa yaz.

Dosyalar `veri/kalite_olcumu/opus/` altında. Sıra: `o` (Haiku/Sonnet'in işaretlediği 2.838 anlam, 50'şer) → `y` (hiç taranmamış 8.313 anlam, 100'er) → `t` (taranmış, temiz çıkmış 15.233 anlam, 100'er).

## Adımlar
1. **Eksikleri bul** (proje kökünden):
   `python3 araclar/dogrulama_kontrol.py veri/kalite_olcumu/opus && cat veri/kalite_olcumu/opus/eksik.txt`
   Liste boşsa 5. adıma geç.
2. **Grupla:** Listeyi verilen sırayla 4'erli kümelere böl.
3. **Dağıt:** Her küme için Agent aracıyla alt ajan başlat: `subagent_type: general-purpose`, `model: opus`, arka planda. Aynı anda **en çok 4** ajan; biri bitince sıradakini başlat. İstem aynen şu (dosya listesini değiştir):
   ```
   Proje kökündeki `veri/kalite_olcumu/opus/KURALLAR.md` dosyasını oku ve kurallara aynen uy.
   Dosyalar, sırayla: o001, o002, o003, o004. Her biri için `veri/kalite_olcumu/opus/girdi/<ad>.txt` dosyasını Read ile oku, her kaydı tek tek değerlendir, sonucu `veri/kalite_olcumu/opus/cikti/<ad>.tsv` dosyasına Write ile yaz. Satır sayısının girdideki kayıt sayısından az olmadığını wc -l ile doğrula.
   Başka dosya okuma, veritabanına dokunma. Bitince tek satır: `o001 OK (n DUZELT, n BIRAK, n EFE), ...`.
   ```
   - Her 4 küme bitince: `git add veri/kalite_olcumu/opus && git commit -m "Opus turu: ara sonuç"`.
   - **Kullanım limiti / rate limit hatası** alırsan yeni ajan başlatma, çalışanları bekle, commit'le ve 4. adımı (uygulama) **o ana kadar bitenler için** yap; sonra "Limit doldu, N dosya kaldı" de ve dur. Efe aynı istemi tekrar verince 1. adımdan devam edersin.
   - Efe'nin haftalık limit sınırı yok; yine de her 10 kümede bir "N/294 dosya bitti" diye tek satır yaz.
4. **Uygula** (her `o` serisi bittiğinde, limit dolduğunda ve en sonda):
   ```
   python3 araclar/dogrulama_kontrol.py veri/kalite_olcumu/opus
   mkdir -p ~/LearnVocab-yedek && cp db.sqlite3 ~/LearnVocab-yedek/db-$(date +%Y%m%d-%H%M).sqlite3
   cp db.sqlite3 ~/db-calisma.sqlite3
   python3 araclar/opus_uygula.py --db ~/db-calisma.sqlite3
   ```
   Kuru denemede "atlanan" sayısı uygulanacakların %5'inden fazlaysa **dur** ve Efe'ye sor. Değilse:
   ```
   python3 araclar/opus_uygula.py --db ~/db-calisma.sqlite3 --uygula
   cp ~/db-calisma.sqlite3 db.sqlite3
   .venv/bin/python manage.py test --parallel 4 --noinput
   git add veri/kalite_olcumu/opus && git commit -m "Opus turu: düzeltmeler uygulandı"
   ```
   Testler başarısızsa yedeği geri koy (`cp ~/LearnVocab-yedek/<son yedek> db.sqlite3`) ve Efe'ye çıktıyı göster. Araç tekrar çalıştırılabilir: daha önce uygulananları atlar.
5. **Doğrula ve bitir:** Kontrol aracında bozuk dosya varsa 1. adıma dön (en çok 2 tur). Sonra 4. adımı son kez çalıştır ve şunları göster: kontrol aracı özeti, uygulama özeti, `veri/kalite_olcumu/opus/efe.tsv` satır sayısı. Şunu yaz: "Opus turu bitti. Ana Opus oturumuna 'Opus turu bitti' yaz."
