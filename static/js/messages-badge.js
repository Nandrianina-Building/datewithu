(function () {
    "use strict";

    async function refreshBadge() {
        const badges = document.querySelectorAll(".js-messages-badge");
        if (!badges.length) return;
        try {
            const res = await fetch("/api/messages/");
            const items = await res.json();
            const unread = items.reduce((sum, i) => sum + (i.unread || 0), 0);
            badges.forEach((badge) => {
                if (unread > 0) {
                    badge.textContent = unread;
                    badge.style.display = "inline-block";
                } else {
                    badge.style.display = "none";
                }
            });
        } catch (e) {
            // silencieux : le badge n'est qu'un indicateur secondaire
        }
    }

    refreshBadge();
})();
