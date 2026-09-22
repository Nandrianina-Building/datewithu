from django.conf import settings
from django.db import models


class PlaceClaim(models.Model):
    """
    Un·e gérant·e de lieu revendique sa fiche pour pouvoir la modifier et
    voir ses statistiques — fonctionnalité B2B classique ("claim your
    business") qui différencie la plateforme d'un simple annuaire.
    """

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_APPROVED, "Approuvée"),
        (STATUS_REJECTED, "Refusée"),
    ]

    place = models.ForeignKey(
        "catalog.Place", verbose_name="Lieu",
        related_name="claims", on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Demandeur·se",
        related_name="place_claims", on_delete=models.CASCADE,
    )
    role = models.CharField("Rôle", max_length=100, blank=True, help_text="Ex : Gérant, Propriétaire...")
    proof_details = models.TextField(
        "Justificatif", blank=True,
        help_text="Éléments permettant de vérifier le lien avec l'établissement (numéro de téléphone pro, etc.).",
    )
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField("Demandé le", auto_now_add=True)
    reviewed_at = models.DateTimeField("Traité le", null=True, blank=True)

    class Meta:
        verbose_name = "Revendication de lieu"
        verbose_name_plural = "Revendications de lieux"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["place", "user"], name="unique_place_claim_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.place} ({self.get_status_display()})"
