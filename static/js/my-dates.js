(function () {
    "use strict";

    const icon = (name, cls) => (window.DWU.icon ? window.DWU.icon(name, cls) : "");

    const STATUS_LABELS = {
        pending: "En attente",
        viewed: "Vue",
        accepted: "Acceptée",
        maybe: "Peut-être",
        declined: "Déclinée",
        expired: "Expirée",
        cancelled: "Annulée",
    };

    const STATUS_ICONS = {
        pending: "clock",
        viewed: "eye",
        accepted: "check-circle",
        maybe: "clock",
        declined: "x-circle",
        expired: "clock",
        cancelled: "slash-circle",
    };

    function closeShareModal() {
        const overlay = document.getElementById("dwu-share-overlay");
        if (overlay) overlay.remove();
    }

    async function openShare(token) {
        closeShareModal();
        const overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.id = "dwu-share-overlay";
        overlay.innerHTML = `<div class="modal-panel" style="max-width:520px;"><p style="padding:2rem;text-align:center;"><em>Chargement...</em></p></div>`;
        overlay.addEventListener("click", (e) => { if (e.target === overlay) closeShareModal(); });
        document.body.appendChild(overlay);

        try {
            const res = await fetch(`/api/invitations/${token}/`);
            if (!res.ok) throw new Error("not found");
            const invitation = await res.json();
            const panel = overlay.querySelector(".modal-panel");
            panel.innerHTML = `
                <button class="modal-close" id="dwu-share-close" aria-label="Fermer">${icon("x-circle")}</button>
                <div class="modal-body">
                    <h2 style="margin-bottom:0.8rem;">Partager ce rendez-vous</h2>
                    ${window.DWU.renderShareCard(invitation)}
                </div>
            `;
            window.DWU.bindShareCard(panel);
            panel.querySelector("#dwu-share-close").addEventListener("click", closeShareModal);
        } catch (e) {
            overlay.querySelector(".modal-panel").innerHTML = `
                <button class="modal-close" id="dwu-share-close" aria-label="Fermer">${icon("x-circle")}</button>
                <p style="padding:2rem;text-align:center;">Impossible de charger ce lien.</p>
            `;
            overlay.querySelector("#dwu-share-close").addEventListener("click", closeShareModal);
        }
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    function truncate(str, maxLength) {
        if (!str) return "";
        return str.length > maxLength ? `${str.slice(0, maxLength - 1).trimEnd()}…` : str;
    }

    async function load() {
        const list = document.getElementById("my-dates-list");
        try {
            const res = await fetch("/api/my-dates/");
            const dates = await res.json();
            if (!dates.length) {
                list.innerHTML = "<li><em>Aucun rendez-vous créé pour l'instant.</em></li>";
                return;
            }
            list.innerHTML = dates.map((d) => {
                const where = d.place || d.activity || d.city || "Rendez-vous";
                const when = d.date_value ? `${d.date_value}${d.time_value ? " à " + d.time_value.slice(0, 5) : ""}` : "";
                const statusKey = d.invitation_status;
                const statusLabel = statusKey ? (STATUS_LABELS[statusKey] || statusKey) : "Brouillon d'invitation";
                const statusIcon = icon(statusKey ? (STATUS_ICONS[statusKey] || "clock") : "clock");
                return `
                    <li class="my-date-item">
                        <div class="my-date-info">
                            <strong>${escapeHtml(truncate(where, 50))}</strong>
                            <span class="my-date-meta">${escapeHtml(when)}</span>
                            <span class="my-date-status">${statusIcon} ${statusLabel}</span>
                        </div>
                        <div class="my-date-actions">
                            ${d.invitation_token ? `<button type="button" class="link-btn" data-share="${d.invitation_token}">${icon("qrcode")} Lien / QR</button>` : ""}
                            <a href="/dates/${d.plan_id}/chat/">${icon("message-circle")} Discuter</a>
                        </div>
                    </li>
                `;
            }).join("");
            list.querySelectorAll("[data-share]").forEach((btn) => {
                btn.addEventListener("click", () => openShare(btn.dataset.share));
            });
        } catch (e) {
            list.innerHTML = "<li><em>Impossible de charger tes rendez-vous.</em></li>";
        }
    }

    load();
})();
