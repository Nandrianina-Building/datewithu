(function () {
    "use strict";

    async function refreshBadge() {
        const badges = document.querySelectorAll(".js-notif-badge");
        if (!badges.length) return;
        try {
            const res = await fetch("/api/notifications/?unread=1");
            const data = await res.json();
            badges.forEach((badge) => {
                if (data.unread_count > 0) {
                    badge.textContent = data.unread_count;
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
