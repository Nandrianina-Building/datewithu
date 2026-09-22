from django.conf import settings
from django.db import models


class Block(models.Model):
    """
    Un utilisateur en bloque un autre : la personne bloquée ne peut plus lui
    envoyer d'invitation ni de message. Fonctionnalité de sécurité de base,
    attendue sur toute plateforme qui met en relation des inconnus.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Utilisateur",
        related_name="blocks_made", on_delete=models.CASCADE,
    )
    blocked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Utilisateur bloqué",
        related_name="blocked_by", on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField("Bloqué le", auto_now_add=True)

    class Meta:
        verbose_name = "Blocage"
        verbose_name_plural = "Blocages"
        unique_together = ["user", "blocked_user"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} bloque {self.blocked_user}"


class Report(models.Model):
    """Signalement d'un·e utilisateur·rice par un·e autre, pour modération."""

    REASON_INAPPROPRIATE = "inappropriate"
    REASON_FAKE = "fake_profile"
    REASON_HARASSMENT = "harassment"
    REASON_SPAM = "spam"
    REASON_OTHER = "other"
    REASON_CHOICES = [
        (REASON_INAPPROPRIATE, "Comportement ou contenu inapproprié"),
        (REASON_FAKE, "Faux profil / usurpation"),
        (REASON_HARASSMENT, "Harcèlement"),
        (REASON_SPAM, "Spam ou démarchage"),
        (REASON_OTHER, "Autre"),
    ]

    STATUS_PENDING = "pending"
    STATUS_REVIEWED = "reviewed"
    STATUS_DISMISSED = "dismissed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_REVIEWED, "Traité"),
        (STATUS_DISMISSED, "Classé sans suite"),
    ]

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Signalé par",
        related_name="reports_made", on_delete=models.CASCADE,
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Utilisateur signalé",
        related_name="reports_received", on_delete=models.CASCADE,
    )
    reason = models.CharField("Motif", max_length=20, choices=REASON_CHOICES)
    details = models.TextField("Détails", blank=True)
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField("Signalé le", auto_now_add=True)

    class Meta:
        verbose_name = "Signalement"
        verbose_name_plural = "Signalements"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reporter} → {self.reported_user} ({self.get_reason_display()})"
