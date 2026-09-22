(function () {
    "use strict";

    const app = document.getElementById("packages-app");
    const icon = (name) => (window.DWU.icon ? window.DWU.icon(name) : "");
    let packagesById = {};

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    function truncate(str, maxLength) {
        // Toutes les cartes doivent garder la même hauteur : on tronque
        // systématiquement à une longueur fixe pour ne jamais casser
        // l'alignement de la grille avec une carte plus haute que les autres.
        if (!str) return "";
        return str.length > maxLength ? `${str.slice(0, maxLength - 1).trimEnd()}…` : str;
    }

    function formatPrice(amount) {
        if (!amount) return "";
        return `${amount.toLocaleString("fr-FR")} Ar`;
    }

    async function usePackage(id) {
        const res = await fetch(`/api/packages/${id}/use/`, {
            method: "POST",
            headers: { "X-CSRFToken": window.DWU.getCsrfToken() },
        });
        const data = await res.json();
        if (!res.ok) {
            alert(data.detail || "Une erreur est survenue.");
            return;
        }
        window.location.href = `/date-builder/?plan=${data.plan.id}`;
    }

    function closeDetail() {
        document.getElementById("dwu-package-overlay")?.remove();
    }

    function openDetail(pkg) {
        closeDetail();
        const overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.id = "dwu-package-overlay";
        overlay.addEventListener("click", (e) => { if (e.target === overlay) closeDetail(); });

        const place = pkg.place;
        const activity = pkg.activity;
        const budgetLabel = pkg.budget ? pkg.budget.label : "";

        overlay.innerHTML = `
            <div class="modal-panel" style="max-width:640px;">
                <button class="modal-close" id="dwu-package-close" aria-label="Fermer">${icon("x-circle")}</button>
                <img src="${pkg.image || `https://picsum.photos/seed/dwu-package-${pkg.id}/900/400`}" alt="${escapeHtml(pkg.name)}" style="width:100%;height:220px;object-fit:cover;border-radius:var(--radius-lg) var(--radius-lg) 0 0;">
                <div class="modal-body">
                    ${pkg.is_featured ? '<span class="badge-featured">Coup de cœur</span>' : ""}
                    <h2 style="margin:0.4rem 0 0.3rem;">${escapeHtml(pkg.name)}</h2>
                    <div class="place-meta-row">
                        ${pkg.city ? `<span class="place-chip">${icon("map-pin")} ${escapeHtml(pkg.city.name)}</span>` : ""}
                        ${pkg.mood ? `<span class="place-chip">${escapeHtml(pkg.mood.name)}</span>` : ""}
                        ${budgetLabel ? `<span class="place-chip place-chip-rating">${escapeHtml(budgetLabel)}</span>` : ""}
                    </div>
                    ${pkg.description ? `<p>${escapeHtml(pkg.description)}</p>` : ""}

                    <div class="place-info-grid">
                        ${place ? `
                            <div class="place-info-item">
                                ${icon("map-pin")}
                                <span><strong>${escapeHtml(place.name)}</strong>${place.short_description ? ` — ${escapeHtml(place.short_description)}` : ""}${place.rating ? ` · ★ ${place.rating}` : ""}</span>
                            </div>
                        ` : ""}
                        ${activity ? `
                            <div class="place-info-item">
                                ${icon("target")}
                                <span><strong>${escapeHtml(activity.name)}</strong>${activity.duration_minutes ? ` — ${activity.duration_minutes} min` : ""}${activity.description ? ` · ${escapeHtml(activity.description)}` : ""}</span>
                            </div>
                        ` : ""}
                        ${pkg.price_estimate ? `
                            <div class="place-info-item">
                                ${icon("check-circle")}
                                <span>Budget estimé : <strong>${formatPrice(pkg.price_estimate)}</strong></span>
                            </div>
                        ` : ""}
                    </div>

                    <button class="btn btn-primary use-package-btn" style="width:100%;margin-top:0.6rem;">
                        ${icon("check-circle")} Utiliser ce package
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        overlay.querySelector("#dwu-package-close").addEventListener("click", closeDetail);
        overlay.querySelector(".use-package-btn").addEventListener("click", () => usePackage(pkg.id));
    }

    async function load() {
        try {
            const res = await fetch("/api/packages/");
            const data = await res.json();
            const list = data.results || data;
            if (!list.length) {
                app.innerHTML = "<p><em>Aucun package pour l'instant — ajoutes-en depuis le Django Admin.</em></p>";
                return;
            }
            packagesById = Object.fromEntries(list.map((p) => [p.id, p]));
            app.innerHTML = "";
            list.forEach((pkg) => {
                const card = document.createElement("div");
                card.className = "place-card";
                const cityName = pkg.city ? pkg.city.name : "";
                const moodLabel = pkg.mood ? pkg.mood.name : "";
                card.innerHTML = `
                    <img src="${pkg.image || `https://picsum.photos/seed/dwu-package-${pkg.id}/500/400`}" alt="${escapeHtml(pkg.name)}" class="place-card-media">
                    <div class="place-card-body">
                        ${pkg.is_featured ? '<span class="badge-featured">Coup de cœur</span>' : ""}
                        <h3 style="margin-bottom:0.2rem;">${escapeHtml(truncate(pkg.name, 45))}</h3>
                        <p style="margin-bottom:0.4rem;font-size:0.85rem;">${escapeHtml(cityName)}${cityName && moodLabel ? " · " : ""}${escapeHtml(moodLabel)}</p>
                        <p style="font-size:0.88rem;">${escapeHtml(truncate(pkg.description, 90))}</p>
                        <p><strong>${formatPrice(pkg.price_estimate)}</strong></p>
                        <button class="btn btn-primary view-detail-btn" style="width:100%;margin-top:0.4rem;">${icon("eye")} Voir le détail</button>
                    </div>
                `;
                card.querySelector(".view-detail-btn").addEventListener("click", () => openDetail(packagesById[pkg.id]));
                app.appendChild(card);
            });
        } catch (e) {
            app.innerHTML = "<p><em>Impossible de charger les packages.</em></p>";
        }
    }

    load();
})();
