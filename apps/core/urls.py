from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("dashboard/", views.user_dashboard_view, name="dashboard"),
    path("dashboard/admin/", views.admin_dashboard_view, name="admin_dashboard"),
    path("date-builder/", views.date_builder_view, name="date_builder"),
    path("explore/", views.explore_view, name="explore"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("mes-rendez-vous/", views.my_dates_page_view, name="my_dates"),
    path("premium/", views.premium_view, name="premium"),
    path("statistiques/", views.statistics_view, name="statistics"),
    path("cgu/", views.terms_view, name="terms"),
    path("confidentialite/", views.privacy_view, name="privacy"),
    path("map/", views.map_view, name="map"),
    path("packages/", views.packages_view, name="packages"),
    path("dates/<int:plan_id>/chat/", views.chat_view, name="chat"),
    path("invite/<uuid:token>/", views.invitation_public_view, name="invitation_public"),
    path("invite/<uuid:token>/qr.png", views.invitation_qr_view, name="invitation_qr"),
    path("invite/<uuid:token>/carte.png", views.invitation_card_view, name="invitation_card"),
    path("suivre/<uuid:token>/", views.track_location_view, name="track_location"),
    path("dates/<int:plan_id>/calendrier.ics", views.date_ics_view, name="date_ics"),
    path("recommandations/", views.recommendations_api_view, name="recommendations"),
    path("invite/<uuid:token>/chat/", views.chat_public_view, name="chat_public"),
]
