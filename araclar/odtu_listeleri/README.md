# ODTÜ DBE kelime listeleri → hazır listeler (rapor 13.3, D7)

Hocaların belgelerinde hedef kelime **kalın** yazılıyor (bazılarında kalın + altı çizili).
Kelimeler yalnızca bu kalınlardan alınır; kalıplar, tanımlar ve örnek cümleler alınmaz.

1. Kalınları çıkar (her span için bir JSON):
   ```
   .venv/bin/python -I araclar/odtu_listeleri/docx_kalin.py "<span>.docx" <klasör>/kalin1.json
   .venv/bin/python -I araclar/odtu_listeleri/pdf_kalin.py  "<span>.pdf"  <klasör>/kalin1.json
   ```
2. Liste dosyalarını üret (proje kökünde; `uret.py`'nin sonundaki span/ad/ilk bölüm satırları kura göre düzenlenir):
   ```
   python3 araclar/odtu_listeleri/uret.py <klasör> veri/hazir_listeler
   ```
   Bölümler: `WEEK n` → hafta, `RHO n`, `Handout n`, `Unit n`, `More to Read II`.
   Sözlük biçimli bölümlerde (`kelime (n): tanım`) yalnızca türü ya da tanımı yazan kalınlar alınır, eş dizim satırları atlanır.
   Kalın bir kalıpta altı çizili kelime ya da kalıbın B1 ve üstü kelimeleri alınır.
   Sözlükte olmayanlar `odtu-<kur>-sozlukte-yok.txt`'ye yazılır (18.38).
3. Önce `hazir_liste_yukle … --dry-run`, sonra yükle (`--yenile` var olanın üyelerini baştan yazar).
4. Çıktı belgeyle karşılaştırılır (ilk haftalar ekran görüntüsüyle); hoca bazı yerlerde kalın yazmayı unutabiliyor.
