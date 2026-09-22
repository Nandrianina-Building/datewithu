(function () {
    "use strict";

    function csrfHeaders(extra) {
        return Object.assign({ "X-CSRFToken": window.DWU.getCsrfToken() }, extra || {});
    }

    // --- Onglets ---------------------------------------------------------
    const navButtons = document.querySelectorAll("#admin-nav button[data-tab]");
    navButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            navButtons.forEach((b) => b.classList.remove("active"));
            document.querySelectorAll(".admin-tab").forEach((t) => t.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
        });
    });

    function statCard(title, value, sub, className = "") {
        const valueClass = className ? "admin-stat-list-value" : "stat";
        return `<div class="card ${className}"><h2>${title}</h2><p class="${valueClass}">${value}</p>${sub ? `<p>${sub}</p>` : ""}</div>`;
    }

    // --- Vue d'ensemble ----------------------------------------------------
    async function loadStats() {
        const grid = document.getElementById("admin-stats-grid");
        try {
            const res = await fetch("/api/admin/stats/");
            const s = await res.json();

            const invitationsBreakdown = Object.entries(s.invitations.by_status || {})
                .map(([k, v]) => `${k}: ${v}`).join(" · ") || "aucune";

            const topCities = (s.top_cities || []).map((c) => `${c.name} (${c.plan_count})`).join(", ") || "—";
            const topMoods = (s.top_moods || [])
                .map((m) => `${m.name} (${m.plan_count})`).join(", ") || "—";

            grid.innerHTML = [
                statCard("Utilisateurs", s.users.total, `+${s.users.new_last_7_days} sur 7j · +${s.users.new_last_30_days} sur 30j`),
                statCard("Rendez-vous", s.date_plans.total, `${s.date_plans.draft} brouillons · ${s.date_plans.completed} complétés`),
                statCard("Invitations", s.invitations.total, invitationsBreakdown),
                statCard(
                    "Taux d'acceptation",
                    s.invitations.acceptance_rate_percent !== null ? `${s.invitations.acceptance_rate_percent}%` : "—",
                    "parmi les invitations avec réponse"
                ),
                statCard("Lieux", s.places.total, `${s.places.active} actifs · ${s.places.inactive} inactifs`),
                statCard("Activités", s.activities.total, `${s.activities.active} actives`),
                statCard("Villes les + demandées", topCities, "", "admin-stat-list"),
                statCard("Ambiances les + choisies", topMoods, "", "admin-stat-list admin-stat-moods"),
            ].join("");
        } catch (e) {
            grid.innerHTML = "<p><em>Impossible de charger les statistiques.</em></p>";
        }
    }

    // --- Rendez-vous ---------------------------------------------------
    async function loadDatesOverview() {
        const el = document.getElementById("admin-dates-overview");
        const params = new URLSearchParams();
        const when = document.getElementById("filter-when").value;
        const status = document.getElementById("filter-status").value;
        if (when) params.set("when", when);
        if (status) params.set("status", status);

        el.innerHTML = "<p><em>Chargement...</em></p>";
        try {
            const res = await fetch(`/api/admin/dates/?${params.toString()}`);
            const dates = await res.json();
            if (!dates.length) {
                el.innerHTML = "<p><em>Aucun rendez-vous pour ces filtres.</em></p>";
                return;
            }
            const rows = dates.map((d) => `
                <tr>
                    <td>${d.creator}</td>
                    <td>${d.place || d.activity || "—"}</td>
                    <td>${d.city || "—"}</td>
                    <td>${d.date_value || "—"} ${d.time_value || ""}</td>
                    <td>${d.invitation_status || "sans invitation"}</td>
                    <td>${d.view_count}</td>
                </tr>
            `).join("");
            el.innerHTML = `
                <table class="admin-table">
                    <thead><tr><th>Créateur</th><th>Lieu/Activité</th><th>Ville</th><th>Date</th><th>Statut invitation</th><th>Vues</th></tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            `;
        } catch (e) {
            el.innerHTML = "<p><em>Impossible de charger les rendez-vous.</em></p>";
        }
    }
    document.getElementById("filter-when").addEventListener("change", loadDatesOverview);
    document.getElementById("filter-status").addEventListener("change", loadDatesOverview);

    // --- Modération des lieux ---------------------------------------------
    async function toggleActive(placeId, row) {
        const res = await fetch(`/api/admin/places/${placeId}/toggle-active/`, {
            method: "POST",
            headers: csrfHeaders(),
        });
        const data = await res.json();
        row.querySelector(".place-status").textContent = data.is_active ? "Actif" : "Inactif";
        row.querySelector(".place-status").className = `place-status ${data.is_active ? "active" : "inactive"}`;
        row.querySelector(".toggle-btn").textContent = data.is_active ? "Désactiver" : "Activer";
    }

    async function loadModeration() {
        const el = document.getElementById("admin-places-moderation");
        try {
            const res = await fetch("/api/admin/places/");
            const places = await res.json();
            if (!places.length) {
                el.innerHTML = "<p><em>Aucun lieu enregistré pour l'instant.</em></p>";
                return;
            }
            el.innerHTML = `
                <table class="admin-table">
                    <thead><tr><th>Nom</th><th>Ville</th><th>Catégorie</th><th>Statut</th><th></th></tr></thead>
                    <tbody>${places.map((p) => `
                        <tr data-id="${p.id}">
                            <td>${p.name}</td>
                            <td>${p.city || "—"}</td>
                            <td>${p.category || "—"}</td>
                            <td><span class="place-status ${p.is_active ? "active" : "inactive"}">${p.is_active ? "Actif" : "Inactif"}</span></td>
                            <td><button class="mini-btn toggle-btn">${p.is_active ? "Désactiver" : "Activer"}</button></td>
                        </tr>
                    `).join("")}</tbody>
                </table>
            `;
            el.querySelectorAll("tr[data-id]").forEach((row) => {
                row.querySelector(".toggle-btn").addEventListener("click", () => {
                    toggleActive(row.dataset.id, row);
                });
            });
        } catch (e) {
            el.innerHTML = "<p><em>Impossible de charger la liste des lieux.</em></p>";
        }
    }

    // --- Utilisateurs -------------------------------------------------
    let userSearchTimer = null;

    async function toggleUserActive(userId, row) {
        const res = await fetch(`/api/admin/users/${userId}/toggle-active/`, {
            method: "POST",
            headers: csrfHeaders(),
        });
        const data = await res.json();
        if (!res.ok) {
            alert(data.detail || "Action impossible.");
            return;
        }
        row.querySelector(".place-status").textContent = data.is_active ? "Actif" : "Désactivé";
        row.querySelector(".place-status").className = `place-status ${data.is_active ? "active" : "inactive"}`;
        row.querySelector(".toggle-btn").textContent = data.is_active ? "Désactiver" : "Réactiver";
    }

    async function loadUsers() {
        const el = document.getElementById("admin-users-list");
        const params = new URLSearchParams();
        const q = document.getElementById("user-search").value.trim();
        const verified = document.getElementById("user-filter-verified").value;
        if (q) params.set("q", q);
        if (verified) params.set("verified", verified);

        try {
            const res = await fetch(`/api/admin/users/?${params.toString()}`);
            const data = await res.json();
            if (!data.results.length) {
                el.innerHTML = "<p><em>Aucun utilisateur trouvé.</em></p>";
                return;
            }
            el.innerHTML = `
                <table class="admin-table">
                    <thead><tr><th>Utilisateur</th><th>E-mail</th><th>Vérifié</th><th>Rôle</th><th>Statut</th><th></th></tr></thead>
                    <tbody>${data.results.map((u) => `
                        <tr data-id="${u.id}">
                            <td>${u.username}</td>
                            <td>${u.email}</td>
                            <td>${u.is_verified ? "Oui" : "Non"}</td>
                            <td>${u.is_staff ? "Staff" : "Membre"}</td>
                            <td><span class="place-status ${u.is_active ? "active" : "inactive"}">${u.is_active ? "Actif" : "Désactivé"}</span></td>
                            <td>${u.is_staff ? "" : `<button class="mini-btn toggle-btn danger">${u.is_active ? "Désactiver" : "Réactiver"}</button>`}</td>
                        </tr>
                    `).join("")}</tbody>
                </table>
                <p style="font-size:0.85rem;color:var(--ink-soft);">${data.total} compte(s) au total.</p>
            `;
            el.querySelectorAll("tr[data-id]").forEach((row) => {
                const btn = row.querySelector(".toggle-btn");
                if (btn) btn.addEventListener("click", () => toggleUserActive(row.dataset.id, row));
            });
        } catch (e) {
            el.innerHTML = "<p><em>Impossible de charger les utilisateurs.</em></p>";
        }
    }
    document.getElementById("user-search").addEventListener("input", () => {
        clearTimeout(userSearchTimer);
        userSearchTimer = setTimeout(loadUsers, 300);
    });
    document.getElementById("user-filter-verified").addEventListener("change", loadUsers);

    // --- Paramètres du site ---------------------------------------------
    async function loadSettings() {
        try {
            const res = await fetch("/api/admin/settings/");
            const data = await res.json();
            document.querySelectorAll("[data-setting]").forEach((input) => {
                input.checked = !!data[input.dataset.setting];
            });
        } catch (e) {
            // silencieux : les interrupteurs restent sur leur état par défaut
        }
    }

    document.querySelectorAll("[data-setting]").forEach((input) => {
        input.addEventListener("change", async () => {
            const payload = {};
            payload[input.dataset.setting] = input.checked;
            const res = await fetch("/api/admin/settings/", {
                method: "PATCH",
                headers: csrfHeaders({ "Content-Type": "application/json" }),
                body: JSON.stringify(payload),
            });
            if (!res.ok) {
                input.checked = !input.checked;
                alert("Impossible d'enregistrer ce réglage.");
            }
        });
    });

    loadStats();
    loadDatesOverview();
    loadModeration();
    loadUsers();
    loadSettings();
})();
