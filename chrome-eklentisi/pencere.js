// Araç çubuğundaki simgeye tıklayınca açılan kısa bilgi (rapor 11).
document.documentElement.lang = chrome.i18n.getUILanguage().startsWith("tr") ? "tr" : "en";
document.querySelectorAll("[data-i18n]").forEach((e) => {
  const yazi = chrome.i18n.getMessage(e.dataset.i18n);
  if (yazi) { e.textContent = yazi; }
});
