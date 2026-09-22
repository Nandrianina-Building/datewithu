(function () {
    "use strict";

    const banner = document.getElementById("pending-ratings-banner");
    if (!banner) return;

    const icon = (name) => (window.DWU.icon ? window.DWU.icon(name) : "");

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    function renderPrompt(item) {
        banner.innerHTML = `
            <div class="card status-card-warning" style="margin-bottom:1.2rem;">
                <h2 style="font-size:1rem;margin-bottom:0.4rem;">${icon("star")} Comment s'est passé ton rendez-vous ?</h2>
                <p style="color:var(--ink-soft);margin-bottom:0.7rem;">
                    Avec ${escapeHtml(item.other_user_name)}${item.place ? ` — ${escapeHtml(item.place)}` : ""}
                </p>
                <div class="star-picker" role="radiogroup" aria-label="Note" id="dashboard-rating-stars">
                    ${[5, 4, 3, 2, 1].map((n) => `<label class="star-option"><input type="radio" name="dashboard-stars" value="${n}"${n === 5 ? " checked" : ""}><span aria-hidden="true">★</span></label>`).join("")}
                </div>
                <textarea id="dashboard-rating-comment" rows="2" maxlength="300" placeholder="Un commentaire ? (optionnel)" style="width:100%;margin:0.6rem 0;"></textarea>
                <button type="button" class="btn btn-primary" id="dashboard-rating-submit">Envoyer</button>
                <button type="button" class="link-btn" id="dashboard-rating-skip" style="margin-left:0.6rem;">Plus tard</button>
            </div>
        `;
        document.getElementById("dashboard-rating-submit").addEventListener("click", async () => {
            const stars = banner.querySelector('input[name="dashboard-stars"]:checked').value;
            const comment = document.getElementById("dashboard-rating-comment").value;
            await fetch(`/api/date-ratings/${item.plan_id}/`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": window.DWU.getCsrfToken() },
                body: JSON.stringify({ stars, comment }),
            });
            banner.innerHTML = "";
        });
        document.getElementById("dashboard-rating-skip").addEventListener("click", () => { banner.innerHTML = ""; });
    }

    async function load() {
        try {
            const res = await fetch("/api/date-ratings/pending/");
            const items = await res.json();
            if (items.length) renderPrompt(items[0]);
        } catch (e) {
            // silencieux
        }
    }

    load();
})();
