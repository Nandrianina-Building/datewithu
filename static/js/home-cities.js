/**
 * Section "villes" de la page d'accueil : on affiche un nombre limité de
 * villes au chargement (voir home_view), et un bouton « Voir plus »
 * charge la suite en AJAX via /api/cities/ plutôt que de tout envoyer
 * d'un bloc ou de recharger la page.
 */
(function () {
    "use strict";

    const btn = document.getElementById("cities-more-btn");
    const list = document.getElementById("city-scroll-list");
    if (!btn || !list) return;

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    function cityTile(city) {
        const a = document.createElement("a");
        a.href = `/explore/?city=${encodeURIComponent(city.slug)}`;
        a.className = "city-tile";
        const img = city.image || `https://picsum.photos/seed/dwu-city-${city.slug}/600/500`;
        a.innerHTML = `
            <img src="${img}" alt="${escapeHtml(city.name)}">
            <div class="city-tile-overlay">
                <div>
                    <h3>${escapeHtml(city.name)}</h3>
                    ${city.region ? `<span>${escapeHtml(city.region)}</span>` : ""}
                </div>
            </div>
        `;
        return a;
    }

    btn.addEventListener("click", async () => {
        const nextPage = parseInt(btn.dataset.page, 10) + 1;
        btn.disabled = true;
        const originalText = btn.textContent;
        btn.textContent = "Chargement...";
        try {
            const res = await fetch(`/api/cities/?page=${nextPage}`);
            const data = await res.json();
            const results = data.results || data || [];
            results.forEach((city) => list.appendChild(cityTile(city)));
            btn.dataset.page = String(nextPage);
            if (!data.next) {
                btn.remove();
            } else {
                btn.disabled = false;
                btn.textContent = originalText;
            }
        } catch (e) {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    });
})();
