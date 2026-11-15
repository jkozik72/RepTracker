// RepTracker's service worker: what makes the site installable as an app (D9).
// It never caches data, videos or pictures (those always come from the server, so they are current).
// It only keeps a small "can't reach RepTracker" page for when the phone is away from home or the Pi is off.
const CACHE = "reptracker-v1";
const OFFLINE = "/static/offline.html";

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll([OFFLINE, "/static/icons/icon-192.png"])));
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener("fetch", event => {
  if (event.request.mode !== "navigate") return;   // everything but page loads goes straight to the server
  event.respondWith(fetch(event.request).catch(() => caches.match(OFFLINE)));
});
