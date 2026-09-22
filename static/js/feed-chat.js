(function () {
    "use strict";

    const app = document.getElementById("feed-chat-app");
    const header = document.getElementById("chat-header");
    const captionEl = document.getElementById("feed-chat-post-caption");
    const conversationId = app.dataset.conversationId;
    const messagesEl = document.getElementById("chat-messages");
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const API = `/api/feed/conversations/${conversationId}/messages/`;

    let headerRendered = false;
    let consecutiveFailures = 0;

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    function renderHeader(otherParty) {
        if (headerRendered || !otherParty) return;
        headerRendered = true;
        const avatar = otherParty.avatar_url
            ? `<img src="${otherParty.avatar_url}" alt="" class="chat-header-avatar">`
            : `<span class="chat-header-avatar chat-header-avatar-fallback">${window.DWU.icon ? window.DWU.icon("user") : ""}</span>`;
        header.innerHTML = `<a class="chat-partner-link" href="/accounts/u/${otherParty.id}/">${avatar}<h1>${escapeHtml(otherParty.name)}</h1></a>`;
    }

    function renderMessages(messages) {
        if (!messages.length) {
            messagesEl.innerHTML = "<p><em>Dis bonjour !</em></p>";
            return;
        }
        messagesEl.innerHTML = messages.map((m) => `
            <div class="chat-bubble ${m.mine ? "mine" : ""}">
                ${!m.mine ? `<span class="chat-sender">${escapeHtml(m.sender_label)}</span>` : ""}
                <p>${escapeHtml(m.content)}</p>
            </div>
        `).join("");
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    async function loadMessages() {
        try {
            const res = await fetch(API, { credentials: "same-origin" });
            if (!res.ok) {
                consecutiveFailures += 1;
                if (consecutiveFailures >= 3) {
                    messagesEl.innerHTML = "<p><em>Impossible de charger cette conversation.</em></p>";
                }
                return;
            }
            consecutiveFailures = 0;
            const data = await res.json();
            renderMessages(data.messages);
            renderHeader(data.other_party);
            if (data.post_caption && captionEl) {
                captionEl.textContent = `À propos de : « ${data.post_caption} »`;
            }
        } catch (e) {
            // on retente au prochain cycle de polling
        }
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const content = input.value.trim();
        if (!content) return;
        input.value = "";
        try {
            const res = await fetch(API, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": window.DWU.getCsrfToken() },
                body: JSON.stringify({ content }),
            });
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                input.value = content;
                window.DWU.infoModal(
                    data.detail || "Impossible d'envoyer ce message.",
                    { title: "Message non envoyé", tone: "danger", icon: "x-circle" }
                );
                return;
            }
            loadMessages();
        } catch (e) {
            // erreur réseau ponctuelle : le prochain polling remettra à jour
        }
    });

    loadMessages();
    setInterval(loadMessages, 3000);
})();
