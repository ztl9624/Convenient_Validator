const CACHE_NAME = 'totp-manager-cache-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  // jsOTP 脚本
  'https://cdnjs.cloudflare.com/ajax/libs/jsOTP/2.0.0/jsOTP.min.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(urlsToCache);
    })
  );
  self.skipWaiting();
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request);
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(key => key !== CACHE_NAME)
        .map(key => caches.delete(key)))
    )
  );
  self.clients.claim();
});
