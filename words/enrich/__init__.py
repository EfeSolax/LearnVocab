"""
Toplu kelime zenginleştirme hattı.

Akış tek yönlü ve her adımı ayrı dosyada:

    context.py  DB'ye bakar   -> "bu kelime/aile hakkında elimizde ne var?"
    prompt.py   metni kurar   -> modele ne soracağımız
    schema.py   şekli kurar   -> modelin döndürmek ZORUNDA olduğu yapı
    checks.py   denetler      -> modelin döndürdüğü şey kabul edilebilir mi
    writer.py   yazar         -> yalnızca denetimden geçen veri DB'ye girer

Modelin veritabanına erişimi YOKTUR ve olmamalıdır. Sorguyu kod atar, cevabı
koda verir; model yalnızca dil üretir. Bunun üç sebebi var: ucuz (tek tur),
tekrarlanabilir (aynı girdi aynı çıktı), ve denetlenebilir (uydurma bir
lookup diye bir şey olamaz).
"""
