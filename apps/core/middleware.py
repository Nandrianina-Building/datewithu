import logging

from django.conf import settings
from django.db import DatabaseError
from django.db.models import F

from .models import SiteConfiguration

logger = logging.getLogger(__name__)


class PageViewCountMiddleware:
    """Count successful HTML page loads without storing visitor data."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        content_type = response.get("Content-Type", "")

        if (
            request.method == "GET"
            and response.status_code == 200
            and content_type.startswith("text/html")
            and not request.path.startswith((
                "/api/",
                "/static/",
                "/media/",
                f"/{settings.ADMIN_URL_PATH.lstrip('/')}",
            ))
        ):
            try:
                updated = SiteConfiguration.objects.filter(pk=1).update(
                    page_views=F("page_views") + 1,
                )
                if not updated:
                    SiteConfiguration.objects.get_or_create(pk=1)
                    SiteConfiguration.objects.filter(pk=1).update(
                        page_views=F("page_views") + 1,
                    )
            except DatabaseError:
                logger.exception("Impossible d'incrémenter le compteur de visites.")

        return response
