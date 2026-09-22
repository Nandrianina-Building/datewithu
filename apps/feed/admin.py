from django.contrib import admin

from .models import FeedConversation, FeedMessage, Post, PostInterest, PostLike


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["author", "caption", "city", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["author__username", "caption"]


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ["post", "user", "created_at"]


@admin.register(PostInterest)
class PostInterestAdmin(admin.ModelAdmin):
    list_display = ["post", "requester", "status", "created_at"]
    list_filter = ["status"]


@admin.register(FeedConversation)
class FeedConversationAdmin(admin.ModelAdmin):
    list_display = ["post", "author", "requester", "created_at"]


@admin.register(FeedMessage)
class FeedMessageAdmin(admin.ModelAdmin):
    list_display = ["conversation", "sender", "created_at"]
