from django.contrib import admin

from .models import PremiumPlan, Subscription


@admin.register(PremiumPlan)
class PremiumPlanAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "duration_days", "max_active_dates", "is_active", "display_order"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "status", "requested_at", "expires_at"]
    list_filter = ["status", "plan"]
    search_fields = ["user__username", "user__email", "payment_reference"]
    actions = ["approve_and_activate", "reject"]

    @admin.action(description="Approuver et activer l'abonnement")
    def approve_and_activate(self, request, queryset):
        for sub in queryset.filter(status=Subscription.STATUS_PENDING):
            sub.activate()

    @admin.action(description="Refuser la demande")
    def reject(self, request, queryset):
        queryset.filter(status=Subscription.STATUS_PENDING).update(status=Subscription.STATUS_REJECTED)
