from django.db import models
from django.utils import timezone


class Article(models.Model):
    """Article de magazine ("Top 10 spots romantiques à Tana"...) — bon
    pour le SEO (contenu indexable, voir sitemap) et pour donner une vraie
    identité éditoriale à la plateforme au-delà du simple annuaire."""

    title = models.CharField("Titre", max_length=200)
    slug = models.SlugField("Slug", max_length=220, unique=True, blank=True)
    excerpt = models.CharField("Accroche", max_length=300, blank=True)
    content = models.TextField("Contenu", help_text="Markdown simple (titres ##, listes -, gras **texte**).")
    cover_image = models.ImageField("Image de couverture", upload_to="blog/", blank=True, null=True)
    city = models.ForeignKey(
        "locations.City", verbose_name="Ville concernée", null=True, blank=True,
        related_name="articles", on_delete=models.SET_NULL,
    )
    is_published = models.BooleanField("Publié", default=False)
    published_at = models.DateTimeField("Publié le", default=timezone.now)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)[:220]
        super().save(*args, **kwargs)
