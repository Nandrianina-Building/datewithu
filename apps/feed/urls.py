from django.urls import path

from . import views

app_name = "feed"

urlpatterns = [
    path("", views.feed_view, name="feed"),
]

messages_urlpatterns = [
    path("", views.inbox_view, name="inbox"),
    path("demandes/", views.received_requests_view, name="received_requests"),
    path("<int:conversation_id>/", views.feed_conversation_view, name="conversation"),
]
