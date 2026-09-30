(function () {
    "use strict";

    const greeting = document.getElementById("dashboard-greeting-word");
    if (!greeting) return;

    greeting.textContent = new Date().getHours() >= 18 ? "Bonsoir" : "Bonjour";
})();