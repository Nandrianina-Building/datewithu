from django.contrib import admin

from .models import DateRating, Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["place", "user", "rating", "created_at"]
    list_filter = ["rating"]
    search_fields = ["place__name", "user__username", "comment"]


@admin.register(DateRating)
class DateRatingAdmin(admin.ModelAdmin):
    list_display = ["rater", "rated_user", "stars", "date_plan", "created_at"]
    search_fields = ["rater__username", "rated_user__username"]
