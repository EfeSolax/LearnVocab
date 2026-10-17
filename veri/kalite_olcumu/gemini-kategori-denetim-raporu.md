# 34 Kategori Kapsamlı Kalite ve Uyum Denetimi Raporu

Bu rapor, veritabanındaki 34 konu kategorisine (`words_category` / `words_meaning_categories`) bağlı toplam **7.049 kelime-anlam bağının** tek tek taranması sonucunda tespit edilen hatalı anlam eşleşmelerini, veritabanı tanımı kategoriyle uyuşmayan kelimeleri, kategori kapsamını aşan (zorlama/yan) kelimeleri ve konu kartlarında (`words/konular.py` + `words/kart.py`) yanıltıcı görünen ikincil anlamları içerir.

## 1. Özet İstatistikler ve Kök Nedenler

- **Yanlış Anlam Bağı (`YANLIS_ANLAM_BAGI` — 33 kayıt):** Kelimenin doğru anlamı veritabanında mevcut olduğu hâlde kategoriye yanlış `meaning_id` (farklı anlam veya farklı sözcük türü) bağlanmış (örn. `doga` kategorisinde `delta` için nehir deltası yerine Yunan harfi `Δ`; `hayvanlar` kategorisinde `colony` için canlı kolonisi yerine siyasi sömürge; `giyim-moda` kategorisinde `top` için bluz/üst giysi yerine 'en yüksek tepe kısım').
- **Veritabanı Tanımı Kategoriyle Uyumsuz (`TANIM_UYUMSUZ_CIKAR` — 69 kayıt):** Kelime çok anlamlı olduğu için kategoriye eklenmiş ancak veritabanında kelimenin o kategoriye ait anlamı **bulunmuyor**; yalnızca başka bir anlamı kayıtlı (örn. `yiyecek-icecek` içinde `kiwi` -> yalnızca *'Yeni Zelanda'ya özgü uçamayan kivi kuşu'*, `cream` -> yalnızca *'cilde sürülen nemlendirici krem'*; `teknoloji` içinde `cloud` -> *'gökyüzündeki su buharı bulutu'*, `menu` -> *'restoran yemek listesi'*, `window` -> *'bina penceresi'*; `saglik` içinde `needle` -> *'dikiş iğnesi'*, `broken` -> *'bozuk eşya'*; `iletisim-medya` içinde `advert` -> C2 seviyesinde *'bir konuya değinmek (advert to)'* fiili).
- **Kategoriye Ait Olmayan / Zorlama Kelimeler (`KATEGORIYE_AIT_DEGIL_CIKAR` — 292 kayıt):** Anlamı doğru olsa bile o kategorinin çekirdek kapsamına girmeyen, başka bir kategoriye ait olan veya fazla genel kalan kelimeler (örn. `ev-esyalar (Home and furniture)` içindeki `mortgage`, `lease`, `evict`, `wire`, `pipe`, `plumbing`, `brick`, `hammer`, `screwdriver`, `tissue`, `toothpaste`; `hayvanlar (Animals)` içindeki `school`, `pride`, `pen`, `collar`, `muzzle`, `barn`, `stable`, `zoo`, `vet`, `poacher`; `sehir-yerler` içindeki `behind`, `between`, `left`, `right`, `barber`, `butcher`, `mayor`).
- **İkincil Anlam Kaynaklı Kart/Seviye Yanıltması (`IKINCIL_ANLAM_KARTTA_YANILTICI` — 458 kayıt):** Kelime kategoriye 2. veya 3. anlamıyla (`sort_order > 0`) girdiği hâlde `words/kart.py` içindeki `Kart.ozet` her zaman `self.anlamlar[0].meaning_tr` (1. anlamı) gösterdiği ve `words/konular.py` içindeki `konu_kelime_idleri()` filtrelemede `Meaning.cefr` yerine `Word.cefr` kullandığı için kartta alakasız 1. anlamın ve yanlış seviyenin görünmesi (örn. `Animals -> A1` altında `school · okul, eğitim kurumu (A1)` veya `Home and furniture -> B2` altında `landing · iniş (uçak)`).

## 2. Mimari Kök Neden: Konu Sayfası Kart Özeti ve CEFR Filtresi

Ekran görüntülerindeki `school · okul, eğitim kurumu (A1)` ve `landing · iniş (uçak)` durumunun teknik sebebi iki noktadan kaynaklanmaktadır:

1. **`words/konular.py` (`konu_kelime_idleri`):** `Word.objects.filter(ortak, meanings__categories=kategori).values_list('id', 'cefr', 'siklik')` sorgusu kelimenin o kategorideki anlamının seviyesini (`meanings__cefr`) değil, kelimenin genel seviyesini (`Word.cefr`, yani en kolay anlamının seviyesini) çekmektedir. Bu yüzden `school` kelimesinin `'balık sürüsü'` anlamı `B2` olduğu hâlde kelime `Animals` sayfasında `A1` sekmesinde listelenmektedir.
2. **`words/kart.py` (`Kart.ozet`):** Kart başlığındaki mavi Türkçe özet her zaman `self.anlamlar[0].meaning_tr` (kelimenin 1. anlamı) olarak basılmaktadır. Kategori sayfasında (`sozluk_konu`) karta o kategoriye ait anlam önceliklendirilmediği için `school` kartında `'balık sürüsü'` yerine `'okul, eğitim kurumu'`, `landing` kartında `'sahanlık'` yerine `'iniş (uçak)'` yazmaktadır.

## 3. Yanlış Anlam Bağları (`YANLIS_ANLAM_BAGI` — Doğru Anlamı Veritabanında Mevcut Olanlar)

| Kategori | Kelime | Mevcut Hatalı Anlam (`meaning_id`) | Bağlanması Gereken Doğru Anlam | Açıklama |
|---|---|---|---|---|
| `gorunus-beden` (Görünüş ve beden) | **organ** (noun) | `18599`: organ, kurul, merci | `18598 (organ:noun = vücut organı, iç organ)` | Görünüş ve beden kategorisinde 'organ, kurul, merci' (18599) yerine anatomik 'vücut organı, iç organ' (18598) anlamı bağlanmalı |
| `yiyecek-icecek` (Yiyecek ve içecek) | **fiber** (noun) | `13426`: lif, elyaf | `13427 (fiber:noun = gıda lifi, diyet lifi)` | Yiyecek ve içecek kategorisinde tekstil/yapı 'lif, elyaf' (13426) yerine beslenme terimi olan 'gıda lifi, diyet lifi' (13427) anlamı bağlanmalı |
| `giyim-moda` (Giyim ve moda) | **top** (noun) | `20446`: tepe, üst | `20447 (top:noun = üst (giysi), bluz)` | Giyim kategorisinde 'tepe, üst (en yüksek kısım)' (20446) yerine kıyafet olan 'üst (giysi), bluz' (20447) anlamı bağlanmalı |
| `okul-egitim` (Okul ve eğitim) | **degree** (noun) | `16595`: seviye, derece, ölçü | `16594 (degree:noun = üniversite derecesi, diploma)` | Okul ve eğitim kategorisinde 'seviye, derece, ölçü' (16595) fazladan bağlanmış; zaten bağlı olan 'üniversite derecesi, diploma' (16594) kalmalı, 16595 çıkarılmalı |
| `spor` (Spor) | **warm up** (phrasal_verb) | `26807`: ısınmak, ısıtmak | `26808 (warm up:phrasal_verb = (spordan önce) ısınma hareketi yapmak)` | Spor kategorisinde hava/nesne için 'ısınmak, ısıtmak' (26807) yerine '(spordan önce) ısınma hareketi yapmak' (26808) anlamı bağlanmalı |
| `bos-zaman` (Boş zaman ve hobiler) | **reception** (noun) | `12679`: resepsiyon | `12680 (reception:noun = karşılama, karşılama töreni)` | Boş zaman/etkinlik kategorisinde otel girişi olan 'resepsiyon' (12679) yerine 'karşılama, davet, resepsiyon' (12680) anlamı bağlanmalı |
| `doga` (Doğa) | **delta** (noun) | `8082`: delta | `8081 (delta:noun = nehir deltası)` | Doğa kategorisinde Yunan alfabesi harfi olan 'delta (Δ)' (8082) yerine coğrafi 'nehir deltası' (8081) anlamı bağlanmalı |
| `doga` (Doğa) | **fire** (noun) | `7992`: yangın | `7993 (fire:noun = ateş)` | Doğa kategorisinde mülk/bina yıkımı olan 'yangın' (7992) yerine doğal element/yanma olayı olan 'ateş' (7993) anlamı bağlanmalı |
| `hayvanlar` (Hayvanlar) | **colony** (noun) | `11880`: sömürge, koloni | `11881 (colony:noun = koloni)` | Hayvanlar kategorisinde siyasi 'sömürge, koloni' (11880) yerine biyolojik 'koloni (birlikte yaşayan canlı topluluğu)' (11881) anlamı bağlanmalı |
| `zaman` (Zaman) | **age** (noun) | `15554`: yaş | `15555 (age:noun = dönem, çağ)` | Zaman kategorisinde hem 'insan yaşı' (15554) hem 'dönem, çağ' (15555) bağlı; 'yaş' (15554) kişisel bilgi olduğu için çıkarılıp yalnız 'dönem, çağ' (15555) bırakılmalı |
| `teknoloji` (Teknoloji ve internet) | **icon** (noun) | `12258`: simge, ikon | `12259 (icon:noun = ikon, bilgisayar simgesi)` | Teknoloji kategorisinde kültürel 'simge, ikon kişi' (12258) yerine 'ikon, bilgisayar ekran simgesi' (12259) anlamı bağlanmalı |
| `teknoloji` (Teknoloji ve internet) | **profile** (noun) | `17015`: profil, yan görünüm, dış hat | `17016 (profile:noun = özgeçmiş, profil)` | Teknoloji/internet kategorisinde 'yüzün yandan görünümü, dış hat' (17015) yerine kullanıcı profili/özgeçmiş olan 'profil' (17016) anlamı bağlanmalı |
| `bilim-arastirma` (Bilim ve araştırma) | **model** (noun) | `16060`: örnek, örnek kişi, timsal | `16059 (model:noun = maket, minyatür)` | Bilim kategorisinde 'örnek kişi, timsal (role model)' (16060) yerine 'maket, minyatür, model' (16059) anlamı bağlanmalı |
| `bilim-arastirma` (Bilim ve araştırma) | **organ** (noun) | `18599`: organ, kurul, merci | `18598 (organ:noun = vücut organı, iç organ)` | Bilim kategorisinde 'organ, kurul, merci' (18599) yerine biyolojik 'vücut organı, iç organ' (18598) anlamı bağlanmalı |
| `ekonomi-is-dunyasi` (Ekonomi ve iş dünyası) | **commission** (noun) | `16663`: komisyon, kurul | `16664 (commission:noun = görev, yetki, sorumluluk)` | Ekonomi kategorisinde 'komisyon, kurul (heyet)' (16663) yerine ticari 'komisyon, aracılık ücreti' (16664) anlamı bağlanmalı |
| `hukuk-suc` (Hukuk ve suç) | **compliance** (noun) | `14652`: uyum, uygunluk | `14651 (compliance:noun = uyma, itaat, riayet)` | Hukuk kategorisinde genel 'uyum, uygunluk' (14652) yerine kurallara/yasalara 'uyma, itaat, riayet' (14651) anlamı bağlanmalı |
| `hukuk-suc` (Hukuk ve suç) | **illegitimate** (adjective) | `14627`: evlilik dışı doğmuş, gayrimeşru | `14626 (illegitimate:adjective = hukuka aykırı, yasa dışı)` | Hukuk ve suç kategorisinde 'evlilik dışı doğmuş' (14627) yerine 'hukuka aykırı, yasa dışı' (14626) anlamı bağlanmalı |
| `siyaset-toplum` (Siyaset ve toplum) | **lobby** (noun) | `12285`: giriş holü, lobi | `12286 (lobby:noun = lobi, baskı grubu)` | Siyaset kategorisinde bina girişi olan 'giriş holü, lobi' (12285) yerine siyasi 'lobi, baskı grubu' (12286) anlamı bağlanmalı |
| `siyaset-toplum` (Siyaset ve toplum) | **norm** (noun) | `7943`: ortalama, istatistiksel norm | `7942 (norm:noun = kural, standart)` | Siyaset ve toplum kategorisinde 'istatistiksel ortalama' (7943) yerine toplumsal 'kural, standart, norm' (7942) anlamı bağlanmalı |
| `siyaset-toplum` (Siyaset ve toplum) | **summit** (noun) | `6677`: zirve, dağ zirvesi | `6678 (summit:noun = zirve toplantısı, yüksek düzey görüşme)` | Siyaset kategorisinde 'dağ zirvesi' (6677) yerine diplomatik 'zirve toplantısı, yüksek düzey görüşme' (6678) anlamı bağlanmalı |
| `tarih` (Tarih) | **enlightenment** (noun) | `18532`: bilgi, kavrayış, aydınlanma | `18533 (enlightenment:noun = Aydınlanma Çağı, Aydınlanma Dönemi)` | Tarih kategorisinde genel 'bilgi, kavrayış' (18532) yerine tarihsel dönem olan 'Aydınlanma Çağı, Aydınlanma Dönemi' (18533) anlamı bağlanmalı |
| `tarih` (Tarih) | **lord** (noun) | `16151`: efendi, lord, saygıdeğer kişi | `16150 (lord:noun = soylu, asil, derebeyi)` | Tarih kategorisinde hitap olan 'efendi, saygıdeğer kişi' (16151) yerine feodal unvan olan 'soylu, asil, derebeyi' (16150) anlamı bağlanmalı |
| `neden-sonuc-degisim` (Neden, sonuç ve değişim) | **boom** (noun) | `6387`: gürültülü patlama sesi | `6386 (boom:noun = ekonomik büyüme, hızlı artış)` | Neden-sonuç ve değişim kategorisinde 'gürültülü patlama sesi' (6387) yerine 'hızlı artış, büyüme' (6386) anlamı bağlanmalı |
| `neden-sonuc-degisim` (Neden, sonuç ve değişim) | **dictate** (verb) | `11449`: yazdırmak, dikte etmek | `11448 (dictate:verb = dikte etmek, emretmek, belirlemek, öngörmek)` | Neden-sonuç kategorisinde 'birine metin yazdırmak, dikte etmek' (11449) yerine 'belirlemek, zorunlu kılmak, öngörmek' (11448) anlamı bağlanmalı |
| `neden-sonuc-degisim` (Neden, sonuç ve değişim) | **drop** (verb) | `11216`: bırakmak, düşürmek | `11217 (drop:verb = azalmak, düşmek)` | Değişim kategorisinde fiziksel 'elinden bırakmak, düşürmek' (11216) yerine miktar/seviye olarak 'azalmak, düşmek' (11217) anlamı bağlanmalı |
| `neden-sonuc-degisim` (Neden, sonuç ve değişim) | **jump** (noun) | `17544`: atlama, sıçrama | `17545 (jump:noun = ani artış, yükseliş)` | Değişim kategorisinde fiziksel 'atlama, sıçrama' (17544) yerine 'ani artış, yükseliş' (17545) anlamı bağlanmalı |
| `neden-sonuc-degisim` (Neden, sonuç ve değişim) | **shape** (verb) | `17447`: şekillendirmek, biçim vermek | `17448 (shape:verb = etkilemek, belirlemek)` | Neden-sonuç ve değişim kategorisinde fiziksel 'biçim vermek' (17447) yerine 'etkilemek, belirlemek, yön vermek' (17448) anlamı bağlanmalı |
| `neden-sonuc-degisim` (Neden, sonuç ve değişim) | **so** (adverb) | `20846`: çok, o kadar | `20848 (then:adverb = o zaman, o sırada)` | Neden-sonuç kategorisinde zarf olan 'çok, o kadar' (20846) yerine bağlaç olan 'bu yüzden, dolayısıyla' (20848) anlamı bağlanmalı |
| `tartisma` (Tartışma ve fikir bildirme) | **argue** (verb) | `425`: tartışmak, münakaşa etmek | `426 (argue:verb = iddia etmek, savunmak)` | Tartışma ve fikir bildirme (akademik) kategorisinde 'öfkeyle kavga/münakaşa etmek' (425) yerine 'iddia etmek, gerekçelerle savunmak' (426) anlamı bağlanmalı |
| `tartisma` (Tartışma ve fikir bildirme) | **argument** (noun) | `428`: tartışma, anlaşmazlık | `429 (argument:noun = savunma, gerekçe, iddia)` | Tartışma ve fikir bildirme kategorisinde 'kavga, sözlü münakaşa' (428) yerine 'savunma, gerekçe, argüman, iddia' (429) anlamı bağlanmalı |
| `tartisma` (Tartışma ve fikir bildirme) | **highlight** (noun) | `13068`: en önemli kısım, doruk noktası | `13069 (highlight:verb = vurgulamak, öne çıkarmak)` | Tartışma kategorisinde isim olan 'en önemli kısım' (13068) yerine fiil olan 'vurgulamak, öne çıkarmak (highlight:v)' (13069) anlamı bağlanmalı |
| `tartisma` (Tartışma ve fikir bildirme) | **thesis** (noun) | `13811`: tez, yüksek lisans/doktora çalışması | `13812 (thesis:noun = sav, öneri, temel düşünce)` | Tartışma ve fikir bildirme kategorisinde 'yüksek lisans/doktora tezi' (13811 - okul-egitim'e ait) yerine 'sav, öneri, temel düşünce' (13812) anlamı bağlanmalı |
| `tartisma` (Tartışma ve fikir bildirme) | **underline** (verb) | `25895`: altını çizmek, bir çizgiyle işaretlemek | `25896 (underline:verb = vurgulamak, dikkat çekmek)` | Tartışma kategorisinde fiziksel 'altını çizgiyle işaretlemek' (25895) yerine 'vurgulamak, dikkat çekmek' (25896) anlamı bağlanmalı |

## 4. Veritabanı Tanımı Kategoriyle Uyumsuz Olanlar (`TANIM_UYUMSUZ_CIKAR`)

Bu kelimeler çok anlamlılık nedeniyle kategoriye eklenmiş ancak veritabanında kelimenin o kategoriye uygun anlamı **yoktur**; mevcut tanım tamamen farklı bir anlama aittir:

| Kategori | Kelime | `meaning_id` | Veritabanındaki Mevcut Anlam (`meaning_tr`) | İngilizce Tanım (`definition`) | Neden Uyumsuz? |
|---|---|---|---|---|---|
| `duygular` | **upset** (verb, B2) | `17863` | altüst etmek, bozmak | to disturb the normal order or arrangement of something; to cause disorder | Veritabanındaki tanımı bir düzeni/planı 'altüst etmek, bozmak'tır; duygusal olarak 'üzmek' anlamı değildir |
| `kisilik-davranis` | **character** (noun, B1) | `1792` | karakter, kahraman | a person in a story, play, film, or other narrative work | Veritabanındaki tanımı roman/filmdeki 'kurgusal karakter, kahraman'dır; insan kişiliği/huyu anlamı veritabanında yoktur |
| `gorunus-beden` | **palate** (noun, B2) | `24538` | damak zevki, damak tadı, damak | the sense of taste; the ability to distinguish flavors | Veritabanındaki tanımı mecazi 'damak zevki, tat ayırt etme yetisi'dir; anatomik ağız tavanı (damak) olarak tanımlanmamıştır |
| `gorunus-beden` | **short** (adjective, A2) | `3701` | kısa | having a small length or distance | Veritabanındaki tanımı nesne ve mesafeler için 'kısa (uzunluğu az olan)'dır; insan boyu için 'kısa boylu' anlamı ayrılmamıştır |
| `gorunus-beden` | **straight** (adjective, A2) | `6621` | düz, bükülmemiş | extending in the same direction without curving or bending; not crooked or angled | Veritabanındaki tanımı çizgi/yol için 'düz, bükülmemiş'tir; düz saç anlamı değildir |
| `aile-iliskiler` | **born** (adjective, B1) | `20108` | doğuştan | existing from birth; inherent or innate. | Veritabanındaki tanımı 'doğuştan (a born leader - innate)' sıfatıdır; doğum/aile anlamı değildir |
| `aile-iliskiler` | **separate** (verb, B2) | `11275` | ayrılmak | to move away from a group, place, or person; to withdraw | Veritabanındaki tanımı fiziksel olarak 'bir gruptan/yerden uzaklaşmak'tır; eşlerin ayrılması anlamı değildir |
| `yiyecek-icecek` | **consume** (verb, B1) | `5075` | kullanmak, tüketmek | to use up a resource or amount of something completely | Veritabanındaki tanımı enerji/kaynak 'tüketmek, harcamak'tır; yiyecek/içecek yemek-içmek anlamı değildir |
| `yiyecek-icecek` | **cream** (noun, B1) | `17842` | krem | a thick, smooth preparation applied to the skin for moisturizing or medicinal purposes | Veritabanındaki tanımı cilde sürülen kozmetik 'nemlendirici cilt kremi'dir; süt kreması/kaymak anlamı veritabanında yoktur! |
| `yiyecek-icecek` | **healthy** (adjective, A1) | `15403` | sağlıklı | in a good physical condition; free from illness or injury | Veritabanındaki tanımı insan/canlı için 'hasta olmayan, sağlığı yerinde'dir; besleyici/sağlığa yararlı gıda anlamı değildir |
| `yiyecek-icecek` | **kiwi** (noun, B1) | `24372` | kivi kuşu | a small, flightless bird native to New Zealand, known for its long beak and nocturnal habits | Veritabanındaki tanımı Yeni Zelanda'ya özgü uçamayan 'kivi kuşu'dur; kivi meyvesi anlamı veritabanında yoktur! |
| `yiyecek-icecek` | **mineral** (noun, B2) | `7884` | mineral | a naturally occurring inorganic solid substance with a defined chemical composition and crystalline structure | Veritabanındaki tanımı jeolojik 'kayaç/maden minerali'dir; besin minerali olarak tanımlanmamıştır |
| `yemek-yapma` | **mix up** (phrasal_verb, Belirtilmemiş) | `26575` | karıştırmak, birbirine karıştırmak | to think that one person or thing is another | Veritabanındaki tanımı 'iki kişi veya şeyi birbiriyle karıştırmak (zihninde ayırt edememek)'tir; malzemeleri karıştırmak anlamı değildir |
| `yemek-yapma` | **tender** (adjective, B1) | `15027` | nazik, yumuşak | showing gentleness, kindness, or careful consideration | Veritabanındaki tanımı insan davranışı için 'nazik, şefkatli (kind and gentle)'dir; pişmiş etin yumuşak/gevrek olması anlamı veritabanında yoktur |
| `saglik` | **broken** (adjective, A1) | `11712` | kırık, bozuk | damaged and no longer in its original or functional shape | Veritabanındaki tanımı eşya/makine için 'kırık, bozuk, çalışmayan'dır; kırık kemik (broken bone) anlamı değildir |
| `saglik` | **needle** (noun, A2) | `4015` | iğne | a thin, pointed metal tool used for sewing or stitching fabric | Veritabanındaki tanımı dikiş dikmekte kullanılan 'dikiş iğnesi (sewing needle)'dir; tıbbi enjektör/şırınga iğnesi değildir |
| `saglik` | **syrup** (noun, B1) | `22463` | şurup | a thick, sweet liquid made by dissolving sugar in water or juice, often flavored, used as a topping or ingredient | Veritabanındaki tanımı şekerli suyla yapılan tatlı 'meyve/tatlı şurubu'dur; tıbbi öksürük şurubu değildir |
| `okul-egitim` | **globe** (noun, B2) | `3065` | küre, yuvarlak nesne | a spherical object or shape, often used to describe a ball-like form | Veritabanındaki tanımı genel 'küre, yuvarlak nesne'dir; coğrafya dersindeki yer küre (world globe) değildir |
| `sanat-eglence` | **curtain** (noun, Belirtilmemiş) | `20464` | perde | a piece of cloth that hangs in front of a window | Veritabanındaki tanımı 'pencere perdesi (window curtain)'dir; tiyatro/sahne perdesi anlamı değildir |
| `sanat-eglence` | **horror** (noun, B2) | `940` | korku, dehşet | a strong feeling of fear, shock, or disgust | Veritabanındaki tanımı genel 'korku, dehşet duygusu'dur (duygular kategorisinde zaten var); korku filmi/edebiyatı türü olarak tanımlanmamıştır |
| `sanat-eglence` | **juggle** (verb, B2) | `14497` | birden çok işi idare etmek, hokkabazlık yapmak | to manage several tasks or responsibilities at the same time | Veritabanındaki tanımı mecazi 'aynı anda birden çok işi idare etmek'tir; sirkte toplarla jonglörlük yapmak anlamı değildir |
| `sanat-eglence` | **mystery** (noun, B2) | `1126` | gizem, bilinmezlik | something that is difficult or impossible to understand or explain | Veritabanındaki tanımı genel 'gizem, bilinmezlik'tir; polisiye/gizem türü olarak tanımlanmamıştır |
| `sanat-eglence` | **romance** (noun, B1) | `7489` | aşk ilişkisi, romantik ilişki | a close, affectionate relationship between two people that involves love and emotional intimacy | Veritabanındaki tanımı 'romantik ilişki, aşk ilişkisi'dir (aile-iliskiler'de zaten var); romantik film/roman türü değildir |
| `spor` | **captain** (noun, A2) | `16711` | kaptan | the person in command of a ship or vessel | Veritabanındaki tanımı 'gemi kaptanı (person in command of a ship)'dır; spor takımı kaptanı anlamı veritabanında yoktur |
| `spor` | **favorite** (noun, B2) | `6181` | gözde, favori, kayırılan kişi | a person who receives special attention or treatment from someone | Veritabanındaki tanımı 'otorite tarafından kayırılan gözde kişi (teacher's pet)'dir; yarışmada kazanması beklenen favori (tournament favorite) anlamı değildir |
| `spor` | **professional** (adjective, B2) | `4760` | mesleki, işine ait | relating to a recognized occupation or to the standards of a particular profession | Veritabanındaki tanımı 'bir mesleğe/işe ait (mesleki)'dir; amatör karşıtı 'profesyonel sporcu' anlamı değildir |
| `spor` | **stretching** (noun, B1) | `1519` | germe, esneme | the act or process of extending or lengthening something, especially a part of the body, to increase flexibility or range of motion | Veritabanındaki tanımı bir nesneyi 'uzatma, germe'dir; spor öncesi esneme egzersizi olarak tanımlanmamıştır |
| `seyahat` | **pick up** (phrasal_verb, A2) | `22103` | almak, toplamak | to take something that is lying or standing somewhere and bring it with you | Veritabanındaki tanımı 'yerde duran bir nesneyi eliyle kaldırmak/almak'tır; yolcuyu araçla almak (pick someone up) anlamı değildir |
| `ulasim` | **pick up** (phrasal_verb, A2) | `22103` | almak, toplamak | to take something that is lying or standing somewhere and bring it with you | Veritabanındaki tanımı 'yerden bir nesneyi almak/kaldırmak'tır; yolcu almak anlamı değildir |
| `ulasim` | **platform** (noun, A2) | `17610` | yükseltilmiş zemin, platform | a raised, flat surface on which people or things can stand or be placed | Veritabanındaki tanımı konuşmacı/sahne için 'yükseltilmiş kürsü, podyum'dur; tren peronu anlamı değildir |
| `ulasim` | **radiator** (noun, B1) | `19208` | radyatör, kalorifer peteği | a device, usually made of metal, that transfers heat from hot water or steam to the surrounding air in a building | Veritabanındaki tanımı ev/odaları ısıtan 'kalorifer peteği'dir; otomobil motor radyatörü anlamı değildir |
| `ulasim` | **wing** (noun, A2) | `17867` | kanat | the paired, usually feathered appendage of a bird or other flying animal that enables flight | Veritabanındaki tanımı 'kuş kanadı (feathered appendage of a bird)'dır; uçak kanadı anlamı değildir |
| `sehir-yerler` | **booth** (noun, B2) | `14642` | kabin, küçük bölme | a small enclosed compartment where a person can cast a vote or perform a private activity | Veritabanındaki tanımı 'oy verme/telefon kabini'dir; şehir mekânı olarak temel bir yer değildir |
| `sehir-yerler` | **opposite** (noun, A2) | `6243` | karşıtı, zıttı | a thing that is completely different from or contrary to another | Veritabanındaki tanımı soyut 'tam tersi, zıttı (antonym/reverse)'dir; mekânsal 'karşısında (across from)' anlamı değildir |
| `sehir-yerler` | **sign** (noun, A2) | `19267` | belirti, işaret | a mark, object, or event that indicates the presence or existence of something | Veritabanındaki tanımı hastalık/olay için 'belirti, alamet, işaret'tir; sokak/trafik tabelası (street sign) anlamı değildir |
| `alisveris-para` | **card** (noun, A2) | `16302` | kart, tebrik kartı | a piece of paper or cardboard, often folded, that is sent to convey congratulations, good wishes, or greetings | Veritabanındaki tanımı 'tebrik kartı, davetiye kartı (greeting card)'dır; kredi/banka kartı anlamı veritabanında yoktur |
| `hava-durumu` | **biting** (adjective, B2) | `7233` | keskin, alaycı | causing a sharp or stinging effect, especially in speech or taste; sharply critical or sarcastic. | Veritabanındaki tanımı 'keskin, iğneleyici, alaycı (söz/konuşma)'dır; dondurucu soğuk (biting cold) anlamı değildir |
| `hava-durumu` | **boil** (verb, A2) | `3255` | kaynatmak, kaynamaya getirmek | to heat a liquid until it reaches its boiling point and produces bubbles | Veritabanındaki tanımı mutfakta 'sıvıyı kaynatmak'tır; havanın aşırı sıcak olması (boiling hot) anlamı değildir |
| `hava-durumu` | **clear** (adjective, A2) | `9476` | açık, belli, anlaşılır | easily understood or perceived; not hidden or ambiguous | Veritabanındaki tanımı 'açık, anlaşılır, belli (easily understood)'dir; bulutsuz/açık hava anlamı veritabanında yoktur |
| `hava-durumu` | **degree** (noun, B1) | `16596` | derece | a unit of angular measurement equal to 1/360 of a full circle | Veritabanındaki tanımı geometrik 'açı derecesi (1/360 çember)'dir; sıcaklık derecesi (temperature degree) anlamı değildir |
| `hava-durumu` | **freezing** (noun, B2) | `4124` | donma, dondurma süreci | the process of turning a liquid into a solid by lowering its temperature to the freezing point | Veritabanındaki tanımı fiziksel/endüstriyel 'sıvıyı dondurma işlemi'dir; dondurucu hava (freezing:adj) değildir |
| `doga` | **crystal** (noun, B1) | `7833` | kristal, kristal cam | a clear, hard, transparent material made of silica, often used for decorative objects or drinkware | Veritabanındaki tanımı insan yapımı 'kristal cam eşya (glassware)'dır; doğal mineral kristali değildir |
| `doga` | **tremor** (noun, B2) | `1616` | titreme, sarsıntı | a small or slight shaking movement, especially of the body or an object | Veritabanındaki tanımı 'vücut/el titremesi (trembling of the body)'dir; deprem sarsıntısı olarak tanımlanmamıştır |
| `hayvanlar` | **antenna** (noun, B1) | `21246` | anten | a device that receives or transmits radio, television, or other electromagnetic signals | Veritabanındaki tanımı radyo/TV 'elektrik/metal anteni'dir; böcek duyargası/anteni anlamı değildir |
| `hayvanlar` | **den** (noun, B1) | `21565` | in, çalışma odası, sığınak | a small, secluded room or shelter, often used as a private retreat or a wild animal's lair | Veritabanındaki tanımı evdeki 'küçük özel çalışma odası, sığınak'tır; vahşi hayvan ini olarak tanımlanmamıştır |
| `hayvanlar` | **sponge** (noun, A2) | `22406` | sünger | a porous, absorbent material used for cleaning or soaking up liquids | Veritabanındaki tanımı temizlikte kullanılan 'bulaşık/temizlik süngeri'dir; deniz canlısı olan sünger değildir |
| `zaman` | **alarm** (noun, A2) | `395` | alarm | a device that makes a loud sound to warn of danger or to wake someone | Veritabanındaki tanımı 'tehlike/yangın/hırsız alarmı veya korku/endişe'dir; çalar saat (alarm clock) anlamı değildir |
| `zaman` | **annual** (noun, B2) | `14192` | yıllık, yıllık yayın | a publication that is issued once a year | Veritabanında 'annual' yalnızca isim olarak ('yılda bir basılan dergi/yıllık kitap') kayıtlıdır; 'yıllık (her yıl yapılan)' sıfat anlamı değildir |
| `zaman` | **pass** (verb, A2) | `1181` | geçmek, bir yeri aşmak | to move or cause to move in a specified direction so that one goes beyond a point, obstacle, or area | Veritabanındaki tanımı mekânsal olarak 'bir yerin yanından geçip gitmek'tir; zamanın geçmesi anlamı değildir |
| `iletisim-medya` | **advert** (verb, C2) | `23855` | değinmek, bahsetmek | to refer to or mention something briefly | Veritabanında 'advert' yalnızca C2 seviyesinde arkaik fiil ('bir konuya değinmek, atıfta bulunmak - advert to') olarak kayıtlıdır; 'reklam/ilan' isim anlamı yoktur! |
| `teknoloji` | **cloud** (noun, A2) | `578` | bulut | a visible mass of condensed water vapor floating in the atmosphere | Veritabanındaki tanımı gökyüzündeki 'su buharı bulutu'dur; bulut bilişim (cloud computing) anlamı veritabanında yoktur |
| `teknoloji` | **drag** (verb, B1) | `740` | sürüklemek, çekmek | to pull someone or something along the ground or across a surface, often with effort or resistance | Veritabanındaki tanımı ağır bir cismi 'yerde sürükleyerek çekmek'tir; fareyle sürükle-bırak (drag and drop) anlamı değildir |
| `teknoloji` | **drop** (verb, A2) | `11216` | bırakmak, düşürmek | to let something fall unintentionally or intentionally from a higher position to a lower one | Veritabanındaki tanımı fiziksel bir cismi 'elinden düşürmek'tir; fareyle sürükle-bırak (drag and drop) anlamı değildir |
| `teknoloji` | **freeze** (verb, B1) | `4121` | katılaşmak, donmak | to change from a liquid or gas to a solid state, typically because of low temperature | Veritabanındaki tanımı sıvının 'buz hâline gelmesi, donması'dır; bilgisayar/ekran donması anlamı değildir |
| `teknoloji` | **menu** (noun, Belirtilmemiş) | `20335` | menü, yemek listesi | a list of the food that you can order in a restaurant | Veritabanındaki tanımı restorandaki 'yemek listesi, menü'dür; bilgisayar/uygulama menüsü anlamı veritabanında yoktur |
| `teknoloji` | **paste** (verb, B1) | `22066` | yapıştırmak | to attach or stick one material to another, usually by applying an adhesive substance | Veritabanındaki tanımı kağıt/malzemeyi 'tutkalla yapıştırmak'tır; bilgisayarda kopyala-yapıştır (copy & paste) anlamı değildir |
| `teknoloji` | **program** (noun, A2) | `15624` | program | a scheduled series of radio or television content | Veritabanındaki tanımı 'televizyon veya radyo yayını/programı'dır; bilgisayar yazılımı/programı anlamı değildir |
| `teknoloji` | **smart** (adjective, A1) | `16976` | akıllı, zeki | having or showing a quick-witted intelligence; able to understand and solve problems efficiently | Veritabanındaki tanımı insan için 'zeki, akıllı (quick-witted)'dir; akıllı cihaz/telefon (smart device) anlamı değildir |
| `teknoloji` | **window** (noun, A2) | `19970` | pencere | an opening in the wall of a building, vehicle, or computer screen that allows light, air, or a view to pass through. | Veritabanındaki tanımı bina duvarındaki 'cam pencere'dir; bilgisayar arayüz penceresi anlamı değildir |
| `bilim-arastirma` | **blind** (adjective, A2) | `469` | görme yeteneği olmayan, kör | unable to see; lacking visual perception | Veritabanındaki tanımı fiziksel 'görme yeteneği olmayan, kör'dür; 'kör deney (blind study)' anlamı yoktur |
| `ekonomi-is-dunyasi` | **recovery** (noun, B1) | `2246` | iyileşme, toparlanma | the process of returning to a normal state of health, mind, or strength after illness or injury | Veritabanındaki tanımı 'hastalıktan/travmadan iyileşme, sağlığına kavuşma'dır; ekonomik toparlanma değildir |
| `ekonomi-is-dunyasi` | **speculation** (noun, B2) | `5491` | tahmin, spekülasyon | the act of forming ideas or theories without firm evidence; a guess or hypothesis about something uncertain | Veritabanındaki tanımı 'kanıtsız tahmin yürütme'dir; finansal spekülasyon anlamı (speculate fiilinin aksine) isimde yoktur |
| `siyaset-toplum` | **assimilation** (noun, C1) | `24983` | özümseme, entegrasyon, asimilasyon | the process of taking in and fully understanding information or ideas; the process by which a minority group adopts the customs and attitudes of the prevailing culture. | Veritabanındaki tanımı 'bilgiyi zihne alıp tam olarak kavrama/özümseme'dir; kültürel/toplumsal asimilasyon anlamı değildir |
| `siyaset-toplum` | **discrimination** (noun, B2) | `9601` | ayırt etme, ayrım | the act or process of distinguishing between two or more things; a distinction | Veritabanındaki tanımı bilişsel olarak 'iki şey arasındaki farkı ayırt etme'dir; toplumsal ayrımcılık (racial/gender discrimination) anlamı değildir |
| `psikoloji-zihin` | **break down** (phrasal_verb, Belirtilmemiş) | `26212` | başarısız olmak, çökmek | to fail or stop | Veritabanındaki tanımı müzakere/sistem için 'başarısız olmak, çökmek'tir; duygusal çöküntü yaşamak anlamı (26211) değildir |
| `psikoloji-zihin` | **character** (noun, B1) | `1792` | karakter, kahraman | a person in a story, play, film, or other narrative work | Veritabanındaki tanımı roman/filmdeki 'kurgusal karakter, kahraman'dır; psikolojik karakter/kişilik anlamı değildir |
| `psikoloji-zihin` | **projection** (noun, B2) | `9155` | yansıtma, izdüşüm | the act of extending something outward or the image of something on a surface, especially in geometry or optics | Veritabanındaki tanımı fiziksel/optik 'dışarı uzanma veya görüntü izdüşümü'dür; psikolojik yansıtma savunma mekanizması değildir |
| `cevre-iklim` | **exhaust** (verb, B2) | `2726` | yormak, bitkin düşürmek, tüketmek, bitirmek | to use up completely; to cause someone to become very tired | Veritabanındaki tanımı bir insanı 'yormak, bitkin düşürmek'tir; egzoz gazı (exhaust:n) değildir |
| `cevre-iklim` | **footprint** (noun, A2) | `13528` | ayak izi | the mark or impression left by a foot on a surface | Veritabanındaki tanımı çamur/kum üzerindeki fiziksel 'ayak izi'dir; 'karbon ayak izi (carbon footprint)' anlamı değildir |

## 5. Kategoriye Ait Olmayan / Kapsam Dışı Kelimeler (`KATEGORIYE_AIT_DEGIL_CIKAR`)

### `duygular` — Duygular (8 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **crush** | noun (B1) | `2323` | hoşlanma, platonik aşk, romantik ilgi | hoşlanma, platonik aşk, romantik ilgi | Romantik ilişki kavramıdır ('hoşlanma, platonik aşk'); aile-iliskiler kategorisinde zaten vardır, temel duygu değildir |
| **frown** | verb (B1) | `874` | kaşlarını çatmak, surat asmak | kaşlarını çatmak, surat asmak | Yüz hareketidir ('kaşlarını çatmak'); duygu değil mimiktir |
| **groan** | verb (B1) | `4697` | inlemek, homurdanmak | inlemek, homurdanmak | Ses çıkarma eylemidir ('inlemek, homurdanmak'); duygu değildir |
| **scream** | verb (B1) | `1392` | çığlık atmak, bağırmak | çığlık atmak, bağırmak | Ses çıkarma eylemidir ('çığlık atmak, bağırmak'); duygu değildir |
| **shiver** | verb (B1) | `6380` | titremek, ürpermek | titremek, ürpermek | Soğuktan veya korkudan fiziksel 'titremek' fiilidir; duygu değil bedensel tepkidir |
| **sigh** | noun (B1) | `1449` | iç çekiş | iç çekiş | Nefes verme eylemidir ('iç çekme, ah çekme'); duygu değildir |
| **sigh** | verb (B1) | `1450` | iç çekmek | iç çekmek | Nefes verme eylemidir ('iç çekmek'); duygu değildir |
| **tremble** | verb (B1) | `1615` | titremek | titremek | Fiziksel 'titremek, sarsılmak' fiilidir; duygu değil bedensel tepkidir |

### `kisilik-davranis` — Kişilik ve davranış (2 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **routine** | noun (B1) | `6803` | alışkanlık, rutin | alışkanlık, rutin | Günlük zaman/düzen kavramıdır ('rutin, günlük alışkanlık'); kişilik özelliği değildir |
| **versatile** | adjective (B2) | `22561` | çok yönlü, çeşitli alanlarda kullanılabilen | çok yönlü, çeşitli alanlarda kullanılabilen | Daha çok eşya/yetenek için kullanılan 'çok yönlü, çok amaçlı' sıfatıdır |

### `gorunus-beden` — Görünüş ve beden (15 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **blink** | verb (A2) | `5087` | göz kırpmak | göz kırpmak | Refleks/göz hareketidir ('göz kırpmak'); beden parçası veya dış görünüş değildir |
| **charming** | adjective (B2) | `557` | çekici, büyüleyici | çekici, büyüleyici | Kişilik/etki sıfatıdır ('çekici, büyüleyici, sempatik'); kisilik-davranis kategorisinde zaten vardır |
| **crouch** | verb (B1) | `8217` | çömelmek, sinmek, eğilmek | çömelmek, sinmek, eğilmek | Hareket/duruş fiilidir ('çömelmek'); dış görünüş değildir |
| **frown** | verb (B1) | `874` | kaşlarını çatmak, surat asmak | kaşlarını çatmak, surat asmak | Mimik eylemidir ('kaşlarını çatmak'); beden parçası veya dış görünüş değildir |
| **gaze** | verb (B1) | `882` | uzun uzun bakmak, dalıp bakmak, gözünü dikip bakmak | uzun uzun bakmak, dalıp bakmak, gözünü dikip bakmak | Bakış eylemidir ('uzun uzun bakmak'); beden parçası veya dış görünüş değildir |
| **glance** | verb (B1) | `888` | bakmak, göz atmak | bakmak, göz atmak | Bakış eylemidir ('hızlıca göz atmak'); beden parçası veya dış görünüş değildir |
| **kneel** | verb (B1) | `6520` | diz çökmek | diz çökmek | Hareket/duruş fiilidir ('diz çökmek'); dış görünüş değildir |
| **lean** | verb (B1) | `1054` | eğilmek, yaslanmak, yana yatmak | eğilmek, yaslanmak, yana yatmak | Hareket/duruş fiilidir ('eğilmek, yaslanmak'); dış görünüş değildir |
| **lovely** | adjective (A2) | `4232` | güzel, hoş | güzel, hoş | Genel beğeni sıfatıdır ('hoş, çok güzel, harika'); fiziksel görünüşe özgü değildir |
| **neat** | adjective (A2) | `10691` | düzenli, tertipli | düzenli, tertipli | Düzen/temizlik sıfatıdır ('düzenli, tertipli, derli toplu'); fiziksel görünüş veya beden kelimesi değildir |
| **nod** | verb (B1) | `1145` | başını sallamak | başını sallamak | İletişim/baş hareketidir ('onaylamak için başını sallamak'); beden parçası veya dış görünüş değildir |
| **spit** | verb (B1) | `9885` | tükürmek | tükürmek | Fiziksel eylemdir ('tükürmek'); görünüş ve beden kategorisine uygun değildir |
| **stare** | verb (B1) | `6442` | dik dik bakmak, gözlerini dikmek | dik dik bakmak, gözlerini dikmek | Bakış eylemidir ('dik dik bakmak'); beden parçası veya dış görünüş değildir |
| **wink** | verb (B1) | `8427` | göz kırpmak | göz kırpmak | Göz hareketidir ('göz kırpmak'); beden parçası veya dış görünüş değildir |
| **yawn** | verb (A2) | `8034` | esnemek | esnemek | Fizyolojik reflekstir ('esnemek'); dış görünüş değildir |

### `aile-iliskiler` — Aile ve ilişkiler (3 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **darling** | adjective (B1) | `9837` | sevgili, canım, sevimli, tatlı | sevgili, canım, sevimli, tatlı | Genel karşıtlık/muhalefet kelimesidir ('düşman, rakip, hasım'); aile ve özel ilişki kavramı değildir |
| **seal** | verb (B1) | `3926` | kapatmak, mühürlemek | kapatmak, mühürlemek | Daha çok iş/suç/faaliyet ortağı ('ortak, suç ortağı') anlamındadır |
| **tone** | noun (B2) | `1599` | ton, ses tonu, üslup, tavır | ton, ses tonu | Resmi veya ticari işlem ('evlat edinme veya bir fikri/yöntemi benimseme') olarak tanımlanmıştır |

### `yiyecek-icecek` — Yiyecek ve içecek (6 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **bill** | noun (A2) | `15975` | fatura, hesap | fatura, hesap | Finans/ödeme terimidir ('fatura, hesap'); alisveris-para'da zaten vardır, yiyecek/içecek değildir |
| **lean** | adjective (B1) | `1050` | yağsız, ince, zayıf | yağsız, ince, zayıf | İnsan/hayvan bedeni için 'zayıf, ince, yağsız' sıfatıdır (gorunus-beden'de zaten var) |
| **mild** | adjective (B1) | `4635` | hafif, yumuşak | hafif, yumuşak | Genel 'hafif, ılımlı, yumuşak' sıfatıdır |
| **organic** | adjective (B1) | `18987` | organik | organik | Kimyasal/biyolojik 'canlı maddeden türeyen, organik' olarak tanımlanmıştır |
| **portion** | noun (B1) | `4197` | kısım, pay, porsiyon | kısım, pay, porsiyon | Genel 'parça, kısım, pay' olarak tanımlanmıştır; yemek porsiyonu olarak özelleşmemiştir |
| **tip** | noun (A2) | `18129` | bahşiş | bahşiş | Ödeme terimidir ('bahşiş'); alisveris-para'da zaten vardır, yiyecek/içecek değildir |

### `yemek-yapma` — Yemek yapma (9 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **add** | verb (A2) | `13616` | eklemek, toplamak | eklemek, toplamak | Genel matematik/ekleme fiilidir ('eklemek, toplamak') |
| **container** | noun (B1) | `18154` | kap, saklama kabı | kap, saklama kabı | Genel taşımacılık/saklama 'kap, kutu, konteyner' kelimesidir |
| **cut** | verb (A2) | `15690` | kesmek, doğramak | kesmek, doğramak | Genel 'kesmek' fiilidir |
| **funnel** | noun (B1) | `23133` | huni, daralan boru | huni, daralan boru | Genel sıvı aktarma aparatıdır ('huni') |
| **measure** | verb (B1) | `10930` | ölçmek, belirlemek | ölçmek, belirlemek | Genel 'ölçmek' fiilidir |
| **serve** | verb (A1) | `19958` | sunmak, hizmet etmek | sunmak, hizmet etmek | 1. anlamı 'hizmet etmek, görev yapmak'tır; yemek servis etmek (19959) yiyecek-icecek'te bağlıdır |
| **thermometer** | noun (A2) | `24839` | sıcaklık ölçer, termometre | sıcaklık ölçer, termometre | Sıcaklık ölçüm aletidir ('termometre'); hava-durumu ve saglik'ta zaten vardır |
| **timer** | noun (A2) | `15100` | zamanlayıcı | zamanlayıcı | Zaman ölçerdir ('zamanlayıcı, kronometre') |
| **wash** | verb (A1) | `2265` | yıkamak, temizlemek | yıkamak, temizlemek | Genel 'yıkamak' fiilidir |

### `ev-esyalar` — Ev ve eşyalar (43 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **beam** | noun (B2) | `442` | kiriş | ışın, ışık demeti | İnşaat yapı elemanıdır ('kiriş') ve 1. anlamı 'ışın' olduğu için kartta 'ışın, ışık hüzmesi' olarak görünmektedir |
| **bleach** | noun (B1) | `22768` | çamaşır suyu | çamaşır suyu | Temizlik kimyasalıdır ('çamaşır suyu'); mobilya veya ev eşyası değildir |
| **bolt** | noun (B1) | `1982` | sürgü | sürgü | Hırdavat/kapı parçasıdır ('sürgü, cıvata'); mobilya veya ev eşyası değildir |
| **brick** | noun (A2) | `5738` | tuğla | tuğla | İnşaat ham maddesidir ('tuğla'); mobilya veya ev eşyası değildir |
| **column** | noun (B1) | `596` | sütun, dikey destek | sütun, dikey destek | Mimari/inşaat yapı elemanıdır ('taş sütun'); mobilya veya ev eşyası değildir |
| **cord** | noun (B1) | `7125` | elektrik kablosu | halat, ip | Elektrik malzemesidir ('elektrik kablosu'); mobilya veya temel ev eşyası değildir |
| **detergent** | noun (B1) | `25158` | temizleyici, deterjan | temizleyici, deterjan | Temizlik kimyasalıdır ('deterjan'); mobilya veya ev eşyası değildir |
| **drain** | noun (B1) | `8666` | gider, mazgal, su yolu | gider, mazgal, su yolu | Altyapı/tesisat terimidir ('gider, lağım, mazgal'); mobilya veya ev eşyası değildir |
| **drill** | noun (A2) | `8084` | matkap, delgi aleti | matkap, delgi aleti | El aleti/inşaat ekipmanıdır ('matkap'); mobilya veya ev eşyası değildir |
| **evict** | verb (C1) | `23073` | tahliye etmek | tahliye etmek | Hukuki tahliye işlemidir ('kiracıyı mülkten tahliye etmek'); ev eşyası veya mobilya değildir |
| **fuse** | noun (B1) | `9352` | sigorta | sigorta | Elektrik tesisatı parçasıdır ('elektrik sigortası'); mobilya veya temel ev eşyası değildir |
| **glue** | noun (B1) | `11969` | yapıştırıcı | yapıştırıcı | Kırtasiye/tamir malzemesidir ('yapıştırıcı, tutkal'); mobilya veya ev eşyası değildir |
| **hammer** | noun (A2) | `7548` | çekiç | çekiç | El aleti/hırdavat malzemesidir ('çekiç'); mobilya veya ev eşyası değildir |
| **hinge** | noun (B1) | `19648` | menteşe | menteşe | Hırdavat parçasıdır ('menteşe'); mobilya veya ev eşyası değildir |
| **landing** | noun (Belirtilmemiş) | `20559` | sahanlık | iniş (uçak) | 2. anlamı 'sahanlık (merdiven başı)'tır ancak kartta 1. anlamı olan 'iniş (uçak)' görünmektedir; ayrıca mobilya/ev eşyası değildir |
| **landlord** | noun (B1) | `19131` | ev sahibi, kiraya veren | ev sahibi, kiraya veren | Kişi/statü kelimesidir ('ev sahibi'); evin bölümleri veya mobilya değildir |
| **lease** | noun (B2) | `21026` | kira sözleşmesi | kira sözleşmesi | Hukuki/finansal sözleşme terimidir ('kira sözleşmesi, kontrat'); ev eşyası veya mobilya değildir |
| **lease** | verb (B2) | `21027` | kiralamak, kiraya vermek | kiralamak, kiraya vermek | Hukuki/finansal işlemdir ('kiraya vermek, kiralamak'); ev eşyası veya mobilya değildir |
| **mortgage** | noun (Belirtilmemiş) | `20573` | konut kredisi, ipotek | konut kredisi, ipotek | Finans ve bankacılık terimidir ('konut kredisi, ipotek'); 'Ev ve eşyalar (Home and furniture)' kategorisine ait değildir (alisveris-para ve ekonomi-is-dunyasi'nda zaten var) |
| **nail** | noun (A2) | `3861` | çivi | çivi | Hırdavat malzemesidir ('çivi'); mobilya veya ev eşyası değildir |
| **neighbor** | noun (A2) | `4831` | komşu | komşu | Kişi/ilişki kelimesidir ('komşu'); aile-iliskiler kategorisinde zaten yer almaktadır |
| **pillar** | noun (B2) | `7343` | sütun, destek | sütun, destek | Mimari/inşaat yapı elemanıdır ('sütun, kolon'); mobilya veya ev eşyası değildir |
| **pipe** | noun (A2) | `2101` | boru, kanal | boru, kanal | Altyapı/tesisat malzemesidir ('boru'); mobilya veya ev eşyası değildir |
| **plumbing** | noun (B2) | `22138` | tesisat, borulama sistemi | tesisat, borulama sistemi | İnşaat/altyapı terimidir ('su ve kanalizasyon tesisatı'); mobilya veya ev eşyası değildir |
| **polish** | noun (B1) | `5603` | cila, parlatıcı | cila, parlatıcı | Genel parlatma işlemidir ('cilalama, parlatma'); mobilya kategorisi için yan unsurdur |
| **polish** | verb (B1) | `5605` | parlatmak, yüzeyi pürüzsüz hâle getirmek | parlatmak, yüzeyi pürüzsüz hâle getirmek | Genel 'parlatmak, cilalamak' fiilidir; mobilya kategorisi için yan unsurdur |
| **rag** | noun (B1) | `2345` | bez, paçavra | bez, paçavra | Eski bez parçasıdır ('paçavra, toz bezi'); mobilya veya temel ev eşyası değildir |
| **razor** | noun (B1) | `10647` | tıraş bıçağı, jilet, ustura | tıraş bıçağı, jilet, ustura | Kişisel bakım ürünüdür ('tıraş bıçağı, ustura'); mobilya veya ev eşyası değildir |
| **rent** | noun (A2) | `17992` | kira | kira | Finansal ödemedir ('kira bedeli'); ev eşyası değildir (alisveris-para'da zaten var) |
| **rent** | verb (B1) | `17994` | kiralamak | kiralamak | Finansal işlemdir ('ücret karşılığı kiralamak'); ev eşyası değildir (alisveris-para'da zaten var) |
| **roommate** | noun (B1) | `15464` | oda arkadaşı, ev arkadaşı | oda arkadaşı, ev arkadaşı | Kişi/ilişki kelimesidir ('ev arkadaşı'); aile-iliskiler kategorisinde zaten yer almaktadır |
| **screw** | noun (A2) | `5122` | vida | vida | Hırdavat malzemesidir ('vida'); mobilya veya ev eşyası değildir |
| **screwdriver** | noun (A2) | `5125` | tornavida | tornavida | El aleti/hırdavat malzemesidir ('tornavida'); mobilya veya ev eşyası değildir |
| **shampoo** | noun (A2) | `22351` | şampuan, saç temizleme ürünü | şampuan, saç temizleme ürünü | Kişisel bakım ürünüdür ('şampuan'); mobilya veya ev eşyası değildir |
| **soap** | noun (A2) | `10888` | sabun | sabun | Kişisel temizlik ürünüdür ('sabun'); mobilya veya ev eşyası değildir |
| **tape** | noun (A2) | `5379` | bant | bant | Kırtasiye/paketleme malzemesidir ('yapışkan bant'); mobilya veya ev eşyası değildir |
| **tenant** | noun (Belirtilmemiş) | `20809` | kiracı | kiracı | Kişi/statü kelimesidir ('kiracı'); evin bölümleri veya mobilya değildir |
| **tissue** | noun (A2) | `7510` | kağıt mendil, ince kağıt | kağıt mendil, ince kağıt | Kişisel hijyen/tüketim ürünüdür ('kağıt mendil'); 'Home and furniture' kategorisine ait değildir (1. anlamı da 'biyolojik doku'dur) |
| **toothbrush** | noun (A1) | `23768` | diş fırçası | diş fırçası | Kişisel bakım ürünüdür ('diş fırçası'); mobilya veya ev eşyası değildir |
| **toothpaste** | noun (A2) | `23769` | diş macunu | diş macunu | Kişisel bakım ürünüdür ('diş macunu'); mobilya veya ev eşyası değildir |
| **vent** | noun (B2) | `9494` | havalandırma açıklığı, delik | havalandırma açıklığı, delik | Tesisat/havalandırma terimidir ('havalandırma deliği, baca'); mobilya veya ev eşyası değildir |
| **wire** | noun (A2) | `5541` | tel | tel | Genel elektrik/metal malzemesidir ('tel, kablo teli'); mobilya veya temel ev eşyası değildir |
| **wrench** | noun (B1) | `7197` | İngiliz anahtarı, somun anahtarı, anahtar | İngiliz anahtarı, somun anahtarı, anahtar | Tamir/tesisat aletidir ('İngiliz anahtarı, somun anahtarı'); mobilya veya ev eşyası değildir |

### `giyim-moda` — Giyim ve moda (20 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **apron** | noun (A2) | `11776` | önlük | önlük | Mutfak/iş koruyucu örtüsüdür ('mutfak/iş önlüğü') |
| **backpack** | noun (A2) | `8859` | sırt çantası | sırt çantası | Çanta/seyahat eşyasıdır ('sırt çantası'); seyahat ve okul kategorilerinde daha uygundur |
| **change** | verb (A1) | `14271` | değiştirmek, farklı hâle getirmek | değiştirmek, farklı hâle getirmek | Genel 'değiştirmek, farklı hâle getirmek' fiilidir; üstünü değiştirmek anlamı özelleşmemiştir |
| **crown** | noun (A2) | `18084` | taç | taç | Tarihsel/kraliyet sembolüdür ('kraliyet tacı'); giyim ve moda kelimesi değildir |
| **diamond** | noun (A2) | `7656` | elmas | elmas | Değerli taştır ('elmas'); doğrudan giyim kelimesi değildir |
| **disguise** | noun (B2) | `8168` | kılık, kılık değiştirme | kılık, kılık değiştirme | Kimlik gizleme kavramıdır ('kılık değiştirme, gizleme'); moda terimi değildir |
| **fold** | verb (A2) | `2219` | katlamak, bükmek | katlamak, bükmek | Genel fiziksel eylemdir ('katlamak, bükmek') |
| **gem** | noun (B1) | `21723` | değerli taş | değerli taş | Değerli taştır ('cevher, kıymetli taş'); doğrudan giyim kelimesi değildir |
| **gold** | noun (A1) | `15910` | altın | altın | Kimyasal element/değerli metaldir ('altın'); doğrudan giyim kelimesi değildir |
| **handkerchief** | noun (A2) | `8030` | mendil | mendil | Temizlik/hijyen eşyasıdır ('cep mendili') |
| **helmet** | noun (A2) | `10097` | kask | kask | Güvenlik/spor ekipmanıdır ('kask, miğfer'); spor ve ulasim'da zaten vardır |
| **iron** | verb (A2) | `17337` | ütülemek | ütülemek | Ev işi fiilidir ('ütü yapmak') |
| **jewel** | noun (B1) | `9938` | mücevher | mücevher | Değerli taştır ('mücevher taşı'); doğrudan giyim kelimesi değildir |
| **pattern** | noun (B1) | `18072` | örnek, desen, kalıp | örnek, desen, kalıp | Genel 'örnek, kalıp, düzen' kelimesidir |
| **pearl** | noun (B1) | `9443` | inci | inci | Değerli taştır ('inci'); doğrudan giyim kelimesi değildir |
| **silver** | noun (B1) | `9764` | gümüş | gümüş | Kimyasal element/değerli metaldir ('gümüş'); doğrudan giyim kelimesi değildir |
| **stain** | noun (B1) | `7732` | leke | leke | Temizlik terimidir ('leke, kir'); giyim ve moda kavramı değildir |
| **stain** | verb (B1) | `7734` | lekelemek | lekelemek | Temizlik terimidir ('lekelemek, kirletmek'); giyim ve moda kavramı değildir |
| **umbrella** | noun (A2) | `12781` | şemsiye | şemsiye | Yağmur eşyasıdır ('şemsiye'); giysi veya moda terimi değildir |
| **wallet** | noun (A2) | `13796` | cüzdan | cüzdan | Kişisel para eşyasıdır ('cüzdan'); alisveris-para'da zaten vardır |

### `saglik` — Sağlık ve hastalık (3 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **twist** | verb (B1) | `1979` | burkmak, bükmek | burkmak, bükmek | Genel fiziksel 'bükmek, kıvırmak' fiilidir (burkulmak sprain ile zaten mevcuttur) |
| **vet** | noun (Belirtilmemiş) | `27420` | veteriner | veteriner | Hayvan doktorudur ('veteriner'); is-meslekler'de zaten vardır, insan sağlığı/tıp kategorisine ait değildir |
| **veterinarian** | noun (B2) | `14239` | veteriner, veteriner hekim, hayvan hekimi | veteriner, veteriner hekim, hayvan hekimi | Hayvan doktorudur ('veteriner hekim'); is-meslekler'de zaten vardır, insan sağlığı/tıp kategorisine ait değildir |

### `okul-egitim` — Okul ve eğitim (12 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **absent** | adjective (A2) | `2930` | yok, bulunmayan | yok, bulunmayan | Genel 'yok, mevcut olmayan' sıfatıdır |
| **ceremony** | noun (B2) | `6655` | tören | tören | Genel toplumsal etkinliktir ('tören, merasim'); okula özgü değildir |
| **corridor** | noun (B1) | `645` | koridor, geçit | koridor, geçit | Genel bina bölümüdür ('koridor'); okula özgü değildir |
| **glue** | noun (B1) | `11969` | yapıştırıcı | yapıştırıcı | Genel yapıştırıcı/tutkal malzemesidir |
| **hall** | noun (A2) | `6492` | salon, toplantı salonu, büyük oda | salon, toplantı salonu, büyük oda | Genel bina bölümüdür ('hol, salon'); okula özgü değildir |
| **law** | noun (A2) | `19900` | yasa, kanun, hukuk | yasa, kanun, hukuk | Hukuk kavramıdır ('hukuk, yasa'); hukuk-suc kategorisinde zaten vardır |
| **manual** | noun (B1) | `13770` | kullanma kılavuzu, el kitabı | kullanma kılavuzu, el kitabı | Cihaz/makine 'kullanma kılavuzu, el kitabı'dır; okul ders kitabı değildir |
| **present** | adjective (A2) | `2946` | mevcut, bulunmakta olan | mevcut, bulunmakta olan | Genel 'mevcut, hazır bulunan' sıfatıdır |
| **proverb** | noun (B2) | `11161` | atasözü | atasözü | Dil/kültür kavramıdır ('atasözü'); okul-egitim kelimesi değildir |
| **scissors** | noun (A2) | `22324` | makas | makas | Genel kesici alettir ('makas') |
| **stapler** | noun (A2) | `22416` | zımba | zımba | Ofis/kırtasiye eşyasıdır ('zımba') |
| **tape** | noun (A2) | `5379` | bant | bant | Genel yapışkan bant malzemesidir |

### `is-meslekler` — İş ve meslekler (7 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **boycott** | verb (B2) | `21346` | boykot etmek | boykot etmek | Siyasi/tüketici eylemidir ('boykot etmek'); siyaset-toplum'da zaten vardır, iş/meslek terimi değildir |
| **call off** | phrasal_verb (Belirtilmemiş) | `26235` | iptal etmek | iptal etmek | Genel phrasal verb'dür ('iptal etmek'); iş ve mesleklere özgü değildir |
| **insurance** | noun (B2) | `16604` | sigorta, teminat | sigorta, teminat | Finans terimidir ('sigorta'); ekonomi-is-dunyasi'nda zaten vardır |
| **put off** | phrasal_verb (Belirtilmemiş) | `26626` | ertelemek | ertelemek | Genel phrasal verb'dür ('ertelemek'); iş ve mesleklere özgü değildir |
| **relocate** | verb (B1) | `8138` | taşınmak, yer değiştirmek | taşınmak, yer değiştirmek | Genel taşınma fiilidir ('taşınmak, başka yere yerleşmek') |
| **stationery** | noun (B1) | `24795` | kırtasiye malzemeleri | kırtasiye malzemeleri | Kırtasiye malzemeleridir ('kırtasiye'); okul-egitim'de zaten vardır |
| **tax** | noun (B1) | `16006` | vergi | vergi | Ekonomi/maliye terimidir ('vergi'); ekonomi-is-dunyasi'nda zaten vardır |

### `sanat-eglence` — Sanat, müzik ve film (2 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **auction** | noun (Belirtilmemiş) | `20515` | açık artırma, mezat | açık artırma, mezat | Ticaret/satış yöntemidir ('açık artırma, müzayede'); alisveris-para'da zaten vardır |
| **collector** | noun (B2) | `8507` | koleksiyoncu | koleksiyoncu | Hobi/ticaret kişisidir ('koleksiyoncu'); bos-zaman'da zaten vardır |

### `spor` — Spor (2 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **ribbon** | noun (A2) | `10358` | kurdele | kurdele | Tuhafiye/süs eşyasıdır ('kurdele'); spor terimi değildir |
| **swing** | verb (A2) | `3040` | sallanmak, sallamak | sallanmak, sallamak | Genel 'sallanmak, ileri geri salınmak' fiilidir |

### `bos-zaman` — Boş zaman ve hobiler (5 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **astronomy** | noun (Belirtilmemiş) | `27464` | astronomi, gökbilim | astronomi, gökbilim | Bilim dalıdır ('astronomi, gök bilimi'); bilim-arastirma kategorisinde zaten vardır |
| **coin** | noun (A2) | `3639` | madeni para | madeni para | Para birimidir ('madeni para, bozuk para'); alisveris-para'da zaten vardır (koleksiyonculuk yüzünden eklenmiş) |
| **holiday** | noun (A2) | `17656` | bayram, resmi tatil | bayram, resmi tatil | Resmi/dini gün terimidir ('bayram, resmi tatil'); kültür/zaman kavramıdır |
| **telescope** | noun (A2) | `22478` | teleskop | teleskop | Bilimsel gözlem cihazıdır ('teleskop'); bilim-arastirma kategorisinde zaten vardır |
| **volunteer** | noun (B1) | `4309` | gönüllü, ücretsiz çalışan | gönüllü, ücretsiz çalışan | Toplumsal/iş kavramıdır ('gönüllü çalışan'); siyaset-toplum ve is-meslekler'de zaten vardır |

### `seyahat` — Seyahat ve tatil (9 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **bargain** | verb (B1) | `9873` | (with ile) pazarlık yapmak, pazarlığa oturmak | (with ile) pazarlık yapmak, pazarlığa oturmak | Alışveriş terimidir ('pazarlık yapmak'); alisveris-para'da zaten vardır |
| **cancel** | verb (Belirtilmemiş) | `20521` | iptal etmek | iptal etmek | Genel 'iptal etmek' fiilidir; seyahate özgü değildir |
| **delay** | noun (B1) | `4098` | gecikme | gecikme | Genel 'gecikme, erteleme' ismidir |
| **double** | adjective (A2) | `14573` | çift, iki kişilik | iki katı, iki misli | Genel sayı/miktar sıfatıdır ('çift, iki kat'); çift kişilik oda anlamı özelleşmemiştir |
| **insurance** | noun (B2) | `16604` | sigorta, teminat | sigorta, teminat | Finans terimidir ('sigorta'); ekonomi-is-dunyasi'nda zaten vardır |
| **leave** | verb (A2) | `15514` | ayrılmak, gitmek | ayrılmak, gitmek | Çok genel 'ayrılmak, çıkmak' fiilidir |
| **postpone** | verb (B1) | `12078` | ertelemek | ertelemek | Genel 'ertelemek' fiilidir; seyahate özgü değildir |
| **room** | noun (A2) | `15461` | oda, salon | oda, salon | Genel 'oda' kelimesidir; ev-esyalar kategorisinde zaten vardır |
| **single** | adjective (B1) | `20016` | tek, yalnız bir | evli olmayan, bekar | Genel sayı/miktar sıfatıdır ('tek, yalnız bir'); tek kişilik oda anlamı özelleşmemiştir |

### `ulasim` — Ulaşım (16 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **ambulance** | noun (B1) | `11895` | ambulans | ambulans | Sağlık acil aracıdır ('ambulans'); saglik kategorisinde zaten vardır |
| **billboard** | noun (B1) | `21324` | reklam panosu, billboard | reklam panosu, billboard | Reklamcılık terimidir ('reklam panosu, billboard'); iletisim-medya'da zaten vardır |
| **catch** | verb (A2) | `16801` | yakalamak, tutmak | yakalamak, tutmak | 1. anlamı 'atılan bir cismi havada yakalamak'tır; otobüs/tren yakalamak anlamı değildir |
| **chain** | noun (A2) | `17705` | zincir | zincir | Genel metal 'zincir (bağlama/güvenlik zinciri)' olarak tanımlanmıştır; ulaşım terimi değildir |
| **crane** | noun (B2) | `11922` | vinç, kaldırma makinesi | turna, uzun boyunlu kuş | İnşaat iş makinesidir ('vinç'); ulaşım aracı değildir |
| **fasten** | verb (B1) | `4278` | bağlamak, tutturmak | bağlamak, tutturmak | Genel 'bağlamak, tutturmak, iliklemek' fiilidir |
| **gutter** | noun (B1) | `23178` | yol kenarı su oluğu, oluk, su kanalı | yol kenarı su oluğu, oluk, su kanalı | Çatı/sokak 'yağmur oluğu'dur; ulaşım kavramı değildir |
| **late** | adjective (A2) | `7496` | geç, zamanında gelmemiş | geç, zamanında gelmemiş | Zaman sıfatıdır ('geç, gecikmiş'); zaman kategorisinde zaten vardır |
| **mirror** | noun (A2) | `2688` | ayna | ayna | Ev eşyası olan genel 'ayna'dır; ev-esyalar'da zaten vardır |
| **miss** | verb (A2) | `15775` | kaçırmak, yakalayamamak | kaçırmak, yakalayamamak | 1. anlamı 'hedefi ıskalamak, kaçırmak'tır |
| **pass** | verb (A2) | `1181` | geçmek, bir yeri aşmak | geçmek, bir yeri aşmak | Genel 'yanından geçmek' fiilidir |
| **run out of** | phrasal_verb (Belirtilmemiş) | `26659` | (bir şey) bitmek, tüketmek | (bir şey) bitmek, tüketmek | Genel '(bir şeyi) bitirmek, tüketmek' phrasal verb'üdür |
| **sink** | verb (A2) | `1915` | batmak, batırmak | batmak, batırmak | Fiziksel 'suya batmak' fiilidir |
| **skateboard** | noun (B1) | `22366` | kaykay | kaykay | Spor/oyun ekipmanıdır ('kaykay'); spor ve bos-zaman'da zaten vardır |
| **tractor** | noun (B1) | `19945` | traktör | traktör | Tarım iş makinesidir ('traktör'); şehir/yolcu ulaşım aracı değildir |
| **wheelchair** | noun (B1) | `6256` | tekerlekli sandalye | tekerlekli sandalye | Tıbbi/ortopedik destektir ('tekerlekli sandalye'); saglik kategorisinde zaten vardır |

### `sehir-yerler` — Şehir ve yerler (15 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **barber** | noun (A2) | `21305` | berber | berber | Meslek/kişi ismidir ('berber'); yer/dükkân değil kişi olarak tanımlanmıştır (is-meslekler'de zaten var) |
| **behind** | adverb (Belirtilmemiş) | `20284` | arkada, geride | arkada, geride | Genel yer/yön zarfıdır ('arkasında, gerisinde'); şehir veya mekân ismi değildir |
| **between** | preposition (A2) | `15152` | arasında | arasında | Genel yer/yön edatıdır ('arasında'); şehir veya mekân ismi değildir |
| **butcher** | noun (B1) | `21373` | kasap | kasap | Meslek/kişi ismidir ('kasap'); yer/dükkân değil kişi olarak tanımlanmıştır (is-meslekler'de zaten var) |
| **citizen** | noun (B1) | `19497` | vatandaş | vatandaş | Toplum/hukuk kavramıdır ('vatandaş, yurttaş'); siyaset-toplum'da zaten vardır, yer ismi değildir |
| **far** | adverb (A2) | `19789` | uzak, uzağa, çok (daha) | uzak, uzağa, çok (daha) | Genel mesafe zarfıdır ('uzakta, uzak'); şehir veya mekân ismi değildir |
| **jeweler** | noun (B2) | `9941` | kuyumcu | kuyumcu | Meslek/kişi ismidir ('kuyumcu'); yer/dükkân değil kişi olarak tanımlanmıştır (is-meslekler'de zaten var) |
| **left** | noun (A2) | `15520` | sol | sol | Genel yön ismidir ('sol taraf'); şehir veya mekân ismi değildir |
| **mayor** | noun (B1) | `17849` | belediye başkanı | belediye başkanı | Siyasi makam/kişi ismidir ('belediye başkanı'); siyaset-toplum ve is-meslekler'de zaten vardır, yer ismi değildir |
| **near** | adjective (A2) | `4554` | yakın, yakın konumda | yakın, yakın konumda | Genel mesafe sıfatıdır ('yakın'); şehir veya mekân ismi değildir |
| **nearby** | adjective (B1) | `4559` | yakındaki, yakın | yakındaki, yakın | Genel mesafe sıfatıdır ('yakındaki, civardaki'); şehir veya mekân ismi değildir |
| **nearby** | adverb (Belirtilmemiş) | `20576` | yakında, yakınlarda | yakında, yakınlarda | Genel mesafe zarfıdır ('yakında, yakınlarda'); şehir veya mekân ismi değildir |
| **right** | noun (A1) | `5890` | sağ, sağ taraf | hak | Genel yön ismidir ('sağ taraf') ve kartta 1. anlamı olan 'hak' görünmektedir; şehir veya mekân ismi değildir |
| **ruin** | noun (B2) | `2870` | yıkım, harabe | yıkım, harabe | Soyut/genel 'yıkım, harabe olma durumu'dur; antik ören yeri (ruins) anlamı değildir |
| **straight** | adjective (A2) | `6621` | düz, bükülmemiş | düz, bükülmemiş | Genel şekil sıfatıdır ('düz, bükülmemiş'); şehir veya mekân ismi değildir |

### `alisveris-para` — Alışveriş ve para (9 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **fare** | noun (B1) | `10113` | bilet ücreti, yol parası, yol ücreti | bilet ücreti, yol parası, yol ücreti | Ulaşım terimidir ('bilet/yolculuk ücreti'); ulasim'da zaten vardır, alışveriş kelimesi değildir |
| **grant** | noun (B2) | `17635` | hibe, bağış | hibe, bağış | Devlet/akademik fon terimidir ('hibe, devlet desteği'); alışveriş kelimesi değildir |
| **loyalty** | noun (B2) | `10895` | sadakat | sadakat | Kişilik ve duygu kavramıdır ('sadakat, bağlılık'); alışveriş ve para kelimesi değildir |
| **online** | adjective (Belirtilmemiş) | `20349` | çevrimiçi, internetteki | çevrimiçi, internetteki | Genel teknoloji sıfatıdır ('çevrimiçi'); alışverişe özgü bir kelime değildir (teknoloji'de zaten var) |
| **pension** | noun (B1) | `10318` | emekli maaşı, emekli aylığı | emekli maaşı, emekli aylığı | Sosyal güvenlik/çalışma hayatı terimidir ('emekli maaşı'); alışveriş kelimesi değildir |
| **postage** | noun (B1) | `22151` | posta ücreti | posta ücreti | Posta gönderim ücretidir ('posta ücreti'); alışveriş kelimesi değildir |
| **scholarship** | noun (B2) | `18725` | burs, öğrenim bursu | burs, öğrenim bursu | Eğitim terimidir ('öğrenci bursu'); okul-egitim kategorisinde zaten vardır, alışveriş kelimesi değildir |
| **toll** | noun (B1) | `11890` | geçiş ücreti, geçiş bedeli | geçiş ücreti, geçiş bedeli | Ulaşım terimidir ('otoyol/köprü geçiş ücreti'); ulasim'da zaten vardır, alışveriş kelimesi değildir |
| **welfare** | noun (B2) | `9813` | refah, esenlik, sosyal yardım | refah, esenlik, sosyal yardım | Siyaset/toplum kavramıdır ('refah, sosyal yardım'); siyaset-toplum'da zaten vardır, alışveriş kelimesi değildir |

### `hava-durumu` — Hava durumu (7 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **changeable** | adjective (B2) | `14273` | değişebilir, değişken | değişebilir, değişken | Genel 'değişken, kararsız' sıfatıdır |
| **extreme** | adjective (B2) | `10032` | aşırı, çok şiddetli | aşırı, çok şiddetli | Genel derece sıfatıdır ('aşırı, uç'); hava durumuna özgü değildir |
| **gloom** | noun (B2) | `5785` | kasvet, karanlık, umutsuzluk | kasvet, karanlık, umutsuzluk | Genel 'karanlık, kasvet, üzüntü' ismidir; doğrudan hava durumu terimi değildir |
| **raincoat** | noun (B1) | `14721` | yağmurluk | yağmurluk | Giysi ismidir ('yağmurluk'); giyim-moda'da zaten vardır, hava olayı değildir |
| **severe** | adjective (B2) | `7396` | ciddi, şiddetli | ciddi, şiddetli | Genel şiddet/ciddiyet sıfatıdır ('şiddetli, ağır, sert'); hava durumuna özgü değildir |
| **umbrella** | noun (A2) | `12781` | şemsiye | şemsiye | Eşya ismidir ('şemsiye'); hava olayı değildir |
| **unpredictable** | adjective (B2) | `3100` | tahmin edilemez, öngörülemez | tahmin edilemez, öngörülemez | Genel 'öngörülemez, tahmin edilemez' sıfatıdır |

### `doga` — Doğa (8 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **beautiful** | adjective (A1) | `14681` | güzel, alımlı | güzel, alımlı | Çok genel A1 sıfatıdır ('güzel'); doğa kategorisine özgü değildir |
| **climb** | verb (A2) | `573` | tırmanmak, yükselmek | tırmanmak, yükselmek | Genel hareket fiilidir ('tırmanmak'); spor/hareket kelimesidir |
| **explore** | verb (B1) | `3918` | keşfetmek, araştırmak | keşfetmek, araştırmak | Genel 'keşfetmek, araştırmak' fiilidir; seyahat ve bilim kategorilerinde zaten vardır |
| **peaceful** | adjective (B1) | `7249` | huzurlu, barışçıl | huzurlu, barışçıl | Genel duygu/ortam sıfatıdır ('huzurlu, sakin'); doğaya özgü değildir |
| **pollution** | noun (B2) | `4478` | kirlilik, çevre kirliliği | kirlilik, çevre kirliliği | Çevre sorunu kavramıdır ('çevre kirliliği'); cevre-iklim kategorisinde zaten vardır |
| **protect** | verb (B1) | `9114` | korumak | korumak | Genel 'korumak, savunmak' fiilidir; doğaya özgü değildir |
| **recycle** | verb (B1) | `8608` | geri dönüştürmek | geri dönüştürmek | Çevre politikası/atık yönetimi fiilidir ('geri dönüştürmek'); cevre-iklim kategorisinde zaten vardır |
| **turf** | noun (B1) | `22525` | çim, çimlik, saha | çim, çimlik, saha | Spor sahası/bahçe çimi ('çim, saha') anlamındadır; vahşi doğa kavramı değildir |

### `hayvanlar` — Hayvanlar (17 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **barn** | noun (B1) | `7710` | ahır, ambar | ahır, ambar | Bina/yapı ismidir ('ahır, samanlık'); hayvan değildir |
| **cage** | noun (A2) | `4393` | kafes | kafes | Eşya/yapı ismidir ('kafes'); hayvan değildir |
| **camouflage** | noun (B2) | `22836` | kamuflaj | kamuflaj | Askeri/genel 'kamuflaj, gizlenme' kavramıdır; hayvan değildir |
| **collar** | noun (B1) | `9446` | hayvan tasması | yaka | Kelimenin A2 1. anlamı 'gömlek yakası'dır; 2. anlamı 'hayvan tasması' yüzünden Animals kartında 'collar · yaka' olarak çıkmaktadır! Hayvan değil, eşyadır |
| **farm** | noun (A2) | `6318` | çiftlik, tarım arazisi | çiftlik, tarım arazisi | Tarım alanı/mekân ismidir ('çiftlik'); hayvan değildir |
| **kennel** | noun (B1) | `25405` | köpek kulübesi | köpek kulübesi | Yapı/kulübe ismidir ('köpek kulübesi'); hayvan değildir |
| **muzzle** | noun (B2) | `24486` | ağızlık | namlu ağzı | Kelimenin 1. anlamı 'silah namlu ağzı'dır; 2. anlamı 'hayvan ağızlığı' yüzünden Animals kartında 'muzzle · namlu ağzı' olarak çıkmaktadır! Hayvan değil, eşyadır |
| **pen** | noun (B1) | `3029` | ağıl, hayvan bölmesi | kalem | Kelimenin A1 1. anlamı 'kalem'dir; 2. anlamı olan 'ağıl, hayvan bölmesi (B2)' yüzünden Animals -> A1 listesinde 'pen · kalem' olarak çıkmaktadır! Hayvan değil, yapı ismidir |
| **poacher** | noun (B2) | `25569` | kaçak avcı | kaçak avcı | Kişi/suçlu ismidir ('kaçak avcı'); hayvan değildir |
| **pride** | noun (B2) | `2923` | aslan sürüsü | onur, gurur | Kelimenin 1. anlamı 'onur, gurur'dur; 2. anlamı olan 'aslan sürüsü' yüzünden Animals kartında 'pride · onur, gurur' olarak çıkmaktadır! Hayvan değil, grup ismidir |
| **saddle** | noun (B1) | `22298` | eyer | eyer | Binicilik ekipmanıdır ('eyer'); hayvan değildir |
| **school** | noun (B2) | `18717` | balık sürüsü | okul, eğitim kurumu | Kelimenin A1 1. anlamı 'okul, eğitim kurumu'dur; 2. anlamı olan 'balık sürüsü (B2)' yüzünden Animals -> A1 listesinde 'school · okul, eğitim kurumu' olarak çıkmaktadır! Hayvan değil, grup ismidir |
| **shelter** | noun (B1) | `5799` | barınak, sığınak | barınak, sığınak | Genel 'barınak, sığınak' ismidir; hayvan değildir |
| **stable** | noun (B1) | `6160` | ahır | ahır | Bina/yapı ismidir ('at ahırı') ve 1. anlamı sıfat olan 'istikrarlı, dengeli'dir; hayvan değildir |
| **vet** | noun (Belirtilmemiş) | `27420` | veteriner | veteriner | Meslek ismidir ('veteriner'); is-meslekler kategorisinde zaten vardır, hayvan değildir |
| **web** | noun (A2) | `17345` | örümcek ağı | ağ | 1. anlamı genel 'ağ, internet ağı'dır; 2. anlamı 'örümcek ağı' yüzünden Animals kartında 'web · ağ' olarak görünmektedir |
| **zoo** | noun (A2) | `12262` | hayvanat bahçesi | hayvanat bahçesi | Mekân ismidir ('hayvanat bahçesi'); sehir-yerler kategorisinde olmalıdır, hayvan değildir |

### `zaman` — Zaman (5 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **agenda** | noun (Belirtilmemiş) | `20510` | gündem | gündem | İş/toplantı terimidir ('toplantı gündemi'); zaman kavramı değildir |
| **diary** | noun (A2) | `6330` | günlük, ajanda | günlük, ajanda | Kişisel defterdir ('hatıra defteri, günlük'); zaman kavramı değildir |
| **extend** | verb (B1) | `19394` | uzatmak, genişletmek | uzatmak, genişletmek | Genel 'uzatmak, genişletmek' fiilidir |
| **itinerary** | noun (B2) | `24355` | seyahat programı, gezi planı | seyahat programı, gezi planı | Seyahat terimidir ('seyahat güzergâhı/programı'); seyahat kategorisinde zaten vardır |
| **planner** | noun (A2) | `15595` | ajanda, planlayıcı | plan yapan kişi, düzenleyici | Kişi ('planlayıcı') veya kırtasiye ('ajanda') ismidir; zaman kavramı değildir |

### `iletisim-medya` — İletişim ve medya (9 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **booth** | noun (B1) | `14641` | stant, kulübe, gişe | stant, kulübe, gişe | Pazar/fuar yapısıdır ('stant, kulübe, gişe'); iletişim ve medya terimi değildir |
| **courier** | noun (B1) | `21505` | kargo taşıyıcısı, kurye | kargo taşıyıcısı, kurye | Taşımacılık/lojistik mesleğidir ('kurye'); medya terimi değildir |
| **deliver** | verb (A2) | `14475` | teslim etmek, ulaştırmak | teslim etmek, ulaştırmak | Taşımacılık/teslimat fiilidir ('teslim etmek, dağıtmak') |
| **nod** | verb (B1) | `1145` | başını sallamak | başını sallamak | Baş hareketidir ('başını sallamak') |
| **package** | noun (A2) | `5027` | paket | paket | Kargo/eşya terimidir ('paket, koli'); medya/iletişim terimi değildir |
| **scream** | verb (B1) | `1392` | çığlık atmak, bağırmak | çığlık atmak, bağırmak | Ses eylemidir ('çığlık atmak') |
| **shout** | verb (A1) | `1448` | bağırmak | bağırmak | Ses eylemidir ('bağırmak') |
| **wave** | verb (A2) | `17840` | el sallamak, el etmek, sallamak | el sallamak, el etmek, sallamak | El hareketidir ('el sallamak'); medya/iletişim terimi olarak zayıftır |
| **wink** | verb (B1) | `8427` | göz kırpmak | göz kırpmak | Göz hareketidir ('göz kırpmak') |

### `teknoloji` — Teknoloji ve internet (13 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **appliance** | noun (B1) | `9725` | ev aleti, cihaz | ev aleti, cihaz | Ev eşyası/beyaz eşyadır ('ev aleti, cihaz'); ev-esyalar'da zaten vardır |
| **browse** | verb (B1) | `14813` | göz atmak, incelemek | göz atmak, incelemek | Mağazada/kitapta 'rastgele göz gezdirmek' olarak tanımlanmıştır; internette gezinmek olarak özelleşmemiştir |
| **engine** | noun (B1) | `16929` | motor, makine | motor, makine | Mekanik araç parçasıdır ('motor - yakıtlı'); ulasim kategorisinde zaten vardır |
| **generator** | noun (B2) | `4469` | jeneratör, üreteç | jeneratör, üreteç | Elektrik üretim makinesidir ('jeneratör, üreteç') |
| **highlight** | verb (B2) | `13069` | vurgulamak, öne çıkarmak | vurgulamak, öne çıkarmak | Genel 'vurgulamak, öne çıkarmak' fiilidir |
| **microscope** | noun (A2) | `14833` | mikroskop | mikroskop | Laboratuvar/bilim aletidir ('mikroskop'); bilim-arastirma'da zaten vardır |
| **motor** | noun (A2) | `8250` | motor, motorlu aygıt | motor, motorlu aygıt | Mekanik araç parçasıdır ('motor'); ulasim kategorisinde zaten vardır |
| **scam** | noun (B2) | `22321` | dolandırıcılık | dolandırıcılık | Suç/dolandırıcılık terimidir ('dolandırıcılık, üçkağıt'); hukuk-suc kategorisinde zaten vardır |
| **select** | verb (B1) | `17805` | seçmek, tercih etmek | seçmek, tercih etmek | Genel 'seçmek, ayırmak' fiilidir |
| **sign up** | phrasal_verb (Belirtilmemiş) | `26692` | kaydolmak, yazılmak | kaydolmak, yazılmak | Kursa/organizasyona 'kaydolmak' olarak tanımlanmıştır; web sitesine üye olmak anlamı değildir |
| **telescope** | noun (A2) | `22478` | teleskop | teleskop | Astronomi/bilim aletidir ('teleskop'); bilim-arastirma'da zaten vardır |
| **turbine** | noun (B2) | `22522` | türbin | türbin | Enerji/mekanik santral parçasıdır ('türbin'); cevre-iklim'de zaten vardır |
| **wire** | noun (A2) | `5541` | tel | tel | Fiziksel metal 'tel'dir; bilişim/internet kavramı değildir |

### `bilim-arastirma` — Bilim ve araştırma (3 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **conference** | noun (A2) | `14057` | toplantı, konferans | toplantı, konferans | İş ve akademik dünyadaki genel 'kongre, konferans' kelimesidir; doğrudan bilim terimi değildir |
| **patent** | noun (B2) | `9623` | patent | patent | Hukuk ve ticaret terimidir ('patent, buluş tescili'); doğrudan temel bilim kavramı değildir |
| **peer** | noun (B1) | `1198` | akran, yaşıt, emsal | akran, yaşıt, emsal | Genel 'akran, yaşıt' kelimesidir; tek başına akademik hakem (peer review) anlamı taşımaz |

### `ekonomi-is-dunyasi` — Ekonomi ve iş dünyası (5 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **global** | adjective (B2) | `3066` | küresel | küresel | Genel 'küresel, dünya çapında' sıfatıdır |
| **international** | adjective (A2) | `15321` | uluslararası, devletlerarası | uluslararası, devletlerarası | Genel 'uluslararası' sıfatıdır |
| **stability** | noun (B2) | `6162` | istikrar, kararlılık | istikrar, kararlılık | Genel fiziksel/durumsal 'denge, istikrar, sağlamlık' kavramıdır |
| **strategy** | noun (B2) | `17349` | strateji, plan | strateji, plan | Genel 'strateji, plan' kelimesidir |
| **target** | noun (B1) | `17026` | hedef | hedef | Genel 'hedef, amaç' kelimesidir |

### `hukuk-suc` — Hukuk ve suç (2 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **id** | noun (A2) | `17871` | kimlik, kimlik belgesi | kimlik, kimlik belgesi | Günlük kimlik belgesidir ('kimlik, ID'); suç veya yargı terimi değildir |
| **identity card** | noun (Belirtilmemiş) | `27361` | kimlik kartı | kimlik kartı | Günlük kimlik belgesidir ('kimlik kartı'); suç veya yargı terimi değildir |

### `siyaset-toplum` — Siyaset ve toplum (2 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **epidemic** | noun (B2) | `11968` | salgın, salgın hastalık | salgın, salgın hastalık | Tıp/sağlık terimidir ('salgın hastalık, epidemi'); saglik kategorisinde zaten vardır |
| **pension** | noun (B1) | `10318` | emekli maaşı, emekli aylığı | emekli maaşı, emekli aylığı | Kişisel finans/emeklilik terimidir ('emekli maaşı') |

### `tarih` — Tarih (14 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **collapse** | noun (B2) | `4316` | çöküş, yıkım, çökme | çöküş, yıkım, çökme | Genel 'çöküş, yıkılma' ismidir |
| **contemporary** | adjective (B2) | `3213` | çağdaş, modern | çağdaş, modern | Genel 'çağdaş, günümüze ait' sıfatıdır |
| **decline** | noun (B2) | `3383` | azalma, düşüş | azalma, düşüş | Genel 'azalma, gerileme, düşüş' ismidir |
| **document** | noun (A2) | `13445` | belge | belge | Genel 'belge, doküman' ismidir |
| **event** | noun (A2) | `15876` | olay | olay | Genel 'olay, etkinlik' ismidir |
| **flourish** | verb (B2) | `8728` | gelişmek, başarılı olmak | gelişmek, başarılı olmak | Genel 'gelişmek, başarılı olmak' fiilidir |
| **migrate** | verb (B2) | `11286` | göç etmek | göç etmek | Coğrafya/toplum/doğa fiilidir ('göç etmek'); siyaset-toplum ve hayvanlar'da zaten vardır |
| **migration** | noun (B2) | `11297` | göç, yer değiştirme | göç, yer değiştirme | Coğrafya/toplum kavramıdır ('göç'); siyaset-toplum'da zaten vardır |
| **modern** | adjective (A1) | `16235` | modern, çağdaş, günümüze ait | modern, çağdaş, günümüze ait | Genel 'modern, çağdaş' sıfatıdır |
| **oral** | adjective (B1) | `14184` | sözlü | sözlü | Genel 'sözlü, ağızla ilgili' sıfatıdır; tek başına 'sözlü tarih' anlamı taşımaz |
| **perish** | verb (B2) | `7376` | ölmek, yok olmak | ölmek, yok olmak | Genel/edebi 'ölmek, yok olmak' fiilidir |
| **record** | noun (B2) | `15791` | kayıt | kayıt | Genel 'kayıt, belge' ismidir |
| **rise** | noun (B1) | `17070` | yükseliş, artış | yükseliş, artış | Genel 'yükseliş, artış' ismidir |
| **thrive** | verb (B2) | `11383` | başarılı olmak, gelişmek | başarılı olmak, gelişmek | Genel 'gelişmek, serpilmek' fiilidir |

### `psikoloji-zihin` — Psikoloji ve zihin (5 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **conform** | verb (B1) | `19233` | uygun davranmak, kurallara uymak | uygun davranmak, kurallara uymak | Toplumsal kurallara 'uymak, ayak uydurmak' fiilidir |
| **incentive** | noun (B2) | `13817` | teşvik | teşvik | Ekonomi ve yönetim kavramıdır ('teşvik, özendirici'); ekonomi-is-dunyasi'nda zaten vardır |
| **obedience** | noun (B2) | `2663` | itaat | itaat | Toplumsal/otorite kavramıdır ('itaat, boyun eğme') |
| **punishment** | noun (B1) | `2636` | ceza | ceza | Hukuk ve disiplin kavramıdır ('ceza'); hukuk-suc kategorisinde zaten vardır |
| **reward** | noun (B2) | `2409` | ödül, mükafat | ödül, mükafat | Genel 'ödül, mükafat' kavramıdır |

### `cevre-iklim` — Çevre ve iklim (11 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **clean up** | phrasal_verb (B1) | `22872` | temizlemek, düzenlemek | temizlemek, düzenlemek | Genel temizlik phrasal verb'üdür ('temizlemek, toplamak'); çevreye özgü değildir |
| **efficiency** | noun (B2) | `5722` | verimlilik, etkinlik | verimlilik, etkinlik | Genel iş/üretim kavramıdır ('verimlilik, etkinlik'); çevreye özgü değildir |
| **efficient** | adjective (B2) | `5721` | verimli, etkili | verimli, etkili | Genel nitelik sıfatıdır ('verimli, etkin'); çevreye özgü değildir |
| **extract** | verb (B1) | `19010` | çıkarmak, çıkartmak | çıkarmak, çıkartmak | Genel 'çekip çıkarmak, özünü çıkarmak' fiilidir |
| **famine** | noun (C1) | `8405` | kıtlık, açlık, kıtlık durumu | kıtlık, açlık, kıtlık durumu | İnsani/toplumsal kriz terimidir ('kıtlık, açlık'); siyaset-toplum'da yer almalıdır |
| **offset** | verb (B2) | `22023` | telafi etmek, dengelemek | telafi etmek, dengelemek | Genel ekonomi/dengeleme fiilidir ('dengelemek, telafi etmek'); tek başına karbon dengeleme anlamı taşımaz |
| **packaging** | noun (B2) | `5030` | paketleme, ambalaj | paketleme, ambalaj | Ticaret/ambalaj terimidir ('paketleme, ambalaj'); doğrudan çevre/iklim kavramı değildir |
| **refine** | verb (B2) | `12357` | iyileştirmek, arıtmak, geliştirmek | iyileştirmek, arıtmak, geliştirmek | Endüstriyel/genel 'arıtmak, saflaştırmak, geliştirmek' fiilidir |
| **switch off** | phrasal_verb (Belirtilmemiş) | `26730` | (cihazı) kapatmak | (cihazı) kapatmak | Genel günlük phrasal verb'dür ('(ışığı/cihazı) kapatmak'); çevre ve iklim kelimesi değildir |
| **throw away** | phrasal_verb (Belirtilmemiş) | `26771` | (çöpe) atmak | (çöpe) atmak | Genel günlük phrasal verb'dür ('çöpe atmak, elden çıkarmak'); çevreye özgü değildir |
| **turn down** | phrasal_verb (Belirtilmemiş) | `26786` | (sesi, ısıyı) kısmak | (teklifi) reddetmek, geri çevirmek | Genel günlük phrasal verb'dür ('(sesi, ısıyı) kısmak'); çevre ve iklim kelimesi değildir |

### `neden-sonuc-degisim` — Neden, sonuç ve değişim (4 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **climb** | verb (A2) | `573` | tırmanmak, yükselmek | tırmanmak, yükselmek | Fiziksel hareket fiilidir ('elleriyle tırmanmak'); değişim kategorisi için zorlamadır |
| **course** | noun (B1) | `20008` | rota, gidişat, akış yönü | kurs, ders | Fiziksel hareket/seyahat yönüdür ('rota, gidiş yönü'); neden-sonuç kavramı değildir |
| **leap** | verb (B1) | `3011` | atlamak, sıçramak | atlamak, sıçramak | Fiziksel hareket fiilidir ('atlamak, sıçramak'); değişim kategorisi için zorlamadır |
| **motivation** | noun (B2) | `4168` | güdü, motivasyon | güdü, motivasyon | Psikoloji kavramıdır ('motivasyon, güdü'); psikoloji-zihin'de zaten vardır |

### `tartisma` — Tartışma ve fikir bildirme (1 kelime)

| Kelime | Tür / CEFR | `meaning_id` | Bağlı Anlam (`meaning_tr`) | Kartta Görünen 1. Anlam | Çıkarılma Gerekçesi |
|---|---|---|---|---|---|
| **dimension** | noun (B2) | `6332` | boyut, yön | boyut, yön | Fiziksel/geometrik 'boyut, ölçü (en, boy, derinlik)' olarak tanımlanmıştır |

## 6. İkincil Anlamıyla Bağlı Olup Kartta Farklı 1. Anlam Gösteren Kelimeler (`IKINCIL_ANLAM_KARTTA_YANILTICI`)

Aşağıdaki kelimeler ilgili kategoriye 2., 3. veya 4. anlamıyla (`sort_order > 0`) bağlıdır. Kategori bağlantısı anlamsal olarak savunulabilir olsa bile, konu sayfasındaki kapalı kartta **1. anlam (`kartta_gorunen_1_anlam`)** ve **kelimenin genel CEFR seviyesi (`kelime_cefr`)** gösterildiği için kullanıcıya yanlış görünmektedir. Konu sayfasında kategoriye bağlı anlamın özete taşınması veya çok yan anlamların çıkarılması önerilir:

| Kategori | Kelime | `meaning_id` | Kelime CEFR / Anlam CEFR | Kategorideki İkincil Anlamı | Kartta Görünen 1. Anlamı |
|---|---|---|---|---|---|
| `duygular` | **alarm** (noun) | `396` | B1 / B1 (2. anlam) | endişe, kaygı duygusu | **alarm** |
| `duygular` | **appreciate** (verb) | `11630` | B1 / B1 (2. anlam) | minnettar olmak, teşekkür etmek | **takdir etmek, değerini bilmek** |
| `duygular` | **bitter** (adjective) | `8018` | B2 / B2 (2. anlam) | kırgın, içerlemiş, küskün | **acı, buruk** |
| `duygular` | **break down** (phrasal_verb) | `26211` | A2 / Belirtilmemiş (2. anlam) | (kendini tutamayıp) ağlamaya başlamak | **bozulmak, arızalanmak** |
| `duygular` | **gloomy** (adjective) | `5788` | B1 / B2 (2. anlam) | kasvetli, karamsar, morali bozuk | **karanlık, loş** |
| `duygular` | **mad** (adjective) | `4493` | B1 / A2 (2. anlam) | kızgın, öfkeli | **deli, çılgın** |
| `duygular` | **miss** (verb) | `15776` | A1 / A1 (2. anlam) | özlemek, hasret duymak | **kaçırmak, yakalayamamak** |
| `duygular` | **moving** (adjective) | `19542` | B2 / B2 (2. anlam) | dokunaklı, duygusal olarak etkileyen | **hareket eden, hareketli** |
| `duygular` | **offense** (noun) | `2963` | B1 / B1 (2. anlam) | alınma, gücenme, kırılma | **suç, yasa dışı eylem** |
| `duygular` | **relief** (noun) | `1973` | B2 / B1 (2. anlam) | rahatlama, hafifleme | **yardım, destek** |
| `duygular` | **satisfy** (verb) | `2183` | B2 / B2 (2. anlam) | memnun etmek, tatmin etmek | **karşılamak, yerine getirmek** |
| `duygular` | **surprise** (noun) | `6215` | A2 / B1 (2. anlam) | şaşkınlık, hayret duygusu | **beklenmedik olay, sürpriz** |
| `duygular` | **tension** (noun) | `5232` | B2 / B1 (2. anlam) | gerginlik, sıkıntı | **gerilim, gerilme** |
| `kisilik-davranis` | **awkward** (adjective) | `7095` | B2 / B2 (2. anlam) | beceriksiz, sakar | **garip, tuhaf, rahatsız, mahcup** |
| `kisilik-davranis` | **bright** (adjective) | `18951` | A2 / A2 (2. anlam) | zeki, akıllı | **parlak, ışık yayan** |
| `kisilik-davranis` | **brilliant** (adjective) | `18961` | A2 / B1 (3. anlam) | zeki, üstün yetenekli | **harika, mükemmel** |
| `kisilik-davranis` | **communicative** (adjective) | `4013` | B1 / B1 (2. anlam) | konuşkan, sosyal | **iletişimsel** |
| `kisilik-davranis` | **flexible** (adjective) | `8315` | B2 / B2 (2. anlam) | uyarlanabilir, değişime açık | **esnek, bükülebilir** |
| `kisilik-davranis` | **innocent** (adjective) | `3423` | B1 / B2 (2. anlam) | naif, saf, deneyimsiz | **masum, suçsuz** |
| `kisilik-davranis` | **manner** (noun) | `7055` | A2 / B1 (2. anlam) | tavır, davranış, görgü (manners) | **yöntem, şekil** |
| `kisilik-davranis` | **nice** (adjective) | `14645` | A1 / A1 (2. anlam) | kibar, nazik | **hoş, güzel** |
| `kisilik-davranis` | **peculiar** (adjective) | `1959` | C1 / B2 (2. anlam) | garip, tuhaf | **kendine özgü, has, özgü** |
| `kisilik-davranis` | **persistent** (adjective) | `5365` | C1 / B1 (2. anlam) | ısrarcı, kararlı, inatçı | **süregelen, geçmeyen, kalıcı, devam eden** |
| `kisilik-davranis` | **responsible** (adjective) | `19888` | B1 / B1 (2. anlam) | sorumluluk sahibi, güvenilir | **sorumlu, hesap verebilir** |
| `kisilik-davranis` | **sharp** (adjective) | `1432` | B1 / B2 (3. anlam) | zeki, akıllı | **keskin, sivri** |
| `kisilik-davranis` | **spoiled** (adjective) | `7151` | B1 / B2 (2. anlam) | şımarık, şımarmış | **bozulmuş, çürümüş** |
| `kisilik-davranis` | **temper** (noun) | `4358` | B1 / B2 (2. anlam) | karakter, mizaç | **öfke, sinir** |
| `kisilik-davranis` | **upright** (adjective) | `6745` | B1 / B2 (2. anlam) | dürüst, ahlaklı | **dikey, dik** |
| `kisilik-davranis` | **willful** (adjective) | `6366` | B2 / B2 (2. anlam) | inatçı, kendi bildiğini okuyan | **kasıtlı, isteyerek yapılan** |
| `gorus-tercih` | **dull** (adjective) | `4726` | B2 / B1 (2. anlam) | sıkıcı, ilgi çekmeyen | **mat, donuk** |
| `gorus-tercih` | **feel** (verb) | `15199` | A1 / B1 (2. anlam) | düşünmek, kanısında olmak | **hissetmek, duyu organlarıyla algılamak** |
| `gorus-tercih` | **outlook** (noun) | `9840` | C1 / B1 (2. anlam) | bakış açısı, perspektif | **gelecek beklentisi, gidişat** |
| `gorus-tercih` | **partial** (adjective) | `1928` | C1 / B2 (2. anlam) | taraflı | **kısmi, eksik** |
| `gorus-tercih` | **taste** (noun) | `17399` | A2 / B1 (2. anlam) | tercih, zevk | **tat, lezzet** |
| `gorunus-beden` | **calf** (noun) | `12416` | A2 / B1 (2. anlam) | baldır, baldır kası | **buzağı, dana** |
| `gorunus-beden` | **dark** (adjective) | `670` | A1 / A2 (2. anlam) | koyu | **karanlık, loş** |
| `gorunus-beden` | **fair** (adjective) | `2577` | A2 / B1 (2. anlam) | açık renkli, sarı, açık tenli | **adil, hakkaniyetli** |
| `gorunus-beden` | **frame** (noun) | `14607` | B1 / B2 (2. anlam) | vücut yapısı, beden, iskelet | **çerçeve** |
| `gorunus-beden` | **gum** (noun) | `12749` | A2 / B2 (2. anlam) | diş eti | **sakız** |
| `gorunus-beden` | **height** (noun) | `18319` | A2 / A2 (2. anlam) | boy | **yükseklik** |
| `gorunus-beden` | **look** (verb) | `9181` | A1 / A1 (2. anlam) | görünmek | **bakmak** |
| `gorunus-beden` | **mole** (noun) | `21060` | B1 / B1 (3. anlam) | ben | **köstebek** |
| `gorunus-beden` | **nail** (noun) | `3862` | B1 / A1 (2. anlam) | tırnak | **çivi** |
| `gorunus-beden` | **pupil** (noun) | `5662` | B2 / B2 (2. anlam) | göz bebeği | **öğrenci** |
| `gorunus-beden` | **sole** (noun) | `5611` | B1 / B1 (2. anlam) | taban, ayak tabanı, ayakkabı tabanı | **dil balığı** |
| `gorunus-beden` | **temple** (noun) | `1571` | B2 / B1 (2. anlam) | şakak | **tapınak** |
| `gorunus-beden` | **tissue** (noun) | `7509` | B2 / C1 (2. anlam) | biyolojik doku, hücre topluluğu | **kağıt mendil, ince kağıt** |
| `aile-iliskiler` | **adopt** (verb) | `3595` | B2 / B2 (2. anlam) | evlat edinmek | **kabul etmek, benimsemek** |
| `aile-iliskiler` | **affair** (noun) | `18184` | B2 / B2 (2. anlam) | ilişki, aşk ilişkisi | **mesele, konu, iş** |
| `aile-iliskiler` | **attachment** (noun) | `18765` | B2 / B2 (2. anlam) | bağlılık, duygusal bağ | **ek, ilişik, bağ** |
| `aile-iliskiler` | **blood** (noun) | `6818` | A2 / B2 (2. anlam) | soy, kan bağı | **kan** |
| `aile-iliskiler` | **conceive** (verb) | `18305` | C1 / B1 (2. anlam) | hamile kalmak, gebe kalmak | **tasarlamak, bir fikir ortaya koymak** |
| `aile-iliskiler` | **engagement** (noun) | `778` | C1 / B2 (2. anlam) | nişan, nişanlılık | **randevu, sözleşme** |
| `aile-iliskiler` | **get on** (phrasal_verb) | `26400` | A2 / Belirtilmemiş (2. anlam) | iyi geçinmek, anlaşmak | **(otobüse, trene) binmek** |
| `aile-iliskiler` | **go out** (phrasal_verb) | `26459` | A2 / Belirtilmemiş (2. anlam) | (biriyle) çıkmak, sevgili olmak | **dışarı çıkmak, eğlenmeye çıkmak** |
| `aile-iliskiler` | **make up** (phrasal_verb) | `26569` | B1 / Belirtilmemiş (3. anlam) | barışmak | **uydurmak** |
| `aile-iliskiler` | **proposal** (noun) | `18673` | B2 / B2 (2. anlam) | evlilik teklifi | **öneri, tasarı** |
| `aile-iliskiler` | **propose** (verb) | `18671` | B2 / B2 (2. anlam) | evlenme teklif etmek, evlilik teklifinde bulunmak | **önermek, teklif etmek** |
| `aile-iliskiler` | **raise** (verb) | `17326` | A2 / B2 (2. anlam) | büyütmek, yetiştirmek | **kaldırmak, yükseltmek, artırmak** |
| `aile-iliskiler` | **spoil** (verb) | `7147` | B2 / B2 (2. anlam) | şımartmak, fazla ilgi göstermek | **bozmak, mahvetmek, bozulmak** |
| `aile-iliskiler` | **tie** (noun) | `2058` | A2 / B1 (2. anlam) | bağ, ilişki | **kravat** |
| `yiyecek-icecek` | **cider** (noun) | `22866` | B1 / B1 (2. anlam) | alkolsüz elma suyu | **alkollü elma şarabı** |
| `yiyecek-icecek` | **clove** (noun) | `5720` | B1 / B2 (2. anlam) | karanfil | **sarımsak dişi** |
| `yiyecek-icecek` | **date** (noun) | `15779` | A1 / B1 (2. anlam) | hurma | **tarih, gün** |
| `yiyecek-icecek` | **diner** (noun) | `10898` | B1 / B1 (2. anlam) | küçük restoran, lokanta | **yemek yiyen kişi, müşteri** |
| `yiyecek-icecek` | **dip** (noun) | `7570` | A2 / A2 (2. anlam) | sos, dip sosu | **çukur, çöküntü, (hafif) düşüş** |
| `yiyecek-icecek` | **hot** (adjective) | `12170` | A1 / B1 (2. anlam) | baharatlı, acı | **sıcak** |
| `yiyecek-icecek` | **live on** (phrasal_verb) | `26534` | B2 / Belirtilmemiş (2. anlam) | (bir yiyecekle) beslenmek | **(bir miktar parayla) geçinmek** |
| `yiyecek-icecek` | **oil** (noun) | `14009` | A2 / A2 (2. anlam) | yemeklik yağ, pişirme yağı | **petrol, ham petrol** |
| `yiyecek-icecek` | **spirit** (noun) | `3982` | B1 / B2 (2. anlam) | sert içki, damıtılmış alkollü içki | **ruh, öz, içsel varlık** |
| `yiyecek-icecek` | **swallow** (noun) | `2076` | B1 / B1 (2. anlam) | yudum, yutma | **kırlangıç** |
| `yiyecek-icecek` | **tasteless** (adjective) | `17409` | B1 / B1 (2. anlam) | tatsız, lezzetsiz | **zevksiz** |
| `yemek-yapma` | **carve** (verb) | `2046` | C1 / B1 (2. anlam) | dilimlemek, doğramak | **oymak, şekil vermek** |
| `yemek-yapma` | **glass** (noun) | `16902` | A1 / A2 (2. anlam) | bardak, kadeh | **cam, şeffaf sert madde** |
| `yemek-yapma` | **mold** (noun) | `11095` | B1 / B2 (2. anlam) | kalıp | **küf** |
| `yemek-yapma` | **pit** (verb) | `3997` | B2 / B2 (2. anlam) | çekirdeğini çıkarmak, içini boşaltmak | **(against ile) karşı karşıya getirmek, yarıştırmak** |
| `yemek-yapma` | **scramble** (verb) | `6278` | B1 / B1 (2. anlam) | karıştırmak, çırpmak | **tırmanmak, zor bir yoldan çıkmak** |
| `yemek-yapma` | **steam** (verb) | `4960` | B1 / B1 (2. anlam) | buharda pişirmek | **buhar çıkarmak, buhar üretmek** |
| `yemek-yapma` | **weigh** (verb) | `18482` | B1 / B1 (2. anlam) | tartmak, ağırlığını ölçmek | **ağırlığında olmak, gelmek** |
| `ev-esyalar` | **chest** (noun) | `564` | B1 / B1 (2. anlam) | sandık, kutu | **göğüs** |
| `ev-esyalar` | **do up** (phrasal_verb) | `26318` | B1 / Belirtilmemiş (2. anlam) | (evi) yenilemek, onarmak | **iliklemek, bağlamak, kapamak** |
| `ev-esyalar` | **fan** (noun) | `14548` | A2 / A2 (2. anlam) | vantilatör, fan, yelpaze | **hayran, taraftar** |
| `ev-esyalar` | **hall** (noun) | `6493` | A2 / A2 (2. anlam) | koridor, geçit | **salon, toplantı salonu, büyük oda** |
| `ev-esyalar` | **install** (verb) | `8657` | B2 / B1 (2. anlam) | kurmak, yerleştirmek | **yüklemek, kurmak** |
| `ev-esyalar` | **iron** (noun) | `17334` | B1 / A2 (2. anlam) | ütü | **demir** |
| `ev-esyalar` | **match** (noun) | `16048` | A1 / A2 (3. anlam) | kibrit, kibrit çubuğu | **maç, karşılaşma, müsabaka** |
| `ev-esyalar` | **sheet** (noun) | `2623` | A2 / A2 (2. anlam) | çarşaf | **yaprak, tabaka, kağıt** |
| `ev-esyalar` | **tile** (noun) | `22495` | A2 / B1 (2. anlam) | fayans, karo | **kiremit** |
| `ev-esyalar` | **vanity** (noun) | `3754` | B1 / B1 (2. anlam) | makyaj masası, banyo tezgahı | **kibir, kendini beğenmişlik, gösteriş** |
| `giyim-moda` | **clog** (noun) | `24037` | B1 / B2 (2. anlam) | takunya | **tıkanıklık, engel** |
| `giyim-moda` | **hang up** (phrasal_verb) | `26483` | B1 / Belirtilmemiş (2. anlam) | (askıya) asmak | **(telefonu) kapatmak** |
| `giyim-moda` | **lace** (noun) | `12371` | A2 / B2 (2. anlam) | dantel | **ayakkabı bağı** |
| `giyim-moda` | **material** (noun) | `14509` | A2 / A2 (2. anlam) | kumaş | **madde** |
| `giyim-moda` | **model** (noun) | `16061` | A1 / A2 (2. anlam) | manken, model | **örnek, örnek kişi, timsal** |
| `giyim-moda` | **runway** (noun) | `22293` | B1 / B2 (2. anlam) | podyum, defile pisti | **pist, uçak pisti** |
| `giyim-moda` | **smart** (adjective) | `16977` | B1 / B1 (2. anlam) | şık, moda, tarz sahibi | **akıllı, zeki** |
| `giyim-moda` | **sole** (noun) | `5611` | B1 / B1 (2. anlam) | taban, ayak tabanı, ayakkabı tabanı | **dil balığı** |
| `giyim-moda` | **trainer** (noun) | `16537` | A2 / A2 (2. anlam) | spor ayakkabısı | **eğitmen, antrenör** |
| `giyim-moda` | **wardrobe** (noun) | `11356` | A2 / B2 (2. anlam) | kostüm koleksiyonu | **gardırop** |
| `giyim-moda` | **wrap up** (phrasal_verb) | `26824` | B2 / Belirtilmemiş (2. anlam) | sıkı giyinmek | **(paket) sarmak** |
| `saglik` | **cast** (noun) | `17116` | B2 / B2 (2. anlam) | alçı | **oyuncu kadrosu** |
| `saglik` | **come round** (phrasal_verb) | `26285` | B2 / Belirtilmemiş (2. anlam) | kendine gelmek, ayılmak | **fikrini değiştirip kabul etmek, ikna olmak** |
| `saglik` | **drug** (noun) | `16794` | A2 / B1 (2. anlam) | ilaç, tıbbi madde | **uyuşturucu, yasa dışı madde** |
| `saglik` | **faint** (adjective) | `830` | B1 / B2 (2. anlam) | bayılacak gibi, halsiz, başı dönen | **zayıf, hafif, belirsiz** |
| `saglik` | **mortality** (noun) | `1869` | B2 / C1 (2. anlam) | ölüm oranı | **ölümlülük** |
| `saglik` | **operate** (verb) | `19410` | B2 / C1 (2. anlam) | ameliyat etmek | **çalıştırmak, işletmek** |
| `saglik` | **sterile** (adjective) | `23709` | B2 / C1 (2. anlam) | steril | **kısır, üreme yeteneği olmayan** |
| `saglik` | **stroke** (noun) | `3858` | B2 / B2 (2. anlam) | inme, felç | **vuruş, darbe, kulaç** |
| `saglik` | **temperature** (noun) | `17764` | A2 / B1 (2. anlam) | ateş | **sıcaklık, derece** |
| `saglik` | **terminal** (adjective) | `19458` | C1 / C1 (2. anlam) | ölümcül, ölüm getiren | **son, nihai** |
| `saglik` | **treat** (verb) | `20149` | B1 / B2 (2. anlam) | tedavi etmek, iyileştirmek | **davranmak, muamelede bulunmak** |
| `saglik` | **warm up** (phrasal_verb) | `26808` | B1 / Belirtilmemiş (2. anlam) | (spordan önce) ısınma hareketi yapmak | **ısınmak, ısıtmak** |
| `okul-egitim` | **accent** (noun) | `8518` | B2 / B1 (2. anlam) | vurgu, hece vurgusu | **aksan, şive** |
| `okul-egitim` | **binder** (noun) | `18923` | B1 / B1 (2. anlam) | dosya, klasör | **bağlayıcı, yapıştırıcı** |
| `okul-egitim` | **composition** (noun) | `18396` | C1 / B1 (2. anlam) | kompozisyon, beste, yapıt | **bileşim, yapı** |
| `okul-egitim` | **fraction** (noun) | `11941` | B2 / B1 (100. anlam) | kesir | **küçük bir parça** |
| `okul-egitim` | **junior** (noun) | `9573` | B1 / B1 (2. anlam) | üçüncü sınıf öğrencisi | **kıdemsiz kişi, ast, daha genç kişi** |
| `okul-egitim` | **mark** (noun) | `1824` | A2 / B1 (2. anlam) | puan, not | **işaret, damga** |
| `okul-egitim` | **medicine** (noun) | `20211` | A2 / B1 (2. anlam) | tıp bilimi, tıbbi uygulama | **ilaç, tedavi edici madde** |
| `okul-egitim` | **operation** (noun) | `19416` | B1 / C1 (3. anlam) | matematiksel işlem, aritmetik işlem | **cerrahi müdahale, ameliyat** |
| `okul-egitim` | **outline** (noun) | `4983` | B2 / B2 (2. anlam) | taslak, özet | **dış hat, silüet** |
| `okul-egitim` | **paper** (noun) | `16232` | A1 / C1 (3. anlam) | makale, bildiri | **kağıt** |
| `okul-egitim` | **period** (noun) | `12583` | A1 / A2 (2. anlam) | nokta | **zaman aralığı, dönem** |
| `okul-egitim` | **train** (verb) | `16533` | A2 / A2 (2. anlam) | birini eğitmek | **antrenman yapmak** |
| `okul-egitim` | **work out** (phrasal_verb) | `26820` | A2 / Belirtilmemiş (2. anlam) | (sonunda) anlamak, çözmek | **spor yapmak, antrenman yapmak** |
| `is-meslekler` | **anchor** (noun) | `6721` | C1 / B2 (2. anlam) | haber spikeri, sunucu | **çapa, çıpa, demir** |
| `is-meslekler` | **application** (noun) | `9730` | B1 / B1 (2. anlam) | başvuru, müracaat | **uygulama, program** |
| `is-meslekler` | **appointment** (noun) | `7827` | B1 / B2 (2. anlam) | görev, atama | **randevu, görüşme** |
| `is-meslekler` | **benefit** (noun) | `9121` | A2 / B1 (2. anlam) | ödenek, yardım parası, yan hak | **fayda, yarar, kazanç** |
| `is-meslekler` | **board** (noun) | `15709` | A2 / B2 (2. anlam) | yönetim kurulu | **tahta, levha** |
| `is-meslekler` | **branch** (noun) | `17980` | B1 / B1 (2. anlam) | şube | **dal** |
| `is-meslekler` | **client** (noun) | `14603` | B1 / B2 (2. anlam) | danışan, müvekkil | **müşteri, alıcı** |
| `is-meslekler` | **craft** (noun) | `2090` | B2 / B2 (2. anlam) | beceri, el sanatları, zanaat | **araç, gemi, tekne** |
| `is-meslekler` | **dismiss** (verb) | `6099` | B2 / B2 (2. anlam) | işten çıkarmak, görevden almak | **reddetmek, göz ardı etmek** |
| `is-meslekler` | **fill in** (phrasal_verb) | `26356` | A2 / Belirtilmemiş (3. anlam) | (birinin) yerine bakmak, vekâlet etmek | **(formu, boşluğu) doldurmak** |
| `is-meslekler` | **fire** (verb) | `7994` | B1 / B1 (2. anlam) | işten çıkarmak, kovmak | **ateş etmek, ateşlemek** |
| `is-meslekler` | **interview** (noun) | `16848` | A1 / B2 (2. anlam) | mülakat, değerlendirme görüşmesi | **görüşme, röportaj** |
| `is-meslekler` | **model** (noun) | `16061` | A1 / A2 (2. anlam) | manken, model | **örnek, örnek kişi, timsal** |
| `is-meslekler` | **partner** (noun) | `11608` | A1 / B2 (2. anlam) | iş ortağı | **eş, hayat arkadaşı** |
| `is-meslekler` | **producer** (noun) | `19326` | B1 / B1 (2. anlam) | yapımcı | **üretici** |
| `is-meslekler` | **promote** (verb) | `10059` | B1 / B1 (2. anlam) | terfi ettirmek, yükseltmek | **teşvik etmek, desteklemek** |
| `is-meslekler` | **remote** (adjective) | `3632` | B1 / B2 (2. anlam) | uzaktan, uzaktan yapılan, uzaktan erişimli | **uzak, ücra, ıssız** |
| `is-meslekler` | **run** (verb) | `15356` | A1 / B2 (2. anlam) | yürütmek, işletmek | **koşmak** |
| `is-meslekler` | **shift** (noun) | `18037` | B1 / A2 (2. anlam) | vardiya, nöbet | **değişim, kayma** |
| `is-meslekler` | **take on** (phrasal_verb) | `26746` | B2 / Belirtilmemiş (2. anlam) | işe almak | **(iş, sorumluluk) üstlenmek** |
| `is-meslekler` | **title** (noun) | `19911` | A1 / B1 (2. anlam) | unvan, makam | **başlık** |
| `is-meslekler` | **trade** (noun) | `16086` | B1 / B2 (2. anlam) | meslek, zanaat, uğraş | **ticaret, alışveriş** |
| `is-meslekler` | **union** (noun) | `20118` | B1 / B2 (2. anlam) | sendika, işçi birliği | **birlik, birleşme** |
| `sanat-eglence` | **animation** (noun) | `10913` | B2 / B1 (2. anlam) | çizgi film, hareketli görüntü | **animasyon** |
| `sanat-eglence` | **craft** (noun) | `2090` | B2 / B2 (2. anlam) | beceri, el sanatları, zanaat | **araç, gemi, tekne** |
| `sanat-eglence` | **design** (noun) | `13378` | A1 / A2 (2. anlam) | tasarım, desen, görünüm | **tasarım, plan** |
| `sanat-eglence` | **dub** (verb) | `20684` | C1 / Belirtilmemiş (2. anlam) | dublaj yapmak | **lakap takmak, … diye adlandırmak** |
| `sanat-eglence` | **focus** (verb) | `16419` | A2 / B2 (2. anlam) | odaklamak, netlemek | **odaklanmak, konsantre olmak** |
| `sanat-eglence` | **instrument** (noun) | `986` | A2 / A2 (2. anlam) | müzik aleti | **araç, alet** |
| `sanat-eglence` | **key** (noun) | `20091` | A1 / B1 (2. anlam) | ton | **anahtar** |
| `sanat-eglence` | **keyboard** (noun) | `20094` | B1 / A2 (2. anlam) | org, elektronik klavye | **klavye** |
| `sanat-eglence` | **landscape** (noun) | `18382` | B2 / B2 (2. anlam) | manzara resmi, peyzaj tablosu | **manzara, doğa görünümü** |
| `sanat-eglence` | **note** (noun) | `12714` | A1 / B1 (2. anlam) | müzik notası, ses | **kısa yazılı kayıt, not** |
| `sanat-eglence` | **organ** (noun) | `18600` | B2 / B1 (3. anlam) | org, klavye çalgısı | **vücut organı, iç organ** |
| `sanat-eglence` | **paint** (verb) | `2775` | A1 / A1 (2. anlam) | resim yapmak, sanat eseri üretmek | **boyamak, renk vermek** |
| `sanat-eglence` | **part** (noun) | `1926` | A1 / A2 (2. anlam) | rol, görev, karakter | **parça, bölüm, kısım** |
| `sanat-eglence` | **perform** (verb) | `15930` | A2 / A2 (2. anlam) | sahnelemek, icra etmek, gösteri yapmak | **gerçekleştirmek, yerine getirmek** |
| `sanat-eglence` | **pitch** (noun) | `2317` | B2 / B1 (3. anlam) | perde, ses perdesi, ton | **saha** |
| `sanat-eglence` | **put on** (phrasal_verb) | `26631` | A2 / Belirtilmemiş (4. anlam) | (gösteri) sahnelemek, düzenlemek | **giymek, takmak** |
| `sanat-eglence` | **record** (noun) | `15790` | A2 / B1 (3. anlam) | plak | **kayıt** |
| `sanat-eglence` | **score** (noun) | `16970` | A2 / B2 (2. anlam) | müzik parçası, film müziği | **puan, skor** |
| `sanat-eglence` | **show** (noun) | `15186` | A1 / B1 (2. anlam) | sergi, sergileme | **program, televizyon yayını** |
| `sanat-eglence` | **show** (noun) | `15187` | A1 / A1 (3. anlam) | performans, sahne gösterisi | **program, televizyon yayını** |
| `sanat-eglence` | **speaker** (noun) | `11152` | A2 / A2 (2. anlam) | hoparlör, ses çıkaran aygıt | **konuşmacı, konuşan kişi** |
| `sanat-eglence` | **star** (noun) | `12569` | A1 / B1 (2. anlam) | ünlü kişi, yıldız | **yıldız** |
| `sanat-eglence` | **theme** (noun) | `17830` | B1 / C1 (2. anlam) | müzikal tema, melodi | **konu, ana fikir** |
| `sanat-eglence` | **track** (noun) | `16361` | A2 / B1 (2. anlam) | şarkı, parça | **yol, iz, patika** |
| `sanat-eglence` | **zoom** (verb) | `7439` | B1 / B2 (2. anlam) | (in ile) yakınlaştırmak, büyütmek | **hızla geçmek, hızla ilerlemek, fırlamak** |
| `spor` | **arena** (noun) | `13054` | C1 / B2 (2. anlam) | arena, kapalı spor salonu | **alan, meydan** |
| `spor` | **bat** (noun) | `19066` | B2 / A2 (2. anlam) | sopa, beyzbol sopası | **yarasa** |
| `spor` | **beat** (verb) | `6831` | A2 / B1 (2. anlam) | yenmek, mağlup etmek | **vurmak, dövmek** |
| `spor` | **coach** (noun) | `16529` | A2 / A2 (2. anlam) | antrenör, koç | **şehirlerarası otobüs, tur otobüsü** |
| `spor` | **court** (noun) | `20026` | B1 / B1 (2. anlam) | spor sahası, oyun alanı | **mahkeme, yargı yeri** |
| `spor` | **cup** (noun) | `16111` | A1 / B1 (2. anlam) | kupa | **bardak, fincan** |
| `spor` | **equalize** (verb) | `800` | B1 / B1 (2. anlam) | beraberliği sağlamak, skoru eşitlemek | **eşitlemek, eşit hale getirmek** |
| `spor` | **fencing** (noun) | `9611` | B1 / B2 (2. anlam) | eskrim, kılıç sporu | **çit, çit malzemesi** |
| `spor` | **foul** (verb) | `7881` | B2 / B2 (2. anlam) | kural ihlali yapmak, faul yapmak | **kirletmek, pisletmek** |
| `spor` | **header** (noun) | `21799` | B1 / B2 (2. anlam) | kafa vuruşu | **başlık, üst bilgi** |
| `spor` | **judge** (noun) | `18402` | B1 / B1 (2. anlam) | jüri üyesi, hakem | **hâkim, yargıç** |
| `spor` | **knock out** (phrasal_verb) | `26514` | B2 / Belirtilmemiş (2. anlam) | (yarışmadan) elemek | **bayıltmak, nakavt etmek** |
| `spor` | **lap** (noun) | `6545` | C1 / B1 (2. anlam) | tur, çevrim | **kucak** |
| `spor` | **pace** (noun) | `1172` | B2 / B2 (2. anlam) | hız, tempo | **adım, yürüyüş hızı** |
| `spor` | **point** (noun) | `15269` | A1 / B1 (2. anlam) | puan | **nokta** |
| `spor` | **record** (noun) | `15792` | A2 / B2 (2. anlam) | rekor | **kayıt** |
| `spor` | **relay** (noun) | `22245` | B1 / B1 (2. anlam) | bayrak yarışı | **röle** |
| `spor` | **rod** (noun) | `9294` | C1 / B1 (2. anlam) | olta, olta kamışı | **çubuk** |
| `spor` | **sporty** (adjective) | `26146` | B1 / B2 (2. anlam) | spor tarzı, sportif | **spora düşkün, sporsever** |
| `spor` | **tackle** (verb) | `6200` | B2 / B1 (2. anlam) | düşürmek, topa müdahale etmek | **ele almak, çözmek** |
| `spor` | **tie** (noun) | `2060` | A2 / B2 (3. anlam) | beraberlik, eşitlik | **kravat** |
| `spor` | **training** (noun) | `16541` | A2 / A2 (2. anlam) | egzersiz, spor antrenmanı | **eğitim, öğretim** |
| `spor` | **whistle** (noun) | `4028` | A2 / A2 (2. anlam) | düdük | **ıslık** |
| `bos-zaman` | **chill** (verb) | `5403` | B1 / B2 (2. anlam) | rahatlamak, dinlenmek | **soğutmak, serinletmek** |
| `bos-zaman` | **craft** (noun) | `2090` | B2 / B2 (2. anlam) | beceri, el sanatları, zanaat | **araç, gemi, tekne** |
| `bos-zaman` | **diversion** (noun) | `10727` | B1 / B2 (2. anlam) | eğlence, oyalanma, dikkat dağıtma | **yol değişikliği, alternatif yol** |
| `bos-zaman` | **entertain** (verb) | `6105` | B1 / B1 (2. anlam) | misafir ağırlamak, ikramda bulunmak | **eğlendirmek, hoşnut etmek** |
| `bos-zaman` | **pool** (noun) | `17623` | A1 / B1 (3. anlam) | bilardo, bilardo oyunu | **havuz** |
| `bos-zaman` | **walk** (noun) | `16191` | A1 / B1 (2. anlam) | gezinti | **yürüyüş** |
| `seyahat` | **camper** (noun) | `8211` | B1 / B2 (2. anlam) | karavan | **kamp yapan kişi** |
| `seyahat` | **declare** (verb) | `18223` | B2 / B2 (2. anlam) | gümrükte beyan etmek | **ilan etmek, duyurmak** |
| `seyahat` | **get away** (phrasal_verb) | `26378` | B1 / Belirtilmemiş (2. anlam) | (tatile) gitmek, uzaklaşmak | **kaçmak, kurtulmak** |
| `seyahat` | **hire** (verb) | `7841` | B1 / A2 (2. anlam) | kiralamak | **işe almak, istihdam etmek** |
| `seyahat` | **immigration** (noun) | `11293` | B2 / B2 (2. anlam) | pasaport kontrolü | **göç** |
| `seyahat` | **steward** (noun) | `10710` | B1 / B1 (2. anlam) | uçuş görevlisi, kabin memuru | **kâhya, yönetici, sorumlu kişi** |
| `seyahat` | **take off** (phrasal_verb) | `24825` | A2 / B1 (2. anlam) | havalanmak, kalkmak | **kıyafet çıkarmak, soyunmak** |
| `seyahat` | **view** (noun) | `8999` | A2 / A2 (2. anlam) | manzara, görünüm | **görüş, düşünce** |
| `ulasim` | **accelerator** (noun) | `5292` | B1 / B1 (2. anlam) | gaz pedalı | **hızlandırıcı, ivmelendirici** |
| `ulasim` | **bonnet** (noun) | `23978` | B2 / B2 (2. anlam) | kaput, motorlu taşıtın ön kapağı | **kadın başlığı, bebek başlığı** |
| `ulasim` | **boot** (noun) | `478` | A1 / B1 (2. anlam) | bagaj | **çizme, bot** |
| `ulasim` | **conductor** (noun) | `14735` | B2 / B2 (3. anlam) | kondüktör, biletçi | **orkestra şefi** |
| `ulasim` | **cycle** (noun) | `8601` | A2 / A2 (2. anlam) | bisiklet | **döngü, devir, periyot** |
| `ulasim` | **depot** (noun) | `21569` | B1 / B2 (2. anlam) | garaj, araç deposu, terminal | **depo, saklama yeri** |
| `ulasim` | **embark** (verb) | `9718` | C1 / B1 (2. anlam) | binmek, gemiye binmek, uçağa binmek | **(on ile) (bir işe/yolculuğa) başlamak, girişmek** |
| `ulasim` | **fly** (verb) | `2717` | A1 / A2 (2. anlam) | uçakla seyahat etmek | **uçmak** |
| `ulasim` | **garage** (noun) | `20473` | B1 / Belirtilmemiş (2. anlam) | tamirhane, oto servis | **garaj** |
| `ulasim` | **gas** (noun) | `16406` | A2 / A2 (2. anlam) | benzin | **gaz** |
| `ulasim` | **get out** (phrasal_verb) | `26404` | B1 / Belirtilmemiş (2. anlam) | (arabadan) inmek | **dışarı çıkmak, kaçmak** |
| `ulasim` | **hood** (noun) | `8955` | A2 / B1 (2. anlam) | kaput | **kapüşon** |
| `ulasim` | **horn** (noun) | `2881` | C1 / A2 (2. anlam) | araç kornası | **hayvan boynuzu** |
| `ulasim` | **lane** (noun) | `18024` | B2 / B1 (2. anlam) | şerit, yol şeridi | **dar yol, patika, sokak** |
| `ulasim` | **pull out** (phrasal_verb) | `26608` | B2 / Belirtilmemiş (2. anlam) | (araç) yola çıkmak, şerit değiştirmek | **(anlaşmadan, yarıştan) çekilmek** |
| `ulasim` | **reverse** (noun) | `3270` | C1 / B2 (2. anlam) | geri vites; geriye gidiş, tersine dönüş | **ters, aksi** |
| `ulasim` | **take off** (phrasal_verb) | `24825` | A2 / B1 (2. anlam) | havalanmak, kalkmak | **kıyafet çıkarmak, soyunmak** |
| `ulasim` | **track** (noun) | `16359` | A2 / B1 (3. anlam) | ray, demir yolu | **yol, iz, patika** |
| `ulasim` | **trailer** (noun) | `20820` | C1 / Belirtilmemiş (2. anlam) | römork | **fragman** |
| `ulasim` | **trolley** (noun) | `23783` | A2 / B2 (2. anlam) | tramvay | **alışveriş arabası, bagaj arabası, servis arabası** |
| `ulasim` | **walk** (noun) | `16191` | A1 / B1 (2. anlam) | gezinti | **yürüyüş** |
| `sehir-yerler` | **arcade** (noun) | `21266` | B1 / B2 (2. anlam) | kapalı alışveriş pasajı | **oyun salonu** |
| `sehir-yerler` | **arena** (noun) | `13054` | C1 / B2 (2. anlam) | arena, kapalı spor salonu | **alan, meydan** |
| `sehir-yerler` | **block** (noun) | `16746` | B1 / B1 (2. anlam) | blok, ada, iki sokak arası | **küp, blok, parça** |
| `sehir-yerler` | **busy** (adjective) | `14155` | A1 / B1 (2. anlam) | yoğun, hareketli | **meşgul, bir işi/planı olan** |
| `sehir-yerler` | **diner** (noun) | `10898` | B1 / B1 (2. anlam) | küçük restoran, lokanta | **yemek yiyen kişi, müşteri** |
| `sehir-yerler` | **plant** (noun) | `16717` | A1 / B2 (2. anlam) | fabrika, tesis | **bitki** |
| `sehir-yerler` | **quarter** (noun) | `17457` | A1 / B2 (3. anlam) | semt, mahalle, bölge | **çeyrek, dörtte bir** |
| `sehir-yerler` | **salon** (noun) | `12786` | B1 / B1 (2. anlam) | kuaför salonu, güzellik salonu | **salon, büyük oturma odası** |
| `sehir-yerler` | **square** (noun) | `16925` | A2 / B1 (2. anlam) | şehir meydanı, açık alan | **kare** |
| `alisveris-para` | **allowance** (noun) | `16404` | C1 / A2 (2. anlam) | harçlık, ödenek | **hak, pay, limit** |
| `alisveris-para` | **balance** (noun) | `17280` | B1 / B1 (2. anlam) | bakiye, kalan tutar | **denge, istikrar** |
| `alisveris-para` | **change** (noun) | `14269` | A1 / A2 (2. anlam) | bozuk para, para üstü | **değişim, dönüşüm** |
| `alisveris-para` | **check** (noun) | `15559` | A2 / A2 (3. anlam) | çek | **denetim, inceleme** |
| `alisveris-para` | **interest** (noun) | `15901` | A1 / B2 (2. anlam) | faiz, getiri | **ilgi, merak** |
| `alisveris-para` | **line** (noun) | `11640` | A1 / B1 (2. anlam) | kuyruk, sıra | **çizgi, hat** |
| `alisveris-para` | **loss** (noun) | `20124` | B1 / B1 (2. anlam) | zarar | **kayıp** |
| `alisveris-para` | **note** (noun) | `12715` | A1 / A2 (3. anlam) | kağıt para, banknot | **kısa yazılı kayıt, not** |
| `alisveris-para` | **order** (noun) | `1739` | A1 / A2 (3. anlam) | sipariş, talep edilen ürün | **düzen, sıra, düzenleme** |
| `alisveris-para` | **promotion** (noun) | `10063` | B2 / B1 (2. anlam) | tanıtım, reklam kampanyası | **terfi, yükselme** |
| `alisveris-para` | **property** (noun) | `16105` | B1 / B1 (2. anlam) | mülk, mülkiyet | **özellik, nitelik** |
| `alisveris-para` | **quarter** (noun) | `17456` | A1 / A2 (2. anlam) | yirmi beş sentlik, çeyrek dolar | **çeyrek, dörtte bir** |
| `alisveris-para` | **reasonable** (adjective) | `11031` | B2 / B1 (2. anlam) | makul, uygun fiyatlı | **mantıklı, akla yatkın** |
| `alisveris-para` | **return** (verb) | `15844` | A1 / B1 (2. anlam) | geri vermek, iade etmek | **geri dönmek, tekrar gelmek** |
| `alisveris-para` | **used** (adjective) | `18510` | B1 / B1 (2. anlam) | kullanılmış | **(to ile) alışkın, alışmış** |
| `alisveris-para` | **withdrawal** (noun) | `5650` | C1 / B1 (2. anlam) | para çekme | **geri çekilme, çekilme** |
| `hava-durumu` | **bolt** (noun) | `1983` | B1 / B1 (2. anlam) | yıldırım | **sürgü** |
| `hava-durumu` | **brisk** (adjective) | `9801` | B1 / B2 (2. anlam) | serin, soğuk | **canlı, enerjik** |
| `hava-durumu` | **clear up** (phrasal_verb) | `26258` | B1 / Belirtilmemiş (2. anlam) | (hava) açılmak | **toplamak, ortalığı derlemek** |
| `hava-durumu` | **fair** (adjective) | `2578` | A2 / B1 (3. anlam) | açık, güzel, elverişli | **adil, hakkaniyetli** |
| `hava-durumu` | **mild** (adjective) | `4636` | B1 / B2 (2. anlam) | ılıman, hafif, az şiddetli | **hafif, yumuşak** |
| `hava-durumu` | **shower** (noun) | `12642` | A1 / B1 (2. anlam) | sağanak | **duş** |
| `doga` | **bank** (noun) | `15921` | A1 / B1 (2. anlam) | kıyı, nehir kıyısı, kenar | **banka, finans kurumu** |
| `doga` | **bark** (noun) | `4992` | A2 / B1 (2. anlam) | ağaç kabuğu | **havlama sesi** |
| `doga` | **bud** (noun) | `10552` | B1 / B1 (2. anlam) | tomurcuk, çiçek tomurcuğu | **dost, ahbap** |
| `doga` | **cape** (noun) | `4133` | B1 / B1 (2. anlam) | burun | **pelerin** |
| `doga` | **channel** (noun) | `16883` | B1 / B2 (2. anlam) | kanal, su yolu, boğaz | **televizyon kanalı, yayın kanalı** |
| `doga` | **earth** (noun) | `4428` | A2 / B1 (2. anlam) | toprak, yer | **dünya, gezegen** |
| `doga` | **palm** (noun) | `4818` | B2 / B1 (2. anlam) | palmiye ağacı | **avuç içi, elin iç kısmı** |
| `doga` | **space** (noun) | `20066` | A1 / A2 (2. anlam) | uzay | **alan, boşluk, yer** |
| `doga` | **spring** (noun) | `4944` | A1 / B1 (2. anlam) | kaynak | **bahar** |
| `doga` | **trunk** (noun) | `2141` | B1 / B1 (3. anlam) | ağaç gövdesi | **fil hortumu** |
| `doga` | **wood** (noun) | `17142` | A2 / B1 (2. anlam) | ormanlık alan | **ahşap, tahta, odun** |
| `hayvanlar` | **cricket** (noun) | `20937` | A2 / B1 (2. anlam) | cırcır böceği | **kriket** |
| `hayvanlar` | **lay** (verb) | `2849` | B1 / B1 (2. anlam) | yumurta bırakmak, yumurtlamak | **yerleştirmek, koymak** |
| `hayvanlar` | **pouch** (noun) | `12910` | B1 / B2 (2. anlam) | kese | **küçük çanta, torba** |
| `hayvanlar` | **ray** (noun) | `17551` | C1 / B1 (2. anlam) | vatoz | **ışın, ışık ışını** |
| `hayvanlar` | **tick** (noun) | `9900` | B1 / B1 (2. anlam) | kene | **tık sesi, tıkırtı** |
| `zaman` | **latter** (adjective) | `18098` | C1 / B2 (2. anlam) | son, sonraki | **ikinci, bahsedilen ikincisi** |
| `zaman` | **present** (noun) | `2948` | A1 / A2 (2. anlam) | şimdiki zaman, şu an, günümüz | **hediye** |
| `zaman` | **shift** (noun) | `18037` | B1 / A2 (2. anlam) | vardiya, nöbet | **değişim, kayma** |
| `zaman` | **span** (noun) | `6718` | C1 / B2 (2. anlam) | zaman dilimi, süre | **uzunluk, mesafe** |
| `zaman` | **stage** (noun) | `16136` | A2 / B2 (2. anlam) | aşama, evre | **sahne** |
| `iletisim-medya` | **anchor** (noun) | `6721` | C1 / B2 (2. anlam) | haber spikeri, sunucu | **çapa, çıpa, demir** |
| `iletisim-medya` | **bring up** (phrasal_verb) | `26843` | B1 / Belirtilmemiş (2. anlam) | (konuyu) açmak, gündeme getirmek | **(çocuk) yetiştirmek, büyütmek** |
| `iletisim-medya` | **circulation** (noun) | `19521` | C1 / B1 (2. anlam) | tiraj, yayın dağıtımı | **kan dolaşımı** |
| `iletisim-medya` | **column** (noun) | `597` | A2 / B2 (2. anlam) | yazı köşesi, köşe yazısı | **sütun, dikey destek** |
| `iletisim-medya` | **convey** (verb) | `5506` | B2 / B2 (2. anlam) | iletmek, aktarmak | **taşımak, nakletmek** |
| `iletisim-medya` | **feed** (noun) | `5319` | B2 / B1 (2. anlam) | akış (haber, sosyal medya) | **yem, hayvan yemi** |
| `iletisim-medya` | **interpret** (verb) | `4666` | B2 / B2 (2. anlam) | çevirmenlik yapmak, sözlü çeviri yapmak | **açıklamak, yorumlamak** |
| `iletisim-medya` | **issue** (noun) | `15725` | B1 / B2 (2. anlam) | yayın, sayı | **konu, mesele** |
| `iletisim-medya` | **letter** (noun) | `16559` | A1 / A2 (2. anlam) | mektup, yazılı iletişim | **harf, alfabe karakteri** |
| `iletisim-medya` | **paper** (noun) | `16230` | A1 / A2 (2. anlam) | gazete | **kağıt** |
| `iletisim-medya` | **post** (noun) | `10532` | A1 / B1 (2. anlam) | gönderi, paylaşım | **posta, mektup gönderimi** |
| `iletisim-medya` | **receiver** (noun) | `12677` | B2 / B2 (2. anlam) | ahize | **alıcı** |
| `iletisim-medya` | **scoop** (noun) | `12007` | B1 / B2 (2. anlam) | özel haber, atlatma haber | **kepçe, dondurma kaşığı, derin kaşık** |
| `iletisim-medya` | **sensational** (adjective) | `18348` | B2 / C1 (2. anlam) | skandal yaratıcı, sansasyonel | **olağanüstü, çarpıcı** |
| `teknoloji` | **account** (noun) | `10841` | B1 / A2 (3. anlam) | kullanıcı hesabı, profil | **hesap, banka hesabı, mali kayıt** |
| `teknoloji` | **back up** (phrasal_verb) | `25959` | B1 / B2 (2. anlam) | kopyasını almak, yedeklemek | **desteklemek, yardım etmek** |
| `teknoloji` | **backup** (noun) | `18297` | C1 / B2 (2. anlam) | yedek kopya, veri yedeklemesi | **destek, takviye** |
| `teknoloji` | **bug** (noun) | `12244` | B2 / B2 (2. anlam) | yazılım hatası | **böcek** |
| `teknoloji` | **charge** (verb) | `16347` | B1 / B1 (2. anlam) | şarj etmek | **ücret almak, fiyat istemek** |
| `teknoloji` | **code** (noun) | `19670` | A2 / B1 (3. anlam) | kod, program kodu | **şifre, gizli işaret** |
| `teknoloji` | **cookie** (noun) | `13809` | A2 / B2 (2. anlam) | çerez | **kurabiye, bisküvi** |
| `teknoloji` | **cord** (noun) | `7125` | B1 / B1 (2. anlam) | elektrik kablosu | **halat, ip** |
| `teknoloji` | **crash** (noun) | `18144` | B2 / B2 (2. anlam) | çöküş, (sistem) çökme, (borsada) ani düşüş | **çarpışma, kaza** |
| `teknoloji` | **display** (noun) | `17788` | B2 / B2 (2. anlam) | ekran, gösterge paneli | **sergi, sergileme, gösteri** |
| `teknoloji` | **link** (noun) | `16487` | A2 / A2 (2. anlam) | bağlantı, link, köprü | **bağlantı, ilişki** |
| `teknoloji` | **memory** (noun) | `20193` | A2 / B2 (2. anlam) | bellek, hafıza | **hafıza, bellek, anı** |
| `teknoloji` | **mouse** (noun) | `5937` | A1 / A1 (2. anlam) | bilgisayar faresi | **fare** |
| `teknoloji` | **navigation** (noun) | `14781` | B2 / B1 (2. anlam) | navigasyon | **yön bulma, seyir** |
| `teknoloji` | **platform** (noun) | `17611` | A2 / B2 (2. anlam) | yazılım ortamı, platform | **yükseltilmiş zemin, platform** |
| `teknoloji` | **port** (noun) | `19554` | B1 / B2 (2. anlam) | giriş, port, bağlantı noktası | **liman, iskele** |
| `teknoloji` | **script** (noun) | `19608` | B1 / C1 (2. anlam) | betik, komut dosyası | **senaryo, metin** |
| `teknoloji` | **signal** (noun) | `20248` | B1 / B2 (2. anlam) | elektronik sinyal | **işaret, belirti** |
| `teknoloji` | **speaker** (noun) | `11152` | A2 / A2 (2. anlam) | hoparlör, ses çıkaran aygıt | **konuşmacı, konuşan kişi** |
| `teknoloji` | **tab** (noun) | `19746` | A2 / A2 (2. anlam) | sekme | **hesap, fatura** |
| `teknoloji` | **tablet** (noun) | `6847` | A2 / B1 (2. anlam) | tablet, tablet bilgisayar | **hap** |
| `teknoloji` | **undo** (verb) | `12869` | B1 / B2 (2. anlam) | geri almak, etkisini ortadan kaldırmak | **çözmek, açmak** |
| `teknoloji` | **virus** (noun) | `6929` | A2 / B1 (2. anlam) | bilgisayar virüsü | **virüs** |
| `bilim-arastirma` | **conductor** (noun) | `14734` | B2 / C1 (2. anlam) | iletken | **orkestra şefi** |
| `bilim-arastirma` | **crust** (noun) | `7014` | B1 / C1 (2. anlam) | yer kabuğu | **kabuk, ekmek kabuğu** |
| `bilim-arastirma` | **field** (noun) | `15698` | A2 / B2 (2. anlam) | alan, disiplin | **tarla, arazi** |
| `bilim-arastirma` | **figure** (noun) | `13005` | A2 / A2 (3. anlam) | sayı, rakam | **şekil, form** |
| `bilim-arastirma` | **friction** (noun) | `20985` | B2 / B2 (2. anlam) | sürtünme, direnç | **sürtüşme, anlaşmazlık, gerginlik** |
| `bilim-arastirma` | **journal** (noun) | `9100` | B1 / B2 (2. anlam) | akademik dergi, bilimsel yayın | **günlük, kişisel defter** |
| `bilim-arastirma` | **mass** (noun) | `16775` | B2 / B1 (3. anlam) | kütle | **büyük miktar, çokluk** |
| `bilim-arastirma` | **matter** (noun) | `14518` | A2 / B1 (2. anlam) | madde | **konu, mesele** |
| `bilim-arastirma` | **plasma** (noun) | `22122` | B2 / C1 (2. anlam) | plazma, iyonlaşmış gaz | **kan plazması** |
| `bilim-arastirma` | **react** (verb) | `18459` | A2 / C1 (2. anlam) | kimyasal reaksiyona girmek, etkileşime girmek | **tepki vermek, tepki göstermek** |
| `bilim-arastirma` | **reaction** (noun) | `18462` | B1 / B1 (2. anlam) | kimyasal reaksiyon | **tepki** |
| `bilim-arastirma` | **replicate** (verb) | `21136` | B2 / C1 (2. anlam) | tekrarlamak, yeniden üretmek | **kopyasını oluşturmak, çoğaltmak** |
| `bilim-arastirma` | **rigorous** (adjective) | `22281` | B2 / B2 (2. anlam) | titiz, ayrıntılı, sıkı | **katı, sıkı, kurallara bağlı** |
| `bilim-arastirma` | **scale** (noun) | `19438` | B2 / B2 (2. anlam) | ölçek, ölçekteki değer aralığı | **terazi, tartı, baskül** |
| `bilim-arastirma` | **significant** (adjective) | `6314` | B2 / C1 (2. anlam) | istatistiksel olarak anlamlı | **önemli, kayda değer** |
| `bilim-arastirma` | **solution** (noun) | `1485` | A2 / B2 (2. anlam) | çözelti | **çözüm, yanıt** |
| `bilim-arastirma` | **study** (noun) | `20054` | A1 / A2 (2. anlam) | araştırma, inceleme | **öğrenim, ders çalışma** |
| `bilim-arastirma` | **test** (noun) | `9635` | A1 / A2 (2. anlam) | deneme, deney | **sınav, değerlendirme** |
| `bilim-arastirma` | **tissue** (noun) | `7509` | B2 / C1 (2. anlam) | biyolojik doku, hücre topluluğu | **kağıt mendil, ince kağıt** |
| `bilim-arastirma` | **valid** (adjective) | `9673` | B2 / C1 (2. anlam) | mantıklı, akla yatkın, tutarlı | **geçerli** |
| `bilim-arastirma` | **volume** (noun) | `17288` | B2 / B1 (2. anlam) | miktar, hacim | **ses şiddeti** |
| `ekonomi-is-dunyasi` | **board** (noun) | `15709` | A2 / B2 (2. anlam) | yönetim kurulu | **tahta, levha** |
| `ekonomi-is-dunyasi` | **bond** (noun) | `17931` | B2 / B2 (2. anlam) | tahvil, bono | **bağ, ilişki, bağlanma** |
| `ekonomi-is-dunyasi` | **branch** (noun) | `17980` | B1 / B1 (2. anlam) | şube | **dal** |
| `ekonomi-is-dunyasi` | **capital** (noun) | `10992` | A1 / B2 (2. anlam) | sermaye | **başkent** |
| `ekonomi-is-dunyasi` | **compensate** (verb) | `11004` | C1 / C1 (2. anlam) | tazmin etmek, ödeme yapmak | **telafi etmek, dengelemek** |
| `ekonomi-is-dunyasi` | **competition** (noun) | `6935` | A2 / B1 (2. anlam) | rekabet, kıyasıya mücadele | **yarışma, müsabaka** |
| `ekonomi-is-dunyasi` | **depression** (noun) | `18364` | B2 / B1 (2. anlam) | ekonomik bunalım, buhran | **depresyon** |
| `ekonomi-is-dunyasi` | **enterprise** (noun) | `20694` | C1 / Belirtilmemiş (2. anlam) | girişimcilik, atılganlık | **kuruluş, şirket, işletme** |
| `ekonomi-is-dunyasi` | **gross** (adjective) | `13374` | C1 / C1 (2. anlam) | brüt, toplam | **iğrenç, tiksindirici** |
| `ekonomi-is-dunyasi` | **index** (noun) | `18042` | B2 / B2 (2. anlam) | endeks, gösterge | **dizin, liste** |
| `ekonomi-is-dunyasi` | **interest** (noun) | `15901` | A1 / B2 (2. anlam) | faiz, getiri | **ilgi, merak** |
| `ekonomi-is-dunyasi` | **liability** (noun) | `7137` | B2 / B2 (2. anlam) | borç, mali yükümlülük | **hukuki sorumluluk** |
| `ekonomi-is-dunyasi` | **loss** (noun) | `20124` | B1 / B1 (2. anlam) | zarar | **kayıp** |
| `ekonomi-is-dunyasi` | **market** (noun) | `15598` | A1 / B2 (2. anlam) | piyasa, finansal piyasa | **pazar, alışveriş yeri** |
| `ekonomi-is-dunyasi` | **mint** (noun) | `21975` | A2 / B2 (2. anlam) | para basım yeri, darphane | **nane, nane bitkisi** |
| `ekonomi-is-dunyasi` | **partner** (noun) | `11608` | A1 / B2 (2. anlam) | iş ortağı | **eş, hayat arkadaşı** |
| `ekonomi-is-dunyasi` | **plant** (noun) | `16717` | A1 / B2 (2. anlam) | fabrika, tesis | **bitki** |
| `ekonomi-is-dunyasi` | **portfolio** (noun) | `20769` | C1 / Belirtilmemiş (2. anlam) | yatırım portföyü | **portfolyo, dosya (çalışmalar)** |
| `ekonomi-is-dunyasi` | **regulation** (noun) | `18632` | B2 / B1 (2. anlam) | düzenleme, kontrol | **kural, yönetmelik** |
| `ekonomi-is-dunyasi` | **return** (noun) | `15841` | A1 / B2 (2. anlam) | getiri, kazanç | **geri dönüş, dönüş** |
| `ekonomi-is-dunyasi` | **royalty** (noun) | `16895` | B2 / C1 (2. anlam) | telif ücreti, telif hakkı geliri | **kraliyet mensubu, kraliyet ailesi** |
| `ekonomi-is-dunyasi` | **speculate** (verb) | `5490` | B2 / C1 (2. anlam) | spekülasyon yapmak, riskli yatırım yapmak | **tahmin etmek, varsaymak** |
| `ekonomi-is-dunyasi` | **statement** (noun) | `19257` | A1 / B2 (2. anlam) | mali rapor, finansal tablo | **beyan, açıklama** |
| `hukuk-suc` | **appeal** (noun) | `17625` | B2 / C1 (3. anlam) | temyiz, itiraz | **çekicilik, cazibe** |
| `hukuk-suc` | **breach** (verb) | `11628` | C1 / B2 (2. anlam) | ihlal etmek, kuralları çiğnemek | **yarmak, delik açmak** |
| `hukuk-suc` | **break** (verb) | `11700` | A1 / B2 (3. anlam) | ihlâl etmek, kuralları çiğnemek | **parçalamak, kırmak** |
| `hukuk-suc` | **case** (noun) | `15263` | A2 / B1 (3. anlam) | hukuki dava | **durum, vaka** |
| `hukuk-suc` | **cell** (noun) | `14696` | B2 / B1 (2. anlam) | hapis hücresi | **hücre** |
| `hukuk-suc` | **charge** (verb) | `18238` | B1 / B2 (100. anlam) | suçlamak, itham etmek | **ücret almak, fiyat istemek** |
| `hukuk-suc` | **clause** (noun) | `20462` | B1 / Belirtilmemiş (2. anlam) | madde, hüküm (sözleşmede) | **yan cümle, cümlecik** |
| `hukuk-suc` | **code** (noun) | `19669` | A2 / B2 (2. anlam) | yasa, kanun bütünü | **şifre, gizli işaret** |
| `hukuk-suc` | **conviction** (noun) | `642` | C1 / C1 (2. anlam) | mahkumiyet, hüküm | **inanç, kanaat** |
| `hukuk-suc` | **counsel** (noun) | `6399` | B2 / C1 (2. anlam) | avukat, dava vekili | **tavsiye, danışmanlık** |
| `hukuk-suc` | **custody** (noun) | `20665` | C1 / Belirtilmemiş (2. anlam) | gözaltı, tutukluluk | **velayet** |
| `hukuk-suc` | **deed** (noun) | `7928` | C1 / B2 (2. anlam) | senet, tapu | **iş, eylem, davranış** |
| `hukuk-suc` | **execute** (verb) | `7854` | C1 / C1 (2. anlam) | infaz etmek, idam etmek | **uygulamak, yerine getirmek** |
| `hukuk-suc` | **guilty** (adjective) | `6329` | B1 / B2 (2. anlam) | suçlu, suç işleyen | **suçluluk hisseden** |
| `hukuk-suc` | **hearing** (noun) | `9537` | B2 / B2 (2. anlam) | mahkeme duruşması, dinleme | **duyma, işitme** |
| `hukuk-suc` | **judgment** (noun) | `18407` | B2 / B2 (2. anlam) | hukuki karar, mahkeme kararı | **kişisel görüş, kanaat** |
| `hukuk-suc` | **launder** (verb) | `23315` | B1 / C1 (2. anlam) | kara para aklamak | **yıkamak, temizlemek** |
| `hukuk-suc` | **overturn** (verb) | `13285` | C1 / C1 (2. anlam) | (kararı) bozmak, iptal etmek | **devirmek, tersine çevirmek** |
| `hukuk-suc` | **sentence** (noun) | `17999` | A1 / B2 (2. anlam) | hüküm, ceza | **cümle** |
| `hukuk-suc` | **slaughter** (noun) | `10986` | B1 / C1 (2. anlam) | katliam, toplu öldürme | **kesim, boğazlama** |
| `hukuk-suc` | **trial** (noun) | `16822` | B2 / B2 (2. anlam) | dava, duruşma, yargılama | **deneme, test** |
| `hukuk-suc` | **will** (noun) | `6356` | B1 / B1 (3. anlam) | vasiyetname | **irade, kararlılık** |
| `siyaset-toplum` | **class** (noun) | `13583` | A1 / B1 (3. anlam) | sınıf, toplumsal katman | **ders, ders saati** |
| `siyaset-toplum` | **demonstrate** (verb) | `4609` | B2 / B2 (2. anlam) | protesto etmek, gösteri yapmak | **göstermek, açıklamak** |
| `siyaset-toplum` | **demonstrator** (noun) | `4618` | B1 / B2 (2. anlam) | gösterici, eylemci | **tanıtımcı, ürün tanıtıcısı** |
| `siyaset-toplum` | **department** (noun) | `3690` | A2 / B1 (2. anlam) | bakanlık, daire | **bölüm** |
| `siyaset-toplum` | **foundation** (noun) | `3782` | B2 / B1 (2. anlam) | vakıf, kurum | **temel, alt yapı** |
| `siyaset-toplum` | **march** (noun) | `15644` | A1 / B2 (2. anlam) | yürüyüş, protesto yürüyüşü | **yürüyüş, protesto yürüyüşü** |
| `siyaset-toplum` | **party** (noun) | `15368` | A1 / A2 (2. anlam) | parti, siyasi parti | **parti, eğlence, davet** |
| `siyaset-toplum` | **race** (noun) | `16203` | A2 / B2 (2. anlam) | etnik grup, ırk | **yarış, rekabet** |
| `siyaset-toplum` | **state** (noun) | `19248` | A2 / B1 (2. anlam) | devlet | **durum, hal** |
| `tarih` | **age** (noun) | `15555` | A1 / B2 (2. anlam) | dönem, çağ | **yaş** |
| `tarih` | **campaign** (noun) | `16434` | B1 / C1 (2. anlam) | sefer, askeri harekat | **kampanya** |
| `tarih` | **landmark** (noun) | `20724` | C1 / Belirtilmemiş (2. anlam) | dönüm noktası | **simge yapı, tanınmış yer** |
| `tarih` | **mummy** (noun) | `12048` | A2 / B2 (2. anlam) | mumya | **anne** |
| `tarih` | **nobility** (noun) | `1142` | B1 / B1 (2. anlam) | soylular, aristokrasi | **asalet, yücelik, asil davranış** |
| `tarih` | **ruler** (noun) | `1364` | A2 / B2 (2. anlam) | hükümdar, lider | **cetvel, ölçü aleti** |
| `tarih` | **settlement** (noun) | `1411` | C1 / B1 (2. anlam) | yerleşim, topluluk | **anlaşma, uzlaşma** |
| `tarih` | **slaughter** (noun) | `10986` | B1 / C1 (2. anlam) | katliam, toplu öldürme | **kesim, boğazlama** |
| `tarih` | **tablet** (noun) | `6848` | A2 / B2 (3. anlam) | tablet, yazıt, kitabe | **hap** |
| `psikoloji-zihin` | **brain** (noun) | `16584` | A2 / B2 (2. anlam) | zihin | **beyin** |
| `psikoloji-zihin` | **breakdown** (noun) | `11707` | C1 / B2 (2. anlam) | sinir krizi, psikolojik çöküş, bunalım | **arızalanma, bozulma** |
| `psikoloji-zihin` | **isolation** (noun) | `6073` | C1 / B1 (2. anlam) | yalnızlık, tek başına kalma | **izolasyon, soyutlanma, tecrit** |
| `psikoloji-zihin` | **outlook** (noun) | `9840` | C1 / B1 (2. anlam) | bakış açısı, perspektif | **gelecek beklentisi, gidişat** |
| `psikoloji-zihin` | **reason** (noun) | `11027` | A1 / C1 (2. anlam) | akıl, mantık | **gerekçe, sebep** |
| `psikoloji-zihin` | **reflect** (verb) | `1306` | B1 / B2 (2. anlam) | düşünmek, gözden geçirmek | **yansıtmak, geri yansıtmak** |
| `psikoloji-zihin` | **resolve** (verb) | `2451` | B2 / B2 (2. anlam) | karar vermek | **çözmek** |
| `psikoloji-zihin` | **response** (noun) | `1339` | A2 / B2 (2. anlam) | tepki, reaksiyon | **yanıt, cevap** |
| `psikoloji-zihin` | **withdrawal** (noun) | `5651` | C1 / B2 (3. anlam) | yoksunluk, kriz, çekilme | **geri çekilme, çekilme** |
| `cevre-iklim` | **green** (adjective) | `14501` | A1 / B2 (2. anlam) | çevre dostu, ekolojik | **yeşil** |
| `cevre-iklim` | **grid** (noun) | `9833` | C1 / B2 (2. anlam) | elektrik şebekesi | **ızgara, kareli desen** |
| `cevre-iklim` | **litter** (noun) | `13896` | B2 / B1 (2. anlam) | çöp, atık, dağınık nesneler | **bir batında doğan yavrular** |
| `cevre-iklim` | **power** (noun) | `10818` | A2 / B1 (2. anlam) | enerji, güç | **güç, yetki, otorite, hâkimiyet** |
| `cevre-iklim` | **reserve** (noun) | `9456` | B2 / B2 (2. anlam) | koruma alanı, doğal rezerv | **yedek, ayrılmış miktar** |
| `neden-sonuc-degisim` | **allow** (verb) | `16401` | A2 / B2 (2. anlam) | mümkün kılmak, yol açmak | **izin vermek, müsaade etmek** |
| `neden-sonuc-degisim` | **cut down** (phrasal_verb) | `26302` | B1 / Belirtilmemiş (2. anlam) | azaltmak | **(ağaç) kesmek** |
| `neden-sonuc-degisim` | **degree** (noun) | `16595` | A2 / B2 (2. anlam) | seviye, derece, ölçü | **üniversite derecesi, diploma** |
| `neden-sonuc-degisim` | **dramatic** (adjective) | `3974` | B2 / B1 (2. anlam) | çarpıcı, etkileyici, ani | **dramatik, tiyatroyla ilgili** |
| `neden-sonuc-degisim` | **dramatically** (adverb) | `3976` | B2 / C1 (2. anlam) | büyük ölçüde, çarpıcı biçimde | **dramatik bir şekilde** |
| `neden-sonuc-degisim` | **drop** (noun) | `11213` | B1 / A2 (2. anlam) | düşüş, azalma | **damla** |
| `neden-sonuc-degisim` | **encourage** (verb) | `766` | B1 / B2 (2. anlam) | teşvik etmek, yönlendirmek | **desteklemek, cesaret vermek** |
| `neden-sonuc-degisim` | **fall** (noun) | `18804` | A2 / B1 (2. anlam) | düşme, düşüş | **sonbahar** |
| `neden-sonuc-degisim` | **govern** (verb) | `3361` | B2 / C1 (2. anlam) | düzenlemek, yönlendirmek | **yönetmek, idare etmek** |
| `neden-sonuc-degisim` | **involve** (verb) | `2007` | A2 / B2 (2. anlam) | içermek, kapsamak | **dahil etmek, karıştırmak** |
| `neden-sonuc-degisim` | **modest** (adjective) | `11789` | B2 / B2 (2. anlam) | mütevazı, ufak, sınırlı | **mütevazı, alçakgönüllü** |
| `neden-sonuc-degisim` | **mount** (verb) | `1120` | B2 / B2 (2. anlam) | artmak, çoğalmak | **binmek, çıkmak, tırmanmak** |
| `neden-sonuc-degisim` | **origin** (noun) | `2981` | B2 / B1 (2. anlam) | başlangıç, doğuş | **köken, kaynak** |
| `neden-sonuc-degisim` | **pace** (noun) | `1172` | B2 / B2 (2. anlam) | hız, tempo | **adım, yürüyüş hızı** |
| `neden-sonuc-degisim` | **plunge** (verb) | `3578` | C1 / B2 (2. anlam) | hızla düşmek, çakılmak, dibe vurmak | **suya dalmak, atlamak** |
| `neden-sonuc-degisim` | **radical** (adjective) | `10301` | C1 / C1 (2. anlam) | temel, köklü | **aşırı, radikal** |
| `neden-sonuc-degisim` | **revise** (verb) | `20491` | B1 / Belirtilmemiş (2. anlam) | gözden geçirmek, düzeltmek | **(sınava) tekrar etmek, çalışmak** |
| `neden-sonuc-degisim` | **root** (noun) | `2160` | B2 / B1 (2. anlam) | kaynak, köken | **kök, kök organı** |
| `neden-sonuc-degisim` | **scale** (noun) | `19438` | B2 / B2 (2. anlam) | ölçek, ölçekteki değer aralığı | **terazi, tartı, baskül** |
| `neden-sonuc-degisim` | **set off** (phrasal_verb) | `26675` | B1 / Belirtilmemiş (3. anlam) | tetiklemek, başlatmak | **yola çıkmak** |
| `neden-sonuc-degisim` | **sharp** (adjective) | `1430` | B1 / B1 (2. anlam) | ani, sert | **keskin, sivri** |
| `neden-sonuc-degisim` | **since** (conjunction) | `15155` | A2 / B2 (2. anlam) | çünkü | **...'den beri** |
| `neden-sonuc-degisim` | **stage** (noun) | `16136` | A2 / B2 (2. anlam) | aşama, evre | **sahne** |
| `neden-sonuc-degisim` | **sustain** (verb) | `6581` | C1 / B2 (2. anlam) | sürdürmek, devam ettirmek | **hasar görmek, maruz kalmak** |
| `tartisma` | **agreement** (noun) | `8393` | B1 / B1 (2. anlam) | uyum, mutabakat | **anlaşma, sözleşme, antlaşma** |
| `tartisma` | **bring up** (phrasal_verb) | `26843` | B1 / Belirtilmemiş (2. anlam) | (konuyu) açmak, gündeme getirmek | **(çocuk) yetiştirmek, büyütmek** |
| `tartisma` | **compromise** (verb) | `9113` | C1 / B2 (2. anlam) | uzlaşmak, ödün vermek | **tehlikeye atmak, zedelemek** |
| `tartisma` | **conclude** (verb) | `615` | B1 / B1 (2. anlam) | sonuç çıkarmak, hüküm vermek | **sonuçlandırmak, bitirmek** |
| `tartisma` | **contention** (noun) | `10675` | C1 / C1 (2. anlam) | iddia, savunma | **tartışma, anlaşmazlık** |
| `tartisma` | **expand** (verb) | `4112` | B1 / B2 (2. anlam) | açıklamak, ayrıntılandırmak | **genişlemek, büyümek, genişletmek, büyütmek** |
| `tartisma` | **implication** (noun) | `2080` | B2 / B1 (2. anlam) | ima, örtük anlam | **olası sonuç, etki** |
| `tartisma` | **maintain** (verb) | `12209` | B2 / B2 (3. anlam) | iddia etmek, savunmak | **sürdürmek, devam ettirmek** |
| `tartisma` | **parallel** (noun) | `5616` | B2 / C1 (2. anlam) | eş, emsal, benzerlik | **enlem çizgisi** |
| `tartisma` | **point** (noun) | `15270` | A1 / B1 (3. anlam) | ana fikir, konu, mesele | **nokta** |
| `tartisma` | **presumption** (noun) | `8713` | B2 / C1 (2. anlam) | varsayım, tahmin | **küstahlık, hadsizlik** |
| `tartisma` | **row** (noun) | `17883` | A2 / B1 (2. anlam) | tartışma, kavga | **sıra, diziliş** |
| `tartisma` | **state** (verb) | `19250` | B1 / B2 (2. anlam) | belirtmek, tanımlamak | **ifade etmek, söylemek** |
| `tartisma` | **tension** (noun) | `5232` | B2 / B1 (2. anlam) | gerginlik, sıkıntı | **gerilim, gerilme** |
| `tartisma` | **valid** (adjective) | `9673` | B2 / C1 (2. anlam) | mantıklı, akla yatkın, tutarlı | **geçerli** |
| `tartisma` | **while** (conjunction) | `14690` | A2 / B2 (2. anlam) | oysa, -e rağmen | **-iken, ... sırasında, ... süresince** |
