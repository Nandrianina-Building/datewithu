(function () {
    "use strict";

    const list = document.getElementById("blocked-users-list");
    if (!list) return;

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    async function unblock(userId, li) {
        try {
            await fetch(`/api/safety/block/${userId}/`, {
                method: "DELETE",
                headers: { "X-CSRFToken": window.DWU.getCsrfToken() },
            });
            li.remove();
            if (!list.children.length) {
                list.innerHTML = "<li><em>Aucun compte bloqué.</em></li>";
            }
        } catch (e) {
            // silencieux
        }
    }

    async function load() {
        try {
            const res = await fetch("/api/safety/blocked/");
            const blocked = await res.json();
            if (!blocked.length) {
                list.innerHTML = "<li><em>Aucun compte bloqué.</em></li>";
                return;
            }
            list.innerHTML = "";
            blocked.forEach((b) => {
                const li = document.createElement("li");
                li.className = "my-date-item";
                li.innerHTML = `
                    <span>${escapeHtml(b.name)}</span>
                    <button type="button" class="link-btn">Débloquer</button>
                `;
                li.querySelector("button").addEventListener("click", () => unblock(b.id, li));
                list.appendChild(li);
            });
        } catch (e) {
            list.innerHTML = "<li><em>Impossible de charger la liste.</em></li>";
        }
    }

    load();
})();
