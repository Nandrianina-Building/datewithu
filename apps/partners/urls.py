from django.urls import path

from . import views

app_name = "partners"

urlpatterns = [
    path("", views.partner_dashboard_view, name="dashboard"),
    path("revendiquer/<int:place_id>/", views.claim_place_view, name="claim"),
    path("lieux/<int:place_id>/", views.edit_claimed_place_view, name="edit_place"),
    path("avis/<int:review_id>/repondre/", views.reply_to_review_view, name="reply_review"),
]
