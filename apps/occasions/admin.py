from django.contrib import admin

from .models import Occasion


@admin.register(Occasion)
class OccasionAdmin(admin.ModelAdmin):
    list_display = ["emoji", "name", "is_active", "display_order"]
    list_editable = ["is_active", "display_order"]
    search_fields = ["name"]
