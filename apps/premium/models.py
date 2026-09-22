from django.conf import settings
from django.db import models
from django.utils import timezone


class PremiumPlan(models.Model):
    """
    Formule payante. Le paiement réel (Mobile Money — MVola / Orange Money /
    Airtel Money — étant l'option la plus pertinente à Madagascar) n'est pas
    intégré ici : aucune passerelle de paiement locale n'expose d'API
    publique testable depuis cet environnement. Le circuit prévu est donc :
    demande d'activation → validation manuelle par un admin (voir
    `Subscription.STATUS_PENDING`) → activation. Le jour où une passerelle
    est choisie, il suffit de brancher la confirmation de paiement sur
    `Subscription.activate()`.
    """

    name = models.CharField("Nom", max_length=100)
    slug = models.SlugField("Slug", unique=True, blank=True)
    price = models.PositiveIntegerField("Prix (Ar / mois)")
    duration_days = models.PositiveIntegerField("Durée (jours)", default=30)
    max_active_dates = models.PositiveIntegerField(
        "Rendez-vous actifs simultanés", null=True, blank=True,
        help_text="Laisser vide = illimité (formule Premium).",
    )
    perks = models.TextField(
        "Avantages", blank=True,
        help_text="Un avantage par ligne, affiché sur la page tarifs.",
    )
    is_active = models.BooleanField("Actif", default=True)
    display_order = models.PositiveIntegerField("Ordre d'affichage", default=0)

    class Meta:
        verbose_name = "Formule Premium"
        verbose_name_plural = "Formules Premium"
        ordering = ["display_order", "price"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def perks_list(self):
        return [line.strip() for line in self.perks.splitlines() if line.strip()]


class Subscription(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ACTIVE = "active"
    STATUS_EXPIRED = "expired"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente de validation"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_EXPIRED, "Expirée"),
        (STATUS_REJECTED, "Refusée"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Utilisateur",
        related_name="subscriptions", on_delete=models.CASCADE,
    )
    plan = models.ForeignKey(PremiumPlan, verbose_name="Formule", on_delete=models.PROTECT)
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    requested_at = models.DateTimeField("Demandée le", auto_now_add=True)
    activated_at = models.DateTimeField("Activée le", null=True, blank=True)
    expires_at = models.DateTimeField("Expire le", null=True, blank=True)
    payment_reference = models.CharField(
        "Référence de paiement", max_length=120, blank=True,
        help_text="Ex : référence de transfert Mobile Money, à vérifier manuellement pour l'instant.",
    )

    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.user} — {self.plan} ({self.get_status_display()})"

    def activate(self):
        self.status = self.STATUS_ACTIVE
        self.activated_at = timezone.now()
        self.expires_at = self.activated_at + timezone.timedelta(days=self.plan.duration_days)
        self.save(update_fields=["status", "activated_at", "expires_at"])
        User = self.user.__class__
        User.objects.filter(pk=self.user_id).update(is_premium=True)

    @property
    def is_currently_active(self):
        return self.status == self.STATUS_ACTIVE and self.expires_at and self.expires_at > timezone.now()
