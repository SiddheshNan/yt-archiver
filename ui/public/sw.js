// Service Worker for YT Archiver PWA
// Minimal SW — required for PWA installability on some browsers.
// Uses network-first strategy so the app always loads fresh content.

const CACHE_NAME = "yt-archiver-v1";

// Pre-cache only the app shell on install
self.addEventListener("install", (event) => {
  self.skipWaiting();
});

// Clean up old caches on activate
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(
        names
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      )
    )
  );
  self.clients.claim();
});

// Network-first: always try network, fall back to cache for offline shell
self.addEventListener("fetch", (event) => {
  // Skip non-GET and API/stream requests
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/api/")) return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Cache successful navigations and static assets
        if (response.ok && (event.request.mode === "navigate" || url.pathname.match(/\.(js|css|png|ico|woff2?)$/))) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
