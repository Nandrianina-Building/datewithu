from django.conf import settings
from django.db import models

from apps.activities.models import Activity
from apps.catalog.models import Place


class FavoritePlace(models.Model):
    """Lieu mis en favori par un utilisateur (Phase 5)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Utilisateur",
        related_name="favorite_places", on_delete=models.CASCADE,
    )
    place = models.ForeignKey(Place, verbose_name="Lieu", related_name="favorited_by", on_delete=models.CASCADE)
    created_at = models.DateTimeField("Ajouté le", auto_now_add=True)

    class Meta:
        verbose_name = "Lieu favori"
        verbose_name_plural = "Lieux favoris"
        unique_together = ["user", "place"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} ❤️ {self.place}"


class FavoriteActivity(models.Model):
    """Activité mise en favori par un utilisateur (Phase 5)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Utilisateur",
        related_name="favorite_activities", on_delete=models.CASCADE,
    )
    activity = models.ForeignKey(
        Activity, verbose_name="Activité", related_name="favorited_by", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField("Ajoutée le", auto_now_add=True)

    class Meta:
        verbose_name = "Activité favorite"
        verbose_name_plural = "Activités favorites"
        unique_together = ["user", "activity"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} ❤️ {self.activity}"
