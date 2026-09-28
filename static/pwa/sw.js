/*
 * LearnVocab service worker (rapor 10).
 *
 * Yalnızca bildirim işi yapar: push olayını gösterir, tıklanınca ilgili
 * adrese gider. Bilerek ÖNBELLEKLEME YOK (fetch dinleyicisi yok): eski
 * sayfaların takılı kalması gibi sorunlar yaşanmasın. Sunucu bu dosyayı
 * /sw.js adresinden, önbelleğe alınmadan verir.
 */

self.addEventListener('install', function () {
    self.skipWaiting();
});

self.addEventListener('activate', function (event) {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('push', function (event) {
    var veri = {};
    try { veri = event.data ? event.data.json() : {}; } catch (e) {
        veri = { govde: event.data ? event.data.text() : '' };
    }
    var baslik = veri.baslik || 'LearnVocab';
    event.waitUntil(self.registration.showNotification(baslik, {
        body: veri.govde || '',
        icon: '/static/pwa/ikon-192.png',
        badge: '/static/pwa/ikon-192.png',
        lang: 'tr',
        data: { url: veri.url || '/' },
    }));
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    var hedef = new URL((event.notification.data && event.notification.data.url) || '/',
                        self.location.origin).href;
    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (pencereler) {
            for (var i = 0; i < pencereler.length; i++) {
                var p = pencereler[i];
                if (p.url === hedef && 'focus' in p) { return p.focus(); }
            }
            // Açık bir LearnVocab penceresi varsa onu kullan, yoksa yenisini aç.
            for (var j = 0; j < pencereler.length; j++) {
                if ('navigate' in pencereler[j]) {
                    return pencereler[j].navigate(hedef).then(function (p) { return p && p.focus(); });
                }
            }
            return self.clients.openWindow(hedef);
        })
    );
});
