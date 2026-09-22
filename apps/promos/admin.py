from django.contrib import admin

from .models import PromoCode


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "place", "discount_percent", "valid_until", "used_count", "max_uses", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "place__name"]
