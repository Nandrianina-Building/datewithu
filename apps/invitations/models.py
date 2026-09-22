import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.planner.models import DatePlan


class Invitation(models.Model):
    """
    Invitation générée à partir d'un DatePlan complété (section 1 : « générer
    une proposition de rendez-vous » → « partager »).

    Le partenaire n'a pas besoin de compte : il accède via un lien à token
    unique et répond Accepte / Peut-être / Décline (section 16). S'il a un
    compte et se connecte au moment de répondre, on relie `partner_user`.
    """

    STATUS_PENDING = "pending"
    STATUS_VIEWED = "viewed"
    STATUS_ACCEPTED = "accepted"
    STATUS_MAYBE = "maybe"
    STATUS_DECLINED = "declined"
    STATUS_EXPIRED = "expired"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_VIEWED, "Vue"),
        (STATUS_ACCEPTED, "Acceptée"),
        (STATUS_MAYBE, "Peut-être"),
        (STATUS_DECLINED, "Déclinée"),
        (STATUS_EXPIRED, "Expirée"),
        (STATUS_CANCELLED, "Annulée"),
    ]

    date_plan = models.OneToOneField(
        DatePlan, verbose_name="Rendez-vous", related_name="invitation", on_delete=models.CASCADE
    )
    token = models.UUIDField("Token", default=uuid.uuid4, unique=True, editable=False)

    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    partner_name = models.CharField("Nom du partenaire", max_length=100, blank=True)
    partner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Compte du partenaire",
        null=True, blank=True, related_name="received_invitations", on_delete=models.SET_NULL,
    )
    partner_reply_message = models.TextField("Message de réponse", blank=True)

    view_count = models.PositiveIntegerField("Nombre de vues", default=0)
    first_viewed_at = models.DateTimeField("Première vue le", null=True, blank=True)
    reminder_sent = models.BooleanField(
        "Rappel envoyé", default=False,
        help_text="Coché automatiquement par la commande send_date_reminders.",
    )
    responded_at = models.DateTimeField("Répondu le", null=True, blank=True)

    created_at = models.DateTimeField("Créée le", auto_now_add=True)
    expires_at = models.DateTimeField("Expire le")

    class Meta:
        verbose_name = "Invitation"
        verbose_name_plural = "Invitations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invitation #{self.pk} — {self.get_status_display()}"

    @property
    def is_expired(self):
        return self.status not in (self.STATUS_ACCEPTED, self.STATUS_MAYBE, self.STATUS_DECLINED) \
            and timezone.now() > self.expires_at

    @property
    def is_answered(self):
        return self.status in (self.STATUS_ACCEPTED, self.STATUS_MAYBE, self.STATUS_DECLINED)

    def mark_viewed(self):
        now = timezone.now()
        first_time = self.first_viewed_at is None
        if first_time:
            self.first_viewed_at = now
        self.view_count += 1
        if self.status == self.STATUS_PENDING:
            self.status = self.STATUS_VIEWED
        self.save(update_fields=["view_count", "first_viewed_at", "status"])

        if first_time:
            from apps.notifications.models import Notification, notify
            notify(
                self.date_plan.creator,
                Notification.TYPE_INVITATION_VIEWED,
                "Ton invitation a été vue",
                message=f"Ta proposition pour le {self.date_plan.date_value or '...'} a été consultée.",
                link=f"/dashboard/",
            )

    def respond(self, response, partner_name="", partner_user=None, message=""):
        mapping = {
            "accept": self.STATUS_ACCEPTED,
            "maybe": self.STATUS_MAYBE,
            "decline": self.STATUS_DECLINED,
        }
        self.status = mapping[response]
        self.partner_name = partner_name or self.partner_name
        self.partner_reply_message = message
        if partner_user is not None:
            self.partner_user = partner_user
        self.responded_at = timezone.now()
        self.save(update_fields=[
            "status", "partner_name", "partner_reply_message", "partner_user", "responded_at",
        ])

        from apps.notifications.models import Notification, notify
        notif_map = {
            self.STATUS_ACCEPTED: (Notification.TYPE_INVITATION_ACCEPTED, "Invitation acceptée"),
            self.STATUS_MAYBE: (Notification.TYPE_INVITATION_MAYBE, "Réponse : peut-être"),
            self.STATUS_DECLINED: (Notification.TYPE_INVITATION_DECLINED, "Invitation déclinée"),
        }
        notif_type, title = notif_map[self.status]
        who = self.partner_name or "Ton/ta partenaire"
        # L'action pertinente après une réponse Accepte/Peut-être est de
        # discuter avec le/la partenaire — on y renvoie directement plutôt
        # que vers le dashboard générique.
        link = f"/dates/{self.date_plan_id}/chat/" if self.status in (
            self.STATUS_ACCEPTED, self.STATUS_MAYBE,
        ) else "/dashboard/"
        notify(
            self.date_plan.creator,
            notif_type,
            title,
            message=f"{who} a répondu à ta proposition.",
            link=link,
        )
