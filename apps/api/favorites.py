from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activities.models import Activity
from apps.catalog.models import Place
from apps.favorites.models import FavoriteActivity, FavoritePlace

from .serializers import ActivitySerializer, PlaceListSerializer


class FavoritePlaceToggleView(APIView):
    """POST /api/favorites/places/<place_id>/toggle/"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, place_id):
        place = Place.objects.filter(pk=place_id, is_active=True).first()
        if place is None:
            return Response({"detail": "Lieu introuvable."}, status=status.HTTP_404_NOT_FOUND)

        favorite = FavoritePlace.objects.filter(user=request.user, place=place).first()
        if favorite:
            favorite.delete()
            return Response({"favorited": False})

        FavoritePlace.objects.create(user=request.user, place=place)
        return Response({"favorited": True})


class FavoriteActivityToggleView(APIView):
    """POST /api/favorites/activities/<activity_id>/toggle/"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, activity_id):
        activity = Activity.objects.filter(pk=activity_id, is_active=True).first()
        if activity is None:
            return Response({"detail": "Activité introuvable."}, status=status.HTTP_404_NOT_FOUND)

        favorite = FavoriteActivity.objects.filter(user=request.user, activity=activity).first()
        if favorite:
            favorite.delete()
            return Response({"favorited": False})

        FavoriteActivity.objects.create(user=request.user, activity=activity)
        return Response({"favorited": True})


class MyFavoritesListView(APIView):
    """GET /api/favorites/ — lieux + activités favoris de l'utilisateur connecté."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        places = Place.objects.filter(favorited_by__user=request.user, is_active=True)
        activities = Activity.objects.filter(favorited_by__user=request.user, is_active=True)
        return Response({
            "places": PlaceListSerializer(places, many=True).data,
            "activities": ActivitySerializer(activities, many=True).data,
        })
