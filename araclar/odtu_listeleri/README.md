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

**Kalınsız listeler (201/202):** hedef kelime kalın değil, maddeler kalıp ("to grow flowers (v phr)").
`uret_kalinsiz.py` kalıptaki bütün içerik kelimelerini alır (Efe'nin kararı, 10 Ekim); be/have/do/get ve
işlev kelimeleri atlanır. Etiketsiz kısa satırlar ("white", "a teacher") arkasından tek başına gelen etikete
("(adj)", "(v phr)") kadar grup sayılır. Phrasal verb'ler 18.38'e yazılır.

**101 (OLR + RHO + Speakout):** `docx_bicim.py` kalını ve altı çiziliyi ayrı çıkarır (`olr.json`, `rho.json`, `so.json`);
`uret_101.py` OLR'de altı çizili hedefleri, RHO'da türlü kalın başlıkları alır ve ikisini hafta hafta tek listede
birleştirir; Speakout'ta düz liste satırları ve kalınlar, ünite ünite. Yarım kalın ("Argentin**ian**") tam kelimeye
tamamlanır; ülke tablosundan Polish/Turkey/China başka anlamdaki kelimelere (polish, turkey, china) bağlanmaz.

**Yalnızca altı çizili listeler (502 Span 3–4):** `docx_bicim.py` ile çıkar, `uret_alti_cizili.py <json> veri/hazir_listeler <ad>`.
