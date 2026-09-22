/**
 * Remplace le <input type="file"> natif (avec son bouton "Choisir un
 * fichier") par une zone cliquable affichant directement un aperçu de la
 * photo de profil. Le champ de formulaire d'origine reste dans le DOM
 * (masqué visuellement) pour que la soumission du formulaire continue de
 * fonctionner normalement.
 */
(function () {
    "use strict";

    const trigger = document.getElementById("avatar-picker-trigger");
    if (!trigger) return;

    const fileInput = document.querySelector('#profile-edit-form input[type="file"][name="avatar"]')
        || document.querySelector('input[type="file"][name="avatar"]');
    const previewImg = document.getElementById("avatar-preview-img");
    const fallback = document.getElementById("avatar-preview-fallback");

    if (!fileInput) return;

    trigger.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", () => {
        const file = fileInput.files && fileInput.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            previewImg.style.display = "block";
            if (fallback) fallback.style.display = "none";
        };
        reader.readAsDataURL(file);
    });
})();
