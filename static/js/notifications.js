(function () {
    "use strict";

    async function markRead(id) {
        await fetch(`/api/notifications/${id}/read/`, {
            method: "POST",
            headers: { "X-CSRFToken": window.DWU.getCsrfToken() },
        });
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    async function load() {
        const list = document.getElementById("notifications-list");
        try {
            const res = await fetch("/api/notifications/?unread=1");
            const data = await res.json();
            const results = data.results.slice(0, 5);
            if (!results.length) {
                list.innerHTML = "<li><em>Aucune nouvelle notification.</em></li>";
                return;
            }
            list.innerHTML = results.map((n) => `
                <li class="my-date-item ${n.is_read ? "" : "unread"}" data-id="${n.id}" data-link="${n.link || ""}" style="cursor:pointer;">
                    <div class="my-date-info">
                        <strong>${escapeHtml(n.title)}</strong>
                        ${n.message ? `<span class="my-date-meta">${escapeHtml(n.message)}</span>` : ""}
                    </div>
                </li>
            `).join("");
            list.querySelectorAll("li[data-id]").forEach((li) => {
                li.addEventListener("click", () => {
                    markRead(li.dataset.id);
                    if (li.dataset.link) window.location.href = li.dataset.link;
                });
            });
        } catch (e) {
            list.innerHTML = "<li><em>Impossible de charger tes notifications.</em></li>";
        }
    }

    load();
})();
