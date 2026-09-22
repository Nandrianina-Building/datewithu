/**
 * Page publique d'une invitation (Phase 4 — section 16).
 *
 * Depuis la refonte sécurité : cette page ne se charge que pour un
 * utilisateur déjà connecté (voir core/views.invitation_public_view et
 * core/templates/core/invitation_public.html, qui affichent un mur
 * d'inscription à la place pour tout visiteur anonyme). L'API
 * /api/invitations/<token>/public/ est elle-même protégée par
 * IsAuthenticated côté serveur — ce script ne fait qu'afficher ce que
 * l'API accepte de renvoyer.
 */
(function () {
    "use strict";

    const root = document.getElementById("invitation-app");
    if (!root) return;
    const token = root.dataset.token;
    const API = `/api/invitations/${token}/`;

    // Petites icônes SVG inline (mêmes tracés que apps/core/templatetags/icons.py)
    // pour rester cohérent avec la charte — pas d'emoji dans l'interface.
    const ICONS = {
        heart: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7.5-4.6-10-9.3C.4 8.1 2 4.5 5.6 4.1 8 3.8 10 5 12 7.5 14 5 16 3.8 18.4 4.1 22 4.5 23.6 8.1 22 11.7 19.5 16.4 12 21 12 21Z"/></svg>',
        check: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="m8.5 12.5 2.5 2.5 5-5"/></svg>',
        question: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 1.7-2.5 2-2.5 4"/><path d="M12 17h.01"/></svg>',
        close: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 6l12 12"/><path d="M18 6 6 18"/></svg>',
        clock: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/></svg>',
        chat: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v11H8l-4 4V5Z"/></svg>',
        mapPin: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.1 7-12a7 7 0 1 0-14 0c0 5.9 7 12 7 12Z"/><circle cx="12" cy="9" r="2.5"/></svg>',
    };

    function getCookie(name) {
        const match = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]+)"));
        return match ? decodeURIComponent(match[2]) : null;
    }

    function getCsrfToken() {
        return (root.dataset.csrfToken
            || document.querySelector("[name=csrfmiddlewaretoken]")?.value
            || getCookie("csrftoken")
            || "").trim();
    }

    async function apiGet(path) {
        const res = await fetch(path);
        return res.json();
    }

    async function apiPost(path, body) {
        const res = await fetch(path, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            credentials: "same-origin",
            body: JSON.stringify(body),
        });
        return { ok: res.ok, data: await res.json() };
    }

    function isPastDate(dateValue, timeValue) {
        if (!dateValue) return false;
        const iso = timeValue ? `${dateValue}T${timeValue}` : `${dateValue}T23:59:59`;
        const when = new Date(iso);
        if (Number.isNaN(when.getTime())) return false;
        return when.getTime() < Date.now();
    }

    function heroImage(plan) {
        const img = (plan.place && plan.place.main_image) || (plan.activity && plan.activity.image);
        const seed = (plan.place && plan.place.id) || (plan.activity && plan.activity.id) || "default";
        return img || `https://picsum.photos/seed/dwu-invite-${seed}/900/500`;
    }

    function planChips(plan) {
        const chips = [];
        if (plan.mood) chips.push(`${ICONS.heart} ${escapeHtml(plan.mood.name)}`);
        if (plan.place) chips.push(`${ICONS.mapPin} ${escapeHtml(plan.place.name)}`);
        else if (plan.activity) chips.push(`${ICONS.mapPin} ${escapeHtml(plan.activity.name)}`);
        if (plan.city) chips.push(`${ICONS.mapPin} ${escapeHtml(plan.city.name)}`);
        if (plan.date_value) chips.push(`${ICONS.clock} ${escapeHtml(plan.date_value)}${plan.time_value ? ` à ${escapeHtml(plan.time_value.slice(0, 5))}` : ""}`);
        return chips.map((c) => `<span class="invite-chip">${c}</span>`).join("");
    }

    function renderOwnInvitation(data) {
        root.innerHTML = `
            <div class="invite-card">
                <img class="invite-hero" src="${heroImage(data.plan)}" alt="">
                <div class="invite-body" style="text-align:center;">
                    ${ICONS.heart}
                    <h1>C'est ton invitation !</h1>
                    <p>Tu ne peux pas répondre à ta propre proposition — partage plutôt ce lien avec la
                    personne concernée pour qu'elle puisse accepter, décliner ou dire peut-être.</p>
                    <p><a class="btn btn-primary" href="/dashboard/">Retourner à mon espace</a></p>
                </div>
            </div>
        `;
    }

    function renderAnswered(data) {
        const labels = { accepted: "acceptée", maybe: "en peut-être", declined: "déclinée" };
        const canChat = data.status === "accepted" || data.status === "maybe";
        const plan = data.plan || {};
        // Avant la refonte, cette page arrêtait d'afficher les détails du
        // rendez-vous dès qu'une réponse était enregistrée — y compris pour
        // une invitation acceptée à venir. On les affiche désormais tant
        // que la date du rendez-vous elle-même n'est pas passée (l'expiration
        // du LIEN d'invitation, gérée plus haut par `is_expired`, est une
        // notion différente et déjà traitée avant d'arriver ici).
        const past = isPastDate(plan.date_value, plan.time_value);
        root.innerHTML = `
            <div class="invite-card">
                <img class="invite-hero" src="${heroImage(plan)}" alt="">
                <div class="invite-body">
                    <span class="invite-status-pill invite-status-${data.status}">${ICONS.check} Réponse enregistrée</span>
                    <h1>Invitation ${labels[data.status] || data.status}</h1>
                    ${!past ? `
                        <div class="invite-chips">${planChips(plan)}</div>
                        ${plan.personal_message ? `<blockquote class="invite-message">${escapeHtml(plan.personal_message)}</blockquote>` : ""}
                    ` : `<p><em>Ce rendez-vous est passé.</em></p>`}
                    ${canChat ? `<a class="btn btn-primary invite-cta" href="/invite/${token}/chat/">${ICONS.chat} Discuter</a>` : ""}
                </div>
            </div>
        `;
    }

    function renderExpired() {
        root.innerHTML = `
            <div class="invite-card">
                <div class="invite-body" style="text-align:center;">
                    ${ICONS.clock}
                    <h1>Invitation expirée</h1>
                    <p>Ce lien n'est plus valide, demande une nouvelle invitation à la personne concernée.</p>
                </div>
            </div>
        `;
    }

    function renderInvitation(data) {
        if (data.is_expired) return renderExpired();
        if (data.is_own_invitation) return renderOwnInvitation(data);
        if (["accepted", "maybe", "declined"].includes(data.status)) return renderAnswered(data);

        root.innerHTML = `
            <div class="invite-card">
                <img class="invite-hero" src="${heroImage(data.plan)}" alt="">
                <div class="invite-body">
                    <h1>${ICONS.heart} ${escapeHtml(data.creator_name)} t'invite</h1>
                    <div class="invite-chips">${planChips(data.plan)}</div>
                    ${data.plan.personal_message ? `<blockquote class="invite-message">${escapeHtml(data.plan.personal_message)}</blockquote>` : ""}

                    <div class="invite-actions" id="invitation-actions">
                        <button class="btn btn-primary" data-response="accept">${ICONS.check} J'accepte</button>
                        <button class="btn" data-response="maybe">${ICONS.question} Peut-être</button>
                        <button class="btn btn-decline" data-response="decline">${ICONS.close} Je décline</button>
                    </div>

                    <label class="invite-name-label" for="partner-name">Ton prénom <span>(optionnel)</span></label>
                    <input type="text" id="partner-name" class="invite-name-input" placeholder="Ex : Mialy">
                </div>
            </div>
        `;

        document.querySelectorAll("#invitation-actions button").forEach((btn) => {
            btn.addEventListener("click", async () => {
                document.querySelectorAll("#invitation-actions button").forEach((b) => { b.disabled = true; });
                const nameInput = document.getElementById("partner-name");
                const { ok, data: result } = await apiPost(`${API}respond/`, {
                    response: btn.dataset.response,
                    partner_name: nameInput ? nameInput.value.trim() : "",
                });
                if (ok) {
                    renderAnswered(result);
                } else {
                    alert(result.detail || "Une erreur est survenue.");
                    document.querySelectorAll("#invitation-actions button").forEach((b) => { b.disabled = false; });
                }
            });
        });
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    apiGet(`${API}public/`).then(renderInvitation);
})();
