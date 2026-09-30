# Veri B aşaması: Efe ile birlikte bakılacak adaylar (1 Ekim 2026)

Bu dosya bir **inceleme listesidir**; hiçbir değişiklik uygulanmadı (rapor 18.7 B aşaması, 18.16).
Seviyesi Oxford'la doğrulanmamış (`cefr_kaynak = learnvocab`) kelimelerde sıklıkla seviye arasındaki tutarsızlıklar.

## 1. Çok sık ama C1–C2 etiketli (19)

Çoğu, sık bir kelimenin **nadir bir türü** (august sıfat "saygın", bay fiil, don fiil, fate fiil, railroad fiil) ya da bir özel adın şişirdiği sıklık (lee). Sıklık yazımı sayar, türü ayırmaz.
**Claude'un önerisi:** Bunlar `nadir_tur` olarak işaretlensin (L&P'ye yalnızca C1–C2'ye gelir, günün kelimesi olmaz); anlamı gerçekten ileri düzey olanlar (colonel, insane, progressive…) seviyesinde kalsın.

| Kelime | Tür | Seviye | Sıklık (Zipf) |
|---|---|---|---|
| august | sıfat | C1 | 5.10 |
| master | sıfat | C1 | 4.93 |
| learned | sıfat | C1 | 4.85 |
| lee | isim | C1 | 4.73 |
| bay | sıfat | C1 | 4.73 |
| bay | fiil | C1 | 4.73 |
| affected | sıfat | C1 | 4.64 |
| don | fiil | C1 | 4.60 |
| absolute | isim | C1 | 4.54 |
| offensive | isim | C1 | 4.46 |
| rank | sıfat | C2 | 4.44 |
| colonel | isim | C1 | 4.41 |
| insane | sıfat | C1 | 4.40 |
| fate | fiil | C1 | 4.36 |
| cant | isim | C2 | 4.35 |
| cant | fiil | C1 | 4.35 |
| progressive | isim | C1 | 4.34 |
| fleet | sıfat | C2 | 4.33 |
| railroad | fiil | C1 | 4.32 |

## 2. Çok seyrek ama A1–A2 etiketli (27)

Çoğu bileşik isim (coffeeshop, bedsheet, doorknob, trashcan…): kolay ama sıklığı düşük; bir kısmı Amerikan kullanımı ya da iki kelimelik yazımın bitişik hâli (coffee shop, bed sheet). "gramme" (gram'ın eski İngiliz yazımı) gereksiz.
**Claude'un önerisi:** Seviyeleri kalsın (anlamı kolay), bitişik yazımı yaygın olmayanlar (coffeeshop, bedsheet, birthdate, trashcan) iki kelimelik yazıma çevrilsin ya da silinsin; "gramme" silinsin.

| Kelime | Tür | Seviye | Sıklık (Zipf) |
|---|---|---|---|
| gramme | isim | A1 | 1.64 |
| coffeeshop | isim | A1 | 2.07 |
| bedsheet | isim | A2 | 2.08 |
| houseplant | isim | A2 | 2.08 |
| birdhouse | isim | A2 | 2.32 |
| shoelace | isim | A2 | 2.35 |
| bicyclist | isim | A2 | 2.38 |
| birthdate | isim | A2 | 2.43 |
| trashcan | isim | A2 | 2.46 |
| untie | fiil | A2 | 2.51 |
| ballpoint | isim | A2 | 2.53 |
| policewoman | isim | A2 | 2.54 |
| unwrap | fiil | A2 | 2.56 |
| shoestring | isim | A2 | 2.65 |
| doorknob | isim | A2 | 2.65 |
| nightstand | isim | A2 | 2.72 |
| lunchbox | isim | A2 | 2.72 |
| snore | fiil | A2 | 2.76 |
| keychain | isim | A2 | 2.76 |
| hazelnut | isim | A2 | 2.78 |
| pajama | isim | A1 | 2.81 |
| undress | fiil | A2 | 2.87 |
| sleeveless | sıfat | A2 | 2.89 |
| clipboard | isim | A2 | 2.89 |
| centimeter | isim | A2 | 2.89 |
| bookshelf | isim | A1 | 2.92 |
| eraser | isim | A2 | 2.94 |

## 3. Anlam sırası

Bazı kelimelerde ilk (kartta en üstte görünen) anlam en yaygın anlam değil. Örnekte görüldü: **interpret** (önce "çevirmenlik yapmak", olması gereken "yorumlamak"), **occur** (önce "aklına gelmek", olması gereken "meydana gelmek"). Bunlar otomatik bulunamıyor; kelimeler gözden geçirilirken düzeltilir.
