/**
 * Icônes SVG inline pour le JS (miroir de apps/core/templatetags/icons.py).
 *
 * Certaines interfaces sont entièrement rendues en JS (favoris, historique
 * des rendez-vous, partage de lien/QR code...) et utilisaient encore des
 * émojis (📋 👀 ❌ 🚫 📍 🎯) pour ces icônes-là, en décalage avec le reste du
 * site qui utilise déjà des icônes ligne cohérentes. `window.DWU.icon(name)`
 * renvoie le même tracé que le tag `{% icon %}` côté Django.
 */
window.DWU = window.DWU || {};

(function (ns) {
    "use strict";

    const PATHS = {
        copy: '<rect x="9" y="9" width="12" height="12" rx="1.5"/><path d="M6 15H4.5A1.5 1.5 0 0 1 3 13.5v-9A1.5 1.5 0 0 1 4.5 3h9A1.5 1.5 0 0 1 15 4.5V6"/>',
        eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
        "x-circle": '<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6M15 9l-6 6"/>',
        "slash-circle": '<circle cx="12" cy="12" r="9"/><path d="m6 6 12 12"/>',
        "map-pin": '<path d="M12 21s7-6.1 7-12a7 7 0 1 0-14 0c0 5.9 7 12 7 12Z"/><circle cx="12" cy="9" r="2.5"/>',
        target: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="0.8" fill="currentColor"/>',
        clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
        "message-circle": '<path d="M4 5h16v11H8l-4 4V5Z"/>',
        user: '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4.5 5-6 8-6s6.5 1.5 8 6"/>',
        bell: '<path d="M12 3a5 5 0 0 0-5 5v3.2c0 .6-.2 1.2-.6 1.7L5 15h14l-1.4-2.1a2.8 2.8 0 0 1-.6-1.7V8a5 5 0 0 0-5-5Z"/><path d="M9.5 18a2.5 2.5 0 0 0 5 0"/>',
        "check-circle": '<circle cx="12" cy="12" r="9"/><path d="m8.5 12.5 2.5 2.5 5-5"/>',
        heart: '<path d="M12 21s-7.5-4.6-10-9.3C.4 8.1 2 4.5 5.6 4.1 8 3.8 10 5 12 7.5 14 5 16 3.8 18.4 4.1 22 4.5 23.6 8.1 22 11.7 19.5 16.4 12 21 12 21Z"/>',
        qrcode: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 14h3v3h-3zM19 14h2M14 19h2M19 19h2v2h-2z"/>',
        shield: '<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3Z"/>',
        edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
        image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8.5" cy="9.5" r="1.5"/><path d="m21 15-5-5-9 9"/>',
        trash: '<path d="M4 7h16"/><path d="M6 7l1 13a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-13"/><path d="M9 7V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3"/>',
        plus: '<path d="M12 5v14"/><path d="M5 12h14"/>',
        send: '<path d="m3 11 18-8-8 18-2.5-7.5L3 11Z"/>',
        dice: '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1.2"/><circle cx="16" cy="16" r="1.2"/><circle cx="12" cy="12" r="1.2"/><circle cx="8" cy="16" r="1.2"/><circle cx="16" cy="8" r="1.2"/>',
    };

    ns.icon = function icon(name, cssClass) {
        const d = PATHS[name];
        if (!d) return "";
        return `<svg class="${cssClass || "icon"}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${d}</svg>`;
    };

    /**
     * Tronque un texte à une longueur fixe (avec un « … » de fin) — utilisé
     * partout où plusieurs cartes de même taille affichent une description
     * de longueur variable (lieux, packages, rendez-vous...), pour éviter
     * qu'une carte plus longue ne casse l'alignement de toute la grille.
     */
    ns.truncate = function truncate(str, maxLength) {
        if (!str) return "";
        return str.length > maxLength ? `${str.slice(0, maxLength - 1).trimEnd()}…` : str;
    };
})(window.DWU);
