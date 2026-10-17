/*
 * Tailwind derlemesi (rapor 18.17: Standalone CLI). Sunucuda hiçbir şey çalışmaz;
 * çıktı static/css/site.css git'e girer.
 *
 *   Derle:   .venv/bin/tailwindcss -c tailwind.config.js -i static/css/tailwind-giris.css -o static/css/site.css --minify
 *   İzle:    aynı komut + --watch
 *   Program: .venv/bin/tailwindcss (v3.4.19, git'e girmez). Yoksa GitHub'dan
 *            tailwindlabs/tailwindcss sürüm v3.4.19 → tailwindcss-macos-arm64 indirilir.
 *
 * Şablon değiştikten sonra yeniden derlemeyi unutma: yeni bir sınıf derlenmezse
 * sayfada stili görünmez (LearnVocab/test_tailwind.py bunu yakalar).
 *
 * Renkler defter teması (rapor 18.12, static/css/defter.css): indigo/violet/purple
 * mürekkep mavisi, gray kâğıt-mürekkep nötrleri, slate gece defteri.
 */
const murekkep = { 50: '#eef2fb', 100: '#dde5f7', 200: '#bccbee', 300: '#92aae0', 400: '#9db8ff', 500: '#3a5fbf',
                   600: '#1d3f8f', 700: '#17337a', 800: '#132a63', 900: '#10224f', 950: '#0c1a3d' };

module.exports = {
  darkMode: 'class',
  future: { hoverOnlyWhenSupported: true },
  content: [
    './templates/**/*.html',
    './*/templates/**/*.html',
  ],
  // Adı şablonda değişkenle kurulan sınıflar: okuma konularının renkleri
  // (readings/models.py TOPICS; templates/pages/readings.html).
  safelist: [
    // Okuma konularının renkleri (readings.models.RENKLER; admin'den seçilir)
    { pattern: /^(bg|text)-(indigo|violet|emerald|amber|rose|sky|teal|orange|lime|fuchsia|cyan|pink)-(50|300|600|700|950)$/, variants: ['dark'] },
  ],
  theme: { extend: {
    colors: {
      indigo: murekkep, violet: murekkep, purple: murekkep,
      gray: { 50: '#f7f6f1', 100: '#efede6', 200: '#e3e1d8', 300: '#cfccc1', 400: '#a19f97', 500: '#6f6e6a',
              600: '#55565b', 700: '#3c3e44', 800: '#26282d', 900: '#1b1d22', 950: '#111215' },
      slate: { 50: '#f4f3ee', 100: '#e9e8e2', 200: '#d6d5cf', 300: '#bdbcb6', 400: '#a3a7b0', 500: '#7b808b',
               600: '#4c515c', 700: '#2e323b', 800: '#1d2027', 900: '#16181d', 950: '#0f1013' },
    },
    fontFamily: {
      sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      serif: ['Fraunces', 'Georgia', 'serif'],
    },
  } },
};
