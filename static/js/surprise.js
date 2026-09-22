(function () {
    "use strict";

    const btn = document.getElementById("surprise-date-btn");
    if (!btn) return;

    function getCookie(name) {
        const match = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]+)"));
        return match ? decodeURIComponent(match[2]) : null;
    }

    function getCsrfToken() {
        return document.querySelector("[name=csrfmiddlewaretoken]")?.value
            || getCookie("csrftoken")
            || "";
    }

    btn.addEventListener("click", async () => {
        const label = btn.querySelector(".tile-overlay strong") || btn;
        const originalLabel = label.innerHTML;
        btn.disabled = true;
        label.textContent = "Tirage en cours...";
        try {
            const res = await fetch("/api/date-builder/surprise/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken(),
                },
                credentials: "same-origin",
                body: JSON.stringify({}),
            });
            const data = await res.json();
            if (!res.ok) {
                alert(data.detail || "Impossible de générer une surprise pour l'instant.");
                btn.disabled = false;
                label.innerHTML = originalLabel;
                return;
            }
            window.location.href = `/date-builder/?plan=${data.plan.id}`;
        } catch (e) {
            btn.disabled = false;
            label.innerHTML = originalLabel;
        }
    });
})();
