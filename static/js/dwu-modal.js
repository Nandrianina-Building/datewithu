/**
 * Petite modale réutilisable pour remplacer les alert()/confirm() natifs,
 * qui sont bloquants, moches et non personnalisables (ex : message
 * "Impossible d'envoyer un message à cette personne." quand on a bloqué
 * quelqu'un). Réutilise les classes .modal-overlay/.modal-panel déjà
 * définies dans main.css.
 *
 * Usage :
 *   window.DWU.infoModal("Impossible d'envoyer un message à cette personne.");
 *   window.DWU.infoModal("...", { title: "Oups", tone: "danger" });
 */
(function () {
    "use strict";

    function escapeHtml(value) {
        const div = document.createElement("div");
        div.textContent = String(value || "");
        return div.innerHTML;
    }

    function closeAll() {
        document.querySelectorAll(".dwu-info-modal-overlay").forEach((el) => el.remove());
    }

    function infoModal(message, options) {
        options = options || {};
        closeAll();
        const overlay = document.createElement("div");
        overlay.className = "modal-overlay dwu-info-modal-overlay";
        overlay.addEventListener("click", (e) => { if (e.target === overlay) closeAll(); });

        const icon = (window.DWU && window.DWU.icon) ? window.DWU.icon(options.icon || "message-circle") : "";
        const title = options.title || (options.tone === "danger" ? "Une erreur est survenue" : "Information");
        overlay.innerHTML = `
            <div class="modal-panel dwu-info-modal-panel" role="alertdialog" aria-modal="true">
                <button class="modal-close" type="button" aria-label="Fermer">${(window.DWU && window.DWU.icon) ? window.DWU.icon("x-circle") : "✕"}</button>
                <div class="modal-body dwu-info-modal-body">
                    <div class="dwu-info-modal-icon ${options.tone || ""}">${icon}</div>
                    <h2>${escapeHtml(title)}</h2>
                    <p>${escapeHtml(message)}</p>
                    <button type="button" class="btn btn-primary dwu-info-modal-ok">Compris</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        overlay.querySelector(".modal-close").addEventListener("click", closeAll);
        overlay.querySelector(".dwu-info-modal-ok").addEventListener("click", closeAll);
        document.addEventListener("keydown", function escHandler(e) {
            if (e.key === "Escape") { closeAll(); document.removeEventListener("keydown", escHandler); }
        });
    }

    function confirmModal(message, options) {
        options = options || {};
        closeAll();
        const overlay = document.createElement("div");
        overlay.className = "modal-overlay dwu-info-modal-overlay";
        overlay.innerHTML = `
            <div class="modal-panel dwu-info-modal-panel dwu-confirm-modal-panel" role="dialog" aria-modal="true">
                <button class="modal-close" type="button" aria-label="Fermer">${(window.DWU && window.DWU.icon) ? window.DWU.icon("x-circle") : "✕"}</button>
                <div class="modal-body dwu-info-modal-body">
                    <div class="dwu-info-modal-icon danger">${(window.DWU && window.DWU.icon) ? window.DWU.icon(options.icon || "trash") : ""}</div>
                    <h2>${escapeHtml(options.title || "Confirmer la suppression")}</h2>
                    <p>${escapeHtml(message)}</p>
                    <div class="dwu-confirm-actions">
                        <button type="button" class="btn dwu-confirm-cancel">Annuler</button>
                        <button type="button" class="btn btn-danger dwu-confirm-ok">${escapeHtml(options.confirmLabel || "Retirer")}</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        return new Promise((resolve) => {
            let settled = false;
            const finish = (value) => {
                if (settled) return;
                settled = true;
                document.removeEventListener("keydown", overlay._dwuEscHandler);
                closeAll();
                resolve(value);
            };
            overlay.addEventListener("click", (e) => { if (e.target === overlay) finish(false); });
            overlay.querySelector(".modal-close").addEventListener("click", () => finish(false));
            overlay.querySelector(".dwu-confirm-cancel").addEventListener("click", () => finish(false));
            overlay.querySelector(".dwu-confirm-ok").addEventListener("click", () => finish(true));
            overlay._dwuEscHandler = (e) => { if (e.key === "Escape") finish(false); };
            document.addEventListener("keydown", overlay._dwuEscHandler);
        });
    }

    window.DWU = window.DWU || {};
    window.DWU.infoModal = infoModal;
    window.DWU.confirmModal = confirmModal;
    window.DWU.closeInfoModal = closeAll;
    window.alert = function (message) {
        infoModal(message, { tone: "danger", icon: "alert-circle" });
    };
})();
