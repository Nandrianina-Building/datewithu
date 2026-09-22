from django.contrib import admin

from .models import FavoriteActivity, FavoritePlace


@admin.register(FavoritePlace)
class FavoritePlaceAdmin(admin.ModelAdmin):
    list_display = ["user", "place", "created_at"]
    search_fields = ["user__username", "place__name"]


@admin.register(FavoriteActivity)
class FavoriteActivityAdmin(admin.ModelAdmin):
    list_display = ["user", "activity", "created_at"]
    search_fields = ["user__username", "activity__name"]
