from django.db import models
from django.utils.text import slugify


class City(models.Model):
    """Ville malgache administrable (section 5)."""

    name = models.CharField("Nom", max_length=100)
    slug = models.SlugField("Slug", max_length=110, unique=True, blank=True)
    region = models.CharField("Région", max_length=100, blank=True)
    description = models.TextField("Description", blank=True)
    image = models.ImageField("Image", upload_to="cities/", blank=True, null=True)

    latitude = models.DecimalField("Latitude", max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField("Longitude", max_digits=9, decimal_places=6, blank=True, null=True)

    is_active = models.BooleanField("Active", default=True)
    display_order = models.PositiveIntegerField("Ordre d'affichage", default=0)

    created_at = models.DateTimeField("Créée le", auto_now_add=True)
    updated_at = models.DateTimeField("Mise à jour le", auto_now=True)

    class Meta:
        verbose_name = "Ville"
        verbose_name_plural = "Villes"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
