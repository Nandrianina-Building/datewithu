from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LocationShare

#: Durée par défaut d'un partage de position, avant expiration automatique.
DEFAULT_SHARE_HOURS = 6


class StartLocationShareView(APIView):
    """POST /api/safeshare/start/  body: {"contact_name": "...", "date_plan_id": 12}"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        share = LocationShare.objects.create(
            user=request.user,
            date_plan_id=request.data.get("date_plan_id") or None,
            contact_name=request.data.get("contact_name", "")[:100],
            expires_at=timezone.now() + timezone.timedelta(hours=DEFAULT_SHARE_HOURS),
        )
        share_url = request.build_absolute_uri(f"/suivre/{share.token}/")
        return Response({"token": str(share.token), "share_url": share_url}, status=status.HTTP_201_CREATED)


class UpdateLocationShareView(APIView):
    """POST /api/safeshare/<token>/update/  body: {"lat": ..., "lng": ...} — appelé
    régulièrement par le téléphone de la personne qui partage sa position."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, token):
        share = get_object_or_404(LocationShare, token=token, user=request.user)
        if not share.is_currently_active:
            return Response({"detail": "Ce partage de position est terminé."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            lat, lng = float(request.data.get("lat")), float(request.data.get("lng"))
        except (TypeError, ValueError):
            return Response({"detail": "Coordonnées invalides."}, status=status.HTTP_400_BAD_REQUEST)
        share.update_position(lat, lng)
        return Response({"detail": "Position mise à jour."})

    def delete(self, request, token):
        """Arrêter le partage manuellement, avant l'expiration."""
        share = get_object_or_404(LocationShare, token=token, user=request.user)
        share.is_active = False
        share.save(update_fields=["is_active"])
        return Response({"detail": "Partage arrêté."})


class ViewLocationShareView(APIView):
    """
    GET /api/safeshare/<token>/ — consultable SANS compte par la personne
    prévenue : c'est tout l'intérêt (elle n'a pas à s'inscrire pour
    vérifier que tout va bien).
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        share = get_object_or_404(LocationShare, token=token)
        return Response({
            "user_name": share.user.get_full_name() or share.user.username,
            "contact_name": share.contact_name,
            "latitude": share.latitude,
            "longitude": share.longitude,
            "last_updated_at": share.last_updated_at,
            "is_active": share.is_currently_active,
            "expires_at": share.expires_at,
        })
