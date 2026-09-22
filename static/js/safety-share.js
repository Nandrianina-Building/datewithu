(function () {
    "use strict";

    const btn = document.getElementById("safety-share-btn");
    if (!btn) return;

    const icon = (name) => (window.DWU.icon ? window.DWU.icon(name) : "");
    const planId = document.getElementById("chat-app")?.dataset.planId;

    let watchId = null;
    let shareToken = null;

    function closeModal() {
        document.getElementById("dwu-safeshare-overlay")?.remove();
        if (watchId !== null) {
            navigator.geolocation.clearWatch(watchId);
            watchId = null;
        }
    }

    async function stopSharing() {
        if (shareToken) {
            try {
                await fetch(`/api/safeshare/${shareToken}/update/`, {
                    method: "DELETE",
                    headers: { "X-CSRFToken": window.DWU.getCsrfToken() },
                });
            } catch (e) { /* silencieux */ }
        }
        closeModal();
    }

    function openActiveModal(shareUrl) {
        const overlay = document.getElementById("dwu-safeshare-overlay");
        if (!overlay) return;
        overlay.querySelector(".modal-panel").innerHTML = `
            <button class="modal-close" id="safeshare-close" aria-label="Fermer">${icon("x-circle")}</button>
            <div class="modal-body">
                <h2 style="margin-bottom:0.6rem;">${icon("shield")} Partage de position actif</h2>
                <p style="color:var(--ink-soft);margin-bottom:0.8rem;">
                    Envoie ce lien à un·e proche — il/elle pourra suivre ta position en direct, sans avoir
                    besoin de compte. Le partage s'arrête automatiquement dans 6h.
                </p>
                <div class="share-link-row">
                    <input type="text" class="share-link-input" readonly value="${shareUrl}">
                    <button type="button" class="btn btn-primary" id="safeshare-copy">${icon("copy")} Copier</button>
                </div>
                <button type="button" class="btn" id="safeshare-stop" style="width:100%;margin-top:0.8rem;color:var(--danger);border-color:var(--danger);">
                    Arrêter le partage
                </button>
            </div>
        `;
        overlay.querySelector("#safeshare-close").addEventListener("click", closeModal);
        overlay.querySelector("#safeshare-copy").addEventListener("click", () => {
            navigator.clipboard?.writeText(shareUrl);
        });
        overlay.querySelector("#safeshare-stop").addEventListener("click", stopSharing);
    }

    btn.addEventListener("click", () => {
        closeModal();
        const overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.id = "dwu-safeshare-overlay";
        overlay.addEventListener("click", (e) => { if (e.target === overlay) closeModal(); });
        overlay.innerHTML = `
            <div class="modal-panel" style="max-width:440px;">
                <button class="modal-close" id="safeshare-close" aria-label="Fermer">${icon("x-circle")}</button>
                <div class="modal-body">
                    <h2 style="margin-bottom:0.6rem;">${icon("shield")} Prévenir un proche</h2>
                    <p style="color:var(--ink-soft);margin-bottom:0.8rem;">
                        Génère un lien de suivi en direct de ta position, à envoyer à quelqu'un de confiance
                        pendant ton rendez-vous.
                    </p>
                    <form id="safeshare-form">
                        <input type="text" id="safeshare-contact-name" placeholder="Prénom du/de la proche (optionnel)" style="width:100%;margin-bottom:0.8rem;">
                        <button type="submit" class="btn btn-primary" style="width:100%;">Démarrer le partage</button>
                    </form>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        overlay.querySelector("#safeshare-close").addEventListener("click", closeModal);
        overlay.querySelector("#safeshare-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            if (!navigator.geolocation) {
                alert("La géolocalisation n'est pas disponible sur cet appareil.");
                return;
            }
            const contactName = document.getElementById("safeshare-contact-name").value;
            const res = await fetch("/api/safeshare/start/", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": window.DWU.getCsrfToken() },
                body: JSON.stringify({ contact_name: contactName, date_plan_id: planId }),
            });
            const data = await res.json();
            shareToken = data.token;
            openActiveModal(data.share_url);

            watchId = navigator.geolocation.watchPosition(
                (pos) => {
                    fetch(`/api/safeshare/${shareToken}/update/`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-CSRFToken": window.DWU.getCsrfToken() },
                        body: JSON.stringify({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
                    }).catch(() => {});
                },
                () => {},
                { enableHighAccuracy: true, maximumAge: 10000, timeout: 15000 },
            );
        });
    });
})();
