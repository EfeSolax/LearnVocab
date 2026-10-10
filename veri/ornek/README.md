# Boş havuzlara 5'er örnek (rapor 18.14)

Havuzlar boş görünmesin diye Claude'un **elle** yazdığı örnekler (API yok).
Hepsi `kaynak` alanında "örnek" diye işaretli; gerçek havuz gelince silinip
yerine gerçek veri yüklenir.

| Dosya | Havuz | Yükleme |
|---|---|---|
| `d2_baglac.jsonl` | D2 bağlaç/ifade cümleleri | `manage.py baglac_havuzu_yukle veri/ornek/d2_baglac.jsonl` |
| `d3_esdizim.jsonl` | D3 eş dizim çeldiricileri | `manage.py esdizim_celdiricileri --yukle veri/ornek/d3_esdizim.jsonl` |
| `d5_kutuphane.jsonl` | D5 okuma kütüphanesi | `manage.py kutuphane_yukle veri/ornek/d5_kutuphane.jsonl` |
| `d6_diyalog.jsonl` | D6 diyaloglar | `manage.py diyalog_yukle veri/ornek/d6_diyalog.jsonl` |
| `d7_akademik_fiiller.txt` | D7 hazır liste (10 Ekim'de kaldırıldı; Bilkent listeleri geldi) | `manage.py hazir_liste_yukle veri/ornek/d7_akademik_fiiller.txt --ad "Örnek liste: Akademik fiiller" --slug ornek-akademik-fiiller --aciklama "…"` |

D4 (seviye testi özet soruları) tam havuz olarak yazıldı: `seviye/havuz/`.
