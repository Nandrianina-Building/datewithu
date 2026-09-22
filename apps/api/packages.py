from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.packages.models import DatePackage
from apps.planner.models import STEP_SCHEDULE, DatePlan

from . import serializers


class DatePackageViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/packages/ — liste des rendez-vous clé en main."""

    serializer_class = serializers.DatePackageSerializer

    def get_queryset(self):
        qs = DatePackage.objects.filter(is_active=True).select_related(
            "city", "mood", "budget", "place", "activity"
        )
        city = self.request.query_params.get("city")
        if city:
            qs = qs.filter(city_id=city)
        return qs


class DatePackageUseView(APIView):
    """
    POST /api/packages/<id>/use/ — crée un DatePlan pré-rempli à partir
    du package, prêt pour l'étape "date & heure" (l'utilisateur n'a plus
    qu'à choisir quand, au lieu de refaire les 7 étapes).
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        package = DatePackage.objects.filter(pk=pk, is_active=True).first()
        if package is None:
            return Response({"detail": "Package introuvable."}, status=status.HTTP_404_NOT_FOUND)

        plan = DatePlan.objects.create(
            creator=request.user,
            mood=package.mood,
            city=package.city,
            place=package.place,
            activity=package.activity,
            budget=package.budget,
            current_step=STEP_SCHEDULE,
        )
        return Response(
            {"plan": serializers.DatePlanStateSerializer(plan).data, "next_step": STEP_SCHEDULE},
            status=status.HTTP_201_CREATED,
        )
