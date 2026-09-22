from django.contrib import admin

from .models import Category, Place, PlaceImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["emoji", "name", "parent", "is_active", "display_order"]
    list_editable = ["is_active", "display_order"]
    list_filter = ["is_active", "parent"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


class PlaceImageInline(admin.TabularInline):
    model = PlaceImage
    extra = 1


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = [
        "name", "category", "subcategory", "city", "price_min", "price_max",
        "rating", "is_recommended", "is_popular", "is_new", "is_active",
    ]
    list_editable = ["is_recommended", "is_popular", "is_new", "is_active"]
    list_filter = ["city", "category", "subcategory", "is_active", "is_recommended", "is_popular"]
    search_fields = ["name", "neighborhood", "address"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [PlaceImageInline]
    fieldsets = (
        ("Identité", {"fields": ("name", "slug", "short_description", "full_description")}),
        ("Classement", {"fields": ("category", "subcategory")}),
        ("Localisation", {"fields": ("city", "neighborhood", "address", "latitude", "longitude")}),
        ("Contact", {"fields": ("phone", "email", "website", "facebook", "instagram")}),
        ("Prix", {"fields": ("price_min", "price_max")}),
        ("Médias", {"fields": ("main_image",)}),
        ("Horaires", {"fields": ("opening_hours", "available_days")}),
        ("Mise en avant", {"fields": ("rating", "is_recommended", "is_popular", "is_new", "is_active")}),
    )
