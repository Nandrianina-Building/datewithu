from django.db import models
from django.utils.text import slugify

from apps.budgets.models import Budget
from apps.catalog.models import Category, Place
from apps.locations.models import City
from apps.moods.models import Mood


class Activity(models.Model):
    """
    Activité (section 7) — distincte d'un lieu : un même lieu peut
    proposer plusieurs activités (ex. Parc X → promenade, pique-nique,
    photographie, coucher de soleil).
    """

    name = models.CharField("Nom", max_length=150)
    slug = models.SlugField("Slug", max_length=160, unique=True, blank=True)
    description = models.TextField("Description", blank=True)

    category = models.ForeignKey(
        Category, verbose_name="Catégorie", related_name="activities",
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    image = models.ImageField("Image", upload_to="activities/", blank=True, null=True)

    duration_minutes = models.PositiveIntegerField(
        "Durée (minutes)", blank=True, null=True,
        help_text="Durée approximative de l'activité.",
    )
    price = models.PositiveIntegerField("Prix (Ar)", default=0)

    city = models.ForeignKey(City, verbose_name="Ville", related_name="activities", on_delete=models.PROTECT)
    place = models.ForeignKey(
        Place, verbose_name="Lieu associé", related_name="activities",
        null=True, blank=True, on_delete=models.SET_NULL,
    )

    compatible_moods = models.ManyToManyField(
        Mood, verbose_name="Moods compatibles", related_name="activities", blank=True
    )
    compatible_budgets = models.ManyToManyField(
        Budget, verbose_name="Budgets compatibles", related_name="activities", blank=True
    )

    is_active = models.BooleanField("Active", default=True)

    created_at = models.DateTimeField("Créée le", auto_now_add=True)
    updated_at = models.DateTimeField("Mise à jour le", auto_now=True)

    class Meta:
        verbose_name = "Activité"
        verbose_name_plural = "Activités"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
