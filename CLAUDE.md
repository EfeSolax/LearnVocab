# LearnVocab — Claude için başlangıç notu

İşe başlamadan önce ürün raporunu oku: `ozetler/2026-09-27_urun-raporu.md`
- Ürünün tek doğruluk kaynağı bu rapordur. Kararlar, ekran tasarımları, veri işleri ve uygulama planı orada.
- Rapordaki "Vazgeçilen fikirler" (Bölüm 17) geri getirilmez.
- "Sonra konuşulacaklar" (Bölüm 16) Efe ile konuşulmadan uygulanmaz.
- Yeni karar alınırsa raporu güncelle ve "Değişiklik kaydı"na ekle.

Çalışma kuralları (ayrıntı: raporun Bölüm 14'ü):
- Testler her değişiklikten sonra çalıştırılır:
  `manage.py test --settings=testayar --parallel 4`
- Bağlı klasörde dosya silinmez.
- Veritabanı işleri `yazayar` kopyasında yapılır, sonra geri kopyalanır.
- API anahtarları sohbete yazılmaz.
- Hassas veya müstehcen anlamlar yazılmaz.
- Efe ile Türkçe konuşulur.
