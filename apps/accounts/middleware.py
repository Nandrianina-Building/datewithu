from urllib.parse import urlencode

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse


class RequireVerifiedEmailMiddleware:
    """Keep unverified signed-in users on confirmation and account recovery routes."""

    ALLOWED_PATHS = {
        "/accounts/verify/pending/",
        "/accounts/verify/resend/",
        "/accounts/logout/",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        path = request.path_info
        if (
            not user.is_authenticated
            or user.is_verified
            or path in self.ALLOWED_PATHS
            or path.startswith("/accounts/verify/")
            or path.startswith("/static/")
            or path.startswith("/media/")
        ):
            return self.get_response(request)

        message = (
            "Confirme ton adresse e-mail pour accéder aux fonctionnalités de Date With U. "
            "Tu peux renvoyer le lien depuis cette page."
        )
        if path.startswith("/api/"):
            return JsonResponse(
                {
                    "detail": message,
                    "code": "email_not_verified",
                    "resend_url": reverse("accounts:resend_verification"),
                },
                status=403,
            )

        messages.warning(request, message)
        next_url = request.get_full_path()
        return redirect(f"{reverse('accounts:verify_pending')}?{urlencode({'next': next_url})}")