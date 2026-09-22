from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activities.models import Activity
from apps.catalog.models import Place
from apps.invitations.models import Invitation
from apps.locations.models import City
from apps.moods.models import Mood
from apps.planner.models import DatePlan

from .permissions import IsStaffUser

User = get_user_model()


class AdminStatsView(APIView):
    """
    GET /api/admin/stats/ — chiffres clés pour le dashboard admin (section
    « statistiques avancées »).
    """

    permission_classes = [IsStaffUser]

    def get(self, request):
        now = timezone.now()
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)

        users_stats = {
            "total": User.objects.count(),
            "staff": User.objects.filter(is_staff=True).count(),
            "new_last_7_days": User.objects.filter(created_at__gte=last_7d).count(),
            "new_last_30_days": User.objects.filter(created_at__gte=last_30d).count(),
        }

        plans_stats = {
            "total": DatePlan.objects.count(),
            "draft": DatePlan.objects.filter(status=DatePlan.STATUS_DRAFT).count(),
            "completed": DatePlan.objects.filter(status=DatePlan.STATUS_COMPLETED).count(),
        }

        invitation_counts = dict(
            Invitation.objects.values_list("status").annotate(count=Count("id")).order_by()
        )
        responded = (
            invitation_counts.get(Invitation.STATUS_ACCEPTED, 0)
            + invitation_counts.get(Invitation.STATUS_MAYBE, 0)
            + invitation_counts.get(Invitation.STATUS_DECLINED, 0)
        )
        acceptance_rate = (
            round(invitation_counts.get(Invitation.STATUS_ACCEPTED, 0) / responded * 100, 1)
            if responded else None
        )
        invitations_stats = {
            "total": Invitation.objects.count(),
            "by_status": invitation_counts,
            "acceptance_rate_percent": acceptance_rate,
        }

        places_stats = {
            "total": Place.objects.count(),
            "active": Place.objects.filter(is_active=True).count(),
            "inactive": Place.objects.filter(is_active=False).count(),
        }
        activities_stats = {
            "total": Activity.objects.count(),
            "active": Activity.objects.filter(is_active=True).count(),
        }

        top_cities = list(
            City.objects.annotate(plan_count=Count("dateplan"))
            .order_by("-plan_count")
            .values("name", "plan_count")[:5]
        )
        top_moods = list(
            Mood.objects.annotate(plan_count=Count("dateplan"))
            .order_by("-plan_count")
            .values("name", "emoji", "plan_count")[:5]
        )

        recent_signups = list(
            User.objects.order_by("-created_at").values("username", "email", "created_at")[:10]
        )

        return Response({
            "users": users_stats,
            "date_plans": plans_stats,
            "invitations": invitations_stats,
            "places": places_stats,
            "activities": activities_stats,
            "top_cities": top_cities,
            "top_moods": top_moods,
            "recent_signups": recent_signups,
        })


class AdminDateOverviewView(APIView):
    """
    GET /api/admin/dates/?status=&city=&when=upcoming|past
    Vue d'ensemble de TOUS les rendez-vous (tous utilisateurs confondus) —
    à ne pas confondre avec /api/my-dates/ qui est scopé au créateur.
    """

    permission_classes = [IsStaffUser]

    def get(self, request):
        plans = (
            DatePlan.objects.filter(status=DatePlan.STATUS_COMPLETED)
            .select_related("creator", "city", "place", "activity", "invitation")
            .order_by("-updated_at")
        )

        params = request.query_params
        city = params.get("city")
        if city:
            plans = plans.filter(city_id=city)

        when = params.get("when")
        if when in ("upcoming", "past"):
            today = timezone.now().date()
            plans = plans.filter(date_value__gte=today) if when == "upcoming" else plans.filter(date_value__lt=today)

        invitation_status = params.get("status")
        if invitation_status:
            plans = plans.filter(invitation__status=invitation_status)

        plans = plans[:100]

        data = []
        for plan in plans:
            invitation = getattr(plan, "invitation", None)
            data.append({
                "plan_id": plan.id,
                "creator": plan.creator.username,
                "city": plan.city.name if plan.city else None,
                "place": plan.place.name if plan.place else None,
                "activity": plan.activity.name if plan.activity else None,
                "date_value": plan.date_value,
                "time_value": plan.time_value,
                "invitation_status": invitation.status if invitation else None,
                "view_count": invitation.view_count if invitation else 0,
            })
        return Response(data)


