from django.db import models


class Budget(models.Model):
    """
    Tranche de budget administrable (section 9).
    Ex : Petit budget 0-30 000 Ar, Budget moyen 30 000-80 000 Ar,
    Premium 80 000-150 000 Ar, Luxe 150 000 Ar+.
    L'admin peut modifier les montants sans toucher au code.
    """

    label = models.CharField("Nom", max_length=60)
    min_amount = models.PositiveIntegerField("Montant minimum (Ar)", default=0)
    max_amount = models.PositiveIntegerField(
        "Montant maximum (Ar)", blank=True, null=True,
        help_text="Laisser vide pour un budget sans plafond (ex : Luxe, 150 000 Ar+).",
    )

    is_active = models.BooleanField("Actif", default=True)
    display_order = models.PositiveIntegerField("Ordre d'affichage", default=0)

    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"
        ordering = ["display_order", "min_amount"]

    def __str__(self):
        if self.max_amount:
            return f"{self.label} ({self.min_amount:,} – {self.max_amount:,} Ar)".replace(",", " ")
        return f"{self.label} ({self.min_amount:,} Ar+)".replace(",", " ")
