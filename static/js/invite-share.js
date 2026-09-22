/**
 * Carte de partage moderne (lien + QR code) pour une invitation — utilisée
 * à la fois à la fin du Date Builder (date-builder.js) et depuis "Mes
 * rendez-vous" (my-dates.js) pour repartager une invitation existante.
 *
 * Génère le QR code via notre propre endpoint (/invite/<token>/qr.png)
 * plutôt qu'un service tiers, pour ne jamais dépendre d'un service externe
 * ni fuiter l'URL du rendez-vous à un tiers.
 */
window.DWU = window.DWU || {};

(function (ns) {
    "use strict";

    ns.renderShareCard = function renderShareCard(invitation) {
        const url = invitation.share_url;
        const token = invitation.token;
        const text = encodeURIComponent("J'ai un rendez-vous à te proposer sur Date With U");
        const qrSrc = `/invite/${token}/qr.png`;
        const icon = ns.icon || (() => "");

        return `
            <div class="share-card">
                <div class="share-card-main">
                    <p class="share-card-label">Lien de ton invitation</p>
                    <div class="share-link-row">
                        <input type="text" class="share-link-input" readonly value="${url}">
                        <button type="button" class="btn btn-primary share-copy-btn" data-share-url="${url}">
                            ${icon("copy")} <span>Copier</span>
                        </button>
                    </div>
                    <div class="share-social-row">
                        <a class="btn share-social-btn" target="_blank" rel="noopener"
                           href="https://wa.me/?text=${text}%20${encodeURIComponent(url)}">WhatsApp</a>
                        <a class="btn share-social-btn" target="_blank" rel="noopener"
                           href="https://www.facebook.com/dialog/send?link=${encodeURIComponent(url)}&app_id=0&redirect_uri=${encodeURIComponent(url)}">
                           Messenger</a>
                    </div>
                </div>
                <div class="share-card-qr">
                    ${icon("qrcode", "icon")}
                    <img src="${qrSrc}" alt="QR code de l'invitation" width="110" height="110" loading="lazy">
                    <span class="share-qr-caption">Ou fais scanner ce QR code</span>
                    <a class="btn share-download-btn" href="/invite/${token}/carte.png" download>${icon("copy")} Télécharger la carte</a>
                </div>
            </div>
        `;
    };

    ns.bindShareCard = function bindShareCard(root) {
        const btn = root.querySelector(".share-copy-btn");
        if (!btn) return;
        btn.addEventListener("click", async () => {
            const url = btn.dataset.shareUrl;
            const label = btn.querySelector("span");
            try {
                await navigator.clipboard.writeText(url);
            } catch (e) {
                root.querySelector(".share-link-input")?.select();
                document.execCommand("copy");
            }
            if (label) {
                const original = label.textContent;
                label.textContent = "Copié !";
                setTimeout(() => { label.textContent = original; }, 1800);
            }
        });
    };
})(window.DWU);
