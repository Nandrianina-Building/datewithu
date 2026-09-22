/**
 * Page "Tous mes rendez-vous" : deux onglets bien distincts —
 * "Mes propositions" (rendez-vous créés par l'utilisateur) et
 * "Invitations reçues" (où l'utilisateur est le/la partenaire) — chacun
 * avec des cartes complètes (image, lieu, date, statut, actions).
 */
(function () {
    "use strict";

    const icon = (name, cls) => (window.DWU.icon ? window.DWU.icon(name, cls) : "");

    const STATUS_LABELS = {
        pending: "En attente de réponse",
        viewed: "Vue par le/la partenaire",
        accepted: "Acceptée",
        maybe: "Peut-être",
        declined: "Déclinée",
        expired: "Expirée",
        cancelled: "Annulée",
    };
    const STATUS_ICONS = {
        pending: "clock", viewed: "eye", accepted: "check-circle", maybe: "clock",
        declined: "x-circle", expired: "clock", cancelled: "slash-circle",
    };

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    function formatDate(dateValue, timeValue) {
        if (!dateValue) return "Date à définir";
        try {
            const d = new Date(`${dateValue}T${timeValue || "00:00:00"}`);
            const formatted = d.toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });
            return timeValue ? `${formatted} à ${timeValue.slice(0, 5)}` : formatted;
        } catch (e) {
            return dateValue;
        }
    }

    function coverImage(item) {
        return item.place_image || item.activity_image
            || `https://picsum.photos/seed/dwu-date-${item.plan_id}/600/400`;
    }

    function statusPill(status) {
        if (!status) return `<span class="mydate-status mydate-status-pending">${icon("clock")} Invitation non envoyée</span>`;
        return `<span class="mydate-status mydate-status-${status}">${icon(STATUS_ICONS[status] || "clock")} ${STATUS_LABELS[status] || status}</span>`;
    }

    function proposedCard(item) {
        const where = item.place || item.activity || item.city || "Rendez-vous";
        const card = document.createElement("div");
        card.className = "mydate-card";
        card.innerHTML = `
            <div class="mydate-cover" style="background-image:url('${coverImage(item)}');">
                ${statusPill(item.invitation_status)}
            </div>
            <div class="mydate-body">
                <h3>${escapeHtml(window.DWU.truncate(where, 42))}</h3>
                <p class="mydate-meta">${icon("map-pin")} ${escapeHtml(item.city || "")}</p>
                <p class="mydate-meta">${icon("clock")} ${formatDate(item.date_value, item.time_value)}</p>
                <div class="mydate-actions">
                    ${item.invitation_token ? `<button type="button" class="btn btn-primary" data-share="${item.invitation_token}">${icon("qrcode")} Lien / QR</button>` : ""}
                    <a class="btn" href="/dates/${item.plan_id}/chat/">${icon("message-circle")} Discuter</a>
                    ${item.date_value ? `<a class="btn" href="/dates/${item.plan_id}/calendrier.ics">${icon("clock")} Calendrier</a>` : ""}
                </div>
            </div>
        `;
        return card;
    }

    function receivedCard(item) {
        const where = item.place || item.activity || item.city || "Rendez-vous";
        const canChat = item.invitation_status === "accepted" || item.invitation_status === "maybe";
        const needsResponse = item.invitation_status === "pending" || item.invitation_status === "viewed";
        const card = document.createElement("div");
        card.className = "mydate-card";
        card.innerHTML = `
            <div class="mydate-cover" style="background-image:url('${coverImage(item)}');">
                ${statusPill(item.invitation_status)}
            </div>
            <div class="mydate-body">
                <h3>${escapeHtml(window.DWU.truncate(where, 42))}</h3>
                <p class="mydate-meta">${icon("user")} Proposé par <a href="/accounts/u/${item.creator_id}/">${escapeHtml(window.DWU.truncate(item.creator_name, 24))}</a></p>
                <p class="mydate-meta">${icon("map-pin")} ${escapeHtml(item.city || "")}</p>
                <p class="mydate-meta">${icon("clock")} ${formatDate(item.date_value, item.time_value)}</p>
                <div class="mydate-actions">
                    ${needsResponse ? `<a class="btn btn-primary" href="/invite/${item.invitation_token}/">${icon("heart")} Répondre</a>` : ""}
                    ${canChat ? `<a class="btn" href="/invite/${item.invitation_token}/chat/">${icon("message-circle")} Discuter</a>` : ""}
                    ${canChat && item.date_value ? `<a class="btn" href="/dates/${item.plan_id}/calendrier.ics">${icon("clock")} Calendrier</a>` : ""}
                </div>
            </div>
        `;
        return card;
    }

    function closeShareModal() {
        document.getElementById("dwu-share-overlay")?.remove();
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
            overlay.querySelector(".modal-panel").innerHTML = `<p style="padding:2rem;text-align:center;">Impossible de charger ce lien.</p>`;
        }
    }

    async function loadProposed() {
        const grid = document.getElementById("proposed-grid");
        try {
            const res = await fetch("/api/my-dates/");
            const dates = await res.json();
            document.getElementById("count-proposed").textContent = dates.length ? `(${dates.length})` : "";
            if (!dates.length) {
                grid.innerHTML = `<p class="mydates-empty"><em>Tu n'as encore rien proposé — <a href="/date-builder/">crée ton premier rendez-vous</a>.</em></p>`;
                return;
            }
            grid.innerHTML = "";
            dates.forEach((d) => grid.appendChild(proposedCard(d)));
            grid.querySelectorAll("[data-share]").forEach((btn) => {
                btn.addEventListener("click", () => openShare(btn.dataset.share));
            });
        } catch (e) {
            grid.innerHTML = "<p><em>Impossible de charger tes propositions.</em></p>";
        }
    }

    async function loadReceived() {
        const grid = document.getElementById("received-grid");
        try {
            const res = await fetch("/api/my-dates/received/");
            const dates = await res.json();
            document.getElementById("count-received").textContent = dates.length ? `(${dates.length})` : "";
            if (!dates.length) {
                grid.innerHTML = `<p class="mydates-empty"><em>Tu n'as reçu aucune invitation pour l'instant.</em></p>`;
                return;
            }
            grid.innerHTML = "";
            dates.forEach((d) => grid.appendChild(receivedCard(d)));
        } catch (e) {
            grid.innerHTML = "<p><em>Impossible de charger tes invitations reçues.</em></p>";
        }
    }

    document.querySelectorAll(".mydates-tab").forEach((tab) => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".mydates-tab").forEach((t) => {
                t.classList.remove("active");
                t.setAttribute("aria-selected", "false");
            });
            tab.classList.add("active");
            tab.setAttribute("aria-selected", "true");
            document.querySelectorAll(".mydates-panel").forEach((p) => { p.style.display = "none"; });
            document.getElementById(`panel-${tab.dataset.tab}`).style.display = "";
        });
    });

    loadProposed();
    loadReceived();
})();
