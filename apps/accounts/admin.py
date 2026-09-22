from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class DateWithUUserAdmin(UserAdmin):
    list_display = ["username", "email", "first_name", "last_name", "is_verified", "is_staff", "created_at"]
    list_filter = ["is_staff", "is_active", "is_verified"]
    search_fields = ["username", "email", "first_name", "last_name", "phone"]
    fieldsets = UserAdmin.fieldsets + (
        ("Profil Date With U", {
            "fields": ("phone", "avatar", "bio", "birth_date", "is_verified")
        }),
    )
