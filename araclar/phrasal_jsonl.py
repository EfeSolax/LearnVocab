"""
Elle yazılmış kelime kaynak dosyalarını `elle_kelime_yukle` JSONL'üne çevirir. Claude elle
yazar, API yok. Phrasal verb'ler (veri/phrasal_verbs/*.txt, rapor 18.38) ve temel kelimeler
(veri/temel_kelimeler/*.txt, rapor 18.36).

    .venv/bin/python araclar/phrasal_jsonl.py veri/phrasal_verbs/*.txt

Her .txt'nin yanına aynı adlı .jsonl yazılır. Biçim:

    # yorum
    give up | B1 | c                       <- yazım | seviye | kaynak (c = cambridge, l = learnvocab); tür phrasal_verb
    the | determiner | A1 | c              <- dört alanlı başlıkta ikinci alan tür
      vazgeçmek | to stop trying | Don't give up. / She gave up. | quit, abandon
      (alışkanlığı) bırakmak | to stop doing sth regularly | He gave up smoking. / …

Anlam satırı girintilidir: Türkçe | İngilizce açıklama | örnekler (" / " ile) | benzer (isteğe bağlı, virgülle).
"""
import json
import sys

KAYNAKLAR = {"c": "cambridge", "l": "learnvocab"}
SEVIYELER = {"A1", "A2", "B1", "B2", "C1", "C2"}


def cevir(yol):
    kayitlar, k = [], None
    for no, ham in enumerate(open(yol, encoding="utf-8"), 1):
        satir = ham.rstrip()
        if not satir.strip() or satir.lstrip().startswith("#"):
            continue
        parca = [p.strip() for p in satir.split("|")]
        if not ham[0].isspace():
            if len(parca) == 3:
                parca.insert(1, "phrasal_verb")
            if len(parca) != 4 or parca[2] not in SEVIYELER or parca[3] not in KAYNAKLAR:
                sys.exit(f"{yol}:{no}: başlık bozuk: {satir}")
            k = {"text": parca[0], "pos": parca[1], "cefr": parca[2],
                 "cefr_kaynak": KAYNAKLAR[parca[3]], "anlamlar": []}
            kayitlar.append(k)
            continue
        if k is None or len(parca) not in (3, 4) or not all(parca[:3]):
            sys.exit(f"{yol}:{no}: anlam satırı bozuk: {satir}")
        anlam = {"tr": parca[0], "en": parca[1],
                 "ornekler": [o.strip() for o in parca[2].split(" / ") if o.strip()]}
        if len(parca) == 4 and parca[3]:
            anlam["benzer"] = [b.strip() for b in parca[3].split(",") if b.strip()]
        k["anlamlar"].append(anlam)
    for k in kayitlar:
        if not k["anlamlar"]:
            sys.exit(f"{yol}: {k['text']} anlamsız")
    yazimlar = [(k["text"], k["pos"]) for k in kayitlar]
    tekrar = {y for y in yazimlar if yazimlar.count(y) > 1}
    if tekrar:
        sys.exit(f"{yol}: tekrar eden: {', '.join(sorted(f'{t}:{p}' for t, p in tekrar))}")
    with open(yol[:-4] + ".jsonl", "w", encoding="utf-8") as f:
        for k in kayitlar:
            f.write(json.dumps(k, ensure_ascii=False) + "\n")
    return len(kayitlar)


if __name__ == "__main__":
    for yol in sys.argv[1:]:
        print(f"{yol}: {cevir(yol)} kelime")
