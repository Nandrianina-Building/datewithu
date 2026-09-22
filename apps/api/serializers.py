from rest_framework import serializers

from apps.activities.models import Activity
from apps.budgets.models import Budget
from apps.catalog.models import Category, Place, PlaceImage
from apps.locations.models import City
from apps.moods.models import Mood
from apps.occasions.models import Occasion


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = [
            "id", "name", "slug", "region", "description", "image",
            "latitude", "longitude", "display_order",
        ]


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "emoji", "parent", "display_order", "children"]

    def get_children(self, obj):
        qs = obj.children.filter(is_active=True)
        return CategorySerializer(qs, many=True).data


class MoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mood
        fields = ["id", "name", "slug", "emoji", "description", "display_order"]


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ["id", "label", "min_amount", "max_amount", "display_order"]


class OccasionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Occasion
        fields = ["id", "name", "slug", "emoji", "description", "display_order"]


class PlaceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceImage
        fields = ["id", "image", "caption", "display_order"]


class PlaceListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes / résultats de recherche AJAX."""

    city = serializers.StringRelatedField()
    category = serializers.StringRelatedField()

    class Meta:
        model = Place
        fields = [
            "id", "name", "slug", "short_description", "city", "category",
            "main_image", "price_min", "price_max", "rating",
            "is_recommended", "is_popular", "is_new", "latitude", "longitude",
        ]


class PlaceDetailSerializer(serializers.ModelSerializer):
    gallery = PlaceImageSerializer(many=True, read_only=True)
    city = CitySerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    subcategory = CategorySerializer(read_only=True)

    class Meta:
        model = Place
        fields = [
            "id", "name", "slug", "short_description", "full_description",
            "category", "subcategory", "city", "neighborhood", "address",
            "latitude", "longitude", "phone", "email", "website",
            "facebook", "instagram", "price_min", "price_max", "main_image",
            "gallery", "opening_hours", "available_days", "rating",
            "is_recommended", "is_popular", "is_new",
        ]


class ActivitySerializer(serializers.ModelSerializer):
    city = serializers.StringRelatedField()
    place = serializers.StringRelatedField()
    compatible_moods = MoodSerializer(many=True, read_only=True)
    compatible_budgets = BudgetSerializer(many=True, read_only=True)

    class Meta:
        model = Activity
        fields = [
            "id", "name", "slug", "description", "category", "image",
            "duration_minutes", "price", "city", "place",
            "compatible_moods", "compatible_budgets",
        ]


# --- Phase 3 : Date Builder ------------------------------------------------

from apps.planner.models import (  # noqa: E402
    DatePlan, DatePlanPreferenceAnswer, PreferenceQuestion, SpecialAttention,
)


class PreferenceQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreferenceQuestion
        fields = ["id", "question", "option_a", "option_b", "display_order"]


class SpecialAttentionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialAttention
        fields = ["id", "name", "emoji", "description", "display_order"]


class DatePlanPreferenceAnswerSerializer(serializers.ModelSerializer):
    question = PreferenceQuestionSerializer(read_only=True)

    class Meta:
        model = DatePlanPreferenceAnswer
        fields = ["question", "choice"]


class DatePlanStateSerializer(serializers.ModelSerializer):
    """État complet d'un DatePlan, renvoyé après chaque étape (autosave)."""

    mood = MoodSerializer(read_only=True)
    city = CitySerializer(read_only=True)
    place = PlaceListSerializer(read_only=True)
    activity = ActivitySerializer(read_only=True)
    budget = BudgetSerializer(read_only=True)
    occasion = OccasionSerializer(read_only=True)
    special_attentions = SpecialAttentionSerializer(many=True, read_only=True)
    preference_answers = DatePlanPreferenceAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = DatePlan
        fields = [
            "id", "mood", "city", "place", "activity", "budget", "occasion",
            "date_value", "time_value", "personal_message",
            "special_attentions", "preference_answers",
            "current_step", "status", "created_at", "updated_at",
        ]


# --- Phase 8 : packages, avis --------------------------------------------

from apps.packages.models import DatePackage  # noqa: E402
from apps.reviews.models import Review  # noqa: E402


class DatePackageSerializer(serializers.ModelSerializer):
    """
    Utilisée à la fois pour la liste (cartes) et le détail complet affiché
    avant utilisation (voir static/js/packages.js) : les objets imbriqués
    (lieu, activité) donnent assez d'information pour se décider sans
    avoir à lancer le Date Builder pour "voir ce qu'il y a dedans".
    """

    city = CitySerializer(read_only=True)
    mood = MoodSerializer(read_only=True)
    budget = BudgetSerializer(read_only=True)
    place = PlaceListSerializer(read_only=True)
    activity = ActivitySerializer(read_only=True)

    class Meta:
        model = DatePackage
        fields = [
            "id", "name", "slug", "description", "image", "city", "mood",
            "budget", "place", "activity", "price_estimate", "is_featured",
        ]


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ["id", "user", "rating", "comment", "created_at", "owner_reply", "owner_reply_at"]
        read_only_fields = ["user", "created_at", "owner_reply", "owner_reply_at"]

