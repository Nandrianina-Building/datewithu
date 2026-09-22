from django.contrib import admin

from .models import Activity


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "city", "place", "duration_minutes", "price", "is_active"]
    list_editable = ["is_active"]
    list_filter = ["city", "category", "is_active", "compatible_moods", "compatible_budgets"]
    search_fields = ["name", "description"]
    filter_horizontal = ["compatible_moods", "compatible_budgets"]
    prepopulated_fields = {"slug": ("name",)}
