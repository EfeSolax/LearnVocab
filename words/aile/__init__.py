"""
Aile hattı — kelime verisinin üç aşamalı üretimi.

Eski hat (words/enrich) her seferinde TEK kelime alıyor, kökünü buluyor ve
yalnızca o kelimeyi dolduruyordu; aile kelimeler geldikçe parça parça
kuruluyordu. Sessiz bozulmaların çoğu buradan çıkıyordu: türev tabandan
önce gelince aile ikiye bölünüyor, kök sonradan taşınmak zorunda kalıyordu.

Yeni hat aileyi ÖNCE ve BÜTÜN olarak kuruyor, anlamı SONRA dolduruyor:

    1. ÜRETİM       manage.py aile_uret       listedeki her kelime için model
                                              ailenin tamamını çıkarır
                                              (yalnızca kelime + tür)
    2. BİRLEŞTİRME  manage.py aile_birlestir  farklı kelimelerden gelen
                                              taslaklar tek aileye iner;
                                              örtüşmeyenler RAPORLANIR
    3. ANLAM        manage.py aile_doldur     birleşmiş ailelerin her
                                              kelimesine anlam doldurulur ve
                                              aile VERİTABANINA yazılır

İlk iki aşama veritabanına HİÇ yazmaz. Çıktıları ara depoda durur
(ara-depo/, bkz. depo.py): bozulan bir aşama veritabanını kirletmez ve
istenildiği kadar tekrar çalıştırılabilir. Veritabanına yalnızca 3.
aşama yazacak — anlamı olmayan yarım kelime sitede hiç görünmesin diye.

Modülün dosyaları:

    schema.py     modelin döndürmek ZORUNDA olduğu yapı (kelime + tür)
    denetim.py    modelin cevabını ölçer, onarır, çekimleri ekler
    depo.py       ara depo: taslaklar, kararlar, birleşmiş aileler
    birlestir.py  taslakları aileye indiren saf fonksiyonlar
    deneme.py     modelin kalitesini ölçen beklentili deneme listeleri
    anlam.py      3. aşamanın şeması, denetimi ve veritabanı yazıcısı

Kural aynı: KOD SORAR, MODEL YAZAR, KOD DENETLER. Modelin tek işi kelimeyi
ve türünü yazmak; çekimler (inflect.cekimler), varlık denetimi (wordfreq)
ve birleştirme kodun işi.
"""
