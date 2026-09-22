from django.conf import settings
from django.db import models

from apps.activities.models import Activity
from apps.budgets.models import Budget
from apps.catalog.models import Place
from apps.locations.models import City
from apps.moods.models import Mood
from apps.occasions.models import Occasion

# Les 7 étapes du Date Builder dynamique (section 12). L'ordre fait foi
# pour calculer `next_step` — mais chaque étape reste indépendante côté
# API : le frontend peut très bien en sauter certaines si le mood/budget
# rendent un choix inutile (ex. pas de lieu disponible pour ce budget).
STEP_MOOD = "mood"
STEP_CITY = "city"
STEP_PLACE = "place"
STEP_ACTIVITY = "activity"
STEP_BUDGET = "budget"
STEP_SCHEDULE = "schedule"
STEP_FINAL = "final"

STEP_ORDER = [
    STEP_MOOD, STEP_CITY, STEP_PLACE, STEP_ACTIVITY,
    STEP_BUDGET, STEP_SCHEDULE, STEP_FINAL,
]


class PreferenceQuestion(models.Model):
    """
    Question binaire du Date Builder (section 11).
    Ex : "Indoor / Outdoor", "Jour / Nuit", "Calme / Animé"...
    L'admin peut ajouter de nouvelles questions sans toucher au code.
    """

    question = models.CharField("Question", max_length=100, help_text='Ex : "Indoor / Outdoor"')
    option_a = models.CharField("Option A", max_length=50)
    option_b = models.CharField("Option B", max_length=50)

    is_active = models.BooleanField("Active", default=True)
    display_order = models.PositiveIntegerField("Ordre d'affichage", default=0)

    class Meta:
        verbose_name = "Question de préférence"
        verbose_name_plural = "Questions de préférence"
        ordering = ["display_order"]

    def __str__(self):
        return f"{self.option_a} / {self.option_b}"


class SpecialAttention(models.Model):
    """
    « Petite attention » proposée en dernière étape du Date Builder
    (ex. 🎁 apporter un petit cadeau, 🌹 prévoir des fleurs, 📸 prendre des
    photos souvenir). Administrable comme le reste du contenu.
    """

    name = models.CharField("Nom", max_length=100)
    emoji = models.CharField("Emoji", max_length=10, blank=True)
    description = models.CharField("Description", max_length=255, blank=True)

    is_active = models.BooleanField("Active", default=True)
    display_order = models.PositiveIntegerField("Ordre d'affichage", default=0)

    class Meta:
        verbose_name = "Petite attention"
        verbose_name_plural = "Petites attentions"
        ordering = ["display_order"]

    def __str__(self):
        return f"{self.emoji} {self.name}".strip()


class DatePlan(models.Model):
    """
    Rendez-vous en cours de construction via le Date Builder (section 1 et 12).

    Un DatePlan appartient toujours à son créateur. Tant que
    `status == "draft"`, il est modifiable étape par étape (autosave à
    chaque appel AJAX). Une fois `status == "completed"`, il devient la
    base de l'invitation générée en Phase 4.
    """

    STATUS_DRAFT = "draft"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Brouillon"),
        (STATUS_COMPLETED, "Complété"),
    ]

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Créateur",
        related_name="date_plans", on_delete=models.CASCADE,
    )

    mood = models.ForeignKey(Mood, verbose_name="Ambiance", null=True, blank=True, on_delete=models.SET_NULL)
    city = models.ForeignKey(City, verbose_name="Ville", null=True, blank=True, on_delete=models.SET_NULL)
    place = models.ForeignKey(Place, verbose_name="Lieu", null=True, blank=True, on_delete=models.SET_NULL)
    activity = models.ForeignKey(Activity, verbose_name="Activité", null=True, blank=True, on_delete=models.SET_NULL)
    budget = models.ForeignKey(Budget, verbose_name="Budget", null=True, blank=True, on_delete=models.SET_NULL)
    occasion = models.ForeignKey(Occasion, verbose_name="Occasion", null=True, blank=True, on_delete=models.SET_NULL)

    date_value = models.DateField("Date", null=True, blank=True)
    time_value = models.TimeField("Heure", null=True, blank=True)

    special_attentions = models.ManyToManyField(
        SpecialAttention, verbose_name="Petites attentions", blank=True, related_name="date_plans"
    )
    personal_message = models.TextField("Message personnel", blank=True)

    current_step = models.CharField(
        "Étape courante", max_length=20, choices=[(s, s) for s in STEP_ORDER], default=STEP_MOOD
    )
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    updated_at = models.DateTimeField("Mis à jour le (autosave)", auto_now=True)

    class Meta:
        verbose_name = "Rendez-vous en construction"
        verbose_name_plural = "Rendez-vous en construction"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"DatePlan #{self.pk} de {self.creator} ({self.get_status_display()})"

    @property
    def is_complete_enough_to_finalize(self):
        """Champs jugés indispensables pour passer en `completed` (section 1)."""
        return all([self.mood_id, self.city_id, self.budget_id, self.date_value, self.time_value]) \
            and (self.place_id or self.activity_id)


class DatePlanPreferenceAnswer(models.Model):
    """Réponse (A ou B) du créateur à une PreferenceQuestion, pour un DatePlan donné."""

    CHOICE_A = "a"
    CHOICE_B = "b"
    CHOICE_CHOICES = [(CHOICE_A, "Option A"), (CHOICE_B, "Option B")]

    date_plan = models.ForeignKey(DatePlan, related_name="preference_answers", on_delete=models.CASCADE)
    question = models.ForeignKey(PreferenceQuestion, related_name="answers", on_delete=models.CASCADE)
    choice = models.CharField(max_length=1, choices=CHOICE_CHOICES)

    class Meta:
        verbose_name = "Réponse de préférence"
        verbose_name_plural = "Réponses de préférence"
        unique_together = ["date_plan", "question"]

    def __str__(self):
        option = self.question.option_a if self.choice == self.CHOICE_A else self.question.option_b
        return f"{self.question}: {option}"
