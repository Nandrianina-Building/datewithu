from django.db import models

from apps.planner.models import DatePlan


class Conversation(models.Model):
    """
    Fil de discussion attaché à un rendez-vous (section « Communication »).

    Une conversation relie le créateur (toujours un compte) et son/sa
    partenaire (qui peut ne pas avoir de compte — identifié par le token
    de l'invitation, comme pour la réponse Accepte/Peut-être/Décline en
    Phase 4).
    """

    date_plan = models.OneToOneField(
        DatePlan, verbose_name="Rendez-vous", related_name="conversation", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField("Créée le", auto_now_add=True)

    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    def __str__(self):
        return f"Conversation #{self.pk} — {self.date_plan}"


class Message(models.Model):
    """
    Message de chat. `from_creator` distingue les deux parties sans
    imposer que le/la partenaire ait un compte utilisateur.
    """

    conversation = models.ForeignKey(
        Conversation, verbose_name="Conversation", related_name="messages", on_delete=models.CASCADE
    )
    from_creator = models.BooleanField("Envoyé par le créateur du rendez-vous")
    sender_label = models.CharField("Nom affiché de l'expéditeur", max_length=100, blank=True)
    content = models.TextField("Contenu")

    is_read = models.BooleanField("Lu par le destinataire", default=False)
    created_at = models.DateTimeField("Envoyé le", auto_now_add=True)

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender_label or ('Créateur' if self.from_creator else 'Partenaire')}: {self.content[:40]}"
