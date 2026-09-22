(function () {
    "use strict";

    const btn = document.getElementById("theme-toggle-btn");
    const iconSlot = document.getElementById("theme-toggle-icon");
    if (!btn) return;

    const MOON = '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5Z"/></svg>';
    const SUN = '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4.5"/><path d="M12 2.5v2M12 19.5v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2.5 12h2M19.5 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg>';

    function currentTheme() {
        const saved = localStorage.getItem("dwu-theme");
        // Le thème sombre est la valeur par défaut de la marque (voir
        // main.css) — on ne retombe plus sur la préférence système ici,
        // seul un choix explicite de l'utilisateur bascule vers le clair.
        return saved || "dark";
    }

    function applyIcon(theme) {
        iconSlot.innerHTML = theme === "dark" ? SUN : MOON;
    }

    applyIcon(currentTheme());

    btn.addEventListener("click", () => {
        const next = currentTheme() === "dark" ? "light" : "dark";
        localStorage.setItem("dwu-theme", next);
        document.documentElement.setAttribute("data-theme", next);
        applyIcon(next);
    });
})();
