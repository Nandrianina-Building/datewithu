from django.contrib import admin

from .models import Block, Report


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ["user", "blocked_user", "created_at"]
    search_fields = ["user__username", "blocked_user__username"]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["reporter", "reported_user", "reason", "status", "created_at"]
    list_filter = ["reason", "status"]
    search_fields = ["reporter__username", "reported_user__username", "details"]
    actions = ["mark_reviewed", "mark_dismissed"]

    @admin.action(description="Marquer comme traité")
    def mark_reviewed(self, request, queryset):
        queryset.update(status=Report.STATUS_REVIEWED)

    @admin.action(description="Classer sans suite")
    def mark_dismissed(self, request, queryset):
        queryset.update(status=Report.STATUS_DISMISSED)
