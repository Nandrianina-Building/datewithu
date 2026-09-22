from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Utilisateur Date With U.

    On étend AbstractUser plutôt que de repartir de zéro : on garde
    username/email/password/is_staff/is_superuser gratuitement, et
    is_staff donne déjà accès au dashboard admin Django — pratique
    pour la Phase 1. Les champs métier (ville préférée, moods...)
    arriveront en Phase 2/3 une fois les modèles de contenu créés.
    """

    phone = models.CharField("Téléphone", max_length=20, blank=True)
    avatar = models.ImageField(
        "Photo de profil", upload_to="avatars/", blank=True, null=True
    )
    bio = models.TextField("Bio", blank=True)
    birth_date = models.DateField("Date de naissance", blank=True, null=True)

    is_verified = models.BooleanField(
        "Compte vérifié", default=False,
        help_text="Vérification email/téléphone (à activer en Phase 5).",
    )
    email_notifications_enabled = models.BooleanField(
        "Recevoir les notifications par e-mail", default=True,
        help_text="Invitation acceptée/déclinée, nouveau message... "
        "en plus des notifications dans l'application.",
    )
    accepted_terms_at = models.DateTimeField(
        "CGU acceptées le", null=True, blank=True,
        help_text="Horodatage de l'acceptation des CGU à l'inscription.",
    )
    is_premium = models.BooleanField(
        "Compte Premium", default=False,
        help_text="Mis à jour automatiquement par Subscription.activate().",
    )
    identity_verified = models.BooleanField(
        "Identité vérifiée (selfie)", default=False,
    )
    selfie_photo = models.ImageField(
        "Photo de vérification", upload_to="verification/", null=True, blank=True,
        help_text="Photo privée utilisée uniquement pour la vérification manuelle d'identité — jamais affichée publiquement.",
    )

    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    updated_at = models.DateTimeField("Mis à jour le", auto_now=True)

    #: Champs obligatoires à compléter avant d'accéder au dashboard —
    #: garantit qu'on a de quoi personnaliser le Date Builder (téléphone
    #: pour être recontacté, date de naissance pour les suggestions
    #: d'occasions...).
    REQUIRED_PROFILE_FIELDS = ["first_name", "last_name", "phone", "birth_date"]

    @property
    def has_completed_profile(self):
        return all(getattr(self, field) for field in self.REQUIRED_PROFILE_FIELDS)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["-created_at"]

    def __str__(self):
        return self.get_full_name() or self.username
