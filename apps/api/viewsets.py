from django.db import models
from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.response import Response

from apps.activities.models import Activity
from apps.budgets.models import Budget
from apps.catalog.models import Category, Place
from apps.locations.models import City
from apps.moods.models import Mood
from apps.occasions.models import Occasion

from . import serializers
from .pagination import TenPerPagePagination


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/cities/?search=ana&page=2
    Recherche + pagination AJAX des villes (page d'accueil « Voir plus »,
    étape 2 du Date Builder). Public : la liste des villes est déjà
    visible par tout le monde sur la page d'accueil, pas de raison de
    l'exiger derrière une connexion pour le "Voir plus" en AJAX.
    """

    serializer_class = serializers.CitySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = City.objects.filter(is_active=True).order_by("display_order", "name")
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(region__icontains=search))
        return qs


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Ne renvoie que les catégories racines ; les sous-catégories sont
    imbriquées dans `children` (voir CategorySerializer)."""

    queryset = Category.objects.filter(is_active=True, parent__isnull=True)
    serializer_class = serializers.CategorySerializer


class MoodViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Mood.objects.filter(is_active=True)
    serializer_class = serializers.MoodSerializer


class BudgetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Budget.objects.filter(is_active=True)
    serializer_class = serializers.BudgetSerializer


class OccasionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Occasion.objects.filter(is_active=True)
    serializer_class = serializers.OccasionSerializer


class PlaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Recherche + filtrage AJAX des lieux (sections 13-14).

    Exemples :
        GET /api/places/?search=tana
        GET /api/places/?city=1&category=2&budget=3&mood=1
    """

    pagination_class = TenPerPagePagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.PlaceDetailSerializer
        return serializers.PlaceListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Place.objects.filter(pk=instance.pk).update(view_count=models.F("view_count") + 1)
        instance.refresh_from_db(fields=["view_count"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        qs = Place.objects.filter(is_active=True).select_related(
            "city", "category", "subcategory"
        ).prefetch_related("gallery")

        params = self.request.query_params

        search = params.get("search")
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(short_description__icontains=search)
                | Q(neighborhood__icontains=search)
                | Q(city__name__icontains=search)
            )

        city = params.get("city")
        if city:
            qs = qs.filter(city_id=city)

        category = params.get("category")
        if category:
            qs = qs.filter(category_id=category)

        subcategory = params.get("subcategory")
        if subcategory:
            qs = qs.filter(subcategory_id=subcategory)

        budget = params.get("budget")
        if budget:
            try:
                b = Budget.objects.get(pk=budget)
            except Budget.DoesNotExist:
                b = None
            if b:
                qs = qs.filter(price_min__gte=b.min_amount)
                if b.max_amount is not None:
                    qs = qs.filter(price_max__lte=b.max_amount)

        mood = params.get("mood")
        if mood:
            qs = qs.filter(activities__compatible_moods__id=mood).distinct()

        recommended = params.get("recommended")
        if recommended is not None:
            qs = qs.filter(is_recommended=True)

        popular = params.get("popular")
        if popular is not None:
            qs = qs.filter(is_popular=True)

        return qs.distinct()


class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/activities/?city=1&mood=2&budget=3&category=4
    """

    serializer_class = serializers.ActivitySerializer

    def get_queryset(self):
        qs = Activity.objects.filter(is_active=True).select_related(
            "city", "place", "category"
        ).prefetch_related("compatible_moods", "compatible_budgets")

        params = self.request.query_params

        city = params.get("city")
        if city:
            qs = qs.filter(city_id=city)

        category = params.get("category")
        if category:
            qs = qs.filter(category_id=category)

        mood = params.get("mood")
        if mood:
            qs = qs.filter(compatible_moods__id=mood)

        budget = params.get("budget")
        if budget:
            qs = qs.filter(compatible_budgets__id=budget)

        search = params.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))

        return qs.distinct()
