(function () {
    "use strict";

    const root = document.getElementById("safety-actions");
    if (!root) return;

    const userId = root.dataset.userId;
    let blocked = root.dataset.blocked === "true";
    const blockBtn = document.getElementById("block-btn");
    const reportBtn = document.getElementById("report-btn");
    const icon = (name) => (window.DWU.icon ? window.DWU.icon(name) : "");

    function setBlockLabel() {
        blockBtn.innerHTML = blocked
            ? `${icon("check-circle")} Débloquer`
            : `${icon("slash-circle")} Bloquer`;
    }

    blockBtn.addEventListener("click", async () => {
        const wasBlocked = blocked;
        blockBtn.disabled = true;
        try {
            const res = await fetch(`/api/safety/block/${userId}/`, {
                method: wasBlocked ? "DELETE" : "POST",
                headers: { "X-CSRFToken": window.DWU.getCsrfToken() },
            });
            if (res.ok) {
                blocked = !wasBlocked;
                setBlockLabel();
            }
        } finally {
            blockBtn.disabled = false;
        }
    });

    function closeReportModal() {
        document.getElementById("dwu-report-overlay")?.remove();
    }

    reportBtn.addEventListener("click", () => {
        closeReportModal();
        const overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.id = "dwu-report-overlay";
        overlay.addEventListener("click", (e) => { if (e.target === overlay) closeReportModal(); });
        overlay.innerHTML = `
            <div class="modal-panel" style="max-width:440px;">
                <button class="modal-close" id="report-close" aria-label="Fermer">${icon("x-circle")}</button>
                <div class="modal-body">
                    <h2 style="margin-bottom:0.8rem;">Signaler ce profil</h2>
                    <form id="report-form">
                        <p class="checkbox-field" style="margin-bottom:0.5rem;">
                            <input type="radio" name="reason" value="inappropriate" id="reason-1" checked>
                            <label for="reason-1">Comportement ou contenu inapproprié</label>
                        </p>
                        <p class="checkbox-field" style="margin-bottom:0.5rem;">
                            <input type="radio" name="reason" value="fake_profile" id="reason-2">
                            <label for="reason-2">Faux profil / usurpation</label>
                        </p>
                        <p class="checkbox-field" style="margin-bottom:0.5rem;">
                            <input type="radio" name="reason" value="harassment" id="reason-3">
                            <label for="reason-3">Harcèlement</label>
                        </p>
                        <p class="checkbox-field" style="margin-bottom:0.5rem;">
                            <input type="radio" name="reason" value="spam" id="reason-4">
                            <label for="reason-4">Spam ou démarchage</label>
                        </p>
                        <p class="checkbox-field" style="margin-bottom:0.8rem;">
                            <input type="radio" name="reason" value="other" id="reason-5">
                            <label for="reason-5">Autre</label>
                        </p>
                        <textarea name="details" rows="3" placeholder="Précise si besoin (optionnel)" style="width:100%;margin-bottom:0.8rem;"></textarea>
                        <button type="submit" class="btn btn-primary" style="width:100%;">${icon("x-circle")} Envoyer le signalement</button>
                        <p id="report-feedback" style="margin-top:0.6rem;font-size:0.85rem;"></p>
                    </form>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        overlay.querySelector("#report-close").addEventListener("click", closeReportModal);
        overlay.querySelector("#report-form").addEventListener("submit", async (e) => {
            e.preventDefault();
            const form = e.target;
            const reason = form.querySelector('input[name="reason"]:checked').value;
            const details = form.querySelector('[name="details"]').value;
            const feedback = document.getElementById("report-feedback");
            try {
                const res = await fetch(`/api/safety/report/${userId}/`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": window.DWU.getCsrfToken(),
                    },
                    body: JSON.stringify({ reason, details }),
                });
                const data = await res.json();
                if (res.ok) {
                    feedback.style.color = "var(--success)";
                    feedback.textContent = data.detail;
                    setTimeout(closeReportModal, 1800);
                } else {
                    feedback.style.color = "var(--danger)";
                    feedback.textContent = data.detail || "Une erreur est survenue.";
                }
            } catch (err) {
                feedback.style.color = "var(--danger)";
                feedback.textContent = "Une erreur est survenue.";
            }
        });
    });
})();
