from django.contrib import admin

from .models import SiteConfiguration


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ["site_name", "default_currency", "maintenance_mode", "updated_at"]

    def has_add_permission(self, request):
        # Singleton : on ne peut pas en créer un deuxième.
        return not SiteConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
