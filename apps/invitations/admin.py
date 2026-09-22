from django.contrib import admin

from .models import Invitation


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = [
        "id", "date_plan", "status", "partner_name", "view_count",
        "created_at", "expires_at", "responded_at",
    ]
    list_filter = ["status"]
    search_fields = ["date_plan__creator__username", "partner_name", "token"]
    readonly_fields = ["token", "view_count", "first_viewed_at", "created_at", "responded_at"]
