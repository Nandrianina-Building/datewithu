(function () {
    "use strict";

    const app = document.getElementById("explore-app");
    const pagination = document.getElementById("explore-pagination");
    const isAuthenticated = app.dataset.authenticated === "true";
    let searchTimer = null;
    let currentPage = 1;

    const searchInput = document.getElementById("explore-search");

    function truncate(str, maxLength) {
        return window.DWU.truncate ? window.DWU.truncate(str, maxLength) : (str || "");
    }

    function getCookie(name) {
        const match = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]+)"));
        return match ? decodeURIComponent(match[2]) : null;
    }

    function getCsrfToken() {
        const token = app.dataset.csrfToken
            || document.querySelector("[name=csrfmiddlewaretoken]")?.value
            || getCookie("csrftoken")
            || "";
        return token.trim();
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    async function toggleFavorite(placeId, btn) {
        if (!isAuthenticated) return;
        btn.disabled = true;
        try {
            const csrfToken = getCsrfToken();
            if (![32, 64].includes(csrfToken.length)) {
                throw new Error("Session CSRF invalide. Recharge la page et reconnecte-toi.");
            }
            const res = await fetch(`/api/favorites/places/${placeId}/toggle/`, {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken },
                credentials: "same-origin",
            });
            const data = await res.json();
            if (!res.ok) {
                throw new Error(res.status === 403 ? "Connecte-toi pour ajouter un favori." : (data.detail || "Impossible de modifier ce favori."));
            }
            btn.textContent = data.favorited ? "\u2665" : "\u2661";
            btn.classList.toggle("favorited", data.favorited);
        } catch (error) {
            btn.title = error.message;
            btn.classList.add("favorite-error");
        } finally {
            btn.disabled = false;
        }
    }

    async function loadFilters() {
        try {
            const [citiesRes, categoriesRes] = await Promise.all([
                fetch("/api/cities/"),
                fetch("/api/categories/"),
            ]);
            const cities = await citiesRes.json();
            const categories = await categoriesRes.json();
            const citySelect = document.getElementById("explore-filter-city");
            const categorySelect = document.getElementById("explore-filter-category");
            (cities.results || cities).forEach((c) => {
                citySelect.insertAdjacentHTML("beforeend", `<option value="${c.id}">${escapeHtml(c.name)}</option>`);
            });
            (categories.results || categories).forEach((c) => {
                categorySelect.insertAdjacentHTML("beforeend", `<option value="${c.id}">${escapeHtml(c.name)}</option>`);
            });
        } catch (e) {
            // non bloquant
        }
    }

    async function load(page) {
        currentPage = page || 1;
        const params = new URLSearchParams();
        const search = searchInput.value.trim();
        const city = document.getElementById("explore-filter-city").value;
        const category = document.getElementById("explore-filter-category").value;
        if (search) params.set("search", search);
        if (city) params.set("city", city);
        if (category) params.set("category", category);
        params.set("page", String(currentPage));

        app.innerHTML = "<p><em>Chargement...</em></p>";
        pagination.innerHTML = "";
        const favoriteRequest = isAuthenticated
            ? fetch("/api/favorites/")
            : Promise.resolve({ ok: true, json: async () => ({ places: [] }) });
        const [placesRes, favoritesRes] = await Promise.all([
            fetch(`/api/places/?${params.toString()}`),
            favoriteRequest,
        ]);
        if (!placesRes.ok) throw new Error("Impossible de charger les lieux.");
        if (!favoritesRes.ok && isAuthenticated) throw new Error("Impossible de charger tes favoris.");
        const places = await placesRes.json();
        const favorites = await favoritesRes.json();
        const favoriteIds = new Set((favorites.places || []).map((p) => p.id));

        const list = places.results || places;
        if (!list.length) {
            app.innerHTML = "<p><em>Aucun lieu ne correspond à ces critères.</em></p>";
            return;
        }

        app.innerHTML = "";
        list.forEach((place) => {
            const card = document.createElement("div");
            card.className = "place-card";
            const isFav = favoriteIds.has(place.id);
            card.innerHTML = `
                ${place.main_image
                    ? `<img src="${place.main_image}" alt="${escapeHtml(place.name)}" class="place-card-media">`
                    : `<img src="https://picsum.photos/seed/dwu-place-${place.id}/500/400" alt="" class="place-card-media">`}
                <button class="fav-btn ${isFav ? "favorited" : ""}" data-id="${place.id}" ${isAuthenticated ? "" : "disabled title=\"Connecte-toi pour ajouter ce lieu à tes favoris\""}>${isFav ? "\u2665" : "\u2661"}</button>
                <div class="place-card-body">
                    <h3 style="margin-bottom:0.2rem;">${escapeHtml(place.name)}</h3>
                    <p style="margin-bottom:0.4rem;font-size:0.85rem;">${escapeHtml(place.city || "")}${place.city && place.category ? " · " : ""}${escapeHtml(place.category || "")}</p>
                    <p style="font-size:0.88rem;">${escapeHtml(truncate(place.short_description, 90))}</p>
                    <p style="font-size:0.85rem;">${place.rating ? `★ ${place.rating}` : "Pas encore noté"}</p>
                    <button class="btn btn-primary place-detail-btn" style="width:100%;margin-top:0.4rem;" data-id="${place.id}">Voir détails</button>
                </div>
            `;
            card.querySelector(".fav-btn").addEventListener("click", (e) => {
                e.stopPropagation();
                toggleFavorite(place.id, e.currentTarget);
            });
            card.querySelector(".place-detail-btn").addEventListener("click", () => {
                window.DWU.openPlaceDetail(place.id);
            });
            app.appendChild(card);
        });

        renderPagination(places);
    }

    function renderPagination(places) {
        pagination.innerHTML = "";
        if (!places.next && !places.previous) return; // une seule page : rien à afficher
        const totalPages = places.count ? Math.ceil(places.count / 10) : currentPage;
        pagination.innerHTML = `
            <button type="button" class="btn" id="explore-prev" ${places.previous ? "" : "disabled"}>← Précédent</button>
            <span class="explore-pagination-status">Page ${currentPage} / ${totalPages}</span>
            <button type="button" class="btn" id="explore-next" ${places.next ? "" : "disabled"}>Suivant →</button>
        `;
        // On ne touche à AUCUN champ de recherche/filtre ici : `load()` les
        // relit tels quels depuis le DOM, donc Suivant/Précédent ne changent
        // que la page, jamais la recherche ou les filtres en cours.
        document.getElementById("explore-prev")?.addEventListener("click", () => load(currentPage - 1));
        document.getElementById("explore-next")?.addEventListener("click", () => load(currentPage + 1));
    }

    searchInput.addEventListener("input", () => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => load(1), 350);
    });
    document.getElementById("explore-filter-city").addEventListener("change", () => load(1));
    document.getElementById("explore-filter-category").addEventListener("change", () => load(1));

    loadFilters();
    load(1);
})();
