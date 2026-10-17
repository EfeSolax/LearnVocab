/*
 * LearnVocab Chrome eklentisi: arka plan (rapor 11).
 *
 * Siteye giden bütün istekler buradan atılır, sayfanın içinden değil:
 *   - Eklentinin siteye erişim izni (host_permissions) olduğu için Chrome burada
 *     CORS uygulamaz ve LearnVocab oturum çerezini gönderir. Kullanıcı sitede
 *     girişliyse eklentide de girişlidir; ayrı bir giriş yok.
 *   - Sayfanın kendi güvenlik kuralları (CSP) istekleri engelleyemez.
 *
 * Mesajlar (icerik.js'ten):
 *   {tur: "sorgula", q, once, sonra}  -> {sonuc} | {hata}
 *   {tur: "liste", id, ekle}          -> {ok, kayitli} | {giris: true} | {hata}
 *   {tur: "giris"}                    -> sitenin giriş sayfasını yeni sekmede açar
 *   {tur: "oxford", q}                -> Oxford'da aramayı yeni sekmede açar (sayfa yerinde kalır)
 */

const SITE = "https://www.learnvocab.com.tr";
const OXFORD = "https://www.oxfordlearnersdictionaries.com/search/english/?q=";

async function sorgula(m) {
  const p = new URLSearchParams({ q: String(m.q || "").slice(0, 60) });
  if (m.once) { p.set("once", String(m.once).slice(0, 80)); }
  if (m.sonra) { p.set("sonra", String(m.sonra).slice(0, 80)); }
  const cevap = await fetch(`${SITE}/api/kelime/?${p}`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (!cevap.ok) { return { hata: cevap.status }; }
  return { sonuc: await cevap.json() };
}

async function liste(m) {
  const id = Number(m.id);
  if (!Number.isInteger(id) || id <= 0) { return { hata: "kimlik" }; }
  const cevap = await fetch(`${SITE}/api/eklenti/listem/${id}/`, {
    method: m.ekle ? "POST" : "DELETE",
    credentials: "include",
    headers: { Accept: "application/json", "X-Requested-With": "fetch" },
  });
  if (cevap.status === 401) { return { giris: true }; }
  if (!cevap.ok) { return { hata: cevap.status }; }
  return cevap.json();
}

async function isle(m) {
  switch (m && m.tur) {
    case "sorgula": return sorgula(m);
    case "liste": return liste(m);
    case "giris":
      await chrome.tabs.create({ url: `${SITE}/giris/` });
      return { ok: true };
    case "oxford":
      // Yalnızca Oxford araması açılır; adres burada kurulur (sayfadan adres alınmaz)
      await chrome.tabs.create({ url: OXFORD + encodeURIComponent(String(m.q || "").slice(0, 60)) });
      return { ok: true };
    default: return { hata: "tur" };
  }
}

chrome.runtime.onMessage.addListener((mesaj, gonderen, yanitla) => {
  isle(mesaj).then(yanitla, (hata) => yanitla({ hata: String(hata) }));
  return true;   // yanıt sonra gelecek
});
