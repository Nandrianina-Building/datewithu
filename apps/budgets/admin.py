from django.contrib import admin

from .models import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ["label", "min_amount", "max_amount", "is_active", "display_order"]
    list_editable = ["min_amount", "max_amount", "is_active", "display_order"]
