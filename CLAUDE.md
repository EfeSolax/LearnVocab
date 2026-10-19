# LearnVocab — Claude için başlangıç notu

İşe başlamadan önce ürün durumunu oku: `ozetler/2026-09-27_urun-raporu.md` (kısa, ~170 satır)
Yayın durumu ve açık işler için ayrıca: `ozetler/2026-10-20_devir-notu.md` (site yayında, 20 Ekim).
- Ürünün tek doğruluk kaynağı bu dosyadır: güncel kararlar, ekranlar, veri durumu, açık işler.
- Tarihçe ve gerekçeler `ozetler/arsiv/2026-09-27_urun-raporu-tam.md` dosyasında. Koddaki "rapor 18.8" gibi atıflar arşivdeki numaralara bakar.
- "Vazgeçilen fikirler" (Bölüm 16) geri getirilmez.
- "Açık işler ve karar bekleyenler" (Bölüm 15) Efe ile konuşulmadan uygulanmaz.
- Yeni karar alınırsa durum dosyasını güncelle (eskiyi sil, yenisini yaz) ve arşivin sonundaki "Değişiklik kaydı"na tarihli satır ekle.
- Veri kalitesi ölçümü: `veri/kalite_olcumu/`.

Çalışma kuralları (ayrıntı: durum dosyasının Bölüm 18'i):
- Testler her değişiklikten sonra çalıştırılır:
  `manage.py test --settings=testayar --parallel 4`
- Bağlı klasörde dosya silinmez.
- Veritabanı işleri `yazayar` kopyasında yapılır, sonra geri kopyalanır.
- API anahtarları sohbete yazılmaz.
- Hassas veya müstehcen anlamlar yazılmaz.
- Efe ile Türkçe konuşulur.
