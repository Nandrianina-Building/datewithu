const CACHE_NAME = "datewithu-v1";
const APP_SHELL = [
    "/static/css/main.css",
    "/static/icons/icon.svg",
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
    );
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
        )
    );
    self.clients.claim();
});

// Stratégie "network first" : toujours essayer le réseau (les pages sont
// dynamiques), et retomber sur le cache uniquement pour l'app shell si
// hors-ligne. On ne met JAMAIS en cache les appels /api/ pour ne pas
// afficher de données obsolètes (rendez-vous, chat, notifications...).
self.addEventListener("fetch", (event) => {
    const url = new URL(event.request.url);
    if (url.pathname.startsWith("/api/")) return;

    event.respondWith(
        fetch(event.request).catch(() => caches.match(event.request))
    );
});
