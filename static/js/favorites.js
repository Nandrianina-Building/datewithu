(function () {
    "use strict";

    const icon = (name) => (window.DWU.icon ? window.DWU.icon(name) : "");

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    async function load() {
        const list = document.getElementById("favorites-list");
        try {
            const res = await fetch("/api/favorites/");
            const data = await res.json();
            const items = [
                ...(data.places || []).map((p) => `${icon("map-pin")} ${escapeHtml(p.name)}${p.city ? ` (${escapeHtml(p.city)})` : ""}`),
                ...(data.activities || []).map((a) => `${icon("target")} ${escapeHtml(a.name)}`),
            ];
            list.innerHTML = items.length
                ? items.map((t) => `<li class="my-date-item">${t}</li>`).join("")
                : "<li><em>Aucun favori pour l'instant.</em></li>";
        } catch (e) {
            list.innerHTML = "<li><em>Impossible de charger tes favoris.</em></li>";
        }
    }

    load();
})();
