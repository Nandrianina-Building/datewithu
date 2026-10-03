(function () {
    "use strict";

    const eyeIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>';
    const eyeOffIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m3 3 18 18M10.6 10.6a2 2 0 0 0 2.8 2.8"/><path d="M9.9 5.2A10.8 10.8 0 0 1 12 5c6.5 0 10 7 10 7a16 16 0 0 1-3.1 3.8M6.2 6.2C3.5 8 2 12 2 12s3.5 7 10 7c1.1 0 2.1-.2 3-.5"/></svg>';

    document.querySelectorAll("[data-block-password-copy]").forEach((wrapper) => {
        wrapper.addEventListener("copy", (event) => event.preventDefault());
        wrapper.addEventListener("cut", (event) => event.preventDefault());
    });

    document.querySelectorAll("[data-block-password-paste]").forEach((wrapper) => {
        wrapper.addEventListener("paste", (event) => event.preventDefault());
    });

    document.querySelectorAll("[data-password-visibility-toggle]").forEach((button) => {
        const input = button.closest(".password-input-wrap")?.querySelector('input[type="password"]');
        if (!input) return;

        button.addEventListener("click", () => {
            const isVisible = input.type === "text";
            input.type = isVisible ? "password" : "text";
            button.setAttribute("aria-pressed", String(!isVisible));
            button.setAttribute(
                "aria-label",
                isVisible ? "Afficher le mot de passe" : "Masquer le mot de passe",
            );
            button.innerHTML = isVisible ? eyeIcon : eyeOffIcon;
        });
    });
})();
