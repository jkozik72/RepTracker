// RepTracker's service worker: what makes the site installable as an app (D9).
// It never caches data, videos or pictures (those always come from the server, so they are current).
// It only keeps a small "can't reach RepTracker" page for when the phone is away from home or the Pi is off.
const CACHE = "reptracker-v2";
const OFFLINE = "/static/offline.html";

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll([OFFLINE, "/static/icons/icon-192.png"])));
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});

// Alerts from the server (D10): the notification reads the animal's new alerts. Tapping it opens that animal.
self.addEventListener("push", event => {
  let d = {};
  try { d = event.data ? event.data.json() : {}; } catch { d = { body: event.data && event.data.text() }; }
  event.waitUntil(self.registration.showNotification(d.title || "RepTracker", {
    body: d.body || "", tag: d.tag || undefined, renotify: !!d.tag, icon: "/static/icons/icon-192.png",
    badge: "/static/icons/badge-96.png", data: { url: d.url || "/" },
  }));
});

self.addEventListener("notificationclick", event => {
  event.notification.close();
  const url = new URL(event.notification.data?.url || "/", self.location.origin).href;
  event.waitUntil(clients.matchAll({ type: "window", includeUncontrolled: true }).then(windows => {
    const open = windows.find(w => w.url.startsWith(self.location.origin));
    if (open) return open.navigate(url).then(w => (w || open).focus());
    return clients.openWindow(url);
  }));
});

self.addEventListener("fetch", event => {
  if (event.request.mode !== "navigate") return;   // everything but page loads goes straight to the server
  event.respondWith(fetch(event.request).catch(() => caches.match(OFFLINE)));
});
