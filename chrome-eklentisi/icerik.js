/*
 * LearnVocab Chrome eklentisi: sayfadaki baloncuk (rapor 11).
 *
 * Herhangi bir sitede İngilizce bir kelimeye ÇİFT TIKLAYINCA, Okumalar'daki
 * baloncuğun aynısı çıkar (templates/pages/readings/_kelimeBaloncugu.html):
 * kök, numaralı anlamlar, phrasal verb, "Listeme ekle +", yoksa "Henüz
 * sözlüğümüzde yok". Altta "Oxford'da ara" aynı sekmede Oxford'a gider.
 *
 * Kapanma: baloncuğun dışında herhangi bir yere (kelimenin kendisi dahil) bir
 * kez tıklayınca, Esc'ye basınca ya da kelime ekrandan çıkınca. Ekran dolmasın
 * diye aynı anda tek baloncuk olur.
 *
 * Baloncuk kapalı bir Shadow DOM içinde: sitenin CSS'i onu, onun CSS'i siteyi
 * bozmaz. Yazı kutularında (input, textarea, düzenlenebilir alanlar) çift
 * tıklama sitenin kendi işi olduğu için açılmaz.
 */
(() => {
  if (window.__learnvocabBaloncugu) { return; }
  window.__learnvocabBaloncugu = true;

  const t = (ad, yedek) => (chrome.i18n && chrome.i18n.getMessage(ad)) || yedek || ad;
  const OXFORD = "https://www.oxfordlearnersdictionaries.com/search/english/?q=";

  const HARF = /[A-Za-zÀ-ɏ'’\-]/;
  const CUMLE_SINIRI = /[.!?;:,()\[\]"“”]/;
  const sonuclar = new Map();   // anahtar -> sonuç (sayfa açık kaldıkça)
  let host = null, balon = null;
  let etkin = null;             // { aralik, kelime, anahtar }
  let istekNo = 0;

  // ---------- Kurulum ----------
  const STIL = `
    :host { all: initial; }
    .balon {
      position: fixed; z-index: 2147483647; box-sizing: border-box;
      width: min(21rem, calc(100vw - 2rem)); padding: 14px 16px 10px;
      background: #fbfaf5; color: #1b1d22; border: 1.5px solid #1d3f8f; border-radius: 4px;
      box-shadow: 4px 4px 0 #e9eefb, 0 8px 24px rgba(0, 0, 0, .14);
      font: 400 15px/1.45 Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
      text-align: left; letter-spacing: normal; text-transform: none;
    }
    .balon[hidden] { display: none; }
    .madde + .madde { margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(66, 110, 190, .22); }
    .ust { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
    .baslik { min-width: 0; margin: 0; padding-top: 2px; }
    .yazim { color: #5f6470; font-size: 15px; }
    .kok { font: 900 24px/1 Georgia, "Times New Roman", serif; color: #1b1d22; overflow-wrap: anywhere; }
    .anlamlar { margin: 6px 0 0; padding: 0; color: #1d3f8f; font-weight: 700; font-size: 16px; }
    ol.anlamlar { padding-left: 20px; }
    .anlamlar li, .anlamlar p { margin: 2px 0 0; line-height: 1.35; }
    .soluk { color: #5f6470; margin: 4px 0 0; }
    .yok { font-weight: 600; margin: 0; }
    button {
      all: unset; box-sizing: border-box; cursor: pointer; white-space: nowrap; flex: none;
      font: 600 13px/1 Inter, ui-sans-serif, system-ui, sans-serif; border-radius: 4px; padding: 7px 10px;
    }
    button:focus-visible { outline: 2px solid #1d3f8f; outline-offset: 2px; }
    button[disabled] { opacity: .6; cursor: default; }
    .liste { background: #1d3f8f; color: #fff; }
    .liste:hover { background: #163274; }
    .liste[data-listede="1"] { background: #e3f3ea; color: #1f7a4c; box-shadow: inset 0 0 0 1px #9fd4b6; }
    .alt { display: flex; align-items: center; justify-content: space-between; gap: 8px;
           margin-top: 12px; padding-top: 8px; border-top: 1px dashed rgba(66, 110, 190, .22); }
    .sag { display: flex; flex-wrap: wrap; justify-content: flex-end; align-items: center; gap: 2px 12px; }
    .marka { font: 700 13px/1 Inter, ui-sans-serif, system-ui, sans-serif; color: #5f6470; }
    .oxford { color: #1d3f8f; padding: 6px 4px; text-decoration: underline; text-underline-offset: 3px; }
    .giris { color: #1d3f8f; padding: 6px 4px; text-decoration: underline; text-underline-offset: 3px; }
    @media (prefers-color-scheme: dark) {
      .balon { background: #1d2027; color: #e9e8e2; border-color: #9db8ff; box-shadow: 4px 4px 0 #1f2a44, 0 8px 24px rgba(0, 0, 0, .5); }
      .kok { color: #e9e8e2; }
      .anlamlar, .oxford, .giris { color: #9db8ff; }
      .yazim, .soluk, .marka { color: #a3a7b0; }
      .liste { background: #9db8ff; color: #16181d; }
      .liste:hover { background: #b9ccff; }
      .liste[data-listede="1"] { background: #13291f; color: #6fd6a0; box-shadow: inset 0 0 0 1px #2f6b4b; }
      .madde + .madde, .alt { border-color: rgba(130, 160, 230, .16); }
    }
  `;

  function kur() {
    if (host && host.isConnected) { return; }
    host = document.createElement("learnvocab-baloncuk");
    const golge = host.attachShadow({ mode: "closed" });
    const stil = document.createElement("style");
    stil.textContent = STIL;
    balon = document.createElement("div");
    balon.className = "balon";
    balon.hidden = true;
    balon.setAttribute("role", "dialog");
    balon.setAttribute("aria-live", "polite");
    balon.setAttribute("lang", "tr");
    golge.append(stil, balon);
    document.documentElement.append(host);
  }

  function eleman(etiket, sinif, yazi) {
    const e = document.createElement(etiket);
    if (sinif) { e.className = sinif; }
    if (yazi != null) { e.textContent = yazi; }
    return e;
  }

  // ---------- Çift tıklanan kelime ----------
  function duzenlenebilir(hedef) {
    for (let e = hedef; e && e.nodeType === 1; e = e.parentElement) {
      if (e.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(e.tagName)) { return true; }
    }
    return false;
  }

  function kelimeler(yazi) {
    return yazi.split(/\s+/).filter((k) => /[A-Za-z]/.test(k));
  }

  function secilenKelime() {
    const secim = window.getSelection();
    if (!secim || !secim.rangeCount) { return null; }
    const r = secim.getRangeAt(0);
    const dugum = r.startContainer;
    if (dugum.nodeType !== 3) { return null; }
    const yazi = dugum.data;
    let bas = r.startOffset, son = r.startOffset;
    while (son < yazi.length && /\s/.test(yazi[son])) { son++; bas++; }
    while (bas > 0 && HARF.test(yazi[bas - 1])) { bas--; }
    while (son < yazi.length && HARF.test(yazi[son])) { son++; }
    while (bas < son && /['’\-]/.test(yazi[bas])) { bas++; }
    while (son > bas && /['’\-]/.test(yazi[son - 1])) { son--; }
    const kelime = yazi.slice(bas, son).replace(/[’']s$/i, "");
    // Yalnızca İngilizce harflerle yazılmış, makul uzunlukta bir kelime.
    if (!/^[A-Za-z][A-Za-z'’\-]{0,39}$/.test(kelime)) { return null; }

    const aralik = document.createRange();
    aralik.setStart(dugum, bas);
    aralik.setEnd(dugum, bas + kelime.length);

    // Aynı cümle parçasındaki komşu kelimeler (phrasal verb için: "gave it up").
    let onceki = yazi.slice(Math.max(0, bas - 60), bas).split(CUMLE_SINIRI).pop();
    let sonraki = yazi.slice(son, son + 60).split(CUMLE_SINIRI)[0];
    if (bas > 0 && CUMLE_SINIRI.test(yazi[bas - 1])) { onceki = ""; }
    if (son < yazi.length && CUMLE_SINIRI.test(yazi[son])) { sonraki = ""; }
    return {
      aralik, kelime,
      once: kelimeler(onceki).slice(-2).join(" "),
      sonra: kelimeler(sonraki).slice(0, 3).join(" "),
    };
  }

  // ---------- Sunucu (arka plan betiği üzerinden) ----------
  function gonder(mesaj) {
    return new Promise((coz) => {
      try {
        chrome.runtime.sendMessage(mesaj, (yanit) => {
          coz(chrome.runtime.lastError ? { hata: "baglanti" } : (yanit || { hata: "bos" }));
        });
      } catch (h) {
        coz({ hata: "baglanti" });   // eklenti güncellendi, sayfa eski betikle kaldı
      }
    });
  }

  // ---------- Baloncuk ----------
  function listeDugmesi(madde) {
    const d = eleman("button", "liste");
    d.type = "button";
    const guncelle = () => {
      d.dataset.listede = madde.listede ? "1" : "0";
      d.textContent = madde.listede ? t("listemde", "Listemde") + " ✓" : t("listeme_ekle", "Listeme ekle") + " +";
      d.title = madde.listede ? t("listemde_cikar", "Listemde — çıkarmak için tıkla") : t("listeme_ekle", "Listeme ekle");
      d.setAttribute("aria-pressed", madde.listede ? "true" : "false");
    };
    guncelle();
    d.addEventListener("click", async () => {
      d.disabled = true;
      const yanit = await gonder({ tur: "liste", id: madde.word_id, ekle: !madde.listede });
      d.disabled = false;
      if (yanit.giris) { gonder({ tur: "giris" }); return; }
      if (yanit.hata) { d.textContent = t("tekrar_dene", "Olmadı, tekrar dene"); return; }
      madde.listede = !!yanit.kayitli;
      guncelle();
    });
    return d;
  }

  function blok(madde, yazim, girisli) {
    const kutu = eleman("div", "madde");
    const ust = eleman("div", "ust");
    const baslik = eleman("p", "baslik");
    if (yazim && yazim.toLowerCase() !== String(madde.kok).toLowerCase()) {
      baslik.append(eleman("span", "yazim", yazim + " → "));
    }
    const kok = eleman("span", "kok", madde.kok);
    kok.lang = "en";
    baslik.append(kok);
    ust.append(baslik);
    if (girisli) { ust.append(listeDugmesi(madde)); }
    kutu.append(ust);

    const anlamlar = madde.anlamlar || [];
    const liste = eleman(anlamlar.length > 1 ? "ol" : "div", "anlamlar");
    anlamlar.forEach((a) => {
      const s = eleman(anlamlar.length > 1 ? "li" : "p", null, a.tr);
      if (a.tanim) { s.title = a.tanim; }
      liste.append(s);
    });
    kutu.append(liste);
    return kutu;
  }

  function altSatir(aranan, girisli, bulundu) {
    const alt = eleman("div", "alt");
    alt.append(eleman("span", "marka", "LearnVocab"));
    const sag = eleman("div", "sag");
    if (!girisli && bulundu) {
      const g = eleman("button", "giris", t("giris_yap", "Giriş yap, listene ekle"));
      g.type = "button";
      g.addEventListener("click", () => gonder({ tur: "giris" }));
      sag.append(g);
    }
    const o = eleman("button", "oxford", t("oxford_ara", "Oxford'da ara"));
    o.type = "button";
    o.addEventListener("click", () => { window.location.assign(OXFORD + encodeURIComponent(aranan)); });
    sag.append(o);
    alt.append(sag);
    return alt;
  }

  function ciz(sonuc, kelime) {
    const girisli = !!sonuc.girisli;
    const bloklar = [];
    if (sonuc.phrasal) { bloklar.push(blok(sonuc.phrasal, null, girisli)); }
    if (sonuc.bulundu) {
      bloklar.push(blok(sonuc, kelime, girisli));
      (sonuc.digerleri || []).forEach((m) => bloklar.push(blok(m, null, girisli)));
    }
    balon.replaceChildren();
    if (!bloklar.length) {
      balon.append(eleman("p", "yok", kelime));
      balon.append(eleman("p", "soluk", t("sozlukte_yok", "Henüz sözlüğümüzde yok.")));
    } else {
      bloklar.forEach((b) => balon.append(b));
    }
    const aranan = sonuc.phrasal ? sonuc.phrasal.kok : (sonuc.bulundu ? sonuc.kok : kelime);
    balon.append(altSatir(aranan, girisli, bloklar.length > 0));
  }

  function bekliyor(kelime) {
    balon.replaceChildren(eleman("p", "soluk", kelime + " …"));
  }

  function hata(kelime) {
    balon.replaceChildren(eleman("p", "soluk", t("getiremedik", "Anlamı şu an getiremedik, tekrar dener misin?")));
    balon.append(altSatir(kelime, true, false));
  }

  function konumla() {
    if (!etkin) { return; }
    const r = etkin.aralik.getBoundingClientRect();
    if (!r.width && !r.height) { kapat(); return; }
    if (r.bottom < 0 || r.top > window.innerHeight) { kapat(); return; }
    const gen = balon.offsetWidth, yuk = balon.offsetHeight;
    const x = Math.min(Math.max(8, r.left + r.width / 2 - gen / 2), window.innerWidth - gen - 8);
    let y = r.bottom + 8;
    if (y + yuk > window.innerHeight - 8 && r.top - yuk - 8 > 8) { y = r.top - yuk - 8; }
    balon.style.left = Math.max(8, x) + "px";
    balon.style.top = Math.max(8, y) + "px";
  }

  function kapat() {
    etkin = null;
    if (balon) { balon.hidden = true; balon.replaceChildren(); }
  }

  async function ac(s) {
    kur();
    const anahtar = [s.kelime, s.once, s.sonra].join("|").toLowerCase();
    const no = ++istekNo;
    etkin = { aralik: s.aralik, kelime: s.kelime, anahtar };

    const hazir = sonuclar.get(anahtar);
    if (hazir) { ciz(hazir, s.kelime); } else { bekliyor(s.kelime); }
    balon.hidden = false;
    konumla();
    if (hazir) { return; }

    const yanit = await gonder({ tur: "sorgula", q: s.kelime, once: s.once, sonra: s.sonra });
    if (no !== istekNo || !etkin) { return; }
    if (yanit.sonuc) {
      sonuclar.set(anahtar, yanit.sonuc);
      ciz(yanit.sonuc, s.kelime);
    } else {
      hata(s.kelime);
    }
    konumla();
  }

  // ---------- Olaylar ----------
  const baloncuktaMi = (olay) => !!host && olay.composedPath().includes(host);

  document.addEventListener("dblclick", (olay) => {
    if (baloncuktaMi(olay) || duzenlenebilir(olay.target)) { return; }
    const s = secilenKelime();
    if (s) { ac(s); }
  }, true);

  // Baloncuğun dışına (kelimenin kendisi dahil) bir kez basınca kapanır.
  // Çift tıklamanın ilk basışı eski baloncuğu kapatır; dblclick yenisini açar.
  document.addEventListener("pointerdown", (olay) => {
    if (etkin && !baloncuktaMi(olay)) { kapat(); }
  }, true);
  document.addEventListener("keydown", (olay) => {
    if (olay.key === "Escape" && etkin) { kapat(); }
  }, true);
  window.addEventListener("scroll", konumla, { passive: true, capture: true });
  window.addEventListener("resize", konumla, { passive: true });
})();
