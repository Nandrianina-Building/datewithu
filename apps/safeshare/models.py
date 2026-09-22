import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class LocationShare(models.Model):
    """
    « Prévenir un·e proche » : pendant un rendez-vous, l'utilisateur peut
    partager sa position en direct via un lien temporaire (aucun compte
    requis pour le/la destinataire). Fonctionnalité de sécurité classique
    sur les apps qui mettent en relation des inconnus.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Partagé par",
        related_name="location_shares", on_delete=models.CASCADE,
    )
    date_plan = models.ForeignKey(
        "planner.DatePlan", verbose_name="Rendez-vous concerné",
        related_name="location_shares", null=True, blank=True, on_delete=models.CASCADE,
    )
    token = models.UUIDField("Jeton", default=uuid.uuid4, unique=True, editable=False)
    contact_name = models.CharField("Nom du proche prévenu", max_length=100, blank=True)
    latitude = models.DecimalField("Latitude", max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField("Longitude", max_digits=9, decimal_places=6, null=True, blank=True)
    last_updated_at = models.DateTimeField("Dernière position le", null=True, blank=True)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    expires_at = models.DateTimeField("Expire le")
    is_active = models.BooleanField("Actif", default=True)

    class Meta:
        verbose_name = "Partage de position"
        verbose_name_plural = "Partages de position"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Position de {self.user} — {'actif' if self.is_currently_active else 'terminé'}"

    @property
    def is_currently_active(self):
        return self.is_active and self.expires_at > timezone.now()

    def update_position(self, lat, lng):
        self.latitude = lat
        self.longitude = lng
        self.last_updated_at = timezone.now()
        self.save(update_fields=["latitude", "longitude", "last_updated_at"])
