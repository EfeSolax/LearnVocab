"""
İfadelerin bilinirliği (rapor 18.8): "yaygın bilinen" / "az bilinen".

Günün İfadesi yalnızca AZ BİLİNEN ifadelerden seçilir: "but", "because",
"however" gibi herkesin bildiği bağlaçlar günün ifadesi olarak bir şey
öğretmez. İşaretleme elle yapıldı (Claude, 30 Eylül 2026; API yok):

  - A1 ve A2 ifadelerin hepsi yaygın.
  - B1 ve B2'de aşağıdaki listedekiler yaygın, gerisi az bilinen.
  - C1 ve C2'nin hepsi az bilinen.

Yeni ifade eklenince varsayılan "az bilinen"dir; yaygınsa buraya eklenir ve
`manage.py ifade_bilinirligi` çalıştırılır.
"""

YAYGIN = "yaygin"
AZ = "az"

HEP_YAYGIN_SEVIYELER = ("A1", "A2")

YAYGIN_IFADELER = frozenset({
    # --- B1 ---
    "according to", "afterwards", "although", "apart from", "apparently", "as",
    "as a result", "as long as", "as well as", "at the same time", "besides",
    "by the time", "certainly", "clearly", "compared to", "currently", "despite",
    "due to", "even if", "even though", "eventually", "except for", "firstly",
    "for instance", "from now on", "generally", "however", "in addition",
    "in case", "in conclusion", "in fact", "in general", "in my view",
    "in order to", "in particular", "in short", "in spite of", "in time",
    "including", "instead", "lastly", "neither … nor", "not only … but also",
    "obviously", "on the other hand", "once", "otherwise", "overall",
    "particularly", "personally", "possibly", "rather than", "secondly", "since",
    "so that", "still", "such as", "thanks to", "that is why", "therefore",
    "though", "unless", "unlike", "whenever", "while", "yet",
    # --- B2 ---
    "additionally", "consequently", "e.g.", "equally", "furthermore", "i.e.",
    "importantly", "in contrast", "in summary", "indeed", "initially",
    "meanwhile", "moreover", "nevertheless", "only if", "previously", "rather",
    "regarding", "significantly", "similarly", "specifically", "thus",
    "typically", "ultimately", "undoubtedly", "whereas",
})


def bilinirlik(metin, cefr):
    if cefr in HEP_YAYGIN_SEVIYELER or (metin or "").lower() in YAYGIN_IFADELER:
        return YAYGIN
    return AZ
