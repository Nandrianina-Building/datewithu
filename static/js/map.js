(function () {
    "use strict";

    // Centré sur Antananarivo par défaut — ajuste selon ta ville principale.
    const map = L.map("places-map").setView([-18.8792, 47.5079], 12);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; contributeurs OpenStreetMap",
        maxZoom: 19,
    }).addTo(map);

    let markersLayer = L.layerGroup().addTo(map);
    let userMarker = null;
    const placeMarkerIcon = L.divIcon({
        className: "map-place-marker",
        html: '<svg viewBox="0 0 32 42" aria-hidden="true"><path d="M16 1C7.7 1 1 7.7 1 16c0 11 15 25 15 25s15-14 15-25C31 7.7 24.3 1 16 1Z"/><circle cx="16" cy="16" r="5"/></svg>',
        iconSize: [32, 42],
        iconAnchor: [16, 42],
        popupAnchor: [0, -38],
    });

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    function popupContent(place) {
        const rating = place.rating ? `★ ${place.rating}` : "";
        return `
            <div class="place-popup">
                ${place.main_image ? `<img src="${place.main_image}" alt="">` : ""}
                <h3>${escapeHtml(place.name)}</h3>
                <p style="margin:0;font-size:0.82rem;">${escapeHtml(place.category || "")}${place.category && place.city ? " · " : ""}${escapeHtml(place.city || "")} ${rating}</p>
                <button class="btn btn-primary place-detail-btn" data-id="${place.id}">Voir détails</button>
            </div>
        `;
    }

    async function loadFilters() {
        try {
            const [citiesRes, categoriesRes] = await Promise.all([
                fetch("/api/cities/"),
                fetch("/api/categories/"),
            ]);
            const cities = await citiesRes.json();
            const categories = await categoriesRes.json();
            const citySelect = document.getElementById("map-filter-city");
            const categorySelect = document.getElementById("map-filter-category");

            const cityList = cities.results || cities;
            cityList.forEach((c) => {
                citySelect.insertAdjacentHTML("beforeend", `<option value="${c.id}">${escapeHtml(c.name)}</option>`);
            });
            const antananarivo = cityList.find(
                (city) => city.name.trim().toLocaleLowerCase("fr") === "antananarivo",
            );
            if (antananarivo) citySelect.value = String(antananarivo.id);
            (categories.results || categories).forEach((c) => {
                categorySelect.insertAdjacentHTML("beforeend", `<option value="${c.id}">${escapeHtml(c.name)}</option>`);
            });
        } catch (e) {
            // Filtres non bloquants : la carte fonctionne quand même sans eux.
        }
    }

    async function loadPlaces() {
        const params = new URLSearchParams();
        const city = document.getElementById("map-filter-city").value;
        const category = document.getElementById("map-filter-category").value;
        if (city) params.set("city", city);
        if (category) params.set("category", category);

        try {
            const res = await fetch(`/api/places/?${params.toString()}`);
            const data = await res.json();
            const places = (data.results || data).filter((p) => p.latitude && p.longitude);

            markersLayer.clearLayers();
            if (!places.length) return;

            const bounds = [];
            places.forEach((p) => {
                const lat = parseFloat(p.latitude);
                const lng = parseFloat(p.longitude);
                const marker = L.marker([lat, lng], { icon: placeMarkerIcon }).addTo(markersLayer);
                marker.bindPopup(popupContent(p));
                marker.on("popupopen", (e) => {
                    const btn = e.popup.getElement().querySelector(".place-detail-btn");
                    if (btn) btn.addEventListener("click", () => window.DWU.openPlaceDetail(btn.dataset.id));
                });
                bounds.push([lat, lng]);
            });
            if (bounds.length > 1) map.fitBounds(bounds, { padding: [30, 30] });
        } catch (e) {
            console.error("Impossible de charger les lieux sur la carte.", e);
        }
    }

    document.getElementById("map-filter-city").addEventListener("change", loadPlaces);
    document.getElementById("map-filter-category").addEventListener("change", loadPlaces);

    document.getElementById("map-locate-btn").addEventListener("click", () => {
        if (!navigator.geolocation) {
            alert("La géolocalisation n'est pas disponible sur ce navigateur.");
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const { latitude, longitude } = pos.coords;
                if (userMarker) map.removeLayer(userMarker);
                userMarker = L.circleMarker([latitude, longitude], {
                    radius: 8,
                    color: "#d94675",
                    fillColor: "#d94675",
                    fillOpacity: 0.6,
                }).addTo(map).bindPopup("Toi").openPopup();
                map.setView([latitude, longitude], 14);
            },
            () => alert("Impossible de récupérer ta position — vérifie les autorisations du navigateur."),
        );
    });

    async function initializeMap() {
        await loadFilters();
        await loadPlaces();
    }

    initializeMap();
})();
