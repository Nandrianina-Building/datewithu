/**
 * Alimente les compteurs de la ligne de stats du profil (façon Instagram :
 * "X rendez-vous", "X favoris"), en réutilisant les endpoints déjà
 * existants plutôt que d'en créer un dédié.
 */
(function () {
    "use strict";

    const datesEl = document.getElementById("stat-dates");
    const favEl = document.getElementById("stat-favorites");
    if (!datesEl && !favEl) return;

    async function count(url, el) {
        if (!el) return;
        try {
            const res = await fetch(url);
            const data = await res.json();
            const items = Array.isArray(data) ? data : (data.results || []);
            el.textContent = items.length;
        } catch (e) {
            el.textContent = "—";
        }
    }

    count("/api/my-dates/", datesEl);
    count("/api/favorites/", favEl);
})();
