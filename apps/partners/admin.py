from django.contrib import admin
from django.utils import timezone

from .models import PlaceClaim


@admin.register(PlaceClaim)
class PlaceClaimAdmin(admin.ModelAdmin):
    list_display = ["place", "user", "role", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["place__name", "user__username", "user__email"]
    actions = ["approve", "reject"]

    @admin.action(description="Approuver la revendication")
    def approve(self, request, queryset):
        queryset.update(status=PlaceClaim.STATUS_APPROVED, reviewed_at=timezone.now())

    @admin.action(description="Refuser la revendication")
    def reject(self, request, queryset):
        queryset.update(status=PlaceClaim.STATUS_REJECTED, reviewed_at=timezone.now())
