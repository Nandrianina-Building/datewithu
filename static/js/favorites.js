(function () {
    "use strict";

    const icon = (name) => (window.DWU.icon ? window.DWU.icon(name) : "");

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    async function removeFavorite(button, list) {
        const { kind, id } = button.dataset;
        button.disabled = true;
        try {
            const response = await fetch(`/api/favorites/${kind}s/${id}/toggle/`, {
                method: "POST",
                headers: { "X-CSRFToken": window.DWU.getCsrfToken() },
            });
            if (!response.ok) throw new Error("Impossible de retirer ce favori.");

            const result = await response.json();
            if (result.favorited) throw new Error("Le favori n'a pas pu être retiré.");

            button.closest(".favorite-item").remove();
            if (!list.querySelector(".favorite-item")) {
                list.innerHTML = "<li><em>Aucun favori pour l'instant.</em></li>";
            }
        } catch (error) {
            button.disabled = false;
            button.title = error.message;
        }
    }

    async function load() {
        const list = document.getElementById("favorites-list");
        try {
            const res = await fetch("/api/favorites/");
            const data = await res.json();
            const items = [
                ...(data.places || []).map((place) => ({ kind: "place", id: place.id, icon: "map-pin", name: escapeHtml(place.name), detail: escapeHtml(place.city || "") })),
                ...(data.activities || []).map((activity) => ({ kind: "activity", id: activity.id, icon: "target", name: escapeHtml(activity.name), detail: escapeHtml(activity.city || activity.place || "") })),
            ];
            list.innerHTML = items.length
                ? items.map((item) => `
                    <li class="favorite-item">
                        ${item.kind === "place"
                            ? `<button type="button" class="favorite-item-open" data-place-id="${item.id}" aria-label="Voir le détail du lieu favori">`
                            : `<div class="favorite-item-open">`}
                            <span class="favorite-item-icon">${icon(item.icon)}</span>
                            <span class="favorite-item-copy"><strong>${item.name}</strong>${item.detail ? `<small>${item.detail}</small>` : ""}</span>
                        ${item.kind === "place" ? "</button>" : "</div>"}
                        <button type="button" class="favorite-remove" data-kind="${item.kind}" data-id="${item.id}" aria-label="Retirer des favoris" title="Retirer des favoris">${icon("x-circle")}</button>
                    </li>
                `).join("")
                : "<li><em>Aucun favori pour l'instant.</em></li>";

            list.querySelectorAll("[data-place-id]").forEach((button) => {
                button.addEventListener("click", () => window.DWU.openPlaceDetail(Number(button.dataset.placeId)));
            });
            list.querySelectorAll(".favorite-remove").forEach((button) => {
                button.addEventListener("click", () => removeFavorite(button, list));
            });
        } catch (e) {
            list.innerHTML = "<li><em>Impossible de charger tes favoris.</em></li>";
        }
    }

    load();
})();
