/**
 * Modale de détails d'un lieu — partagée entre la page Explorer et la Carte.
 * Consomme GET /api/places/<id>/ (PlaceDetailSerializer) et
 * GET/POST /api/places/<id>/reviews/.
 */
window.DWU = window.DWU || {};

(function (ns) {
    "use strict";

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    function closeModal() {
        const overlay = document.getElementById("dwu-modal-overlay");
        if (overlay) overlay.remove();
        document.removeEventListener("keydown", onEscape);
    }

    function onEscape(e) {
        if (e.key === "Escape") closeModal();
    }

    function formatPrice(place) {
        if (!place.price_min && !place.price_max) return null;
        if (place.price_min && place.price_max) return `${place.price_min} — ${place.price_max} MGA`;
        return `${place.price_min || place.price_max} MGA`;
    }

    async function loadReviews(placeId, panel) {
        panel.innerHTML = "<p><em>Chargement des avis...</em></p>";
        try {
            const res = await fetch(`/api/places/${placeId}/reviews/`);
            if (!res.ok) throw new Error("reviews unavailable");
            const reviews = await res.json();
            const list = reviews.length
                ? reviews.map((r) => `<li class="review-item"><div class="review-item-head"><span class="review-stars" aria-label="${r.rating} étoiles sur 5">${"\u2605".repeat(r.rating)}${"\u2606".repeat(5 - r.rating)}</span><strong>${escapeHtml(r.user)}</strong></div>${r.comment ? `<p>${escapeHtml(r.comment)}</p>` : ""}${r.owner_reply ? `<div class="owner-reply"><strong>Réponse du gérant :</strong> ${escapeHtml(r.owner_reply)}</div>` : ""}</li>`).join("")
                : "<li><em>Aucun avis pour l'instant, sois le premier !</em></li>";
            panel.innerHTML = `
                <ul class="reviews-list">${list}</ul>
                <form class="review-form">
                    <fieldset class="review-rating-group">
                        <legend>Ta note</legend>
                        <div class="star-picker" role="radiogroup" aria-label="Choisir une note sur 5">
                            ${[5, 4, 3, 2, 1].map((rating) => `<label class="star-option"><input type="radio" name="rating" value="${rating}"${rating === 5 ? " checked" : ""}><span aria-hidden="true">★</span><span class="sr-only">${rating} étoile${rating > 1 ? "s" : ""}</span></label>`).join("")}
                        </div>
                    </fieldset>
                    <label class="review-comment-label" for="review-comment-${placeId}">Ton expérience <span>(optionnel)</span></label>
                    <textarea id="review-comment-${placeId}" class="review-comment" rows="3" maxlength="500" placeholder="Qu'est-ce qui t'a plu dans ce lieu ?"></textarea>
                    <div class="review-form-footer">
                        <p class="review-form-status" role="status" aria-live="polite"></p>
                        <button type="submit" class="btn btn-primary">Publier mon avis</button>
                    </div>
                </form>
            `;
            panel.querySelector(".review-form").addEventListener("submit", async (e) => {
                e.preventDefault();
                const form = e.currentTarget;
                const button = form.querySelector("button[type=submit]");
                const status = form.querySelector(".review-form-status");
                button.disabled = true;
                status.textContent = "Publication en cours...";
                try {
                    const response = await fetch(`/api/places/${placeId}/reviews/`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": ns.getCsrfToken(),
                        },
                        body: JSON.stringify({
                            rating: form.querySelector("input[name=rating]:checked").value,
                            comment: form.querySelector(".review-comment").value.trim(),
                        }),
                    });
                    if (response.status === 401 || response.status === 403) {
                        throw new Error("Connecte-toi pour publier un avis.");
                    }
                    if (!response.ok) throw new Error("Impossible de publier cet avis.");
                    loadReviews(placeId, panel);
                } catch (error) {
                    status.textContent = error.message;
                    button.disabled = false;
                }
            });
        } catch (e) {
            panel.innerHTML = "<p><em>Impossible de charger les avis.</em></p>";
        }
    }

    ns.openPlaceDetail = async function openPlaceDetail(placeId) {
        closeModal();

        const overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.id = "dwu-modal-overlay";
        overlay.innerHTML = `<div class="modal-panel"><p style="padding:2rem;text-align:center;"><em>Chargement...</em></p></div>`;
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) closeModal();
        });
        document.body.appendChild(overlay);
        document.addEventListener("keydown", onEscape);

        try {
            const res = await fetch(`/api/places/${placeId}/`);
            if (!res.ok) throw new Error("not found");
            const place = await res.json();

            const gallery = (place.gallery || []).slice(0, 3);
            const mainImage = place.main_image || (gallery[0] && gallery[0].image);
            const sideImages = gallery.slice(0, 2);

            const price = formatPrice(place);
            const mapsUrl = place.latitude && place.longitude
                ? `https://www.openstreetmap.org/?mlat=${place.latitude}&mlon=${place.longitude}#map=17/${place.latitude}/${place.longitude}`
                : null;

            const panel = overlay.querySelector(".modal-panel");
            panel.innerHTML = `
                <button class="modal-close" id="dwu-modal-close" aria-label="Fermer">
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M6 6l12 12"/><path d="M18 6 6 18"/></svg>
                </button>
                ${mainImage ? `
                <div class="modal-gallery">
                    <img src="${mainImage}" alt="${escapeHtml(place.name)}">
                    ${sideImages.length ? `<div class="gallery-side">${sideImages.map((g) => `<img src="${g.image}" alt="">`).join("")}</div>` : ""}
                </div>` : ""}
                <div class="modal-body">
                    <h2 style="margin-bottom:0.3rem;">${escapeHtml(place.name)}</h2>
                    <div class="place-meta-row">
                        ${place.category ? `<span class="place-chip">${escapeHtml(place.category.name || place.category)}</span>` : ""}
                        ${place.city ? `<span class="place-chip">${window.DWU.icon ? window.DWU.icon("map-pin") : ""} ${escapeHtml(place.city.name || place.city)}</span>` : ""}
                        ${place.rating ? `<span class="place-chip place-chip-rating">★ ${place.rating}</span>` : ""}
                    </div>
                    ${place.full_description || place.short_description ? `<p>${escapeHtml(place.full_description || place.short_description)}</p>` : ""}

                    <div class="place-info-grid">
                        ${place.address ? `<div class="place-info-item"><svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 21s7-6.1 7-12a7 7 0 1 0-14 0c0 5.9 7 12 7 12Z"/><circle cx="12" cy="9" r="2.5"/></svg><span>${escapeHtml(place.address)}${place.neighborhood ? `, ${escapeHtml(place.neighborhood)}` : ""}</span></div>` : ""}
                        ${place.opening_hours ? `<div class="place-info-item"><svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/></svg><span>${escapeHtml(place.opening_hours)}</span></div>` : ""}
                        ${place.phone ? `<div class="place-info-item"><svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6.6 10.8c1.4 2.8 3.8 5.2 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.4c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.4 0 .8-.2 1L6.6 10.8Z"/></svg><a href="tel:${escapeHtml(place.phone)}">${escapeHtml(place.phone)}</a></div>` : ""}
                        ${price ? `<div class="place-info-item"><svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7v10M9.5 9.5c0-1 .8-2 2.5-2s2.5.9 2.5 2c0 2.5-5 1.8-5 4.3 0 1.1 1 2.2 2.5 2.2s2.5-1 2.5-2"/></svg><span>${price}</span></div>` : ""}
                        ${place.website ? `<div class="place-info-item"><svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c2.5 2.5 4 5.8 4 9s-1.5 6.5-4 9c-2.5-2.5-4-5.8-4-9s1.5-6.5 4-9Z"/></svg><a href="${escapeHtml(place.website)}" target="_blank" rel="noopener">Site web</a></div>` : ""}
                        ${mapsUrl ? `<div class="place-info-item"><svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 3 3 5.5v15L9 18l6 2.5 6-2.5v-15L15 5.5 9 3Z"/></svg><a href="${mapsUrl}" target="_blank" rel="noopener">Voir sur la carte</a></div>` : ""}
                    </div>

                    <h3 style="font-size:1rem;">Avis</h3>
                    <div class="place-reviews-panel"></div>

                    <p style="margin-top:1rem;">
                        <a href="/partenaires/revendiquer/${place.id}/" style="font-size:0.8rem;color:var(--ink-soft);">
                            Ce lieu est le vôtre ? Revendiquez la fiche →
                        </a>
                    </p>
                </div>
            `;
            panel.querySelector("#dwu-modal-close").addEventListener("click", closeModal);
            loadReviews(place.id, panel.querySelector(".place-reviews-panel"));
        } catch (e) {
            overlay.querySelector(".modal-panel").innerHTML = `
                <button class="modal-close" id="dwu-modal-close" aria-label="Fermer">&times;</button>
                <p style="padding:2rem;text-align:center;">Impossible de charger ce lieu.</p>
            `;
            overlay.querySelector("#dwu-modal-close").addEventListener("click", closeModal);
        }
    };
})(window.DWU);
