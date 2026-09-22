from django.db import models
from django.utils.text import slugify


class Mood(models.Model):
    """
    Ambiance proposée par le Date Builder (section 8).
    Ex : ❤️ Romantique, 😂 Fun, 🌿 Nature, 🔥 Aventure, 😌 Chill...
    Entièrement administrable — l'admin peut en ajouter de nouvelles.
    """

    name = models.CharField("Nom", max_length=60)
    slug = models.SlugField("Slug", max_length=70, unique=True, blank=True)
    emoji = models.CharField("Emoji", max_length=10, blank=True)
    description = models.CharField("Description", max_length=255, blank=True)

    is_active = models.BooleanField("Active", default=True)
    display_order = models.PositiveIntegerField("Ordre d'affichage", default=0)

    class Meta:
        verbose_name = "Ambiance"
        verbose_name_plural = "Ambiances"
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.emoji} {self.name}".strip()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
