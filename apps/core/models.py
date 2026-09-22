from django.core.exceptions import ValidationError
from django.db import models


class SiteConfiguration(models.Model):
    """
    Réglages généraux du site (section 109 du cahier des charges).

    Singleton : un seul enregistrement doit exister. Les modules de
    contenu (villes, lieux, activités...) arriveront en Phase 2 dans
    des apps dédiées (apps.locations, apps.places, ...) pour ne pas
    tout entasser dans un seul models.py géant.
    """

    site_name = models.CharField("Nom du site", max_length=100, default="Date With U")
    logo = models.ImageField("Logo", upload_to="site/", blank=True, null=True)
    contact_email = models.EmailField("Email de contact", blank=True)
    contact_phone = models.CharField("Téléphone de contact", max_length=20, blank=True)

    default_currency = models.CharField("Devise par défaut", max_length=10, default="MGA")
    invitation_expiration_days = models.PositiveIntegerField(
        "Expiration des invitations (jours)", default=7
    )

    maintenance_mode = models.BooleanField("Mode maintenance", default=False)
    registration_enabled = models.BooleanField("Inscriptions activées", default=True)
    chat_enabled = models.BooleanField("Chat activé", default=False)
    reviews_enabled = models.BooleanField("Avis activés", default=False)

    updated_at = models.DateTimeField("Mis à jour le", auto_now=True)

    class Meta:
        verbose_name = "Configuration du site"
        verbose_name_plural = "Configuration du site"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # Le singleton ne doit jamais être supprimé.

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def clean(self):
        if SiteConfiguration.objects.exclude(pk=1).exists():
            raise ValidationError("Une seule configuration de site est autorisée.")
