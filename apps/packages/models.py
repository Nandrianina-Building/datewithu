from django.db import models
from django.utils.text import slugify

from apps.activities.models import Activity
from apps.budgets.models import Budget
from apps.catalog.models import Place
from apps.locations.models import City
from apps.moods.models import Mood


class DatePackage(models.Model):
    """
    Rendez-vous « clé en main » (section « Packages ») : une combinaison
    lieu + activité + ambiance + budget déjà assemblée par l'admin, que
    l'utilisateur peut utiliser directement au lieu de passer par les 7
    étapes du Date Builder.
    """

    name = models.CharField("Nom", max_length=150)
    slug = models.SlugField("Slug", max_length=160, unique=True, blank=True)
    description = models.TextField("Description", blank=True)
    image = models.ImageField("Image", upload_to="packages/", blank=True, null=True)

    city = models.ForeignKey(City, verbose_name="Ville", related_name="packages", on_delete=models.PROTECT)
    mood = models.ForeignKey(Mood, verbose_name="Ambiance", null=True, blank=True, on_delete=models.SET_NULL)
    budget = models.ForeignKey(Budget, verbose_name="Budget", null=True, blank=True, on_delete=models.SET_NULL)
    place = models.ForeignKey(
        Place, verbose_name="Lieu", null=True, blank=True, related_name="packages", on_delete=models.SET_NULL
    )
    activity = models.ForeignKey(
        Activity, verbose_name="Activité", null=True, blank=True, related_name="packages", on_delete=models.SET_NULL
    )

    price_estimate = models.PositiveIntegerField("Prix estimé (Ar)", default=0)

    is_featured = models.BooleanField("Mis en avant", default=False)
    is_active = models.BooleanField("Actif", default=True)
    display_order = models.PositiveIntegerField("Ordre d'affichage", default=0)

    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Package"
        verbose_name_plural = "Packages"
        ordering = ["-is_featured", "display_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
