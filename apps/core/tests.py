from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from .middleware import PageViewCountMiddleware
from .models import SiteConfiguration


class PageViewCountMiddlewareTests(TestCase):
    def setUp(self):
        self.config = SiteConfiguration.objects.create(page_views=0)
        self.factory = RequestFactory()

    def make_request(self, path="/explore/", method="get", status=200, content_type="text/html"):
        middleware = PageViewCountMiddleware(
            lambda request: HttpResponse("response", status=status, content_type=content_type)
        )
        return middleware(getattr(self.factory, method)(path))

    def test_counts_successful_html_get(self):
        self.make_request()

        self.config.refresh_from_db()
        self.assertEqual(self.config.page_views, 1)

    def test_creates_counter_when_first_visit_has_no_configuration(self):
        self.config.delete()

        self.make_request()

        self.assertEqual(SiteConfiguration.objects.get(pk=1).page_views, 1)

    def test_does_not_count_api_or_static_requests(self):
        self.make_request("/api/places/")
        self.make_request("/static/css/main.css", content_type="text/html")

        self.config.refresh_from_db()
        self.assertEqual(self.config.page_views, 0)

    def test_does_not_count_non_html_or_unsuccessful_responses(self):
        self.make_request(content_type="application/json")
        self.make_request(status=404)
        self.make_request(method="head")

        self.config.refresh_from_db()
        self.assertEqual(self.config.page_views, 0)
