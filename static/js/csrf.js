/**
 * Jeton CSRF partagé pour tous les appels fetch() en AJAX.
 *
 * Le cookie "csrftoken" est en HttpOnly (illisible en JS, par sécurité —
 * voir CSRF_COOKIE_HTTPONLY dans config/settings.py), donc `document.cookie`
 * ne le contient jamais. Avant ce fichier, plusieurs scripts lisaient quand
 * même le cookie et obtenaient systématiquement une chaîne vide : Django
 * refusait alors la requête (403), ce que le JS appelant confondait avec
 * "utilisateur non connecté" (ex. le message "Connecte-toi pour publier un
 * avis" qui s'affichait même en étant connecté).
 *
 * La balise <meta name="csrf-token"> posée dans templates/base.html est,
 * elle, toujours présente et lisible : c'est la source de vérité. On garde
 * les autres méthodes en secours pour rester robuste si ce fichier est
 * chargé avant que le <head> ne soit prêt sur une page inhabituelle.
 */
window.DWU = window.DWU || {};

(function (ns) {
    "use strict";

    function getCookie(name) {
        const match = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]+)"));
        return match ? decodeURIComponent(match[2]) : null;
    }

    ns.getCsrfToken = function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        const fromMeta = meta && meta.content;
        const fromForm = document.querySelector("[name=csrfmiddlewaretoken]");
        return (
            (fromMeta && fromMeta.trim())
            || (fromForm && fromForm.value)
            || getCookie("csrftoken")
            || ""
        );
    };
})(window.DWU);
