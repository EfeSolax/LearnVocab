"""docx'ten paragraf metni ve kalın parçalar (hedef kelimeler kalın yazılıyor)."""
import sys, zipfile, json
from xml.etree import ElementTree as ET
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
def kalin(r):
    rpr = r.find(W + "rPr")
    if rpr is None: return False
    b = rpr.find(W + "b")
    return b is not None and b.get(W + "val") not in ("0", "false")
def alti_cizili(r):
    rpr = r.find(W + "rPr")
    if rpr is None: return False
    u = rpr.find(W + "u")
    return u is not None and u.get(W + "val") not in ("none", "0", None)
def paragraflar(yol):
    govde = ET.fromstring(zipfile.ZipFile(yol).read("word/document.xml")).find(W + "body")
    out = []
    for p in govde.iter(W + "p"):
        parca, kal, aktif, alt, aaktif = [], [], "", [], ""
        for r in p.iter(W + "r"):
            t = "".join(x.text or "" for x in r.findall(W + "t"))
            if not t: continue
            parca.append(t)
            if alti_cizili(r) and kalin(r): aaktif += t
            elif aaktif and t.strip() in ("", "-"): aaktif += t
            else:
                if aaktif.strip(): alt.append(aaktif.strip())
                aaktif = ""
            if kalin(r): aktif += t
            elif aktif and t.strip() in ("", "-"): aktif += t      # kalınların arasındaki boşluk ya da tire
            else:
                if aktif.strip(): kal.append(aktif.strip())
                aktif = ""
        if aktif.strip(): kal.append(aktif.strip())
        if aaktif.strip(): alt.append(aaktif.strip())
        m = "".join(parca).strip()
        if m: out.append({"t": m, "b": kal, "u": alt})
    return out
if __name__ == "__main__":
    json.dump(paragraflar(sys.argv[1]), open(sys.argv[2], "w"), ensure_ascii=False)
