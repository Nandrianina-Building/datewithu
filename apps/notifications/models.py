from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    Notification interne (Phase 5). Générées automatiquement par le
    système (ex. invitation vue/acceptée) — l'admin ne les crée pas à la
    main, mais peut les consulter/purger depuis le Django Admin.
    """

    TYPE_INVITATION_VIEWED = "invitation_viewed"
    TYPE_INVITATION_ACCEPTED = "invitation_accepted"
    TYPE_INVITATION_MAYBE = "invitation_maybe"
    TYPE_INVITATION_DECLINED = "invitation_declined"
    TYPE_SYSTEM = "system"
    TYPE_CHOICES = [
        (TYPE_INVITATION_VIEWED, "Invitation vue"),
        (TYPE_INVITATION_ACCEPTED, "Invitation acceptée"),
        (TYPE_INVITATION_MAYBE, "Invitation en peut-être"),
        (TYPE_INVITATION_DECLINED, "Invitation déclinée"),
        (TYPE_SYSTEM, "Système"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Destinataire",
        related_name="notifications", on_delete=models.CASCADE,
    )
    notif_type = models.CharField("Type", max_length=30, choices=TYPE_CHOICES, default=TYPE_SYSTEM)
    title = models.CharField("Titre", max_length=150)
    message = models.CharField("Message", max_length=255, blank=True)
    link = models.CharField("Lien", max_length=255, blank=True, help_text="Chemin relatif, ex: /dashboard/")

    is_read = models.BooleanField("Lue", default=False)
    created_at = models.DateTimeField("Créée le", auto_now_add=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} → {self.user}"


def notify(user, notif_type, title, message="", link=""):
    """Petite fonction utilitaire pour créer une notification depuis
    n'importe quel autre module (ex. apps.invitations.models)."""
    notification = Notification.objects.create(
        user=user, notif_type=notif_type, title=title, message=message, link=link,
    )
    # En plus de la notification in-app : un e-mail pour les événements qui
    # méritent qu'on soit prévenu même hors ligne (réponse à une invitation,
    # nouveau message) — mais pas pour "invitation vue", trop fréquent pour
    # justifier un e-mail. Respecte la préférence utilisateur
    # `email_notifications_enabled` (profil).
    if (
        notif_type != Notification.TYPE_INVITATION_VIEWED
        and getattr(user, "email_notifications_enabled", True)
        and user.email
    ):
        _send_notification_email(user, title, message, link)
    return notification


def _send_notification_email(user, title, message, link):
    from django.conf import settings
    from django.core.mail import send_mail

    body_lines = [
        f"Bonjour {user.first_name or user.username},",
        "",
        title,
    ]
    if message:
        body_lines.append(message)
    if link:
        base_url = getattr(settings, "SITE_BASE_URL", "").rstrip("/")
        body_lines += ["", f"Voir : {base_url}{link}" if base_url else f"Voir dans l'application : {link}"]
    body_lines += [
        "",
        "Tu reçois cet e-mail parce que les notifications par e-mail sont activées sur ton "
        "compte — tu peux les désactiver à tout moment depuis ton profil.",
        "",
        "— L'équipe Date With U",
    ]
    try:
        send_mail(
            f"{title} — Date With U",
            "\n".join(body_lines),
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
    except Exception:
        pass
