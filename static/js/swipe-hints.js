(function () {
    "use strict";

    const selectors = ".city-scroll, #recommendations-grid";
    const cloneClass = "swiper-auto-clone";
    const mobileQuery = window.matchMedia("(max-width: 900px)");
    const reducedMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const carousels = [];

    function setup(element) {
        let animationFrame = 0;
        let lastFrameTime = 0;
        let fractionalOffset = 0;
        let loopDistance = 0;
        let pauseTimer = 0;
        let refreshFrame = 0;
        let isVisible = true;
        let isHovered = false;

        function originals() {
            return Array.from(element.children).filter((child) => !child.classList.contains(cloneClass));
        }

        function stop() {
            if (animationFrame) cancelAnimationFrame(animationFrame);
            animationFrame = 0;
            lastFrameTime = 0;
            fractionalOffset = 0;
        }

        function removeClones() {
            element.querySelectorAll(`:scope > .${cloneClass}`).forEach((clone) => clone.remove());
            element.classList.remove("is-auto-scrolling");
            loopDistance = 0;
        }

        function shouldAnimate() {
            return loopDistance > 0 && isVisible && !document.hidden && !isHovered
                && !element.matches(":focus-within") && performance.now() >= pauseTimer;
        }

        function animate(time) {
            animationFrame = 0;
            if (!shouldAnimate()) return;
            if (lastFrameTime) {
                const elapsed = Math.min(time - lastFrameTime, 48);
                const offset = fractionalOffset + elapsed * 0.06;
                const wholePixels = Math.floor(offset);
                fractionalOffset = offset - wholePixels;
                if (wholePixels) element.scrollLeft += wholePixels;
                if (element.scrollLeft >= loopDistance) element.scrollLeft -= loopDistance;
            }
            lastFrameTime = time;
            animationFrame = requestAnimationFrame(animate);
        }

        function start() {
            if (!animationFrame && shouldAnimate()) animationFrame = requestAnimationFrame(animate);
        }

        function pauseThenResume(delay) {
            stop();
            pauseTimer = performance.now() + delay;
            clearTimeout(pauseTimerId);
            pauseTimerId = window.setTimeout(start, delay);
        }

        let pauseTimerId = 0;

        function refresh() {
            stop();
            removeClones();
            const items = originals();
            const canScroll = ["auto", "scroll"].includes(getComputedStyle(element).overflowX)
                && element.scrollWidth > element.clientWidth + 2;
            if (!mobileQuery.matches || reducedMotionQuery.matches || !canScroll || items.length < 2) return;

            const clones = items.map((item) => {
                const clone = item.cloneNode(true);
                clone.classList.add(cloneClass);
                clone.removeAttribute("id");
                clone.querySelectorAll("[id]").forEach((node) => node.removeAttribute("id"));
                clone.setAttribute("aria-hidden", "true");
                clone.inert = true;
                return clone;
            });
            clones.forEach((clone) => element.appendChild(clone));
            element.classList.add("is-auto-scrolling");
            loopDistance = clones[0].getBoundingClientRect().left - items[0].getBoundingClientRect().left;
            if (loopDistance <= element.clientWidth) {
                removeClones();
                return;
            }
            start();
        }

        function scheduleRefresh() {
            if (refreshFrame) cancelAnimationFrame(refreshFrame);
            refreshFrame = requestAnimationFrame(() => {
                refreshFrame = 0;
                refresh();
            });
        }

        const mutationObserver = new MutationObserver((records) => {
            const changedOriginals = records.some((record) =>
                [...record.addedNodes, ...record.removedNodes].some((node) =>
                    node.nodeType === Node.ELEMENT_NODE && !node.classList.contains(cloneClass)));
            if (changedOriginals) scheduleRefresh();
        });
        mutationObserver.observe(element, { childList: true });
        new ResizeObserver(scheduleRefresh).observe(element);
        element.addEventListener("mouseenter", () => { isHovered = true; stop(); });
        element.addEventListener("mouseleave", () => { isHovered = false; start(); });
        element.addEventListener("focusin", stop);
        element.addEventListener("focusout", start);
        element.addEventListener("pointerdown", () => pauseThenResume(3500), { passive: true });
        element.addEventListener("touchend", () => pauseThenResume(2500), { passive: true });
        element.addEventListener("wheel", () => pauseThenResume(2500), { passive: true });
        element.addEventListener("scroll", () => {
            if (loopDistance > 0 && element.scrollLeft >= loopDistance) element.scrollLeft -= loopDistance;
        }, { passive: true });

        if ("IntersectionObserver" in window) {
            new IntersectionObserver(([entry]) => {
                isVisible = entry.isIntersecting;
                if (isVisible) start();
                else stop();
            }).observe(element);
        }

        carousels.push(scheduleRefresh);
    }

    function init() {
        document.querySelectorAll(selectors).forEach(setup);
        const refreshAll = () => carousels.forEach((refresh) => refresh());
        mobileQuery.addEventListener("change", refreshAll);
        reducedMotionQuery.addEventListener("change", refreshAll);
        document.addEventListener("visibilitychange", refreshAll);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
