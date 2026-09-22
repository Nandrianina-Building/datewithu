from django.contrib import admin

from .models import DatePackage


@admin.register(DatePackage)
class DatePackageAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "mood", "budget", "price_estimate", "is_featured", "is_active", "display_order"]
    list_editable = ["is_featured", "is_active", "display_order"]
    list_filter = ["city", "mood", "is_active", "is_featured"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
