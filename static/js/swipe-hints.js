(function () {
    "use strict";

    const selectors = ".dash-quickbar, .city-scroll, .mydates-grid";

    function updateHint(element) {
        const hasMore = element.scrollWidth > element.clientWidth + 2;
        const atStart = element.scrollLeft <= 20;
        element.classList.toggle("has-swipe-hint", hasMore && atStart);
    }

    function setup(element) {
        updateHint(element);
        element.addEventListener("scroll", () => updateHint(element), { passive: true });
        new ResizeObserver(() => updateHint(element)).observe(element);
        new MutationObserver(() => updateHint(element)).observe(element, { childList: true });
    }

    function init() {
        document.querySelectorAll(selectors).forEach(setup);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
