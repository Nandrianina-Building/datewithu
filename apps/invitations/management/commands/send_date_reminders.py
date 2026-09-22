"""
Envoie un rappel (notification in-app + e-mail si activé) aux deux
participant·e·s d'un rendez-vous accepté qui a lieu demain.

Pensé pour être lancé une fois par jour via une tâche planifiée — par
exemple un "Scheduled task" PythonAnywhere (gratuit, une exécution/jour) :

    python manage.py send_date_reminders

Idempotent : un flag `reminder_sent` sur l'invitation évite les doublons
si la commande est relancée plusieurs fois le même jour.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.invitations.models import Invitation
from apps.notifications.models import Notification, notify


class Command(BaseCommand):
    help = "Envoie un rappel aux participant·e·s des rendez-vous qui ont lieu demain."

    def handle(self, *args, **options):
        tomorrow = (timezone.now() + timezone.timedelta(days=1)).date()

        invitations = Invitation.objects.filter(
            status__in=[Invitation.STATUS_ACCEPTED, Invitation.STATUS_MAYBE],
            date_plan__date_value=tomorrow,
            reminder_sent=False,
        ).select_related("date_plan", "date_plan__creator", "date_plan__place", "partner_user")

        sent = 0
        for invitation in invitations:
            plan = invitation.date_plan
            where = plan.place.name if plan.place_id else (plan.activity.name if plan.activity_id else "ton rendez-vous")
            when = plan.time_value.strftime("%H:%M") if plan.time_value else ""

            notify(
                plan.creator,
                Notification.TYPE_SYSTEM,
                "Rappel : ton rendez-vous est demain",
                message=f"{where}{f' à {when}' if when else ''}, demain.",
                link=f"/dates/{plan.id}/chat/",
            )
            if invitation.partner_user_id:
                notify(
                    invitation.partner_user,
                    Notification.TYPE_SYSTEM,
                    "Rappel : ton rendez-vous est demain",
                    message=f"{where}{f' à {when}' if when else ''}, demain.",
                    link=f"/invite/{invitation.token}/chat/",
                )

            invitation.reminder_sent = True
            invitation.save(update_fields=["reminder_sent"])
            sent += 1

        self.stdout.write(self.style.SUCCESS(f"{sent} rappel(s) envoyé(s) pour le {tomorrow}."))
