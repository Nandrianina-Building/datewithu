(function () {
    "use strict";

    const list = document.getElementById("inbox-list");
    if (!list) return;
    const icon = (name) => (window.DWU.icon ? window.DWU.icon(name) : "");

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    function timeAgo(iso) {
        const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
        if (minutes < 1) return "à l'instant";
        if (minutes < 60) return `il y a ${minutes} min`;
        const hours = Math.round(minutes / 60);
        if (hours < 24) return `il y a ${hours} h`;
        return `il y a ${Math.round(hours / 24)} j`;
    }

    async function load() {
        try {
            const res = await fetch("/api/messages/");
            const items = await res.json();
            if (!items.length) {
                list.innerHTML = `<p class="mydates-empty"><em>Pas encore de conversation. Propose un rendez-vous ou publie une idée sur <a href="/fil/">le fil</a> pour commencer à discuter.</em></p>`;
                return;
            }
            list.innerHTML = items.map((item) => `
                <a href="${item.url || '#'}" class="inbox-row ${item.unread ? 'unread' : ''}">
                    ${item.other_avatar_url
                        ? `<img src="${item.other_avatar_url}" alt="" class="inbox-row-avatar">`
                        : `<div class="feed-post-avatar">${escapeHtml((item.other_name || "?")[0]?.toUpperCase() || "?")}</div>`}
                    <div class="inbox-row-body">
                        <div class="inbox-row-top">
                            <strong>${escapeHtml(item.other_name || "Sans nom")}</strong>
                            <span class="inbox-row-time">${timeAgo(item.last_at)}</span>
                        </div>
                        <span class="place-chip" style="margin:0.2rem 0;">${escapeHtml(item.label)}</span>
                        <p class="inbox-row-preview">${escapeHtml(item.title)}${item.last_message ? ` — ${escapeHtml(item.last_message)}` : ""}</p>
                    </div>
                    ${item.unread ? `<span class="notif-dot" aria-hidden="true"></span>` : ""}
                </a>
            `).join("");
        } catch (e) {
            list.innerHTML = "<p><em>Impossible de charger tes messages.</em></p>";
        }
    }

    load();
})();
