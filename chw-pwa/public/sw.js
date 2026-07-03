const CACHE_NAME = "chw-pwa-shell-v1";
const APP_SHELL = ["/", "/index.html"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

// Cache-first for the app shell so it loads offline; everything else
// (GraphQL/webhook calls) goes straight to the network -- we never want to
// serve a stale API response as if it were live data.
self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  event.respondWith(
    caches.match(request).then((cached) => cached || fetch(request).catch(() => caches.match("/index.html"))),
  );
});

// Best-effort only: the Background Sync API isn't supported in all browsers
// (notably Safari), so this is a bonus path, not the primary sync mechanism.
// The app's own `online` event listener and manual "Retry Sync" button (see
// SyncStatus.jsx) are what the live demo actually relies on -- they work in
// every browser, which matters more for a demo than API completeness.
self.addEventListener("sync", (event) => {
  if (event.tag === "chw-sync") {
    event.waitUntil(
      self.clients.matchAll().then((clients) => {
        clients.forEach((client) => client.postMessage({ type: "TRIGGER_SYNC" }));
      }),
    );
  }
});
