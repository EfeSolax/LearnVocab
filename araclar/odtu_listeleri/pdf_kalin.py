"""PDF'ten satır metni ve kalın parçalar (font adında Bold ya da bold bayrağı)."""
import sys, json, pymupdf
def satirlar(yol):
    out = []
    for sayfa in pymupdf.open(yol):
        for blok in sayfa.get_text("dict")["blocks"]:
            for satir in blok.get("lines", []):
                metin, kal, aktif = "", [], ""
                for sp in satir["spans"]:
                    t = sp["text"]
                    metin += t
                    bold = ("Bold" in sp["font"]) or (sp["flags"] & 16)
                    if bold: aktif += t
                    elif aktif and t.strip() in ("", "-"): aktif += t
                    else:
                        if aktif.strip(): kal.append(aktif.strip())
                        aktif = ""
                if aktif.strip(): kal.append(aktif.strip())
                if metin.strip(): out.append({"t": metin.strip(), "b": kal, "x": round(satir["bbox"][0])})
    return out
if __name__ == "__main__":
    json.dump(satirlar(sys.argv[1]), open(sys.argv[2], "w"), ensure_ascii=False)
