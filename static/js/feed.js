(function () {
    "use strict";

    const list = document.getElementById("feed-list");
    const moreRow = document.getElementById("feed-more-row");
    const icon = (name) => (window.DWU.icon ? window.DWU.icon(name) : "");
    let nextUrl = "/api/feed/";

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

    async function loadSelectOptions(citySelect, moodSelect) {
        try {
            const [citiesRes, moodsRes] = await Promise.all([
                fetch("/api/cities/"), fetch("/api/moods/"),
            ]);
            const cities = (await citiesRes.json()).results || [];
            const moods = (await moodsRes.json()).results || [];
            cities.forEach((c) => citySelect.insertAdjacentHTML("beforeend", `<option value="${c.id}">${escapeHtml(c.name)}</option>`));
            moods.forEach((m) => moodSelect.insertAdjacentHTML("beforeend", `<option value="${m.id}">${escapeHtml(m.name)}</option>`));
        } catch (e) {
            // silencieux
        }
    }

    function interestActionHtml(post) {
        if (post.is_mine) {
            return `<button type="button" class="btn" data-close="${post.id}">${icon("x-circle")} Retirer</button>`;
        }
        if (post.my_interest_status === "accepted") {
            return `<a class="btn btn-primary" href="/messages/${post.conversation_id}/">${icon("message-circle")} Ouvrir la conversation</a>`;
        }
        if (post.my_interest_status === "pending") {
            return `<button type="button" class="btn" disabled>${icon("clock")} Demande envoyée</button>`;
        }
        return `<button type="button" class="btn btn-primary" data-discuss="${post.id}">${icon("message-circle")} Discuter</button>`;
    }

    function postCard(post) {
        const meta = [post.place, post.city, post.mood].filter(Boolean);
        const div = document.createElement("div");
        div.className = "card feed-post";
        div.dataset.postId = post.id;
        div.innerHTML = `
            <div class="feed-post-head">
                ${post.author_avatar_url
                    ? `<img src="${post.author_avatar_url}" alt="" class="feed-post-avatar-img">`
                    : `<div class="feed-post-avatar">${icon("user")}</div>`}
                <div>
                    <strong><a href="/accounts/u/${post.author_id}/">${escapeHtml(post.author_name)}</a></strong>
                    <span class="feed-post-time">${timeAgo(post.created_at)}</span>
                </div>
            </div>
            ${meta.length ? `<div class="place-meta-row" style="margin:0.5rem 0;">${meta.map((m) => `<span class="place-chip">${escapeHtml(m)}</span>`).join("")}</div>` : ""}
            <p class="feed-post-caption">${escapeHtml(post.caption)}</p>
            ${post.cover_image ? `<img src="${post.cover_image}" alt="" class="feed-post-image">` : ""}
            <div class="feed-post-actions">
                <button type="button" class="feed-like-btn ${post.liked_by_me ? "liked" : ""}" data-like="${post.id}">
                    ${icon("heart")} <span class="feed-like-count">${post.like_count}</span>
                </button>
                ${interestActionHtml(post)}
            </div>
        `;
        return div;
    }

    function bindPostActions(el, post) {
        const likeBtn = el.querySelector("[data-like]");
        likeBtn?.addEventListener("click", async () => {
            const liked = likeBtn.classList.contains("liked");
            const res = await fetch(`/api/feed/${post.id}/like/`, {
                method: liked ? "DELETE" : "POST",
                headers: { "X-CSRFToken": window.DWU.getCsrfToken() },
            });
            const data = await res.json();
            likeBtn.classList.toggle("liked", data.liked);
            likeBtn.querySelector(".feed-like-count").textContent = data.like_count;
        });

        el.querySelector("[data-discuss]")?.addEventListener("click", () => openDiscussModal(post));
        el.querySelector("[data-close]")?.addEventListener("click", async () => {
            const confirmed = await window.DWU.confirmModal("Cette publication sera retirée du fil. Cette action est irréversible.", {
                title: "Retirer la publication ?",
                confirmLabel: "Retirer la publication",
            });
            if (!confirmed) return;
            const res = await fetch(`/api/feed/${post.id}/close/`, {
                method: "POST",
                headers: { "X-CSRFToken": window.DWU.getCsrfToken() },
            });
            if (!res.ok) {
                window.DWU.infoModal("La publication n'a pas pu être retirée. Réessaie dans un instant.", {
                    title: "Action impossible",
                    tone: "danger",
                    icon: "alert-circle",
                });
                return;
            }
            el.remove();
        });
    }

    function closeModal() {
        document.getElementById("dwu-discuss-overlay")?.remove();
    }

    function openDiscussModal(post) {
        closeModal();
        const overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.id = "dwu-discuss-overlay";
        overlay.addEventListener("click", (e) => { if (e.target === overlay) closeModal(); });
        overlay.innerHTML = `
            <div class="modal-panel" style="max-width:440px;">
                <button class="modal-close" id="discuss-close" aria-label="Fermer">${icon("x-circle")}</button>
                <div class="modal-body">
                    <h2 style="margin-bottom:0.6rem;">Envoyer une demande</h2>
                    <p style="color:var(--ink-soft);margin-bottom:0.8rem;">
                        ${escapeHtml(post.author_name)} devra accepter avant que la conversation ne s'ouvre.
                    </p>
                    <form id="discuss-form">
                        <textarea name="message" rows="3" maxlength="300" placeholder="Un petit mot (optionnel)" style="width:100%;margin-bottom:0.8rem;"></textarea>
                        <button type="submit" class="btn btn-primary" style="width:100%;">Envoyer la demande</button>
                        <p id="discuss-feedback" style="margin-top:0.5rem;font-size:0.85rem;"></p>
                    </form>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        overlay.querySelector("#discuss-close").addEventListener("click", closeModal);
        overlay.querySelector("#discuss-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            const message = e.target.querySelector('[name="message"]').value;
            const res = await fetch(`/api/feed/${post.id}/interest/`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": window.DWU.getCsrfToken() },
                body: JSON.stringify({ message }),
            });
            const data = await res.json();
            const feedback = document.getElementById("discuss-feedback");
            if (res.ok) {
                feedback.style.color = "var(--success)";
                feedback.textContent = data.detail;
                const card = list.querySelector(`[data-post-id="${post.id}"]`);
                const actionsBtn = card?.querySelector("[data-discuss]");
                if (actionsBtn) {
                    actionsBtn.outerHTML = `<button type="button" class="btn" disabled>${icon("clock")} Demande envoyée</button>`;
                }
                setTimeout(closeModal, 1200);
            } else {
                feedback.style.color = "var(--danger)";
                feedback.textContent = data.detail || "Une erreur est survenue.";
            }
        });
    }

    async function loadPage(reset) {
        if (!nextUrl) return;
        try {
            const res = await fetch(nextUrl);
            const data = await res.json();
            if (reset) list.innerHTML = "";
            const posts = data.results || [];
            if (!posts.length && reset) {
                list.innerHTML = "<p><em>Personne n'a encore publié d'idée de sortie — sois le/la premier·ère !</em></p>";
            }
            posts.forEach((post) => {
                const el = postCard(post);
                bindPostActions(el, post);
                list.appendChild(el);
            });
            nextUrl = data.next;
            moreRow.innerHTML = nextUrl
                ? `<button type="button" class="btn" id="feed-more-btn">Voir plus</button>`
                : "";
            document.getElementById("feed-more-btn")?.addEventListener("click", () => loadPage(false));
        } catch (e) {
            if (reset) list.innerHTML = "<p><em>Impossible de charger le fil.</em></p>";
        }
    }

    function closeComposerModal() {
        document.getElementById("dwu-composer-overlay")?.remove();
    }

    function openComposerModal() {
        closeComposerModal();
        const overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.id = "dwu-composer-overlay";
        overlay.addEventListener("click", (e) => { if (e.target === overlay) closeComposerModal(); });
        overlay.innerHTML = `
            <div class="modal-panel" style="max-width:480px;">
                <button class="modal-close" id="composer-close" aria-label="Fermer">${icon("x-circle")}</button>
                <div class="modal-body">
                    <h2 style="margin-bottom:0.9rem;">${icon("sparkles")} Publier une idée de sortie</h2>
                    <form id="feed-composer-form">
                        <textarea id="feed-caption" rows="3" maxlength="500" placeholder="Une idée de sortie à partager ? (ex : Qui pour un ciné ce week-end à Tana ?)" style="width:100%;margin-bottom:0.8rem;" required></textarea>

                        <button type="button" class="composer-image-picker" id="composer-image-trigger">
                            <span id="composer-image-placeholder">${icon("image")} Ajouter une photo (optionnel)</span>
                            <img id="composer-image-preview" alt="" style="display:none;">
                            <span class="composer-image-remove" id="composer-image-remove" style="display:none;" title="Retirer la photo">${icon("x-circle")}</span>
                        </button>
                        <input type="file" id="composer-image-input" accept="image/*" style="display:none;">

                        <div class="feed-composer-row" style="margin-top:0.8rem;">
                            <select id="feed-city-select"><option value="">Ville (optionnel)</option></select>
                            <select id="feed-mood-select"><option value="">Ambiance (optionnel)</option></select>
                            <input type="date" id="feed-date-input" min="${new Date(Date.now() + 86400000).toISOString().slice(0, 10)}">
                        </div>
                        <button type="submit" class="btn btn-primary" id="feed-publish-btn" style="width:100%;margin-top:1rem;">${icon("send")} Publier</button>
                        <p id="composer-feedback" style="margin-top:0.5rem;font-size:0.85rem;"></p>
                    </form>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        overlay.querySelector("#composer-close").addEventListener("click", closeComposerModal);

        const citySelect = overlay.querySelector("#feed-city-select");
        const moodSelect = overlay.querySelector("#feed-mood-select");
        loadSelectOptions(citySelect, moodSelect);

        // --- Sélecteur de photo avec aperçu, sans bouton natif "Choisir
        // un fichier" : toute la zone est cliquable et affiche l'image
        // choisie directement à la place du texte d'invite. -------------
        const imageInput = overlay.querySelector("#composer-image-input");
        const imageTrigger = overlay.querySelector("#composer-image-trigger");
        const imagePreview = overlay.querySelector("#composer-image-preview");
        const imagePlaceholder = overlay.querySelector("#composer-image-placeholder");
        const imageRemove = overlay.querySelector("#composer-image-remove");

        imageTrigger.addEventListener("click", (e) => {
            if (e.target.closest("#composer-image-remove")) return;
            imageInput.click();
        });
        imageInput.addEventListener("change", () => {
            const file = imageInput.files && imageInput.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                imagePreview.style.display = "block";
                imagePlaceholder.style.display = "none";
                imageRemove.style.display = "flex";
            };
            reader.readAsDataURL(file);
        });
        imageRemove.addEventListener("click", (e) => {
            e.stopPropagation();
            imageInput.value = "";
            imagePreview.style.display = "none";
            imagePlaceholder.style.display = "flex";
            imageRemove.style.display = "none";
        });

        overlay.querySelector("#feed-composer-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            const caption = overlay.querySelector("#feed-caption").value.trim();
            const feedback = overlay.querySelector("#composer-feedback");
            if (!caption) return;

            const publishBtn = overlay.querySelector("#feed-publish-btn");
            publishBtn.disabled = true;

            const formData = new FormData();
            formData.append("caption", caption);
            if (citySelect.value) formData.append("city_id", citySelect.value);
            if (moodSelect.value) formData.append("mood_id", moodSelect.value);
            const dateVal = overlay.querySelector("#feed-date-input").value;
            if (dateVal) formData.append("date_value", dateVal);
            if (imageInput.files[0]) formData.append("image", imageInput.files[0]);

            try {
                const res = await fetch("/api/feed/", {
                    method: "POST",
                    headers: { "X-CSRFToken": window.DWU.getCsrfToken() },
                    body: formData,
                });
                const data = await res.json().catch(() => ({}));
                if (res.ok) {
                    const el = postCard(data);
                    bindPostActions(el, data);
                    list.prepend(el);
                    closeComposerModal();
                } else {
                    feedback.style.color = "var(--danger)";
                    feedback.textContent = data.detail || "Une erreur est survenue.";
                    publishBtn.disabled = false;
                }
            } catch (err) {
                feedback.style.color = "var(--danger)";
                feedback.textContent = "Impossible de publier pour l'instant.";
                publishBtn.disabled = false;
            }
        });
    }

    document.getElementById("feed-open-composer-btn")?.addEventListener("click", openComposerModal);

    loadPage(true);
})();
