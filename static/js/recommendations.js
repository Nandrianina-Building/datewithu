(function () {
    "use strict";

    const grid = document.getElementById("recommendations-grid");
    if (!grid) return;

    const icon = (name) => (window.DWU.icon ? window.DWU.icon(name) : "");

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    async function load() {
        try {
            const res = await fetch("/recommandations/");
            const data = await res.json();
            const places = data.results || [];
            if (!places.length) {
                grid.innerHTML = "<p><em>Explore quelques lieux pour débloquer des recommandations personnalisées.</em></p>";
                return;
            }
            grid.innerHTML = places.map((p) => `
                <div class="mydate-card">
                    <div class="mydate-cover" style="background-image:url('${p.main_image || `https://picsum.photos/seed/dwu-reco-${p.id}/500/400`}');"></div>
                    <div class="mydate-body">
                        <h3>${escapeHtml(p.name)}</h3>
                        <p class="mydate-meta">${icon("map-pin")} ${escapeHtml(p.city || "")}${p.category ? ` · ${escapeHtml(p.category)}` : ""}</p>
                        <p class="mydate-meta">★ ${p.rating}/5</p>
                        <div class="mydate-actions">
                            <a class="btn btn-primary" href="/explore/">${icon("eye")} Découvrir</a>
                        </div>
                    </div>
                </div>
            `).join("");
        } catch (e) {
            grid.innerHTML = "<p><em>Impossible de charger les recommandations.</em></p>";
        }
    }

    load();
})();
