from django.contrib import admin

from .models import City


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ["name", "region", "is_active", "display_order"]
    list_editable = ["is_active", "display_order"]
    list_filter = ["is_active", "region"]
    search_fields = ["name", "region"]
    prepopulated_fields = {"slug": ("name",)}
