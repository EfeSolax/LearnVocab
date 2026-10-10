"""docx: paragraf metni, kalın parçalar, altı çizili parçalar (ayrı ayrı)."""
import sys, zipfile, json
from xml.etree import ElementTree as ET
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
def ozellik(r, ad):
    rpr = r.find(W + "rPr")
    if rpr is None: return False
    e = rpr.find(W + ad)
    if e is None: return False
    v = e.get(W + "val")
    return v not in ("0", "false", "none")
def parcala(runs, ad):
    out, aktif = [], ""
    for t, r in runs:
        if ozellik(r, ad): aktif += t
        elif aktif and t.strip() in ("", "-"): aktif += t
        else:
            if aktif.strip(): out.append(aktif.strip())
            aktif = ""
    if aktif.strip(): out.append(aktif.strip())
    return out
govde = ET.fromstring(zipfile.ZipFile(sys.argv[1]).read("word/document.xml")).find(W + "body")
paras = []
for p in govde.iter(W + "p"):
    runs = [("".join(x.text or "" for x in r.findall(W + "t")), r) for r in p.iter(W + "r")]
    runs = [(t, r) for t, r in runs if t]
    m = "".join(t for t, _ in runs).strip()
    if m: paras.append({"t": m, "b": parcala(runs, "b"), "u": parcala(runs, "u")})
json.dump(paras, open(sys.argv[2], "w"), ensure_ascii=False)
