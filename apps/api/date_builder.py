"""
Date Builder dynamique (section 12) : au lieu d'un `if step === 1 ...`
côté frontend, le frontend POST ce que l'utilisateur vient de choisir,
et Django répond avec l'étape suivante + les options pertinentes,
déjà filtrées par les choix précédents (section 14).

Flux typique côté frontend :

    POST /api/date-builder/start/
    → { "plan": {...}, "next_step": "mood", "options": {...} }

    POST /api/date-builder/<id>/step/   body: {"mood": 3}
    → { "plan": {...}, "next_step": "city", "options": {...} }

    ... (répéter pour city, place, activity, budget, schedule) ...

    POST /api/date-builder/<id>/step/
        body: {"occasion": 2, "preferences": {"1": "a", "2": "b"},
               "special_attentions": [1, 4], "personal_message": "..."}
    → { "plan": {...}, "next_step": "final", "options": {...} }

    POST /api/date-builder/<id>/complete/
    → { "plan": {...} }  (status devient "completed" — base de l'invitation, Phase 4)
"""
from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activities.models import Activity
from apps.budgets.models import Budget
from apps.catalog.models import Place
from apps.locations.models import City
from apps.moods.models import Mood
from apps.occasions.models import Occasion
from apps.planner.models import (
    STEP_ACTIVITY, STEP_BUDGET, STEP_CITY, STEP_FINAL, STEP_MOOD,
    STEP_ORDER, STEP_PLACE, STEP_SCHEDULE,
    DatePlan, DatePlanPreferenceAnswer, PreferenceQuestion, SpecialAttention,
)

from . import serializers


def _is_future_date(value):
    """Return whether a Date Builder date is after the server's local date."""
    return value > timezone.localdate()

#: Nombre d'éléments affichés initialement pour une étape à choix
#: multiples avant recherche/pagination AJAX via /api/cities/ ou
#: /api/places/ (voir static/js/date-builder.js).
SEARCH_PAGE_SIZE = 12


def _step_index(step_name):
    return STEP_ORDER.index(step_name)


def _next_step(current_step):
    idx = _step_index(current_step)
    if idx >= len(STEP_ORDER) - 1:
        return STEP_FINAL
    return STEP_ORDER[idx + 1]


def get_step_options(plan):
    """Options pertinentes pour l'étape courante du plan, filtrées par
    les choix déjà faits (section 14 : suggestions immédiates)."""
    step = plan.current_step

    if step == STEP_MOOD:
        qs = Mood.objects.filter(is_active=True)
        return {"moods": serializers.MoodSerializer(qs, many=True).data}

    if step == STEP_CITY:
        qs = City.objects.filter(is_active=True).order_by("display_order", "name")[:SEARCH_PAGE_SIZE]
        return {"cities": serializers.CitySerializer(qs, many=True).data}

    if step == STEP_PLACE:
        qs = Place.objects.filter(is_active=True)
        if plan.city_id:
            qs = qs.filter(city_id=plan.city_id)
        if plan.budget_id:
            qs = qs.filter(price_min__gte=plan.budget.min_amount)
            if plan.budget.max_amount is not None:
                qs = qs.filter(price_max__lte=plan.budget.max_amount)
        if plan.mood_id:
            qs = qs.filter(activities__compatible_moods=plan.mood_id).distinct()
        qs = qs.order_by("-is_recommended", "-is_popular")[:12]
        return {"places": serializers.PlaceListSerializer(qs, many=True).data}

    if step == STEP_ACTIVITY:
        qs = Activity.objects.filter(is_active=True)
        if plan.city_id:
            qs = qs.filter(city_id=plan.city_id)
        if plan.place_id:
            qs = qs.filter(place_id=plan.place_id)
        if plan.mood_id:
            qs = qs.filter(compatible_moods=plan.mood_id)
        if plan.budget_id:
            qs = qs.filter(compatible_budgets=plan.budget_id)
        qs = qs.distinct()[:12]
        return {"activities": serializers.ActivitySerializer(qs, many=True).data}

    if step == STEP_BUDGET:
        qs = Budget.objects.filter(is_active=True)
        return {"budgets": serializers.BudgetSerializer(qs, many=True).data}

    if step == STEP_SCHEDULE:
        return {}  # le frontend affiche simplement un sélecteur date/heure

    if step == STEP_FINAL:
        return {
            "occasions": serializers.OccasionSerializer(
                Occasion.objects.filter(is_active=True), many=True
            ).data,
            "preference_questions": serializers.PreferenceQuestionSerializer(
                PreferenceQuestion.objects.filter(is_active=True), many=True
            ).data,
            "special_attentions": serializers.SpecialAttentionSerializer(
                SpecialAttention.objects.filter(is_active=True), many=True
            ).data,
        }

    return {}


