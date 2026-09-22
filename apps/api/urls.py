from django.urls import path
from rest_framework.routers import DefaultRouter

from . import viewsets
from .admin_dashboard import (
    AdminDateOverviewView, AdminPlaceModerationListView, AdminPlaceToggleActiveView,
    AdminSiteConfigView, AdminStatsView, AdminUsersListView, AdminUserToggleActiveView,
)
from .chat import ChatMessagesView
from .date_builder import (
    DateBuilderCompleteView, DateBuilderDetailView, DateBuilderStartView, DateBuilderStepView, DateSurpriseView,
)
from .favorites import FavoriteActivityToggleView, FavoritePlaceToggleView, MyFavoritesListView
from .invitations import (
    InvitationCancelView, InvitationCreateView, InvitationDetailView,
    InvitationPublicView, InvitationRespondView, MyDateDetailView, MyDatesListView,
    ReceivedInvitationsListView,
)
from .notifications import (
    NotificationDeleteView, NotificationListView, NotificationMarkAllReadView, NotificationMarkReadView,
)
from .packages import DatePackageUseView, DatePackageViewSet
from .reviews import PlaceReviewsView
from .safety import BlockToggleView, MyBlockedUsersListView, ReportUserView
from .date_ratings import PendingDateRatingsView, SubmitDateRatingView, UserReliabilityView
from apps.safeshare.api import StartLocationShareView, UpdateLocationShareView, ViewLocationShareView
from .feed import (
    FeedConversationMessagesView, FeedListView, InboxView, MyReceivedInterestsView,
    PostDeactivateView, PostInterestCreateView, PostInterestRespondView, PostLikeToggleView,
)

router = DefaultRouter()
router.register("cities", viewsets.CityViewSet, basename="city")
router.register("categories", viewsets.CategoryViewSet, basename="category")
router.register("moods", viewsets.MoodViewSet, basename="mood")
router.register("budgets", viewsets.BudgetViewSet, basename="budget")
router.register("occasions", viewsets.OccasionViewSet, basename="occasion")
router.register("places", viewsets.PlaceViewSet, basename="place")
router.register("activities", viewsets.ActivityViewSet, basename="activity")
router.register("packages", DatePackageViewSet, basename="package")

urlpatterns = router.urls + [
    path("date-builder/start/", DateBuilderStartView.as_view(), name="date-builder-start"),
    path("date-builder/surprise/", DateSurpriseView.as_view(), name="date-builder-surprise"),
    path("date-builder/<int:pk>/", DateBuilderDetailView.as_view(), name="date-builder-detail"),
    path("date-builder/<int:pk>/step/", DateBuilderStepView.as_view(), name="date-builder-step"),
    path("date-builder/<int:pk>/complete/", DateBuilderCompleteView.as_view(), name="date-builder-complete"),
    path("invitations/create/", InvitationCreateView.as_view(), name="invitation-create"),
    path("invitations/<uuid:token>/", InvitationDetailView.as_view(), name="invitation-detail"),
    path("invitations/<uuid:token>/cancel/", InvitationCancelView.as_view(), name="invitation-cancel"),
    path("invitations/<uuid:token>/public/", InvitationPublicView.as_view(), name="invitation-public"),
    path("invitations/<uuid:token>/respond/", InvitationRespondView.as_view(), name="invitation-respond"),
    path("my-dates/", MyDatesListView.as_view(), name="my-dates"),
    path("my-dates/received/", ReceivedInvitationsListView.as_view(), name="my-dates-received"),
    path("my-dates/<int:plan_id>/", MyDateDetailView.as_view(), name="my-date-detail"),
    path("favorites/", MyFavoritesListView.as_view(), name="my-favorites"),
    path("favorites/places/<int:place_id>/toggle/", FavoritePlaceToggleView.as_view(), name="favorite-place-toggle"),
    path("favorites/activities/<int:activity_id>/toggle/", FavoriteActivityToggleView.as_view(), name="favorite-activity-toggle"),
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    path("notifications/<int:pk>/read/", NotificationMarkReadView.as_view(), name="notification-read"),
    path("notifications/<int:pk>/", NotificationDeleteView.as_view(), name="notification-delete"),
    path("notifications/read-all/", NotificationMarkAllReadView.as_view(), name="notifications-read-all"),
    path("admin/stats/", AdminStatsView.as_view(), name="admin-stats"),
    path("admin/dates/", AdminDateOverviewView.as_view(), name="admin-dates"),
    path("admin/places/", AdminPlaceModerationListView.as_view(), name="admin-places"),
    path("admin/places/<int:pk>/toggle-active/", AdminPlaceToggleActiveView.as_view(), name="admin-place-toggle"),
    path("admin/settings/", AdminSiteConfigView.as_view(), name="admin-settings"),
    path("admin/users/", AdminUsersListView.as_view(), name="admin-users"),
    path("admin/users/<int:pk>/toggle-active/", AdminUserToggleActiveView.as_view(), name="admin-user-toggle"),
    path("chat/<int:date_plan_id>/messages/", ChatMessagesView.as_view(), name="chat-messages"),
    path("packages/<int:pk>/use/", DatePackageUseView.as_view(), name="package-use"),
    path("places/<int:place_id>/reviews/", PlaceReviewsView.as_view(), name="place-reviews"),
    path("safety/block/<int:user_id>/", BlockToggleView.as_view(), name="safety-block"),
    path("safety/blocked/", MyBlockedUsersListView.as_view(), name="safety-blocked-list"),
    path("safety/report/<int:user_id>/", ReportUserView.as_view(), name="safety-report"),
    path("date-ratings/pending/", PendingDateRatingsView.as_view(), name="date-ratings-pending"),
    path("date-ratings/<int:plan_id>/", SubmitDateRatingView.as_view(), name="date-ratings-submit"),
    path("users/<int:user_id>/reliability/", UserReliabilityView.as_view(), name="user-reliability"),
    path("safeshare/start/", StartLocationShareView.as_view(), name="safeshare-start"),
    path("safeshare/<uuid:token>/", ViewLocationShareView.as_view(), name="safeshare-view"),
    path("safeshare/<uuid:token>/update/", UpdateLocationShareView.as_view(), name="safeshare-update"),
    path("feed/", FeedListView.as_view(), name="feed-list"),
    path("feed/<int:post_id>/close/", PostDeactivateView.as_view(), name="feed-close"),
    path("feed/<int:post_id>/like/", PostLikeToggleView.as_view(), name="feed-like"),
    path("feed/<int:post_id>/interest/", PostInterestCreateView.as_view(), name="feed-interest"),
    path("feed/demandes-recues/", MyReceivedInterestsView.as_view(), name="feed-interests-received"),
    path("feed/demandes/<int:interest_id>/repondre/", PostInterestRespondView.as_view(), name="feed-interest-respond"),
    path("feed/conversations/<int:conversation_id>/messages/", FeedConversationMessagesView.as_view(), name="feed-conversation-messages"),
    path("messages/", InboxView.as_view(), name="inbox"),
]
