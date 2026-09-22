from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify

from apps.locations.models import City

WEEKDAY_CHOICES = [
    ("mon", "Lundi"), ("tue", "Mardi"), ("wed", "Mercredi"),
    ("thu", "Jeudi"), ("fri", "Vendredi"), ("sat", "Samedi"), ("sun", "Dimanche"),
]


class Category(models.Model):
    """
    Catégorie de lieu (section 6), administrable — l'admin peut en créer
    de nouvelles librement (🍽️ Restaurant, ☕ Café, 🎬 Cinéma...).
    Le champ `parent` permet de représenter les sous-catégories sans
    dupliquer le modèle.
    """

    name = models.CharField("Nom", max_length=80)
    slug = models.SlugField("Slug", max_length=90, unique=True, blank=True)
    emoji = models.CharField("Emoji / icône", max_length=10, blank=True)
    parent = models.ForeignKey(
        "self", verbose_name="Catégorie parente",
        null=True, blank=True, related_name="children", on_delete=models.CASCADE,
    )

    is_active = models.BooleanField("Active", default=True)
    display_order = models.PositiveIntegerField("Ordre d'affichage", default=0)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.emoji} {self.name}".strip()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Place(models.Model):
    """Lieu (section 6) — l'un des modules principaux du catalogue."""

    name = models.CharField("Nom", max_length=150)
    slug = models.SlugField("Slug", max_length=160, unique=True, blank=True)
    short_description = models.CharField("Description courte", max_length=255, blank=True)
    full_description = models.TextField("Description complète", blank=True)

    category = models.ForeignKey(
        Category, verbose_name="Catégorie", related_name="places",
        limit_choices_to={"parent__isnull": True}, on_delete=models.PROTECT,
    )
    subcategory = models.ForeignKey(
        Category, verbose_name="Sous-catégorie", related_name="places_as_subcategory",
        null=True, blank=True, limit_choices_to={"parent__isnull": False},
        on_delete=models.SET_NULL,
    )

    city = models.ForeignKey(City, verbose_name="Ville", related_name="places", on_delete=models.PROTECT)
    neighborhood = models.CharField("Quartier", max_length=100, blank=True)
    address = models.CharField("Adresse", max_length=255, blank=True)

    latitude = models.DecimalField("Latitude", max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField("Longitude", max_digits=9, decimal_places=6, blank=True, null=True)

    phone = models.CharField("Téléphone", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)
    website = models.URLField("Site web", blank=True)
    facebook = models.URLField("Facebook", blank=True)
    instagram = models.URLField("Instagram", blank=True)

    price_min = models.PositiveIntegerField("Prix minimum (Ar)", default=0)
    price_max = models.PositiveIntegerField("Prix maximum (Ar)", default=0)

    main_image = models.ImageField("Image principale", upload_to="places/", blank=True, null=True)

    opening_hours = models.JSONField(
        "Horaires", blank=True, null=True,
        help_text='Ex : {"mon": "09:00-18:00", "sat": "10:00-16:00"}',
    )
    available_days = models.JSONField(
        "Jours disponibles", blank=True, null=True,
        help_text="Liste de codes jours, ex : [\"mon\", \"tue\", \"sat\"]. "
                   f"Codes valides : {', '.join(c for c, _ in WEEKDAY_CHOICES)}",
    )

    rating = models.DecimalField(
        "Note", max_digits=2, decimal_places=1, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )

    is_recommended = models.BooleanField("Lieu recommandé", default=False)
    is_popular = models.BooleanField("Lieu populaire", default=False)
    is_new = models.BooleanField("Nouveau lieu", default=False)
    is_active = models.BooleanField("Actif", default=True)
    view_count = models.PositiveIntegerField(
        "Nombre de vues", default=0,
        help_text="Incrémenté à chaque consultation du détail — utilisé pour les stats partenaires.",
    )

    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    updated_at = models.DateTimeField("Mis à jour le", auto_now=True)

    class Meta:
        verbose_name = "Lieu"
        verbose_name_plural = "Lieux"
        ordering = ["-is_recommended", "-is_popular", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PlaceImage(models.Model):
    """Image de la galerie d'un lieu (section 6 : « Galerie d'images »)."""

    place = models.ForeignKey(Place, verbose_name="Lieu", related_name="gallery", on_delete=models.CASCADE)
    image = models.ImageField("Image", upload_to="places/gallery/")
    caption = models.CharField("Légende", max_length=150, blank=True)
    display_order = models.PositiveIntegerField("Ordre d'affichage", default=0)

    class Meta:
        verbose_name = "Image de lieu"
        verbose_name_plural = "Galerie de lieux"
        ordering = ["display_order"]

    def __str__(self):
        return f"Image de {self.place.name} (#{self.display_order})"
