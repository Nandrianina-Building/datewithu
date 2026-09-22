from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.catalog.models import Place


class Review(models.Model):
    """Avis laissé par un utilisateur sur un lieu (section « Avis »)."""

    place = models.ForeignKey(Place, verbose_name="Lieu", related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Auteur", related_name="reviews", on_delete=models.CASCADE
    )
    rating = models.PositiveSmallIntegerField(
        "Note", validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField("Commentaire", blank=True)

    owner_reply = models.TextField(
        "Réponse du gérant", blank=True,
        help_text="Réponse publique du/de la partenaire ayant revendiqué ce lieu (voir apps.partners).",
    )
    owner_reply_at = models.DateTimeField("Répondu le", null=True, blank=True)

    created_at = models.DateTimeField("Publié le", auto_now_add=True)

    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        unique_together = ["place", "user"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.place} ({self.rating}/5)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._recompute_place_rating()

    def delete(self, *args, **kwargs):
        place = self.place
        super().delete(*args, **kwargs)
        self._recompute_place_rating(place)

    def _recompute_place_rating(self, place=None):
        place = place or self.place
        agg = Review.objects.filter(place=place).aggregate(models.Avg("rating"))
        place.rating = round(agg["rating__avg"] or 0, 1)
        place.save(update_fields=["rating"])


class DateRating(models.Model):
    """
    Note mutuelle après un rendez-vous : contrairement à `Review` (qui note
    un LIEU), ceci note la PERSONNE avec qui le rendez-vous a eu lieu — un
    signal de confiance affiché en note de fiabilité sur le profil public.
    """

    date_plan = models.ForeignKey(
        "planner.DatePlan", verbose_name="Rendez-vous",
        related_name="date_ratings", on_delete=models.CASCADE,
    )
    rater = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Noté par",
        related_name="date_ratings_given", on_delete=models.CASCADE,
    )
    rated_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Utilisateur noté",
        related_name="date_ratings_received", on_delete=models.CASCADE,
    )
    stars = models.PositiveSmallIntegerField(
        "Note", validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.CharField("Commentaire", max_length=300, blank=True)
    created_at = models.DateTimeField("Publié le", auto_now_add=True)

    class Meta:
        verbose_name = "Note de rendez-vous"
        verbose_name_plural = "Notes de rendez-vous"
        unique_together = ["date_plan", "rater", "rated_user"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rater} note {self.rated_user} : {self.stars}/5"
