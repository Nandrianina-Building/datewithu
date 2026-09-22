from django.db import models
from django.utils import timezone


class PromoCode(models.Model):
    """Code promo négocié avec un partenaire (lieu) — affiché sur la fiche
    du lieu et validable côté client avant/au moment de proposer un
    rendez-vous."""

    code = models.CharField("Code", max_length=40, unique=True)
    place = models.ForeignKey(
        "catalog.Place", verbose_name="Lieu", related_name="promo_codes",
        null=True, blank=True, on_delete=models.CASCADE,
        help_text="Laisser vide pour un code valable sur tous les lieux.",
    )
    description = models.CharField("Description", max_length=255, help_text="Ex : -15% sur l'addition, boisson offerte...")
    discount_percent = models.PositiveSmallIntegerField("Réduction (%)", null=True, blank=True)
    valid_from = models.DateTimeField("Valide à partir de", default=timezone.now)
    valid_until = models.DateTimeField("Valide jusqu'au")
    max_uses = models.PositiveIntegerField("Utilisations max", null=True, blank=True, help_text="Vide = illimité.")
    used_count = models.PositiveIntegerField("Utilisations", default=0)
    is_active = models.BooleanField("Actif", default=True)

    class Meta:
        verbose_name = "Code promo"
        verbose_name_plural = "Codes promo"
        ordering = ["-valid_from"]

    def __str__(self):
        return f"{self.code} — {self.place or 'tous lieux'}"

    @property
    def is_valid(self):
        now = timezone.now()
        if not self.is_active or now < self.valid_from or now > self.valid_until:
            return False
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False
        return True
