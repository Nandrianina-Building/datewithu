from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.article_list_view, name="list"),
    path("<slug:slug>/", views.article_detail_view, name="detail"),
]
