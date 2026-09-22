/**
 * Date Builder dynamique (Phase 3 — section 12).
 * Toutes les options viennent de Django ; ce script ne fait que les
 * afficher et poster les choix de l'utilisateur en AJAX (fetch),
 * sans jamais recharger la page (section 13).
 */
(function () {
    "use strict";

    const API = window.DATE_BUILDER_API;
    const progressEl = document.getElementById("db-progress");
    const stepEl = document.getElementById("db-step");
    const errorEl = document.getElementById("db-error");

    const STEP_LABELS = {
        mood: "1. Quelle ambiance ?",
        city: "2. Dans quelle ville ?",
        place: "3. Quel lieu ?",
        activity: "4. Quelle activité ?",
        budget: "5. Quel budget ?",
        schedule: "6. Quand ?",
        final: "7. Derniers détails",
    };
    const STEP_ORDER = ["mood", "city", "place", "activity", "budget", "schedule", "final"];

    let planId = null;

    function getCookie(name) {
        const match = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]+)"));
        return match ? decodeURIComponent(match[2]) : null;
    }

    function getCsrfToken() {
        const token = document.querySelector("#date-builder [name=csrfmiddlewaretoken]")?.value
            || getCookie("csrftoken")
            || "";
        return token.trim();
    }

    async function api(path, body) {
        const opts = {
            method: body ? "POST" : "GET",
            headers: { "Content-Type": "application/json" },
        };
        if (body) {
            opts.headers["X-CSRFToken"] = getCsrfToken();
            opts.body = JSON.stringify(body);
        }
        opts.credentials = "same-origin";
        const res = await fetch(API + path, opts);
        const data = await res.json().catch(() => ({ detail: `Erreur serveur (${res.status}).` }));
        if (!res.ok) {
            throw data;
        }
        return data;
    }

    function showError(err) {
        const fieldErrors = err && err.errors
            ? Object.values(err.errors).flat().join(" ")
            : "";
        const required = err && err.required
            ? ` Champs manquants : ${err.required.join(", ")}.`
            : "";
        if (err && err.upgrade_url) {
            errorEl.innerHTML = `${err.detail || ""} <a href="${err.upgrade_url}" style="font-weight:700;text-decoration:underline;">Voir les formules Premium →</a>`;
            errorEl.style.display = "block";
            return; // pas d'auto-hide : on laisse le temps de cliquer le lien
        }
        errorEl.textContent = [err && err.detail, fieldErrors, err && err.message, required]
            .filter(Boolean)
            .join(" ") || "Une erreur est survenue, réessaie.";
        errorEl.style.display = "block";
        setTimeout(() => { errorEl.style.display = "none"; }, 4000);
    }

    function renderProgress(currentStep) {
        progressEl.innerHTML = STEP_ORDER.map((s) => {
            const done = STEP_ORDER.indexOf(s) < STEP_ORDER.indexOf(currentStep);
            const active = s === currentStep;
            return `<span class="db-dot ${done ? "done" : ""} ${active ? "active" : ""}"></span>`;
        }).join("");
    }

    function choiceButton(label, onClick) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn db-choice";
        btn.textContent = label;
        btn.addEventListener("click", onClick);
        return btn;
    }

    function photoChoiceCard(imageUrl, title, subtitle, onClick) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "db-photo-card";
        btn.innerHTML = `
            <img src="${imageUrl}" alt="">
            <div class="db-photo-overlay">
                <div>
                    <strong>${title}</strong>
                    ${subtitle ? `<span>${subtitle}</span>` : ""}
                </div>
            </div>
        `;
        btn.addEventListener("click", onClick);
        return btn;
    }

    /**
     * Grille de choix avec recherche (debounce) + pagination "Voir plus"
     * en AJAX, pour les étapes "ville" et "lieu" — plutôt que de charger
     * toutes les options d'un bloc. `buildUrl(query, page)` doit renvoyer
     * l'URL de l'API DRF paginée (ex. /api/cities/, /api/places/) et
     * `renderCard(item)` l'élément à insérer dans la grille pour un
     * résultat donné.
     */
    function renderPaginatedChoices(list, { buildUrl, renderCard, placeholder }) {
        list.className = "db-search-choices";

        const searchInput = document.createElement("input");
        searchInput.type = "search";
        searchInput.className = "db-search-input";
        searchInput.placeholder = placeholder || "Rechercher...";
        list.appendChild(searchInput);

        const grid = document.createElement("div");
        grid.className = "db-photo-choices";
        list.appendChild(grid);

        const moreWrap = document.createElement("div");
        moreWrap.className = "db-more-row";
        list.appendChild(moreWrap);

        let page = 1;
        let query = "";
        let loading = false;
        let requestToken = 0;

        async function loadPage(reset) {
            if (loading) return;
            loading = true;
            const myToken = ++requestToken;
            if (reset) {
                page = 1;
                grid.innerHTML = "<p class=\"db-search-loading\"><em>Recherche...</em></p>";
            }
            try {
                const res = await fetch(buildUrl(query, page), { credentials: "same-origin" });
                const data = await res.json().catch(() => ({}));
                if (myToken !== requestToken) return; // une recherche plus récente a été lancée entre-temps
                const results = data.results || (Array.isArray(data) ? data : []);
                if (reset) grid.innerHTML = "";
                results.forEach((item) => grid.appendChild(renderCard(item)));
                if (!results.length && reset) {
                    grid.innerHTML = "<p><em>Aucun résultat pour cette recherche.</em></p>";
                }
                moreWrap.innerHTML = "";
                if (data.next) {
                    moreWrap.appendChild(choiceButton("Voir plus →", () => { page += 1; loadPage(false); }));
                }
            } catch (e) {
                if (reset) grid.innerHTML = "<p><em>Impossible de charger les résultats.</em></p>";
            } finally {
                loading = false;
            }
        }

        let debounceTimer;
        searchInput.addEventListener("input", () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                query = searchInput.value.trim();
                loadPage(true);
            }, 300);
        });

        loadPage(true);
        return grid;
    }

    function setVisual(url) {
        const img = document.getElementById("db-visual-image");
        if (img && url) img.src = url;
    }

    function render(data) {
        planId = data.plan.id;
        renderProgress(data.next_step);
        stepEl.innerHTML = "";

        const title = document.createElement("h2");
        title.textContent = STEP_LABELS[data.next_step] || "";
        stepEl.appendChild(title);

        const list = document.createElement("div");
        list.className = "db-choices";
        stepEl.appendChild(list);

        const step = data.next_step;
        const options = data.options || {};

        if (step === "mood") {
            setVisual("https://picsum.photos/seed/dwu-step-mood/500/900");
            (options.moods || []).forEach((m) =>
                list.appendChild(choiceButton(m.name, () => submitStep({ mood: m.id })))
            );
        } else if (step === "city") {
            setVisual("https://picsum.photos/seed/dwu-step-city/500/900");
            renderPaginatedChoices(list, {
                placeholder: "Rechercher une ville...",
                buildUrl: (q, page) => {
                    const params = new URLSearchParams({ page: String(page) });
                    if (q) params.set("search", q);
                    return `/api/cities/?${params.toString()}`;
                },
                renderCard: (c) => photoChoiceCard(
                    c.image || `https://picsum.photos/seed/dwu-city-${c.slug}/400/300`,
                    c.name,
                    c.region || "",
                    () => submitStep({ city: c.id })
                ),
            });
        } else if (step === "place") {
            setVisual("https://picsum.photos/seed/dwu-step-place/500/900");
            const plan = data.plan || {};
            renderPaginatedChoices(list, {
                placeholder: "Rechercher un lieu...",
                buildUrl: (q, page) => {
                    const params = new URLSearchParams({ page: String(page) });
                    if (plan.city) params.set("city", plan.city.id);
                    if (plan.budget) params.set("budget", plan.budget.id);
                    if (plan.mood) params.set("mood", plan.mood.id);
                    if (q) params.set("search", q);
                    return `/api/places/?${params.toString()}`;
                },
                renderCard: (p) => photoChoiceCard(
                    p.main_image || `https://picsum.photos/seed/dwu-place-${p.id}/400/300`,
                    p.name,
                    p.category || "",
                    () => submitStep({ place: p.id })
                ),
            });
            list.appendChild(skipButton("place"));
        } else if (step === "activity") {
            setVisual("https://picsum.photos/seed/dwu-step-activity/500/900");
            list.className = "db-photo-choices";
            (options.activities || []).forEach((a) =>
                list.appendChild(photoChoiceCard(
                    a.image || `https://picsum.photos/seed/dwu-activity-${a.id}/400/300`,
                    a.name,
                    a.duration_minutes ? `${a.duration_minutes} min` : "",
                    () => submitStep({ activity: a.id })
                ))
            );
            list.appendChild(skipButton("activity"));
        } else if (step === "budget") {
            setVisual("https://picsum.photos/seed/dwu-step-budget/500/900");
            (options.budgets || []).forEach((b) =>
                list.appendChild(choiceButton(b.label, () => submitStep({ budget: b.id })))
            );
        } else if (step === "schedule") {
            setVisual("https://picsum.photos/seed/dwu-step-schedule/500/900");
            renderSchedule(list);
        } else if (step === "final") {
            setVisual("https://picsum.photos/seed/dwu-step-final/500/900");
            renderFinal(list, options);
        }
    }

    function skipButton(stepName) {
        return choiceButton("Passer cette étape →", () => submitStep({ skip: stepName }));
    }

    function renderSchedule(list) {
        const dateInput = document.createElement("input");
        dateInput.type = "date";
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        dateInput.min = tomorrow.toISOString().slice(0, 10);
        const timeInput = document.createElement("input");
        timeInput.type = "time";
        const submit = choiceButton("Valider", () => {
            submitStep({ date: dateInput.value, time: timeInput.value });
        });
        list.appendChild(dateInput);
        list.appendChild(timeInput);
        list.appendChild(submit);
    }

    function renderFinal(list, options) {
        const occasionSelect = document.createElement("select");
        const emptyOpt = document.createElement("option");
        emptyOpt.value = "";
        emptyOpt.textContent = "Occasion (optionnel)";
        occasionSelect.appendChild(emptyOpt);
        (options.occasions || []).forEach((o) => {
            const opt = document.createElement("option");
            opt.value = o.id;
            opt.textContent = `${o.emoji} ${o.name}`;
            occasionSelect.appendChild(opt);
        });
        list.appendChild(occasionSelect);

        const messageBox = document.createElement("textarea");
        messageBox.placeholder = "Un petit message personnel...";
        list.appendChild(messageBox);

        const attentionsWrap = document.createElement("div");
        (options.special_attentions || []).forEach((a) => {
            const label = document.createElement("label");
            const cb = document.createElement("input");
            cb.type = "checkbox";
            cb.value = a.id;
            label.appendChild(cb);
            label.append(` ${a.emoji} ${a.name}`);
            attentionsWrap.appendChild(label);
        });
        list.appendChild(attentionsWrap);

        const finishBtn = choiceButton("Générer ma proposition de rendez-vous", async () => {
            const attentions = Array.from(attentionsWrap.querySelectorAll("input:checked")).map((el) => el.value);
            finishBtn.disabled = true;
            try {
                await api(`${planId}/step/`, {
                    occasion: occasionSelect.value || undefined,
                    personal_message: messageBox.value,
                    special_attentions: attentions,
                });
                await api(`${planId}/complete/`, {});
                await createAndShowInvitation();
            } catch (err) {
                showError(err);
                finishBtn.disabled = false;
            }
        });
        list.appendChild(finishBtn);
    }

    async function createAndShowInvitation() {
        const res = await fetch("/api/invitations/create/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            credentials: "same-origin",
            body: JSON.stringify({ date_plan: planId }),
        });
        const invitation = await res.json().catch(() => ({
            detail: `Le serveur a rencontré une erreur (${res.status}). Vérifie les logs Django.`,
        }));
        if (!res.ok) {
            throw invitation;
        }
        renderShare(invitation);
    }

    function renderShare(invitation) {
        stepEl.innerHTML = `
            <h2>${(window.DWU.icon && window.DWU.icon("check-circle")) || ""} Ton rendez-vous est prêt !</h2>
            <p>Partage ce lien avec ta/ton partenaire :</p>
            ${window.DWU.renderShareCard(invitation)}
        `;
        window.DWU.bindShareCard(stepEl);
    }

    async function submitStep(payload) {
        try {
            const data = await api(`${planId}/step/`, payload);
            render(data);
        } catch (err) {
            showError(err);
        }
    }

    async function fetchState() {
        try {
            const data = await api(`${planId}/`, null);
            render(data);
        } catch (err) {
            showError(err);
        }
    }

    async function start() {
        try {
            const params = new URLSearchParams(window.location.search);
            const existingPlanId = params.get("plan");
            if (existingPlanId) {
                planId = existingPlanId;
                const data = await api(`${planId}/`, null);
                render(data);
                return;
            }
            const data = await api("start/", {});
            render(data);
        } catch (err) {
            showError(err);
        }
    }

    start();
})();
