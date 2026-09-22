(function () {
    "use strict";

    const token = window.DWU_TRACK_TOKEN;
    const subtitle = document.getElementById("track-subtitle");
    const statusBox = document.getElementById("track-status");
    let map, marker;

    function initMap(lat, lng) {
        map = L.map("track-map").setView([lat, lng], 15);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "&copy; OpenStreetMap",
        }).addTo(map);
        marker = L.marker([lat, lng]).addTo(map);
    }

    function timeAgo(iso) {
        if (!iso) return "jamais";
        const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
        if (minutes < 1) return "à l'instant";
        if (minutes < 60) return `il y a ${minutes} min`;
        return `il y a ${Math.round(minutes / 60)} h`;
    }

    async function poll() {
        try {
            const res = await fetch(`/api/safeshare/${token}/`);
            if (!res.ok) {
                subtitle.textContent = "Ce lien de suivi n'existe pas ou plus.";
                return;
            }
            const data = await res.json();
            subtitle.textContent = `${data.user_name} partage sa position avec toi${data.contact_name ? ` (${data.contact_name})` : ""}.`;

            if (!data.is_active) {
                statusBox.innerHTML = `<p><strong>Ce partage de position est terminé.</strong> Dernière position connue affichée ci-dessous.</p>`;
            } else {
                statusBox.innerHTML = `<p>Position mise à jour ${timeAgo(data.last_updated_at)}.</p>`;
            }

            if (data.latitude && data.longitude) {
                const lat = parseFloat(data.latitude);
                const lng = parseFloat(data.longitude);
                if (!map) {
                    initMap(lat, lng);
                } else {
                    marker.setLatLng([lat, lng]);
                    map.panTo([lat, lng]);
                }
            } else if (!map) {
                statusBox.innerHTML += `<p><em>En attente de la première position...</em></p>`;
            }

            if (data.is_active) {
                setTimeout(poll, 15000);
            }
        } catch (e) {
            setTimeout(poll, 15000);
        }
    }

    poll();
})();
