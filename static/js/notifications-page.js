/**
 * Page dédiée aux notifications : chaque élément est cliquable et amène
 * directement à l'action correspondante (voir Notification.link côté
 * back — ex. la conversation d'un rendez-vous accepté). On peut aussi
 * supprimer une notification individuellement, et la liste se charge
 * par tranches (20 à la fois) avec un chargement automatique quand on
 * approche du bas, plutôt que de tout récupérer d'un coup.
 */
(function () {
    "use strict";

    const list = document.getElementById("notifications-full-list");
    const markAllBtn = document.getElementById("mark-all-read-btn");
    const icon = (name) => (window.DWU.icon ? window.DWU.icon(name) : "");

    let currentPage = 0;
    let hasMore = true;
    let loading = false;

    const TYPE_ICONS = {
        invitation_viewed: "eye",
        invitation_accepted: "check-circle",
        invitation_maybe: "clock",
        invitation_declined: "x-circle",
        system: "message-circle",
    };

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    function timeAgo(iso) {
        const diffMs = Date.now() - new Date(iso).getTime();
        const minutes = Math.round(diffMs / 60000);
        if (minutes < 1) return "à l'instant";
        if (minutes < 60) return `il y a ${minutes} min`;
        const hours = Math.round(minutes / 60);
        if (hours < 24) return `il y a ${hours} h`;
        const days = Math.round(hours / 24);
        return `il y a ${days} j`;
    }

    async function markRead(id) {
        try {
            await fetch(`/api/notifications/${id}/read/`, {
                method: "POST",
                headers: { "X-CSRFToken": window.DWU.getCsrfToken() },
            });
        } catch (e) {
            // navigation vers le lien reste prioritaire même si le "lu" échoue
        }
    }

    async function deleteNotification(id, row) {
        row.classList.add("notif-row-removing");
        try {
            await fetch(`/api/notifications/${id}/`, {
                method: "DELETE",
                headers: { "X-CSRFToken": window.DWU.getCsrfToken() },
            });
            row.remove();
            if (!list.querySelector(".notif-row")) {
                list.innerHTML = "<li><em>Aucune notification pour l'instant.</em></li>";
            }
        } catch (e) {
            row.classList.remove("notif-row-removing");
        }
    }

    function renderRow(n) {
        const li = document.createElement("li");
        li.className = `notif-row ${n.is_read ? "" : "unread"}`;
        li.dataset.id = n.id;
        li.dataset.link = n.link || "";
        li.tabIndex = 0;
        li.setAttribute("role", "button");
        li.innerHTML = `
            <span class="notif-row-icon">${icon(TYPE_ICONS[n.type] || "bell")}</span>
            <div class="notif-row-body">
                <strong>${escapeHtml(n.title)}</strong>
                ${n.message ? `<p>${escapeHtml(n.message)}</p>` : ""}
                <span class="notif-row-time">${timeAgo(n.created_at)}</span>
            </div>
            ${!n.is_read ? `<span class="notif-dot" aria-hidden="true"></span>` : ""}
            <button type="button" class="notif-delete-btn" aria-label="Supprimer cette notification">${icon("trash")}</button>
        `;
        const activate = () => {
            const { id, link } = li.dataset;
            markRead(id);
            if (link) {
                window.location.href = link;
            } else {
                li.classList.remove("unread");
                li.querySelector(".notif-dot")?.remove();
            }
        };
        li.addEventListener("click", (e) => {
            if (e.target.closest(".notif-delete-btn")) return;
            activate();
        });
        li.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") { e.preventDefault(); activate(); }
        });
        li.querySelector(".notif-delete-btn").addEventListener("click", (e) => {
            e.stopPropagation();
            deleteNotification(n.id, li);
        });
        return li;
    }

    function ensureSentinel() {
        let sentinel = document.getElementById("notif-load-sentinel");
        if (!sentinel) {
            sentinel = document.createElement("li");
            sentinel.id = "notif-load-sentinel";
            sentinel.innerHTML = `<button type="button" id="notif-load-more-btn" class="link-btn">Charger plus de notifications</button>`;
            list.appendChild(sentinel);
            sentinel.querySelector("#notif-load-more-btn").addEventListener("click", () => loadPage());
            const observer = new IntersectionObserver((entries) => {
                if (entries[0].isIntersecting) loadPage();
            }, { rootMargin: "200px" });
            observer.observe(sentinel);
        }
        return sentinel;
    }

    async function loadPage() {
        if (loading || !hasMore) return;
        loading = true;
        const sentinel = ensureSentinel();
        sentinel.querySelector("#notif-load-more-btn").textContent = "Chargement...";

        try {
            currentPage += 1;
            const res = await fetch(`/api/notifications/?page=${currentPage}`);
            const data = await res.json();

            if (currentPage === 1 && !data.results.length) {
                list.innerHTML = "<li><em>Aucune notification pour l'instant.</em></li>";
                hasMore = false;
                loading = false;
                return;
            }

            data.results.forEach((n) => list.insertBefore(renderRow(n), sentinel));
            hasMore = !!data.has_more;
            if (!hasMore) {
                sentinel.remove();
            } else {
                sentinel.querySelector("#notif-load-more-btn").textContent = "Charger plus de notifications";
            }
        } catch (e) {
            if (currentPage === 1) {
                list.innerHTML = "<li><em>Impossible de charger tes notifications.</em></li>";
            }
        } finally {
            loading = false;
        }
    }

    markAllBtn?.addEventListener("click", async () => {
        try {
            await fetch("/api/notifications/read-all/", {
                method: "POST",
                headers: { "X-CSRFToken": window.DWU.getCsrfToken() },
            });
            list.querySelectorAll(".notif-row.unread").forEach((row) => {
                row.classList.remove("unread");
                row.querySelector(".notif-dot")?.remove();
            });
        } catch (e) {
            // silencieux
        }
    });

    loadPage();
})();
