# -*- coding: utf-8 -*-
"""
İki (ya da daha çok) kontrol modelinin kararlarını yan yana koyar.

    python manage.py kontrol_kiyasla --depolar ara-depo-kontrol-gemini,ara-depo-kontrol-luna

Her depo aynı üretim cevaplarının kopyası olmalı ve her birinde
`aile_doldur --dry-run --hepsi --kontrol-model <model>` çalışmış olmalı.
Karşılaştırma yalnızca iki modelin BİREBİR AYNI girdiyi gördüğü kelimelerde
yapılır (ilk_kontrol_icin eşit); farklı girdi görenler sayılıp dışarıda kalır.

Ne ölçülüyor:
  - Her modelin kararları: kaç anlam doğru / karşılık yanlış / anlam yanlış,
    kaç kelime "bu türde kullanılmaz", kaç cümle ve seviye değişikliği.
    Maliyet ve token (depodaki kontrol_token'dan).
  - ANLAŞMA: iki modelin aynı anlama aynı kararı verme oranı.
  - ANLAŞMAZLIKLAR: her biri ayrı ayrı, iki modelin gerekçesi ve önerdiği
    karşılıkla. Hakem burada karar verir: hangi model haklı?

Rapor ekrana ve ilk deponun içine (kontrol-kiyas.txt) yazılır.
"""

import json
from collections import Counter
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from words.aile.depo import Depo
from words.aile.kontrol import KontrolCevabi


