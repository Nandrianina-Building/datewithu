from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Place
from apps.reviews.models import Review

from . import serializers


class PlaceReviewsView(APIView):
    """
    GET  /api/places/<place_id>/reviews/  → liste des avis
    POST /api/places/<place_id>/reviews/  body: {"rating": 1-5, "comment": "..."}
         (un seul avis par utilisateur et par lieu — renvoie 200 et met à
         jour l'avis existant si l'utilisateur en avait déjà laissé un)
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get(self, request, place_id):
        place = get_object_or_404(Place, pk=place_id)
        reviews = place.reviews.select_related("user")
        return Response(serializers.ReviewSerializer(reviews, many=True).data)

    def post(self, request, place_id):
        place = get_object_or_404(Place, pk=place_id)
        rating = request.data.get("rating")
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            rating = None
        if rating is None or not (1 <= rating <= 5):
            return Response({"detail": "La note doit être un entier entre 1 et 5."}, status=status.HTTP_400_BAD_REQUEST)

        review, created = Review.objects.update_or_create(
            place=place, user=request.user,
            defaults={"rating": rating, "comment": request.data.get("comment", "")},
        )
        return Response(
            serializers.ReviewSerializer(review).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
