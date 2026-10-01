// Örnek sayfaların ortak küçük davranışları.
(function () {
  // Bugünün tarihi (el yazısı başlık)
  document.querySelectorAll('[data-bugun]').forEach(function (el) {
    try { el.textContent = new Date().toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', weekday: 'long' }); } catch (e) {}
  });

  // Gece / gündüz
  var d = document.createElement('button');
  d.className = 'tema-dugme';
  d.textContent = 'gece / gündüz';
  d.addEventListener('click', function () {
    var r = document.documentElement;
    var koyu = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    r.dataset.theme = koyu ? 'light' : 'dark';
  });
  var yer = document.querySelector('.ust .sag');
  if (yer) { d.classList.add('ust-icinde'); yer.insertBefore(d, yer.firstChild); } else { document.body.appendChild(d); }

  // Ortak menüleri doldur: hangi sayfadaysak o işaretlenir
  var bolumler = [
    ['kelime.html', 'Sözlük', '<path d="M4.5 5.2c0-1.2.9-2.1 2.1-2.1h12.6v15.8H6.6c-1.2 0-2.1.9-2.1 2.1V5.2Z"/><path d="M4.5 19.2c0-1.1.9-2 2-2h12.7"/>'],
    ['learnpass.html', 'Çalışmalar', '<path d="M5 4.3h14.2v15.4H4.8z"/><path d="m8.4 12.2 2.6 2.7 4.8-5.6"/>'],
    ['index.html', 'Ana Sayfa', '<path d="M4 11.2 12.1 4l7.9 7.1v8.3H15v-5.8H9.1v5.8H4.1z"/>'],
    ['okuma.html', 'Okumalar', '<path d="M5.2 3.1h13.6v17.8H5.1z"/><path d="M8.8 8.1h6.5M8.8 12h6.2M8.8 15.9h3.4"/>'],
    ['yazilar.html', 'Yazılar', '<path d="M4 20.1h4.1L19.2 9l-4.1-4.1L4 16z"/><path d="m13.2 6.8 4 4"/>']
  ];
  var burasi = location.pathname.split('/').pop() || 'index.html';
  if (burasi.indexOf('.html') < 0) burasi = 'index.html';
  var ust = document.querySelector('.ust nav');
  if (ust) ust.innerHTML = bolumler.map(function (b) {
    return '<a href="' + b[0] + '"' + (b[0] === burasi ? ' class="secili"' : '') + '>' + b[1] + '</a>';
  }).join('');
  var alt = document.createElement('nav');
  alt.className = 'alt-menu';
  alt.innerHTML = bolumler.map(function (b) {
    return '<a href="' + b[0] + '"' + (b[0] === burasi ? ' class="secili"' : '') + '><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">' + b[2] + '</svg><span>' + b[1] + '</span></a>';
  }).join('');
  if (!document.body.hasAttribute('data-menusuz')) document.body.appendChild(alt);
})();
