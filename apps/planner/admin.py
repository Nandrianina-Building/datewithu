from django.contrib import admin

from .models import DatePlan, DatePlanPreferenceAnswer, PreferenceQuestion, SpecialAttention


@admin.register(PreferenceQuestion)
class PreferenceQuestionAdmin(admin.ModelAdmin):
    list_display = ["question", "option_a", "option_b", "is_active", "display_order"]
    list_editable = ["is_active", "display_order"]


@admin.register(SpecialAttention)
class SpecialAttentionAdmin(admin.ModelAdmin):
    list_display = ["emoji", "name", "is_active", "display_order"]
    list_editable = ["is_active", "display_order"]


class DatePlanPreferenceAnswerInline(admin.TabularInline):
    model = DatePlanPreferenceAnswer
    extra = 0


@admin.register(DatePlan)
class DatePlanAdmin(admin.ModelAdmin):
    list_display = [
        "id", "creator", "mood", "city", "budget", "date_value",
        "time_value", "current_step", "status", "updated_at",
    ]
    list_filter = ["status", "current_step", "city", "mood"]
    search_fields = ["creator__username", "creator__email"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [DatePlanPreferenceAnswerInline]