class AdminPlaceModerationListView(APIView):
    """
    GET /api/admin/places/?active=0 — file de modération : par défaut,
    lieux inactifs (à valider) en premier.
    """

    permission_classes = [IsStaffUser]

    def get(self, request):
        qs = Place.objects.select_related("city", "category").order_by("is_active", "-created_at")
        active_param = request.query_params.get("active")
        if active_param is not None:
            qs = qs.filter(is_active=active_param not in ("0", "false", "False"))
        qs = qs[:100]
        data = [
            {
                "id": p.id,
                "name": p.name,
                "city": p.city.name if p.city else None,
                "category": str(p.category) if p.category else None,
                "is_active": p.is_active,
                "is_recommended": p.is_recommended,
                "created_at": p.created_at,
            }
            for p in qs
        ]
        return Response(data)


class AdminPlaceToggleActiveView(APIView):
    """POST /api/admin/places/<id>/toggle-active/ — activer/désactiver un lieu depuis le dashboard."""

    permission_classes = [IsStaffUser]

    def post(self, request, pk):
        place = get_object_or_404(Place, pk=pk)
        place.is_active = not place.is_active
        place.save(update_fields=["is_active"])
        return Response({"id": place.id, "is_active": place.is_active})


class AdminSiteConfigView(APIView):
    """
    GET/PATCH /api/admin/settings/ — bascule des réglages globaux du site
    (maintenance, inscriptions, chat, avis) sans passer par le Django Admin.
    """

    permission_classes = [IsStaffUser]

    FIELDS = ("maintenance_mode", "registration_enabled", "chat_enabled", "reviews_enabled")

    def _serialize(self, config):
        return {field: getattr(config, field) for field in self.FIELDS} | {
            "site_name": config.site_name,
        }

    def get(self, request):
        from apps.core.models import SiteConfiguration

        return Response(self._serialize(SiteConfiguration.load()))

    def patch(self, request):
        from apps.core.models import SiteConfiguration

        config = SiteConfiguration.load()
        updated = []
        for field in self.FIELDS:
            if field in request.data:
                setattr(config, field, bool(request.data[field]))
                updated.append(field)
        if updated:
            config.save(update_fields=updated)
        return Response(self._serialize(config))


class AdminUsersListView(APIView):
    """
    GET /api/admin/users/?q=&verified=&staff= — liste des comptes pour la
    modération (recherche + filtres), avec pagination simple (limit/offset).
    """

    permission_classes = [IsStaffUser]

    def get(self, request):
        qs = User.objects.all().order_by("-created_at")
        q = request.query_params.get("q")
        if q:
            qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))

        verified = request.query_params.get("verified")
        if verified is not None:
            qs = qs.filter(is_verified=verified not in ("0", "false", "False"))

        staff = request.query_params.get("staff")
        if staff is not None:
            qs = qs.filter(is_staff=staff not in ("0", "false", "False"))

        total = qs.count()
        try:
            offset = int(request.query_params.get("offset", 0))
        except ValueError:
            offset = 0
        page = qs[offset:offset + 25]

        data = [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "is_staff": u.is_staff,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
                "created_at": u.created_at,
            }
            for u in page
        ]
        return Response({"total": total, "offset": offset, "results": data})


class AdminUserToggleActiveView(APIView):
    """
    POST /api/admin/users/<id>/toggle-active/ — active/désactive un compte
    (bannissement doux : la personne ne peut plus se connecter, sans que
    ses données soient supprimées). Un admin ne peut pas se désactiver
    lui-même par erreur.
    """

    permission_classes = [IsStaffUser]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user.pk == request.user.pk:
            return Response(
                {"detail": "Tu ne peux pas désactiver ton propre compte."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        return Response({"id": user.id, "is_active": user.is_active})
