from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core.views import service_worker_view, robots_txt_view, sitemap_xml_view
from apps.feed.urls import messages_urlpatterns

urlpatterns = [
    # Le chemin est configurable via ADMIN_URL_PATH (.env) : en prod, on évite
    # de laisser le Django Admin sur le très prévisible "/admin/".
    path(settings.ADMIN_URL_PATH, admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("partenaires/", include("apps.partners.urls")),
    path("magazine/", include("apps.blog.urls")),
    path("fil/", include("apps.feed.urls")),
    path("messages/", include((messages_urlpatterns, "feedmessages"), namespace="messages")),
    path("api/", include("apps.api.urls")),
    path("sw.js", service_worker_view, name="service-worker"),
    path("robots.txt", robots_txt_view, name="robots-txt"),
    path("sitemap.xml", sitemap_xml_view, name="sitemap-xml"),
    path("", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
