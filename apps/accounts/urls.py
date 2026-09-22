from django.urls import path

from . import google_auth, views

app_name = "accounts"

urlpatterns = [
    path("login/", views.DateWithULoginView.as_view(), name="login"),
    path("logout/", views.DateWithULogoutView.as_view(), name="logout"),
    path("google/login/", google_auth.google_login_view, name="google_login"),
    path("google/callback/", google_auth.google_callback_view, name="google_callback"),
    path("password-reset/", views.password_reset_request_view, name="password_reset_request"),
    path("password-reset/envoye/", views.password_reset_sent_view, name="password_reset_sent"),
    path("password-reset/<str:token>/", views.password_reset_confirm_view, name="password_reset_confirm"),
    path("register/", views.register_view, name="register"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/modifier/", views.profile_edit_view, name="profile_edit"),
    path("password-change/", views.DateWithUPasswordChangeView.as_view(), name="password_change"),
    path("password-change/fait/", views.DateWithUPasswordChangeDoneView.as_view(), name="password_change_done"),
    path("supprimer-compte/", views.delete_account_view, name="delete_account"),
    path("u/<int:user_id>/", views.public_profile_view, name="public_profile"),
    path("verify/pending/", views.verify_pending_view, name="verify_pending"),
    path("verify/resend/", views.resend_verification_view, name="resend_verification"),
    path("complete-profile/", views.complete_profile_view, name="complete_profile"),
    path("verify/<str:token>/", views.verify_email_view, name="verify_email"),
]