class DateBuilderStartView(APIView):
    """POST /api/date-builder/start/ — crée un nouveau brouillon de rendez-vous."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        plan = DatePlan.objects.create(creator=request.user)
        return Response(
            {
                "plan": serializers.DatePlanStateSerializer(plan).data,
                "next_step": plan.current_step,
                "options": get_step_options(plan),
            },
            status=status.HTTP_201_CREATED,
        )


class DateBuilderDetailView(APIView):
    """GET /api/date-builder/<id>/ — reprendre un brouillon existant."""

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, pk):
        return DatePlan.objects.filter(pk=pk, creator=request.user).first()

    def get(self, request, pk):
        plan = self.get_object(request, pk)
        if plan is None:
            return Response({"detail": "Introuvable."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "plan": serializers.DatePlanStateSerializer(plan).data,
                "next_step": plan.current_step,
                "options": get_step_options(plan),
            }
        )


class DateBuilderStepView(APIView):
    """POST /api/date-builder/<id>/step/ — met à jour une étape (autosave)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        plan = DatePlan.objects.filter(pk=pk, creator=request.user).first()
        if plan is None:
            return Response({"detail": "Introuvable."}, status=status.HTTP_404_NOT_FOUND)
        if plan.status == DatePlan.STATUS_COMPLETED:
            return Response(
                {"detail": "Ce rendez-vous est déjà finalisé."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data
        touched_step = None
        errors = {}

        if data.get("skip") in (STEP_PLACE, STEP_ACTIVITY):
            touched_step = data["skip"]

        if "mood" in data:
            touched_step = STEP_MOOD
            mood = Mood.objects.filter(pk=data["mood"], is_active=True).first()
            if mood is None:
                errors["mood"] = "Ambiance invalide."
            else:
                plan.mood = mood

        if "city" in data:
            touched_step = STEP_CITY
            city = City.objects.filter(pk=data["city"], is_active=True).first()
            if city is None:
                errors["city"] = "Ville invalide."
            else:
                if plan.city_id != city.id:
                    # La ville change : les choix de lieu/activité ne sont
                    # plus forcément cohérents, on les réinitialise.
                    plan.place = None
                    plan.activity = None
                plan.city = city

        if "place" in data:
            touched_step = STEP_PLACE
            qs = Place.objects.filter(pk=data["place"], is_active=True)
            if plan.city_id:
                qs = qs.filter(city_id=plan.city_id)
            place = qs.first()
            if place is None:
                errors["place"] = "Lieu invalide pour la ville sélectionnée."
            else:
                plan.place = place

        if "activity" in data:
            touched_step = STEP_ACTIVITY
            qs = Activity.objects.filter(pk=data["activity"], is_active=True)
            if plan.city_id:
                qs = qs.filter(city_id=plan.city_id)
            activity = qs.first()
            if activity is None:
                errors["activity"] = "Activité invalide pour la ville sélectionnée."
            else:
                plan.activity = activity

        if "budget" in data:
            touched_step = STEP_BUDGET
            budget = Budget.objects.filter(pk=data["budget"], is_active=True).first()
            if budget is None:
                errors["budget"] = "Budget invalide."
            else:
                plan.budget = budget

        if "date" in data or "time" in data:
            touched_step = STEP_SCHEDULE
            if "date" in data:
                try:
                    date_value = datetime.strptime(data["date"], "%Y-%m-%d").date()
                    if not _is_future_date(date_value):
                        errors["date"] = "La date du rendez-vous doit être dans le futur."
                    else:
                        plan.date_value = date_value
                except (ValueError, TypeError):
                    errors["date"] = "Format attendu : AAAA-MM-JJ."
            if "time" in data:
                try:
                    plan.time_value = datetime.strptime(data["time"], "%H:%M").time()
                except (ValueError, TypeError):
                    errors["time"] = "Format attendu : HH:MM."

        if "occasion" in data:
            touched_step = STEP_FINAL
            occasion_id = data.get("occasion")
            if not occasion_id:
                plan.occasion = None
            else:
                try:
                    occasion_id = int(occasion_id)
                except (TypeError, ValueError):
                    occasion_id = None
                occasion = Occasion.objects.filter(pk=occasion_id, is_active=True).first() if occasion_id else None
                if occasion is None:
                    errors["occasion"] = "Occasion invalide."
                else:
                    plan.occasion = occasion

        if "personal_message" in data:
            touched_step = STEP_FINAL
            plan.personal_message = data["personal_message"]

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        plan.save()

        # M2M : special_attentions et preferences se sauvegardent après le
        # save() du plan (nécessite un pk existant, déjà le cas ici).
        if "special_attentions" in data:
            touched_step = STEP_FINAL
            ids = data.get("special_attentions") or []
            plan.special_attentions.set(
                SpecialAttention.objects.filter(pk__in=ids, is_active=True)
            )

        if "preferences" in data:
            touched_step = STEP_FINAL
            for question_id, choice in (data.get("preferences") or {}).items():
                if choice not in (DatePlanPreferenceAnswer.CHOICE_A, DatePlanPreferenceAnswer.CHOICE_B):
                    continue
                question = PreferenceQuestion.objects.filter(pk=question_id, is_active=True).first()
                if not question:
                    continue
                DatePlanPreferenceAnswer.objects.update_or_create(
                    date_plan=plan, question=question, defaults={"choice": choice}
                )

        # On avance current_step sans jamais reculer, pour ne pas perdre
        # la progression si l'utilisateur revient corriger une étape passée.
        if touched_step is not None:
            candidate = _next_step(touched_step)
            if _step_index(candidate) > _step_index(plan.current_step):
                plan.current_step = candidate
                plan.save(update_fields=["current_step"])

        return Response(
            {
                "plan": serializers.DatePlanStateSerializer(plan).data,
                "next_step": plan.current_step,
                "options": get_step_options(plan),
            }
        )


class DateBuilderCompleteView(APIView):
    """
    POST /api/date-builder/<id>/complete/ — finalise le rendez-vous.
    Devient la "proposition de rendez-vous" (section 1) que la Phase 4
    transformera en invitation.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        plan = DatePlan.objects.filter(pk=pk, creator=request.user).first()
        if plan is None:
            return Response({"detail": "Introuvable."}, status=status.HTTP_404_NOT_FOUND)

        if not plan.is_complete_enough_to_finalize:
            return Response(
                {
                    "detail": "Le rendez-vous n'est pas encore complet.",
                    "required": ["mood", "city", "budget", "date_value", "time_value", "place_ou_activity"],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not _is_future_date(plan.date_value):
            return Response(
                {"detail": "La date du rendez-vous doit être dans le futur."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        plan.status = DatePlan.STATUS_COMPLETED
        plan.current_step = STEP_FINAL
        plan.save(update_fields=["status", "current_step"])

        return Response({"plan": serializers.DatePlanStateSerializer(plan).data})


class DateSurpriseView(APIView):
    """
    POST /api/date-builder/surprise/   body: {"city": <id>?, "budget": <id>?}

    « Surprise Date » (section « Fonctionnalités avancées ») : Django
    choisit tout au hasard (ambiance, ville si non précisée, lieu ou
    activité compatible, budget si non précisé, prochain samedi 19h) et
    renvoie un DatePlan encore en brouillon — l'utilisateur peut relancer,
    ajuster, ou finaliser directement via /complete/.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        mood = Mood.objects.filter(is_active=True).order_by("?").first()
        if mood is None:
            return Response({"detail": "Aucune ambiance disponible."}, status=status.HTTP_400_BAD_REQUEST)

        city_id = request.data.get("city")
        city = City.objects.filter(pk=city_id, is_active=True).first() if city_id else None
        if city is None:
            city = City.objects.filter(is_active=True).order_by("?").first()
        if city is None:
            return Response({"detail": "Aucune ville disponible."}, status=status.HTTP_400_BAD_REQUEST)

        budget_id = request.data.get("budget")
        budget = Budget.objects.filter(pk=budget_id, is_active=True).first() if budget_id else None
        if budget is None:
            budget = Budget.objects.filter(is_active=True).order_by("?").first()

        place = Place.objects.filter(is_active=True, city=city).order_by("?").first()
        activity = None
        if place is None:
            activity_qs = Activity.objects.filter(is_active=True, city=city)
            if budget:
                activity_qs = activity_qs.filter(compatible_budgets=budget)
            activity = activity_qs.order_by("?").first()

        today = timezone.now().date()
        days_until_saturday = (5 - today.weekday()) % 7 or 7  # le prochain samedi, jamais aujourd'hui
        surprise_date = today + timedelta(days=days_until_saturday)

        plan = DatePlan.objects.create(
            creator=request.user,
            mood=mood,
            city=city,
            budget=budget,
            place=place,
            activity=activity,
            date_value=surprise_date,
            time_value=datetime.strptime("19:00", "%H:%M").time(),
            current_step=STEP_FINAL,
        )

        return Response(
            {
                "plan": serializers.DatePlanStateSerializer(plan).data,
                "next_step": STEP_FINAL,
                "options": get_step_options(plan),
            },
            status=status.HTTP_201_CREATED,
        )
