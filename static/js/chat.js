/**
 * Chat en polling HTTP (Phase 7). Simple et fiable, sans dépendance
 * supplémentaire. Si tu actives Channels + Redis plus tard (voir
 * apps/chat/consumers.py), ce fichier peut être remplacé par un client
 * WebSocket sans changer le HTML ni l'API REST d'historique.
 */
(function () {
    "use strict";

    const app = document.getElementById("chat-app");
    const header = document.getElementById("chat-header");
    const planId = app.dataset.planId;
    const token = app.dataset.token;
    const messagesEl = document.getElementById("chat-messages");
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    let headerRendered = false;

    const API = `/api/chat/${planId}/messages/`;
    const POLL_INTERVAL_MS = 3000;

    function getCookie(name) {
        const match = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]+)"));
        return match ? decodeURIComponent(match[2]) : null;
    }

    function getCsrfToken() {
        return (app.dataset.csrfToken
            || document.querySelector("[name=csrfmiddlewaretoken]")?.value
            || getCookie("csrftoken")
            || "").trim();
    }

    function withToken(url) {
        if (!token) return url;
        const sep = url.includes("?") ? "&" : "?";
        return `${url}${sep}token=${encodeURIComponent(token)}`;
    }

    function renderHeader(otherParty) {
        if (headerRendered || !otherParty || !header) return;
        headerRendered = true;
        const avatar = otherParty.avatar_url
            ? `<img src="${otherParty.avatar_url}" alt="" class="chat-header-avatar">`
            : `<span class="chat-header-avatar chat-header-avatar-fallback">${window.DWU.icon ? window.DWU.icon("user") : ""}</span>`;
        const name = escapeHtml(otherParty.name || "Ton/ta partenaire");
        header.innerHTML = otherParty.id
            ? `<a class="chat-partner-link" href="/accounts/u/${otherParty.id}/">${avatar}<h1>${name}</h1></a>`
            : `<div class="chat-partner-link">${avatar}<h1>${name}</h1></div>`;
    }

    function renderMessages(messages) {
        if (!messages.length) {
            messagesEl.innerHTML = "<p><em>Aucun message pour l'instant — dis bonjour</em></p>";
            return;
        }
        const atBottom = messagesEl.scrollTop + messagesEl.clientHeight >= messagesEl.scrollHeight - 10;
        messagesEl.innerHTML = messages.map((m) => `
            <div class="chat-bubble ${m.mine ? "mine" : "theirs"}">
                <span class="chat-sender">${m.mine ? "Toi" : escapeHtml(m.sender_label || "")}</span>
                <p>${escapeHtml(m.content)}</p>
            </div>
        `).join("");
        if (atBottom) messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    let consecutiveFailures = 0;

    async function loadMessages() {
        try {
            const res = await fetch(withToken(API), { credentials: "same-origin" });
            if (!res.ok) {
                consecutiveFailures += 1;
                // Une requête peut échouer ponctuellement (redirection HTTPS
                // d'un proxy, coupure réseau passagère...) sans que la
                // conversation soit réellement inaccessible : on ne remplace
                // le fil de discussion par un message d'erreur qu'après
                // plusieurs échecs consécutifs, pour ne pas donner
                // l'impression que « le rendez-vous a disparu » à cause d'un
                // simple raté de polling.
                if (consecutiveFailures >= 3) {
                    let detail = "Accès refusé.";
                    try { detail = (await res.json()).detail || detail; } catch (e) { /* réponse non-JSON */ }
                    if (res.status === 401 || res.status === 403) {
                        messagesEl.innerHTML = `
                            <p><em>${escapeHtml(detail)} Ta session a peut-être expiré.</em></p>
                            <p><a class="btn btn-primary" href="${window.location.pathname}${window.location.search}">Recharger la conversation</a></p>
                        `;
                    } else {
                        messagesEl.innerHTML = `<p><em>${escapeHtml(detail)}</em></p>`;
                    }
                }
                return;
            }
            consecutiveFailures = 0;
            const data = await res.json();
            renderMessages(data.messages);
            renderHeader(data.other_party);
        } catch (e) {
            // Erreur réseau ponctuelle : on retente au prochain cycle de
            // polling sans casser l'affichage courant.
        }
    }

    async function sendMessage(content) {
        const body = { content };
        if (token) body.token = token;
        const res = await fetch(API, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            credentials: "same-origin",
            body: JSON.stringify(body),
        });
        const data = await res.json().catch(() => ({ detail: `Erreur serveur (${res.status}).` }));
        if (!res.ok) {
            throw new Error(data.detail || "Impossible d'envoyer le message.");
        }
        await loadMessages();
    }

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        const content = input.value.trim();
        if (!content) return;
        input.value = "";
        sendMessage(content).catch((error) => {
            input.value = content;
            if (window.DWU && window.DWU.infoModal) {
                window.DWU.infoModal(error.message, { title: "Message non envoyé", tone: "danger", icon: "x-circle" });
            } else {
                alert(error.message);
            }
        });
    });

    loadMessages();
    setInterval(loadMessages, POLL_INTERVAL_MS);
})();