class Command(BaseCommand):
    help = "Kontrol modellerinin kararlarını karşılaştırır."

    def add_arguments(self, c):
        c.add_argument("--depolar", required=True, help="Virgülle ayrılmış depo klasörleri.")
        c.add_argument("--fiyatlar", default="",
                       help="Her depo için 'girdi,çıktı' fiyatı, ';' ile: 0.75,3.75;0.2,1.2")

    def handle(self, *args, **s):
        yollar = [y.strip() for y in s["depolar"].split(",") if y.strip()]
        if len(yollar) < 2:
            raise CommandError("En az iki depo ver.")
        fiyatlar = []
        if s["fiyatlar"]:
            fiyatlar = [tuple(float(x) for x in f.split(",")) for f in s["fiyatlar"].split(";")]

        veriler = []
        for yol in yollar:
            kayitlar = {k: v for k, v in Depo(yol).anlamlar().items() if v.get("ilk_kontrol_ham")}
            if not kayitlar:
                raise CommandError(f"{yol}: kontrol edilmiş kayıt yok. Önce aile_doldur "
                                   f"--dry-run --hepsi --kontrol-model … çalıştır.")
            model = Counter(v.get("kontrol_model", "?") for v in kayitlar.values()).most_common(1)[0][0]
            veriler.append({"yol": yol, "model": model, "kayitlar": kayitlar})

        ortak = set.intersection(*(set(v["kayitlar"]) for v in veriler))
        ayni = [k for k in sorted(ortak)
                if len({v["kayitlar"][k]["ilk_kontrol_icin"] for v in veriler}) == 1]
        dislanan = len(ortak) - len(ayni)

        s_ = []
        yaz = s_.append
        yaz("KONTROL MODELİ KIYASI")
        yaz("=" * 78)
        yaz(f"Karşılaştırılan kelime: {len(ayni)}"
            + (f" ({dislanan} kelime farklı girdi gördüğü için dışarıda)" if dislanan else ""))
        yaz("")

        # --- Model başına özet ------------------------------------------
        kararlar = []   # model sırasıyla: {(kelime, tür): KontrolCevabi}
        for i, v in enumerate(veriler):
            kk = {k: KontrolCevabi.model_validate_json(v["kayitlar"][k]["ilk_kontrol_ham"])
                  for k in ayni}
            kararlar.append(kk)
            say = Counter()
            for k, karar in kk.items():
                anlam_sayisi = len(v["kayitlar"][k].get("ilk_kontrol_anlamlar") or [])
                say["anlam"] += anlam_sayisi
                if not karar.word_valid:
                    say["kelime_ret"] += 1
                for m in karar.meanings:
                    say[m.verdict] += 1
                    say["cumle"] += len(m.bad_sentences)
                    say["esdizim"] += len(m.bad_collocations)
                    anlamlar = v["kayitlar"][k].get("ilk_kontrol_anlamlar") or []
                    if 1 <= m.index <= len(anlamlar) and anlamlar[m.index - 1]["cefr"] != m.cefr:
                        say["cefr"] += 1
            girdi = sum((v["kayitlar"][k].get("kontrol_token") or {}).get("girdi", 0) for k in ayni)
            cikti = sum((v["kayitlar"][k].get("kontrol_token") or {}).get("cikti", 0) for k in ayni)
            yanlis = say["karsilik_yanlis"] + say["anlam_yanlis"]
            yaz(f"[{i + 1}] {v['model']}  ({v['yol']})")
            yaz(f"    {say['anlam']} anlam: {say['dogru']} doğru · {say['karsilik_yanlis']} karşılık "
                f"yanlış · {say['anlam_yanlis']} anlam yanlış  → yanlış dediği: "
                f"%{100 * yanlis / max(say['anlam'], 1):.1f}")
            yaz(f"    {say['kelime_ret']} kelime 'bu türde kullanılmaz' · {say['cumle']} hatalı cümle · "
                f"{say['esdizim']} hatalı eş dizim · {say['cefr']} seviye değişikliği")
            satir = f"    token: {girdi:,} girdi + {cikti:,} çıktı"
            if len(fiyatlar) > i:
                maliyet = girdi / 1e6 * fiyatlar[i][0] + cikti / 1e6 * fiyatlar[i][1]
                satir += (f" · ${maliyet:.3f} · kelime başı ${maliyet / max(len(ayni), 1):.5f}"
                          f" · 10.000 kelime ≈ ${maliyet / max(len(ayni), 1) * 10000:.2f}")
            yaz(satir)
            yaz("")

        # --- Anlaşma ve anlaşmazlıklar (ilk iki model) -------------------
        a, b = kararlar[0], kararlar[1]
        ma, mb = veriler[0]["model"], veriler[1]["model"]
        toplam = anlasan = 0
        ayrilik = []
        for k in ayni:
            anlamlar = veriler[0]["kayitlar"][k].get("ilk_kontrol_anlamlar") or []
            ka, kb = a[k], b[k]
            if ka.word_valid != kb.word_valid:
                ayrilik.append((k, None, anlamlar, ka, kb))
            da = {m.index: m for m in ka.meanings}
            db = {m.index: m for m in kb.meanings}
            for no in range(1, len(anlamlar) + 1):
                toplam += 1
                va = da.get(no).verdict if no in da else "karar_yok"
                vb = db.get(no).verdict if no in db else "karar_yok"
                if va == vb:
                    anlasan += 1
                else:
                    ayrilik.append((k, no, anlamlar, da.get(no), db.get(no)))

        yaz(f"ANLAŞMA ({ma} ↔ {mb}): {anlasan}/{toplam} anlam = %{100 * anlasan / max(toplam, 1):.1f}")
        yaz(f"ANLAŞMAZLIK: {len(ayrilik)}")
        yaz("=" * 78)
        for k, no, anlamlar, x, y in ayrilik:
            kelime, tur = k
            if no is None:
                yaz(f"■ {kelime} ({tur}) — KELİME GEÇERLİ Mİ?")
                yaz(f"    [1] {x.word_valid}  {x.word_reason}")
                yaz(f"    [2] {y.word_valid}  {y.word_reason}")
                yaz("")
                continue
            anlam = anlamlar[no - 1]
            yaz(f"■ {kelime} ({tur}) · anlam {no}: \"{anlam['meaning_tr']}\" ({anlam['cefr']})")
            yaz(f"    tanım: {anlam['definition']}")
            for etiket, karar in (("[1]", x), ("[2]", y)):
                if karar is None:
                    yaz(f"    {etiket} karar vermedi")
                    continue
                ek = f" → '{karar.correct_tr}'" if karar.correct_tr else ""
                yaz(f"    {etiket} {karar.verdict}{ek}  {karar.reason}".rstrip())
            yaz("")

        metin = "\n".join(s_) + "\n"
        self.stdout.write(metin)
        hedef = Path(yollar[0]) / "kontrol-kiyas.txt"
        hedef.write_text(metin, encoding="utf-8")
        self.stdout.write(f"Rapor: {hedef}")
        # Makinenin okuyacağı hâli de (hakem adımı için)
        (Path(yollar[0]) / "kontrol-kiyas.json").write_text(json.dumps(
            [{"kelime": k[0], "tur": k[1], "anlam": no,
              "karsilik": (anl[no - 1]["meaning_tr"] if no else None),
              "a": x.model_dump() if x else None, "b": y.model_dump() if y else None}
             for k, no, anl, x, y in ayrilik], ensure_ascii=False, indent=1), encoding="utf-8")
