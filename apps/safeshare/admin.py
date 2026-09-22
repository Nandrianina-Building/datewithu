from django.contrib import admin

from .models import LocationShare


@admin.register(LocationShare)
class LocationShareAdmin(admin.ModelAdmin):
    list_display = ["user", "contact_name", "created_at", "expires_at", "is_active"]
    list_filter = ["is_active"]
    readonly_fields = ["token"]
