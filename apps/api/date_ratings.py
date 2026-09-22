from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.invitations.models import Invitation
from apps.planner.models import DatePlan
from apps.reviews.models import DateRating


def _other_party(plan, user):
    """Renvoie l'autre personne du rendez-vous (créateur ou partenaire)."""
    invitation = getattr(plan, "invitation", None)
    if plan.creator_id == user.id:
        return invitation.partner_user if invitation else None
    return plan.creator


class PendingDateRatingsView(APIView):
    """
    GET /api/date-ratings/pending/
    Rendez-vous passés (date dans le passé, invitation acceptée/peut-être)
    où l'utilisateur n'a pas encore noté l'autre partie.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()
        plans = DatePlan.objects.filter(
            Q(creator=user) | Q(invitation__partner_user=user),
            status=DatePlan.STATUS_COMPLETED,
            invitation__status__in=[Invitation.STATUS_ACCEPTED, Invitation.STATUS_MAYBE],
            date_value__isnull=False,
        ).select_related("invitation", "creator", "place").distinct()

        already_rated_ids = set(
            DateRating.objects.filter(rater=user).values_list("date_plan_id", flat=True)
        )

        results = []
        for plan in plans:
            when = timezone.datetime.combine(plan.date_value, plan.time_value or timezone.datetime.min.time())
            when = timezone.make_aware(when) if timezone.is_naive(when) else when
            if when >= now or plan.id in already_rated_ids:
                continue
            other = _other_party(plan, user)
            if other is None:
                continue
            results.append({
                "plan_id": plan.id,
                "other_user_id": other.id,
                "other_user_name": other.get_full_name() or other.username,
                "place": plan.place.name if plan.place_id else None,
                "date_value": plan.date_value,
            })
        return Response(results)


class SubmitDateRatingView(APIView):
    """POST /api/date-ratings/<plan_id>/  body: {"stars": 1-5, "comment": "..."}"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, plan_id):
        plan = get_object_or_404(DatePlan, pk=plan_id)
        user = request.user
        if plan.creator_id != user.id and not (
            getattr(plan, "invitation", None) and plan.invitation.partner_user_id == user.id
        ):
            return Response({"detail": "Accès non autorisé."}, status=status.HTTP_403_FORBIDDEN)

        other = _other_party(plan, user)
        if other is None:
            return Response({"detail": "Impossible de déterminer l'autre participant·e."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            stars = int(request.data.get("stars"))
        except (TypeError, ValueError):
            stars = None
        if stars is None or not (1 <= stars <= 5):
            return Response({"detail": "La note doit être un entier entre 1 et 5."}, status=status.HTTP_400_BAD_REQUEST)

        rating, _ = DateRating.objects.update_or_create(
            date_plan=plan, rater=user, rated_user=other,
            defaults={"stars": stars, "comment": request.data.get("comment", "")[:300]},
        )
        return Response({"detail": "Merci pour ton retour !"}, status=status.HTTP_201_CREATED)


class UserReliabilityView(APIView):
    """GET /api/users/<user_id>/reliability/ — note moyenne publique (affichée sur le profil)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, user_id):
        qs = DateRating.objects.filter(rated_user_id=user_id)
        agg = qs.aggregate(avg=Avg("stars"))
        avg = round(agg["avg"], 1) if agg["avg"] else None
        return Response({"average": avg, "count": qs.count()})
