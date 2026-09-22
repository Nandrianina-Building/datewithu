(function () {
    "use strict";

    const list = document.getElementById("requests-list");
    if (!list) return;
    const icon = (name) => (window.DWU.icon ? window.DWU.icon(name) : "");

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    async function respond(interestId, response, row) {
        const res = await fetch(`/api/feed/demandes/${interestId}/repondre/`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": window.DWU.getCsrfToken() },
            body: JSON.stringify({ response }),
        });
        const data = await res.json();
        if (res.ok && response === "accept" && data.conversation_id) {
            window.location.href = `/messages/${data.conversation_id}/`;
            return;
        }
        row.remove();
        if (!list.children.length) {
            list.innerHTML = "<p><em>Aucune demande en attente.</em></p>";
        }
    }

    async function load() {
        try {
            const res = await fetch("/api/feed/demandes-recues/");
            const items = await res.json();
            if (!items.length) {
                list.innerHTML = "<p><em>Aucune demande en attente.</em></p>";
                return;
            }
            list.innerHTML = "";
            items.forEach((item) => {
                const row = document.createElement("div");
                row.className = "inbox-row";
                row.style.cursor = "default";
                row.innerHTML = `
                    <div class="feed-post-avatar">${escapeHtml((item.requester_name || "?")[0].toUpperCase())}</div>
                    <div class="inbox-row-body">
                        <strong><a href="/accounts/u/${item.requester_id}/">${escapeHtml(item.requester_name)}</a></strong>
                        <p class="inbox-row-preview">À propos de : « ${escapeHtml(item.post_caption)} »</p>
                        ${item.message ? `<p class="inbox-row-preview">"${escapeHtml(item.message)}"</p>` : ""}
                    </div>
                    <div style="display:flex;gap:0.5rem;flex-shrink:0;">
                        <button type="button" class="btn btn-primary" data-accept>${icon("check-circle")} Accepter</button>
                        <button type="button" class="btn" data-decline>${icon("x-circle")} Décliner</button>
                    </div>
                `;
                row.querySelector("[data-accept]").addEventListener("click", () => respond(item.id, "accept", row));
                row.querySelector("[data-decline]").addEventListener("click", () => respond(item.id, "decline", row));
                list.appendChild(row);
            });
        } catch (e) {
            list.innerHTML = "<p><em>Impossible de charger les demandes.</em></p>";
        }
    }

    load();
})();
