from django.contrib import admin

from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "city", "is_published", "published_at"]
    list_filter = ["is_published", "city"]
    search_fields = ["title", "content"]
    prepopulated_fields = {"slug": ["title"]}
